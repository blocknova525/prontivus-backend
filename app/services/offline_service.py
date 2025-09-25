"""
Offline-first data flow service
Handles offline data storage, sync triggers, and connection monitoring
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
import json
import os
import threading
import time
from dataclasses import dataclass
from enum import Enum

from app.core.config import settings
from app.services.sync_service import sync_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConnectionStatus(Enum):
    """Connection status"""
    ONLINE = "online"
    OFFLINE = "offline"
    CONNECTING = "connecting"
    UNKNOWN = "unknown"

class OfflineOperation(Enum):
    """Offline operation types"""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    SYNC = "sync"

@dataclass
class OfflineRecord:
    """Represents a record stored offline"""
    table_name: str
    operation: OfflineOperation
    record_id: Any
    data: Dict[str, Any]
    timestamp: datetime
    sync_status: str = "pending"
    retry_count: int = 0
    last_error: Optional[str] = None

class OfflineDataManager:
    """Manages offline data storage and operations"""
    
    def __init__(self):
        self.sqlite_engine = None
        self.sqlite_session = None
        self.offline_queue: List[OfflineRecord] = []
        self.connection_status = ConnectionStatus.UNKNOWN
        self.connection_callbacks: List[Callable] = []
        self.is_monitoring = False
        self.monitor_thread = None
        
        # Initialize SQLite for offline storage
        self._initialize_offline_storage()
    
    def _initialize_offline_storage(self):
        """Initialize SQLite engine for offline storage"""
        try:
            self.sqlite_engine = create_engine(
                settings.SQLITE_URL,
                connect_args={"check_same_thread": False},
                poolclass=None,
                echo=False
            )
            
            self.sqlite_session = sessionmaker(bind=self.sqlite_engine)()
            
            # Create offline operations table if it doesn't exist
            self._create_offline_tables()
            
            logger.info("✅ Offline storage initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize offline storage: {e}")
            raise
    
    def _create_offline_tables(self):
        """Create tables for offline operations tracking"""
        try:
            with self.sqlite_engine.connect() as conn:
                # Create offline operations table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS offline_operations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        table_name TEXT NOT NULL,
                        operation TEXT NOT NULL,
                        record_id TEXT,
                        data TEXT NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        sync_status TEXT DEFAULT 'pending',
                        retry_count INTEGER DEFAULT 0,
                        last_error TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                
                # Create connection status table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS connection_status (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        status TEXT NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        details TEXT
                    )
                """))
                
                # Create indexes
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_offline_operations_sync_status 
                    ON offline_operations(sync_status)
                """))
                
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_offline_operations_timestamp 
                    ON offline_operations(timestamp)
                """))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"❌ Failed to create offline tables: {e}")
    
    def start_connection_monitoring(self):
        """Start monitoring database connection status"""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_connection)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        logger.info("🔍 Started connection monitoring")
    
    def stop_connection_monitoring(self):
        """Stop monitoring database connection status"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        logger.info("🛑 Stopped connection monitoring")
    
    def _monitor_connection(self):
        """Monitor database connection in background thread"""
        while self.is_monitoring:
            try:
                # Test PostgreSQL connection
                postgres_status = self._test_postgresql_connection()
                
                # Update connection status
                old_status = self.connection_status
                self.connection_status = ConnectionStatus.ONLINE if postgres_status else ConnectionStatus.OFFLINE
                
                # Notify callbacks if status changed
                if old_status != self.connection_status:
                    self._notify_connection_change()
                
                # Log connection status
                self._log_connection_status()
                
                # If online, trigger sync
                if self.connection_status == ConnectionStatus.ONLINE:
                    asyncio.create_task(self._trigger_sync())
                
            except Exception as e:
                logger.error(f"❌ Connection monitoring error: {e}")
                self.connection_status = ConnectionStatus.UNKNOWN
            
            # Wait before next check
            time.sleep(30)  # Check every 30 seconds
    
    def _test_postgresql_connection(self) -> bool:
        """Test PostgreSQL connection"""
        try:
            postgres_engine = create_engine(settings.DATABASE_URL)
            with postgres_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except:
            return False
    
    def _notify_connection_change(self):
        """Notify registered callbacks of connection status change"""
        for callback in self.connection_callbacks:
            try:
                callback(self.connection_status)
            except Exception as e:
                logger.error(f"❌ Connection callback error: {e}")
    
    def _log_connection_status(self):
        """Log current connection status"""
        try:
            with self.sqlite_engine.connect() as conn:
                conn.execute(text("""
                    INSERT INTO connection_status (status, details)
                    VALUES (:status, :details)
                """), {
                    "status": self.connection_status.value,
                    "details": f"Auto-detected at {datetime.utcnow()}"
                })
                conn.commit()
                
        except Exception as e:
            logger.error(f"❌ Failed to log connection status: {e}")
    
    def register_connection_callback(self, callback: Callable):
        """Register a callback for connection status changes"""
        self.connection_callbacks.append(callback)
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get current connection status and history"""
        try:
            with self.sqlite_engine.connect() as conn:
                # Get current status
                current_status = {
                    "status": self.connection_status.value,
                    "is_monitoring": self.is_monitoring,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                # Get recent status history
                history = conn.execute(text("""
                    SELECT status, timestamp, details
                    FROM connection_status
                    ORDER BY timestamp DESC
                    LIMIT 10
                """)).fetchall()
                
                status_history = [
                    {
                        "status": row[0],
                        "timestamp": row[1],
                        "details": row[2]
                    }
                    for row in history
                ]
                
                return {
                    "current": current_status,
                    "history": status_history
                }
                
        except Exception as e:
            logger.error(f"❌ Failed to get connection status: {e}")
            return {"current": {"status": "unknown"}, "history": []}
    
    async def store_offline_operation(self, table_name: str, operation: OfflineOperation, 
                                    record_id: Any, data: Dict[str, Any]):
        """Store an operation for offline processing"""
        try:
            offline_record = OfflineRecord(
                table_name=table_name,
                operation=operation,
                record_id=record_id,
                data=data,
                timestamp=datetime.utcnow()
            )
            
            # Store in SQLite
            with self.sqlite_engine.connect() as conn:
                conn.execute(text("""
                    INSERT INTO offline_operations 
                    (table_name, operation, record_id, data, timestamp, sync_status)
                    VALUES (:table_name, :operation, :record_id, :data, :timestamp, :sync_status)
                """), {
                    "table_name": table_name,
                    "operation": operation.value,
                    "record_id": str(record_id) if record_id else None,
                    "data": json.dumps(data),
                    "timestamp": offline_record.timestamp,
                    "sync_status": offline_record.sync_status
                })
                conn.commit()
            
            # Add to memory queue
            self.offline_queue.append(offline_record)
            
            logger.info(f"📱 Stored offline operation: {operation.value} on {table_name}")
            
            # If online, try to sync immediately
            if self.connection_status == ConnectionStatus.ONLINE:
                await self._trigger_sync()
            
        except Exception as e:
            logger.error(f"❌ Failed to store offline operation: {e}")
    
    async def _trigger_sync(self):
        """Trigger synchronization of offline operations"""
        if not self.offline_queue:
            return
        
        logger.info(f"🔄 Triggering sync for {len(self.offline_queue)} offline operations")
        
        try:
            # Process offline operations
            for operation in self.offline_queue[:]:
                await self._process_offline_operation(operation)
            
            # Clear processed operations
            self.offline_queue.clear()
            
        except Exception as e:
            logger.error(f"❌ Failed to trigger sync: {e}")
    
    async def _process_offline_operation(self, operation: OfflineRecord):
        """Process a single offline operation"""
        try:
            # Try to apply operation to PostgreSQL
            success = await self._apply_operation_to_postgresql(operation)
            
            if success:
                # Mark as synced
                await self._mark_operation_synced(operation)
                logger.info(f"✅ Synced offline operation: {operation.operation.value} on {operation.table_name}")
            else:
                # Increment retry count
                operation.retry_count += 1
                if operation.retry_count >= settings.SYNC_RETRY_ATTEMPTS:
                    await self._mark_operation_failed(operation, "Max retry attempts reached")
                else:
                    logger.warning(f"⚠️ Retrying offline operation: {operation.operation.value} on {operation.table_name}")
            
        except Exception as e:
            logger.error(f"❌ Failed to process offline operation: {e}")
            operation.last_error = str(e)
    
    async def _apply_operation_to_postgresql(self, operation: OfflineRecord) -> bool:
        """Apply offline operation to PostgreSQL"""
        try:
            postgres_engine = create_engine(settings.DATABASE_URL)
            
            with postgres_engine.connect() as conn:
                if operation.operation == OfflineOperation.CREATE:
                    await self._create_record_postgresql(conn, operation)
                elif operation.operation == OfflineOperation.UPDATE:
                    await self._update_record_postgresql(conn, operation)
                elif operation.operation == OfflineOperation.DELETE:
                    await self._delete_record_postgresql(conn, operation)
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to apply operation to PostgreSQL: {e}")
            return False
    
    async def _create_record_postgresql(self, conn, operation: OfflineRecord):
        """Create record in PostgreSQL"""
        columns = list(operation.data.keys())
        placeholders = ", ".join([f":{col}" for col in columns])
        
        query = text(f"""
            INSERT INTO {operation.table_name} ({', '.join(columns)})
            VALUES ({placeholders})
        """)
        
        conn.execute(query, operation.data)
    
    async def _update_record_postgresql(self, conn, operation: OfflineRecord):
        """Update record in PostgreSQL"""
        id_field = self._get_id_field(operation.table_name)
        record_id = operation.data.get(id_field)
        
        if not record_id:
            return
        
        update_fields = [f"{col} = :{col}" for col in operation.data.keys() if col != id_field]
        
        query = text(f"""
            UPDATE {operation.table_name} 
            SET {', '.join(update_fields)}
            WHERE {id_field} = :{id_field}
        """)
        
        conn.execute(query, operation.data)
    
    async def _delete_record_postgresql(self, conn, operation: OfflineRecord):
        """Delete record from PostgreSQL"""
        id_field = self._get_id_field(operation.table_name)
        record_id = operation.data.get(id_field)
        
        if not record_id:
            return
        
        query = text(f"""
            DELETE FROM {operation.table_name} 
            WHERE {id_field} = :{id_field}
        """)
        
        conn.execute(query, {id_field: record_id})
    
    def _get_id_field(self, table_name: str) -> str:
        """Get the primary key field name for a table"""
        id_mapping = {
            "users": "id",
            "patients": "id", 
            "appointments": "id",
            "medical_records": "id",
            "prescriptions": "id"
        }
        return id_mapping.get(table_name, "id")
    
    async def _mark_operation_synced(self, operation: OfflineRecord):
        """Mark operation as successfully synced"""
        try:
            with self.sqlite_engine.connect() as conn:
                conn.execute(text("""
                    UPDATE offline_operations 
                    SET sync_status = 'synced'
                    WHERE table_name = :table_name 
                    AND operation = :operation 
                    AND record_id = :record_id
                    AND timestamp = :timestamp
                """), {
                    "table_name": operation.table_name,
                    "operation": operation.operation.value,
                    "record_id": str(operation.record_id) if operation.record_id else None,
                    "timestamp": operation.timestamp
                })
                conn.commit()
                
        except Exception as e:
            logger.error(f"❌ Failed to mark operation as synced: {e}")
    
    async def _mark_operation_failed(self, operation: OfflineRecord, error: str):
        """Mark operation as failed"""
        try:
            with self.sqlite_engine.connect() as conn:
                conn.execute(text("""
                    UPDATE offline_operations 
                    SET sync_status = 'failed', last_error = :error
                    WHERE table_name = :table_name 
                    AND operation = :operation 
                    AND record_id = :record_id
                    AND timestamp = :timestamp
                """), {
                    "table_name": operation.table_name,
                    "operation": operation.operation.value,
                    "record_id": str(operation.record_id) if operation.record_id else None,
                    "timestamp": operation.timestamp,
                    "error": error
                })
                conn.commit()
                
        except Exception as e:
            logger.error(f"❌ Failed to mark operation as failed: {e}")
    
    def get_offline_operations(self, status: str = None) -> List[Dict[str, Any]]:
        """Get offline operations with optional status filter"""
        try:
            with self.sqlite_engine.connect() as conn:
                if status:
                    query = text("""
                        SELECT table_name, operation, record_id, data, timestamp, 
                               sync_status, retry_count, last_error
                        FROM offline_operations
                        WHERE sync_status = :status
                        ORDER BY timestamp DESC
                    """)
                    results = conn.execute(query, {"status": status}).fetchall()
                else:
                    query = text("""
                        SELECT table_name, operation, record_id, data, timestamp, 
                               sync_status, retry_count, last_error
                        FROM offline_operations
                        ORDER BY timestamp DESC
                    """)
                    results = conn.execute(query).fetchall()
                
                return [
                    {
                        "table_name": row[0],
                        "operation": row[1],
                        "record_id": row[2],
                        "data": json.loads(row[3]) if row[3] else {},
                        "timestamp": row[4],
                        "sync_status": row[5],
                        "retry_count": row[6],
                        "last_error": row[7]
                    }
                    for row in results
                ]
                
        except Exception as e:
            logger.error(f"❌ Failed to get offline operations: {e}")
            return []
    
    def cleanup_old_operations(self):
        """Cleanup old offline operations"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=settings.OFFLINE_DATA_RETENTION_DAYS)
            
            with self.sqlite_engine.connect() as conn:
                conn.execute(text("""
                    DELETE FROM offline_operations 
                    WHERE timestamp < :cutoff_date 
                    AND sync_status = 'synced'
                """), {"cutoff_date": cutoff_date})
                conn.commit()
                
            logger.info("🧹 Cleaned up old offline operations")
                
        except Exception as e:
            logger.error(f"❌ Failed to cleanup old operations: {e}")
    
    def get_offline_stats(self) -> Dict[str, Any]:
        """Get offline operations statistics"""
        try:
            with self.sqlite_engine.connect() as conn:
                # Get counts by status
                status_counts = conn.execute(text("""
                    SELECT sync_status, COUNT(*) as count
                    FROM offline_operations
                    GROUP BY sync_status
                """)).fetchall()
                
                # Get counts by operation type
                operation_counts = conn.execute(text("""
                    SELECT operation, COUNT(*) as count
                    FROM offline_operations
                    GROUP BY operation
                """)).fetchall()
                
                # Get recent activity
                recent_activity = conn.execute(text("""
                    SELECT COUNT(*) as count
                    FROM offline_operations
                    WHERE timestamp > datetime('now', '-1 hour')
                """)).fetchone()
                
                return {
                    "status_counts": {row[0]: row[1] for row in status_counts},
                    "operation_counts": {row[0]: row[1] for row in operation_counts},
                    "recent_activity": recent_activity[0] if recent_activity else 0,
                    "connection_status": self.connection_status.value,
                    "queue_size": len(self.offline_queue)
                }
                
        except Exception as e:
            logger.error(f"❌ Failed to get offline stats: {e}")
            return {}
    
    def close(self):
        """Close offline data manager"""
        self.stop_connection_monitoring()
        if self.sqlite_session:
            self.sqlite_session.close()
        logger.info("🔒 Offline data manager closed")

# Global offline data manager instance
offline_manager = OfflineDataManager()
