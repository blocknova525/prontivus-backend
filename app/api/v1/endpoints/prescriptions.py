"""
Prescription endpoints
"""

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date

from app.database.database import get_db
from app.api.v1.dependencies.auth import get_current_user_flexible

router = APIRouter()

# Mock prescriptions data for development
MOCK_PRESCRIPTIONS = [
    {
        "id": 1,
        "patient_id": 4,  # patient@prontivus.com
        "doctor_id": 2,
        "doctor_name": "Dr. João Silva",
        "issued_date": "2024-01-20",
        "medications": [
            {
                "name": "Paracetamol",
                "dosage": "500mg",
                "frequency": "3x ao dia",
                "duration": "7 dias"
            },
            {
                "name": "Ibuprofeno",
                "dosage": "400mg",
                "frequency": "2x ao dia",
                "duration": "5 dias"
            }
        ],
        "notes": "Tomar com alimentos",
        "status": "active",
        "created_at": datetime.now()
    },
    {
        "id": 2,
        "patient_id": 4,
        "doctor_id": 2,
        "doctor_name": "Dra. Maria Santos",
        "issued_date": "2024-01-15",
        "medications": [
            {
                "name": "Vitamina D",
                "dosage": "1000 UI",
                "frequency": "1x ao dia",
                "duration": "30 dias"
            }
        ],
        "notes": "Tomar pela manhã",
        "status": "active",
        "created_at": datetime.now()
    },
    {
        "id": 3,
        "patient_id": 4,
        "doctor_id": 2,
        "doctor_name": "Dr. João Silva",
        "issued_date": "2024-01-10",
        "medications": [
            {
                "name": "Omeprazol",
                "dosage": "20mg",
                "frequency": "1x ao dia",
                "duration": "15 dias"
            }
        ],
        "notes": "Tomar em jejum",
        "status": "completed",
        "created_at": datetime.now()
    },
    {
        "id": 4,
        "patient_id": 5,
        "doctor_id": 2,
        "doctor_name": "Dr. João Silva",
        "issued_date": "2024-09-20",
        "medications": [
            {
                "name": "Losartana",
                "dosage": "50mg",
                "frequency": "1x ao dia",
                "duration": "30 dias"
            },
            {
                "name": "Hidroclorotiazida",
                "dosage": "25mg",
                "frequency": "1x ao dia",
                "duration": "30 dias"
            }
        ],
        "notes": "Tomar pela manhã, controlar pressão arterial",
        "status": "active",
        "created_at": datetime.now()
    },
    {
        "id": 5,
        "patient_id": 5,
        "doctor_id": 2,
        "doctor_name": "Dr. João Silva",
        "issued_date": "2024-09-15",
        "medications": [
            {
                "name": "Metformina",
                "dosage": "500mg",
                "frequency": "2x ao dia",
                "duration": "30 dias"
            }
        ],
        "notes": "Tomar com as refeições",
        "status": "active",
        "created_at": datetime.now()
    }
]


@router.get("/", response_model=List[dict])
async def list_prescriptions(
    patient_id: Optional[int] = Query(None),
    doctor_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_flexible),
):
    """List prescriptions with optional filtering"""
    import os
    
    # Always use mock data for now (until we fix the schema mismatch)
    import os
    prescriptions = MOCK_PRESCRIPTIONS.copy()
    
    # For patients, only show their own prescriptions
    if current_user["type"] == "patient":
        prescriptions = [prescription for prescription in prescriptions if prescription["patient_id"] == current_user["id"]]
    else:
        # For staff, filter by provided parameters
        if patient_id:
            prescriptions = [prescription for prescription in prescriptions if prescription["patient_id"] == patient_id]
        
        if doctor_id:
            prescriptions = [prescription for prescription in prescriptions if prescription["doctor_id"] == doctor_id]
    
    # Filter by status if provided
    if status:
        prescriptions = [prescription for prescription in prescriptions if prescription["status"] == status]
    
    return prescriptions


@router.get("/{prescription_id}", response_model=dict)
async def get_prescription(
    prescription_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_flexible),
):
    """Get a specific prescription"""
    import os
    
    if os.getenv("USE_DATABASE", "false").lower() == "false":
        # Return mock data
        for prescription in MOCK_PRESCRIPTIONS:
            if prescription["id"] == prescription_id:
                return prescription
        
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Prescription not found")
    else:
        # Use real database - implement when needed
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Prescription not found")


@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_prescription(
    prescription_data: dict,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_flexible),
):
    """Create a new prescription"""
    import os
    
    if os.getenv("USE_DATABASE", "false").lower() == "false":
        # Mock creation
        new_prescription = {
            "id": len(MOCK_PRESCRIPTIONS) + 1,
            "patient_id": prescription_data.get("patient_id"),
            "doctor_id": prescription_data.get("doctor_id"),
            "doctor_name": "Dr. Médico",
            "issued_date": datetime.now().strftime("%Y-%m-%d"),
            "medications": prescription_data.get("medications", []),
            "notes": prescription_data.get("notes", ""),
            "status": "active",
            "created_at": datetime.now()
        }
        MOCK_PRESCRIPTIONS.append(new_prescription)
        return new_prescription
    else:
        # Use real database - implement when needed
        return {"message": "Prescription created successfully"}


@router.put("/{prescription_id}", response_model=dict)
async def update_prescription(
    prescription_id: int,
    prescription_data: dict,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_flexible),
):
    """Update a prescription"""
    import os
    
    if os.getenv("USE_DATABASE", "false").lower() == "false":
        # Mock update
        for i, prescription in enumerate(MOCK_PRESCRIPTIONS):
            if prescription["id"] == prescription_id:
                MOCK_PRESCRIPTIONS[i].update(prescription_data)
                return MOCK_PRESCRIPTIONS[i]
        
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Prescription not found")
    else:
        # Use real database - implement when needed
        return {"message": "Prescription updated successfully"}


@router.delete("/{prescription_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prescription(
    prescription_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_flexible),
):
    """Delete a prescription"""
    import os
    
    if os.getenv("USE_DATABASE", "false").lower() == "false":
        # Mock deletion
        global MOCK_PRESCRIPTIONS
        MOCK_PRESCRIPTIONS = [prescription for prescription in MOCK_PRESCRIPTIONS if prescription["id"] != prescription_id]
        return
    else:
        # Use real database - implement when needed
        return
