"""
License and billing models
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

class License(Base):
    """License model"""
    __tablename__ = "licenses"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    
    # License information
    license_key = Column(String(255), unique=True, nullable=False)
    plan = Column(String(50), nullable=False)  # basic, professional, enterprise
    modules = Column(JSON, nullable=False)  # List of enabled modules
    
    # Limits
    users_limit = Column(Integer, nullable=False)
    units_limit = Column(Integer, nullable=False)
    
    # Validity
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    
    # Status
    status = Column(String(20), default="active")  # active, expired, suspended, cancelled
    
    # Digital signature
    signature = Column(Text, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    tenant = relationship("Tenant")
    activations = relationship("LicenseActivation", back_populates="license")
    entitlements = relationship("LicenseEntitlement", back_populates="license")

class LicenseActivation(Base):
    """License activation model"""
    __tablename__ = "license_activations"
    
    id = Column(Integer, primary_key=True, index=True)
    license_id = Column(Integer, ForeignKey("licenses.id"), nullable=False)
    
    # Activation information
    instance_id = Column(String(255), unique=True, nullable=False)
    device_info = Column(JSON, nullable=True)
    
    # Status
    status = Column(String(20), default="active")  # active, inactive, suspended
    
    # Timestamps
    activated_at = Column(DateTime(timezone=True), server_default=func.now())
    last_check_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    license = relationship("License", back_populates="activations")

class LicenseEntitlement(Base):
    """License entitlement model"""
    __tablename__ = "license_entitlements"
    
    id = Column(Integer, primary_key=True, index=True)
    license_id = Column(Integer, ForeignKey("licenses.id"), nullable=False)
    
    # Entitlement information
    module = Column(String(100), nullable=False)
    enabled = Column(Boolean, default=True)
    limits = Column(JSON, nullable=True)  # Module-specific limits
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    license = relationship("License", back_populates="entitlements")

class Payment(Base):
    """Payment model"""
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    
    # Payment information
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="BRL")
    payment_method = Column(String(50), nullable=False)  # credit_card, pix, boleto, etc.
    
    # External references
    external_payment_id = Column(String(255), nullable=True)
    invoice_id = Column(String(100), nullable=True)
    
    # Status
    status = Column(String(20), default="pending")  # pending, paid, failed, refunded
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    paid_at = Column(DateTime(timezone=True), nullable=True)
    due_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    tenant = relationship("Tenant")

class Invoice(Base):
    """Invoice model"""
    __tablename__ = "invoices"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    
    # Invoice information
    invoice_number = Column(String(100), unique=True, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="BRL")
    
    # Status
    status = Column(String(20), default="pending")  # pending, paid, overdue, cancelled
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    due_at = Column(DateTime(timezone=True), nullable=False)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    
    # File
    pdf_url = Column(String(500), nullable=True)
    
    # Relationships
    tenant = relationship("Tenant")

class BillingWebhook(Base):
    """Billing webhook model for payment confirmations"""
    __tablename__ = "billing_webhooks"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Webhook information
    webhook_id = Column(String(255), unique=True, nullable=False)
    event_type = Column(String(100), nullable=False)
    payload = Column(JSON, nullable=False)
    
    # Processing status
    processed = Column(Boolean, default=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
