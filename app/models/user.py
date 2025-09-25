"""
User and authentication models
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base
from ..utils.database_compat import (
    get_json_type, get_datetime_type, get_string_type, 
    get_boolean_type, get_integer_type, get_foreign_key
)

class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(get_integer_type(), primary_key=True, index=True)
    tenant_id = Column(get_integer_type(), get_foreign_key("tenants.id"), nullable=True)  # Multi-tenant support
    email = Column(get_string_type(255), unique=True, index=True, nullable=False)
    username = Column(get_string_type(100), unique=True, index=True, nullable=True)  # Optional for patients
    full_name = Column(get_string_type(255), nullable=False)
    cpf = Column(get_string_type(14), unique=True, index=True, nullable=True)  # For patients
    phone = Column(get_string_type(20), nullable=True)
    hashed_password = Column(get_string_type(255), nullable=False)
    is_active = Column(get_boolean_type(), default=True)
    is_verified = Column(get_boolean_type(), default=False)
    is_superuser = Column(get_boolean_type(), default=False)
    must_reset_password = Column(get_boolean_type(), default=False)  # Force password reset
    
    # Profile information
    crm = Column(get_string_type(20), nullable=True)  # For doctors
    specialty = Column(get_string_type(100), nullable=True)
    avatar_url = Column(get_string_type(500), nullable=True)
    
    # 2FA
    two_factor_enabled = Column(get_boolean_type(), default=False)
    two_factor_secret = Column(get_string_type(32), nullable=True)
    two_factor_method = Column(get_string_type(10), default="email")  # email, sms
    
    # Security
    failed_login_attempts = Column(get_integer_type(), default=0)
    locked_until = Column(get_datetime_type(), nullable=True)
    
    # LGPD Compliance
    consent_given = Column(get_boolean_type(), default=False)
    consent_date = Column(get_datetime_type(), nullable=True)
    
    # Timestamps
    created_at = Column(get_datetime_type(), server_default=func.now())
    updated_at = Column(get_datetime_type(), onupdate=func.now())
    last_login = Column(get_datetime_type(), nullable=True)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="users", foreign_keys=[tenant_id])
    roles = relationship("UserRole", back_populates="user")
    # Temporarily commented out to avoid circular dependencies
    # audit_logs = relationship("AuditLog", back_populates="user")
    two_factor_tokens = relationship("TwoFactorToken", back_populates="user")

class Role(Base):
    """Role model"""
    __tablename__ = "roles"
    
    id = Column(get_integer_type(), primary_key=True, index=True)
    name = Column(get_string_type(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    permissions = Column(get_json_type(), nullable=True)  # List of permissions
    
    # Timestamps
    created_at = Column(get_datetime_type(), server_default=func.now())
    updated_at = Column(get_datetime_type(), onupdate=func.now())
    
    # Relationships
    users = relationship("UserRole", back_populates="role")

class UserRole(Base):
    """User-Role association"""
    __tablename__ = "user_roles"
    
    id = Column(get_integer_type(), primary_key=True, index=True)
    user_id = Column(get_integer_type(), get_foreign_key("users.id"), nullable=False)
    role_id = Column(get_integer_type(), get_foreign_key("roles.id"), nullable=False)
    tenant_id = Column(get_integer_type(), get_foreign_key("tenants.id"), nullable=True)  # Multi-tenant
    
    # Timestamps
    created_at = Column(get_datetime_type(), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="roles")
    role = relationship("Role", back_populates="users")
    tenant = relationship("Tenant", back_populates="user_roles")


class TwoFactorToken(Base):
    """2FA token model"""
    __tablename__ = "two_factor_tokens"
    
    id = Column(get_integer_type(), primary_key=True, index=True)
    user_id = Column(get_integer_type(), get_foreign_key("users.id"), nullable=False)
    token = Column(get_string_type(6), nullable=False)  # 6-digit code
    expires_at = Column(get_datetime_type(), nullable=False)
    used = Column(get_boolean_type(), default=False)
    method = Column(get_string_type(10), default="email")  # email, sms
    
    # Timestamps
    created_at = Column(get_datetime_type(), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="two_factor_tokens")

class PasswordResetToken(Base):
    """Password reset token model"""
    __tablename__ = "password_reset_tokens"
    
    id = Column(get_integer_type(), primary_key=True, index=True)
    user_id = Column(get_integer_type(), get_foreign_key("users.id"), nullable=False)
    token = Column(get_string_type(255), unique=True, nullable=False)
    expires_at = Column(get_datetime_type(), nullable=False)
    used = Column(get_boolean_type(), default=False)
    
    # Timestamps
    created_at = Column(get_datetime_type(), server_default=func.now())
    
    # Relationships
    user = relationship("User")

