"""
Base model class for all database models with cross-platform compatibility
"""

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, DateTime, String
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from sqlalchemy import TypeDecorator
import json
import os

Base = declarative_base()

class CrossPlatformJSON(TypeDecorator):
    """JSON type that works on both SQLite and PostgreSQL"""
    impl = String
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(JSONB())
        else:
            return dialect.type_descriptor(SQLiteJSON())

    def process_bind_param(self, value, dialect):
        if value is not None:
            if dialect.name == 'postgresql':
                return value
            else:
                return json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            if dialect.name == 'postgresql':
                return value
            else:
                return json.loads(value)
        return value

class BaseModel(Base):
    """Base model with common fields and cross-platform compatibility"""
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Cross-platform timestamp handling
    if os.getenv("USE_SQLITE", "false").lower() == "true":
        # SQLite doesn't support timezone-aware timestamps
        created_at = Column(DateTime, server_default=func.now())
        updated_at = Column(DateTime, onupdate=func.now())
    else:
        # PostgreSQL supports timezone-aware timestamps
        created_at = Column(DateTime(timezone=True), server_default=func.now())
        updated_at = Column(DateTime(timezone=True), onupdate=func.now())