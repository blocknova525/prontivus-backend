"""
Appointment schemas
"""

from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime, date, time
from enum import Enum

class AppointmentStatus(str, Enum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    RESCHEDULED = "rescheduled"

class AppointmentType(str, Enum):
    CONSULTATION = "consultation"
    FOLLOW_UP = "follow_up"
    EMERGENCY = "emergency"
    PROCEDURE = "procedure"
    EXAMINATION = "examination"
    THERAPY = "therapy"

class AppointmentBase(BaseModel):
    """Base appointment schema"""
    patient_id: int
    doctor_id: int
    appointment_date: date
    appointment_time: time
    duration_minutes: int = 60
    type: AppointmentType
    status: AppointmentStatus = AppointmentStatus.SCHEDULED
    notes: Optional[str] = None
    reason: Optional[str] = None
    location: Optional[str] = None
    reminder_sent: bool = False

class AppointmentCreate(AppointmentBase):
    """Schema for creating an appointment"""
    pass

class AppointmentUpdate(BaseModel):
    """Schema for updating an appointment"""
    patient_id: Optional[int] = None
    doctor_id: Optional[int] = None
    appointment_date: Optional[date] = None
    appointment_time: Optional[time] = None
    duration_minutes: Optional[int] = None
    type: Optional[AppointmentType] = None
    status: Optional[AppointmentStatus] = None
    notes: Optional[str] = None
    reason: Optional[str] = None
    location: Optional[str] = None
    reminder_sent: Optional[bool] = None

class Appointment(AppointmentBase):
    """Schema for appointment response"""
    id: int
    tenant_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
