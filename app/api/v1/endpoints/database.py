"""
Database management API endpoints
Provides endpoints for sync, monitoring, and database operations
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

from app.database.database import get_db
from app.services.sync_service import sync_service
from app.services.offline_service import offline_manager
from app.services.database_monitor import db_monitor
from app.database.migrations import DatabaseMigrator, MigrationType
from app.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/health")
async def get_database_health():
    """Get database health status"""
    try:
        health_status = db_monitor.get_health_status()
        return {
            "status": "success",
            "data": health_status,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Failed to get database health: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics")
async def get_database_metrics(hours: int = 24):
    """Get database performance metrics"""
    try:
        metrics = db_monitor.get_metrics_history(hours)
        current_metrics = db_monitor.get_current_metrics()
        
        return {
            "status": "success",
            "data": {
                "current": current_metrics.__dict__ if current_metrics else None,
                "history": metrics,
                "summary": db_monitor.get_performance_summary()
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Failed to get database metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sync/status")
async def get_sync_status():
    """Get database sync status"""
    try:
        sync_status = sync_service.get_sync_status()
        conflicts = sync_service.get_conflicts()
        
        return {
            "status": "success",
            "data": {
                "sync_status": sync_status,
                "conflicts": conflicts,
                "conflict_count": len(conflicts)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Failed to get sync status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync/force")
async def force_sync(background_tasks: BackgroundTasks):
    """Force an immediate database sync"""
    try:
        # Run sync in background
        background_tasks.add_task(sync_service.force_sync)
        
        return {
            "status": "success",
            "message": "Sync initiated in background",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Failed to force sync: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sync/conflicts")
async def get_sync_conflicts():
    """Get sync conflicts"""
    try:
        conflicts = sync_service.get_conflicts()
        
        return {
            "status": "success",
            "data": {
                "conflicts": conflicts,
                "count": len(conflicts)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Failed to get sync conflicts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync/conflicts/{conflict_id}/resolve")
async def resolve_conflict(conflict_id: str, resolution: str):
    """Resolve a sync conflict"""
    try:
        if resolution not in ["postgresql_wins", "sqlite_wins", "manual"]:
            raise HTTPException(status_code=400, detail="Invalid resolution strategy")
        
        sync_service.resolve_conflict_manually(conflict_id, resolution)
        
        return {
            "status": "success",
            "message": f"Conflict {conflict_id} resolved with {resolution}",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Failed to resolve conflict: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/offline/status")
async def get_offline_status():
    """Get offline mode status"""
    try:
        connection_status = offline_manager.get_connection_status()
        offline_stats = offline_manager.get_offline_stats()
        
        return {
            "status": "success",
            "data": {
                "connection_status": connection_status,
                "offline_stats": offline_stats
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Failed to get offline status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/offline/operations")
async def get_offline_operations(status: Optional[str] = None):
    """Get offline operations"""
    try:
        operations = offline_manager.get_offline_operations(status)
        
        return {
            "status": "success",
            "data": {
                "operations": operations,
                "count": len(operations)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Failed to get offline operations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/offline/cleanup")
async def cleanup_offline_operations():
    """Cleanup old offline operations"""
    try:
        offline_manager.cleanup_old_operations()
        
        return {
            "status": "success",
            "message": "Offline operations cleaned up",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Failed to cleanup offline operations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/migrations/history")
async def get_migration_history():
    """Get migration history"""
    try:
        migrator = DatabaseMigrator(settings.DATABASE_URL)
        history = migrator.get_migration_history()
        
        return {
            "status": "success",
            "data": {
                "migrations": history,
                "count": len(history)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Failed to get migration history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/migrations/pending")
async def get_pending_migrations():
    """Get pending migrations"""
    try:
        migrator = DatabaseMigrator(settings.DATABASE_URL)
        pending = migrator.get_pending_migrations()
        
        return {
            "status": "success",
            "data": {
                "migrations": [
                    {
                        "version": m.version,
                        "name": m.name,
                        "migration_type": m.migration_type.value,
                        "description": m.description,
                        "created_at": m.created_at.isoformat()
                    }
                    for m in pending
                ],
                "count": len(pending)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Failed to get pending migrations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/migrations/run")
async def run_pending_migrations():
    """Run all pending migrations"""
    try:
        migrator = DatabaseMigrator(settings.DATABASE_URL)
        success = migrator.run_all_pending_migrations()
        
        if success:
            return {
                "status": "success",
                "message": "All pending migrations completed successfully",
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="Migration failed")
            
    except Exception as e:
        logger.error(f"❌ Failed to run migrations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/migrations/create")
async def create_migration(
    name: str,
    migration_type: str,
    up_sql: str,
    down_sql: Optional[str] = None,
    description: str = ""
):
    """Create a new migration"""
    try:
        if migration_type not in [t.value for t in MigrationType]:
            raise HTTPException(status_code=400, detail="Invalid migration type")
        
        migrator = DatabaseMigrator(settings.DATABASE_URL)
        migration = migrator.create_migration(
            name=name,
            migration_type=MigrationType(migration_type),
            up_sql=up_sql,
            down_sql=down_sql,
            description=description
        )
        
        return {
            "status": "success",
            "data": {
                "version": migration.version,
                "name": migration.name,
                "migration_type": migration.migration_type.value,
                "description": migration.description,
                "created_at": migration.created_at.isoformat()
            },
            "message": f"Migration {migration.version}_{migration.name} created successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Failed to create migration: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/connection/status")
async def get_connection_status():
    """Get database connection status"""
    try:
        # Test PostgreSQL connection
        postgres_status = offline_manager._test_postgresql_connection()
        
        # Test SQLite connection
        sqlite_status = True  # SQLite is always available
        
        return {
            "status": "success",
            "data": {
                "postgresql": {
                    "connected": postgres_status,
                    "status": "online" if postgres_status else "offline"
                },
                "sqlite": {
                    "connected": sqlite_status,
                    "status": "online"
                },
                "current_mode": "sqlite" if settings.USE_SQLITE else "postgresql"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Failed to get connection status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/monitoring/start")
async def start_monitoring():
    """Start database monitoring"""
    try:
        if db_monitor.is_monitoring:
            return {
                "status": "success",
                "message": "Monitoring already running",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Start monitoring in background
        import asyncio
        asyncio.create_task(db_monitor.start_monitoring())
        
        return {
            "status": "success",
            "message": "Database monitoring started",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Failed to start monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/monitoring/stop")
async def stop_monitoring():
    """Stop database monitoring"""
    try:
        await db_monitor.stop_monitoring()
        
        return {
            "status": "success",
            "message": "Database monitoring stopped",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Failed to stop monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/monitoring/health-check")
async def force_health_check():
    """Force an immediate health check"""
    try:
        health_status = await db_monitor.force_health_check()
        
        return {
            "status": "success",
            "data": health_status,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Failed to force health check: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/info")
async def get_database_info():
    """Get comprehensive database information"""
    try:
        # Get all database information
        health_status = db_monitor.get_health_status()
        sync_status = sync_service.get_sync_status()
        connection_status = offline_manager.get_connection_status()
        offline_stats = offline_manager.get_offline_stats()
        
        return {
            "status": "success",
            "data": {
                "health": health_status,
                "sync": sync_status,
                "connection": connection_status,
                "offline": offline_stats,
                "configuration": {
                    "use_sqlite": settings.USE_SQLITE,
                    "sync_enabled": settings.SYNC_ENABLED,
                    "offline_mode_enabled": settings.OFFLINE_MODE_ENABLED,
                    "conflict_resolution": settings.SYNC_CONFLICT_RESOLUTION
                }
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Failed to get database info: {e}")
        raise HTTPException(status_code=500, detail=str(e))
