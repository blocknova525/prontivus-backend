#!/usr/bin/env python3
"""
Robust server startup script for Prontivus Backend
"""

import os
import sys
import uvicorn
import signal
import time
from pathlib import Path

# Set environment variables for PostgreSQL (only if not already set)
if "USE_SQLITE" not in os.environ:
    os.environ["USE_SQLITE"] = "false"  # Use PostgreSQL instead of SQLite
if "USE_DATABASE" not in os.environ:
    os.environ["USE_DATABASE"] = "true"  # Use database endpoints for Prontivus
if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = "postgresql://postgres:devil@localhost:5432/prontivus_db"
if "DATABASE_URL_ASYNC" not in os.environ:
    os.environ["DATABASE_URL_ASYNC"] = "postgresql+asyncpg://postgres:devil@localhost:5432/prontivus_db"
if "POSTGRES_HOST" not in os.environ:
    os.environ["POSTGRES_HOST"] = "localhost"
if "POSTGRES_PORT" not in os.environ:
    os.environ["POSTGRES_PORT"] = "5432"
if "POSTGRES_DB" not in os.environ:
    os.environ["POSTGRES_DB"] = "prontivus_db"
if "POSTGRES_USER" not in os.environ:
    os.environ["POSTGRES_USER"] = "postgres"
if "POSTGRES_PASSWORD" not in os.environ:
    os.environ["POSTGRES_PASSWORD"] = "devil"
if "ENVIRONMENT" not in os.environ:
    os.environ["ENVIRONMENT"] = "production"
if "DEBUG" not in os.environ:
    os.environ["DEBUG"] = "false"

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def signal_handler(sig, frame):
    """Handle shutdown signals gracefully"""
    print('\n🛑 Shutting down server gracefully...')
    sys.exit(0)

def main():
    """Main server startup function"""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Determine mode based on environment variables
    use_database = os.environ.get("USE_DATABASE", "false").lower() == "true"
    use_sqlite = os.environ.get("USE_SQLITE", "true").lower() == "true"
    
    print("🚀 Starting Prontivus Backend Server...")
    if use_database:
        if use_sqlite:
            print("📱 Using SQLite Database (Offline Mode)")
        else:
            print("🌐 Using PostgreSQL Database (Online Mode)")
        print("🔐 Database Authentication Enabled")
    else:
        print("🎭 Using Mock Endpoints (Development)")
    
    print("📡 Server will be available at: http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("🔍 Health Check: http://localhost:8000/health")
    print("=" * 60)
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    
    try:
        # Start the server
        uvicorn.run(
            "main:app",
            host="localhost",
            port=8000,
            reload=False,  # Disable reload for stability
            log_level="info",
            access_log=True,
            loop="asyncio"
        )
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server startup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
