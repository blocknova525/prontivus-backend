# Prontivus Dual Database Setup Guide

## Quick Start

### 1. Environment Setup

Create a `.env` file in the backend directory:

```bash
# Database Configuration
USE_SQLITE=true
USE_DATABASE=true

# PostgreSQL (for production/online mode)
DATABASE_URL=postgresql://clinicore_user:clinicore_password@localhost/clinicore
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=clinicore
POSTGRES_USER=clinicore_user
POSTGRES_PASSWORD=clinicore_password
POSTGRES_SSL_MODE=prefer

# SQLite (for offline mode)
SQLITE_URL=sqlite:///./clinicore_offline.db

# Sync Configuration
SYNC_ENABLED=true
SYNC_INTERVAL_SECONDS=300
SYNC_CONFLICT_RESOLUTION=postgresql_wins
SYNC_RETRY_ATTEMPTS=3

# Offline Configuration
OFFLINE_MODE_ENABLED=true
OFFLINE_DATA_RETENTION_DAYS=30
OFFLINE_SYNC_ON_STARTUP=true
```

### 2. Install Dependencies

```bash
# Install additional dependencies for monitoring
pip install psutil

# Install all requirements
pip install -r requirements.txt
```

### 3. Initialize Databases

#### Option A: SQLite Only (Offline Mode)
```bash
# Set environment for SQLite
export USE_SQLITE=true
export USE_DATABASE=true

# Initialize SQLite database
python simple_init_db.py
```

#### Option B: PostgreSQL Only (Online Mode)
```bash
# Set environment for PostgreSQL
export USE_SQLITE=false
export USE_DATABASE=true

# Initialize PostgreSQL database
python init_postgresql_db.py
```

#### Option C: Both Databases (Hybrid Mode)
```bash
# Initialize both databases
python unified_db_init.py
```

### 4. Start the Application

```bash
# Start with database integration
python main.py
```

## Verification

### Check Database Status
```bash
# Check overall status
curl http://localhost:8000/startup

# Check database health
curl http://localhost:8000/api/v1/database/health

# Check sync status
curl http://localhost:8000/api/v1/database/sync/status
```

### Check API Documentation
Visit `http://localhost:8000/docs` to see all available endpoints.

## Configuration Options

### Sync Strategies

#### PostgreSQL Wins (Recommended for Production)
```bash
SYNC_CONFLICT_RESOLUTION=postgresql_wins
```
- PostgreSQL data takes precedence in conflicts
- Best for production environments
- Ensures data consistency across multiple clients

#### SQLite Wins (Recommended for Offline-First)
```bash
SYNC_CONFLICT_RESOLUTION=sqlite_wins
```
- SQLite data takes precedence in conflicts
- Best for offline-first scenarios
- Prioritizes local changes

#### Newest Wins (Time-Based)
```bash
SYNC_CONFLICT_RESOLUTION=newest_wins
```
- Most recent timestamp wins
- Good for distributed scenarios
- Requires accurate system clocks

#### Manual Resolution
```bash
SYNC_CONFLICT_RESOLUTION=manual
```
- Conflicts require manual intervention
- Best for critical data
- Provides full control over resolution

### Performance Tuning

#### Connection Pool Settings
```bash
# PostgreSQL connection pool
DB_POOL_SIZE=20              # Base pool size
DB_MAX_OVERFLOW=30           # Additional connections
DB_POOL_TIMEOUT=30           # Connection timeout (seconds)
DB_POOL_RECYCLE=3600         # Connection recycle time (seconds)
```

#### Sync Settings
```bash
SYNC_INTERVAL_SECONDS=300    # Sync frequency (5 minutes)
SYNC_BATCH_SIZE=1000        # Records per batch
SYNC_RETRY_ATTEMPTS=3       # Retry attempts
SYNC_RETRY_DELAY=5          # Delay between retries (seconds)
```

## Monitoring

### Start Monitoring
```bash
# Start database monitoring
curl -X POST http://localhost:8000/api/v1/database/monitoring/start

# Check monitoring status
curl http://localhost:8000/api/v1/database/monitoring/status
```

### View Metrics
```bash
# Get current metrics
curl http://localhost:8000/api/v1/database/metrics

# Get health status
curl http://localhost:8000/api/v1/database/health

# Force health check
curl -X POST http://localhost:8000/api/v1/database/monitoring/health-check
```

## Troubleshooting

### Common Issues

#### 1. Database Connection Failed
```bash
# Check connection status
curl http://localhost:8000/api/v1/database/connection/status

# Test database connection
python -c "from app.database.database import test_connection; print('Connected' if test_connection() else 'Failed')"
```

#### 2. Sync Not Working
```bash
# Check sync status
curl http://localhost:8000/api/v1/database/sync/status

# Force sync
curl -X POST http://localhost:8000/api/v1/database/sync/force

# Check conflicts
curl http://localhost:8000/api/v1/database/sync/conflicts
```

#### 3. Performance Issues
```bash
# Check metrics
curl http://localhost:8000/api/v1/database/metrics

# Check health
curl http://localhost:8000/api/v1/database/health
```

### Debug Mode
```bash
# Enable debug logging
export DEBUG=true
export LOG_LEVEL=DEBUG

# Start with verbose output
python main.py --log-level debug
```

## Migration Management

### Create Migration
```bash
# Create a new migration
curl -X POST http://localhost:8000/api/v1/database/migrations/create \
  -H "Content-Type: application/json" \
  -d '{
    "name": "add_new_table",
    "migration_type": "create_table",
    "up_sql": "CREATE TABLE new_table (id SERIAL PRIMARY KEY, name VARCHAR(255))",
    "down_sql": "DROP TABLE new_table",
    "description": "Add new table for testing"
  }'
```

### Run Migrations
```bash
# Check pending migrations
curl http://localhost:8000/api/v1/database/migrations/pending

# Run all pending migrations
curl -X POST http://localhost:8000/api/v1/database/migrations/run
```

### View Migration History
```bash
# Get migration history
curl http://localhost:8000/api/v1/database/migrations/history
```

## Production Deployment

### Environment Variables
```bash
# Production settings
ENVIRONMENT=production
DEBUG=false
USE_SQLITE=false
USE_DATABASE=true

# PostgreSQL production URL
DATABASE_URL=postgresql://user:password@production-host/clinicore

# Security
SECRET_KEY=your-production-secret-key
POSTGRES_SSL_MODE=require

# Performance
DB_POOL_SIZE=50
DB_MAX_OVERFLOW=100
SYNC_INTERVAL_SECONDS=60
```

### Docker Deployment
```dockerfile
# Dockerfile example
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "main.py"]
```

### Kubernetes Deployment
```yaml
# kubernetes-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: clinicore-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: clinicore-backend
  template:
    metadata:
      labels:
        app: clinicore-backend
    spec:
      containers:
      - name: clinicore-backend
        image: clinicore-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: clinicore-secrets
              key: database-url
```

## Support

For additional support:
- Check the main documentation: `DATABASE_ARCHITECTURE.md`
- Review API documentation: `http://localhost:8000/docs`
- Check logs for detailed error messages
- Use the health check endpoints for diagnostics
