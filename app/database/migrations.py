"""
Enhanced database migration utilities for Prontivus
Supports both PostgreSQL and SQLite with rollback capabilities
"""

from sqlalchemy import create_engine, text, MetaData, Table, Column, Integer, String, DateTime, Text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import logging
from typing import List, Dict, Any, Optional
import os
import json
import hashlib
from datetime import datetime
from pathlib import Path
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MigrationStatus(Enum):
    """Migration status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"

class MigrationType(Enum):
    """Migration type"""
    CREATE_TABLE = "create_table"
    ALTER_TABLE = "alter_table"
    DROP_TABLE = "drop_table"
    CREATE_INDEX = "create_index"
    DROP_INDEX = "drop_index"
    INSERT_DATA = "insert_data"
    UPDATE_DATA = "update_data"
    DELETE_DATA = "delete_data"

class Migration:
    """Represents a database migration"""
    
    def __init__(self, version: str, name: str, migration_type: MigrationType, 
                 up_sql: str, down_sql: str = None, description: str = ""):
        self.version = version
        self.name = name
        self.migration_type = migration_type
        self.up_sql = up_sql
        self.down_sql = down_sql
        self.description = description
        self.status = MigrationStatus.PENDING
        self.created_at = datetime.utcnow()
        self.executed_at = None
        self.checksum = self._calculate_checksum()
    
    def _calculate_checksum(self) -> str:
        """Calculate checksum for migration integrity"""
        content = f"{self.version}{self.name}{self.up_sql}{self.down_sql or ''}"
        return hashlib.md5(content.encode()).hexdigest()

class DatabaseMigrator:
    """Handles database migrations and schema updates"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.migrations_dir = Path("migrations")
        self.migrations_dir.mkdir(exist_ok=True)
        
        # Initialize migration tracking table
        self._init_migration_table()
    
    def _init_migration_table(self):
        """Initialize migration tracking table"""
        try:
            with self.engine.connect() as conn:
                # Create migration tracking table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS schema_migrations (
                        id SERIAL PRIMARY KEY,
                        version VARCHAR(255) UNIQUE NOT NULL,
                        name VARCHAR(255) NOT NULL,
                        migration_type VARCHAR(50) NOT NULL,
                        up_sql TEXT NOT NULL,
                        down_sql TEXT,
                        description TEXT,
                        status VARCHAR(50) DEFAULT 'pending',
                        checksum VARCHAR(32) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        executed_at TIMESTAMP,
                        error_message TEXT
                    )
                """))
                conn.commit()
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize migration table: {e}")
    
    def create_migration(self, name: str, migration_type: MigrationType, 
                        up_sql: str, down_sql: str = None, description: str = "") -> Migration:
        """Create a new migration"""
        version = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        migration = Migration(version, name, migration_type, up_sql, down_sql, description)
        
        # Save migration to file
        self._save_migration_file(migration)
        
        # Save to database
        self._save_migration_to_db(migration)
        
        logger.info(f"✅ Created migration: {version}_{name}")
        return migration
    
    def _save_migration_file(self, migration: Migration):
        """Save migration to file"""
        try:
            migration_data = {
                "version": migration.version,
                "name": migration.name,
                "migration_type": migration.migration_type.value,
                "up_sql": migration.up_sql,
                "down_sql": migration.down_sql,
                "description": migration.description,
                "checksum": migration.checksum,
                "created_at": migration.created_at.isoformat()
            }
            
            filename = f"{migration.version}_{migration.name}.json"
            filepath = self.migrations_dir / filename
            
            with open(filepath, 'w') as f:
                json.dump(migration_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"❌ Failed to save migration file: {e}")
    
    def _save_migration_to_db(self, migration: Migration):
        """Save migration to database"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("""
                    INSERT INTO schema_migrations 
                    (version, name, migration_type, up_sql, down_sql, description, checksum)
                    VALUES (:version, :name, :migration_type, :up_sql, :down_sql, :description, :checksum)
                """), {
                    "version": migration.version,
                    "name": migration.name,
                    "migration_type": migration.migration_type.value,
                    "up_sql": migration.up_sql,
                    "down_sql": migration.down_sql,
                    "description": migration.description,
                    "checksum": migration.checksum
                })
                conn.commit()
                
        except Exception as e:
            logger.error(f"❌ Failed to save migration to database: {e}")
    
    def run_migration(self, migration: Migration) -> bool:
        """Run a specific migration"""
        try:
            logger.info(f"🔄 Running migration: {migration.version}_{migration.name}")
            
            # Update status to running
            self._update_migration_status(migration, MigrationStatus.RUNNING)
            
            # Execute migration SQL
            with self.engine.connect() as conn:
                # Handle different migration types
                if migration.migration_type == MigrationType.CREATE_TABLE:
                    conn.execute(text(migration.up_sql))
                elif migration.migration_type == MigrationType.ALTER_TABLE:
                    conn.execute(text(migration.up_sql))
                elif migration.migration_type == MigrationType.CREATE_INDEX:
                    conn.execute(text(migration.up_sql))
                elif migration.migration_type == MigrationType.INSERT_DATA:
                    conn.execute(text(migration.up_sql))
                else:
                    conn.execute(text(migration.up_sql))
                
                conn.commit()
            
            # Update status to completed
            self._update_migration_status(migration, MigrationStatus.COMPLETED)
            migration.executed_at = datetime.utcnow()
            
            logger.info(f"✅ Migration completed: {migration.version}_{migration.name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {migration.version}_{migration.name} - {e}")
            self._update_migration_status(migration, MigrationStatus.FAILED, str(e))
            return False
    
    def rollback_migration(self, migration: Migration) -> bool:
        """Rollback a specific migration"""
        try:
            if not migration.down_sql:
                logger.warning(f"⚠️ No rollback SQL for migration: {migration.version}_{migration.name}")
                return False
            
            logger.info(f"🔄 Rolling back migration: {migration.version}_{migration.name}")
            
            # Update status to running
            self._update_migration_status(migration, MigrationStatus.RUNNING)
            
            # Execute rollback SQL
            with self.engine.connect() as conn:
                conn.execute(text(migration.down_sql))
                conn.commit()
            
            # Update status to rolled back
            self._update_migration_status(migration, MigrationStatus.ROLLED_BACK)
            
            logger.info(f"✅ Migration rolled back: {migration.version}_{migration.name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Rollback failed: {migration.version}_{migration.name} - {e}")
            self._update_migration_status(migration, MigrationStatus.FAILED, str(e))
            return False
    
    def _update_migration_status(self, migration: Migration, status: MigrationStatus, error_message: str = None):
        """Update migration status in database"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("""
                    UPDATE schema_migrations 
                    SET status = :status, executed_at = :executed_at, error_message = :error_message
                    WHERE version = :version
                """), {
                    "status": status.value,
                    "executed_at": datetime.utcnow() if status == MigrationStatus.COMPLETED else None,
                    "error_message": error_message,
                    "version": migration.version
                })
                conn.commit()
                
        except Exception as e:
            logger.error(f"❌ Failed to update migration status: {e}")
    
    def get_pending_migrations(self) -> List[Migration]:
        """Get list of pending migrations"""
        try:
            with self.engine.connect() as conn:
                results = conn.execute(text("""
                    SELECT version, name, migration_type, up_sql, down_sql, description, checksum
                    FROM schema_migrations
                    WHERE status = 'pending'
                    ORDER BY version
                """)).fetchall()
                
                migrations = []
                for row in results:
                    migration = Migration(
                        version=row[0],
                        name=row[1],
                        migration_type=MigrationType(row[2]),
                        up_sql=row[3],
                        down_sql=row[4],
                        description=row[5] or ""
                    )
                    migration.checksum = row[6]
                    migrations.append(migration)
                
                return migrations
                
        except Exception as e:
            logger.error(f"❌ Failed to get pending migrations: {e}")
            return []
    
    def get_migration_history(self) -> List[Dict[str, Any]]:
        """Get migration history"""
        try:
            with self.engine.connect() as conn:
                results = conn.execute(text("""
                    SELECT version, name, migration_type, status, created_at, executed_at, error_message
                    FROM schema_migrations
                    ORDER BY version DESC
                """)).fetchall()
                
                return [
                    {
                        "version": row[0],
                        "name": row[1],
                        "migration_type": row[2],
                        "status": row[3],
                        "created_at": row[4],
                        "executed_at": row[5],
                        "error_message": row[6]
                    }
                    for row in results
                ]
                
        except Exception as e:
            logger.error(f"❌ Failed to get migration history: {e}")
            return []
    
    def run_all_pending_migrations(self) -> bool:
        """Run all pending migrations"""
        try:
            pending_migrations = self.get_pending_migrations()
            
            if not pending_migrations:
                logger.info("✅ No pending migrations")
                return True
            
            logger.info(f"🔄 Running {len(pending_migrations)} pending migrations...")
            
            for migration in pending_migrations:
                if not self.run_migration(migration):
                    logger.error(f"❌ Failed to run migration: {migration.version}_{migration.name}")
                    return False
            
            logger.info("✅ All migrations completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to run pending migrations: {e}")
            return False
    
    def create_all_tables(self):
        """Create all tables in the database"""
        try:
            from app.models.base import Base
            from app.models.user import User, Role, UserRole, TwoFactorToken, PasswordResetToken
            from app.models.patient import Patient
            from app.models.tenant import Tenant, TenantInvitation, TenantSubscription
            from app.models.appointment import Appointment, AppointmentReminder
            from app.models.medical_record import MedicalRecord, MedicalRecordAttachment, VitalSigns
            from app.models.prescription import Prescription, PrescriptionItem, DrugInteraction, PatientAllergy
            from app.models.audit import AuditLog, AuditLogArchive, SecurityEvent, DataAccessLog
            
            Base.metadata.create_all(bind=self.engine)
            logger.info("All tables created successfully")
            return True
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            return False
    
    def drop_all_tables(self):
        """Drop all tables (use with caution!)"""
        try:
            from app.models.base import Base
            Base.metadata.drop_all(bind=self.engine)
            logger.info("All tables dropped successfully")
            return True
        except Exception as e:
            logger.error(f"Error dropping tables: {e}")
            return False
    
    def create_indexes(self):
        """Create additional indexes for performance"""
        indexes = [
            # User indexes
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
            "CREATE INDEX IF NOT EXISTS idx_users_cpf ON users(cpf)",
            "CREATE INDEX IF NOT EXISTS idx_users_tenant ON users(tenant_id)",
            "CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active)",
            
            # Patient indexes
            "CREATE INDEX IF NOT EXISTS idx_patients_tenant ON patients(tenant_id)",
            "CREATE INDEX IF NOT EXISTS idx_patients_user ON patients(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_patients_cpf ON patients(cpf)",
            
            # Appointment indexes
            "CREATE INDEX IF NOT EXISTS idx_appointments_tenant ON appointments(tenant_id)",
            "CREATE INDEX IF NOT EXISTS idx_appointments_patient ON appointments(patient_id)",
            "CREATE INDEX IF NOT EXISTS idx_appointments_doctor ON appointments(doctor_id)",
            "CREATE INDEX IF NOT EXISTS idx_appointments_date ON appointments(appointment_date)",
            "CREATE INDEX IF NOT EXISTS idx_appointments_status ON appointments(status)",
            
            # Medical record indexes
            "CREATE INDEX IF NOT EXISTS idx_medical_records_tenant ON medical_records(tenant_id)",
            "CREATE INDEX IF NOT EXISTS idx_medical_records_patient ON medical_records(patient_id)",
            "CREATE INDEX IF NOT EXISTS idx_medical_records_doctor ON medical_records(doctor_id)",
            "CREATE INDEX IF NOT EXISTS idx_medical_records_number ON medical_records(record_number)",
            "CREATE INDEX IF NOT EXISTS idx_medical_records_status ON medical_records(status)",
            
            # Prescription indexes
            "CREATE INDEX IF NOT EXISTS idx_prescriptions_tenant ON prescriptions(tenant_id)",
            "CREATE INDEX IF NOT EXISTS idx_prescriptions_patient ON prescriptions(patient_id)",
            "CREATE INDEX IF NOT EXISTS idx_prescriptions_doctor ON prescriptions(doctor_id)",
            "CREATE INDEX IF NOT EXISTS idx_prescriptions_number ON prescriptions(prescription_number)",
            "CREATE INDEX IF NOT EXISTS idx_prescriptions_status ON prescriptions(status)",
            
            # Audit log indexes
            "CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_audit_logs_tenant ON audit_logs(tenant_id)",
            "CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action)",
            "CREATE INDEX IF NOT EXISTS idx_audit_logs_entity ON audit_logs(entity_type)",
            "CREATE INDEX IF NOT EXISTS idx_audit_logs_created ON audit_logs(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_audit_logs_ip ON audit_logs(ip_address)",
            
            # Security event indexes
            "CREATE INDEX IF NOT EXISTS idx_security_events_type ON security_events(event_type)",
            "CREATE INDEX IF NOT EXISTS idx_security_events_severity ON security_events(severity)",
            "CREATE INDEX IF NOT EXISTS idx_security_events_detected ON security_events(detected_at)",
            
            # Data access log indexes
            "CREATE INDEX IF NOT EXISTS idx_data_access_user ON data_access_logs(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_data_access_patient ON data_access_logs(patient_id)",
            "CREATE INDEX IF NOT EXISTS idx_data_access_type ON data_access_logs(data_type)",
            "CREATE INDEX IF NOT EXISTS idx_data_access_accessed ON data_access_logs(accessed_at)",
        ]
        
        try:
            with self.engine.connect() as conn:
                for index_sql in indexes:
                    conn.execute(text(index_sql))
                conn.commit()
            logger.info("All indexes created successfully")
            return True
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")
            return False
    
    def seed_initial_data(self):
        """Seed the database with initial data"""
        try:
            db = self.SessionLocal()
            
            # Create default roles
            from app.models.user import Role
            
            default_roles = [
                {
                    "name": "super_admin",
                    "description": "Super Administrator with full system access",
                    "permissions": ["*"]
                },
                {
                    "name": "admin",
                    "description": "Administrator with full tenant access",
                    "permissions": [
                        "users:create", "users:read", "users:update", "users:delete",
                        "patients:create", "patients:read", "patients:update", "patients:delete",
                        "appointments:create", "appointments:read", "appointments:update", "appointments:delete",
                        "medical_records:create", "medical_records:read", "medical_records:update", "medical_records:delete",
                        "prescriptions:create", "prescriptions:read", "prescriptions:update", "prescriptions:delete",
                        "reports:read", "settings:read", "settings:update"
                    ]
                },
                {
                    "name": "doctor",
                    "description": "Medical doctor with patient care access",
                    "permissions": [
                        "patients:read", "patients:update",
                        "appointments:create", "appointments:read", "appointments:update",
                        "medical_records:create", "medical_records:read", "medical_records:update",
                        "prescriptions:create", "prescriptions:read", "prescriptions:update",
                        "reports:read"
                    ]
                },
                {
                    "name": "secretary",
                    "description": "Secretary with scheduling and patient management access",
                    "permissions": [
                        "patients:create", "patients:read", "patients:update",
                        "appointments:create", "appointments:read", "appointments:update", "appointments:delete",
                        "reports:read"
                    ]
                },
                {
                    "name": "finance",
                    "description": "Finance staff with billing and payment access",
                    "permissions": [
                        "patients:read",
                        "appointments:read",
                        "prescriptions:read",
                        "reports:read",
                        "billing:create", "billing:read", "billing:update"
                    ]
                },
                {
                    "name": "patient",
                    "description": "Patient with limited access to own data",
                    "permissions": [
                        "own_data:read",
                        "appointments:read",
                        "prescriptions:read"
                    ]
                }
            ]
            
            for role_data in default_roles:
                existing_role = db.query(Role).filter(Role.name == role_data["name"]).first()
                if not existing_role:
                    role = Role(**role_data)
                    db.add(role)
            
            db.commit()
            logger.info("Initial data seeded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error seeding initial data: {e}")
            db.rollback()
            return False
        finally:
            db.close()
    
    def backup_database(self, backup_path: str):
        """Create a database backup"""
        try:
            # This is a simplified backup - in production, use pg_dump
            logger.info(f"Creating database backup at {backup_path}")
            # Implementation would depend on the database type
            return True
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return False
    
    def restore_database(self, backup_path: str):
        """Restore database from backup"""
        try:
            logger.info(f"Restoring database from {backup_path}")
            # Implementation would depend on the database type
            return True
        except Exception as e:
            logger.error(f"Error restoring database: {e}")
            return False
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get database information and statistics"""
        try:
            db = self.SessionLocal()
            
            # Get table counts
            table_counts = {}
            tables = [
                "users", "patients", "appointments", "medical_records", 
                "prescriptions", "audit_logs", "tenants"
            ]
            
            for table in tables:
                try:
                    result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    table_counts[table] = count
                except:
                    table_counts[table] = 0
            
            # Get database size
            try:
                result = db.execute(text("SELECT pg_size_pretty(pg_database_size(current_database()))"))
                db_size = result.scalar()
            except:
                db_size = "Unknown"
            
            db.close()
            
            return {
                "table_counts": table_counts,
                "database_size": db_size,
                "migration_date": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting database info: {e}")
            return {}

def run_migration(database_url: str):
    """Run complete database migration"""
    migrator = DatabaseMigrator(database_url)
    
    logger.info("Starting database migration...")
    
    # Create all tables
    if not migrator.create_all_tables():
        logger.error("Failed to create tables")
        return False
    
    # Create indexes
    if not migrator.create_indexes():
        logger.error("Failed to create indexes")
        return False
    
    # Seed initial data
    if not migrator.seed_initial_data():
        logger.error("Failed to seed initial data")
        return False
    
    # Get database info
    info = migrator.get_database_info()
    logger.info(f"Migration completed successfully. Database info: {info}")
    
    return True

if __name__ == "__main__":
    # Example usage
    database_url = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/clinicore")
    run_migration(database_url)
