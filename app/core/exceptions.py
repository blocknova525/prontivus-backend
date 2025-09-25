"""
Custom exceptions for Prontivus
"""

from fastapi import HTTPException, status
from typing import Any, Dict, Optional

class ProntivusException(Exception):
    """Base exception for Prontivus"""
    
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

class AuthenticationError(ProntivusException):
    """Authentication related errors"""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED
        )

class AuthorizationError(ProntivusException):
    """Authorization related errors"""
    
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN
        )

class ValidationError(ProntivusException):
    """Validation related errors"""
    
    def __init__(self, message: str = "Validation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details
        )

class NotFoundError(ProntivusException):
    """Resource not found errors"""
    
    def __init__(self, message: str = "Resource not found"):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND
        )

class ConflictError(ProntivusException):
    """Resource conflict errors"""
    
    def __init__(self, message: str = "Resource conflict"):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT
        )

class LicenseError(ProntivusException):
    """License related errors"""
    
    def __init__(self, message: str = "License error"):
        super().__init__(
            message=message,
            status_code=status.HTTP_402_PAYMENT_REQUIRED
        )

class MedicalRecordError(ProntivusException):
    """Medical record related errors"""
    
    def __init__(self, message: str = "Medical record error"):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST
        )

async def prontivus_exception_handler(request, exc: ProntivusException):
    """Handle Prontivus exceptions"""
    return HTTPException(
        status_code=exc.status_code,
        detail={
            "message": exc.message,
            "details": exc.details
        }
    )
