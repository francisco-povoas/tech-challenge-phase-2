"""
Application bootstrap and entry point.

This module is responsible for:
1. Creating the FastAPI application instance
2. Initializing all infrastructure dependencies
3. Starting the server

It should NOT be imported by application/domain modules to avoid
side effects during unit test collection.

Usage:
    from app.main import create_app, start_server
    
    app = create_app()  # Create FastAPI app with all dependencies
    start_server()      # Start uvicorn server
"""

import uvicorn
from fastapi import FastAPI

from app.config import get_settings, Settings
from app.api.app import create_app as _create_fastapi_app


def create_app(settings: Settings | None = None) -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    This function:
    - Validates settings (including DB_URL if needed)
    - Creates the FastAPI instance with lifespan
    - Registers routers and extensions
    
    Args:
        settings: Optional Settings instance. If None, loads from environment.
        
    Returns:
        Configured FastAPI application instance
    """
    if settings is None:
        settings = get_settings()
    
    # Validate critical settings for server operation
    settings.validate_for_server_start()
    
    # Create FastAPI app with infrastructure initialization in lifespan
    app = _create_fastapi_app(settings)
    
    return app


def start_server() -> None:
    """
    Start the uvicorn server.
    
    This is the main entry point for the application.
    It should only be called when the server is actually needed,
    not during test collection.
    """
    settings = get_settings()
    app = create_app(settings)
    
    uvicorn.run(
        app,
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=settings.SERVER_RELOAD,
        log_level=settings.LOG_LEVEL.lower(),
    )


if __name__ == "__main__":
    start_server()
