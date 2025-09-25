"""
Secretary Module Enums
"""

from enum import Enum

class CheckInStatus(str, Enum):
    """Patient check-in status"""
    ARRIVED = "arrived"
    WAITING = "waiting"
    CALLED = "called"
    IN_CONSULTATION = "in_consultation"
    COMPLETED = "completed"
    NO_SHOW = "no_show"
    CANCELLED = "cancelled"

class InsuranceVerificationStatus(str, Enum):
    """Insurance verification status"""
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    EXPIRED = "expired"
    REQUIRES_UPDATE = "requires_update"

class DocumentType(str, Enum):
    """Document type enum"""
    IDENTITY = "identity"
    INSURANCE_CARD = "insurance_card"
    MEDICAL_REPORT = "medical_report"
    LAB_RESULT = "lab_result"
    IMAGING_RESULT = "imaging_result"
    PRESCRIPTION = "prescription"
    REFERRAL = "referral"
    CERTIFICATE = "certificate"
    OTHER = "other"

class ArrivalMethod(str, Enum):
    """Patient arrival method"""
    WALK_IN = "walk_in"
    APPOINTMENT = "appointment"
    EMERGENCY = "emergency"
    REFERRAL = "referral"

class PriorityLevel(int, Enum):
    """Priority level for patients"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    EMERGENCY = 5
