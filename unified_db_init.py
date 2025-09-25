#!/usr/bin/env python3
"""
Unified database initialization for both PostgreSQL and SQLite
Ensures identical content and structure across both databases
"""

import os
import sys
from sqlalchemy import create_engine, text
from app.core.config import settings
from app.database.database import Base, get_engine, create_tables
from app.models import user, patient, appointment, medical_record, prescription, tenant
# Temporarily commented out audit to avoid circular dependencies
# from app.models import audit

def init_unified_database():
    """Initialize database with unified structure and content"""
    print("🚀 Initializing Unified Database...")
    print("=" * 50)
    
    # Set environment variables
    use_sqlite = os.getenv("USE_SQLITE", "false").lower() == "true"
    use_database = os.getenv("USE_DATABASE", "false").lower() == "true"
    
    if use_sqlite:
        print("📱 Using SQLite Database (Offline Mode)")
        database_type = "SQLite"
    else:
        print("🌐 Using PostgreSQL Database (Online Mode)")
        database_type = "PostgreSQL"
    
    try:
        # Create tables
        print(f"Creating tables in {database_type}...")
        create_tables()
        print("✅ Tables created successfully!")
        
        # Create default data
        print("Creating default data...")
        create_default_data()
        print("✅ Default data created successfully!")
        
        print("\n" + "=" * 50)
        print(f"🎉 {database_type} database initialization complete!")
        print("\nDefault credentials:")
        print("Admin: admin@prontivus.com / admin123")
        print("Doctor: doctor@prontivus.com / doctor123")
        print("Secretary: secretary@prontivus.com / secretary123")
        print("Patient: patient@prontivus.com / patient123")
        
        return True
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

