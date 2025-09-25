"""
Appointment endpoints
"""

from fastapi import APIRouter, Depends, status, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date, time
from enum import Enum

from app.database.database import get_db
from app.schemas.appointment import Appointment as AppointmentSchema, AppointmentCreate, AppointmentUpdate
from app.services.appointment_service import AppointmentService
from app.api.v1.dependencies.auth import get_current_user_flexible
from ....services.change_tracking_service import get_change_tracker

router = APIRouter()

# Mock data for development
class AppointmentStatus(str, Enum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"

class AppointmentType(str, Enum):
    CONSULTATION = "consultation"
    FOLLOW_UP = "follow_up"
    EMERGENCY = "emergency"
    PROCEDURE = "procedure"
    EXAMINATION = "examination"
    THERAPY = "therapy"

# Mock appointments data
MOCK_APPOINTMENTS = [
    {
        "id": 1,
        "patient_id": 2,
        "doctor_id": 2,
        "appointment_date": date(2025, 9, 20),
        "appointment_time": time(10, 0),
        "type": AppointmentType.CONSULTATION,
        "status": AppointmentStatus.SCHEDULED,
        "notes": "Consulta de rotina",
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    },
    {
        "id": 2,
        "patient_id": 3,
        "doctor_id": 2,
        "appointment_date": date(2025, 9, 24),
        "appointment_time": time(14, 30),
        "type": AppointmentType.FOLLOW_UP,
        "status": AppointmentStatus.CONFIRMED,
        "notes": "Retorno após tratamento",
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    },
    {
        "id": 3,
        "patient_id": 4,
        "doctor_id": 2,
        "appointment_date": date(2025, 10, 14),
        "appointment_time": time(9, 15),
        "type": AppointmentType.EXAMINATION,
        "status": AppointmentStatus.SCHEDULED,
        "notes": "Exame de rotina",
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    },
    {
        "id": 4,
        "patient_id": 2,
        "doctor_id": 2,
        "appointment_date": date(2025, 10, 13),
        "appointment_time": time(16, 0),
        "type": AppointmentType.CONSULTATION,
        "status": AppointmentStatus.CONFIRMED,
        "notes": "Consulta especializada",
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    },
    {
        "id": 5,
        "patient_id": 3,
        "doctor_id": 2,
        "appointment_date": date(2025, 10, 1),
        "appointment_time": time(11, 30),
        "type": AppointmentType.FOLLOW_UP,
        "status": AppointmentStatus.COMPLETED,
        "notes": "Consulta finalizada",
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    },
    {
        "id": 6,
        "patient_id": 5,
        "doctor_id": 2,
        "doctor_name": "Dr. João Silva",
        "doctor_specialty": "Clínica Geral",
        "appointment_date": date(2025, 9, 25),
        "appointment_time": time(15, 0),
        "type": AppointmentType.CONSULTATION,
        "status": AppointmentStatus.SCHEDULED,
        "notes": "Consulta de rotina - Paciente 5",
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    },
    {
        "id": 7,
        "patient_id": 5,
        "doctor_id": 2,
        "doctor_name": "Dr. João Silva",
        "doctor_specialty": "Clínica Geral",
        "appointment_date": date(2025, 10, 2),
        "appointment_time": time(10, 30),
        "type": AppointmentType.FOLLOW_UP,
        "status": AppointmentStatus.CONFIRMED,
        "notes": "Retorno - Paciente 5",
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
]


@router.get("/", response_model=List[AppointmentSchema])
async def list_appointments(
    patient_id: Optional[int] = Query(None),
    doctor_id: Optional[int] = Query(None),
    date: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_flexible),
):
    # Always use mock data for now (until we fix the schema mismatch)
    import os
    appointments = MOCK_APPOINTMENTS.copy()
    
    # For patients, only show their own appointments
    if current_user["type"] == "patient":
        appointments = [apt for apt in appointments if apt["patient_id"] == current_user["id"]]
    else:
        # For staff, filter by provided parameters
        if patient_id:
            appointments = [apt for apt in appointments if apt["patient_id"] == patient_id]
        
        if doctor_id:
            appointments = [apt for apt in appointments if apt["doctor_id"] == doctor_id]
    
    # Filter by status if provided
    if status:
        appointments = [apt for apt in appointments if apt["status"].value == status]
    
    # Filter by type if provided
    if type:
        appointments = [apt for apt in appointments if apt["type"].value == type]
    
    # Enrich appointments with doctor information
    doctor_info = {
        1: {"name": "Dr. Carlos Mendes", "specialty": "Cardiologia"},
        2: {"name": "Dr. João Silva", "specialty": "Clínica Geral"},
        3: {"name": "Dra. Maria Santos", "specialty": "Pediatria"},
        4: {"name": "Dr. Pedro Costa", "specialty": "Ortopedia"},
        5: {"name": "Dra. Ana Lima", "specialty": "Dermatologia"}
    }
    
    # Convert appointments to dict format and handle enum values
    enriched_appointments = []
    for apt in appointments:
        apt_dict = dict(apt)
        
        # Convert enum values to strings
        if hasattr(apt_dict.get("status"), 'value'):
            apt_dict["status"] = apt_dict["status"].value
        if hasattr(apt_dict.get("type"), 'value'):
            apt_dict["type"] = apt_dict["type"].value
            
        enriched_appointments.append(apt_dict)
    
    return enriched_appointments


@router.get("/{appt_id}", response_model=dict)
async def get_appointment(
    appt_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_flexible),
):
    """Get a specific appointment by ID using direct SQL"""
    try:
        from sqlalchemy import text
        
        query = """
            SELECT id, tenant_id, patient_id, doctor_id, appointment_date,
                   duration_minutes, type, status, location, reason, notes,
                   reminder_sent, scheduled_at
            FROM appointments
            WHERE id = :appointment_id
        """
        
        cursor = db.execute(text(query), {"appointment_id": appt_id})
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        # Parse datetime into date and time
        appointment_datetime = str(row[4]) if row[4] else None
        appointment_date = None
        appointment_time = None
        
        if appointment_datetime:
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(appointment_datetime.replace('Z', '+00:00'))
                appointment_date = dt.date().isoformat()
                appointment_time = dt.time().isoformat()
            except:
                appointment_date = appointment_datetime.split(' ')[0] if ' ' in appointment_datetime else appointment_datetime
                appointment_time = appointment_datetime.split(' ')[1] if ' ' in appointment_datetime else "09:00:00"
        
        appointment = {
            "id": row[0],
            "tenant_id": row[1],
            "patient_id": row[2],
            "doctor_id": row[3],
            "appointment_date": appointment_date,
            "appointment_time": appointment_time,
            "duration_minutes": row[5],
            "type": row[6],
            "status": row[7],
            "location": row[8],
            "reason": row[9],
            "notes": row[10],
            "reminder_sent": bool(row[11]),
            "scheduled_at": str(row[12]) if row[12] else None
        }
        
        return appointment
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Database query failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve appointment")


