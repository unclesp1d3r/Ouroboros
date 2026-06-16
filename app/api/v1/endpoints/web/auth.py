"""
Follow these rules for all endpoints in this file:
1. Must return Pydantic models as JSON (no TemplateResponse or render()).
2. Must use FastAPI parameter types: Query, Path, Body, Depends, etc.
3. Must not parse inputs manually -- let FastAPI validate and raise 422s.
4. Must use dependency-injected context for auth/user/project state.
5. Must not include database logic -- delegate to a service layer (e.g. campaign_service).
6. Must not contain HTMX, Jinja, or fragment-rendering logic.
7. Must annotate live-update triggers with: # WS_TRIGGER: <event description>
"""

import re
from typing import Annotated

from fastapi import APIRouter, Body, Cookie, Depends, Form, HTTPException, Response
from fastapi import status as http_status
from jose.exceptions import ExpiredSignatureError, JWTError
from loguru import logger
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import (
    create_access_token,
    decode_access_token,
    hash_password,
    is_token_refresh_needed,
    verify_password,
)
from app.core.config import settings
from app.core.deps import get_current_user
from app.core.services.user_service import (
    authenticate_user_service,
    change_user_password_service,
    get_user_project_context_service,
    set_user_project_context_service,
    update_user_profile_service,
)
from app.db.session import get_db
from app.models.project import Project, ProjectUserAssociation
from app.models.user import User
from app.schemas.auth import (
    ContextResponse,
    LoginResult,
    LoginResultLevel,
    SetContextRequest,
)
from app.schemas.user import UserRead, UserUpdate

router = APIRouter(prefix="/auth", tags=["Auth"])

PASSWORD_MIN_LENGTH = 10


@router.post(
    "/login",
    summary="Login (Web UI)",
    description="Authenticate user and set JWT cookie for web UI. Accepts email and password in form data.",
)
async def login(
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    email: Annotated[
        str,
        Form(
            min_length=1,
            max_length=255,
            pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
        ),
    ],
    password: Annotated[
        str,
        Form(
            min_length=1,
            max_length=255,
        ),
    ],
) -> LoginResult:
    """
    This endpoint is used to authenticate a user and set the JWT cookie for the web UI.
    It accepts email and password in form data, not JSON.
    Returns success/error in a format compatible with SvelteKit SuperForms.
    """
    user = await authenticate_user_service(email, password, db)
    if not user:
        logger.warning(f"Failed login attempt for email: {email}")
        response.status_code = http_status.HTTP_400_BAD_REQUEST
        return LoginResult(
            message="Invalid email or password.",
            level=LoginResultLevel.ERROR,
            access_token=None,
        )

    if not user.is_active:
        logger.warning(f"Inactive user login attempt: {email}")
        response.status_code = http_status.HTTP_403_FORBIDDEN
        return LoginResult(
            message="Account is inactive.",
            level=LoginResultLevel.ERROR,
            access_token=None,
        )

    token = create_access_token(user.id)
    logger.info(f"User {user.email} logged in successfully.")

    # Set access token cookie
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=settings.cookies_secure,  # Use centralized environment setting
        samesite="lax",
        max_age=60 * 60,
    )

    # Get user's projects to set default active project
    result = await db.execute(
        select(Project)
        .join(ProjectUserAssociation)
        .where(ProjectUserAssociation.user_id == user.id, Project.archived_at.is_(None))
        .order_by(Project.id)  # Use consistent ordering
    )
    projects = result.scalars().all()

    # Set active project cookie to first available project
    if projects:
        first_project_id = projects[0].id
        response.set_cookie(
            key="active_project_id",
            value=str(first_project_id),
            httponly=True,
            secure=settings.cookies_secure,
            samesite="lax",
            max_age=60 * 60 * 24 * 30,  # 30 days - longer than access token
        )
        logger.info(f"Set active project {first_project_id} for user {user.email}")

    return LoginResult(
        message="Login successful.", level=LoginResultLevel.SUCCESS, access_token=token
    )


@router.post(
    "/logout",
    summary="Logout (Web UI)",
    description="Clear JWT cookie and log out user.",
)
async def logout(response: Response) -> LoginResult:
    response.delete_cookie("access_token")
    response.delete_cookie("active_project_id")
    return LoginResult(
        message="Logged out.", level=LoginResultLevel.SUCCESS, access_token=None
    )


