"""
Application startup service
Initializes database services, sync, monitoring, and offline capabilities
"""

import asyncio
import logging
from typing import Dict, Any
from datetime import datetime

from app.core.config import settings
from app.services.sync_service import sync_service
from app.services.offline_service import offline_manager
from app.services.database_monitor import db_monitor
from app.database.database import test_connection, init_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StartupService:
    """Handles application startup and service initialization"""
    
    def __init__(self):
        self.services_initialized = False
        self.startup_time = None
        self.startup_log = []
    
    async def initialize_all_services(self) -> Dict[str, Any]:
        """Initialize all database services"""
        if self.services_initialized:
            logger.info("🔄 Services already initialized")
            return self._get_startup_status()
        
        self.startup_time = datetime.utcnow()
        logger.info("🚀 Starting Prontivus database services...")
        
        try:
            # 1. Test database connection
            await self._log_step("Testing database connection...")
            connection_success = await self._test_database_connection()
            
            # 2. Initialize database schema
            await self._log_step("Initializing database schema...")
            schema_success = await self._initialize_database_schema()
            
            # 3. Start offline data manager
            await self._log_step("Starting offline data manager...")
            offline_success = await self._start_offline_manager()
            
            # 4. Start sync service
            await self._log_step("Starting sync service...")
            sync_success = await self._start_sync_service()
            
            # 5. Start database monitoring
            await self._log_step("Starting database monitoring...")
            monitoring_success = await self._start_database_monitoring()
            
            # 6. Run initial sync if needed
            await self._log_step("Running initial sync...")
            initial_sync_success = await self._run_initial_sync()
            
            # Check if all services started successfully
            all_success = all([
                connection_success,
                schema_success,
                offline_success,
                sync_success,
                monitoring_success,
                initial_sync_success
            ])
            
            if all_success:
                self.services_initialized = True
                await self._log_step("✅ All services initialized successfully!")
                logger.info("🎉 Prontivus database services ready!")
            else:
                await self._log_step("❌ Some services failed to initialize")
                logger.error("❌ Service initialization failed")
            
            return self._get_startup_status()
            
        except Exception as e:
            await self._log_step(f"❌ Startup failed: {str(e)}")
            logger.error(f"❌ Startup service failed: {e}")
            return self._get_startup_status()
    
    async def _test_database_connection(self) -> bool:
        """Test database connection"""
        try:
            success = test_connection()
            if success:
                await self._log_step("✅ Database connection successful")
            else:
                await self._log_step("❌ Database connection failed")
            return success
        except Exception as e:
            await self._log_step(f"❌ Database connection error: {str(e)}")
            return False
    
    async def _initialize_database_schema(self) -> bool:
        """Initialize database schema"""
        try:
            success = init_db()
            if success:
                await self._log_step("✅ Database schema initialized")
            else:
                await self._log_step("❌ Database schema initialization failed")
            return success
        except Exception as e:
            await self._log_step(f"❌ Schema initialization error: {str(e)}")
            return False
    
    async def _start_offline_manager(self) -> bool:
        """Start offline data manager"""
        try:
            # Start connection monitoring
            offline_manager.start_connection_monitoring()
            
            # Register connection callback
            offline_manager.register_connection_callback(self._on_connection_change)
            
            await self._log_step("✅ Offline data manager started")
            return True
        except Exception as e:
            await self._log_step(f"❌ Offline manager error: {str(e)}")
            return False
    
    async def _start_sync_service(self) -> bool:
        """Start sync service"""
        try:
            if settings.SYNC_ENABLED:
                # Start sync service in background
                asyncio.create_task(sync_service.start_sync_service())
                await self._log_step("✅ Sync service started")
            else:
                await self._log_step("⚠️ Sync service disabled in configuration")
            return True
        except Exception as e:
            await self._log_step(f"❌ Sync service error: {str(e)}")
            return False
    
    async def _start_database_monitoring(self) -> bool:
        """Start database monitoring"""
        try:
            # Start monitoring in background
            asyncio.create_task(db_monitor.start_monitoring())
            await self._log_step("✅ Database monitoring started")
            return True
        except Exception as e:
            await self._log_step(f"❌ Monitoring error: {str(e)}")
            return False
    
    async def _run_initial_sync(self) -> bool:
        """Run initial sync if needed"""
        try:
            if settings.SYNC_ENABLED and settings.OFFLINE_SYNC_ON_STARTUP:
                # Force an initial sync
                await sync_service.force_sync()
                await self._log_step("✅ Initial sync completed")
            else:
                await self._log_step("⚠️ Initial sync skipped")
            return True
        except Exception as e:
            await self._log_step(f"❌ Initial sync error: {str(e)}")
            return False
    
    def _on_connection_change(self, status):
        """Handle connection status changes"""
        logger.info(f"🔗 Connection status changed: {status.value}")
        
        # If connection restored, trigger sync
        if status.value == "online":
            asyncio.create_task(sync_service.force_sync())
    
    async def _log_step(self, message: str):
        """Log a startup step"""
        timestamp = datetime.utcnow()
        self.startup_log.append({
            "timestamp": timestamp.isoformat(),
            "message": message
        })
        logger.info(f"📋 {message}")
    
    def _get_startup_status(self) -> Dict[str, Any]:
        """Get startup status"""
        return {
            "initialized": self.services_initialized,
            "startup_time": self.startup_time.isoformat() if self.startup_time else None,
            "duration_seconds": (
                (datetime.utcnow() - self.startup_time).total_seconds() 
                if self.startup_time else None
            ),
            "log": self.startup_log,
            "configuration": {
                "use_sqlite": settings.USE_SQLITE,
                "sync_enabled": settings.SYNC_ENABLED,
                "offline_mode_enabled": settings.OFFLINE_MODE_ENABLED,
                "conflict_resolution": settings.SYNC_CONFLICT_RESOLUTION,
                "sync_interval": settings.SYNC_INTERVAL_SECONDS
            }
        }
    
    async def shutdown_services(self):
        """Shutdown all services gracefully"""
        logger.info("🛑 Shutting down Prontivus services...")
        
        try:
            # Stop monitoring
            await db_monitor.stop_monitoring()
            logger.info("✅ Database monitoring stopped")
            
            # Stop offline manager
            offline_manager.stop_connection_monitoring()
            offline_manager.close()
            logger.info("✅ Offline manager stopped")
            
            # Close sync service
            sync_service.close()
            logger.info("✅ Sync service stopped")
            
            logger.info("🎉 All services shut down gracefully")
            
        except Exception as e:
            logger.error(f"❌ Error during shutdown: {e}")
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get current service status"""
        return {
            "startup": self._get_startup_status(),
            "sync": sync_service.get_sync_status(),
            "offline": offline_manager.get_offline_stats(),
            "monitoring": {
                "is_monitoring": db_monitor.is_monitoring,
                "health_status": db_monitor.get_health_status(),
                "metrics_count": len(db_monitor.metrics_history)
            }
        }

# Global startup service instance
startup_service = StartupService()
