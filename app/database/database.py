"""
Database connection and session management
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import os
from typing import Generator

from app.core.config import settings

# Create base class for models
Base = declarative_base()

# Global variables for engine and session
engine = None
SessionLocal = None

def get_engine():
    """Get database engine, creating it if necessary"""
    global engine
    if engine is None:
        # Determine which database to use based on environment
        use_sqlite = os.getenv("USE_SQLITE", "false").lower() == "true"
        
        if use_sqlite:
            # Use SQLite for offline development with optimized settings
            DATABASE_URL = "sqlite:///./prontivus_offline.db"  # Force Prontivus database
            engine = create_engine(
                DATABASE_URL,
                connect_args={
                    "check_same_thread": False,
                    "timeout": 20,
                    "isolation_level": None  # Autocommit mode for better performance
                },
                poolclass=StaticPool,
                echo=False,  # Disable SQL logging for performance
                pool_pre_ping=True,
                pool_recycle=3600  # Recycle connections every hour
            )
            print("📱 Using SQLite database (Offline Mode)")
        else:
            # Use PostgreSQL for online production with optimized settings
            DATABASE_URL = settings.DATABASE_URL
            
            # Build connection arguments for production
            connect_args = {
                "sslmode": settings.POSTGRES_SSL_MODE,
                "connect_timeout": 10,
                "application_name": "clinicore_backend"
            }
            
            engine = create_engine(
                DATABASE_URL,
                echo=False,  # Disable SQL logging for performance
                pool_pre_ping=settings.DB_POOL_PRE_PING,
                pool_recycle=settings.DB_POOL_RECYCLE,
                pool_size=settings.DB_POOL_SIZE,
                max_overflow=settings.DB_MAX_OVERFLOW,
                pool_timeout=settings.DB_POOL_TIMEOUT,
                connect_args=connect_args,
                # Additional PostgreSQL optimizations
                isolation_level="AUTOCOMMIT",  # Better for read operations
                future=True,  # Use SQLAlchemy 2.0 style
                pool_reset_on_return="commit"  # Reset connections properly
            )
            print("🌐 Using PostgreSQL database (Online Mode)")
            print(f"   📊 Pool size: {settings.DB_POOL_SIZE}")
            print(f"   🔄 Max overflow: {settings.DB_MAX_OVERFLOW}")
            print(f"   🔒 SSL mode: {settings.POSTGRES_SSL_MODE}")
    return engine

def get_session_local():
    """Get session factory, creating it if necessary"""
    global SessionLocal
    if SessionLocal is None:
        SessionLocal = sessionmaker(
            autocommit=False, 
            autoflush=False, 
            bind=get_engine(),
            expire_on_commit=False  # Optimize session management
        )
    return SessionLocal

def get_db() -> Generator:
    """Dependency to get database session"""
    db = get_session_local()()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Create all tables in the database"""
    # Import all models to ensure they're registered with SQLAlchemy
    from app.models import user, patient, appointment, medical_record, prescription, tenant
    # Temporarily commented out audit to avoid circular dependencies
    # from app.models import audit
    
    Base.metadata.create_all(bind=get_engine())

def drop_tables():
    """Drop all tables (use with caution!)"""
    from app.models.base import Base
    Base.metadata.drop_all(bind=get_engine())

def init_db():
    """Initialize database - create tables and indexes"""
    try:
        create_tables()
        print("✅ Database initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

# Test database connection
def test_connection():
    """Test database connection"""
    try:
        from sqlalchemy import text
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
