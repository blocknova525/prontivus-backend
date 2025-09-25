"""
User schemas
"""

from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    full_name: str
    phone: Optional[str] = None

class UserCreate(UserBase):
    """User creation schema"""
    password: str
    username: Optional[str] = None
    cpf: Optional[str] = None
    crm: Optional[str] = None
    specialty: Optional[str] = None
    tenant_id: Optional[int] = None

class UserUpdate(BaseModel):
    """User update schema"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    crm: Optional[str] = None
    specialty: Optional[str] = None
    avatar_url: Optional[str] = None

class User(UserBase):
    """User response schema"""
    id: int
    username: Optional[str] = None
    cpf: Optional[str] = None
    crm: Optional[str] = None
    specialty: Optional[str] = None
    is_active: bool
    is_verified: bool
    is_superuser: bool
    must_reset_password: bool
    two_factor_enabled: bool
    consent_given: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True

class UserProfile(BaseModel):
    """User profile schema"""
    id: int
    email: str
    username: Optional[str] = None
    full_name: str
    cpf: Optional[str] = None
    phone: Optional[str] = None
    crm: Optional[str] = None
    specialty: Optional[str] = None
    avatar_url: Optional[str] = None
    is_verified: bool
    two_factor_enabled: bool
    created_at: datetime

    class Config:
        from_attributes = True
