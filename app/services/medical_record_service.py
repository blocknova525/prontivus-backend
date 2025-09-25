"""
Medical record service
"""

from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.medical_record import MedicalRecord
from app.schemas.medical_record import MedicalRecordCreate, MedicalRecordUpdate
from app.core.exceptions import NotFoundError, ValidationError

class MedicalRecordService:
    """Medical record service class"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_medical_record(self, record_data: MedicalRecordCreate, tenant_id: int) -> MedicalRecord:
        """Create a new medical record"""
        try:
            record = MedicalRecord(
                **record_data.dict(),
                tenant_id=tenant_id
            )
            self.db.add(record)
            self.db.commit()
            self.db.refresh(record)
            return record
        except Exception as e:
            self.db.rollback()
            raise ValidationError(f"Failed to create medical record: {str(e)}")
    
    def get_medical_record(self, record_id: int, tenant_id: int) -> MedicalRecord:
        """Get a medical record by ID"""
        record = self.db.query(MedicalRecord).filter(
            MedicalRecord.id == record_id,
            MedicalRecord.tenant_id == tenant_id
        ).first()
        
        if not record:
            raise NotFoundError("Medical record not found")
        
        return record
    
    def get_medical_records(self, tenant_id: int, skip: int = 0, limit: int = 100) -> List[MedicalRecord]:
        """Get all medical records for a tenant"""
        return self.db.query(MedicalRecord).filter(
            MedicalRecord.tenant_id == tenant_id
        ).offset(skip).limit(limit).all()
    
    def list_records(self) -> List[MedicalRecord]:
        """List all medical records (for API compatibility)"""
        return self.db.query(MedicalRecord).all()
    
    def get_medical_records_by_patient(self, patient_id: int, tenant_id: int) -> List[MedicalRecord]:
        """Get medical records for a specific patient"""
        return self.db.query(MedicalRecord).filter(
            MedicalRecord.patient_id == patient_id,
            MedicalRecord.tenant_id == tenant_id
        ).all()
    
    def get_medical_records_by_doctor(self, doctor_id: int, tenant_id: int) -> List[MedicalRecord]:
        """Get medical records for a specific doctor"""
        return self.db.query(MedicalRecord).filter(
            MedicalRecord.doctor_id == doctor_id,
            MedicalRecord.tenant_id == tenant_id
        ).all()
    
    def update_medical_record(self, record_id: int, record_data: MedicalRecordUpdate, tenant_id: int) -> MedicalRecord:
        """Update a medical record"""
        record = self.get_medical_record(record_id, tenant_id)
        
        try:
            update_data = record_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(record, field, value)
            
            self.db.commit()
            self.db.refresh(record)
            return record
        except Exception as e:
            self.db.rollback()
            raise ValidationError(f"Failed to update medical record: {str(e)}")
    
    def delete_medical_record(self, record_id: int, tenant_id: int) -> bool:
        """Delete a medical record"""
        record = self.get_medical_record(record_id, tenant_id)
        
        try:
            self.db.delete(record)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            raise ValidationError(f"Failed to delete medical record: {str(e)}")
    
    def finalize_medical_record(self, record_id: int, tenant_id: int) -> MedicalRecord:
        """Finalize a medical record"""
        record = self.get_medical_record(record_id, tenant_id)
        record.status = "finalized"
        
        try:
            self.db.commit()
            self.db.refresh(record)
            return record
        except Exception as e:
            self.db.rollback()
            raise ValidationError(f"Failed to finalize medical record: {str(e)}")
    
    def sign_medical_record(self, record_id: int, tenant_id: int) -> MedicalRecord:
        """Sign a medical record"""
        record = self.get_medical_record(record_id, tenant_id)
        record.status = "signed"
        
        try:
            self.db.commit()
            self.db.refresh(record)
            return record
        except Exception as e:
            self.db.rollback()
            raise ValidationError(f"Failed to sign medical record: {str(e)}")