"""
Prontivus Main Application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import os
import logging

from app.core.config import settings
from app.database.database import test_connection
from app.services.startup_service import startup_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description=f"Sistema Médico Completo de Gestão de Clínicas e Consultórios - {settings.BRAND_SLOGAN}",
    version=settings.VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None
)

# CORS middleware
logger.info(f"🌐 CORS Configuration: {settings.ALLOWED_ORIGINS}")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Temporarily allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

# Determine which endpoints to use based on environment
USE_DATABASE = os.getenv("USE_DATABASE", "true").lower() == "true"  # Force database mode for Prontivus
USE_SQLITE = os.getenv("USE_SQLITE", "true").lower() == "true"  # Default to SQLite for development

if USE_DATABASE:
    # Use real database endpoints
    logger.info("🔗 Using real database endpoints")
    
    # Set environment for SQLite if needed
    if USE_SQLITE:
        os.environ["USE_SQLITE"] = "true"
        os.environ["ENVIRONMENT"] = "development"
    
    # Test database connection
    if not test_connection():
        logger.warning("⚠️ Database connection test failed, but continuing with database mode")
        # Don't fall back to mock mode - force database mode for Prontivus
    else:
        logger.info("✅ Database connection successful")
        
        # Import real endpoints
        from app.api.v1 import api as api_v1
        app.include_router(api_v1.api_router, prefix="/api/v1")

if not USE_DATABASE:
    # Use mock endpoints for development
    logger.info("🎭 Using mock endpoints for development")
    
    # Import mock endpoints
    from app.api.v1.endpoints import auth, users, patients, appointments, medical_records, secretary, financial, notifications, prescriptions
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication (Mock)"])
    app.include_router(users.router, prefix="/api/v1/users", tags=["Users (Mock)"])
    app.include_router(patients.router, prefix="/api/v1/patients", tags=["Patients (Mock)"])
    app.include_router(appointments.router, prefix="/api/v1/appointments", tags=["Appointments (Mock)"])
    app.include_router(medical_records.router, prefix="/api/v1/medical-records", tags=["Medical Records (Mock)"])
    app.include_router(prescriptions.router, prefix="/api/v1/prescriptions", tags=["Prescriptions (Mock)"])
    app.include_router(secretary.router, prefix="/api/v1/secretary", tags=["Secretary (Mock)"])
    app.include_router(financial.router, prefix="/api/v1/financial", tags=["Financial (Mock)"])
    app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["Notifications (Mock)"])

# Health check endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": f"{settings.APP_NAME} API",
        "version": settings.VERSION,
        "status": "active",
        "environment": settings.ENVIRONMENT,
        "database": "connected" if USE_DATABASE else "mock",
        "docs_url": "/docs" if settings.DEBUG else None
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    health_status = {
        "status": "healthy",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "database": "connected" if USE_DATABASE else "mock"
    }
    
    if USE_DATABASE:
        # Test database connection
        if test_connection():
            health_status["database_status"] = "connected"
        else:
            health_status["database_status"] = "disconnected"
            health_status["status"] = "unhealthy"
    
    return health_status

@app.get("/startup")
async def startup_status():
    """Get startup service status"""
    if USE_DATABASE:
        return startup_service.get_service_status()
    else:
        return {
            "message": "Mock mode - no database services",
            "database_mode": "mock"
        }

# Startup event
@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info(f"🚀 Starting {settings.APP_NAME} v{settings.VERSION}")
    logger.info(f"📊 Environment: {settings.ENVIRONMENT}")
    logger.info(f"🔧 Debug mode: {settings.DEBUG}")
    logger.info(f"🗄️ Database mode: {'Real' if USE_DATABASE else 'Mock'}")
    
    if USE_DATABASE:
        logger.info("✅ Database integration enabled")
        # Initialize all database services
        await startup_service.initialize_all_services()
    else:
        logger.info("🎭 Mock endpoints enabled for development")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    logger.info(f"🛑 Shutting down {settings.APP_NAME}")
    
    if USE_DATABASE:
        # Shutdown all database services
        await startup_service.shutdown_services()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
