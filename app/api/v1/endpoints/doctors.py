"""
Doctor endpoints for appointment scheduling
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database.database import get_db
from app.api.v1.dependencies.auth import get_current_user_flexible

router = APIRouter()

@router.get("/")
async def list_doctors(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_flexible),
):
    """List available doctors for appointment scheduling"""
    try:
        # Return mock doctor data
        doctors = [
            {"id": 1, "full_name": "Dr. Carlos Mendes", "specialty": "Cardiologia", "crm": "12345", "is_active": True},
            {"id": 2, "full_name": "Dr. João Silva", "specialty": "Clínica Geral", "crm": "23456", "is_active": True},
            {"id": 3, "full_name": "Dra. Maria Santos", "specialty": "Pediatria", "crm": "34567", "is_active": True},
            {"id": 4, "full_name": "Dr. Pedro Costa", "specialty": "Ortopedia", "crm": "45678", "is_active": True},
            {"id": 5, "full_name": "Dra. Ana Lima", "specialty": "Dermatologia", "crm": "56789", "is_active": True}
        ]
        return doctors
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving doctors: {str(e)}"
        )
