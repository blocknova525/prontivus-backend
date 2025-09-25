"""
License schemas
"""

from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime, date
from enum import Enum

class LicenseStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"
    PENDING = "pending"

class LicenseType(str, Enum):
    TRIAL = "trial"
    BASIC = "basic"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"

class LicenseBase(BaseModel):
    """Base license schema"""
    tenant_id: int
    type: LicenseType
    status: LicenseStatus = LicenseStatus.PENDING
    start_date: date
    end_date: date
    max_users: int
    max_patients: int
    features: List[str] = []
    notes: Optional[str] = None

class LicenseCreate(LicenseBase):
    """Schema for creating a license"""
    pass

class LicenseUpdate(BaseModel):
    """Schema for updating a license"""
    tenant_id: Optional[int] = None
    type: Optional[LicenseType] = None
    status: Optional[LicenseStatus] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    max_users: Optional[int] = None
    max_patients: Optional[int] = None
    features: Optional[List[str]] = None
    notes: Optional[str] = None

class License(LicenseBase):
    """Schema for license response"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class ActivationRequest(BaseModel):
    """Schema for license activation request"""
    license_key: str
    tenant_name: str
    contact_email: str
    contact_phone: Optional[str] = None
    notes: Optional[str] = None
