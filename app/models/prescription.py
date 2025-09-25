from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Enum, Numeric, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from .base import Base

class PrescriptionStatus(str, enum.Enum):
    """Prescription status enum"""
    DRAFT = "draft"
    ACTIVE = "active"
    DISPENSED = "dispensed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"

class PrescriptionType(str, enum.Enum):
    """Prescription type enum"""
    MEDICATION = "medication"
    MEDICAL_DEVICE = "medical_device"
    LABORATORY = "laboratory"
    IMAGING = "imaging"
    PROCEDURE = "procedure"

class Prescription(Base):
    """Prescription model"""
    __tablename__ = "prescriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    medical_record_id = Column(Integer, ForeignKey("medical_records.id"), nullable=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True)
    
    # Prescription identification
    prescription_number = Column(String(50), unique=True, nullable=False, index=True)
    type = Column(Enum(PrescriptionType), nullable=False, default=PrescriptionType.MEDICATION)
    status = Column(Enum(PrescriptionStatus), nullable=False, default=PrescriptionStatus.DRAFT)
    
    # Prescription details
    diagnosis = Column(Text, nullable=True)
    instructions = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Validity
    issued_date = Column(DateTime(timezone=True), server_default=func.now())
    valid_until = Column(DateTime(timezone=True), nullable=True)
    refills_allowed = Column(Integer, default=0)
    refills_used = Column(Integer, default=0)
    
    # Digital signature
    doctor_signature = Column(Text, nullable=True)
    signature_timestamp = Column(DateTime(timezone=True), nullable=True)
    signature_hash = Column(String(255), nullable=True)
    
    # Dispensing information
    dispensed_at = Column(DateTime(timezone=True), nullable=True)
    dispensed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    pharmacy_name = Column(String(255), nullable=True)
    pharmacy_address = Column(Text, nullable=True)
    
    # LGPD Compliance
    consent_given = Column(Boolean, default=False)
    consent_date = Column(DateTime(timezone=True), nullable=True)
    data_retention_until = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    tenant = relationship("Tenant")
    patient = relationship("Patient", back_populates="prescriptions")
    doctor = relationship("User", foreign_keys=[doctor_id])
    medical_record = relationship("MedicalRecord", back_populates="prescriptions")
    appointment = relationship("Appointment")
    dispenser = relationship("User", foreign_keys=[dispensed_by])
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    
    # Related records
    prescription_items = relationship("PrescriptionItem", back_populates="prescription")
    
    def __repr__(self):
        return f"<Prescription(id={self.id}, patient_id={self.patient_id}, prescription_number={self.prescription_number})>"

class PrescriptionItem(Base):
    """Prescription item model for individual medications/procedures"""
    __tablename__ = "prescription_items"
    
    id = Column(Integer, primary_key=True, index=True)
    prescription_id = Column(Integer, ForeignKey("prescriptions.id"), nullable=False)
    
    # Item details
    item_type = Column(String(50), nullable=False)  # medication, procedure, exam
    name = Column(String(255), nullable=False)
    generic_name = Column(String(255), nullable=True)
    dosage_form = Column(String(100), nullable=True)  # tablet, capsule, injection, etc.
    strength = Column(String(100), nullable=True)  # 500mg, 10ml, etc.
    
    # Dosage information
    quantity = Column(Numeric(10, 2), nullable=True)
    unit = Column(String(20), nullable=True)  # tablets, ml, mg, etc.
    frequency = Column(String(100), nullable=True)  # "twice daily", "as needed", etc.
    duration = Column(String(100), nullable=True)  # "7 days", "until finished", etc.
    
    # Instructions
    administration_route = Column(String(100), nullable=True)  # oral, IV, topical, etc.
    special_instructions = Column(Text, nullable=True)
    warnings = Column(Text, nullable=True)
    
    # Medication-specific fields
    drug_code = Column(String(50), nullable=True)  # ANVISA code, etc.
    manufacturer = Column(String(255), nullable=True)
    batch_number = Column(String(100), nullable=True)
    expiration_date = Column(DateTime(timezone=True), nullable=True)
    
    # Pricing
    unit_price = Column(Numeric(10, 2), nullable=True)
    total_price = Column(Numeric(10, 2), nullable=True)
    
    # Status
    is_dispensed = Column(Boolean, default=False)
    dispensed_quantity = Column(Numeric(10, 2), nullable=True)
    dispensed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    prescription = relationship("Prescription", back_populates="prescription_items")
    
    def __repr__(self):
        return f"<PrescriptionItem(id={self.id}, prescription_id={self.prescription_id}, name={self.name})>"

class DrugInteraction(Base):
    """Drug interaction model for checking medication conflicts"""
    __tablename__ = "drug_interactions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Drug information
    drug_a_code = Column(String(50), nullable=False)
    drug_a_name = Column(String(255), nullable=False)
    drug_b_code = Column(String(50), nullable=False)
    drug_b_name = Column(String(255), nullable=False)
    
    # Interaction details
    severity = Column(String(20), nullable=False)  # minor, moderate, major, contraindicated
    description = Column(Text, nullable=True)
    clinical_effects = Column(Text, nullable=True)
    management = Column(Text, nullable=True)
    
    # Evidence
    evidence_level = Column(String(20), nullable=True)  # A, B, C, D
    references = Column(JSON, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<DrugInteraction(id={self.id}, drug_a={self.drug_a_name}, drug_b={self.drug_b_name}, severity={self.severity})>"

class PatientAllergy(Base):
    """Patient allergy model"""
    __tablename__ = "patient_allergies"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    
    # Allergy information
    allergen_type = Column(String(50), nullable=False)  # medication, food, environmental
    allergen_name = Column(String(255), nullable=False)
    allergen_code = Column(String(50), nullable=True)  # drug code, etc.
    
    # Reaction details
    reaction_type = Column(String(100), nullable=True)  # rash, anaphylaxis, etc.
    severity = Column(String(20), nullable=True)  # mild, moderate, severe
    description = Column(Text, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    verified_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    patient = relationship("Patient")
    verifier = relationship("User", foreign_keys=[verified_by])
    creator = relationship("User", foreign_keys=[created_by])
    
    def __repr__(self):
        return f"<PatientAllergy(id={self.id}, patient_id={self.patient_id}, allergen={self.allergen_name})>"
