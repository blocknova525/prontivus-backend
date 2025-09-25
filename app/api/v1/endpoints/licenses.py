"""
License endpoints
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

from app.database.database import get_db
from app.schemas.license import License as LicenseSchema, LicenseCreate, LicenseUpdate, ActivationRequest
from app.services.license_service import LicenseService
from app.services.auth_service_db import AuthServiceDB as AuthService

router = APIRouter()


@router.get("/", response_model=List[LicenseSchema])
async def list_licenses(
    db: Session = Depends(get_db),
    current_user=Depends(AuthService.get_current_user),
):
    service = LicenseService(db)
    return service.list_licenses(tenant_id=getattr(current_user, "tenant_id", 0) or 0)


@router.get("/{license_id}", response_model=LicenseSchema)
async def get_license(
    license_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(AuthService.get_current_user),
):
    service = LicenseService(db)
    return service.get_license(license_id)


@router.post("/", response_model=LicenseSchema, status_code=status.HTTP_201_CREATED)
async def create_license(
    payload: LicenseCreate,
    db: Session = Depends(get_db),
    current_user=Depends(AuthService.get_current_user),
):
    service = LicenseService(db)
    return service.create_license(payload)


@router.put("/{license_id}", response_model=LicenseSchema)
async def update_license(
    license_id: int,
    payload: LicenseUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(AuthService.get_current_user),
):
    service = LicenseService(db)
    return service.update_license(license_id, payload)


@router.post("/{license_id}/activate")
async def activate_license(
    license_id: int,
    payload: ActivationRequest,
    db: Session = Depends(get_db),
    current_user=Depends(AuthService.get_current_user),
):
    service = LicenseService(db)
    return service.activate_license(license_id)


@router.delete("/{license_id}")
async def delete_license(
    license_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(AuthService.get_current_user),
):
    """Delete a license"""
    service = LicenseService(db)
    service.delete_license(license_id)
    return {"message": "License deleted successfully"}


