from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from .base import Base

class RecordType(str, enum.Enum):
    """Medical record type enum"""
    CONSULTATION = "consultation"
    EXAM = "exam"
    PROCEDURE = "procedure"
    EMERGENCY = "emergency"
    FOLLOW_UP = "follow_up"
    SURGERY = "surgery"
    LABORATORY = "laboratory"
    IMAGING = "imaging"

class RecordStatus(str, enum.Enum):
    """Medical record status enum"""
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    SIGNED = "signed"
    ARCHIVED = "archived"

class MedicalRecord(Base):
    """Medical record model"""
    __tablename__ = "medical_records"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True)
    
    # Record identification
    record_number = Column(String(50), unique=True, nullable=False, index=True)
    type = Column(Enum(RecordType), nullable=False)
    status = Column(Enum(RecordStatus), nullable=False, default=RecordStatus.DRAFT)
    
    # Medical information
    chief_complaint = Column(Text, nullable=True)  # Main reason for visit
    history_present_illness = Column(Text, nullable=True)
    past_medical_history = Column(Text, nullable=True)
    family_history = Column(Text, nullable=True)
    social_history = Column(Text, nullable=True)
    medications = Column(Text, nullable=True)
    allergies = Column(Text, nullable=True)
    
    # Physical examination
    vital_signs = Column(JSON, nullable=True)  # Blood pressure, temperature, etc.
    physical_exam = Column(Text, nullable=True)
    assessment = Column(Text, nullable=True)  # Clinical impression
    plan = Column(Text, nullable=True)  # Treatment plan
    
    # Diagnosis and coding
    primary_diagnosis = Column(String(255), nullable=True)
    secondary_diagnoses = Column(JSON, nullable=True)  # Array of secondary diagnoses
    icd10_codes = Column(JSON, nullable=True)  # ICD-10 codes
    
    # Additional data
    lab_results = Column(JSON, nullable=True)
    imaging_results = Column(JSON, nullable=True)
    procedures_performed = Column(JSON, nullable=True)
    
    # Digital signature
    doctor_signature = Column(Text, nullable=True)
    signature_timestamp = Column(DateTime(timezone=True), nullable=True)
    signature_hash = Column(String(255), nullable=True)
    
    # Review and approval
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    review_notes = Column(Text, nullable=True)
    
    # LGPD Compliance
    consent_given = Column(Boolean, default=False)
    consent_date = Column(DateTime(timezone=True), nullable=True)
    data_retention_until = Column(DateTime(timezone=True), nullable=True)
    access_log = Column(JSON, nullable=True)  # Track who accessed the record
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    tenant = relationship("Tenant")
    patient = relationship("Patient", back_populates="medical_records")
    doctor = relationship("User", foreign_keys=[doctor_id])
    appointment = relationship("Appointment")
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    
    # Related records
    prescriptions = relationship("Prescription", back_populates="medical_record")
    attachments = relationship("MedicalRecordAttachment", back_populates="medical_record")
    
    def __repr__(self):
        return f"<MedicalRecord(id={self.id}, patient_id={self.patient_id}, type={self.type}, status={self.status})>"

class MedicalRecordAttachment(Base):
    """Medical record attachment model"""
    __tablename__ = "medical_record_attachments"
    
    id = Column(Integer, primary_key=True, index=True)
    medical_record_id = Column(Integer, ForeignKey("medical_records.id"), nullable=False)
    
    # File information
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    
    # File metadata
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=True)  # lab_result, image, document, etc.
    
    # Security
    is_encrypted = Column(Boolean, default=True)
    encryption_key_id = Column(String(100), nullable=True)
    
    # LGPD Compliance
    consent_given = Column(Boolean, default=False)
    consent_date = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    medical_record = relationship("MedicalRecord", back_populates="attachments")
    uploader = relationship("User")
    
    def __repr__(self):
        return f"<MedicalRecordAttachment(id={self.id}, filename={self.filename}, record_id={self.medical_record_id})>"

class VitalSigns(Base):
    """Vital signs model for tracking patient vitals over time"""
    __tablename__ = "vital_signs"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    medical_record_id = Column(Integer, ForeignKey("medical_records.id"), nullable=True)
    
    # Vital signs data
    systolic_bp = Column(Integer, nullable=True)  # mmHg
    diastolic_bp = Column(Integer, nullable=True)  # mmHg
    heart_rate = Column(Integer, nullable=True)  # bpm
    temperature = Column(Integer, nullable=True)  # °C * 100 (to store as integer)
    respiratory_rate = Column(Integer, nullable=True)  # breaths per minute
    oxygen_saturation = Column(Integer, nullable=True)  # %
    weight = Column(Integer, nullable=True)  # grams
    height = Column(Integer, nullable=True)  # centimeters
    
    # Additional measurements
    pain_level = Column(Integer, nullable=True)  # 0-10 scale
    blood_glucose = Column(Integer, nullable=True)  # mg/dL
    
    # Context
    measurement_location = Column(String(100), nullable=True)  # clinic, home, hospital
    notes = Column(Text, nullable=True)
    
    # Timestamps
    measured_at = Column(DateTime(timezone=True), server_default=func.now())
    measured_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    patient = relationship("Patient")
    medical_record = relationship("MedicalRecord")
    measurer = relationship("User")
    
    def __repr__(self):
        return f"<VitalSigns(id={self.id}, patient_id={self.patient_id}, measured_at={self.measured_at})>"
