"""
Authentication dependencies for API endpoints
"""

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, Union
import os

from app.database.database import get_db
from app.services.auth_service import AuthService
from app.api.v1.endpoints.auth_db_only import determine_user_role

# Security scheme for Bearer token
security = HTTPBearer()

def get_current_user_flexible(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> dict:
    """
    Flexible authentication dependency that works with both staff and patient tokens
    """
    try:
        token = credentials.credentials
        auth_service = AuthService(db)
        
        # Verify the token
        token_data = auth_service.verify_token(token)
        user_email = token_data.username
        user_id = token_data.user_id
        
        if not user_email or not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        # Get user from database using direct SQL to avoid ORM issues
        result = db.execute(
            text("SELECT id, email, full_name, cpf, phone, is_active, tenant_id FROM users WHERE id = :user_id"),
            {"user_id": user_id}
        ).fetchone()
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        # Check if user has roles in the database
        role_cursor = db.execute(text("""
            SELECT r.name 
            FROM user_roles ur 
            JOIN roles r ON ur.role_id = r.id 
            WHERE ur.user_id = :user_id
        """), {"user_id": user_id})
        
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
        
        # Create user object
        user_data = {
            "id": result[0],
            "email": result[1],
            "full_name": result[2],
            "cpf": result[3],
            "phone": result[4],
            "is_active": bool(result[5]),
            "tenant_id": result[6],
            "role": user_role,
            "type": user_type
        }
        
        return user_data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}"
        )

def get_current_staff_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> dict:
    """
    Authentication dependency specifically for staff users
    """
    user_data = get_current_user_flexible(request, credentials, db)
    
    # Ensure this is a staff member
    if user_data["type"] != "staff":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. This endpoint is only for staff members."
        )
    
    return user_data

def get_current_patient_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> dict:
    """
    Authentication dependency specifically for patient users
    """
    user_data = get_current_user_flexible(request, credentials, db)
    
    # Ensure this is a patient
    if user_data["type"] != "patient":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. This endpoint is only for patients."
        )
    
    return user_data
