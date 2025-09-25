"""
Database compatibility utilities for SQLite and PostgreSQL
"""

import os
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Date, Numeric, Enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from sqlalchemy import TypeDecorator
import json

def get_json_type():
    """Get the appropriate JSON type for the current database"""
    if os.getenv("USE_SQLITE", "false").lower() == "true":
        return SQLiteJSON
    else:
        return JSONB

def get_datetime_type():
    """Get the appropriate DateTime type for the current database"""
    if os.getenv("USE_SQLITE", "false").lower() == "true":
        # SQLite doesn't support timezone-aware timestamps
        return DateTime
    else:
        # PostgreSQL supports timezone-aware timestamps
        return DateTime(timezone=True)

def get_string_type(length=None):
    """Get the appropriate String type for the current database"""
    if length:
        return String(length)
    else:
        return String

def get_text_type():
    """Get the appropriate Text type for the current database"""
    return Text

def get_boolean_type():
    """Get the appropriate Boolean type for the current database"""
    return Boolean

def get_integer_type():
    """Get the appropriate Integer type for the current database"""
    return Integer

def get_date_type():
    """Get the appropriate Date type for the current database"""
    return Date

def get_numeric_type(precision=10, scale=2):
    """Get the appropriate Numeric type for the current database"""
    return Numeric(precision, scale)

def get_foreign_key(reference):
    """Get the appropriate ForeignKey type for the current database"""
    return ForeignKey(reference)

def get_enum_type(*values):
    """Get the appropriate Enum type for the current database"""
    return Enum(*values)

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

def is_sqlite():
    """Check if we're using SQLite"""
    return os.getenv("USE_SQLITE", "false").lower() == "true"

def is_postgresql():
    """Check if we're using PostgreSQL"""
    return not is_sqlite()

def get_database_type():
    """Get the current database type"""
    return "sqlite" if is_sqlite() else "postgresql"
