"""Login page for NiceGUI interface.

This module provides a login page at /ui/login that integrates with the
existing FastAPI authentication system using authenticate_user_service.
"""

from loguru import logger
from nicegui import app, ui
from sqlalchemy.exc import SQLAlchemyError

from app.core.services.user_service import authenticate_user_service
from app.db.session import sessionmanager


@ui.page("/ui/login")
async def login_page() -> None:
    """NiceGUI login page at /ui/login.

    This page presents a login form with email and password inputs.
    On successful authentication, it stores session data in app.storage.user
    and redirects to the originally requested page or dashboard.
    """
    # Check if already authenticated
    if app.storage.user.get("authenticated", False):
        referrer_path = app.storage.user.get("referrer_path", "/ui/")
        ui.navigate.to(referrer_path)
        return

    # Create centered login card
    with ui.card().classes("w-96 mx-auto mt-20"):
        ui.label("Ouroboros Login").classes("text-2xl font-bold mb-4")

        # Form inputs
        email_input = (
            ui.input(
                label="Email",
                placeholder="Enter your email",
                validation={"Email is required": lambda x: len(x) > 0},
            )
            .classes("w-full mb-4")
            .props("type=email")
        )

        password_input = (
            ui.input(
                label="Password",
                placeholder="Enter your password",
                validation={"Password is required": lambda x: len(x) > 0},
            )
            .classes("w-full mb-4")
            .props("type=password password-toggle-button")
        )

        # Error message label (initially hidden)
        error_label = (
            ui.label("").classes("text-red-500 text-sm mb-4").style("display: none")
        )

        # Login button
        login_button = ui.button("Sign In", color="primary").classes("w-full")

        async def handle_login() -> None:
            """Handle login form submission."""
            # Validate inputs
            email = email_input.value.strip()
            password = password_input.value

            if not email or not password:
                error_label.text = "Email and password are required"
                error_label.style("display: block")
                ui.notify("Email and password are required", color="negative")
                return

            # Get database session
            try:
                async with sessionmanager.session() as db:
                    # Authenticate user
                    # authenticate_user_service can raise SQLAlchemyError from database queries
                    try:
                        user = await authenticate_user_service(email, password, db)
                    except SQLAlchemyError as db_query_error:
                        # Database query errors during authentication
                        logger.error(
                            f"Database query error during authentication for email {email}: {db_query_error}",
                            exc_info=True,
                        )
                        error_label.text = (
                            "An error occurred during authentication. Please try again."
                        )
                        error_label.style("display: block")
                        ui.notify(
                            "An error occurred during authentication", color="negative"
                        )
                        return

                    if not user:
                        error_label.text = "Invalid email or password"
                        error_label.style("display: block")
                        ui.notify("Invalid email or password", color="negative")
                        logger.warning(f"Failed login attempt for email: {email}")
                        return

                    if not user.is_active:
                        error_label.text = "Account is inactive"
                        error_label.style("display: block")
                        ui.notify("Account is inactive", color="negative")
                        logger.warning(f"Inactive user login attempt: {email}")
                        return

                    # Store session data
                    try:
                        app.storage.user["authenticated"] = True
                        app.storage.user["user_id"] = str(user.id)

                        # Get referrer path or default to dashboard
                        referrer_path = app.storage.user.get("referrer_path", "/ui/")

                        # Clear referrer path after use
                        if "referrer_path" in app.storage.user:
                            del app.storage.user["referrer_path"]

                        logger.info(
                            f"User {user.email} logged in successfully via NiceGUI"
                        )

                        # Navigate to original destination or dashboard
                        ui.navigate.to(referrer_path)
                        ui.notify("Login successful", color="positive")
                    except (KeyError, ValueError, RuntimeError) as session_error:
                        # Session storage errors
                        logger.error(
                            f"Session storage error during login for email {email}: {session_error}",
                            exc_info=True,
                        )
                        error_label.text = (
                            "An error occurred during login. Please try again."
                        )
                        error_label.style("display: block")
                        ui.notify("An error occurred during login", color="negative")
            except SQLAlchemyError as db_connection_error:
                # Database connection or session management errors
                logger.error(
                    f"Database connection error during login for email {email}: {db_connection_error}",
                    exc_info=True,
                )
                error_label.text = "An error occurred during login. Please try again."
                error_label.style("display: block")
                ui.notify("An error occurred during login", color="negative")

        # Bind login button click handler
        login_button.on_click(handle_login)

        # Allow Enter key to submit form
        email_input.on("keydown.enter", handle_login)
        password_input.on("keydown.enter", handle_login)
