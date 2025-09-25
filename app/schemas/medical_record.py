"""
Medical record schemas
"""

from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime, date
from enum import Enum

class RecordType(str, Enum):
    CONSULTATION = "consultation"
    EXAMINATION = "examination"
    PROCEDURE = "procedure"
    EMERGENCY = "emergency"
    FOLLOW_UP = "follow_up"
    LABORATORY = "laboratory"
    IMAGING = "imaging"
    PRESCRIPTION = "prescription"

class RecordStatus(str, Enum):
    DRAFT = "draft"
    FINALIZED = "finalized"
    SIGNED = "signed"
    ARCHIVED = "archived"

class MedicalRecordBase(BaseModel):
    """Base medical record schema"""
    patient_id: int
    doctor_id: int
    appointment_id: Optional[int] = None
    type: RecordType
    status: RecordStatus = RecordStatus.DRAFT
    title: str
    chief_complaint: Optional[str] = None
    history_of_present_illness: Optional[str] = None
    physical_examination: Optional[str] = None
    assessment: Optional[str] = None
    plan: Optional[str] = None
    notes: Optional[str] = None
    diagnosis: Optional[str] = None
    treatment: Optional[str] = None
    follow_up_instructions: Optional[str] = None

class MedicalRecordCreate(MedicalRecordBase):
    """Schema for creating a medical record"""
    pass

class MedicalRecordUpdate(BaseModel):
    """Schema for updating a medical record"""
    patient_id: Optional[int] = None
    doctor_id: Optional[int] = None
    appointment_id: Optional[int] = None
    type: Optional[RecordType] = None
    status: Optional[RecordStatus] = None
    title: Optional[str] = None
    chief_complaint: Optional[str] = None
    history_of_present_illness: Optional[str] = None
    physical_examination: Optional[str] = None
    assessment: Optional[str] = None
    plan: Optional[str] = None
    notes: Optional[str] = None
    diagnosis: Optional[str] = None
    treatment: Optional[str] = None
    follow_up_instructions: Optional[str] = None

class MedicalRecord(MedicalRecordBase):
    """Schema for medical record response"""
    id: int
    tenant_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
