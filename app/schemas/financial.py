"""
Financial Module Pydantic Schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
from enum import Enum

class BillingType(str, Enum):
    """Billing type enum"""
    TISS = "tiss"
    PRIVATE = "private"
    CASH = "cash"
    INSURANCE = "insurance"
    CORPORATE = "corporate"

class PaymentStatus(str, Enum):
    """Payment status enum"""
    PENDING = "pending"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    DISPUTED = "disputed"

class PaymentMethod(str, Enum):
    """Payment method enum"""
    CASH = "cash"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    BANK_TRANSFER = "bank_transfer"
    CHECK = "check"
    INSURANCE = "insurance"
    PIX = "pix"
    BOLETO = "boleto"

class RevenueType(str, Enum):
    """Revenue type enum"""
    CONSULTATION = "consultation"
    PROCEDURE = "procedure"
    EXAM = "exam"
    MEDICATION = "medication"
    OTHER = "other"

class ExpenseType(str, Enum):
    """Expense type enum"""
    SALARY = "salary"
    RENT = "rent"
    UTILITIES = "utilities"
    EQUIPMENT = "equipment"
    MEDICATION = "medication"
    SUPPLIES = "supplies"
    MARKETING = "marketing"
    OTHER = "other"

# Billing Schemas
class BillingItemBase(BaseModel):
    item_type: str
    item_code: Optional[str] = None
    item_name: str
    description: Optional[str] = None
    quantity: Decimal = Field(default=1, ge=0)
    unit_price: Decimal = Field(ge=0)
    total_price: Decimal = Field(ge=0)
    cpt_code: Optional[str] = None
    icd10_code: Optional[str] = None
    modifier_code: Optional[str] = None

class BillingItemCreate(BillingItemBase):
    pass

class BillingItemResponse(BillingItemBase):
    id: int
    billing_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class BillingBase(BaseModel):
    patient_id: int
    appointment_id: Optional[int] = None
    doctor_id: int
    billing_type: BillingType
    billing_date: date
    due_date: date
    tax_amount: Decimal = Field(default=0, ge=0)
    discount_amount: Decimal = Field(default=0, ge=0)
    paid_amount: Decimal = Field(default=0, ge=0)
    insurance_company: Optional[str] = None
    insurance_number: Optional[str] = None
    authorization_number: Optional[str] = None
    copay_amount: Optional[Decimal] = Field(None, ge=0)
    tiss_version: Optional[str] = None
    tiss_guia: Optional[str] = None
    notes: Optional[str] = None

class BillingCreate(BillingBase):
    items: List[BillingItemCreate]

class BillingUpdate(BaseModel):
    billing_type: Optional[BillingType] = None
    due_date: Optional[date] = None
    tax_amount: Optional[Decimal] = Field(None, ge=0)
    discount_amount: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = None

class BillingResponse(BillingBase):
    id: int
    tenant_id: int
    billing_number: str
    subtotal: Decimal
    total_amount: Decimal
    balance_amount: Decimal
    payment_status: PaymentStatus
    payment_method: Optional[PaymentMethod]
    payment_date: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: Optional[int]
    
    # Patient information
    patient_name: Optional[str] = None
    patient_cpf: Optional[str] = None
    
    # Doctor information
    doctor_name: Optional[str] = None
    
    # Billing items
    billing_items: List[BillingItemResponse] = []
    
    class Config:
        from_attributes = True

# Payment Schemas
class BillingPaymentBase(BaseModel):
    payment_date: datetime
    payment_method: PaymentMethod
    amount: Decimal = Field(ge=0)
    transaction_id: Optional[str] = None
    authorization_code: Optional[str] = None
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    check_number: Optional[str] = None
    notes: Optional[str] = None

class BillingPaymentCreate(BillingPaymentBase):
    pass

class BillingPaymentResponse(BillingPaymentBase):
    id: int
    billing_id: int
    tenant_id: int
    payment_number: str
    status: str
    is_refunded: bool
    refund_amount: Optional[Decimal]
    refund_date: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    processed_by: Optional[int]
    
    # Processor information
    processor_name: Optional[str] = None
    
    class Config:
        from_attributes = True

# Accounts Receivable Schemas
class AccountsReceivableResponse(BaseModel):
    id: int
    tenant_id: int
    patient_id: int
    billing_id: int
    invoice_number: str
    invoice_date: date
    due_date: date
    original_amount: Decimal
    outstanding_amount: Decimal
    days_overdue: int
    aging_bucket: str
    last_payment_date: Optional[date]
    last_payment_amount: Optional[Decimal]
    collection_attempts: int
    last_collection_date: Optional[date]
    status: str
    is_written_off: bool
    write_off_date: Optional[date]
    write_off_reason: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    
    # Patient information
    patient_name: Optional[str] = None
    patient_cpf: Optional[str] = None
    
    class Config:
        from_attributes = True

# Physician Payout Schemas
class PhysicianPayoutBase(BaseModel):
    doctor_id: int
    payout_date: date
    payout_period_start: date
    payout_period_end: date
    gross_revenue: Decimal = Field(ge=0)
    facility_fee: Decimal = Field(ge=0)
    consultation_count: int = Field(default=0, ge=0)
    procedure_count: int = Field(default=0, ge=0)
    average_consultation_value: Optional[Decimal] = Field(None, ge=0)
    payment_method: PaymentMethod
    notes: Optional[str] = None

class PhysicianPayoutCreate(PhysicianPayoutBase):
    pass

class PhysicianPayoutResponse(PhysicianPayoutBase):
    id: int
    tenant_id: int
    payout_number: str
    net_payout: Decimal
    payment_date: Optional[date]
    payment_reference: Optional[str]
    status: str
    is_paid: bool
    created_at: datetime
    updated_at: Optional[datetime]
    processed_by: Optional[int]
    
    # Doctor information
    doctor_name: Optional[str] = None
    
    # Processor information
    processor_name: Optional[str] = None
    
    class Config:
        from_attributes = True

# Revenue Schemas
class RevenueBase(BaseModel):
    revenue_date: date
    revenue_type: RevenueType
    source: str
    amount: Decimal = Field(ge=0)
    tax_amount: Decimal = Field(default=0, ge=0)
    net_amount: Decimal = Field(ge=0)
    billing_id: Optional[int] = None
    patient_id: Optional[int] = None
    doctor_id: Optional[int] = None
    description: Optional[str] = None
    notes: Optional[str] = None

class RevenueCreate(RevenueBase):
    pass

class RevenueResponse(RevenueBase):
    id: int
    tenant_id: int
    created_at: datetime
    created_by: Optional[int]
    
    # Patient information
    patient_name: Optional[str] = None
    
    # Doctor information
    doctor_name: Optional[str] = None
    
    class Config:
        from_attributes = True

# Expense Schemas
class ExpenseBase(BaseModel):
    expense_date: date
    expense_type: ExpenseType
    category: str
    amount: Decimal = Field(ge=0)
    tax_amount: Decimal = Field(default=0, ge=0)
    net_amount: Decimal = Field(ge=0)
    payment_method: Optional[PaymentMethod] = None
    payment_date: Optional[date] = None
    vendor: Optional[str] = None
    description: Optional[str] = None
    receipt_number: Optional[str] = None
    notes: Optional[str] = None

class ExpenseCreate(ExpenseBase):
    pass

class ExpenseResponse(ExpenseBase):
    id: int
    tenant_id: int
    created_at: datetime
    created_by: Optional[int]
    
    # Creator information
    creator_name: Optional[str] = None
    
    class Config:
        from_attributes = True

# Financial Alert Schemas
class FinancialAlertResponse(BaseModel):
    id: int
    tenant_id: int
    alert_type: str
    alert_level: str
    title: str
    message: str
    threshold_value: Optional[Decimal]
    current_value: Optional[Decimal]
    is_active: bool
    is_read: bool
    read_at: Optional[datetime]
    read_by: Optional[int]
    related_entity_type: Optional[str]
    related_entity_id: Optional[int]
    created_at: datetime
    expires_at: Optional[datetime]
    
    # Reader information
    reader_name: Optional[str] = None
    
    class Config:
        from_attributes = True

# Dashboard Schemas
class BillingDashboardResponse(BaseModel):
    total_revenue: float
    total_payments: float
    outstanding_receivables: float
    overdue_receivables: float
    total_expenses: float
    net_profit: float
    date_from: date
    date_to: date

class RevenueExpenseChartResponse(BaseModel):
    period: str
    revenue_data: List[dict]
    expense_data: List[dict]

# Summary Schemas
class AgingSummary(BaseModel):
    bucket: str
    count: int
    total_amount: float

class AccountsReceivableSummary(BaseModel):
    aging_summary: List[AgingSummary]
    total_outstanding: float

# Export Schemas
class ExportRequest(BaseModel):
    format: str = Field(pattern="^(pdf|excel|csv)$")
    date_from: date
    date_to: date
    filters: Optional[dict] = None

class ExportResponse(BaseModel):
    file_url: str
    file_name: str
    expires_at: datetime
