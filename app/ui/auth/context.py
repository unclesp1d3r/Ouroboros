"""Session management utilities for NiceGUI authentication.

This module provides helper functions for managing user sessions in NiceGUI,
bridging NiceGUI's app.storage.user with the existing database-backed User model.
"""

import contextlib
import functools
from collections.abc import Awaitable, Callable
from typing import ParamSpec, TypeVar
from uuid import UUID

from loguru import logger
from nicegui import app, ui
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload

from app.db.session import sessionmanager
from app.models.user import User

P = ParamSpec("P")
R = TypeVar("R")


async def get_current_ui_user() -> User | None:
    """Get the current authenticated user from NiceGUI session.

    This function:
    - Checks if user is authenticated via app.storage.user
    - Extracts user_id from session storage
    - Queries the database for the full User object
    - Returns None if not authenticated or user not found

    Returns:
        User | None: The authenticated User object or None if not authenticated
    """
    # Check authentication status
    if not app.storage.user.get("authenticated", False):
        return None

    # Get user_id from session
    user_id_str = app.storage.user.get("user_id")
    if not user_id_str:
        logger.warning("Session has authenticated=True but no user_id")
        return None

    # Convert string to UUID and query database
    try:
        user_uuid = UUID(user_id_str)
    except ValueError as e:
        logger.error(f"Invalid user_id format in session: {user_id_str}, error: {e}")
        return None

    # Query database for user
    try:
        async with sessionmanager.session() as db:
            result = await db.execute(
                select(User)
                .where(User.id == user_uuid)
                .options(selectinload(User.project_associations))
            )
            user = result.scalar_one_or_none()

            if user and user.is_active:
                return user

            if user:
                logger.warning(f"Inactive user attempted access: {user.email}")
            else:
                logger.warning(f"User not found for ID: {user_uuid}")
            return None

    except (SQLAlchemyError, ValueError, KeyError) as e:
        logger.error(f"Error getting current UI user: {e}")
        return None


def logout_ui_user() -> None:
    """Log out the current user and clear session data.

    This function:
    - Clears all session data from app.storage.user
    - Navigates to the login page
    - Optionally displays a logout notification
    """
    try:
        # Clear all session data
        app.storage.user.clear()
        logger.info("User logged out via NiceGUI")

        # Navigate to login page
        ui.navigate.to("/ui/login")

        # Display logout notification
        ui.notify("Logged out successfully", color="positive")
    except (KeyError, ValueError, RuntimeError) as e:
        logger.error(f"Error during logout: {e}")
        # Still try to navigate to login
        with contextlib.suppress(Exception):
            ui.navigate.to("/ui/login")


def require_auth(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R | None]]:  # noqa: UP047
    """Decorator that requires authentication for NiceGUI page functions.

    This decorator:
    - Checks authentication before executing the page function
    - Redirects to login if not authenticated
    - Stores the actual current path for post-login redirect
    - Passes the authenticated User object to the wrapped function

    Args:
        func: The NiceGUI page function to protect

    Returns:
        Wrapped function that requires authentication
    """

    @functools.wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R | None:  # type: ignore[valid-type]
        user = await get_current_ui_user()
        if not user:
            # Get the actual current path for redirect after login
            # The middleware handles most cases, but for decorator-based checks,
            # we try to get the path from storage if middleware already set it,
            # otherwise use a sensible default
            referrer_path = app.storage.user.get("referrer_path", "/ui/")

            # Store path for redirect after login (in case middleware hasn't set it yet)
            with contextlib.suppress(KeyError, ValueError):
                app.storage.user["referrer_path"] = referrer_path
            ui.navigate.to("/ui/login")
            return None

        # Call original function with user as first argument
        return await func(user, *args, **kwargs)  # type: ignore[call-arg]

    return wrapper  # type: ignore[return-value]


async def get_user_display_name() -> str:
    """Get the display name for the current authenticated user.

    Returns:
        str: User's name, email, or "Guest" if not authenticated
    """
    user = await get_current_ui_user()
    if not user:
        return "Guest"

    # Prefer name over email for display
    return user.name if user.name else user.email
