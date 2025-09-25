from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from .base import Base

class AuditAction(str, enum.Enum):
    """Audit action types"""
    # Authentication actions
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    PASSWORD_CHANGE = "password_change"
    PASSWORD_RESET = "password_reset"
    TWO_FACTOR_ENABLED = "two_factor_enabled"
    TWO_FACTOR_DISABLED = "two_factor_disabled"
    
    # User management
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    USER_ACTIVATED = "user_activated"
    USER_DEACTIVATED = "user_deactivated"
    
    # Patient management
    PATIENT_CREATED = "patient_created"
    PATIENT_UPDATED = "patient_updated"
    PATIENT_DELETED = "patient_deleted"
    PATIENT_MERGED = "patient_merged"
    
    # Medical records
    RECORD_CREATED = "record_created"
    RECORD_UPDATED = "record_updated"
    RECORD_DELETED = "record_deleted"
    RECORD_VIEWED = "record_viewed"
    RECORD_SIGNED = "record_signed"
    RECORD_PRINTED = "record_printed"
    RECORD_EXPORTED = "record_exported"
    
    # Appointments
    APPOINTMENT_CREATED = "appointment_created"
    APPOINTMENT_UPDATED = "appointment_updated"
    APPOINTMENT_CANCELLED = "appointment_cancelled"
    APPOINTMENT_RESCHEDULED = "appointment_rescheduled"
    APPOINTMENT_COMPLETED = "appointment_completed"
    
    # Prescriptions
    PRESCRIPTION_CREATED = "prescription_created"
    PRESCRIPTION_UPDATED = "prescription_updated"
    PRESCRIPTION_DISPENSED = "prescription_dispensed"
    PRESCRIPTION_CANCELLED = "prescription_cancelled"
    
    # System actions
    SYSTEM_BACKUP = "system_backup"
    SYSTEM_RESTORE = "system_restore"
    CONFIGURATION_CHANGE = "configuration_change"
    DATA_EXPORT = "data_export"
    DATA_IMPORT = "data_import"
    
    # Security actions
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_REVOKED = "permission_revoked"
    ROLE_ASSIGNED = "role_assigned"
    ROLE_REMOVED = "role_removed"
    ACCESS_DENIED = "access_denied"
    
    # LGPD actions
    CONSENT_GIVEN = "consent_given"
    CONSENT_WITHDRAWN = "consent_withdrawn"
    DATA_ANONYMIZATION = "data_anonymization"
    DATA_DELETION = "data_deletion"
    DATA_PORTABILITY = "data_portability"

class AuditLog(Base):
    """Comprehensive audit log for compliance and security"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True)
    
    # User information
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user_email = Column(String(255), nullable=True)  # Store email for deleted users
    user_role = Column(String(100), nullable=True)  # Store role for context
    
    # Action details
    action = Column(Enum(AuditAction), nullable=False)
    entity_type = Column(String(100), nullable=False)  # user, patient, appointment, etc.
    entity_id = Column(String(100), nullable=True)  # ID of the affected entity
    
    # Request context
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    session_id = Column(String(255), nullable=True)
    request_id = Column(String(255), nullable=True)  # For tracing requests
    
    # Action details
    details = Column(JSON, nullable=True)  # Additional context data
    old_values = Column(JSON, nullable=True)  # Previous values (for updates)
    new_values = Column(JSON, nullable=True)  # New values (for updates)
    
    # Result
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    
    # Risk assessment
    risk_level = Column(String(20), default="low")  # low, medium, high, critical
    risk_factors = Column(JSON, nullable=True)  # Factors that contributed to risk
    
    # Compliance
    lgpd_relevant = Column(Boolean, default=False)
    hipaa_relevant = Column(Boolean, default=False)
    requires_review = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    tenant = relationship("Tenant")
    # Temporarily commented out to avoid circular dependencies
    # user = relationship("User", back_populates="audit_logs")
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, action={self.action}, user_id={self.user_id}, entity={self.entity_type})>"

class AuditLogArchive(Base):
    """Archived audit logs for long-term storage"""
    __tablename__ = "audit_log_archives"
    
    id = Column(Integer, primary_key=True, index=True)
    original_log_id = Column(Integer, nullable=False)
    
    # Compressed log data
    log_data = Column(JSON, nullable=False)  # Compressed audit log data
    
    # Archive metadata
    archive_date = Column(DateTime(timezone=True), server_default=func.now())
    archive_reason = Column(String(100), nullable=False)  # retention_policy, space_management, etc.
    
    # Storage information
    storage_location = Column(String(500), nullable=True)
    compression_ratio = Column(Integer, nullable=True)
    
    def __repr__(self):
        return f"<AuditLogArchive(id={self.id}, original_id={self.original_log_id}, archived_at={self.archive_date})>"

class SecurityEvent(Base):
    """Security-specific events for monitoring"""
    __tablename__ = "security_events"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True)
    
    # Event details
    event_type = Column(String(100), nullable=False)  # brute_force, suspicious_login, etc.
    severity = Column(String(20), nullable=False)  # low, medium, high, critical
    
    # Source information
    source_ip = Column(String(45), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user_email = Column(String(255), nullable=True)
    
    # Event data
    description = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)
    
    # Response
    action_taken = Column(String(100), nullable=True)  # account_locked, ip_blocked, etc.
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Timestamps
    detected_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    tenant = relationship("Tenant")
    user = relationship("User", foreign_keys=[user_id])
    resolver = relationship("User", foreign_keys=[resolved_by])
    
    def __repr__(self):
        return f"<SecurityEvent(id={self.id}, type={self.event_type}, severity={self.severity})>"

class DataAccessLog(Base):
    """Log for tracking data access for LGPD compliance"""
    __tablename__ = "data_access_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True)
    
    # Access details
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=True)
    
    # Data accessed
    data_type = Column(String(100), nullable=False)  # medical_record, prescription, etc.
    data_id = Column(String(100), nullable=True)
    access_type = Column(String(50), nullable=False)  # view, edit, print, export, etc.
    
    # Context
    purpose = Column(Text, nullable=True)  # Why was the data accessed
    legal_basis = Column(String(100), nullable=True)  # consent, legitimate_interest, etc.
    
    # Access details
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    session_duration = Column(Integer, nullable=True)  # seconds
    
    # Timestamps
    accessed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    tenant = relationship("Tenant")
    user = relationship("User")
    # Note: Patient relationship will be defined in patient model to avoid circular imports
    
    def __repr__(self):
        return f"<DataAccessLog(id={self.id}, user_id={self.user_id}, data_type={self.data_type}, accessed_at={self.accessed_at})>"
