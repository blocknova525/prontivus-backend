from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from .base import Base

class AppointmentStatus(str, enum.Enum):
    """Appointment status enum"""
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    RESCHEDULED = "rescheduled"

class AppointmentType(str, enum.Enum):
    """Appointment type enum"""
    CONSULTATION = "consultation"
    FOLLOW_UP = "follow_up"
    EXAM = "exam"
    PROCEDURE = "procedure"
    EMERGENCY = "emergency"
    TELEMEDICINE = "telemedicine"

class Appointment(Base):
    """Appointment model"""
    __tablename__ = "appointments"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Appointment details
    appointment_date = Column(DateTime(timezone=True), nullable=False)
    duration_minutes = Column(Integer, default=30)
    type = Column(Enum(AppointmentType), nullable=False, default=AppointmentType.CONSULTATION)
    status = Column(Enum(AppointmentStatus), nullable=False, default=AppointmentStatus.SCHEDULED)
    
    # Location and method
    location = Column(String(255), nullable=True)  # Room, clinic, etc.
    is_telemedicine = Column(Boolean, default=False)
    telemedicine_link = Column(String(500), nullable=True)
    
    # Appointment content
    reason = Column(Text, nullable=True)  # Patient's reason for visit
    notes = Column(Text, nullable=True)  # Doctor's notes
    diagnosis = Column(Text, nullable=True)
    treatment_plan = Column(Text, nullable=True)
    
    # Scheduling
    scheduled_at = Column(DateTime(timezone=True), server_default=func.now())
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    cancellation_reason = Column(Text, nullable=True)
    
    # Reminders and notifications
    reminder_sent = Column(Boolean, default=False)
    reminder_sent_at = Column(DateTime(timezone=True), nullable=True)
    confirmation_sent = Column(Boolean, default=False)
    confirmation_sent_at = Column(DateTime(timezone=True), nullable=True)
    
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
    patient = relationship("Patient", back_populates="appointments")
    doctor = relationship("User", foreign_keys=[doctor_id])
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    
    # Related records
    medical_records = relationship("MedicalRecord", back_populates="appointment")
    prescriptions = relationship("Prescription", back_populates="appointment")
    # Temporarily commented out to avoid circular dependencies
    # checkins = relationship("PatientCheckIn", back_populates="appointment")
    # billings = relationship("Billing", back_populates="appointment")
    
    def __repr__(self):
        return f"<Appointment(id={self.id}, patient_id={self.patient_id}, doctor_id={self.doctor_id}, date={self.appointment_date})>"

class AppointmentReminder(Base):
    """Appointment reminder model"""
    __tablename__ = "appointment_reminders"
    
    id = Column(Integer, primary_key=True, index=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=False)
    
    # Reminder details
    reminder_type = Column(String(20), nullable=False)  # email, sms, push
    scheduled_for = Column(DateTime(timezone=True), nullable=False)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), default="pending")  # pending, sent, failed
    
    # Content
    message = Column(Text, nullable=True)
    subject = Column(String(255), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    appointment = relationship("Appointment")
    
    def __repr__(self):
        return f"<AppointmentReminder(id={self.id}, appointment_id={self.appointment_id}, type={self.reminder_type})>"
