# Prontivus Database Schema Documentation

## Overview

Prontivus implements a comprehensive database schema designed for healthcare management with full compliance to Brazilian LGPD (Lei Geral de Proteção de Dados) regulations. The system supports multi-tenancy, comprehensive audit logging, and advanced security features.

## Database Architecture

### Technology Stack
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy
- **Migration Tool**: Custom migration system
- **Backup**: Automated backup with retention policies

### Core Principles
1. **Multi-tenancy**: Complete data isolation between healthcare facilities
2. **LGPD Compliance**: Full data protection and privacy compliance
3. **Audit Logging**: Comprehensive tracking of all system activities
4. **Security**: Advanced security features and encryption
5. **Scalability**: Designed for high-volume healthcare operations

## Database Models

### 1. User Management & Authentication

#### Users (`users`)
- **Purpose**: Central user management for all system users
- **Key Features**:
  - Multi-tenant support (`tenant_id`)
  - CPF support for Brazilian patients
  - CRM support for doctors
  - 2FA support (TOTP, Email, SMS)
  - Account lockout protection
  - Password reset functionality
  - LGPD consent tracking

#### Roles (`roles`)
- **Purpose**: Role-based access control (RBAC)
- **Default Roles**:
  - `super_admin`: Full system access
  - `admin`: Full tenant access
  - `doctor`: Medical care access
  - `secretary`: Scheduling and patient management
  - `finance`: Billing and payment access
  - `patient`: Limited access to own data

#### User Roles (`user_roles`)
- **Purpose**: Many-to-many relationship between users and roles
- **Features**: Tenant-specific role assignments

#### Two-Factor Authentication (`two_factor_tokens`)
- **Purpose**: 2FA token management
- **Features**: Support for email and SMS verification

#### Password Reset (`password_reset_tokens`)
- **Purpose**: Secure password reset functionality
- **Features**: Time-limited tokens with usage tracking

### 2. Multi-Tenancy

#### Tenants (`tenants`)
- **Purpose**: Healthcare facility management
- **Key Features**:
  - Complete facility information (CNPJ, CNES, licenses)
  - Subscription management
  - Feature flags and limits
  - LGPD compliance tracking
  - Custom branding and settings

#### Tenant Invitations (`tenant_invitations`)
- **Purpose**: Secure user invitation system
- **Features**: Role-based invitations with expiration

#### Tenant Subscriptions (`tenant_subscriptions`)
- **Purpose**: Subscription history and management
- **Features**: Usage tracking and billing integration

### 3. Patient Management

#### Patients (`patients`)
- **Purpose**: Patient information management
- **Key Features**:
  - Complete demographic information
  - Insurance information
  - Emergency contacts
  - LGPD consent tracking
  - Data retention policies

#### Patient Allergies (`patient_allergies`)
- **Purpose**: Comprehensive allergy tracking
- **Features**: Drug interaction prevention

### 4. Medical Records

#### Medical Records (`medical_records`)
- **Purpose**: Electronic Health Records (EHR)
- **Key Features**:
  - Complete medical history
  - ICD-10 diagnosis coding
  - Digital signatures
  - Review and approval workflow
  - LGPD compliance

#### Medical Record Attachments (`medical_record_attachments`)
- **Purpose**: File attachments for medical records
- **Features**: Encrypted storage with access logging

#### Vital Signs (`vital_signs`)
- **Purpose**: Patient vital signs tracking
- **Features**: Historical tracking with context

### 5. Appointments

#### Appointments (`appointments`)
- **Purpose**: Appointment scheduling and management
- **Key Features**:
  - Multi-status workflow
  - Telemedicine support
  - Reminder system
  - Cancellation tracking
  - LGPD compliance

#### Appointment Reminders (`appointment_reminders`)
- **Purpose**: Automated reminder system
- **Features**: Multi-channel reminders (email, SMS, push)

### 6. Prescriptions

#### Prescriptions (`prescriptions`)
- **Purpose**: Digital prescription management
- **Key Features**:
  - Digital signatures
  - Refill management
  - Pharmacy integration
  - LGPD compliance

#### Prescription Items (`prescription_items`)
- **Purpose**: Individual medication/procedure items
- **Features**: Detailed dosage information

#### Drug Interactions (`drug_interactions`)
- **Purpose**: Drug interaction database
- **Features**: Severity levels and management guidelines

### 7. Audit & Security

#### Audit Logs (`audit_logs`)
- **Purpose**: Comprehensive activity logging
- **Key Features**:
  - All user actions tracked
  - Risk assessment
  - LGPD/HIPAA compliance
  - IP and session tracking

#### Security Events (`security_events`)
- **Purpose**: Security incident tracking
- **Features**: Automated threat detection and response

#### Data Access Logs (`data_access_logs`)
- **Purpose**: LGPD-compliant data access tracking
- **Features**: Purpose and legal basis tracking

#### Audit Log Archives (`audit_log_archives`)
- **Purpose**: Long-term audit log storage
- **Features**: Compressed storage with retention policies

## Security Features

