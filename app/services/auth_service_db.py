"""
Real authentication service with database integration
"""

from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi import Request, HTTPException, status
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import bcrypt
import jwt
import secrets
import pyotp
import qrcode
import io
import base64
from passlib.context import CryptContext

from app.core.config import settings
from app.models.user import User, Role, UserRole, TwoFactorToken, PasswordResetToken
from app.models.tenant import Tenant
from app.models.audit import AuditLog, AuditAction
from app.schemas.auth import (
    UserLogin, StaffRegister, PatientRegister, Token, 
    ForgotPassword, ResetPassword, TwoFactorSetup, TwoFactorVerify
)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthServiceDB:
    """Real authentication service with database integration"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            if payload.get("type") != token_type:
                return None
            return payload
        except jwt.PyJWTError:
            return None
    
    def log_audit_event(
        self,
        user_id: Optional[int],
        action: AuditAction,
        entity_type: str,
        entity_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        risk_level: str = "low"
    ):
        """Log audit event"""
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            risk_level=risk_level
        )
        self.db.add(audit_log)
        self.db.commit()
    
    def is_account_locked(self, user: User) -> bool:
        """Check if account is locked"""
        if user.locked_until and user.locked_until > datetime.utcnow():
            return True
        return False
    
    def lock_account(self, user: User, minutes: int = 30):
        """Lock account for specified minutes"""
        user.locked_until = datetime.utcnow() + timedelta(minutes=minutes)
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
                action=AuditAction.LOGIN_FAILED,
                entity_type="user",
                details={"reason": "user_not_found", "email_or_cpf": email_or_cpf},
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
                success=False,
                risk_level="medium"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Check if account is locked
        if self.is_account_locked(user):
            self.log_audit_event(
                user_id=user.id,
                action=AuditAction.LOGIN_FAILED,
                entity_type="user",
                details={"reason": "account_locked"},
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
                success=False,
                risk_level="high"
            )
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Account is temporarily locked due to multiple failed attempts"
            )
        
        # Verify password
        if not self.verify_password(password, user.hashed_password):
            self.increment_failed_attempts(user)
            self.log_audit_event(
                user_id=user.id,
                action=AuditAction.LOGIN_FAILED,
                entity_type="user",
                details={"reason": "invalid_password"},
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
                success=False,
                risk_level="medium"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Check if account is active
        if not user.is_active:
            self.log_audit_event(
                user_id=user.id,
                action=AuditAction.LOGIN_FAILED,
                entity_type="user",
                details={"reason": "account_disabled"},
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
                success=False,
                risk_level="medium"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is disabled"
            )
        
        # Reset failed attempts on successful login
        self.reset_failed_attempts(user)
        
        # Get user's primary role
        user_role = None
        user_type = "patient"  # Default to patient
        
        if user.roles:
            # Get the first role (users typically have one primary role)
            primary_role = user.roles[0]
            user_role = primary_role.role.name if primary_role.role else None
            user_type = "staff"  # If user has roles, they're staff
        
        # Create tokens
        access_token = self.create_access_token(
            data={
                "sub": user.username or user.email,
                "user_id": user.id,
                "tenant_id": user.tenant_id
            }
        )
        
        refresh_token = self.create_refresh_token(
            data={
                "sub": user.username or user.email,
                "user_id": user.id,
                "tenant_id": user.tenant_id
            }
        )
        
        # Update last login
        user.last_login = datetime.utcnow()
        self.db.commit()
        
        # Log successful login
        self.log_audit_event(
            user_id=user.id,
            action=AuditAction.LOGIN_SUCCESS,
            entity_type="user",
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            success=True,
            risk_level="low"
        )
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user_id=user.id,
            user_role=user_role,
            user_type=user_type,
            requires_2fa=user.two_factor_enabled,
            must_reset_password=user.must_reset_password
        )
    
    def register_staff(self, staff_data: StaffRegister, created_by: int) -> User:
        """Register new staff member"""
        # Check if user already exists
        existing_user = self.db.query(User).filter(
            or_(User.email == staff_data.email, User.cpf == staff_data.cpf)
        ).first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email or CPF already exists"
            )
        
        # Hash password
        hashed_password = self.hash_password(staff_data.password)
        
        # Create user
        user = User(
            email=staff_data.email,
            username=staff_data.username,
            full_name=staff_data.full_name,
            cpf=staff_data.cpf,
            phone=staff_data.phone,
            hashed_password=hashed_password,
            crm=staff_data.crm,
            specialty=staff_data.specialty,
            tenant_id=staff_data.tenant_id,
            must_reset_password=True,  # Force password reset on first login
            consent_given=True,
            consent_date=datetime.utcnow()
        )
        
        self.db.add(user)
        self.db.flush()  # Get the user ID
        
        # Assign role
        role = self.db.query(Role).filter(Role.name == staff_data.role).first()
        if role:
            user_role = UserRole(
                user_id=user.id,
                role_id=role.id,
                tenant_id=staff_data.tenant_id
            )
            self.db.add(user_role)
        
        self.db.commit()
        
        # Log registration
        self.log_audit_event(
            user_id=created_by,
            action=AuditAction.USER_CREATED,
            entity_type="user",
            entity_id=str(user.id),
            details={"new_user_email": user.email, "role": staff_data.role},
            success=True
        )
        
        return user
    
    def register_patient(self, patient_data: PatientRegister) -> User:
        """Register new patient"""
        # Check if user already exists
        existing_user = self.db.query(User).filter(
            or_(User.email == patient_data.email, User.cpf == patient_data.cpf)
        ).first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email or CPF already exists"
            )
        
        # Hash password
        hashed_password = self.hash_password(patient_data.password)
        
        # Create user
        user = User(
            email=patient_data.email,
            full_name=patient_data.full_name,
            cpf=patient_data.cpf,
            phone=patient_data.phone,
            hashed_password=hashed_password,
            consent_given=patient_data.consent_given,
            consent_date=datetime.utcnow() if patient_data.consent_given else None
        )
        
        self.db.add(user)
        self.db.flush()  # Get the user ID
        
        # Assign patient role
        role = self.db.query(Role).filter(Role.name == "patient").first()
        if role:
            user_role = UserRole(
                user_id=user.id,
                role_id=role.id
            )
            self.db.add(user_role)
        
        self.db.commit()
        
        # Log registration
        self.log_audit_event(
            user_id=user.id,
            action=AuditAction.USER_CREATED,
            entity_type="user",
            entity_id=str(user.id),
            details={"user_type": "patient", "email": user.email},
            success=True
        )
        
        return user
    
    def forgot_password(self, email: str) -> Dict[str, str]:
        """Initiate password reset"""
        user = self.db.query(User).filter(User.email == email).first()
        
        if not user:
            # Don't reveal if user exists or not
            return {"message": "If the email exists, a password reset link has been sent"}
        
        # Create reset token
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=1)
        
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
            action=AuditAction.PASSWORD_RESET,
            entity_type="user",
            entity_id=str(user.id),
            details={"email": email},
            success=True
        )
        
        # TODO: Send email with reset link
        # For now, return the token (in production, send via email)
        return {
            "message": "Password reset link sent to your email",
            "token": token  # Remove this in production
        }
    
    def reset_password(self, token: str, new_password: str) -> Dict[str, str]:
        """Reset password using token"""
        reset_token = self.db.query(PasswordResetToken).filter(
            PasswordResetToken.token == token,
            PasswordResetToken.expires_at > datetime.utcnow(),
            PasswordResetToken.used == False
        ).first()
        
        if not reset_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        # Get user
        user = self.db.query(User).filter(User.id == reset_token.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User not found"
            )
        
        # Update password
        user.hashed_password = self.hash_password(new_password)
        user.must_reset_password = False
        user.failed_login_attempts = 0
        user.locked_until = None
        
        # Mark token as used
        reset_token.used = True
        
        self.db.commit()
        
        # Log password reset
        self.log_audit_event(
            user_id=user.id,
            action=AuditAction.PASSWORD_CHANGE,
            entity_type="user",
            entity_id=str(user.id),
            success=True
        )
        
        return {"message": "Password reset successfully"}
    
    def get_current_user(self, token: str) -> Optional[User]:
        """Get current user from token"""
        payload = self.verify_token(token)
        if not payload:
            return None
        
        user_id = payload.get("user_id")
        if not user_id:
            return None
        
        return self.db.query(User).filter(User.id == user_id).first()