def create_default_data():
    """Create default data for both databases"""
    from app.database.database import get_session_local
    from app.models.user import User, Role, UserRole
    from app.models.patient import Patient
    from app.models.appointment import Appointment
    from app.models.medical_record import MedicalRecord
    from app.models.prescription import Prescription
    from passlib.context import CryptContext
    from datetime import datetime
    
    # Password hashing
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    # Get database session
    SessionLocal = get_session_local()
    db = SessionLocal()
    
    try:
        # Create default roles first
        print("Creating default roles...")
        default_roles = [
            {
                "name": "admin",
                "description": "System Administrator",
                "permissions": ["*"]
            },
            {
                "name": "doctor", 
                "description": "Medical Doctor",
                "permissions": ["patients:read", "patients:update", "appointments:create", "appointments:read", "appointments:update", "medical_records:create", "medical_records:read", "medical_records:update", "prescriptions:create", "prescriptions:read", "prescriptions:update", "reports:read"]
            },
            {
                "name": "secretary",
                "description": "Secretary/Receptionist", 
                "permissions": ["patients:create", "patients:read", "patients:update", "appointments:create", "appointments:read", "appointments:update", "appointments:delete", "reports:read"]
            },
            {
                "name": "patient",
                "description": "Patient with limited access to own data",
                "permissions": ["own_data:read", "appointments:read", "prescriptions:read"]
            }
        ]
        
        created_roles = {}
        for role_data in default_roles:
            existing_role = db.query(Role).filter(Role.name == role_data["name"]).first()
            if not existing_role:
                role = Role(**role_data)
                db.add(role)
                db.flush()  # Get the ID
                created_roles[role_data["name"]] = role
                print(f"✅ Created role: {role_data['name']}")
            else:
                created_roles[role_data["name"]] = existing_role
                print(f"✅ Role already exists: {role_data['name']}")
        
        # Create default users
            users_data = [
                {
                    "email": "admin@prontivus.com",
                    "username": "admin",
                    "full_name": "System Administrator",
                    "hashed_password": pwd_context.hash("admin123"),
                    "is_active": True,
                    "is_verified": True,
                    "is_superuser": True,
                    "role": "admin"
                },
                {
                    "email": "doctor@prontivus.com",
                    "username": "doctor",
                    "full_name": "Dr. João Silva",
                    "hashed_password": pwd_context.hash("doctor123"),
                    "is_active": True,
                    "is_verified": True,
                    "is_superuser": False,
                    "crm": "12345",
                    "specialty": "Cardiologia",
                    "role": "doctor"
                },
                {
                    "email": "secretary@prontivus.com",
                    "username": "secretary",
                    "full_name": "Maria Santos",
                    "hashed_password": pwd_context.hash("secretary123"),
                    "is_active": True,
                    "is_verified": True,
                    "is_superuser": False,
                    "role": "secretary"
                },
            {
                "email": "patient@prontivus.com",
                "username": "patient",
                "full_name": "Ana Costa",
                "hashed_password": pwd_context.hash("patient123"),
                "is_active": True,
                "is_verified": True,
                "is_superuser": False,
                "cpf": "12345678901",
                "phone": "(11) 99999-9999",
                "role": "patient"
            }
        ]
        
        # Create users
        created_users = {}
        for user_data in users_data:
            # Remove role from user data before creating user
            user_role = user_data.pop("role")
            user = User(**user_data)
            db.add(user)
            db.flush()  # Get the ID
            created_users[user_role] = user
            print(f"✅ Created {user_role}: {user_data['email']}")
        
        # Assign roles to users
        print("Assigning roles to users...")
        role_assignments = [
            ("admin", "admin"),
            ("doctor", "doctor"), 
            ("secretary", "secretary"),
            ("patient", "patient")
        ]
        
        for user_role, role_name in role_assignments:
            if user_role in created_users and role_name in created_roles:
                user_role_assignment = UserRole(
                    user_id=created_users[user_role].id,
                    role_id=created_roles[role_name].id,
                    tenant_id=1,
                    created_at=datetime.now()
                )
                db.add(user_role_assignment)
                print(f"✅ Assigned {role_name} role to {user_role}")
        
        # Create default patient record
        patient_data = {
            "tenant_id": 1,
            "user_id": created_users["patient"].id,
            "full_name": "Ana Costa",
            "cpf": "12345678901",
            "birth_date": "1985-03-15",
            "gender": "F",
            "phone": "(11) 99999-9999",
            "address": "Rua das Flores, 123",
            "insurance_company": "Unimed",
            "insurance_number": "123456789"
        }
        
        patient = Patient(**patient_data)
        db.add(patient)
        db.flush()
        print("✅ Created patient record")
        
        # Create sample appointment
        appointment_data = {
            "patient_id": patient.id,
            "doctor_id": created_users["doctor"].id,
            "appointment_date": "2024-01-20",
            "appointment_time": "14:00",
            "type": "Consulta",
            "status": "scheduled",
            "notes": "Consulta de rotina"
        }
        
        appointment = Appointment(**appointment_data)
        db.add(appointment)
        print("✅ Created sample appointment")
        
        # Create sample medical record
        medical_record_data = {
            "patient_id": patient.id,
            "doctor_id": created_users["doctor"].id,
            "date": "2024-01-20",
            "type": "Consulta",
            "diagnosis": "Hipertensão arterial",
            "treatment": "Controle da pressão arterial",
            "notes": "Paciente apresentou melhora significativa"
        }
        
        medical_record = MedicalRecord(**medical_record_data)
        db.add(medical_record)
        print("✅ Created sample medical record")
        
        # Create sample prescription
        prescription_data = {
            "patient_id": patient.id,
            "doctor_id": created_users["doctor"].id,
            "issued_date": "2024-01-20",
            "medications": [
                {
                    "name": "Paracetamol",
                    "dosage": "500mg",
                    "frequency": "3x ao dia",
                    "duration": "7 dias"
                }
            ],
            "notes": "Tomar com alimentos",
            "status": "active"
        }
        
        prescription = Prescription(**prescription_data)
        db.add(prescription)
        print("✅ Created sample prescription")
        
        # Commit all changes
        db.commit()
        print("✅ All data committed successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating default data: {e}")
        raise
    finally:
        db.close()

def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("Usage: python unified_db_init.py")
        print("Environment variables:")
        print("  USE_SQLITE=true/false - Use SQLite (true) or PostgreSQL (false)")
        print("  USE_DATABASE=true/false - Use real database (true) or mock (false)")
        return
    
    success = init_unified_database()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
