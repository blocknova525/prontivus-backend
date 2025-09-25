"""
Document generation API endpoints
PDF generation with Prontivus branding
"""

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Dict, Any
import io

from app.database.database import get_db
from app.services.pdf_service import pdf_generator
from app.core.config import settings

router = APIRouter()

@router.post("/prescription")
async def generate_prescription(
    prescription_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Generate prescription PDF with Prontivus branding"""
    try:
        # Generate PDF
        pdf_content = pdf_generator.generate_prescription(prescription_data)
        
        # Return PDF as streaming response
        return StreamingResponse(
            io.BytesIO(pdf_content),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=receita_{prescription_data.get('patient_name', 'paciente')}.pdf"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating prescription: {str(e)}")

@router.post("/certificate")
async def generate_certificate(
    certificate_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Generate medical certificate PDF with Prontivus branding"""
    try:
        # Generate PDF
        pdf_content = pdf_generator.generate_medical_certificate(certificate_data)
        
        # Return PDF as streaming response
        return StreamingResponse(
            io.BytesIO(pdf_content),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=atestado_{certificate_data.get('patient_name', 'paciente')}.pdf"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating certificate: {str(e)}")

@router.post("/report")
async def generate_medical_report(
    report_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Generate medical report PDF with Prontivus branding"""
    try:
        # Generate PDF
        pdf_content = pdf_generator.generate_medical_report(report_data)
        
        # Return PDF as streaming response
        return StreamingResponse(
            io.BytesIO(pdf_content),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=relatorio_{report_data.get('patient_name', 'paciente')}.pdf"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")

@router.post("/receipt")
async def generate_receipt(
    receipt_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Generate payment receipt PDF with Prontivus branding"""
    try:
        # Generate PDF
        pdf_content = pdf_generator.generate_receipt(receipt_data)
        
        # Return PDF as streaming response
        return StreamingResponse(
            io.BytesIO(pdf_content),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=recibo_{receipt_data.get('receipt_number', 'pagamento')}.pdf"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating receipt: {str(e)}")

@router.post("/declaration")
async def generate_declaration(
    declaration_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Generate medical declaration PDF with Prontivus branding"""
    try:
        # Generate PDF
        pdf_content = pdf_generator.generate_declaration(declaration_data)
        
        # Return PDF as streaming response
        return StreamingResponse(
            io.BytesIO(pdf_content),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=declaracao_{declaration_data.get('patient_name', 'paciente')}.pdf"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating declaration: {str(e)}")

@router.post("/guide")
async def generate_medical_guide(
    guide_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Generate medical guide/referral PDF with Prontivus branding"""
    try:
        # Generate PDF
        pdf_content = pdf_generator.generate_medical_guide(guide_data)
        
        # Return PDF as streaming response
        return StreamingResponse(
            io.BytesIO(pdf_content),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=guia_{guide_data.get('patient_name', 'paciente')}.pdf"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating guide: {str(e)}")

@router.post("/exam-request")
async def generate_exam_request(
    exam_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Generate exam request PDF with Prontivus branding"""
    try:
        # Generate PDF
        pdf_content = pdf_generator.generate_exam_request(exam_data)
        
        # Return PDF as streaming response
        return StreamingResponse(
            io.BytesIO(pdf_content),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=solicitacao_exames_{exam_data.get('patient_name', 'paciente')}.pdf"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating exam request: {str(e)}")

@router.get("/templates")
async def get_document_templates():
    """Get available document templates"""
    return {
        "templates": [
            {
                "id": "prescription",
                "name": "Receita Médica",
                "description": "Prescrição de medicamentos com assinatura digital",
                "fields": [
                    "patient_name", "patient_cpf", "patient_birth_date",
                    "consultation_date", "medications", "doctor_name", "doctor_crm"
                ]
            },
            {
                "id": "certificate", 
                "name": "Atestado Médico",
                "description": "Atestado médico para afastamento do trabalho",
                "fields": [
                    "patient_name", "patient_cpf", "consultation_date",
                    "medical_condition", "work_leave_days", "doctor_name", "doctor_crm"
                ]
            },
            {
                "id": "report",
                "name": "Relatório Médico", 
                "description": "Relatório completo do atendimento médico",
                "fields": [
                    "patient_name", "patient_cpf", "consultation_date",
                    "clinical_history", "physical_exam", "evolution", "conduct",
                    "doctor_name", "doctor_crm"
                ]
            },
            {
                "id": "receipt",
                "name": "Recibo de Pagamento",
                "description": "Comprovante de pagamento de serviços médicos",
                "fields": [
                    "patient_name", "patient_cpf", "service_description",
                    "amount", "payment_method", "payment_date", "receipt_number"
                ]
            },
            {
                "id": "declaration",
                "name": "Declaração Médica",
                "description": "Declaração médica para diversos fins",
                "fields": [
                    "patient_name", "patient_cpf", "consultation_date",
                    "purpose", "additional_info", "doctor_name", "doctor_crm"
                ]
            },
            {
                "id": "guide",
                "name": "Guia Médico",
                "description": "Guia para encaminhamento a especialistas",
                "fields": [
                    "patient_name", "patient_cpf", "consultation_date",
                    "specialty", "reason", "diagnosis", "additional_info",
                    "doctor_name", "doctor_crm"
                ]
            },
            {
                "id": "exam-request",
                "name": "Solicitação de Exames",
                "description": "Solicitação de exames laboratoriais e de imagem",
                "fields": [
                    "patient_name", "patient_cpf", "request_date",
                    "exams", "clinical_indication", "doctor_name", "doctor_crm"
                ]
            }
        ],
        "branding": {
            "name": settings.BRAND_NAME,
            "slogan": settings.BRAND_SLOGAN,
            "colors": {
                "primary": settings.BRAND_COLOR_PRIMARY,
                "secondary": settings.BRAND_COLOR_SECONDARY,
                "accent": settings.BRAND_COLOR_ACCENT
            }
        }
    }
