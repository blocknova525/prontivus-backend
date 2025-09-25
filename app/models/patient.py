"""
Patient and medical record models
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Date, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base
from ..utils.database_compat import (
    get_json_type, get_datetime_type, get_string_type, 
    get_boolean_type, get_integer_type, get_foreign_key,
    get_text_type, get_date_type
)

class Patient(Base):
    """Patient model"""
    __tablename__ = "patients"
    
    id = Column(get_integer_type(), primary_key=True, index=True)
    tenant_id = Column(get_integer_type(), get_foreign_key("tenants.id"), nullable=False)
    user_id = Column(get_integer_type(), get_foreign_key("users.id"), nullable=True)  # Link to user account
    
    # Personal information
    full_name = Column(get_string_type(255), nullable=False)
    cpf = Column(get_string_type(14), unique=True, index=True, nullable=False)
    rg = Column(get_string_type(20), nullable=True)
    birth_date = Column(get_date_type(), nullable=False)
    gender = Column(get_string_type(10), nullable=False)  # M, F, Other
    marital_status = Column(get_string_type(20), nullable=True)
    
    # Contact information
    email = Column(get_string_type(255), nullable=True)
    phone = Column(get_string_type(20), nullable=True)
    mobile_phone = Column(get_string_type(20), nullable=True)
    
    # Address
    address = Column(get_text_type(), nullable=True)
    city = Column(get_string_type(100), nullable=True)
    state = Column(get_string_type(2), nullable=True)
    zip_code = Column(get_string_type(10), nullable=True)
    
    # Emergency contact
    emergency_contact_name = Column(get_string_type(255), nullable=True)
    emergency_contact_phone = Column(get_string_type(20), nullable=True)
    emergency_contact_relationship = Column(get_string_type(50), nullable=True)
    
    # Medical information
    blood_type = Column(get_string_type(5), nullable=True)
    allergies = Column(get_text_type(), nullable=True)
    chronic_conditions = Column(get_text_type(), nullable=True)
    medications = Column(get_text_type(), nullable=True)
    
    # Visual/Physical characteristics
    height_cm = Column(get_integer_type(), nullable=True)  # Height in centimeters
    weight_kg = Column(get_integer_type(), nullable=True)  # Weight in kilograms
    eye_color = Column(get_string_type(20), nullable=True)  # Eye color
    hair_color = Column(get_string_type(20), nullable=True)  # Hair color
    skin_tone = Column(get_string_type(20), nullable=True)  # Skin tone description
    distinguishing_features = Column(get_text_type(), nullable=True)  # Scars, tattoos, birthmarks, etc.
    physical_disabilities = Column(get_text_type(), nullable=True)  # Physical limitations or disabilities
    mobility_aids = Column(get_text_type(), nullable=True)  # Wheelchair, cane, walker, etc.
    
    # Visual identifiers for medical staff
    patient_photo_path = Column(get_string_type(512), nullable=True)  # Path to patient photo
    patient_photo_updated = Column(get_datetime_type(), nullable=True)  # When photo was last updated
    visual_notes = Column(get_text_type(), nullable=True)  # Additional visual observations
    
    # Insurance information
    insurance_company = Column(get_string_type(255), nullable=True)
    insurance_number = Column(get_string_type(50), nullable=True)
    insurance_plan = Column(get_string_type(100), nullable=True)
    
    # LGPD Compliance
    consent_given = Column(get_boolean_type(), default=False)
    consent_date = Column(get_datetime_type(), nullable=True)
    
    # Status
    is_active = Column(get_boolean_type(), default=True)
    
    # Timestamps
    created_at = Column(get_datetime_type(), server_default=func.now())
    updated_at = Column(get_datetime_type(), onupdate=func.now())
    
    # Relationships
    tenant = relationship("Tenant")
    user = relationship("User")
    appointments = relationship("Appointment", back_populates="patient")
    medical_records = relationship("MedicalRecord", back_populates="patient")
    prescriptions = relationship("Prescription", back_populates="patient")
    # Temporarily commented out to avoid circular dependencies
    # checkins = relationship("PatientCheckIn", back_populates="patient")
    # documents = relationship("PatientDocument", back_populates="patient")
    # exams = relationship("PatientExam", back_populates="patient")
    # billings = relationship("Billing", back_populates="patient")
    # accounts_receivable = relationship("AccountsReceivable", back_populates="patient")



