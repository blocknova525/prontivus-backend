"""
Appointment service
"""

from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, time
from app.models.appointment import Appointment
from app.schemas.appointment import AppointmentCreate, AppointmentUpdate
from app.core.exceptions import NotFoundError, ValidationError

class AppointmentService:
    """Appointment service class"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_appointment(self, appointment_data: AppointmentCreate, tenant_id: int) -> Appointment:
        """Create a new appointment"""
        try:
            appointment = Appointment(
                **appointment_data.dict(),
                tenant_id=tenant_id
            )
            self.db.add(appointment)
            self.db.commit()
            self.db.refresh(appointment)
            return appointment
        except Exception as e:
            self.db.rollback()
            raise ValidationError(f"Failed to create appointment: {str(e)}")
    
    def get_appointment(self, appointment_id: int, tenant_id: int) -> Appointment:
        """Get an appointment by ID"""
        appointment = self.db.query(Appointment).filter(
            Appointment.id == appointment_id,
            Appointment.tenant_id == tenant_id
        ).first()
        
        if not appointment:
            raise NotFoundError("Appointment not found")
        
        return appointment
    
    def list_appointments(self, tenant_id: int, skip: int = 0, limit: int = 100) -> List[Appointment]:
        """Get all appointments for a tenant"""
        return self.db.query(Appointment).filter(
            Appointment.tenant_id == tenant_id
        ).offset(skip).limit(limit).all()
    
    def get_appointments_by_date(self, appointment_date: date, tenant_id: int) -> List[Appointment]:
        """Get appointments for a specific date"""
        return self.db.query(Appointment).filter(
            Appointment.appointment_date == appointment_date,
            Appointment.tenant_id == tenant_id
        ).all()
    
    def get_appointments_by_patient(self, patient_id: int, tenant_id: int) -> List[Appointment]:
        """Get appointments for a specific patient"""
        return self.db.query(Appointment).filter(
            Appointment.patient_id == patient_id,
            Appointment.tenant_id == tenant_id
        ).all()
    
    def get_appointments_by_doctor(self, doctor_id: int, tenant_id: int) -> List[Appointment]:
        """Get appointments for a specific doctor"""
        return self.db.query(Appointment).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.tenant_id == tenant_id
        ).all()
    
    def update_appointment(self, appointment_id: int, appointment_data: AppointmentUpdate, tenant_id: int) -> Appointment:
        """Update an appointment"""
        appointment = self.get_appointment(appointment_id, tenant_id)
        
        try:
            update_data = appointment_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(appointment, field, value)
            
            self.db.commit()
            self.db.refresh(appointment)
            return appointment
        except Exception as e:
            self.db.rollback()
            raise ValidationError(f"Failed to update appointment: {str(e)}")
    
    def delete_appointment(self, appointment_id: int, tenant_id: int) -> bool:
        """Delete an appointment"""
        appointment = self.get_appointment(appointment_id, tenant_id)
        
        try:
            self.db.delete(appointment)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            raise ValidationError(f"Failed to delete appointment: {str(e)}")
    
    def cancel_appointment(self, appointment_id: int, tenant_id: int) -> Appointment:
        """Cancel an appointment"""
        appointment = self.get_appointment(appointment_id, tenant_id)
        appointment.status = "cancelled"
        
        try:
            self.db.commit()
            self.db.refresh(appointment)
            return appointment
        except Exception as e:
            self.db.rollback()
            raise ValidationError(f"Failed to cancel appointment: {str(e)}")
