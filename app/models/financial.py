"""
Financial Module Models
Billing dashboard (TISS/private), accounts receivable, delinquency, physician payouts, revenue/expense charts
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Enum, JSON, Numeric, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timedelta
import enum

from .base import Base

class BillingType(str, enum.Enum):
    """Billing type enum"""
    TISS = "tiss"  # Brazilian health insurance standard
    PRIVATE = "private"
    CASH = "cash"
    INSURANCE = "insurance"
    CORPORATE = "corporate"

class PaymentStatus(str, enum.Enum):
    """Payment status enum"""
    PENDING = "pending"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    DISPUTED = "disputed"

class PaymentMethod(str, enum.Enum):
    """Payment method enum"""
    CASH = "cash"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    BANK_TRANSFER = "bank_transfer"
    CHECK = "check"
    INSURANCE = "insurance"
    PIX = "pix"  # Brazilian instant payment
    BOLETO = "boleto"  # Brazilian bank slip

class InvoiceStatus(str, enum.Enum):
    """Invoice status enum"""
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"

class RevenueType(str, enum.Enum):
    """Revenue type enum"""
    CONSULTATION = "consultation"
    PROCEDURE = "procedure"
    EXAM = "exam"
    MEDICATION = "medication"
    OTHER = "other"

class ExpenseType(str, enum.Enum):
    """Expense type enum"""
    SALARY = "salary"
    RENT = "rent"
    UTILITIES = "utilities"
    EQUIPMENT = "equipment"
    MEDICATION = "medication"
    SUPPLIES = "supplies"
    MARKETING = "marketing"
    OTHER = "other"

class Billing(Base):
    """Billing model for healthcare services"""
    __tablename__ = "billings"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Billing details
    billing_number = Column(String(50), unique=True, nullable=False, index=True)
    billing_type = Column(Enum(BillingType), nullable=False)
    billing_date = Column(Date, nullable=False, default=func.current_date())
    due_date = Column(Date, nullable=False)
    
    # Financial details
    subtotal = Column(Numeric(10, 2), nullable=False)
    tax_amount = Column(Numeric(10, 2), default=0)
    discount_amount = Column(Numeric(10, 2), default=0)
    total_amount = Column(Numeric(10, 2), nullable=False)
    paid_amount = Column(Numeric(10, 2), default=0)
    balance_amount = Column(Numeric(10, 2), nullable=False)
    
    # Payment information
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    payment_method = Column(Enum(PaymentMethod), nullable=True)
    payment_date = Column(DateTime(timezone=True), nullable=True)
    
    # Insurance information
    insurance_company = Column(String(255), nullable=True)
    insurance_number = Column(String(50), nullable=True)
    authorization_number = Column(String(50), nullable=True)
    copay_amount = Column(Numeric(10, 2), nullable=True)
    
    # TISS specific fields
    tiss_version = Column(String(10), nullable=True)  # TISS version
    tiss_guia = Column(String(50), nullable=True)  # TISS guide number
    tiss_status = Column(String(20), nullable=True)  # TISS processing status
    
    # Additional information
    notes = Column(Text, nullable=True)
    internal_notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    tenant = relationship("Tenant")
    patient = relationship("Patient")
    appointment = relationship("Appointment")
    doctor = relationship("User", foreign_keys=[doctor_id])
    creator = relationship("User", foreign_keys=[created_by])
    billing_items = relationship("BillingItem", back_populates="billing")
    payments = relationship("BillingPayment", back_populates="billing")

class BillingItem(Base):
    """Billing item model for individual services/products"""
    __tablename__ = "billing_items"
    
    id = Column(Integer, primary_key=True, index=True)
    billing_id = Column(Integer, ForeignKey("billings.id"), nullable=False)
    
    # Item details
    item_type = Column(String(50), nullable=False)  # service, product, exam, etc.
    item_code = Column(String(50), nullable=True)  # procedure code, product code
    item_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Pricing
    quantity = Column(Numeric(10, 2), nullable=False, default=1)
    unit_price = Column(Numeric(10, 2), nullable=False)
    total_price = Column(Numeric(10, 2), nullable=False)
    
    # Medical coding
    cpt_code = Column(String(10), nullable=True)  # Current Procedural Terminology
    icd10_code = Column(String(10), nullable=True)  # ICD-10 diagnosis code
    modifier_code = Column(String(10), nullable=True)  # CPT modifier
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    billing = relationship("Billing", back_populates="billing_items")

class BillingPayment(Base):
    """Payment model for billing payments"""
    __tablename__ = "billing_payments"
    
    id = Column(Integer, primary_key=True, index=True)
    billing_id = Column(Integer, ForeignKey("billings.id"), nullable=False)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    
    # Payment details
    payment_number = Column(String(50), unique=True, nullable=False, index=True)
    payment_date = Column(DateTime(timezone=True), nullable=False)
    payment_method = Column(Enum(PaymentMethod), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    
    # Payment processing
    transaction_id = Column(String(100), nullable=True)
    authorization_code = Column(String(50), nullable=True)
    processor_response = Column(JSON, nullable=True)
    
    # Bank information
    bank_name = Column(String(100), nullable=True)
    account_number = Column(String(50), nullable=True)
    check_number = Column(String(20), nullable=True)
    
    # Status
    status = Column(String(20), default="completed")  # pending, completed, failed, refunded
    is_refunded = Column(Boolean, default=False)
    refund_amount = Column(Numeric(10, 2), nullable=True)
    refund_date = Column(DateTime(timezone=True), nullable=True)
    
    # Additional information
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    processed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    billing = relationship("Billing", back_populates="payments")
    processor = relationship("User", foreign_keys=[processed_by])

class AccountsReceivable(Base):
    """Accounts receivable model for tracking outstanding payments"""
    __tablename__ = "accounts_receivable"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    billing_id = Column(Integer, ForeignKey("billings.id"), nullable=False)
    
    # Receivable details
    invoice_number = Column(String(50), nullable=False)
    invoice_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    original_amount = Column(Numeric(10, 2), nullable=False)
    outstanding_amount = Column(Numeric(10, 2), nullable=False)
    
    # Aging information
    days_overdue = Column(Integer, default=0)
    aging_bucket = Column(String(20), nullable=False)  # current, 30, 60, 90, 120+
    
    # Collection information
    last_payment_date = Column(Date, nullable=True)
    last_payment_amount = Column(Numeric(10, 2), nullable=True)
    collection_attempts = Column(Integer, default=0)
    last_collection_date = Column(Date, nullable=True)
    
    # Status
    status = Column(String(20), default="outstanding")  # outstanding, paid, written_off, disputed
    is_written_off = Column(Boolean, default=False)
    write_off_date = Column(Date, nullable=True)
    write_off_reason = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    tenant = relationship("Tenant")
    patient = relationship("Patient")
    billing = relationship("Billing")

class PhysicianPayout(Base):
    """Physician payout model for doctor payments"""
    __tablename__ = "physician_payouts"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Payout details
    payout_number = Column(String(50), unique=True, nullable=False, index=True)
    payout_date = Column(Date, nullable=False)
    payout_period_start = Column(Date, nullable=False)
    payout_period_end = Column(Date, nullable=False)
    
    # Financial details
    gross_revenue = Column(Numeric(10, 2), nullable=False)
    facility_fee = Column(Numeric(10, 2), nullable=False)
    net_payout = Column(Numeric(10, 2), nullable=False)
    
    # Breakdown
    consultation_count = Column(Integer, default=0)
    procedure_count = Column(Integer, default=0)
    average_consultation_value = Column(Numeric(10, 2), nullable=True)
    
    # Payment information
    payment_method = Column(Enum(PaymentMethod), nullable=False)
    payment_date = Column(Date, nullable=True)
    payment_reference = Column(String(100), nullable=True)
    
    # Status
    status = Column(String(20), default="pending")  # pending, paid, cancelled
    is_paid = Column(Boolean, default=False)
    
    # Additional information
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    processed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    doctor = relationship("User", foreign_keys=[doctor_id])
    processor = relationship("User", foreign_keys=[processed_by])

class Revenue(Base):
    """Revenue model for tracking income"""
    __tablename__ = "revenues"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    
    # Revenue details
    revenue_date = Column(Date, nullable=False)
    revenue_type = Column(Enum(RevenueType), nullable=False)
    source = Column(String(100), nullable=False)  # consultation, procedure, exam, etc.
    
    # Financial details
    amount = Column(Numeric(10, 2), nullable=False)
    tax_amount = Column(Numeric(10, 2), default=0)
    net_amount = Column(Numeric(10, 2), nullable=False)
    
    # Reference information
    billing_id = Column(Integer, ForeignKey("billings.id"), nullable=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=True)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Additional information
    description = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    billing = relationship("Billing")
    patient = relationship("Patient")
    doctor = relationship("User", foreign_keys=[doctor_id])
    creator = relationship("User", foreign_keys=[created_by])

class Expense(Base):
    """Expense model for tracking costs"""
    __tablename__ = "expenses"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    
    # Expense details
    expense_date = Column(Date, nullable=False)
    expense_type = Column(Enum(ExpenseType), nullable=False)
    category = Column(String(100), nullable=False)
    
    # Financial details
    amount = Column(Numeric(10, 2), nullable=False)
    tax_amount = Column(Numeric(10, 2), default=0)
    net_amount = Column(Numeric(10, 2), nullable=False)
    
    # Payment information
    payment_method = Column(Enum(PaymentMethod), nullable=True)
    payment_date = Column(Date, nullable=True)
    vendor = Column(String(255), nullable=True)
    
    # Additional information
    description = Column(Text, nullable=True)
    receipt_number = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])

class FinancialAlert(Base):
    """Financial alert model for automated notifications"""
    __tablename__ = "financial_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    
    # Alert details
    alert_type = Column(String(50), nullable=False)  # overdue_payment, low_revenue, high_expense, etc.
    alert_level = Column(String(20), nullable=False)  # info, warning, critical
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    
    # Alert conditions
    threshold_value = Column(Numeric(10, 2), nullable=True)
    current_value = Column(Numeric(10, 2), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime(timezone=True), nullable=True)
    read_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Related entities
    related_entity_type = Column(String(50), nullable=True)  # billing, patient, doctor, etc.
    related_entity_id = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    reader = relationship("User", foreign_keys=[read_by])
