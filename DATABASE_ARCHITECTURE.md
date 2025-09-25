# Prontivus Dual Database Architecture

## Overview

Prontivus implements a sophisticated dual database architecture that combines **PostgreSQL** (production/cloud) and **SQLite** (offline/local) to provide both scalability and offline functionality. This architecture ensures high availability, data integrity, and seamless user experience across different deployment scenarios.

## Architecture Components

### 🐘 PostgreSQL (Production Database)
- **Purpose**: Primary database for production environments and cloud deployments
- **Use Cases**: 
  - Multi-clinic SaaS platforms
  - Cloud-hosted applications
  - High-concurrency scenarios
  - Production environments
- **Features**:
  - ACID compliance for medical data integrity
  - Advanced indexing and query optimization
  - JSON support for flexible data structures
  - Full-text search capabilities
  - Horizontal scaling with read replicas
  - Cloud integration (AWS RDS, GCP Cloud SQL)

### 📱 SQLite (Offline Database)
- **Purpose**: Local database for offline scenarios and mobile applications
- **Use Cases**:
  - Mobile applications (React Native)
  - Desktop installations
  - Offline-first scenarios
  - Development and testing
- **Features**:
  - File-based, no server required
  - Zero configuration
  - Fast read/write operations
  - Cross-platform compatibility
  - Lightweight and embedded

## Key Services

### 1. Database Sync Service (`sync_service.py`)
Handles bidirectional synchronization between PostgreSQL and SQLite.

**Features**:
- **Automatic Sync**: Background synchronization every 5 minutes
- **Conflict Resolution**: Multiple strategies (PostgreSQL wins, SQLite wins, newest wins, manual)
- **Data Integrity**: Checksums and validation
- **Retry Logic**: Automatic retry with exponential backoff
- **Batch Processing**: Efficient bulk operations

**Configuration**:
```python
SYNC_ENABLED = True
SYNC_INTERVAL_SECONDS = 300  # 5 minutes
SYNC_CONFLICT_RESOLUTION = "postgresql_wins"
SYNC_RETRY_ATTEMPTS = 3
```

### 2. Offline Data Manager (`offline_service.py`)
Manages offline data storage and operations.

**Features**:
- **Connection Monitoring**: Real-time connection status detection
- **Offline Queue**: Stores operations when offline
- **Automatic Sync**: Triggers sync when connection restored
- **Data Retention**: Configurable cleanup of old data
- **Conflict Tracking**: Monitors and reports conflicts

**Configuration**:
```python
OFFLINE_MODE_ENABLED = True
OFFLINE_DATA_RETENTION_DAYS = 30
OFFLINE_SYNC_ON_STARTUP = True
```

### 3. Database Monitor (`database_monitor.py`)
Provides real-time monitoring and health checks.

**Features**:
- **Performance Metrics**: Connection counts, query times, cache hit ratios
- **Health Checks**: Connection, performance, disk space, memory
- **System Metrics**: CPU, memory, disk usage
- **Alerting**: Status-based notifications
- **Historical Data**: Metrics history and trends

### 4. Migration System (`migrations.py`)
Handles database schema changes with rollback capabilities.

**Features**:
- **Version Control**: Timestamped migrations
- **Rollback Support**: Safe rollback operations
- **Checksum Validation**: Migration integrity
- **Cross-Platform**: Works with both PostgreSQL and SQLite
- **Audit Trail**: Complete migration history

## Data Flow

### Online Mode (PostgreSQL Primary)
```
User Action → PostgreSQL → Sync Service → SQLite (backup)
```

### Offline Mode (SQLite Primary)
```
User Action → SQLite → Offline Queue → Sync Service → PostgreSQL (when online)
```

### Conflict Resolution
```
Conflict Detected → Resolution Strategy → Apply Changes → Log Result
```

## Configuration

### Environment Variables
```bash
# Database Selection
USE_SQLITE=true                    # Use SQLite for offline mode
USE_DATABASE=true                  # Enable database integration

# PostgreSQL Configuration
DATABASE_URL=postgresql://user:password@localhost/clinicore
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=clinicore
POSTGRES_USER=clinicore_user
POSTGRES_PASSWORD=clinicore_password
POSTGRES_SSL_MODE=prefer

# Connection Pool Settings
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600

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

## API Endpoints

### Database Management
- `GET /api/v1/database/health` - Database health status
- `GET /api/v1/database/metrics` - Performance metrics
- `GET /api/v1/database/info` - Comprehensive database info

### Sync Management
- `GET /api/v1/database/sync/status` - Sync status
- `POST /api/v1/database/sync/force` - Force immediate sync
- `GET /api/v1/database/sync/conflicts` - View conflicts
- `POST /api/v1/database/sync/conflicts/{id}/resolve` - Resolve conflict

### Offline Management
- `GET /api/v1/database/offline/status` - Offline status
- `GET /api/v1/database/offline/operations` - Offline operations
- `POST /api/v1/database/offline/cleanup` - Cleanup old data

### Migration Management
- `GET /api/v1/database/migrations/history` - Migration history
- `GET /api/v1/database/migrations/pending` - Pending migrations
- `POST /api/v1/database/migrations/run` - Run migrations
- `POST /api/v1/database/migrations/create` - Create migration

### Monitoring
- `POST /api/v1/database/monitoring/start` - Start monitoring
- `POST /api/v1/database/monitoring/stop` - Stop monitoring
- `POST /api/v1/database/monitoring/health-check` - Force health check

## Deployment Scenarios

### 1. Cloud Production (PostgreSQL Primary)
```bash
# Environment
USE_SQLITE=false
USE_DATABASE=true
DATABASE_URL=postgresql://user:pass@cloud-host/clinicore

