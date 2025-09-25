"""
Prontivus Configuration Settings
"""

from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Optional, Union
import os
from pathlib import Path

class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "Prontivus"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Branding
    BRAND_NAME: str = "Prontivus"
    BRAND_SLOGAN: str = "Cuidado inteligente"
    BRAND_LOGO_URL: str = "/Logo/Prontivus Horizontal.png"
    BRAND_COLOR_PRIMARY: str = "#2563eb"  # Blue
    BRAND_COLOR_SECONDARY: str = "#059669"  # Green
    BRAND_COLOR_ACCENT: str = "#dc2626"  # Red
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database Configuration
    DATABASE_URL: str = "postgresql://user:password@localhost/prontivus"
    DATABASE_URL_ASYNC: str = "postgresql+asyncpg://user:password@localhost/prontivus"
    SQLITE_URL: str = "sqlite:///./prontivus_offline.db"
    USE_SQLITE: bool = True
    
    # PostgreSQL Production Settings
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "prontivus"
    POSTGRES_USER: str = "prontivus_user"
    POSTGRES_PASSWORD: str = "prontivus_password"
    POSTGRES_SSL_MODE: str = "prefer"  # prefer, require, disable
    
    # Connection Pool Settings
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 30
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600
    DB_POOL_PRE_PING: bool = True
    
    # Sync Configuration
    SYNC_ENABLED: bool = True
    SYNC_INTERVAL_SECONDS: int = 300  # 5 minutes
    SYNC_BATCH_SIZE: int = 1000
    SYNC_CONFLICT_RESOLUTION: str = "postgresql_wins"  # postgresql_wins, sqlite_wins, manual
    SYNC_RETRY_ATTEMPTS: int = 3
    SYNC_RETRY_DELAY: int = 5
    
    # Offline Mode Settings
    OFFLINE_MODE_ENABLED: bool = True
    OFFLINE_DATA_RETENTION_DAYS: int = 30
    OFFLINE_SYNC_ON_STARTUP: bool = True
    OFFLINE_CONFLICT_NOTIFICATION: bool = True
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["*"]  # Temporarily allow all origins for testing
    ALLOWED_HOSTS: List[str] = ["*"]
    
    @field_validator('ALLOWED_ORIGINS', mode='before')
    @classmethod
    def parse_allowed_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v
    
    # Email
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_TLS: bool = True
    
    # File Storage
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # Medical System
    TISS_VERSION: str = "3.05.00"
    DEFAULT_TIMEZONE: str = "America/Sao_Paulo"
    
    # Licensing
    LICENSE_SIGNATURE_KEY: str = "license-signature-key"
    OFFLINE_GRACE_PERIOD_HOURS: int = 72
    
    # Monitoring
    SENTRY_DSN: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Allow extra fields from .env file

# Create settings instance
settings = Settings()

# Ensure upload directory exists
Path(settings.UPLOAD_DIR).mkdir(exist_ok=True)
