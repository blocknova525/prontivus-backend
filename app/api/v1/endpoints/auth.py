"""
Authentication endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Any

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

@router.post("/login", response_model=Token)
async def login(
    login_data: UserLogin,
    request: Request,
    db: Session = Depends(get_db)
) -> Any:
    """Login endpoint"""
    import os
    
    try:
        # Check if we're in mock mode
        if os.getenv("USE_DATABASE", "false").lower() == "false":
            # Mock login for development
            if login_data.email_or_cpf == "admin@prontivus.com" and login_data.password == "admin123":
                return Token(
                    access_token="mock-admin-token",
                    refresh_token="mock-refresh-token",
                    expires_in=1800,
                    user_id=1,
                    user_role="admin",
                    user_type="staff",
                    requires_2fa=False,
                    must_reset_password=False
                )
            elif login_data.email_or_cpf == "doctor@prontivus.com" and login_data.password == "doctor123":
                return Token(
                    access_token="mock-doctor-token",
                    refresh_token="mock-refresh-token",
                    expires_in=1800,
                    user_id=2,
                    user_role="doctor",
                    user_type="staff",
                    requires_2fa=False,
                    must_reset_password=False
                )
            elif login_data.email_or_cpf == "secretary@prontivus.com" and login_data.password == "secretary123":
                return Token(
                    access_token="mock-secretary-token",
                    refresh_token="mock-refresh-token",
                    expires_in=1800,
                    user_id=3,
                    user_role="secretary",
                    user_type="staff",
                    requires_2fa=False,
                    must_reset_password=False
                )
            elif login_data.email_or_cpf == "patient@prontivus.com" and login_data.password == "patient123":
                return Token(
                    access_token="mock-patient-token",
                    refresh_token="mock-refresh-token",
                    expires_in=1800,
                    user_id=4,
                    user_role="patient",
                    user_type="patient",
                    requires_2fa=False,
                    must_reset_password=False
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )
        
        # Real database mode - use simple auth service
        from simple_auth_service import SimpleAuthService
        simple_auth = SimpleAuthService()
        
        # Authenticate user
        user = simple_auth.authenticate_user(login_data.email_or_cpf, login_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Create token
        access_token = simple_auth.create_access_token(
            data={"sub": user.username, "user_id": user.id, "tenant_id": user.tenant_id}
        )
        
        # Determine user type and role
        user_role = "admin" if user.is_superuser else "doctor" if user.crm else "secretary"
        user_type = "staff"
        
        return Token(
            access_token=access_token,
            refresh_token="refresh-token",  # Simplified for now
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user_id=user.id,
            user_role=user_role,
            user_type=user_type,
            requires_2fa=False,
            must_reset_password=False
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.post("/register/staff", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register_staff(
    staff_data: StaffRegister,
    db: Session = Depends(get_db)
) -> Any:
    """Register staff member (admin creates)"""
    import os
    
    try:
        if os.getenv("USE_DATABASE", "false").lower() == "false":
            # Mock staff registration for development
            return {
                "message": "Staff member created successfully", 
                "user_id": 998,
                "email": staff_data.email,
                "must_reset_password": True
            }
        else:
            # Use real database
            auth_service = AuthService(db)
            # For now, use admin user ID (1) as creator
            user = auth_service.register_staff(staff_data, 1)
            return {"message": "Staff member created successfully", "user_id": user.id}
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.message
        )
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
    """Register patient (self-registration)"""
    import os
    
    try:
        if os.getenv("USE_DATABASE", "false").lower() == "false":
            # Mock patient registration for development
            return {
                "message": "Patient registered successfully", 
                "user_id": 999,
                "email": patient_data.email,
                "requires_verification": True
            }
        else:
            # Use real database
            auth_service = AuthService(db)
            user = auth_service.register_patient(patient_data)
            return {"message": "Patient registered successfully", "user_id": user.id}
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.message
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@router.post("/refresh", response_model=Token)
async def refresh_token(
    request_data: dict,
    db: Session = Depends(get_db)
) -> Any:
    """Refresh access token"""
    try:
        refresh_token = request_data.get("refresh_token")
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Refresh token is required"
            )
        
        auth_service = AuthService(db)
        token = auth_service.refresh_access_token(refresh_token)
        return token
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message
        )

@router.get("/me", response_model=dict)
async def get_current_user_info(
    current_user: User = Depends(AuthService.get_current_user)
) -> Any:
    """Get current user information"""
    import os
    
    # Determine user type and role
    user_role = None
    user_type = "patient"  # Default to patient
    
    # Check if we're in mock mode
    if os.getenv("USE_DATABASE", "false").lower() == "false":
        # In mock mode, determine role based on user data
        if current_user.id == 1 or (current_user.username and "admin" in current_user.username.lower()):
            user_role = "admin"
            user_type = "staff"
        elif current_user.id == 2 or current_user.crm:
            user_role = "doctor"
            user_type = "staff"
        elif current_user.id == 3 or (current_user.username and "secretary" in current_user.username.lower()):
            user_role = "secretary"
            user_type = "staff"
        elif current_user.id == 4 or (current_user.username and "patient" in current_user.username.lower()):
            user_role = "patient"
            user_type = "patient"
        elif current_user.username and "finance" in current_user.username.lower():
            user_role = "finance"
            user_type = "staff"
        else:
            # Default to admin for mock mode to allow access to all pages
            user_role = "admin"
            user_type = "staff"
    else:
        # In real database mode, check if user has roles (staff)
        if hasattr(current_user, 'roles') and current_user.roles:
            primary_role = current_user.roles[0] if current_user.roles else None
            user_role = primary_role.role.name if primary_role.role else None
            user_type = "staff"  # If user has roles, they're staff
    
    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "cpf": current_user.cpf,
        "phone": current_user.phone,
        "crm": current_user.crm,
        "specialty": current_user.specialty,
        "is_active": current_user.is_active,
        "is_verified": current_user.is_verified,
        "two_factor_enabled": current_user.two_factor_enabled,
        "must_reset_password": current_user.must_reset_password,
        "tenant_id": current_user.tenant_id,
        "created_at": current_user.created_at,
        "last_login": current_user.last_login,
        "user_type": user_type,
        "user_role": user_role
    }

@router.post("/logout")
async def logout(
    current_user: User = Depends(AuthService.get_current_user)
) -> Any:
    """Logout endpoint"""
    # In a real implementation, you would invalidate the token
    return {"message": "Successfully logged out"}

@router.post("/forgot-password")
async def forgot_password(
    forgot_data: ForgotPassword,
    db: Session = Depends(get_db)
) -> Any:
    """Send password reset email"""
    try:
        auth_service = AuthService(db)
        result = auth_service.forgot_password(forgot_data.email)
        return result
    except Exception as e:
        # Always return success to prevent email enumeration
        return {"message": "If the email exists, a reset link has been sent"}

@router.post("/reset-password")
async def reset_password(
    reset_data: ResetPassword,
    db: Session = Depends(get_db)
) -> Any:
    """Reset password using token"""
    try:
        auth_service = AuthService(db)
        result = auth_service.reset_password(reset_data.token, reset_data.new_password)
        return result
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message
        )

@router.post("/setup-2fa", response_model=TwoFactorSetup)
async def setup_2fa(
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Setup 2FA for user"""
    try:
        auth_service = AuthService(db)
        setup_data = auth_service.setup_2fa(current_user)
        return setup_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to setup 2FA"
        )

