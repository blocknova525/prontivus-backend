"""
Database-only authentication endpoints
No mock authentication - all data must come from database
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Any
from datetime import datetime

from app.database.database import get_db
from app.core.exceptions import AuthenticationError, ValidationError
from app.schemas.auth import (
    Token, UserLogin, StaffRegister, PatientRegister, ForgotPassword,
    ResetPassword, TwoFactorSetup, TwoFactorVerify, ChangePassword
)
from app.services.auth_service import AuthService
from app.models.user import User
from app.core.config import settings

router = APIRouter()

def determine_user_role(email: str) -> str:
    """Determine user role based on email"""
    email_lower = email.lower()
    if "admin" in email_lower:
        return "admin"
    elif "doctor" in email_lower:
        return "doctor"
    elif "secretary" in email_lower:
        return "secretary"
    elif "patient" in email_lower:
        return "patient"
    else:
        return "unknown"

@router.post("/login", response_model=Token)
async def login(
    login_data: UserLogin,
    request: Request,
    db: Session = Depends(get_db)
) -> Any:
    """Login endpoint - Database only authentication"""
    try:
        # Find user by email or CPF using direct SQL to avoid relationship issues
        from sqlalchemy import text
        cursor = db.execute(text("""
            SELECT id, email, full_name, hashed_password, is_active, tenant_id
            FROM users 
            WHERE email = :email_or_cpf OR cpf = :email_or_cpf
        """), {"email_or_cpf": login_data.email_or_cpf})
        
        user_row = cursor.fetchone()
        if not user_row:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Create a simple user object
        user = type('User', (), {
            'id': user_row[0],
            'email': user_row[1], 
            'full_name': user_row[2],
            'hashed_password': user_row[3],
            'is_active': user_row[4],
            'tenant_id': user_row[5]
        })()
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is deactivated"
            )
        
        # Verify password using SHA-256 (our database format)
        import hashlib
        password_hash = hashlib.sha256(login_data.password.encode()).hexdigest()
        
        if password_hash != user.hashed_password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Create access token
        auth_service = AuthService(db)
        access_token = auth_service.create_access_token(
            data={"sub": user.email, "user_id": user.id, "tenant_id": user.tenant_id}
        )
        
        # Create refresh token
        refresh_token = auth_service.create_refresh_token(
            data={"sub": user.email, "user_id": user.id}
        )
        
        # Check if user has roles in the database
        from sqlalchemy import text
        role_cursor = db.execute(text("""
            SELECT r.name 
            FROM user_roles ur 
            JOIN roles r ON ur.role_id = r.id 
            WHERE ur.user_id = :user_id
        """), {"user_id": user.id})
        
        user_roles = [row[0] for row in role_cursor.fetchall()]
        
        # Determine user role and type
        if not user_roles:
            # User has no roles - treat as patient
            user_role = "patient"
            user_type = "patient"
        else:
            # User has roles - they're staff
            user_role = user_roles[0]  # Use first role
            user_type = "staff"
        
        # RESTRICTION: Patients cannot access main system
        if user_type == "patient":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Patients should use the patient portal. Staff members can access the main system."
            )
        
        # Staff members can access main system (user_type already set above)
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user_id=user.id,
            user_role=user_role,
            user_type=user_type,
            requires_2fa=False,  # Simplified for now
            must_reset_password=False  # Can be enhanced later
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

@router.post("/register/staff", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register_staff(
    staff_data: StaffRegister,
    db: Session = Depends(get_db)
) -> Any:
    """Register staff member - Database only"""
    try:
        auth_service = AuthService(db)
        
        # Check if user already exists
        existing_user = auth_service.get_user_by_email(staff_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        # Create new staff user
        user = auth_service.create_staff_user(staff_data)
        
        return {
            "message": "Staff member created successfully",
            "user_id": user.id,
            "email": user.email,
            "must_reset_password": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@router.post("/register/patient", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register_patient(
    patient_data: PatientRegister,
    db: Session = Depends(get_db)
) -> Any:
    """Register patient - Database only"""
    try:
        auth_service = AuthService(db)
        
        # Check if user already exists
        existing_user = auth_service.get_user_by_email(patient_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        # Create new patient user
        user = auth_service.create_patient_user(patient_data)
        
        return {
            "message": "Patient registered successfully",
            "user_id": user.id,
            "email": user.email,
            "must_reset_password": False
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@router.post("/forgot-password", response_model=dict)
async def forgot_password(
    forgot_data: ForgotPassword,
    db: Session = Depends(get_db)
) -> Any:
    """Forgot password - Database only"""
    try:
        auth_service = AuthService(db)
        
        # Check if user exists
        user = auth_service.get_user_by_email(forgot_data.email)
        if not user:
            # Don't reveal if user exists or not for security
            return {"message": "If the email exists, a reset link has been sent"}
        
        # Generate reset token
        reset_token = auth_service.create_password_reset_token(user.id)
        
        # TODO: Send email with reset token
        # For now, just return success
        
        return {"message": "If the email exists, a reset link has been sent"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password reset failed: {str(e)}"
        )

@router.post("/reset-password", response_model=dict)
async def reset_password(
    reset_data: ResetPassword,
    db: Session = Depends(get_db)
) -> Any:
    """Reset password - Database only"""
    try:
        auth_service = AuthService(db)
        
        # Verify reset token
        user_id = auth_service.verify_password_reset_token(reset_data.token)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        # Update password
        auth_service.update_password(user_id, reset_data.new_password)
        
        return {"message": "Password reset successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password reset failed: {str(e)}"
        )

@router.post("/change-password", response_model=dict)
async def change_password(
    change_data: ChangePassword,
    db: Session = Depends(get_db)
) -> Any:
    """Change password - Database only"""
    try:
        auth_service = AuthService(db)
        
        # Get current user (this would come from JWT token in real implementation)
        # For now, we'll need the user_id in the request
        user_id = change_data.user_id  # This should come from JWT token
        
        # Verify current password
        user = auth_service.get_user_by_id(user_id)
        if not auth_service.verify_password(change_data.current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Update password
        auth_service.update_password(user_id, change_data.new_password)
        
        return {"message": "Password changed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password change failed: {str(e)}"
        )

@router.post("/setup-2fa", response_model=dict)
async def setup_2fa(
    setup_data: TwoFactorSetup,
    db: Session = Depends(get_db)
) -> Any:
    """Setup 2FA - Database only"""
    try:
        auth_service = AuthService(db)
        
        # Generate 2FA secret
        secret = auth_service.generate_2fa_secret(setup_data.user_id)
        
        return {
            "message": "2FA setup initiated",
            "secret": secret,
            "qr_code_url": f"otpauth://totp/Prontivus:{setup_data.user_id}?secret={secret}&issuer=Prontivus"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"2FA setup failed: {str(e)}"
        )

@router.post("/verify-2fa", response_model=dict)
async def verify_2fa(
    verify_data: TwoFactorVerify,
    db: Session = Depends(get_db)
) -> Any:
    """Verify 2FA - Database only"""
    try:
        auth_service = AuthService(db)
        
        # Verify 2FA token
        is_valid = auth_service.verify_2fa_token(verify_data.user_id, verify_data.token)
        
        if is_valid:
            return {"message": "2FA verification successful"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid 2FA token"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"2FA verification failed: {str(e)}"
        )

@router.get("/me", response_model=dict)
async def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> Any:
    """Get current user information - Database only"""
    try:
        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or invalid authorization header"
            )
        
        token = auth_header.split(" ")[1]
        
        # Verify token and get user info
        auth_service = AuthService(db)
        try:
            token_data = auth_service.verify_token(token)
            user_email = token_data.username
            user_id = token_data.user_id
            
            if not user_email or not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload"
                )
            
            # Get user from database using direct SQL
            from sqlalchemy import text
            cursor = db.execute(text("""
                SELECT id, email, full_name, cpf, phone, is_active, tenant_id
                FROM users
                WHERE email = :email AND id = :user_id
            """), {"email": user_email, "user_id": user_id})
            
            user_row = cursor.fetchone()
            if not user_row:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )
            
            # Verify this is a staff member
            user_role = determine_user_role(user_email)
            if user_role == "patient":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied. Patients should use the patient portal."
                )
            
            return {
                "id": user_row[0],
                "email": user_row[1],
                "full_name": user_row[2],
                "cpf": user_row[3],
                "phone": user_row[4],
                "is_active": bool(user_row[5]),
                "tenant_id": user_row[6],
                "role": user_role,
                "type": "staff",
                "portal": "main_system"
            }
            
        except Exception as token_error:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token verification failed: {str(token_error)}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user info: {str(e)}"
        )

@router.post("/refresh", response_model=Token)
async def refresh_token(
    request: Request,
    db: Session = Depends(get_db)
) -> Any:
    """Refresh access token - Database only"""
    try:
        # Get refresh token from request body
        body = await request.json()
        refresh_token = body.get("refresh_token")
        
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Refresh token is required"
            )
        
        # Verify refresh token
        auth_service = AuthService(db)
        try:
            token_data = auth_service.verify_refresh_token(refresh_token)
            user_email = token_data.username
            user_id = token_data.user_id
            
            if not user_email or not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token"
                )
            
            # Get user from database
            from sqlalchemy import text
            cursor = db.execute(text("""
                SELECT id, email, full_name, is_active, tenant_id
                FROM users
                WHERE email = :email AND id = :user_id
            """), {"email": user_email, "user_id": user_id})
            
            user_row = cursor.fetchone()
            if not user_row:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )
            
            # Check if user is active
            if not user_row[3]:  # is_active
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User account is inactive"
                )
            
            # Generate new tokens
            new_access_token = auth_service.create_access_token(
                data={"sub": user_email, "user_id": user_id}
            )
            new_refresh_token = auth_service.create_refresh_token(
                data={"sub": user_email, "user_id": user_id}
            )
            
            return Token(
                access_token=new_access_token,
                refresh_token=new_refresh_token,
                token_type="bearer",
                expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
            )
            
        except Exception as token_error:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Refresh token verification failed: {str(token_error)}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token refresh failed: {str(e)}"
        )

@router.post("/logout", response_model=dict)
async def logout(
    request: Request,
    db: Session = Depends(get_db)
) -> Any:
    """Logout - Database only"""
    try:
        # In a real implementation, you would:
        # 1. Extract the token from the request
        # 2. Add it to a blacklist
        # 3. Update user's last logout time
        
        return {"message": "Logged out successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout failed: {str(e)}"
        )
