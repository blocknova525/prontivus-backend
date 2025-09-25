"""
Authentication schemas
"""

from pydantic import BaseModel, EmailStr, validator, Field
from typing import Optional, Literal
from datetime import datetime
import re

class UserLogin(BaseModel):
    """User login schema"""
    email_or_cpf: str = Field(..., description="Email or CPF")
    password: str
    remember_me: bool = False

class StaffRegister(BaseModel):
    """Staff registration schema (admin creates)"""
    email: EmailStr
    username: str
    full_name: str
    password: str
    role: Literal["doctor", "secretary", "finance", "admin"]
    crm: Optional[str] = None
    specialty: Optional[str] = None
    phone: Optional[str] = None
    tenant_id: Optional[int] = None  # Make optional, will be set to default tenant
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v
    
    @validator('crm')
    def validate_crm(cls, v, values):
        if values.get('role') == 'doctor' and not v:
            raise ValueError('CRM is required for doctors')
        return v

class PatientRegister(BaseModel):
    """Patient self-registration schema"""
    full_name: str
    cpf: str
    birth_date: str  # Will be converted to date
    email: EmailStr
    phone: str
    password: str
    insurance_company: Optional[str] = None
    insurance_number: Optional[str] = None
    insurance_plan: Optional[str] = None
    consent_given: bool = True
    
    @validator('cpf')
    def validate_cpf(cls, v):
        # Remove non-digits
        cpf = re.sub(r'\D', '', v)
        if len(cpf) != 11:
            raise ValueError('CPF must have 11 digits')
        
        # Validate CPF algorithm
        if cpf == cpf[0] * 11:  # All same digits
            raise ValueError('Invalid CPF')
        
        # Calculate first digit
        sum1 = sum(int(cpf[i]) * (10 - i) for i in range(9))
        digit1 = 11 - (sum1 % 11)
        if digit1 >= 10:
            digit1 = 0
        
        # Calculate second digit
        sum2 = sum(int(cpf[i]) * (11 - i) for i in range(10))
        digit2 = 11 - (sum2 % 11)
        if digit2 >= 10:
            digit2 = 0
        
        if int(cpf[9]) != digit1 or int(cpf[10]) != digit2:
            raise ValueError('Invalid CPF')
        
        return cpf
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v

class Token(BaseModel):
    """Token response schema"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: int
    user_role: Optional[str] = None
    user_type: Optional[str] = None  # "staff" or "patient"
    requires_2fa: bool = False
    must_reset_password: bool = False

class TokenData(BaseModel):
    """Token data schema"""
    username: Optional[str] = None
    user_id: Optional[int] = None
    tenant_id: Optional[int] = None

class TwoFactorSetup(BaseModel):
    """2FA setup response schema"""
    secret: str
    qr_code_url: str
    backup_codes: list[str]

class TwoFactorVerify(BaseModel):
    """2FA verification schema"""
    code: str
    token: str

class ForgotPassword(BaseModel):
    """Forgot password schema"""
    email: EmailStr

class ResetPassword(BaseModel):
    """Reset password schema"""
    token: str
    new_password: str
    
    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v

class VerifyEmail(BaseModel):
    """Email verification schema"""
    token: str

class ChangePassword(BaseModel):
    """Change password schema"""
    current_password: str
    new_password: str
    
    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v
