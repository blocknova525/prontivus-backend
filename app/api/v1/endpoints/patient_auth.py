"""
Patient Portal Authentication Endpoints
Patients can only access the patient portal, not the main system
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Any
from datetime import datetime

from app.database.database import get_db
from app.core.exceptions import AuthenticationError, ValidationError
from app.schemas.auth import Token, UserLogin
from app.services.auth_service import AuthService
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
async def patient_login(
    login_data: UserLogin,
    request: Request,
    db: Session = Depends(get_db)
) -> Any:
    """Patient portal login - Only patients allowed"""
    try:
        # Find user by email or CPF using direct SQL
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
            # User has roles - check if they have patient role
            user_role = user_roles[0]  # Use first role
            user_type = "staff"
        
        # RESTRICTION: Only patients can access patient portal
        if user_role != "patient":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. This portal is only for patients. Staff members should use the main system."
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

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user_id=user.id,
            user_role="patient",
            user_type="patient",
            requires_2fa=False,
            must_reset_password=False
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

@router.get("/me", response_model=dict)
async def get_patient_info(
    request: Request,
    db: Session = Depends(get_db)
) -> Any:
    """Get current patient information - Patient portal only"""
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
            
            # Verify this is a patient
            user_role = determine_user_role(user_email)
            if user_role != "patient":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied. This endpoint is only for patients."
                )
            
            return {
                "id": user_row[0],
                "email": user_row[1],
                "full_name": user_row[2],
                "cpf": user_row[3],
                "phone": user_row[4],
                "is_active": bool(user_row[5]),
                "tenant_id": user_row[6],
                "role": "patient",
                "type": "patient",
                "portal": "patient_portal"
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
            detail=f"Failed to get patient info: {str(e)}"
        )

@router.put("/profile", response_model=dict)
async def update_patient_profile(
    profile_data: dict,
    request: Request,
    db: Session = Depends(get_db)
) -> Any:
    """Update patient profile information - Patient portal only"""
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
            
            # Verify this is a patient
            user_role = determine_user_role(user_email)
            if user_role != "patient":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied. This endpoint is only for patients."
                )
            
            # Update user profile in database
            from sqlalchemy import text
            update_fields = []
            update_values = {"user_id": user_id}
            
            # Build dynamic update query
            for field, value in profile_data.items():
                if field in ['full_name', 'email', 'phone', 'cpf', 'birth_date', 'gender', 'address', 'insurance_company', 'insurance_number']:
                    update_fields.append(f"{field} = :{field}")
                    update_values[field] = value
            
            if not update_fields:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No valid fields to update"
                )
            
            # Execute update
            update_query = f"""
                UPDATE users 
                SET {', '.join(update_fields)}
                WHERE id = :user_id
            """
            
            db.execute(text(update_query), update_values)
            db.commit()
            
            # Return updated profile
            cursor = db.execute(text("""
                SELECT id, email, full_name, cpf, phone, is_active, tenant_id
                FROM users
                WHERE id = :user_id
            """), {"user_id": user_id})
            
            user_row = cursor.fetchone()
            if not user_row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found after update"
                )
            
            return {
                "id": user_row[0],
                "email": user_row[1],
                "full_name": user_row[2],
                "cpf": user_row[3],
                "phone": user_row[4],
                "is_active": bool(user_row[5]),
                "tenant_id": user_row[6],
                "role": "patient",
                "type": "patient",
                "portal": "patient_portal",
                "message": "Profile updated successfully"
            }
            
        except Exception as token_error:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token verification failed: {str(token_error)}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update patient profile: {str(e)}"
        )

@router.post("/refresh", response_model=dict)
async def refresh_patient_token(
    request: Request,
    db: Session = Depends(get_db)
) -> Any:
    """Refresh patient access token"""
    try:
        # Extract refresh token from request body
        body = await request.json()
        refresh_token = body.get("refresh_token")
        
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Refresh token is required"
            )
        
        # Verify refresh token and get user info
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
            
            # Verify this is a patient
            user_role = determine_user_role(user_email)
            if user_role != "patient":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied. This endpoint is only for patients."
                )
            
            # Create new access token
            new_access_token = auth_service.create_access_token(
                data={"sub": user_email, "user_id": user_id, "tenant_id": token_data.tenant_id}
            )
            
            # Create new refresh token
            new_refresh_token = auth_service.create_refresh_token(
                data={"sub": user_email, "user_id": user_id}
            )
            
            return {
                "access_token": new_access_token,
                "refresh_token": new_refresh_token,
                "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                "user_id": user_id,
                "user_role": "patient",
                "user_type": "patient"
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
            detail=f"Token refresh failed: {str(e)}"
        )

@router.post("/logout", response_model=dict)
async def patient_logout(
    request: Request,
    db: Session = Depends(get_db)
) -> Any:
    """Patient portal logout"""
    try:
        # In a real implementation, you would:
        # 1. Extract the token from the request
        # 2. Add it to a blacklist
        # 3. Update user's last logout time
        
        return {"message": "Logged out successfully from patient portal"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout failed: {str(e)}"
        )
