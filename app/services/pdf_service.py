"""
PDF Document Generation Service for Prontivus
Generates standardized PDF documents with Prontivus branding
"""

import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.platypus.frames import Frame
from reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import io

from app.core.config import settings

class ProntivusPDFGenerator:
    """Generate PDF documents with Prontivus branding"""
    
    def __init__(self):
        self.brand_name = settings.BRAND_NAME
        self.brand_slogan = settings.BRAND_SLOGAN
        self.owner_name = "Dr. Nivaldo Francisco Alves Filho"
        
        # Define colors
        self.primary_color = colors.HexColor(settings.BRAND_COLOR_PRIMARY)
        self.secondary_color = colors.HexColor(settings.BRAND_COLOR_SECONDARY)
        self.accent_color = colors.HexColor(settings.BRAND_COLOR_ACCENT)
        
        # Setup styles
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        # Header style
        self.styles.add(ParagraphStyle(
            name='ProntivusHeader',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=self.primary_color,
            alignment=TA_CENTER,
            spaceAfter=12,
            fontName='Helvetica-Bold'
        ))
        
        # Subheader style
        self.styles.add(ParagraphStyle(
            name='ProntivusSubheader',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=self.secondary_color,
            alignment=TA_CENTER,
            spaceAfter=8,
            fontName='Helvetica'
        ))
        
        # Body text style
        self.styles.add(ParagraphStyle(
            name='ProntivusBody',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.black,
            alignment=TA_JUSTIFY,
            spaceAfter=6,
            fontName='Helvetica'
        ))
        
        # Signature style
        self.styles.add(ParagraphStyle(
            name='ProntivusSignature',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.black,
            alignment=TA_CENTER,
            spaceAfter=20,
            fontName='Helvetica'
        ))
    
    def _create_header(self, story: List, clinic_name: str = None):
        """Create document header with Prontivus branding"""
        # Logo placeholder (you'll need to add actual logo file)
        # logo_path = os.path.join(settings.UPLOAD_DIR, "logo-prontivus.png")
        # if os.path.exists(logo_path):
        #     logo = Image(logo_path, width=2*inch, height=0.8*inch)
        #     story.append(logo)
        #     story.append(Spacer(1, 0.2*inch))
        
        # Brand name
        story.append(Paragraph(self.brand_name, self.styles['ProntivusHeader']))
        story.append(Paragraph(self.brand_slogan, self.styles['ProntivusSubheader']))
        
        # Clinic name if provided
        if clinic_name:
            story.append(Paragraph(f"<b>{clinic_name}</b>", self.styles['ProntivusBody']))
        
        story.append(Spacer(1, 0.3*inch))
    
    def _create_footer(self, story: List, document_type: str = "Documento"):
        """Create document footer with Prontivus branding"""
        story.append(Spacer(1, 0.5*inch))
        
        # Footer line
        footer_data = [
            [f"{self.brand_name} — {self.brand_slogan}", f"Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}"]
        ]
        
        footer_table = Table(footer_data, colWidths=[4*inch, 2*inch])
        footer_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.grey),
            ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        
        story.append(footer_table)
    
    def generate_prescription(self, prescription_data: Dict[str, Any]) -> bytes:
        """Generate prescription PDF"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*inch, bottomMargin=1*inch)
        story = []
        
        # Header
        self._create_header(story, prescription_data.get('clinic_name'))
        
        # Document title
        story.append(Paragraph("RECEITA MÉDICA", self.styles['ProntivusHeader']))
        story.append(Spacer(1, 0.2*inch))
        
        # Patient information
        patient_info = [
            ["<b>Paciente:</b>", prescription_data.get('patient_name', '')],
            ["<b>CPF:</b>", prescription_data.get('patient_cpf', '')],
            ["<b>Data de Nascimento:</b>", prescription_data.get('patient_birth_date', '')],
            ["<b>Data da Consulta:</b>", prescription_data.get('consultation_date', '')],
        ]
        
        patient_table = Table(patient_info, colWidths=[1.5*inch, 4*inch])
        patient_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        story.append(patient_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Prescription items
        story.append(Paragraph("<b>MEDICAÇÕES PRESCRITAS:</b>", self.styles['ProntivusBody']))
        story.append(Spacer(1, 0.1*inch))
        
        for item in prescription_data.get('medications', []):
            medication_text = f"""
            <b>{item.get('name', '')}</b><br/>
            {item.get('dosage', '')} - {item.get('frequency', '')}<br/>
            {item.get('instructions', '')}<br/>
            """
            story.append(Paragraph(medication_text, self.styles['ProntivusBody']))
            story.append(Spacer(1, 0.1*inch))
        
        # Additional instructions
        if prescription_data.get('additional_instructions'):
            story.append(Spacer(1, 0.2*inch))
            story.append(Paragraph("<b>INSTRUÇÕES ADICIONAIS:</b>", self.styles['ProntivusBody']))
            story.append(Paragraph(prescription_data['additional_instructions'], self.styles['ProntivusBody']))
        
        # Signature
        story.append(Spacer(1, 0.5*inch))
        signature_text = f"""
        {prescription_data.get('clinic_location', 'São Paulo')}, {datetime.now().strftime('%d de %B de %Y')}<br/><br/>
        _________________________<br/>
        <b>{prescription_data.get('doctor_name', self.owner_name)}</b><br/>
        CRM: {prescription_data.get('doctor_crm', '')}
        """
        story.append(Paragraph(signature_text, self.styles['ProntivusSignature']))
        
        # Footer
        self._create_footer(story, "Receita Médica")
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    
    def generate_medical_certificate(self, certificate_data: Dict[str, Any]) -> bytes:
        """Generate medical certificate PDF"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*inch, bottomMargin=1*inch)
        story = []
        
        # Header
        self._create_header(story, certificate_data.get('clinic_name'))
        
        # Document title
        story.append(Paragraph("ATESTADO MÉDICO", self.styles['ProntivusHeader']))
        story.append(Spacer(1, 0.3*inch))
        
        # Certificate content
        certificate_text = f"""
        Atesto para os devidos fins que o(a) paciente <b>{certificate_data.get('patient_name', '')}</b>, 
        portador(a) do CPF {certificate_data.get('patient_cpf', '')}, esteve sob meus cuidados médicos 
        em {certificate_data.get('consultation_date', '')}.
        """
        story.append(Paragraph(certificate_text, self.styles['ProntivusBody']))
        story.append(Spacer(1, 0.2*inch))
        
        # Medical condition
        if certificate_data.get('medical_condition'):
            condition_text = f"""
            <b>Diagnóstico:</b> {certificate_data['medical_condition']}
            """
            story.append(Paragraph(condition_text, self.styles['ProntivusBody']))
            story.append(Spacer(1, 0.2*inch))
        
        # Work leave period
        if certificate_data.get('work_leave_days'):
            leave_text = f"""
            Recomendo afastamento das atividades laborais por <b>{certificate_data['work_leave_days']} dias</b>, 
            a partir de {certificate_data.get('leave_start_date', '')}.
            """
            story.append(Paragraph(leave_text, self.styles['ProntivusBody']))
            story.append(Spacer(1, 0.2*inch))
        
        # Additional information
        if certificate_data.get('additional_info'):
            story.append(Paragraph(certificate_data['additional_info'], self.styles['ProntivusBody']))
            story.append(Spacer(1, 0.2*inch))
        
        # Signature
        story.append(Spacer(1, 0.5*inch))
        signature_text = f"""
        {certificate_data.get('clinic_location', 'São Paulo')}, {datetime.now().strftime('%d de %B de %Y')}<br/><br/>
        _________________________<br/>
        <b>{certificate_data.get('doctor_name', self.owner_name)}</b><br/>
        CRM: {certificate_data.get('doctor_crm', '')}
        """
        story.append(Paragraph(signature_text, self.styles['ProntivusSignature']))
        
        # Footer
        self._create_footer(story, "Atestado Médico")
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    
    def generate_medical_report(self, report_data: Dict[str, Any]) -> bytes:
        """Generate medical report PDF"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*inch, bottomMargin=1*inch)
        story = []
        
        # Header
        self._create_header(story, report_data.get('clinic_name'))
        
        # Document title
        story.append(Paragraph("RELATÓRIO MÉDICO", self.styles['ProntivusHeader']))
        story.append(Spacer(1, 0.2*inch))
        
        # Patient information
        patient_info = [
            ["<b>Paciente:</b>", report_data.get('patient_name', '')],
            ["<b>CPF:</b>", report_data.get('patient_cpf', '')],
            ["<b>Data de Nascimento:</b>", report_data.get('patient_birth_date', '')],
            ["<b>Data da Consulta:</b>", report_data.get('consultation_date', '')],
            ["<b>Médico Responsável:</b>", report_data.get('doctor_name', self.owner_name)],
        ]
        
        patient_table = Table(patient_info, colWidths=[1.5*inch, 4*inch])
        patient_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        story.append(patient_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Report sections
        sections = [
            ('HISTÓRIA CLÍNICA', report_data.get('clinical_history', '')),
            ('EXAME FÍSICO', report_data.get('physical_exam', '')),
            ('EVOLUÇÃO', report_data.get('evolution', '')),
            ('CONDUTA', report_data.get('conduct', '')),
        ]
        
        for section_title, section_content in sections:
            if section_content:
                story.append(Paragraph(f"<b>{section_title}:</b>", self.styles['ProntivusBody']))
                story.append(Paragraph(section_content, self.styles['ProntivusBody']))
                story.append(Spacer(1, 0.2*inch))
        
        # Signature
        story.append(Spacer(1, 0.5*inch))
        signature_text = f"""
        {report_data.get('clinic_location', 'São Paulo')}, {datetime.now().strftime('%d de %B de %Y')}<br/><br/>
        _________________________<br/>
        <b>{report_data.get('doctor_name', self.owner_name)}</b><br/>
        CRM: {report_data.get('doctor_crm', '')}
        """
        story.append(Paragraph(signature_text, self.styles['ProntivusSignature']))
        
        # Footer
        self._create_footer(story, "Relatório Médico")
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    
    def generate_receipt(self, receipt_data: Dict[str, Any]) -> bytes:
        """Generate payment receipt PDF"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*inch, bottomMargin=1*inch)
        story = []
        
        # Header
        self._create_header(story, receipt_data.get('clinic_name'))
        
        # Document title
        story.append(Paragraph("RECIBO DE PAGAMENTO", self.styles['ProntivusHeader']))
        story.append(Spacer(1, 0.2*inch))
        
        # Receipt information
        receipt_info = [
            ["<b>Número do Recibo:</b>", receipt_data.get('receipt_number', '')],
            ["<b>Data:</b>", receipt_data.get('payment_date', '')],
            ["<b>Paciente:</b>", receipt_data.get('patient_name', '')],
            ["<b>CPF:</b>", receipt_data.get('patient_cpf', '')],
            ["<b>Serviço:</b>", receipt_data.get('service_description', '')],
            ["<b>Valor:</b>", f"R$ {receipt_data.get('amount', '0,00')}"],
            ["<b>Forma de Pagamento:</b>", receipt_data.get('payment_method', '')],
        ]
        
        receipt_table = Table(receipt_info, colWidths=[1.5*inch, 4*inch])
        receipt_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        story.append(receipt_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Payment confirmation
        confirmation_text = f"""
        Confirmo o recebimento do valor de <b>R$ {receipt_data.get('amount', '0,00')}</b> 
        referente ao serviço de {receipt_data.get('service_description', '')} prestado ao(a) 
        paciente {receipt_data.get('patient_name', '')}.
        """
        story.append(Paragraph(confirmation_text, self.styles['ProntivusBody']))
        
        # Signature
        story.append(Spacer(1, 0.5*inch))
        signature_text = f"""
        {receipt_data.get('clinic_location', 'São Paulo')}, {datetime.now().strftime('%d de %B de %Y')}<br/><br/>
        _________________________<br/>
        <b>{receipt_data.get('clinic_name', 'Clínica')}</b><br/>
        CNPJ: {receipt_data.get('clinic_cnpj', '')}
        """
        story.append(Paragraph(signature_text, self.styles['ProntivusSignature']))
        
        # Footer
        self._create_footer(story, "Recibo de Pagamento")
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    
    def generate_declaration(self, declaration_data: Dict[str, Any]) -> bytes:
        """Generate medical declaration PDF"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*inch, bottomMargin=1*inch)
        story = []
        
        # Header
        self._create_header(story, declaration_data.get('clinic_name'))
        
        # Document title
        story.append(Paragraph("DECLARAÇÃO MÉDICA", self.styles['ProntivusHeader']))
        story.append(Spacer(1, 0.3*inch))
        
        # Declaration content
        declaration_text = f"""
        Declaro para os devidos fins que o(a) paciente <b>{declaration_data.get('patient_name', '')}</b>, 
        portador(a) do CPF {declaration_data.get('patient_cpf', '')}, foi atendido(a) em nossa clínica 
        em {declaration_data.get('consultation_date', '')}.
        """
        story.append(Paragraph(declaration_text, self.styles['ProntivusBody']))
        story.append(Spacer(1, 0.2*inch))
        
        # Purpose of declaration
        if declaration_data.get('purpose'):
            purpose_text = f"""
            <b>Finalidade:</b> {declaration_data['purpose']}
            """
            story.append(Paragraph(purpose_text, self.styles['ProntivusBody']))
            story.append(Spacer(1, 0.2*inch))
        
        # Additional information
        if declaration_data.get('additional_info'):
            story.append(Paragraph(declaration_data['additional_info'], self.styles['ProntivusBody']))
            story.append(Spacer(1, 0.2*inch))
        
        # Signature
        story.append(Spacer(1, 0.5*inch))
        signature_text = f"""
        {declaration_data.get('clinic_location', 'São Paulo')}, {datetime.now().strftime('%d de %B de %Y')}<br/><br/>
        _________________________<br/>
        <b>{declaration_data.get('doctor_name', self.owner_name)}</b><br/>
        CRM: {declaration_data.get('doctor_crm', '')}
        """
        story.append(Paragraph(signature_text, self.styles['ProntivusSignature']))
        
        # Footer
        self._create_footer(story, "Declaração Médica")
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    
    def generate_medical_guide(self, guide_data: Dict[str, Any]) -> bytes:
        """Generate medical guide/referral PDF"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*inch, bottomMargin=1*inch)
        story = []
        
        # Header
        self._create_header(story, guide_data.get('clinic_name'))
        
        # Document title
        story.append(Paragraph("GUIA MÉDICO", self.styles['ProntivusHeader']))
        story.append(Spacer(1, 0.2*inch))
        
        # Patient information
        patient_info = [
            ["<b>Paciente:</b>", guide_data.get('patient_name', '')],
            ["<b>CPF:</b>", guide_data.get('patient_cpf', '')],
            ["<b>Data de Nascimento:</b>", guide_data.get('patient_birth_date', '')],
            ["<b>Data da Consulta:</b>", guide_data.get('consultation_date', '')],
        ]
        
        patient_table = Table(patient_info, colWidths=[1.5*inch, 4*inch])
        patient_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        story.append(patient_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Guide information
        story.append(Paragraph("<b>ESPECIALIDADE SOLICITADA:</b>", self.styles['ProntivusBody']))
        story.append(Paragraph(guide_data.get('specialty', ''), self.styles['ProntivusBody']))
        story.append(Spacer(1, 0.2*inch))
        
        # Reason for referral
        if guide_data.get('reason'):
            story.append(Paragraph("<b>MOTIVO DO ENCAMINHAMENTO:</b>", self.styles['ProntivusBody']))
            story.append(Paragraph(guide_data['reason'], self.styles['ProntivusBody']))
            story.append(Spacer(1, 0.2*inch))
        
        # Diagnosis
        if guide_data.get('diagnosis'):
            story.append(Paragraph("<b>DIAGNÓSTICO:</b>", self.styles['ProntivusBody']))
            story.append(Paragraph(guide_data['diagnosis'], self.styles['ProntivusBody']))
            story.append(Spacer(1, 0.2*inch))
        
        # Additional information
        if guide_data.get('additional_info'):
            story.append(Paragraph("<b>INFORMAÇÕES ADICIONAIS:</b>", self.styles['ProntivusBody']))
            story.append(Paragraph(guide_data['additional_info'], self.styles['ProntivusBody']))
            story.append(Spacer(1, 0.2*inch))
        
        # Signature
        story.append(Spacer(1, 0.5*inch))
        signature_text = f"""
        {guide_data.get('clinic_location', 'São Paulo')}, {datetime.now().strftime('%d de %B de %Y')}<br/><br/>
        _________________________<br/>
        <b>{guide_data.get('doctor_name', self.owner_name)}</b><br/>
        CRM: {guide_data.get('doctor_crm', '')}
        """
        story.append(Paragraph(signature_text, self.styles['ProntivusSignature']))
        
        # Footer
        self._create_footer(story, "Guia Médico")
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    
    def generate_exam_request(self, exam_data: Dict[str, Any]) -> bytes:
        """Generate exam request PDF"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*inch, bottomMargin=1*inch)
        story = []
        
        # Header
        self._create_header(story, exam_data.get('clinic_name'))
        
        # Document title
        story.append(Paragraph("SOLICITAÇÃO DE EXAMES", self.styles['ProntivusHeader']))
        story.append(Spacer(1, 0.2*inch))
        
        # Patient information
        patient_info = [
            ["<b>Paciente:</b>", exam_data.get('patient_name', '')],
            ["<b>CPF:</b>", exam_data.get('patient_cpf', '')],
            ["<b>Data de Nascimento:</b>", exam_data.get('patient_birth_date', '')],
            ["<b>Data da Solicitação:</b>", exam_data.get('request_date', '')],
        ]
        
        patient_table = Table(patient_info, colWidths=[1.5*inch, 4*inch])
        patient_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        story.append(patient_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Requested exams
        story.append(Paragraph("<b>EXAMES SOLICITADOS:</b>", self.styles['ProntivusBody']))
        story.append(Spacer(1, 0.1*inch))
        
        for exam in exam_data.get('exams', []):
            exam_text = f"""
            <b>{exam.get('name', '')}</b><br/>
            {exam.get('description', '')}<br/>
            """
            story.append(Paragraph(exam_text, self.styles['ProntivusBody']))
            story.append(Spacer(1, 0.1*inch))
        
        # Clinical indication
        if exam_data.get('clinical_indication'):
            story.append(Spacer(1, 0.2*inch))
            story.append(Paragraph("<b>INDICAÇÃO CLÍNICA:</b>", self.styles['ProntivusBody']))
            story.append(Paragraph(exam_data['clinical_indication'], self.styles['ProntivusBody']))
            story.append(Spacer(1, 0.2*inch))
        
        # Signature
        story.append(Spacer(1, 0.5*inch))
        signature_text = f"""
        {exam_data.get('clinic_location', 'São Paulo')}, {datetime.now().strftime('%d de %B de %Y')}<br/><br/>
        _________________________<br/>
        <b>{exam_data.get('doctor_name', self.owner_name)}</b><br/>
        CRM: {exam_data.get('doctor_crm', '')}
        """
        story.append(Paragraph(signature_text, self.styles['ProntivusSignature']))
        
        # Footer
        self._create_footer(story, "Solicitação de Exames")
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()

# Global PDF generator instance
pdf_generator = ProntivusPDFGenerator()
