"""
Performance optimization configurations for Prontivus
"""

import os
from typing import Dict, Any

class PerformanceConfig:
    """Performance optimization settings"""
    
    # Database optimization settings
    DATABASE_OPTIMIZATIONS = {
        "pool_size": int(os.getenv("DB_POOL_SIZE", "20")),
        "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "30")),
        "pool_timeout": int(os.getenv("DB_POOL_TIMEOUT", "30")),
        "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "3600")),
        "pool_pre_ping": True,
        "echo": False,  # Disable SQL logging for performance
    }
    
    # Redis optimization settings
    REDIS_OPTIMIZATIONS = {
        "max_connections": int(os.getenv("REDIS_MAX_CONNECTIONS", "50")),
        "socket_timeout": int(os.getenv("REDIS_SOCKET_TIMEOUT", "5")),
        "socket_connect_timeout": int(os.getenv("REDIS_CONNECT_TIMEOUT", "5")),
        "retry_on_timeout": True,
        "health_check_interval": 30,
    }
    
    # FastAPI optimization settings
    FASTAPI_OPTIMIZATIONS = {
        "docs_url": "/docs" if os.getenv("ENVIRONMENT") != "production" else None,
        "redoc_url": "/redoc" if os.getenv("ENVIRONMENT") != "production" else None,
        "openapi_url": "/openapi.json" if os.getenv("ENVIRONMENT") != "production" else None,
        "generate_unique_id_function": lambda route: f"{route.tags[0]}-{route.name}" if route.tags else route.name,
    }
    
    # Caching settings
    CACHE_SETTINGS = {
        "default_timeout": int(os.getenv("CACHE_DEFAULT_TIMEOUT", "300")),  # 5 minutes
        "max_size": int(os.getenv("CACHE_MAX_SIZE", "1000")),
        "enable_query_cache": os.getenv("ENABLE_QUERY_CACHE", "true").lower() == "true",
        "enable_response_cache": os.getenv("ENABLE_RESPONSE_CACHE", "true").lower() == "true",
    }
    
    # Logging optimization
    LOGGING_OPTIMIZATIONS = {
        "level": "WARNING" if os.getenv("ENVIRONMENT") == "production" else "INFO",
        "disable_sql_logging": True,
        "disable_access_logging": os.getenv("ENVIRONMENT") == "production",
    }
    
    # Background task optimization
    BACKGROUND_TASKS = {
        "max_workers": int(os.getenv("MAX_WORKERS", "4")),
        "task_time_limit": int(os.getenv("TASK_TIME_LIMIT", "300")),
        "task_soft_time_limit": int(os.getenv("TASK_SOFT_TIME_LIMIT", "240")),
    }
    
    @classmethod
    def get_database_config(cls) -> Dict[str, Any]:
        """Get optimized database configuration"""
        return cls.DATABASE_OPTIMIZATIONS.copy()
    
    @classmethod
    def get_redis_config(cls) -> Dict[str, Any]:
        """Get optimized Redis configuration"""
        return cls.REDIS_OPTIMIZATIONS.copy()
    
    @classmethod
    def get_fastapi_config(cls) -> Dict[str, Any]:
        """Get optimized FastAPI configuration"""
        return cls.FASTAPI_OPTIMIZATIONS.copy()
    
    @classmethod
    def get_cache_config(cls) -> Dict[str, Any]:
        """Get optimized caching configuration"""
        return cls.CACHE_SETTINGS.copy()
    
    @classmethod
    def get_logging_config(cls) -> Dict[str, Any]:
        """Get optimized logging configuration"""
        return cls.LOGGING_OPTIMIZATIONS.copy()
    
    @classmethod
    def get_background_tasks_config(cls) -> Dict[str, Any]:
        """Get optimized background tasks configuration"""
        return cls.BACKGROUND_TASKS.copy()
