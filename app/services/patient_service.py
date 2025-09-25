"""
Patient service
"""

from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.patient import Patient
from app.schemas.patient import PatientCreate, PatientUpdate, PatientVisualUpdate
from app.core.exceptions import NotFoundError, ValidationError

class PatientService:
    """Patient service class"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_patient(self, patient_data: PatientCreate, tenant_id: int) -> Patient:
        """Create a new patient"""
        try:
            patient = Patient(
                **patient_data.dict(),
                tenant_id=tenant_id
            )
            self.db.add(patient)
            self.db.commit()
            self.db.refresh(patient)
            return patient
        except Exception as e:
            self.db.rollback()
            raise ValidationError(f"Failed to create patient: {str(e)}")
    
    def get_patient(self, patient_id: int, tenant_id: int) -> Patient:
        """Get a patient by ID"""
        patient = self.db.query(Patient).filter(
            Patient.id == patient_id,
            Patient.tenant_id == tenant_id
        ).first()
        
        if not patient:
            raise NotFoundError("Patient not found")
        
        return patient
    
    def list_patients(self, tenant_id: int, skip: int = 0, limit: int = 100) -> List[Patient]:
        """Get all patients for a tenant"""
        return self.db.query(Patient).filter(
            Patient.tenant_id == tenant_id
        ).offset(skip).limit(limit).all()
    
    def update_patient(self, patient_id: int, patient_data: PatientUpdate, tenant_id: int) -> Patient:
        """Update a patient"""
        patient = self.get_patient(patient_id, tenant_id)
        
        try:
            update_data = patient_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(patient, field, value)
            
            self.db.commit()
            self.db.refresh(patient)
            return patient
        except Exception as e:
            self.db.rollback()
            raise ValidationError(f"Failed to update patient: {str(e)}")
    
    def delete_patient(self, patient_id: int, tenant_id: int) -> bool:
        """Delete a patient"""
        patient = self.get_patient(patient_id, tenant_id)
        
        try:
            self.db.delete(patient)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            raise ValidationError(f"Failed to delete patient: {str(e)}")
    
    def update_patient_visual_info(self, patient_id: int, visual_data: PatientVisualUpdate, tenant_id: int) -> Patient:
        """Update patient visual/physical characteristics"""
        patient = self.get_patient(patient_id, tenant_id)
        
        try:
            update_data = visual_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(patient, field, value)
            
            # Update photo timestamp if photo path is being updated
            if 'patient_photo_path' in update_data:
                from sqlalchemy.sql import func
                patient.patient_photo_updated = func.now()
            
            self.db.commit()
            self.db.refresh(patient)
            return patient
        except Exception as e:
            self.db.rollback()
            raise ValidationError(f"Failed to update patient visual information: {str(e)}")
    
    def search_patients(self, query: str, tenant_id: int) -> List[Patient]:
        """Search patients by name, email, or CPF"""
        return self.db.query(Patient).filter(
            Patient.tenant_id == tenant_id,
            (Patient.full_name.ilike(f"%{query}%")) |
            (Patient.email.ilike(f"%{query}%")) |
            (Patient.cpf.ilike(f"%{query}%"))
        ).all()
