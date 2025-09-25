"""
Real authentication endpoints with database integration
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Any

from app.database.database import get_db
from app.services.auth_service_db import AuthServiceDB
from app.schemas.auth import (
    UserLogin, StaffRegister, PatientRegister, Token,
    ForgotPassword, ResetPassword, TwoFactorSetup, TwoFactorVerify
)
from app.models.user import User

router = APIRouter()
security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    auth_service = AuthServiceDB(db)
    user = auth_service.get_current_user(credentials.credentials)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return user

@router.post("/login", response_model=Token)
async def login(
    login_data: UserLogin,
    request: Request,
    db: Session = Depends(get_db)
) -> Any:
    """Login endpoint with database integration"""
    try:
        auth_service = AuthServiceDB(db)
        token = auth_service.authenticate_user(
            email_or_cpf=login_data.email_or_cpf,
            password=login_data.password,
            request=request
        )
        return token
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

@router.post("/register/staff", response_model=dict)
async def register_staff(
    staff_data: StaffRegister,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Register new staff member (admin only)"""
    try:
        auth_service = AuthServiceDB(db)
        user = auth_service.register_staff(staff_data, current_user.id)
        
        return {
            "message": "Staff member registered successfully",
            "user_id": user.id,
            "email": user.email,
            "must_reset_password": user.must_reset_password
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@router.post("/register/patient", response_model=dict)
async def register_patient(
    patient_data: PatientRegister,
    db: Session = Depends(get_db)
) -> Any:
    """Register new patient (self-registration)"""
    try:
        auth_service = AuthServiceDB(db)
        user = auth_service.register_patient(patient_data)
        
        return {
            "message": "Patient registered successfully",
            "user_id": user.id,
            "email": user.email,
            "requires_verification": not user.is_verified
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
    """Initiate password reset"""
    try:
        auth_service = AuthServiceDB(db)
        result = auth_service.forgot_password(forgot_data.email)
        return result
    except HTTPException:
        raise
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
    """Reset password using token"""
    try:
        auth_service = AuthServiceDB(db)
        result = auth_service.reset_password(reset_data.token, reset_data.new_password)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password reset failed: {str(e)}"
        )

@router.get("/me", response_model=dict)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get current user information"""
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
        "last_login": current_user.last_login
    }

@router.post("/logout", response_model=dict)
async def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Logout endpoint"""
    # In a real implementation, you might want to blacklist the token
    # For now, we'll just return a success message
    return {"message": "Logged out successfully"}

@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db)
) -> Any:
    """Refresh access token"""
    try:
        auth_service = AuthServiceDB(db)
        payload = auth_service.verify_token(refresh_token, "refresh")
        
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Get user
        user_id = payload.get("user_id")
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Create new access token
        access_token = auth_service.create_access_token(
            data={
                "sub": user.username or user.email,
                "user_id": user.id,
                "tenant_id": user.tenant_id
            }
        )
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=30 * 60,  # 30 minutes
            user_id=user.id,
            requires_2fa=user.two_factor_enabled,
            must_reset_password=user.must_reset_password
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token refresh failed: {str(e)}"
        )