@router.post("/enable-2fa")
async def enable_2fa(
    secret: str,
    code: str,
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Enable 2FA for user"""
    try:
        auth_service = AuthService(db)
        result = auth_service.enable_2fa(current_user, secret, code)
        return result
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message
        )

@router.post("/verify-2fa")
async def verify_2fa(
    verify_data: TwoFactorVerify,
    db: Session = Depends(get_db)
) -> Any:
    """Verify 2FA code"""
    try:
        auth_service = AuthService(db)
        result = auth_service.verify_2fa(verify_data.token, verify_data.code)
        return result
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message
        )

@router.post("/change-password")
async def change_password(
    change_data: ChangePassword,
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Change user password"""
    try:
        auth_service = AuthService(db)
        
        # Verify current password
        if not auth_service.verify_password(change_data.current_password, current_user.hashed_password):
            raise AuthenticationError("Current password is incorrect")
        
        # Update password
        current_user.hashed_password = auth_service.get_password_hash(change_data.new_password)
        current_user.must_reset_password = False
        db.commit()
        
        # Log password change
        auth_service.log_audit_event(
            user_id=current_user.id,
            action="password_changed",
            entity_type="user",
            entity_id=str(current_user.id)
        )
        
        return {"message": "Password changed successfully"}
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message
        )
