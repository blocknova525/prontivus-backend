from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from .base import Base

class TenantType(str, enum.Enum):
    """Tenant type enum"""
    HOSPITAL = "hospital"
    CLINIC = "clinic"
    MEDICAL_CENTER = "medical_center"
    PRIVATE_PRACTICE = "private_practice"
    PHARMACY = "pharmacy"
    LABORATORY = "laboratory"

class TenantStatus(str, enum.Enum):
    """Tenant status enum"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_APPROVAL = "pending_approval"

class Tenant(Base):
    """Tenant model for multi-tenancy support"""
    __tablename__ = "tenants"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic information
    name = Column(String(255), nullable=False, index=True)
    legal_name = Column(String(255), nullable=True)
    type = Column(Enum(TenantType), nullable=False)
    status = Column(Enum(TenantStatus), nullable=False, default=TenantStatus.PENDING_APPROVAL)
    
    # Contact information
    email = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    website = Column(String(255), nullable=True)
    
    # Address
    address_line1 = Column(String(255), nullable=True)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(100), nullable=True, default="Brazil")
    
    # Business information
    cnpj = Column(String(18), unique=True, nullable=True, index=True)  # Brazilian tax ID
    cnes = Column(String(7), nullable=True)  # Brazilian health facility code
    license_number = Column(String(100), nullable=True)
    license_expiry = Column(DateTime(timezone=True), nullable=True)
    
    # Configuration
    timezone = Column(String(50), default="America/Sao_Paulo")
    language = Column(String(10), default="pt-BR")
    currency = Column(String(3), default="BRL")
    date_format = Column(String(20), default="DD/MM/YYYY")
    
    # Features and limits
    max_users = Column(Integer, default=10)
    max_patients = Column(Integer, default=1000)
    max_storage_gb = Column(Integer, default=10)
    features_enabled = Column(JSON, nullable=True)  # List of enabled features
    
    # Subscription information
    subscription_plan = Column(String(50), nullable=True)
    subscription_start = Column(DateTime(timezone=True), nullable=True)
    subscription_end = Column(DateTime(timezone=True), nullable=True)
    billing_email = Column(String(255), nullable=True)
    
    # Settings
    settings = Column(JSON, nullable=True)  # Tenant-specific settings
    branding = Column(JSON, nullable=True)  # Logo, colors, etc.
    
    # Security and compliance
    data_retention_days = Column(Integer, default=2555)  # 7 years default
    backup_frequency = Column(String(20), default="daily")
    encryption_enabled = Column(Boolean, default=True)
    audit_logging_enabled = Column(Boolean, default=True)
    
    # LGPD Compliance
    lgpd_compliant = Column(Boolean, default=False)
    lgpd_compliance_date = Column(DateTime(timezone=True), nullable=True)
    data_protection_officer = Column(String(255), nullable=True)
    privacy_policy_url = Column(String(500), nullable=True)
    terms_of_service_url = Column(String(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    
    # Related entities
    users = relationship("User", back_populates="tenant", foreign_keys="User.tenant_id")
    user_roles = relationship("UserRole", back_populates="tenant")
    # Temporarily commented out to avoid circular dependencies
    # patients = relationship("Patient", back_populates="tenant")
    # appointments = relationship("Appointment", back_populates="tenant")
    # medical_records = relationship("MedicalRecord", back_populates="tenant")
    # prescriptions = relationship("Prescription", back_populates="tenant")
    # Temporarily commented out to avoid circular dependencies
    # checkins = relationship("PatientCheckIn", back_populates="tenant")
    # documents = relationship("PatientDocument", back_populates="tenant")
    # exams = relationship("PatientExam", back_populates="tenant")
    # Temporarily commented out to avoid circular dependencies
    # billings = relationship("Billing", back_populates="tenant")
    # accounts_receivable = relationship("AccountsReceivable", back_populates="tenant")
    
    def __repr__(self):
        return f"<Tenant(id={self.id}, name={self.name}, type={self.type}, status={self.status})>"

class TenantInvitation(Base):
    """Tenant invitation model for inviting users to join a tenant"""
    __tablename__ = "tenant_invitations"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    invited_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Invitation details
    email = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)  # admin, doctor, secretary, etc.
    invitation_token = Column(String(255), unique=True, nullable=False)
    
    # Status
    status = Column(String(20), default="pending")  # pending, accepted, expired, cancelled
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    accepted_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # Message
    message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    tenant = relationship("Tenant")
    inviter = relationship("User", foreign_keys=[invited_by])
    accepter = relationship("User", foreign_keys=[accepted_by])
    
    def __repr__(self):
        return f"<TenantInvitation(id={self.id}, tenant_id={self.tenant_id}, email={self.email}, status={self.status})>"

class TenantSubscription(Base):
    """Tenant subscription model for tracking subscription history"""
    __tablename__ = "tenant_subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    
    # Subscription details
    plan_name = Column(String(100), nullable=False)
    plan_features = Column(JSON, nullable=True)
    price_per_month = Column(Integer, nullable=False)  # in cents
    
    # Period
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Payment information
    payment_method = Column(String(50), nullable=True)  # credit_card, bank_transfer, etc.
    payment_status = Column(String(20), default="pending")  # pending, paid, failed, refunded
    last_payment_date = Column(DateTime(timezone=True), nullable=True)
    next_payment_date = Column(DateTime(timezone=True), nullable=True)
    
    # Usage tracking
    current_users = Column(Integer, default=0)
    current_patients = Column(Integer, default=0)
    storage_used_gb = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    tenant = relationship("Tenant")
    
    def __repr__(self):
        return f"<TenantSubscription(id={self.id}, tenant_id={self.tenant_id}, plan={self.plan_name}, active={self.is_active})>"
