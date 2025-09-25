"""
Secretary Module Pydantic Schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

from .secretary_enums import CheckInStatus, InsuranceVerificationStatus, DocumentType

class PatientCheckInBase(BaseModel):
    patient_id: int
    appointment_id: Optional[int] = None
    arrival_method: Optional[str] = None
    notes: Optional[str] = None
    priority_level: Optional[int] = Field(default=1, ge=1, le=5)

class PatientCheckInCreate(PatientCheckInBase):
    pass

class PatientCheckInUpdate(BaseModel):
    status: Optional[CheckInStatus] = None
    notes: Optional[str] = None
    priority_level: Optional[int] = Field(ge=1, le=5)
    insurance_notes: Optional[str] = None

class PatientCheckInResponse(PatientCheckInBase):
    id: int
    tenant_id: int
    check_in_time: datetime
    status: CheckInStatus
    checked_in_by: int
    insurance_verified: bool
    insurance_verification_status: InsuranceVerificationStatus
    insurance_verification_date: Optional[datetime]
    insurance_notes: Optional[str]
    waiting_start_time: Optional[datetime]
    estimated_wait_time: Optional[int]
    called_time: Optional[datetime]
    consultation_start_time: Optional[datetime]
    completion_time: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    
    # Patient information
    patient_name: Optional[str] = None
    patient_cpf: Optional[str] = None
    patient_phone: Optional[str] = None
    
    # Secretary information
    secretary_name: Optional[str] = None
    
    class Config:
        from_attributes = True

class PatientDocumentBase(BaseModel):
    patient_id: int
    checkin_id: Optional[int] = None
    document_type: DocumentType
    title: str
    description: Optional[str] = None

class PatientDocumentCreate(PatientDocumentBase):
    pass

class PatientDocumentResponse(PatientDocumentBase):
    id: int
    tenant_id: int
    file_name: str
    file_path: str
    file_size: Optional[int]
    mime_type: Optional[str]
    uploaded_by: int
    uploaded_at: datetime
    is_verified: bool
    verified_by: Optional[int]
    verified_at: Optional[datetime]
    verification_notes: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    
    # Uploader information
    uploader_name: Optional[str] = None
    
    class Config:
        from_attributes = True

class PatientExamBase(BaseModel):
    patient_id: int
    checkin_id: Optional[int] = None
    exam_type: str
    exam_name: str
    exam_date: Optional[datetime] = None
    laboratory: Optional[str] = None
    doctor_requesting: Optional[str] = None
    results_summary: Optional[str] = None
    normal_range: Optional[str] = None
    interpretation: Optional[str] = None

class PatientExamCreate(PatientExamBase):
    pass

class PatientExamResponse(PatientExamBase):
    id: int
    tenant_id: int
    file_name: Optional[str]
    file_path: Optional[str]
    file_size: Optional[int]
    mime_type: Optional[str]
    processed_by: Optional[int]
    processed_at: Optional[datetime]
    processing_notes: Optional[str]
    is_reviewed: bool
    reviewed_by: Optional[int]
    reviewed_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    
    # Processor information
    processor_name: Optional[str] = None
    
    class Config:
        from_attributes = True

class DailyAgendaResponse(BaseModel):
    id: int
    tenant_id: int
    doctor_id: int
    agenda_date: datetime
    total_appointments: int
    completed_appointments: int
    cancelled_appointments: int
    no_show_appointments: int
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    break_start: Optional[datetime]
    break_end: Optional[datetime]
    average_consultation_time: Optional[int]
    total_revenue: Optional[float]
    notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    
    # Doctor information
    doctor_name: Optional[str] = None
    
    class Config:
        from_attributes = True

class WaitingPanelResponse(BaseModel):
    id: int
    tenant_id: int
    panel_name: str
    location: Optional[str]
    is_active: bool
    display_format: str
    refresh_interval: int
    show_estimated_wait: bool
    show_priority: bool
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class InsuranceShortcutBase(BaseModel):
    insurance_name: str
    insurance_code: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    verification_url: Optional[str] = None
    api_endpoint: Optional[str] = None
    requires_auth: bool = False
    auth_token: Optional[str] = None
    valid_codes: Optional[List[str]] = None
    invalid_codes: Optional[List[str]] = None

class InsuranceShortcutCreate(InsuranceShortcutBase):
    pass

class InsuranceShortcutResponse(InsuranceShortcutBase):
    id: int
    tenant_id: int
    is_active: bool
    last_verified: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class CheckInStats(BaseModel):
    """Statistics for check-ins"""
    total_checkins: int
    waiting: int
    in_consultation: int
    completed: int
    cancelled: int
    no_show: int
    average_wait_time: Optional[float]  # minutes

class InsuranceVerificationRequest(BaseModel):
    """Request for insurance verification"""
    patient_id: int
    insurance_company: str
    insurance_number: str
    verification_method: str = "api"  # api, phone, manual

class InsuranceVerificationResponse(BaseModel):
    """Response from insurance verification"""
    is_valid: bool
    status: str
    message: str
    coverage_details: Optional[dict] = None
    copay_amount: Optional[float] = None
    deductible_remaining: Optional[float] = None
    verification_date: datetime
