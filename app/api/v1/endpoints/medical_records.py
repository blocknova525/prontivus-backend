"""
Medical records endpoints
"""

from fastapi import APIRouter, Depends, status, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database.database import get_db
from app.schemas.medical_record import (
    MedicalRecord as MedicalRecordSchema,
    MedicalRecordCreate,
    MedicalRecordUpdate,
)
from app.services.medical_record_service import MedicalRecordService
from app.api.v1.dependencies.auth import get_current_user_flexible

router = APIRouter()

# Mock medical records data for development
MOCK_MEDICAL_RECORDS = [
    {
        "id": 1,
        "patient_id": 4,  # patient@prontivus.com
        "doctor_id": 2,
        "doctor_name": "Dr. João Silva",
        "date": "2024-01-20",
        "type": "Consulta de Rotina",
        "diagnosis": "Resfriado comum",
        "treatment": "Repouso e medicamentos sintomáticos",
        "notes": "Paciente apresentou melhora significativa",
        "created_at": datetime.now()
    },
    {
        "id": 2,
        "patient_id": 4,
        "doctor_id": 2,
        "doctor_name": "Dra. Maria Santos",
        "date": "2024-01-15",
        "type": "Consulta de Especialidade",
        "diagnosis": "Deficiência de Vitamina D",
        "treatment": "Suplementação vitamínica",
        "notes": "Retorno em 30 dias",
        "created_at": datetime.now()
    },
    {
        "id": 3,
        "patient_id": 4,
        "doctor_id": 2,
        "doctor_name": "Dr. João Silva",
        "date": "2024-01-10",
        "type": "Exame de Rotina",
        "diagnosis": "Pressão arterial normal",
        "treatment": "Manter hábitos saudáveis",
        "notes": "Paciente em bom estado geral",
        "created_at": datetime.now()
    },
    {
        "id": 4,
        "patient_id": 5,
        "doctor_id": 2,
        "doctor_name": "Dr. João Silva",
        "date": "2024-09-20",
        "type": "Consulta de Rotina",
        "diagnosis": "Check-up geral",
        "treatment": "Exames laboratoriais solicitados",
        "notes": "Paciente 5 - Primeira consulta",
        "created_at": datetime.now()
    },
    {
        "id": 5,
        "patient_id": 5,
        "doctor_id": 2,
        "doctor_name": "Dr. João Silva",
        "date": "2024-09-15",
        "type": "Consulta de Especialidade",
        "diagnosis": "Hipertensão arterial leve",
        "treatment": "Medicação anti-hipertensiva",
        "notes": "Paciente 5 - Controle de pressão",
        "created_at": datetime.now()
    }
]


@router.get("/")
async def list_medical_records(
    patient_id: Optional[int] = Query(None),
    doctor_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_flexible),
):
    """List medical records with optional filtering"""
    try:
        # Always use mock data for now (until we fix the schema mismatch)
        records = MOCK_MEDICAL_RECORDS.copy()
            
        # For patients, only show their own medical records
        if current_user["type"] == "patient":
            records = [record for record in records if record["patient_id"] == current_user["id"]]
        else:
            # For staff, filter by provided parameters
            if patient_id:
                records = [record for record in records if record["patient_id"] == patient_id]
            
            if doctor_id:
                records = [record for record in records if record["doctor_id"] == doctor_id]
        
        return records
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving medical records: {str(e)}"
        )


@router.get("/patient/{patient_id}", response_model=List[MedicalRecordSchema])
async def list_records_by_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_flexible),
):
    service = MedicalRecordService(db)
    return service.get_medical_records_by_patient(patient_id, tenant_id=getattr(current_user, "tenant_id", 0) or 0)


@router.get("/{record_id}", response_model=MedicalRecordSchema)
async def get_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_flexible),
):
    service = MedicalRecordService(db)
    return service.get_medical_record(record_id, tenant_id=getattr(current_user, "tenant_id", 0) or 0)


@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_record(
    payload: MedicalRecordCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_flexible),
):
    """Create a new medical record"""
    try:
        print(f"Creating medical record for patient {payload.patient_id}")
        print(f"Record data: {payload.dict()}")
        
        # Create a simple response that matches what the frontend expects
        new_record = {
            "id": len(MOCK_MEDICAL_RECORDS) + 1,
            "patient_id": payload.patient_id,
            "doctor_id": payload.doctor_id,
            "type": payload.type,
            "title": payload.title,
            "diagnosis": payload.diagnosis or "",
            "treatment": payload.treatment or "",
            "notes": payload.notes or "",
            "chief_complaint": payload.chief_complaint or "",
            "history_of_present_illness": payload.history_of_present_illness or "",
            "physical_examination": payload.physical_examination or "",
            "assessment": payload.assessment or "",
            "plan": payload.plan or "",
            "follow_up_instructions": payload.follow_up_instructions or "",
            "status": payload.status or "draft",
            "created_at": datetime.now().isoformat(),
            "tenant_id": current_user.get("tenant_id", 1)
        }
        
        # Add to mock data for consistency
        MOCK_MEDICAL_RECORDS.append(new_record)
        
        print(f"Medical record created successfully with ID: {new_record['id']}")
        return new_record
        
    except Exception as e:
        print(f"Error creating medical record: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to create medical record: {str(e)}")


@router.put("/{record_id}", response_model=MedicalRecordSchema)
async def update_record(
    record_id: int,
    payload: MedicalRecordUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_flexible),
):
    service = MedicalRecordService(db)
    return service.update_medical_record(record_id, payload, tenant_id=getattr(current_user, "tenant_id", 0) or 0)


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_flexible),
):
    service = MedicalRecordService(db)
    service.delete_medical_record(record_id, tenant_id=getattr(current_user, "tenant_id", 0) or 0)
    return {"status": "deleted"}


