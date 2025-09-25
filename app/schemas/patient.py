"""
Patient schemas
"""

from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import datetime, date
from enum import Enum

class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"

class MaritalStatus(str, Enum):
    SINGLE = "single"
    MARRIED = "married"
    DIVORCED = "divorced"
    WIDOWED = "widowed"
    SEPARATED = "separated"

class PatientBase(BaseModel):
    """Base patient schema"""
    full_name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    cpf: Optional[str] = None
    rg: Optional[str] = None
    birth_date: Optional[date] = None
    gender: Optional[Gender] = None
    marital_status: Optional[MaritalStatus] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    insurance_provider: Optional[str] = None
    insurance_number: Optional[str] = None
    allergies: Optional[str] = None
    medical_conditions: Optional[str] = None
    medications: Optional[str] = None
    notes: Optional[str] = None
    
    # Visual/Physical characteristics
    height_cm: Optional[int] = None
    weight_kg: Optional[int] = None
    eye_color: Optional[str] = None
    hair_color: Optional[str] = None
    skin_tone: Optional[str] = None
    distinguishing_features: Optional[str] = None
    physical_disabilities: Optional[str] = None
    mobility_aids: Optional[str] = None
    patient_photo_path: Optional[str] = None
    visual_notes: Optional[str] = None

class PatientCreate(PatientBase):
    """Schema for creating a patient"""
    pass

class PatientUpdate(BaseModel):
    """Schema for updating a patient"""
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    cpf: Optional[str] = None
    rg: Optional[str] = None
    birth_date: Optional[date] = None
    gender: Optional[Gender] = None
    marital_status: Optional[MaritalStatus] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    insurance_provider: Optional[str] = None
    insurance_number: Optional[str] = None
    allergies: Optional[str] = None
    medical_conditions: Optional[str] = None
    medications: Optional[str] = None
    notes: Optional[str] = None
    
    # Visual/Physical characteristics
    height_cm: Optional[int] = None
    weight_kg: Optional[int] = None
    eye_color: Optional[str] = None
    hair_color: Optional[str] = None
    skin_tone: Optional[str] = None
    distinguishing_features: Optional[str] = None
    physical_disabilities: Optional[str] = None
    mobility_aids: Optional[str] = None
    patient_photo_path: Optional[str] = None
    visual_notes: Optional[str] = None

class PatientVisualUpdate(BaseModel):
    """Schema for updating patient visual information"""
    height_cm: Optional[int] = None
    weight_kg: Optional[int] = None
    eye_color: Optional[str] = None
    hair_color: Optional[str] = None
    skin_tone: Optional[str] = None
    distinguishing_features: Optional[str] = None
    physical_disabilities: Optional[str] = None
    mobility_aids: Optional[str] = None
    patient_photo_path: Optional[str] = None
    visual_notes: Optional[str] = None

class Patient(PatientBase):
    """Schema for patient response"""
    id: int
    tenant_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
