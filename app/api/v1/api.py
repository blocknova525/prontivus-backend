"""
API v1 router configuration
"""

from fastapi import APIRouter
from app.api.v1.endpoints import auth_db_only, patient_auth, appointments, medical_records, prescriptions, notifications, database, documents, patient_calls, financial, patients, secretary_simple, doctors, licenses, units
# Temporarily commented out endpoints with AuthService import issues
# from app.api.v1.endpoints import licenses, secretary

api_router = APIRouter()

# Include working endpoint routers
api_router.include_router(auth_db_only.router, prefix="/auth", tags=["staff-authentication"])
api_router.include_router(patient_auth.router, prefix="/patient-auth", tags=["patient-authentication"])
api_router.include_router(appointments.router, prefix="/appointments", tags=["appointments"])
api_router.include_router(medical_records.router, prefix="/medical-records", tags=["medical-records"])
api_router.include_router(prescriptions.router, prefix="/prescriptions", tags=["prescriptions"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(database.router, prefix="/database", tags=["database"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(patient_calls.router, prefix="/patient-calls", tags=["patient-calls"])
api_router.include_router(financial.router, prefix="/financial", tags=["financial"])
api_router.include_router(patients.router, prefix="/patients", tags=["patients"])
api_router.include_router(secretary_simple.router, prefix="/secretary", tags=["secretary"])
api_router.include_router(doctors.router, prefix="/doctors", tags=["doctors"])

# Temporarily commented out endpoints with AuthService import issues
api_router.include_router(units.router, prefix="/units", tags=["units"])
