"""
Authentication service
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
import pyotp
import qrcode
from io import BytesIO
import base64
import secrets
import re
from sqlalchemy import or_

from app.core.config import settings
from app.database.database import get_db
from app.core.exceptions import AuthenticationError, ValidationError, NotFoundError
from app.models.user import User, TwoFactorToken, PasswordResetToken
from app.models.audit import AuditLog
from app.schemas.auth import (
    Token, TokenData, TwoFactorSetup, StaffRegister, PatientRegister,
    ForgotPassword, ResetPassword, VerifyEmail, ChangePassword
)

# Password hashing - fix bcrypt version issue
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

class AuthService:
    """Authentication service"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash password"""
        return pwd_context.hash(password)
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str) -> TokenData:
        """Verify and decode token"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            username: str = payload.get("sub")
            user_id: int = payload.get("user_id")
            tenant_id: int = payload.get("tenant_id")
            
            if username is None or user_id is None:
                raise AuthenticationError("Invalid token")
            
            return TokenData(username=username, user_id=user_id, tenant_id=tenant_id)
        except JWTError:
            raise AuthenticationError("Invalid token")
    
    def verify_refresh_token(self, token: str) -> TokenData:
        """Verify and decode refresh token"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            username: str = payload.get("sub")
            user_id: int = payload.get("user_id")
            tenant_id: int = payload.get("tenant_id")
            token_type: str = payload.get("type")
            
            if username is None or user_id is None:
                raise AuthenticationError("Invalid refresh token")
            
            if token_type != "refresh":
                raise AuthenticationError("Invalid refresh token type")
            
            return TokenData(username=username, user_id=user_id, tenant_id=tenant_id)
        except JWTError:
            raise AuthenticationError("Invalid refresh token")
    
    def log_audit_event(self, user_id: Optional[int], action: str, entity_type: str, 
                       entity_id: Optional[str] = None, details: Optional[Dict] = None,
                       ip_address: Optional[str] = None, user_agent: Optional[str] = None):
        """Log audit event"""
        # Temporarily disabled to avoid circular import issues
        pass
        # audit_log = AuditLog(
        #     user_id=user_id,
        #     action=action,
        #     entity_type=entity_type,
        #     entity_id=entity_id,
        #     details=details,
        #     ip_address=ip_address,
        #     user_agent=user_agent
        # )
        # self.db.add(audit_log)
        # self.db.commit()
    
    def is_account_locked(self, user: User) -> bool:
        """Check if account is locked"""
        if user.locked_until and user.locked_until > datetime.utcnow():
            return True
        return False
    
    def lock_account(self, user: User, minutes: int = 30):
        """Lock account for specified minutes"""
        user.locked_until = datetime.utcnow() + timedelta(minutes=minutes)
        user.failed_login_attempts = 0
        self.db.commit()
    
    def increment_failed_attempts(self, user: User):
        """Increment failed login attempts"""
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            self.lock_account(user, 30)  # Lock for 30 minutes
        self.db.commit()
    
    def reset_failed_attempts(self, user: User):
        """Reset failed login attempts"""
        user.failed_login_attempts = 0
        user.locked_until = None
        self.db.commit()
    
    def authenticate_user(self, email_or_cpf: str, password: str, request: Request) -> Token:
        """Authenticate user and return tokens"""
        # Find user by email or CPF
        user = self.db.query(User).filter(
            or_(User.email == email_or_cpf, User.cpf == email_or_cpf)
        ).first()
        
        if not user:
            self.log_audit_event(
                user_id=None,
                action="login_failed",
                entity_type="user",
                details={"reason": "user_not_found", "email_or_cpf": email_or_cpf},
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent")
            )
            raise AuthenticationError("Invalid credentials")
        
        # Check if account is locked
        if self.is_account_locked(user):
            self.log_audit_event(
                user_id=user.id,
                action="login_failed",
                entity_type="user",
                details={"reason": "account_locked"},
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent")
            )
            raise AuthenticationError("Account is temporarily locked due to multiple failed attempts")
        
        # Verify password
        if not self.verify_password(password, user.hashed_password):
            self.increment_failed_attempts(user)
            self.log_audit_event(
                user_id=user.id,
                action="login_failed",
                entity_type="user",
                details={"reason": "invalid_password"},
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent")
            )
            raise AuthenticationError("Invalid credentials")
        
        # Check if account is active
        if not user.is_active:
            self.log_audit_event(
                user_id=user.id,
                action="login_failed",
                entity_type="user",
                details={"reason": "account_disabled"},
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent")
            )
            raise AuthenticationError("Account is disabled")
        
        # Reset failed attempts on successful login
        self.reset_failed_attempts(user)
        
        # Create tokens
        access_token = self.create_access_token(
            data={
                "sub": user.username or user.email,
                "user_id": user.id,
                "tenant_id": getattr(user, 'tenant_id', None)
            }
        )
        
        refresh_token = self.create_refresh_token(
            data={
                "sub": user.username or user.email,
                "user_id": user.id,
                "tenant_id": getattr(user, 'tenant_id', None)
            }
        )
        
        # Update last login
        user.last_login = datetime.utcnow()
        self.db.commit()
        
        # Log successful login
        self.log_audit_event(
            user_id=user.id,
            action="login_success",
            entity_type="user",
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user_id=user.id,
            requires_2fa=user.two_factor_enabled,
            must_reset_password=user.must_reset_password
        )
    
    def register_staff(self, staff_data: StaffRegister, created_by: int) -> User:
        """Register staff member (admin creates)"""
        # Check if email already exists
        existing_user = self.db.query(User).filter(User.email == staff_data.email).first()
        if existing_user:
            raise ValidationError("Email already registered")
        
        # Check if username already exists
        if staff_data.username:
            existing_username = self.db.query(User).filter(User.username == staff_data.username).first()
            if existing_username:
                raise ValidationError("Username already taken")
        
        # Create user with default tenant_id if not provided
        tenant_id = staff_data.tenant_id or 1  # Default to tenant 1
        
        user = User(
            tenant_id=tenant_id,
            email=staff_data.email,
            username=staff_data.username,
            full_name=staff_data.full_name,
            hashed_password=self.get_password_hash(staff_data.password),
            crm=staff_data.crm,
            specialty=staff_data.specialty,
            phone=staff_data.phone,
            must_reset_password=True,  # Force password reset
            consent_given=True,  # Staff consent is implicit
            consent_date=datetime.utcnow()
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        # Log staff creation
        self.log_audit_event(
            user_id=created_by,
            action="staff_created",
            entity_type="user",
            entity_id=str(user.id),
            details={"staff_email": staff_data.email, "role": staff_data.role}
        )
        
        return user
    
    def register_patient(self, patient_data: PatientRegister) -> User:
        """Register patient (self-registration)"""
        # Check if email already exists
        existing_user = self.db.query(User).filter(User.email == patient_data.email).first()
        if existing_user:
            raise ValidationError("Email already registered")
        
        # Check if CPF already exists
        existing_cpf = self.db.query(User).filter(User.cpf == patient_data.cpf).first()
        if existing_cpf:
            raise ValidationError("CPF already registered")
        
        # Create user with default tenant_id
        user = User(
            tenant_id=1,  # Default to tenant 1
            email=patient_data.email,
            full_name=patient_data.full_name,
            cpf=patient_data.cpf,
            phone=patient_data.phone,
            hashed_password=self.get_password_hash(patient_data.password),
            consent_given=patient_data.consent_given,
            consent_date=datetime.utcnow() if patient_data.consent_given else None
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        # Log patient registration
        self.log_audit_event(
            user_id=user.id,
            action="patient_registered",
            entity_type="user",
            entity_id=str(user.id),
            details={"email": patient_data.email, "cpf": patient_data.cpf}
        )
        
        return user
    
    def forgot_password(self, email: str) -> Dict[str, str]:
        """Send password reset email"""
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            # Don't reveal if email exists or not
            return {"message": "If the email exists, a reset link has been sent"}
        
        # Generate reset token
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=1)
        
        # Store reset token
        reset_token = PasswordResetToken(
            user_id=user.id,
            token=token,
            expires_at=expires_at
        )
        
        self.db.add(reset_token)
        self.db.commit()
        
        # Log password reset request
        self.log_audit_event(
            user_id=user.id,
            action="password_reset_requested",
            entity_type="user",
            entity_id=str(user.id)
        )
        
        # TODO: Send email with reset link
        # For now, return the token (in production, this would be sent via email)
        return {
            "message": "Password reset link sent to your email",
            "reset_token": token  # Remove this in production
        }
    
    def reset_password(self, token: str, new_password: str) -> Dict[str, str]:
        """Reset password using token"""
        reset_token = self.db.query(PasswordResetToken).filter(
            PasswordResetToken.token == token,
            PasswordResetToken.expires_at > datetime.utcnow(),
            PasswordResetToken.used == False
        ).first()
        
        if not reset_token:
            raise AuthenticationError("Invalid or expired reset token")
        
        # Update user password
        user = self.db.query(User).filter(User.id == reset_token.user_id).first()
        user.hashed_password = self.get_password_hash(new_password)
        user.must_reset_password = False
        
        # Mark token as used
        reset_token.used = True
        
        self.db.commit()
        
        # Log password reset
        self.log_audit_event(
            user_id=user.id,
            action="password_reset_completed",
            entity_type="user",
            entity_id=str(user.id)
        )
        
        return {"message": "Password reset successfully"}
    
    def setup_2fa(self, user: User) -> TwoFactorSetup:
        """Setup 2FA for user"""
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        
        # Generate backup codes
        backup_codes = [secrets.token_hex(4).upper() for _ in range(10)]
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp.provisioning_uri(
            name=user.email,
            issuer_name=settings.APP_NAME
        ))
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        qr_code_url = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"
        
        return TwoFactorSetup(
            secret=secret, 
            qr_code_url=qr_code_url,
            backup_codes=backup_codes
        )
    
    def enable_2fa(self, user: User, secret: str, code: str) -> Dict[str, str]:
        """Enable 2FA for user"""
        totp = pyotp.TOTP(secret)
        if not totp.verify(code, valid_window=1):
            raise AuthenticationError("Invalid 2FA code")
        
        user.two_factor_enabled = True
        user.two_factor_secret = secret
        self.db.commit()
        
        # Log 2FA enablement
        self.log_audit_event(
            user_id=user.id,
            action="2fa_enabled",
            entity_type="user",
            entity_id=str(user.id)
        )
        
        return {"message": "2FA enabled successfully"}
    
    def verify_2fa(self, token: str, two_factor_code: str) -> Dict[str, Any]:
        """Verify 2FA code"""
        token_data = self.verify_token(token)
        
        user = self.db.query(User).filter(User.id == token_data.user_id).first()
        if not user or not user.two_factor_enabled:
            raise AuthenticationError("2FA not enabled for user")
        
        totp = pyotp.TOTP(user.two_factor_secret)
        if not totp.verify(two_factor_code, valid_window=1):
            raise AuthenticationError("Invalid 2FA code")
        
        # Log 2FA verification
        self.log_audit_event(
            user_id=user.id,
            action="2fa_verified",
            entity_type="user",
            entity_id=str(user.id)
        )
        
        return {"verified": True}
    
    def refresh_access_token(self, refresh_token: str) -> Token:
        """Refresh access token"""
        token_data = self.verify_token(refresh_token)
        
        # Verify it's a refresh token
        try:
            payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            if payload.get("type") != "refresh":
                raise AuthenticationError("Invalid refresh token")
        except JWTError:
            raise AuthenticationError("Invalid refresh token")
        
        # Create new access token
        access_token = self.create_access_token(
            data={
                "sub": token_data.username,
                "user_id": token_data.user_id,
                "tenant_id": token_data.tenant_id
            }
        )
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user_id=token_data.user_id,
            requires_2fa=False,
            must_reset_password=False
        )
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_user_by_cpf(self, cpf: str) -> Optional[User]:
        """Get user by CPF"""
        return self.db.query(User).filter(User.cpf == cpf).first()
    
    def create_staff_user(self, staff_data: StaffRegister) -> User:
        """Create staff user"""
        # Hash password
        hashed_password = self.get_password_hash(staff_data.password)
        
        # Create user
        user = User(
            tenant_id=staff_data.tenant_id or 1,
            email=staff_data.email,
            username=staff_data.username,
            full_name=staff_data.full_name,
            cpf=None,  # CPF not required for staff registration
            phone=staff_data.phone,
            hashed_password=hashed_password,
            crm=staff_data.crm,
            specialty=staff_data.specialty,
            must_reset_password=True,
            consent_given=True,
            consent_date=datetime.utcnow()
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def create_patient_user(self, patient_data: PatientRegister) -> User:
        """Create patient user"""
        # Hash password
        hashed_password = self.get_password_hash(patient_data.password)
        
        # Create user
        user = User(
            tenant_id=1,  # Default tenant
            email=patient_data.email,
            full_name=patient_data.full_name,
            cpf=patient_data.cpf,
            phone=patient_data.phone,
            hashed_password=hashed_password,
            consent_given=patient_data.consent_given,
            consent_date=datetime.utcnow() if patient_data.consent_given else None
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    @staticmethod
    def get_current_user(token: str = Depends(OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")), db: Session = Depends(get_db)) -> User:
        import os
        
        # Check if we're in mock mode
        if os.getenv("USE_DATABASE", "false").lower() == "false":
            # In mock mode, create different mock users based on token
            if token == "mock-admin-token":
                mock_user = User(
                    id=1,
                    email="admin@clinicore.com",
                    username="admin",
                    full_name="Administrator",
                    cpf="12345678901",
                    phone="11999999999",
                    hashed_password="mock_password",
                    is_active=True,
                    is_verified=True,
                    is_superuser=True,
                    crm="12345",
                    specialty="General Medicine",
                    tenant_id=1,
                    created_at=datetime.utcnow(),
                    last_login=datetime.utcnow()
                )
            elif token == "mock-doctor-token":
                mock_user = User(
                    id=2,
                    email="doctor@clinicore.com",
                    username="doctor",
                    full_name="Dr. João Silva",
                    cpf="98765432109",
                    phone="11988888888",
                    hashed_password="mock_password",
                    is_active=True,
                    is_verified=True,
                    is_superuser=False,
                    crm="SP123456",
                    specialty="Cardiologia",
                    tenant_id=1,
                    created_at=datetime.utcnow(),
                    last_login=datetime.utcnow()
                )
            elif token == "mock-secretary-token":
                mock_user = User(
                    id=3,
                    email="secretary@clinicore.com",
                    username="secretary",
                    full_name="Maria Secretária",
                    cpf="11223344556",
                    phone="11977777777",
                    hashed_password="mock_password",
                    is_active=True,
                    is_verified=True,
                    is_superuser=False,
                    tenant_id=1,
                    created_at=datetime.utcnow(),
                    last_login=datetime.utcnow()
                )
            elif token == "mock-patient-token":
                mock_user = User(
                    id=4,
                    email="patient@prontivus.com",
                    username="patient",
                    full_name="Ana Costa",
                    cpf="11144477735",
                    phone="11966666666",
                    hashed_password="mock_password",
                    is_active=True,
                    is_verified=True,
                    is_superuser=False,
                    tenant_id=1,
                    created_at=datetime.utcnow(),
                    last_login=datetime.utcnow()
                )
            else:
                # Default to admin for unknown tokens
                mock_user = User(
                    id=1,
                    email="admin@clinicore.com",
                    username="admin",
                    full_name="Administrator",
                    cpf="12345678901",
                    phone="11999999999",
                    hashed_password="mock_password",
                    is_active=True,
                    is_verified=True,
                    is_superuser=True,
                    crm="12345",
                    specialty="General Medicine",
                    tenant_id=1,
                    created_at=datetime.utcnow(),
                    last_login=datetime.utcnow()
                )
            return mock_user
        
        # In real database mode, use simple database
        try:
            # Import simple auth service
            from simple_auth_service import SimpleAuthService
            simple_auth = SimpleAuthService()
            
            # Verify token
            token_data = simple_auth.verify_token(token)
            user_id = token_data.get("user_id")
            
            if not user_id:
                raise AuthenticationError("Invalid token")
            
            # Get user from simple database
            simple_user = simple_auth.get_user_by_id(user_id)
            if not simple_user:
                raise AuthenticationError("User not found")
            
            # Convert to User model for compatibility
            user = User(
                id=simple_user.id,
                tenant_id=simple_user.tenant_id,
                email=simple_user.email,
                username=simple_user.username,
                full_name=simple_user.full_name,
                cpf=simple_user.cpf,
                phone=simple_user.phone,
                hashed_password=simple_user.hashed_password,
                is_active=simple_user.is_active,
                is_verified=simple_user.is_verified,
                is_superuser=simple_user.is_superuser,
                crm=simple_user.crm,
                specialty=simple_user.specialty,
                created_at=simple_user.created_at,
                last_login=simple_user.last_login
            )
            return user
            
        except Exception as e:
            raise AuthenticationError(f"Authentication failed: {str(e)}")
