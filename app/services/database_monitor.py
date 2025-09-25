"""
Database monitoring and health check service
Provides real-time monitoring, performance metrics, and health checks
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import psutil
import json
from dataclasses import dataclass, asdict
from enum import Enum

from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

@dataclass
class DatabaseMetrics:
    """Database performance metrics"""
    timestamp: datetime
    connection_count: int
    active_connections: int
    idle_connections: int
    query_count: int
    avg_query_time: float
    slow_queries: int
    memory_usage: float
    cpu_usage: float
    disk_usage: float
    cache_hit_ratio: float
    deadlocks: int
    locks_waiting: int

@dataclass
class HealthCheck:
    """Health check result"""
    name: str
    status: HealthStatus
    message: str
    response_time: float
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None

class DatabaseMonitor:
    """Monitors database health and performance"""
    
    def __init__(self):
        self.postgres_engine = None
        self.sqlite_engine = None
        self.metrics_history: List[DatabaseMetrics] = []
        self.health_checks: List[HealthCheck] = []
        self.is_monitoring = False
        self.monitor_task = None
        
        # Initialize engines
        self._initialize_engines()
    
    def _initialize_engines(self):
        """Initialize database engines for monitoring"""
        try:
            # PostgreSQL engine for monitoring
            self.postgres_engine = create_engine(
                settings.DATABASE_URL,
                echo=False,
                pool_pre_ping=True,
                pool_recycle=3600,
                pool_size=5,
                max_overflow=10
            )
            
            # SQLite engine for monitoring
            self.sqlite_engine = create_engine(
                settings.SQLITE_URL,
                connect_args={"check_same_thread": False},
                echo=False
            )
            
            logger.info("✅ Database monitoring engines initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize monitoring engines: {e}")
            raise
    
    async def start_monitoring(self, interval_seconds: int = 60):
        """Start database monitoring"""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        logger.info(f"🔍 Starting database monitoring (interval: {interval_seconds}s)")
        
        while self.is_monitoring:
            try:
                # Collect metrics
                await self._collect_metrics()
                
                # Run health checks
                await self._run_health_checks()
                
                # Cleanup old data
                self._cleanup_old_data()
                
                # Wait for next cycle
                await asyncio.sleep(interval_seconds)
                
            except Exception as e:
                logger.error(f"❌ Monitoring error: {e}")
                await asyncio.sleep(interval_seconds)
    
    async def stop_monitoring(self):
        """Stop database monitoring"""
        self.is_monitoring = False
        logger.info("🛑 Database monitoring stopped")
    
    async def _collect_metrics(self):
        """Collect database performance metrics"""
        try:
            metrics = await self._get_postgresql_metrics()
            self.metrics_history.append(metrics)
            
            # Keep only last 100 metrics
            if len(self.metrics_history) > 100:
                self.metrics_history = self.metrics_history[-100:]
                
        except Exception as e:
            logger.error(f"❌ Failed to collect metrics: {e}")
    
    async def _get_postgresql_metrics(self) -> DatabaseMetrics:
        """Get PostgreSQL performance metrics"""
        try:
            with self.postgres_engine.connect() as conn:
                # Connection metrics
                connection_stats = conn.execute(text("""
                    SELECT 
                        count(*) as total_connections,
                        count(*) FILTER (WHERE state = 'active') as active_connections,
                        count(*) FILTER (WHERE state = 'idle') as idle_connections
                    FROM pg_stat_activity
                """)).fetchone()
                
                # Query performance metrics
                query_stats = conn.execute(text("""
                    SELECT 
                        count(*) as query_count,
                        avg(mean_exec_time) as avg_query_time,
                        count(*) FILTER (WHERE mean_exec_time > 1000) as slow_queries
                    FROM pg_stat_statements
                """)).fetchone()
                
                # Cache hit ratio
                cache_stats = conn.execute(text("""
                    SELECT 
                        round(100.0 * sum(blks_hit) / (sum(blks_hit) + sum(blks_read)), 2) as cache_hit_ratio
                    FROM pg_stat_database
                    WHERE datname = current_database()
                """)).fetchone()
                
                # Lock information
                lock_stats = conn.execute(text("""
                    SELECT 
                        count(*) FILTER (WHERE granted = false) as locks_waiting,
                        count(*) FILTER (WHERE mode = 'ExclusiveLock') as deadlocks
                    FROM pg_locks
                """)).fetchone()
                
                # System metrics
                memory_usage = psutil.virtual_memory().percent
                cpu_usage = psutil.cpu_percent()
                disk_usage = psutil.disk_usage('/').percent
                
                return DatabaseMetrics(
                    timestamp=datetime.utcnow(),
                    connection_count=connection_stats[0] or 0,
                    active_connections=connection_stats[1] or 0,
                    idle_connections=connection_stats[2] or 0,
                    query_count=query_stats[0] or 0,
                    avg_query_time=float(query_stats[1] or 0),
                    slow_queries=query_stats[2] or 0,
                    memory_usage=memory_usage,
                    cpu_usage=cpu_usage,
                    disk_usage=disk_usage,
                    cache_hit_ratio=float(cache_stats[0] or 0),
                    deadlocks=lock_stats[1] or 0,
                    locks_waiting=lock_stats[0] or 0
                )
                
        except Exception as e:
            logger.error(f"❌ Failed to get PostgreSQL metrics: {e}")
            # Return default metrics on error
            return DatabaseMetrics(
                timestamp=datetime.utcnow(),
                connection_count=0,
                active_connections=0,
                idle_connections=0,
                query_count=0,
                avg_query_time=0.0,
                slow_queries=0,
                memory_usage=0.0,
                cpu_usage=0.0,
                disk_usage=0.0,
                cache_hit_ratio=0.0,
                deadlocks=0,
                locks_waiting=0
            )
    
    async def _run_health_checks(self):
        """Run database health checks"""
        health_checks = [
            self._check_connection_health,
            self._check_performance_health,
            self._check_disk_space_health,
            self._check_memory_health,
            self._check_query_performance_health,
            self._check_replication_health
        ]
        
        for check_func in health_checks:
            try:
                health_check = await check_func()
                self.health_checks.append(health_check)
            except Exception as e:
                logger.error(f"❌ Health check failed: {e}")
        
        # Keep only last 50 health checks
        if len(self.health_checks) > 50:
            self.health_checks = self.health_checks[-50:]
    
    async def _check_connection_health(self) -> HealthCheck:
        """Check database connection health"""
        start_time = time.time()
        
        try:
            with self.postgres_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            response_time = (time.time() - start_time) * 1000
            
            if response_time < 100:
                status = HealthStatus.HEALTHY
                message = f"Connection healthy ({response_time:.2f}ms)"
            elif response_time < 500:
                status = HealthStatus.WARNING
                message = f"Connection slow ({response_time:.2f}ms)"
            else:
                status = HealthStatus.CRITICAL
                message = f"Connection very slow ({response_time:.2f}ms)"
            
            return HealthCheck(
                name="connection",
                status=status,
                message=message,
                response_time=response_time,
                timestamp=datetime.utcnow(),
                details={"response_time_ms": response_time}
            )
            
        except Exception as e:
            return HealthCheck(
                name="connection",
                status=HealthStatus.CRITICAL,
                message=f"Connection failed: {str(e)}",
                response_time=(time.time() - start_time) * 1000,
                timestamp=datetime.utcnow(),
                details={"error": str(e)}
            )
    
    async def _check_performance_health(self) -> HealthCheck:
        """Check database performance health"""
        try:
            if not self.metrics_history:
                return HealthCheck(
                    name="performance",
                    status=HealthStatus.UNKNOWN,
                    message="No metrics available",
                    response_time=0,
                    timestamp=datetime.utcnow()
                )
            
            latest_metrics = self.metrics_history[-1]
            
            # Check cache hit ratio
            if latest_metrics.cache_hit_ratio < 90:
                status = HealthStatus.WARNING
                message = f"Low cache hit ratio: {latest_metrics.cache_hit_ratio}%"
            elif latest_metrics.cache_hit_ratio < 95:
                status = HealthStatus.WARNING
                message = f"Cache hit ratio could be better: {latest_metrics.cache_hit_ratio}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"Good cache hit ratio: {latest_metrics.cache_hit_ratio}%"
            
            return HealthCheck(
                name="performance",
                status=status,
                message=message,
                response_time=0,
                timestamp=datetime.utcnow(),
                details={
                    "cache_hit_ratio": latest_metrics.cache_hit_ratio,
                    "avg_query_time": latest_metrics.avg_query_time,
                    "slow_queries": latest_metrics.slow_queries
                }
            )
            
        except Exception as e:
            return HealthCheck(
                name="performance",
                status=HealthStatus.CRITICAL,
                message=f"Performance check failed: {str(e)}",
                response_time=0,
                timestamp=datetime.utcnow(),
                details={"error": str(e)}
            )
    
    async def _check_disk_space_health(self) -> HealthCheck:
        """Check disk space health"""
        try:
            disk_usage = psutil.disk_usage('/').percent
            
            if disk_usage > 90:
                status = HealthStatus.CRITICAL
                message = f"Disk space critical: {disk_usage}% used"
            elif disk_usage > 80:
                status = HealthStatus.WARNING
                message = f"Disk space warning: {disk_usage}% used"
            else:
                status = HealthStatus.HEALTHY
                message = f"Disk space healthy: {disk_usage}% used"
            
            return HealthCheck(
                name="disk_space",
                status=status,
                message=message,
                response_time=0,
                timestamp=datetime.utcnow(),
                details={"disk_usage_percent": disk_usage}
            )
            
        except Exception as e:
            return HealthCheck(
                name="disk_space",
                status=HealthStatus.CRITICAL,
                message=f"Disk space check failed: {str(e)}",
                response_time=0,
                timestamp=datetime.utcnow(),
                details={"error": str(e)}
            )
    
    async def _check_memory_health(self) -> HealthCheck:
        """Check memory health"""
        try:
            memory_usage = psutil.virtual_memory().percent
            
            if memory_usage > 90:
                status = HealthStatus.CRITICAL
                message = f"Memory usage critical: {memory_usage}%"
            elif memory_usage > 80:
                status = HealthStatus.WARNING
                message = f"Memory usage warning: {memory_usage}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"Memory usage healthy: {memory_usage}%"
            
            return HealthCheck(
                name="memory",
                status=status,
                message=message,
                response_time=0,
                timestamp=datetime.utcnow(),
                details={"memory_usage_percent": memory_usage}
            )
            
        except Exception as e:
            return HealthCheck(
                name="memory",
                status=HealthStatus.CRITICAL,
                message=f"Memory check failed: {str(e)}",
                response_time=0,
                timestamp=datetime.utcnow(),
                details={"error": str(e)}
            )
    
    async def _check_query_performance_health(self) -> HealthCheck:
        """Check query performance health"""
        try:
            if not self.metrics_history:
                return HealthCheck(
                    name="query_performance",
                    status=HealthStatus.UNKNOWN,
                    message="No metrics available",
                    response_time=0,
                    timestamp=datetime.utcnow()
                )
            
            latest_metrics = self.metrics_history[-1]
            
            if latest_metrics.avg_query_time > 1000:
                status = HealthStatus.CRITICAL
                message = f"Average query time too high: {latest_metrics.avg_query_time}ms"
            elif latest_metrics.avg_query_time > 500:
                status = HealthStatus.WARNING
                message = f"Average query time high: {latest_metrics.avg_query_time}ms"
            else:
                status = HealthStatus.HEALTHY
                message = f"Query performance good: {latest_metrics.avg_query_time}ms avg"
            
            return HealthCheck(
                name="query_performance",
                status=status,
                message=message,
                response_time=0,
                timestamp=datetime.utcnow(),
                details={
                    "avg_query_time": latest_metrics.avg_query_time,
                    "slow_queries": latest_metrics.slow_queries
                }
            )
            
        except Exception as e:
            return HealthCheck(
                name="query_performance",
                status=HealthStatus.CRITICAL,
                message=f"Query performance check failed: {str(e)}",
                response_time=0,
                timestamp=datetime.utcnow(),
                details={"error": str(e)}
            )
    
    async def _check_replication_health(self) -> HealthCheck:
        """Check replication health (if applicable)"""
        try:
            with self.postgres_engine.connect() as conn:
                # Check if replication is configured
                replication_status = conn.execute(text("""
                    SELECT 
                        CASE 
                            WHEN count(*) > 0 THEN 'replicating'
                            ELSE 'not_configured'
                        END as status
                    FROM pg_stat_replication
                """)).fetchone()
                
                if replication_status[0] == 'not_configured':
                    return HealthCheck(
                        name="replication",
                        status=HealthStatus.HEALTHY,
                        message="Replication not configured (single instance)",
                        response_time=0,
                        timestamp=datetime.utcnow(),
                        details={"status": "not_configured"}
                    )
                else:
                    return HealthCheck(
                        name="replication",
                        status=HealthStatus.HEALTHY,
                        message="Replication active",
                        response_time=0,
                        timestamp=datetime.utcnow(),
                        details={"status": "replicating"}
                    )
                
        except Exception as e:
            return HealthCheck(
                name="replication",
                status=HealthStatus.WARNING,
                message=f"Replication check failed: {str(e)}",
                response_time=0,
                timestamp=datetime.utcnow(),
                details={"error": str(e)}
            )
    
    def _cleanup_old_data(self):
        """Cleanup old monitoring data"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            
            # Cleanup old metrics
            self.metrics_history = [
                m for m in self.metrics_history 
                if m.timestamp > cutoff_time
            ]
            
            # Cleanup old health checks
            self.health_checks = [
                h for h in self.health_checks 
                if h.timestamp > cutoff_time
            ]
            
        except Exception as e:
            logger.error(f"❌ Failed to cleanup old data: {e}")
    
    def get_current_metrics(self) -> Optional[DatabaseMetrics]:
        """Get current database metrics"""
        return self.metrics_history[-1] if self.metrics_history else None
    
    def get_metrics_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get metrics history for specified hours"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        return [
            asdict(metric) for metric in self.metrics_history
            if metric.timestamp > cutoff_time
        ]
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status"""
        if not self.health_checks:
            return {
                "overall_status": HealthStatus.UNKNOWN.value,
                "checks": [],
                "summary": "No health checks available"
            }
        
        # Get latest health checks
        latest_checks = {}
        for check in self.health_checks:
            if check.name not in latest_checks or check.timestamp > latest_checks[check.name].timestamp:
                latest_checks[check.name] = check
        
        # Determine overall status
        statuses = [check.status for check in latest_checks.values()]
        
        if HealthStatus.CRITICAL in statuses:
            overall_status = HealthStatus.CRITICAL
        elif HealthStatus.WARNING in statuses:
            overall_status = HealthStatus.WARNING
        elif HealthStatus.HEALTHY in statuses:
            overall_status = HealthStatus.HEALTHY
        else:
            overall_status = HealthStatus.UNKNOWN
        
        return {
            "overall_status": overall_status.value,
            "checks": [asdict(check) for check in latest_checks.values()],
            "summary": f"Database health: {overall_status.value}",
            "last_updated": max(check.timestamp for check in latest_checks.values()).isoformat()
        }
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        if not self.metrics_history:
            return {"message": "No metrics available"}
        
        latest_metrics = self.metrics_history[-1]
        
        return {
            "timestamp": latest_metrics.timestamp.isoformat(),
            "connections": {
                "total": latest_metrics.connection_count,
                "active": latest_metrics.active_connections,
                "idle": latest_metrics.idle_connections
            },
            "performance": {
                "avg_query_time_ms": latest_metrics.avg_query_time,
                "slow_queries": latest_metrics.slow_queries,
                "cache_hit_ratio": latest_metrics.cache_hit_ratio
            },
            "system": {
                "memory_usage_percent": latest_metrics.memory_usage,
                "cpu_usage_percent": latest_metrics.cpu_usage,
                "disk_usage_percent": latest_metrics.disk_usage
            },
            "issues": {
                "deadlocks": latest_metrics.deadlocks,
                "locks_waiting": latest_metrics.locks_waiting
            }
        }
    
    async def force_health_check(self) -> Dict[str, Any]:
        """Force an immediate health check"""
        logger.info("🔍 Running forced health check...")
        
        # Run all health checks
        await self._run_health_checks()
        
        # Return current health status
        return self.get_health_status()

# Global database monitor instance
db_monitor = DatabaseMonitor()
