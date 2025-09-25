"""
Database synchronization service for PostgreSQL and SQLite
Handles offline-first data flow with conflict resolution
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy import create_engine, text, func
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import json
import os
from dataclasses import dataclass
from enum import Enum

from app.core.config import settings
from app.models.base import Base
from app.models.user import User
from app.models.patient import Patient
from app.models.appointment import Appointment
from app.models.medical_record import MedicalRecord
from app.models.prescription import Prescription

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SyncStatus(Enum):
    """Sync operation status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CONFLICT = "conflict"

class ConflictResolution(Enum):
    """Conflict resolution strategies"""
    POSTGRESQL_WINS = "postgresql_wins"
    SQLITE_WINS = "sqlite_wins"
    MANUAL = "manual"
    NEWEST_WINS = "newest_wins"

@dataclass
class SyncOperation:
    """Represents a sync operation"""
    table_name: str
    operation_type: str  # insert, update, delete
    record_id: Any
    data: Dict[str, Any]
    timestamp: datetime
    source_db: str  # postgresql or sqlite
    status: SyncStatus = SyncStatus.PENDING
    conflict_data: Optional[Dict[str, Any]] = None
    retry_count: int = 0

class DatabaseSyncService:
    """Handles synchronization between PostgreSQL and SQLite databases"""
    
    def __init__(self):
        self.postgres_engine = None
        self.sqlite_engine = None
        self.postgres_session = None
        self.sqlite_session = None
        self.sync_queue: List[SyncOperation] = []
        self.conflict_queue: List[SyncOperation] = []
        self.is_syncing = False
        
        # Initialize engines
        self._initialize_engines()
    
    def _initialize_engines(self):
        """Initialize database engines for both PostgreSQL and SQLite"""
        try:
            # PostgreSQL engine
            self.postgres_engine = create_engine(
                settings.DATABASE_URL,
                echo=False,
                pool_pre_ping=True,
                pool_recycle=3600,
                pool_size=10,
                max_overflow=20
            )
            
            # SQLite engine
            self.sqlite_engine = create_engine(
                settings.SQLITE_URL,
                connect_args={"check_same_thread": False},
                poolclass=None,
                echo=False
            )
            
            # Create session factories
            PostgresSession = sessionmaker(bind=self.postgres_engine)
            SQLiteSession = sessionmaker(bind=self.sqlite_engine)
            
            self.postgres_session = PostgresSession()
            self.sqlite_session = SQLiteSession()
            
            logger.info("✅ Database engines initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize database engines: {e}")
            raise
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get current sync status and statistics"""
        return {
            "is_syncing": self.is_syncing,
            "queue_size": len(self.sync_queue),
            "conflict_count": len(self.conflict_queue),
            "last_sync": self._get_last_sync_time(),
            "sync_enabled": settings.SYNC_ENABLED,
            "conflict_resolution": settings.SYNC_CONFLICT_RESOLUTION
        }
    
    def _get_last_sync_time(self) -> Optional[datetime]:
        """Get the last successful sync time"""
        try:
            # Check sync log table if it exists
            with self.postgres_engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT MAX(sync_timestamp) 
                    FROM sync_log 
                    WHERE status = 'completed'
                """)).fetchone()
                return result[0] if result and result[0] else None
        except:
            return None
    
    async def start_sync_service(self):
        """Start the background sync service"""
        if not settings.SYNC_ENABLED:
            logger.info("🔄 Sync service disabled in configuration")
            return
        
        logger.info("🚀 Starting database sync service...")
        
        while True:
            try:
                await self._sync_cycle()
                await asyncio.sleep(settings.SYNC_INTERVAL_SECONDS)
            except Exception as e:
                logger.error(f"❌ Sync service error: {e}")
                await asyncio.sleep(settings.SYNC_RETRY_DELAY)
    
    async def _sync_cycle(self):
        """Perform one sync cycle"""
        if self.is_syncing:
            logger.debug("⏳ Sync already in progress, skipping cycle")
            return
        
        self.is_syncing = True
        logger.info("🔄 Starting sync cycle...")
        
        try:
            # 1. Sync from SQLite to PostgreSQL (offline changes)
            await self._sync_sqlite_to_postgresql()
            
            # 2. Sync from PostgreSQL to SQLite (online changes)
            await self._sync_postgresql_to_sqlite()
            
            # 3. Handle conflicts
            await self._resolve_conflicts()
            
            # 4. Cleanup old sync data
            await self._cleanup_sync_data()
            
            logger.info("✅ Sync cycle completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Sync cycle failed: {e}")
        finally:
            self.is_syncing = False
    
    async def _sync_sqlite_to_postgresql(self):
        """Sync changes from SQLite to PostgreSQL"""
        logger.debug("📱 Syncing SQLite → PostgreSQL...")
        
        try:
            # Get tables to sync
            tables_to_sync = self._get_sync_tables()
            
            for table_name in tables_to_sync:
                await self._sync_table_sqlite_to_postgresql(table_name)
                
        except Exception as e:
            logger.error(f"❌ SQLite to PostgreSQL sync failed: {e}")
    
    async def _sync_postgresql_to_sqlite(self):
        """Sync changes from PostgreSQL to SQLite"""
        logger.debug("🌐 Syncing PostgreSQL → SQLite...")
        
        try:
            # Get tables to sync
            tables_to_sync = self._get_sync_tables()
            
            for table_name in tables_to_sync:
                await self._sync_table_postgresql_to_sqlite(table_name)
                
        except Exception as e:
            logger.error(f"❌ PostgreSQL to SQLite sync failed: {e}")
    
    def _get_sync_tables(self) -> List[str]:
        """Get list of tables to sync"""
        return [
            "users", "patients", "appointments", 
            "medical_records", "prescriptions"
        ]
    
    async def _sync_table_sqlite_to_postgresql(self, table_name: str):
        """Sync a specific table from SQLite to PostgreSQL"""
        try:
            # Get records modified since last sync
            last_sync = self._get_last_sync_time()
            
            with self.sqlite_engine.connect() as conn:
                if last_sync:
                    query = text(f"""
                        SELECT * FROM {table_name} 
                        WHERE updated_at > :last_sync
                        ORDER BY updated_at
                    """)
                    records = conn.execute(query, {"last_sync": last_sync}).fetchall()
                else:
                    query = text(f"SELECT * FROM {table_name} ORDER BY updated_at")
                    records = conn.execute(query).fetchall()
            
            # Process each record
            for record in records:
                await self._sync_record_to_postgresql(table_name, dict(record._mapping))
                
        except Exception as e:
            logger.error(f"❌ Failed to sync table {table_name}: {e}")
    
    async def _sync_table_postgresql_to_sqlite(self, table_name: str):
        """Sync a specific table from PostgreSQL to SQLite"""
        try:
            # Get records modified since last sync
            last_sync = self._get_last_sync_time()
            
            with self.postgres_engine.connect() as conn:
                if last_sync:
                    query = text(f"""
                        SELECT * FROM {table_name} 
                        WHERE updated_at > :last_sync
                        ORDER BY updated_at
                    """)
                    records = conn.execute(query, {"last_sync": last_sync}).fetchall()
                else:
                    query = text(f"SELECT * FROM {table_name} ORDER BY updated_at")
                    records = conn.execute(query).fetchall()
            
            # Process each record
            for record in records:
                await self._sync_record_to_sqlite(table_name, dict(record._mapping))
                
        except Exception as e:
            logger.error(f"❌ Failed to sync table {table_name}: {e}")
    
    async def _sync_record_to_postgresql(self, table_name: str, record_data: Dict[str, Any]):
        """Sync a single record to PostgreSQL"""
        try:
            with self.postgres_engine.connect() as conn:
                # Check if record exists
                id_field = self._get_id_field(table_name)
                record_id = record_data.get(id_field)
                
                if record_id:
                    # Check for conflicts
                    existing = conn.execute(
                        text(f"SELECT * FROM {table_name} WHERE {id_field} = :id"),
                        {"id": record_id}
                    ).fetchone()
                    
                    if existing:
                        # Handle conflict
                        await self._handle_conflict(table_name, record_data, dict(existing._mapping), "sqlite")
                    else:
                        # Insert new record
                        await self._insert_record_postgresql(table_name, record_data)
                else:
                    # Insert new record
                    await self._insert_record_postgresql(table_name, record_data)
                    
        except Exception as e:
            logger.error(f"❌ Failed to sync record to PostgreSQL: {e}")
    
    async def _sync_record_to_sqlite(self, table_name: str, record_data: Dict[str, Any]):
        """Sync a single record to SQLite"""
        try:
            with self.sqlite_engine.connect() as conn:
                # Check if record exists
                id_field = self._get_id_field(table_name)
                record_id = record_data.get(id_field)
                
                if record_id:
                    # Check for conflicts
                    existing = conn.execute(
                        text(f"SELECT * FROM {table_name} WHERE {id_field} = :id"),
                        {"id": record_id}
                    ).fetchone()
                    
                    if existing:
                        # Handle conflict
                        await self._handle_conflict(table_name, record_data, dict(existing._mapping), "postgresql")
                    else:
                        # Insert new record
                        await self._insert_record_sqlite(table_name, record_data)
                else:
                    # Insert new record
                    await self._insert_record_sqlite(table_name, record_data)
                    
        except Exception as e:
            logger.error(f"❌ Failed to sync record to SQLite: {e}")
    
    async def _handle_conflict(self, table_name: str, new_data: Dict[str, Any], 
                             existing_data: Dict[str, Any], source_db: str):
        """Handle data conflicts between databases"""
        logger.warning(f"⚠️ Conflict detected in {table_name} (source: {source_db})")
        
        # Create conflict operation
        conflict_op = SyncOperation(
            table_name=table_name,
            operation_type="conflict",
            record_id=new_data.get(self._get_id_field(table_name)),
            data=new_data,
            timestamp=datetime.utcnow(),
            source_db=source_db,
            status=SyncStatus.CONFLICT,
            conflict_data=existing_data
        )
        
        self.conflict_queue.append(conflict_op)
        
        # Apply conflict resolution strategy
        resolution = ConflictResolution(settings.SYNC_CONFLICT_RESOLUTION)
        
        if resolution == ConflictResolution.POSTGRESQL_WINS:
            await self._apply_postgresql_wins(table_name, new_data, existing_data)
        elif resolution == ConflictResolution.SQLITE_WINS:
            await self._apply_sqlite_wins(table_name, new_data, existing_data)
        elif resolution == ConflictResolution.NEWEST_WINS:
            await self._apply_newest_wins(table_name, new_data, existing_data)
        else:
            # Manual resolution - just log the conflict
            logger.info(f"🔍 Manual conflict resolution required for {table_name}")
    
    async def _apply_postgresql_wins(self, table_name: str, new_data: Dict[str, Any], 
                                   existing_data: Dict[str, Any]):
        """Apply PostgreSQL wins conflict resolution"""
        # Update SQLite with PostgreSQL data
        await self._update_record_sqlite(table_name, new_data)
        logger.info(f"✅ Applied PostgreSQL wins for {table_name}")
    
    async def _apply_sqlite_wins(self, table_name: str, new_data: Dict[str, Any], 
                                existing_data: Dict[str, Any]):
        """Apply SQLite wins conflict resolution"""
        # Update PostgreSQL with SQLite data
        await self._update_record_postgresql(table_name, new_data)
        logger.info(f"✅ Applied SQLite wins for {table_name}")
    
    async def _apply_newest_wins(self, table_name: str, new_data: Dict[str, Any], 
                               existing_data: Dict[str, Any]):
        """Apply newest wins conflict resolution"""
        new_timestamp = new_data.get('updated_at')
        existing_timestamp = existing_data.get('updated_at')
        
        if new_timestamp and existing_timestamp:
            if new_timestamp > existing_timestamp:
                await self._apply_postgresql_wins(table_name, new_data, existing_data)
            else:
                await self._apply_sqlite_wins(table_name, new_data, existing_data)
        else:
            # Default to PostgreSQL wins if timestamps are missing
            await self._apply_postgresql_wins(table_name, new_data, existing_data)
    
    async def _insert_record_postgresql(self, table_name: str, record_data: Dict[str, Any]):
        """Insert record into PostgreSQL"""
        try:
            with self.postgres_engine.connect() as conn:
                columns = list(record_data.keys())
                values = list(record_data.values())
                
                placeholders = ", ".join([f":{col}" for col in columns])
                query = text(f"""
                    INSERT INTO {table_name} ({', '.join(columns)})
                    VALUES ({placeholders})
                """)
                
                conn.execute(query, record_data)
                conn.commit()
                
        except Exception as e:
            logger.error(f"❌ Failed to insert record into PostgreSQL: {e}")
    
    async def _insert_record_sqlite(self, table_name: str, record_data: Dict[str, Any]):
        """Insert record into SQLite"""
        try:
            with self.sqlite_engine.connect() as conn:
                columns = list(record_data.keys())
                values = list(record_data.values())
                
                placeholders = ", ".join([f":{col}" for col in columns])
                query = text(f"""
                    INSERT INTO {table_name} ({', '.join(columns)})
                    VALUES ({placeholders})
                """)
                
                conn.execute(query, record_data)
                conn.commit()
                
        except Exception as e:
            logger.error(f"❌ Failed to insert record into SQLite: {e}")
    
    async def _update_record_postgresql(self, table_name: str, record_data: Dict[str, Any]):
        """Update record in PostgreSQL"""
        try:
            with self.postgres_engine.connect() as conn:
                id_field = self._get_id_field(table_name)
                record_id = record_data.get(id_field)
                
                if not record_id:
                    return
                
                # Build update query
                update_fields = [f"{col} = :{col}" for col in record_data.keys() if col != id_field]
                query = text(f"""
                    UPDATE {table_name} 
                    SET {', '.join(update_fields)}
                    WHERE {id_field} = :{id_field}
                """)
                
                conn.execute(query, record_data)
                conn.commit()
                
        except Exception as e:
            logger.error(f"❌ Failed to update record in PostgreSQL: {e}")
    
    async def _update_record_sqlite(self, table_name: str, record_data: Dict[str, Any]):
        """Update record in SQLite"""
        try:
            with self.sqlite_engine.connect() as conn:
                id_field = self._get_id_field(table_name)
                record_id = record_data.get(id_field)
                
                if not record_id:
                    return
                
                # Build update query
                update_fields = [f"{col} = :{col}" for col in record_data.keys() if col != id_field]
                query = text(f"""
                    UPDATE {table_name} 
                    SET {', '.join(update_fields)}
                    WHERE {id_field} = :{id_field}
                """)
                
                conn.execute(query, record_data)
                conn.commit()
                
        except Exception as e:
            logger.error(f"❌ Failed to update record in SQLite: {e}")
    
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
    
    async def _resolve_conflicts(self):
        """Resolve pending conflicts"""
        if not self.conflict_queue:
            return
        
        logger.info(f"🔧 Resolving {len(self.conflict_queue)} conflicts...")
        
        for conflict in self.conflict_queue:
            try:
                # Apply conflict resolution
                await self._handle_conflict(
                    conflict.table_name,
                    conflict.data,
                    conflict.conflict_data,
                    conflict.source_db
                )
            except Exception as e:
                logger.error(f"❌ Failed to resolve conflict: {e}")
        
        # Clear resolved conflicts
        self.conflict_queue.clear()
    
    async def _cleanup_sync_data(self):
        """Cleanup old sync data"""
        try:
            # Cleanup old sync logs
            cutoff_date = datetime.utcnow() - timedelta(days=settings.OFFLINE_DATA_RETENTION_DAYS)
            
            with self.postgres_engine.connect() as conn:
                conn.execute(text("""
                    DELETE FROM sync_log 
                    WHERE sync_timestamp < :cutoff_date
                """), {"cutoff_date": cutoff_date})
                conn.commit()
                
        except Exception as e:
            logger.error(f"❌ Failed to cleanup sync data: {e}")
    
    async def force_sync(self):
        """Force an immediate sync"""
        logger.info("🔄 Force sync requested...")
        await self._sync_cycle()
    
    def get_conflicts(self) -> List[Dict[str, Any]]:
        """Get list of pending conflicts"""
        return [
            {
                "table_name": conflict.table_name,
                "record_id": conflict.record_id,
                "source_db": conflict.source_db,
                "timestamp": conflict.timestamp.isoformat(),
                "data": conflict.data,
                "conflict_data": conflict.conflict_data
            }
            for conflict in self.conflict_queue
        ]
    
    def resolve_conflict_manually(self, conflict_id: str, resolution: str):
        """Manually resolve a specific conflict"""
        # Implementation for manual conflict resolution
        pass
    
    def close(self):
        """Close database connections"""
        if self.postgres_session:
            self.postgres_session.close()
        if self.sqlite_session:
            self.sqlite_session.close()
        logger.info("🔒 Database connections closed")

# Global sync service instance
sync_service = DatabaseSyncService()
