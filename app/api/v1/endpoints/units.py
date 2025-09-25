"""
Unit endpoints
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

from app.database.database import get_db
from app.services.auth_service_db import AuthServiceDB as AuthService

router = APIRouter()


@router.get("/")
async def list_units(
    db: Session = Depends(get_db),
    current_user=Depends(AuthService.get_current_user),
):
    """List all units - mock implementation for now"""
    # Mock data for development
    return [
        {
            "id": 1,
            "name": "Clínica Central",
            "type": "Matriz",
            "status": "active",
            "address": "Rua das Flores, 123",
            "city": "São Paulo",
            "state": "SP",
            "zipCode": "01234-567",
            "phone": "(11) 99999-9999",
            "email": "central@clinica.com",
            "doctors": 15,
            "patients": 250,
            "appointments": 45,
            "createdAt": "2023-01-15T10:00:00Z",
            "lastSync": "2024-01-15T15:30:00Z"
        },
        {
            "id": 2,
            "name": "Filial Norte",
            "type": "Filial",
            "status": "active",
            "address": "Av. Paulista, 456",
            "city": "São Paulo",
            "state": "SP",
            "zipCode": "01310-100",
            "phone": "(11) 88888-8888",
            "email": "norte@clinica.com",
            "doctors": 8,
            "patients": 120,
            "appointments": 25,
            "createdAt": "2023-06-01T09:00:00Z",
            "lastSync": "2024-01-15T14:20:00Z"
        }
    ]


@router.get("/{unit_id}")
async def get_unit(
    unit_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(AuthService.get_current_user),
):
    """Get a specific unit - mock implementation for now"""
    return {
        "id": unit_id,
        "name": f"Unidade {unit_id}",
        "type": "Filial",
        "status": "active",
        "address": "Endereço Mock",
        "city": "São Paulo",
        "state": "SP",
        "zipCode": "00000-000",
        "phone": "(11) 00000-0000",
        "email": "mock@clinica.com",
        "doctors": 5,
        "patients": 50,
        "appointments": 10,
        "createdAt": "2023-01-01T00:00:00Z",
        "lastSync": "2024-01-01T00:00:00Z"
    }


@router.post("/")
async def create_unit(
    unit_data: dict,
    db: Session = Depends(get_db),
    current_user=Depends(AuthService.get_current_user),
):
    """Create a new unit - mock implementation for now"""
    return {
        "id": 999,
        "name": unit_data.get("name", "Nova Unidade"),
        "type": unit_data.get("type", "Filial"),
        "status": unit_data.get("status", "active"),
        "address": unit_data.get("address", ""),
        "city": unit_data.get("city", ""),
        "state": unit_data.get("state", ""),
        "zipCode": unit_data.get("zipCode", ""),
        "phone": unit_data.get("phone", ""),
        "email": unit_data.get("email", ""),
        "doctors": unit_data.get("doctors", 0),
        "patients": unit_data.get("patients", 0),
        "appointments": unit_data.get("appointments", 0),
        "createdAt": "2024-01-15T00:00:00Z",
        "lastSync": "2024-01-15T00:00:00Z"
    }


@router.put("/{unit_id}")
async def update_unit(
    unit_id: int,
    unit_data: dict,
    db: Session = Depends(get_db),
    current_user=Depends(AuthService.get_current_user),
):
    """Update a unit - mock implementation for now"""
    return {
        "id": unit_id,
        "name": unit_data.get("name", f"Unidade {unit_id} Atualizada"),
        "type": unit_data.get("type", "Filial"),
        "status": unit_data.get("status", "active"),
        "address": unit_data.get("address", ""),
        "city": unit_data.get("city", ""),
        "state": unit_data.get("state", ""),
        "zipCode": unit_data.get("zipCode", ""),
        "phone": unit_data.get("phone", ""),
        "email": unit_data.get("email", ""),
        "doctors": unit_data.get("doctors", 0),
        "patients": unit_data.get("patients", 0),
        "appointments": unit_data.get("appointments", 0),
        "createdAt": "2023-01-01T00:00:00Z",
        "lastSync": "2024-01-15T00:00:00Z"
    }


@router.delete("/{unit_id}")
async def delete_unit(
    unit_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(AuthService.get_current_user),
):
    """Delete a unit - mock implementation for now"""
    return {"success": True, "message": "Unit deleted successfully"}


@router.post("/{unit_id}/sync")
async def sync_unit(
    unit_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(AuthService.get_current_user),
):
    """Sync a unit - mock implementation for now"""
    return {
        "id": unit_id,
        "name": f"Unidade {unit_id}",
        "lastSync": "2024-01-15T16:00:00Z"
    }


@router.post("/{unit_id}/activate")
async def activate_unit(
    unit_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(AuthService.get_current_user),
):
    """Activate a unit - mock implementation for now"""
    return {
        "id": unit_id,
        "name": f"Unidade {unit_id}",
        "status": "active"
    }


@router.get("/statistics/overview")
async def get_unit_statistics(
    db: Session = Depends(get_db),
    current_user=Depends(AuthService.get_current_user),
):
    """Get unit statistics - mock implementation for now"""
    return {
        "totalUnits": 2,
        "totalDoctors": 23,
        "totalPatients": 370,
        "totalAppointments": 70
    }
