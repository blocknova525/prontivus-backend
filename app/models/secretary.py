"""
Secretary Module Models
Patient check-in, insurance verification, document upload, exam inclusion, consultation release
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Enum, JSON, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from .base import Base

class CheckInStatus(str, enum.Enum):
    """Patient check-in status"""
    ARRIVED = "arrived"
    WAITING = "waiting"
    CALLED = "called"
    IN_CONSULTATION = "in_consultation"
    COMPLETED = "completed"
    NO_SHOW = "no_show"
    CANCELLED = "cancelled"

class InsuranceVerificationStatus(str, enum.Enum):
    """Insurance verification status"""
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    EXPIRED = "expired"
    REQUIRES_UPDATE = "requires_update"

class DocumentType(str, enum.Enum):
    """Document type enum"""
    IDENTITY = "identity"
    INSURANCE_CARD = "insurance_card"
    MEDICAL_REPORT = "medical_report"
    LAB_RESULT = "lab_result"
    IMAGING_RESULT = "imaging_result"
    PRESCRIPTION = "prescription"
    REFERRAL = "referral"
    CERTIFICATE = "certificate"
    OTHER = "other"

class PatientCheckIn(Base):
    """Patient check-in model"""
    __tablename__ = "patient_checkins"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True)
    
    # Check-in details
    check_in_time = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(Enum(CheckInStatus), nullable=False, default=CheckInStatus.ARRIVED)
    arrival_method = Column(String(50), nullable=True)  # walk-in, appointment, emergency
    
    # Secretary information
    checked_in_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    notes = Column(Text, nullable=True)
    
    # Insurance verification
    insurance_verified = Column(Boolean, default=False)
    insurance_verification_status = Column(Enum(InsuranceVerificationStatus), default=InsuranceVerificationStatus.PENDING)
    insurance_verification_date = Column(DateTime(timezone=True), nullable=True)
    insurance_notes = Column(Text, nullable=True)
    
    # Waiting information
    waiting_start_time = Column(DateTime(timezone=True), nullable=True)
    estimated_wait_time = Column(Integer, nullable=True)  # minutes
    priority_level = Column(Integer, default=1)  # 1-5 scale
    
    # Completion
    called_time = Column(DateTime(timezone=True), nullable=True)
    consultation_start_time = Column(DateTime(timezone=True), nullable=True)
    completion_time = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    tenant = relationship("Tenant")
    patient = relationship("Patient")
    appointment = relationship("Appointment")
    secretary = relationship("User", foreign_keys=[checked_in_by])
    documents = relationship("PatientDocument", back_populates="checkin")
    exams = relationship("PatientExam", back_populates="checkin")

class PatientDocument(Base):
    """Patient document model"""
    __tablename__ = "patient_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    checkin_id = Column(Integer, ForeignKey("patient_checkins.id"), nullable=True)
    
    # Document details
    document_type = Column(Enum(DocumentType), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # File information
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=True)  # bytes
    mime_type = Column(String(100), nullable=True)
    
    # Upload information
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Verification
    is_verified = Column(Boolean, default=False)
    verified_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    verification_notes = Column(Text, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    tenant = relationship("Tenant")
    patient = relationship("Patient")
    checkin = relationship("PatientCheckIn", back_populates="documents")
    uploader = relationship("User", foreign_keys=[uploaded_by])
    verifier = relationship("User", foreign_keys=[verified_by])

class PatientExam(Base):
    """Patient exam model for exams brought by patient"""
    __tablename__ = "patient_exams"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    checkin_id = Column(Integer, ForeignKey("patient_checkins.id"), nullable=True)
    
    # Exam details
    exam_type = Column(String(100), nullable=False)  # blood test, x-ray, ultrasound, etc.
    exam_name = Column(String(255), nullable=False)
    exam_date = Column(DateTime(timezone=True), nullable=True)
    laboratory = Column(String(255), nullable=True)
    doctor_requesting = Column(String(255), nullable=True)
    
    # Results
    results_summary = Column(Text, nullable=True)
    normal_range = Column(String(100), nullable=True)
    interpretation = Column(Text, nullable=True)
    
    # File information
    file_name = Column(String(255), nullable=True)
    file_path = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)
    
    # Processing
    processed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    processing_notes = Column(Text, nullable=True)
    
    # Status
    is_reviewed = Column(Boolean, default=False)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    tenant = relationship("Tenant")
    patient = relationship("Patient")
    checkin = relationship("PatientCheckIn", back_populates="exams")
    processor = relationship("User", foreign_keys=[processed_by])
    reviewer = relationship("User", foreign_keys=[reviewed_by])

class DailyAgenda(Base):
    """Daily agenda model for secretary management"""
    __tablename__ = "daily_agendas"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Agenda details
    agenda_date = Column(DateTime(timezone=True), nullable=False)
    total_appointments = Column(Integer, default=0)
    completed_appointments = Column(Integer, default=0)
    cancelled_appointments = Column(Integer, default=0)
    no_show_appointments = Column(Integer, default=0)
    
    # Time slots
    start_time = Column(DateTime(timezone=True), nullable=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    break_start = Column(DateTime(timezone=True), nullable=True)
    break_end = Column(DateTime(timezone=True), nullable=True)
    
    # Statistics
    average_consultation_time = Column(Integer, nullable=True)  # minutes
    total_revenue = Column(Numeric(10, 2), nullable=True)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    doctor = relationship("User", foreign_keys=[doctor_id])

class WaitingPanel(Base):
    """Waiting panel model for real-time patient status"""
    __tablename__ = "waiting_panels"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    
    # Panel configuration
    panel_name = Column(String(100), nullable=False)
    location = Column(String(255), nullable=True)  # reception, waiting room, etc.
    is_active = Column(Boolean, default=True)
    
    # Display settings
    display_format = Column(String(50), default="standard")  # standard, compact, detailed
    refresh_interval = Column(Integer, default=30)  # seconds
    show_estimated_wait = Column(Boolean, default=True)
    show_priority = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    tenant = relationship("Tenant")

class InsuranceShortcut(Base):
    """Insurance shortcut model for quick verification"""
    __tablename__ = "insurance_shortcuts"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    
    # Insurance details
    insurance_name = Column(String(255), nullable=False)
    insurance_code = Column(String(50), nullable=True)
    contact_phone = Column(String(20), nullable=True)
    contact_email = Column(String(255), nullable=True)
    
    # Verification settings
    verification_url = Column(String(500), nullable=True)
    api_endpoint = Column(String(500), nullable=True)
    requires_auth = Column(Boolean, default=False)
    auth_token = Column(String(500), nullable=True)
    
    # Response codes
    valid_codes = Column(JSON, nullable=True)  # List of valid response codes
    invalid_codes = Column(JSON, nullable=True)  # List of invalid response codes
    
    # Status
    is_active = Column(Boolean, default=True)
    last_verified = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    tenant = relationship("Tenant")
