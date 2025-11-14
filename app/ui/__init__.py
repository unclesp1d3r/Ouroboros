"""NiceGUI web interface module for Ouroboros.

This module provides the NiceGUI-based web interface integration with the FastAPI
application. It sets up the NiceGUI interface and configures it to be mounted
at the /ui/ path prefix.
"""

from fastapi import FastAPI
from nicegui import storage
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import settings
from app.ui.auth.middleware import register_auth_middleware


def setup_nicegui_interface(app: FastAPI) -> None:
    """Initialize the NiceGUI interface for the FastAPI application.

    This function sets up NiceGUI configuration, registers required middleware
    for session management, and registers authentication components.

    Middleware registration order is critical:
    1. RequestTrackingMiddleware (for NiceGUI session tracking)
    2. SessionMiddleware (for session cookie management)
    3. Auth middleware (for authentication enforcement)

    Args:
        app: The FastAPI application instance to integrate NiceGUI with.
    """
    # Add NiceGUI session tracking middleware (must be first)
    app.add_middleware(storage.RequestTrackingMiddleware)

    # Add session middleware with matching secret key
    # The secret must match the storage_secret used in ui.run_with()
    app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

    # Register authentication middleware
    register_auth_middleware(app)

    # Import login page module to trigger @ui.page decorator registration
    # This must happen after middleware registration
    # Import NiceGUI modules for future use
    from nicegui import ui

    from app.ui.auth import login

    _ = ui  # Suppress unused import warning
    _ = login  # Trigger module import