@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    payload: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_flexible),
):
    """Create a new appointment using direct SQL"""
    try:
        from sqlalchemy import text
        
        print(f"DEBUG: Received payload: {payload}")
        print(f"DEBUG: Current user: {current_user}")
        
        # Validate required fields
        if not payload.patient_id or not payload.doctor_id or not payload.appointment_date:
            print(f"DEBUG: Missing required fields")
            raise HTTPException(status_code=400, detail="Required fields: patient_id, doctor_id, appointment_date")
        
        # Combine date and time into datetime
        appointment_datetime = f"{payload.appointment_date} {payload.appointment_time}"
        print(f"DEBUG: Combined datetime: {appointment_datetime}")
        
        # Insert the appointment
        insert_query = """
            INSERT INTO appointments (
                tenant_id, patient_id, doctor_id, appointment_date,
                duration_minutes, type, status, location, reason, notes,
                reminder_sent, scheduled_at
            ) VALUES (
                :tenant_id, :patient_id, :doctor_id, :appointment_date,
                :duration_minutes, :type, :status, :location, :reason, :notes,
                :reminder_sent, CURRENT_TIMESTAMP
            )
        """
        
        params = {
            "tenant_id": current_user.get("tenant_id", 1),
            "patient_id": payload.patient_id,
            "doctor_id": payload.doctor_id,
            "appointment_date": appointment_datetime,
            "duration_minutes": payload.duration_minutes or 60,
            "type": payload.type.value if payload.type else "consultation",
            "status": payload.status.value if payload.status else "scheduled",
            "location": payload.location or "Consultório",
            "reason": payload.reason,
            "notes": payload.notes,
            "reminder_sent": payload.reminder_sent or False
        }
        
        print(f"DEBUG: Insert query: {insert_query}")
        print(f"DEBUG: Parameters: {params}")
        
        result = db.execute(text(insert_query), params)
        db.commit()
        
        # Get the created appointment ID
        appointment_id = result.lastrowid
        print(f"DEBUG: Created appointment ID: {appointment_id}")
        
        # Track the change
        change_tracker = get_change_tracker(db)
        change_tracker.track_appointment_change(
            appointment_id=appointment_id,
            change_type="created",
            old_data=None,
            new_data=payload
        )
        
        # Return the created appointment
        return await get_appointment(appointment_id, db, current_user)
        
    except HTTPException as he:
        print(f"DEBUG: HTTPException: {he.detail}")
        raise he
    except Exception as e:
        print(f"DEBUG: Database insert failed: {e}")
        print(f"DEBUG: Exception type: {type(e)}")
        print(f"DEBUG: Exception args: {e.args}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create appointment: {str(e)}")


@router.put("/{appt_id}", response_model=AppointmentSchema)
async def update_appointment(
    appt_id: int,
    payload: AppointmentUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_flexible),
):
    service = AppointmentService(db)
    return service.update_appointment(appt_id, payload, tenant_id=getattr(current_user, "tenant_id", 0) or 0)


@router.delete("/{appt_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_appointment(
    appt_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_flexible),
):
    service = AppointmentService(db)
    service.delete_appointment(appt_id, tenant_id=getattr(current_user, "tenant_id", 0) or 0)
    return {"status": "deleted"}


