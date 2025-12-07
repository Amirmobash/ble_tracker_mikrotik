# main.py
"""
BLE Tracking System - Main Entry Point
Industrial-grade BLE tracking backend for healthcare/industrial environments
"""

import uvicorn
from app.core.config import settings
from app.core.logging_config import setup_logging
from app.api.main import app

def main():
    """Application entry point with proper initialization"""
    # Setup structured logging
    setup_logging()
    
    # Start the server
    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=False  # We use structlog for access logs
    )

if __name__ == "__main__":
    main()