# Features
- High availability
- Scalability
- Multi-tenant support
- Cloud integration
```

### 2. Mobile/Offline (SQLite Primary)
```bash
# Environment
USE_SQLITE=true
USE_DATABASE=true
SQLITE_URL=sqlite:///./clinicore_offline.db

# Features
- Offline-first
- Local storage
- Sync when online
- Conflict resolution
```

### 3. Hybrid Deployment
```bash
# Environment
USE_SQLITE=true
USE_DATABASE=true
DATABASE_URL=postgresql://user:pass@cloud-host/clinicore
SQLITE_URL=sqlite:///./clinicore_offline.db

# Features
- Best of both worlds
- Automatic failover
- Seamless sync
- High availability
```

## Benefits

### 🚀 Performance
- **Optimized Queries**: Database-specific optimizations
- **Connection Pooling**: Efficient connection management
- **Caching**: Intelligent cache management
- **Indexing**: Automatic index optimization

### 🔒 Reliability
- **Data Integrity**: ACID compliance and validation
- **Backup & Recovery**: Automated backup strategies
- **Conflict Resolution**: Multiple resolution strategies
- **Error Handling**: Comprehensive error management

### 📱 Offline Support
- **Offline-First**: Works without internet connection
- **Automatic Sync**: Seamless data synchronization
- **Conflict Management**: Intelligent conflict resolution
- **Data Retention**: Configurable data cleanup

### 🔧 Maintainability
- **Migration System**: Version-controlled schema changes
- **Monitoring**: Real-time health and performance monitoring
- **Logging**: Comprehensive audit trails
- **Documentation**: Self-documenting architecture

## Best Practices

### 1. Conflict Resolution
- **PostgreSQL Wins**: For production environments
- **SQLite Wins**: For offline-first scenarios
- **Newest Wins**: For time-based conflicts
- **Manual**: For complex conflicts requiring human intervention

### 2. Performance Optimization
- **Connection Pooling**: Configure appropriate pool sizes
- **Indexing**: Create indexes for frequently queried fields
- **Query Optimization**: Use database-specific optimizations
- **Caching**: Implement intelligent caching strategies

### 3. Monitoring
- **Health Checks**: Regular health check intervals
- **Metrics Collection**: Monitor key performance indicators
- **Alerting**: Set up alerts for critical issues
- **Logging**: Comprehensive logging for debugging

### 4. Security
- **SSL/TLS**: Use encrypted connections
- **Authentication**: Strong authentication mechanisms
- **Authorization**: Role-based access control
- **Audit Logging**: Track all data access and changes

## Troubleshooting

### Common Issues

#### 1. Sync Failures
```bash
# Check sync status
curl http://localhost:8000/api/v1/database/sync/status

# Force sync
curl -X POST http://localhost:8000/api/v1/database/sync/force
```

#### 2. Connection Issues
```bash
# Check connection status
curl http://localhost:8000/api/v1/database/connection/status

# Check health
curl http://localhost:8000/api/v1/database/health
```

#### 3. Performance Issues
```bash
# Check metrics
curl http://localhost:8000/api/v1/database/metrics

# Check health
curl http://localhost:8000/api/v1/database/monitoring/health-check
```

### Debug Mode
```bash
# Enable debug logging
export DEBUG=true
export LOG_LEVEL=DEBUG

# Start with verbose logging
python -m app.main --log-level debug
```

## Future Enhancements

### Planned Features
- **Real-time Sync**: WebSocket-based real-time synchronization
- **Advanced Analytics**: Database performance analytics
- **Auto-scaling**: Automatic database scaling
- **Multi-region**: Cross-region replication
- **Backup Automation**: Automated backup and restore
- **Performance Tuning**: Automatic performance optimization

### Integration Opportunities
- **Redis**: Caching layer integration
- **Elasticsearch**: Full-text search integration
- **Kubernetes**: Container orchestration
- **Docker**: Containerization support
- **CI/CD**: Automated deployment pipelines

## Conclusion

The Prontivus dual database architecture provides a robust, scalable, and offline-capable solution for healthcare management systems. By combining PostgreSQL's enterprise features with SQLite's simplicity, we achieve the best of both worlds: production-ready scalability and offline functionality.

This architecture ensures that healthcare professionals can continue their critical work regardless of internet connectivity, while maintaining data integrity and providing seamless synchronization when connectivity is restored.