### 1. Data Encryption
- **At Rest**: AES-256 encryption for sensitive fields
- **In Transit**: TLS 1.3 enforced
- **Key Management**: Secure key rotation and storage

### 2. Access Control
- **RBAC**: Role-based access control
- **Multi-tenant**: Complete data isolation
- **Session Management**: Secure session handling
- **API Security**: JWT with refresh tokens

### 3. Audit & Compliance
- **Comprehensive Logging**: All actions logged
- **Risk Assessment**: Automated risk scoring
- **Compliance**: LGPD and HIPAA ready
- **Data Retention**: Automated retention policies

### 4. Authentication Security
- **2FA Support**: TOTP, Email, SMS
- **Account Lockout**: Brute force protection
- **Password Policy**: Strong password requirements
- **Session Timeout**: Automatic session expiration

## LGPD Compliance Features

### 1. Data Protection
- **Consent Management**: Explicit consent tracking
- **Data Minimization**: Only necessary data collected
- **Purpose Limitation**: Clear purpose statements
- **Storage Limitation**: Automated data retention

### 2. User Rights
- **Access Rights**: Data portability
- **Rectification**: Data correction
- **Erasure**: Right to be forgotten
- **Restriction**: Processing limitation

### 3. Data Processing
- **Lawful Basis**: Clear legal basis tracking
- **Transparency**: Clear privacy notices
- **Accountability**: Comprehensive audit trails
- **Security**: Technical and organizational measures

## Database Indexes

### Performance Indexes
- **User Lookups**: Email, CPF, tenant
- **Patient Searches**: Name, CPF, tenant
- **Appointment Queries**: Date, status, patient, doctor
- **Medical Records**: Patient, doctor, status, date
- **Audit Logs**: User, action, date, IP

### Security Indexes
- **Failed Logins**: IP, user, timestamp
- **Security Events**: Type, severity, date
- **Data Access**: User, patient, data type

## Migration System

### Features
- **Automated Setup**: Complete database initialization
- **Index Creation**: Performance optimization
- **Data Seeding**: Default roles and configurations
- **Backup/Restore**: Data protection
- **Version Control**: Schema versioning

### Usage
```python
from app.database.migrations import run_migration

# Run complete migration
run_migration("postgresql://user:password@localhost/clinicore")
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/register/staff` - Staff registration
- `POST /api/v1/auth/register/patient` - Patient registration
- `POST /api/v1/auth/forgot-password` - Password reset
- `POST /api/v1/auth/setup-2fa` - 2FA setup
- `POST /api/v1/auth/verify-2fa` - 2FA verification

### Patient Management
- `GET /api/v1/patients` - List patients
- `GET /api/v1/patients/{id}` - Patient details
- `POST /api/v1/patients` - Create patient
- `PUT /api/v1/patients/{id}` - Update patient

### Medical Records
- `GET /api/v1/medical-records` - List records
- `GET /api/v1/medical-records/{id}` - Record details
- `POST /api/v1/medical-records` - Create record
- `POST /api/v1/medical-records/{id}/sign` - Sign record

### Appointments
- `GET /api/v1/appointments` - List appointments
- `GET /api/v1/appointments/{id}` - Appointment details
- `POST /api/v1/appointments` - Create appointment
- `PUT /api/v1/appointments/{id}` - Update appointment

### Prescriptions
- `GET /api/v1/prescriptions` - List prescriptions
- `GET /api/v1/prescriptions/{id}` - Prescription details
- `POST /api/v1/prescriptions` - Create prescription
- `POST /api/v1/prescriptions/{id}/dispense` - Dispense prescription

### Financial
- `GET /api/v1/financial/transactions` - Financial transactions
- `GET /api/v1/financial/reports` - Financial reports

### Audit & Security
- `GET /api/v1/audit-logs` - Audit logs
- `GET /api/v1/security-events` - Security events

### Tenant Management
- `GET /api/v1/tenants` - List tenants
- `GET /api/v1/tenants/{id}` - Tenant details

## Development Setup

### Offline Development
The system includes a comprehensive offline development setup with mock endpoints:

```bash
# Start offline backend
cd backend
python simple_main.py

# Start frontend
cd frontend
npm run dev
```

### Production Setup
```bash
# Run database migration
python -m app.database.migrations

# Start production server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Best Practices

### 1. Data Security
- Always use parameterized queries
- Encrypt sensitive data at rest
- Implement proper access controls
- Regular security audits

### 2. Performance
- Use appropriate indexes
- Implement query optimization
- Monitor database performance
- Regular maintenance tasks

### 3. Compliance
- Maintain audit logs
- Implement data retention policies
- Regular compliance reviews
- User consent management

### 4. Backup & Recovery
- Regular automated backups
- Test restore procedures
- Disaster recovery planning
- Data integrity checks

## Conclusion

The Prontivus database schema provides a comprehensive, secure, and compliant foundation for healthcare management. With its multi-tenant architecture, comprehensive audit logging, and LGPD compliance features, it meets the highest standards for healthcare data management while providing the flexibility needed for various healthcare facility types.

The system is designed to scale from small private practices to large hospital networks while maintaining data security, privacy compliance, and operational efficiency.
