"""
Prontivus - Sistema Médico Completo
FastAPI Backend Application
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer
import uvicorn
import logging
from contextlib import asynccontextmanager

from app.core.config import settings
from app.database.database import init_db
from app.api.v1.api import api_router
from app.core.exceptions import ProntivusException, prontivus_exception_handler

# Configure logging - optimized for performance
logging.basicConfig(
    level=logging.WARNING,  # Reduce logging level for better performance
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting Prontivus Backend...")
    init_db()
    logger.info("Database initialized successfully")
    yield
    # Shutdown
    logger.info("Shutting down Prontivus Backend...")

# Create FastAPI application with performance optimizations
app = FastAPI(
    title="Prontivus API",
    description="Sistema Médico Completo de Gestão de Clínicas e Consultórios",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    # lifespan=lifespan,  # Temporarily disabled for debugging
    # Performance optimizations
    generate_unique_id_function=lambda route: f"{route.tags[0]}-{route.name}" if route.tags else route.name,
    openapi_url="/openapi.json"
)

# Security middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
app.add_exception_handler(ProntivusException, prontivus_exception_handler)

# Initialize database manually (since lifespan is disabled)
init_db()

# Include API routes
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Prontivus API",
        "version": "1.0.0",
        "status": "active",
        "environment": settings.ENVIRONMENT
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": "2025-01-15T11:15:00Z",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development"
    )
