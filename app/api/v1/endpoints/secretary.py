"""
Secretary Module API Endpoints
Patient check-in, insurance verification, document upload, exam inclusion, consultation release
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import os
import uuid
from pathlib import Path

from ....database.database import get_db
from ....models.secretary import (
    PatientCheckIn, PatientDocument, PatientExam, DailyAgenda, 
    WaitingPanel, InsuranceShortcut, CheckInStatus, InsuranceVerificationStatus, DocumentType
)
from ....models.patient import Patient
from ....models.appointment import Appointment
from ....models.user import User
from ..dependencies.auth import get_current_user_flexible
from ....schemas.secretary import (
    PatientCheckInCreate, PatientCheckInUpdate, PatientCheckInResponse,
    PatientDocumentCreate, PatientDocumentResponse,
    PatientExamCreate, PatientExamResponse,
    DailyAgendaResponse, WaitingPanelResponse,
    InsuranceShortcutCreate, InsuranceShortcutResponse
)

router = APIRouter()

# File upload directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@router.post("/check-in", response_model=dict)
async def check_in_patient(
    check_in_data: dict,
    current_user=Depends(get_current_user_flexible),
    db: Session = Depends(get_db)
):
    """Check in a patient"""
    # Verify patient exists
    patient = db.query(Patient).filter(Patient.id == check_in_data.patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    # Check if already checked in today
    today = datetime.now().date()
    existing_checkin = db.query(PatientCheckIn).filter(
        PatientCheckIn.patient_id == check_in_data.patient_id,
        PatientCheckIn.check_in_time >= datetime.combine(today, datetime.min.time()),
        PatientCheckIn.check_in_time < datetime.combine(today, datetime.max.time())
    ).first()
    
    if existing_checkin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Patient already checked in today"
        )
    
    # Create check-in record
    checkin = PatientCheckIn(
        tenant_id=current_user.tenant_id,
        patient_id=check_in_data.patient_id,
        appointment_id=check_in_data.appointment_id,
        checked_in_by=current_user.id,
        arrival_method=check_in_data.arrival_method,
        notes=check_in_data.notes,
        priority_level=check_in_data.priority_level or 1,
        waiting_start_time=datetime.utcnow()
    )
    
    db.add(checkin)
    db.commit()
    db.refresh(checkin)
    
    return checkin

@router.get("/check-ins", response_model=List[PatientCheckInResponse])
async def get_check_ins(
    status: Optional[CheckInStatus] = None,
    date: Optional[str] = None,
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """Get patient check-ins"""
    query = db.query(PatientCheckIn).filter(PatientCheckIn.tenant_id == current_user.tenant_id)
    
    if status:
        query = query.filter(PatientCheckIn.status == status)
    
    if date:
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
            query = query.filter(
                PatientCheckIn.check_in_time >= datetime.combine(target_date, datetime.min.time()),
                PatientCheckIn.check_in_time < datetime.combine(target_date, datetime.max.time())
            )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD"
            )
    
    checkins = query.order_by(PatientCheckIn.check_in_time.desc()).all()
    return checkins

@router.put("/check-in/{checkin_id}/status", response_model=PatientCheckInResponse)
async def update_check_in_status(
    checkin_id: int,
    new_status: CheckInStatus,
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """Update check-in status"""
    checkin = db.query(PatientCheckIn).filter(
        PatientCheckIn.id == checkin_id,
        PatientCheckIn.tenant_id == current_user.tenant_id
    ).first()
    
    if not checkin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Check-in not found"
        )
    
    # Update status and timestamps
    checkin.status = new_status
    checkin.updated_at = datetime.utcnow()
    
    if new_status == CheckInStatus.CALLED:
        checkin.called_time = datetime.utcnow()
    elif new_status == CheckInStatus.IN_CONSULTATION:
        checkin.consultation_start_time = datetime.utcnow()
    elif new_status == CheckInStatus.COMPLETED:
        checkin.completion_time = datetime.utcnow()
    
    db.commit()
    db.refresh(checkin)
    
    return checkin

@router.post("/insurance/verify/{checkin_id}")
async def verify_insurance(
    checkin_id: int,
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """Verify patient insurance"""
    checkin = db.query(PatientCheckIn).filter(
        PatientCheckIn.id == checkin_id,
        PatientCheckIn.tenant_id == current_user.tenant_id
    ).first()
    
    if not checkin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Check-in not found"
        )
    
    patient = db.query(Patient).filter(Patient.id == checkin.patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    # TODO: Implement actual insurance verification logic
    # This would typically involve API calls to insurance providers
    
    checkin.insurance_verified = True
    checkin.insurance_verification_status = InsuranceVerificationStatus.VERIFIED
    checkin.insurance_verification_date = datetime.utcnow()
    checkin.insurance_notes = f"Insurance verified by {current_user.full_name}"
    
    db.commit()
    
    return {
        "message": "Insurance verified successfully",
        "status": "verified",
        "verified_at": checkin.insurance_verification_date
    }

@router.post("/documents/upload", response_model=PatientDocumentResponse)
async def upload_document(
    patient_id: int = Form(...),
    document_type: DocumentType = Form(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    checkin_id: Optional[int] = Form(None),
    file: UploadFile = File(...),
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """Upload patient document"""
    # Verify patient exists
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    # Generate unique filename
    file_extension = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = UPLOAD_DIR / unique_filename
    
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )
    
    # Create document record
    document = PatientDocument(
        tenant_id=current_user.tenant_id,
        patient_id=patient_id,
        checkin_id=checkin_id,
        document_type=document_type,
        title=title,
        description=description,
        file_name=file.filename,
        file_path=str(file_path),
        file_size=len(content),
        mime_type=file.content_type,
        uploaded_by=current_user.id
    )
    
    db.add(document)
    db.commit()
    db.refresh(document)
    
    return document

@router.get("/documents/{patient_id}", response_model=List[PatientDocumentResponse])
async def get_patient_documents(
    patient_id: int,
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """Get patient documents"""
    documents = db.query(PatientDocument).filter(
        PatientDocument.patient_id == patient_id,
        PatientDocument.tenant_id == current_user.tenant_id,
        PatientDocument.is_active == True
    ).order_by(PatientDocument.uploaded_at.desc()).all()
    
    return documents

@router.post("/exams", response_model=PatientExamResponse)
async def add_patient_exam(
    exam_data: PatientExamCreate,
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """Add patient exam"""
    # Verify patient exists
    patient = db.query(Patient).filter(Patient.id == exam_data.patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    exam = PatientExam(
        tenant_id=current_user.tenant_id,
        patient_id=exam_data.patient_id,
        checkin_id=exam_data.checkin_id,
        exam_type=exam_data.exam_type,
        exam_name=exam_data.exam_name,
        exam_date=exam_data.exam_date,
        laboratory=exam_data.laboratory,
        doctor_requesting=exam_data.doctor_requesting,
        results_summary=exam_data.results_summary,
        normal_range=exam_data.normal_range,
        interpretation=exam_data.interpretation,
        processed_by=current_user.id,
        processed_at=datetime.utcnow()
    )
    
    db.add(exam)
    db.commit()
    db.refresh(exam)
    
    return exam

@router.get("/daily-agenda/{doctor_id}", response_model=DailyAgendaResponse)
async def get_daily_agenda(
    doctor_id: int,
    date: Optional[str] = None,
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """Get daily agenda for a doctor"""
    target_date = datetime.now().date()
    if date:
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD"
            )
    
    # Get appointments for the day
    appointments = db.query(Appointment).filter(
        Appointment.doctor_id == doctor_id,
        Appointment.tenant_id == current_user.tenant_id,
        Appointment.appointment_date >= datetime.combine(target_date, datetime.min.time()),
        Appointment.appointment_date < datetime.combine(target_date, datetime.max.time())
    ).all()
    
    # Calculate statistics
    total_appointments = len(appointments)
    completed_appointments = len([a for a in appointments if a.status.value == "completed"])
    cancelled_appointments = len([a for a in appointments if a.status.value == "cancelled"])
    no_show_appointments = len([a for a in appointments if a.status.value == "no_show"])
    
    agenda = DailyAgenda(
        tenant_id=current_user.tenant_id,
        doctor_id=doctor_id,
        agenda_date=datetime.combine(target_date, datetime.min.time()),
        total_appointments=total_appointments,
        completed_appointments=completed_appointments,
        cancelled_appointments=cancelled_appointments,
        no_show_appointments=no_show_appointments
    )
    
    return agenda

@router.get("/waiting-panel", response_model=List[PatientCheckInResponse])
async def get_waiting_panel(
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """Get waiting panel - patients currently waiting"""
    waiting_patients = db.query(PatientCheckIn).filter(
        PatientCheckIn.tenant_id == current_user.tenant_id,
        PatientCheckIn.status.in_([CheckInStatus.WAITING, CheckInStatus.CALLED])
    ).order_by(PatientCheckIn.priority_level.desc(), PatientCheckIn.check_in_time.asc()).all()
    
    return waiting_patients

@router.post("/insurance-shortcuts", response_model=InsuranceShortcutResponse)
async def create_insurance_shortcut(
    shortcut_data: InsuranceShortcutCreate,
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """Create insurance verification shortcut"""
    shortcut = InsuranceShortcut(
        tenant_id=current_user.tenant_id,
        insurance_name=shortcut_data.insurance_name,
        insurance_code=shortcut_data.insurance_code,
        contact_phone=shortcut_data.contact_phone,
        contact_email=shortcut_data.contact_email,
        verification_url=shortcut_data.verification_url,
        api_endpoint=shortcut_data.api_endpoint,
        requires_auth=shortcut_data.requires_auth,
        auth_token=shortcut_data.auth_token,
        valid_codes=shortcut_data.valid_codes,
        invalid_codes=shortcut_data.invalid_codes
    )
    
    db.add(shortcut)
    db.commit()
    db.refresh(shortcut)
    
    return shortcut

@router.get("/insurance-shortcuts", response_model=List[InsuranceShortcutResponse])
async def get_insurance_shortcuts(
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """Get insurance verification shortcuts"""
    shortcuts = db.query(InsuranceShortcut).filter(
        InsuranceShortcut.tenant_id == current_user.tenant_id,
        InsuranceShortcut.is_active == True
    ).all()
    
    return shortcuts