@router.post(
    "/refresh",
    summary="Refresh JWT token (Web UI)",
    description="Refresh JWT access token using cookie. Supports automatic refresh for long-lived sessions.",
)
async def refresh_token(
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    access_token: Annotated[str | None, Cookie()] = None,
    auto_refresh: Annotated[bool, Form()] = False,
) -> LoginResult:
    """
    Enhanced refresh endpoint that supports:
    - Manual refresh via explicit call
    - Auto-refresh detection for long-lived sessions
    - Proper error handling for expired vs invalid tokens
    """
    if not access_token:
        logger.warning("No access_token cookie found for refresh.")
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED, detail="No token found."
        )

    try:
        # For auto-refresh, check if token actually needs refresh (within 15 minutes of expiration)
        # For manual refresh, always generate a new token
        if auto_refresh and not is_token_refresh_needed(access_token):
            logger.debug(
                "Auto-refresh: Token refresh not needed, returning current token info"
            )
            return LoginResult(
                message="Token is still valid.",
                level=LoginResultLevel.SUCCESS,
                access_token=access_token,
            )

        user_id = decode_access_token(access_token)
    except ExpiredSignatureError:
        logger.info("Expired token provided for refresh")
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
    except JWTError as e:
        logger.warning(f"Invalid token during refresh: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
        ) from e

    user = await db.get(User, user_id)
    if not user or not user.is_active:
        logger.warning(f"Refresh attempt for invalid or inactive user: {user_id}")
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive.",
        )

    # Generate new token with standard expiration
    new_token = create_access_token(user.id)
    logger.info(f"Refreshed token for user {user.email}")

    # Set cookie with secure settings
    response.set_cookie(
        key="access_token",
        value=new_token,
        httponly=True,
        secure=settings.cookies_secure,
        samesite="lax",
        max_age=60 * 60,  # 1 hour standard expiration
    )

    return LoginResult(
        message="Session refreshed.",
        level=LoginResultLevel.SUCCESS,
        access_token=new_token,
    )


@router.get(
    "/me",
    summary="Get current user profile (Web UI)",
    description="Return user profile for current user.",
)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserRead:
    return UserRead.model_validate(current_user, from_attributes=True)


@router.patch(
    "/me",
    summary="Update current user profile (Web UI)",
    description="Update name/email for current user.",
)
async def update_me(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    payload: Annotated[UserUpdate, Body()],
) -> UserRead:
    if (
        payload.name is None and payload.email is None
    ):  # TODO: This should be handled by Pydantic validation
        raise HTTPException(status_code=422, detail="No fields to update.")
    if payload.email and payload.email != current_user.email:
        # TODO: This should be in the service layer
        q = await db.execute(select(User).where(User.email == payload.email))
        if q.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Email already in use.")
    if payload.name and payload.name != current_user.name:
        # TODO: This should be in the service layer
        q = await db.execute(select(User).where(User.name == payload.name))
        if q.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Name already in use.")
    updated_user = await update_user_profile_service(
        current_user, db, name=payload.name, email=payload.email
    )
    return UserRead.model_validate(updated_user, from_attributes=True)


class ChangePasswordRequest(BaseModel):
    old_password: Annotated[
        str, Field(description="Current password", examples=["oldpassword1!A"])
    ]
    new_password: Annotated[
        str, Field(description="New password", examples=["Newpassword2!B"])
    ]
    new_password_confirm: Annotated[
        str, Field(description="New password confirmation", examples=["Newpassword2!B"])
    ]


@router.post(
    "/change_password",
    summary="Change password (Web UI)",
    description="Change password for current user.",
)
async def change_password(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    old_password: Annotated[str, Form(...)],
    new_password: Annotated[str, Form(...)],
    new_password_confirm: Annotated[str, Form(...)],
) -> LoginResult:
    if new_password != new_password_confirm:
        logger.info(
            f"Password change failed: new passwords do not match for user {current_user.email}"
        )
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="New passwords do not match.",
        )

    if (
        len(new_password) < PASSWORD_MIN_LENGTH
        or not re.search(r"[A-Z]", new_password)
        or not re.search(r"[a-z]", new_password)
        or not re.search(r"[0-9]", new_password)
        or not re.search(r"[^A-Za-z0-9]", new_password)
    ):
        logger.info(
            f"Password change failed: weak password for user {current_user.email}"
        )
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Password must be at least {PASSWORD_MIN_LENGTH} characters and include upper, lower, digit, and special character.",
        )
    try:
        await change_user_password_service(
            current_user,
            db,
            old_password=old_password,
            new_password=new_password,
            password_hasher=hash_password,
            password_verifier=verify_password,
        )
        logger.info(f"Password changed successfully for user {current_user.email}")
        return LoginResult(
            message="Password changed successfully.",
            level=LoginResultLevel.SUCCESS,
            access_token=None,
        )
    except ValueError as e:
        logger.warning(f"Password change failed for user {current_user.email}: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED, detail=str(e)
        ) from e
    except (RuntimeError, OSError) as e:
        logger.error(f"Password change error for user {current_user.email}: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again.",
        ) from e


@router.get(
    "/context",
    summary="Get user/project context (Web UI)",
    description="Get current user and project context.",
)
async def get_context(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    active_project_id: Annotated[int | None, Cookie()] = None,
) -> ContextResponse:
    try:
        return await get_user_project_context_service(
            current_user, db, active_project_id
        )
    except Exception as e:
        logger.error(f"Error getting user/project context: {e}")
        raise HTTPException(status_code=500, detail="Failed to get context.") from e


@router.post(
    "/context",
    summary="Set user/project context (Web UI)",
    description="Set active project for current user.",
)
async def set_context(
    response: Response,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    payload: Annotated[SetContextRequest, Body()],
) -> ContextResponse:
    try:
        await set_user_project_context_service(current_user, payload.project_id, db)
    except NoResultFound as e:
        raise HTTPException(
            status_code=403, detail="User does not have access to this project."
        ) from e

    response.set_cookie(
        key="active_project_id",
        value=str(payload.project_id),
        httponly=True,
        secure=settings.cookies_secure,  # Use centralized environment setting
        samesite="lax",
        max_age=60 * 60 * 24 * 30,
    )
    return await get_user_project_context_service(current_user, db, payload.project_id)
