"""Authentication middleware for NiceGUI interface.

This module provides HTTP middleware that intercepts NiceGUI page requests
to enforce authentication. Unauthenticated users are redirected to the login page.
"""

from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.responses import RedirectResponse
from loguru import logger
from nicegui import app

# Unrestricted paths that bypass authentication
UNRESTRICTED_PATHS = {"/ui/login", "/ui/static"}

# Unrestricted path prefixes for NiceGUI static and internal assets
# These paths are served by NiceGUI and should not require authentication
# Include both absolute paths and mount-relative paths (NiceGUI is mounted at /ui/)
UNRESTRICTED_PREFIXES = [
    "/_nicegui/",
    "/_static/",
    "/ui/_nicegui/",
    "/ui/_static/",
]


def _get_nicegui_page_routes() -> set[str]:
    """Get the set of registered NiceGUI page routes.

    Attempts to access NiceGUI's page route registry. Falls back to
    an empty set if the registry is not available or not yet initialized.

    Returns:
        Set of registered page route paths
    """
    try:
        from nicegui import app as nicegui_app

        # Access page routes from NiceGUI app if available
        # NiceGUI stores routes as a dict mapping paths to handlers
        if hasattr(nicegui_app, "routes") and isinstance(nicegui_app.routes, dict):
            # Extract string paths from route keys
            return {str(path) for path in nicegui_app.routes if isinstance(path, str)}
    except (ImportError, AttributeError, RuntimeError, TypeError):
        # NiceGUI registry not available or not initialized
        pass

    return set()


def _should_bypass_auth(path: str) -> bool:
    """Check if a path should bypass authentication checks.

    Args:
        path: The request path to check

    Returns:
        True if the path should bypass authentication, False otherwise
    """
    # Allow unrestricted paths to pass through
    if path in UNRESTRICTED_PATHS:
        return True

    # Allow NiceGUI static and internal asset paths to pass through
    if any(path.startswith(prefix) for prefix in UNRESTRICTED_PREFIXES):
        return True

    # Check if this is a NiceGUI page route using the registry
    page_routes = _get_nicegui_page_routes()
    if page_routes:
        # Use registry-based checking - only protect registered page routes
        return path not in page_routes

    # Fallback: check if path starts with /ui/ (NiceGUI mount path)
    # Only apply auth guard to NiceGUI pages
    return not path.startswith("/ui/")


async def auth_guard_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """HTTP middleware that enforces authentication for NiceGUI pages.

    This middleware:
    - Allows unrestricted paths (login, static assets) to pass through
    - Checks if the request path matches a NiceGUI page route using the registry
    - Verifies authentication status via app.storage.user
    - Redirects unauthenticated users to /ui/login
    - Stores the original request path for post-login redirect

    Args:
        request: The incoming HTTP request
        call_next: The next middleware/handler in the chain

    Returns:
        Response: Either a redirect to login or the response from call_next
    """
    path = request.url.path

    # Check if path should bypass authentication
    if _should_bypass_auth(path):
        return await call_next(request)

    # Check authentication status
    try:
        authenticated = app.storage.user.get("authenticated", False)
        if not authenticated:
            # Store the original request path for post-login redirect
            app.storage.user["referrer_path"] = path
            logger.debug(f"Unauthenticated access to {path}, redirecting to login")
            return RedirectResponse(url="/ui/login", status_code=302)
    except (KeyError, ValueError, RuntimeError) as e:
        logger.warning(f"Error checking authentication status: {e}")
        # On error, redirect to login for safety
        return RedirectResponse(url="/ui/login", status_code=302)

    # User is authenticated, proceed with request
    return await call_next(request)


def register_auth_middleware(app_instance: FastAPI) -> None:
    """Register the authentication middleware with FastAPI.

    This function adds the auth_guard_middleware to the FastAPI application
    using the @app.middleware('http') decorator pattern.

    Args:
        app_instance: The FastAPI application instance
    """

    @app_instance.middleware("http")
    async def _auth_middleware_wrapper(  # pyright: ignore[reportUnusedFunction]
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        return await auth_guard_middleware(request, call_next)
