"""Authentication module for NiceGUI interface.

This module contains authentication-related components for the NiceGUI web
interface, including login pages, authentication middleware, and user context
utilities that integrate with the existing app/core/auth module.

The authentication system integrates NiceGUI's app.storage.user session storage
with the existing FastAPI JWT authentication infrastructure. The login page
is automatically registered via the @ui.page decorator when this module is imported.
"""

from app.ui.auth.context import (
    get_current_ui_user,
    get_user_display_name,
    logout_ui_user,
    require_auth,
)
from app.ui.auth.middleware import register_auth_middleware

__all__ = [
    "get_current_ui_user",
    "get_user_display_name",
    "logout_ui_user",
    "register_auth_middleware",
    "require_auth",
]
