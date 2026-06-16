import secrets
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import hash_password, verify_password
from app.models.project import Project, ProjectUserAssociation
from app.models.user import User, UserRole
from app.schemas.auth import ContextResponse, ProjectContextDetail, UserContextDetail
from app.schemas.shared import PaginatedResponse
from app.schemas.user import UserCreate, UserListItem, UserRead, UserUpdate


def generate_api_key(user_id: UUID) -> str:
    """
    Generate a secure API key for Control API access.
    Format: cst_<user_id>_<random_string>
    """
    # Use token_hex to avoid underscores in the random part
    random_part = secrets.token_hex(24)  # 24 bytes = 48 hex chars
    return f"cst_{user_id}_{random_part}"


def generate_user_api_key(user_id: UUID) -> str:
    """
    Generate API key for a user.
    Returns the API key.
    """
    return generate_api_key(user_id)


async def list_users_service(db: AsyncSession) -> list[UserListItem]:
    result = await db.execute(select(User))
    users = result.scalars().all()
    return [
        UserListItem(username=u.name, email=u.email, is_active=u.is_active)
        for u in users
    ]


async def authenticate_user_service(
    email: str, password: str, db: AsyncSession
) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


async def update_user_profile_service(
    user: User, db: AsyncSession, *, name: str | None = None, email: str | None = None
) -> User:
    updated = False
    if name is not None and name != user.name:
        user.name = name
        updated = True
    if email is not None and email != user.email:
        user.email = email
        updated = True
    if updated:
        await db.commit()
        await db.refresh(user)
    return user


async def get_user_project_context_service(
    user: User, db: AsyncSession, active_project_id: int | None = None
) -> ContextResponse:
    # Get all projects the user has access to, excluding archived
    result = await db.execute(
        select(Project)
        .join(ProjectUserAssociation)
        .where(ProjectUserAssociation.user_id == user.id, Project.archived_at.is_(None))
    )
    projects = result.scalars().all()
    available_projects: list[ProjectContextDetail] = [
        ProjectContextDetail(id=p.id, name=p.name) for p in projects
    ]
    # Get active project (by id from cookie)
    active_project: ProjectContextDetail | None = None
    if active_project_id and (
        active := next((p for p in projects if p.id == active_project_id), None)
    ):
        active_project = ProjectContextDetail(id=active.id, name=active.name)
    # User info (minimal)
    user_info: UserContextDetail = UserContextDetail(
        id=str(user.id), email=user.email, name=user.name, role=user.role.value
    )

    return ContextResponse(
        user=user_info,
        active_project=active_project,
        available_projects=available_projects,
    )


async def set_user_project_context_service(
    user: User, project_id: int, db: AsyncSession
) -> None:
    # Validate user has access to the project
    result = await db.execute(
        select(ProjectUserAssociation).where(
            ProjectUserAssociation.user_id == user.id,
            ProjectUserAssociation.project_id == project_id,
        )
    )
    assoc = result.scalar_one_or_none()
    if not assoc:
        raise NoResultFound("User does not have access to this project.")
    # No DB mutation; context is session/cookie-based


async def change_user_password_service(
    user: User,
    db: AsyncSession,
    *,
    old_password: str,
    new_password: str,
    password_hasher: Callable[[str], str],
    password_verifier: Callable[[str, str], bool],
) -> User:
    if not password_verifier(old_password, user.hashed_password):
        raise ValueError("Current password is incorrect.")
    user.hashed_password = password_hasher(new_password)
    await db.commit()
    await db.refresh(user)
    return user


class PaginatedUserList(PaginatedResponse[UserRead]):
    pass


async def list_users_paginated_service(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    search: str | None = None,
) -> PaginatedUserList:
    query = select(User)
    if search:
        like = f"%{search.lower()}%"
        query = query.where(
            or_(
                func.lower(User.name).like(like),
                func.lower(User.email).like(like),
            )
        )
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    if total is None:
        total = 0
    query = query.order_by(User.name).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    users = result.scalars().all()
    return PaginatedUserList(
        items=[
            UserRead.model_validate({**u.__dict__, "role": u.role.value}) for u in users
        ],
        total=total,
        page=page,
        page_size=page_size,
        search=search,
    )


async def create_user_service(
    db: AsyncSession,
    user_in: UserCreate,
    role: UserRole = UserRole.ANALYST,
    is_superuser: bool = False,
    is_active: bool = True,
) -> UserRead:
    # Check for duplicate email or name
    existing = await db.execute(
        select(User).where((User.email == user_in.email) | (User.name == user_in.name))
    )
    if existing.scalars().first():
        raise ValueError("A user with that email or name already exists.")

    # Create user without API keys first to get the ID
    user = User(
        email=user_in.email,
        name=user_in.name,
        hashed_password=hash_password(user_in.password),
        is_active=is_active,
        is_superuser=is_superuser,
        role=role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Generate API key now that we have the user ID
    api_key = generate_user_api_key(user.id)
    current_time = datetime.now(UTC)

    # Update user with API key
    user.api_key = api_key
    user.api_key_created_at = current_time

    await db.commit()
    await db.refresh(user)
    return UserRead.model_validate({**user.__dict__, "role": user.role.value})


async def get_user_by_id_service(db: AsyncSession, user_id: UUID) -> UserRead:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NoResultFound(f"User with id {user_id} not found.")
    return UserRead.model_validate({**user.__dict__, "role": user.role.value})


async def update_user_service(
    db: AsyncSession,
    user_id: UUID,
    payload: UserUpdate,
) -> UserRead:
    from app.core.auth import hash_password
    from app.models.user import UserRole
    from app.schemas.user import UserRead

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NoResultFound(f"User with id {user_id} not found.")

    # Check for duplicate email/name if changed
    if payload.email and payload.email != user.email:
        q = await db.execute(select(User).where(User.email == payload.email))
        if q.scalar_one_or_none():
            raise ValueError("Email already in use.")
        user.email = payload.email
    if payload.name and payload.name != user.name:
        q = await db.execute(select(User).where(User.name == payload.name))
        if q.scalar_one_or_none():
            raise ValueError("Name already in use.")
        user.name = payload.name
    if payload.password:
        user.hashed_password = hash_password(payload.password)
    if payload.role:
        try:
            user.role = UserRole(payload.role)
        except ValueError:
            raise ValueError(f"Invalid role: {payload.role}") from None
    await db.commit()
    await db.refresh(user)
    return UserRead.model_validate({**user.__dict__, "role": user.role.value})


async def deactivate_user_service(db: AsyncSession, user_id: UUID) -> UserRead:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NoResultFound(f"User with id {user_id} not found.")
    user.is_active = False
    await db.commit()
    await db.refresh(user)
    from app.schemas.user import UserRead

    return UserRead.model_validate({**user.__dict__, "role": user.role.value})


async def rotate_user_api_key_service(db: AsyncSession, user_id: UUID) -> str:
    """
    Rotate the API key for a user.
    Returns the new API key.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NoResultFound(f"User with id {user_id} not found.")

    # Generate new API key
    new_api_key = generate_user_api_key(user.id)
    current_time = datetime.now(UTC)

    # Update user with new API key
    user.api_key = new_api_key
    user.api_key_created_at = current_time

    await db.commit()
    await db.refresh(user)

    return new_api_key


async def get_user_api_key_info_service(
    db: AsyncSession, user_id: UUID
) -> dict[str, Any]:
    """
    Get API key information for a user.
    Returns information about the user's API key without exposing the full key.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NoResultFound(f"User with id {user_id} not found.")

    has_api_key = user.api_key is not None
    api_key_prefix = None
    created_at = None
    message = "No API key found for this user"

    if has_api_key and user.api_key:
        # Show first 8 characters for identification
        api_key_prefix = user.api_key[:8] + "..."
        created_at = user.api_key_created_at
        message = "API key is active and available"

    return {
        "has_api_key": has_api_key,
        "api_key_prefix": api_key_prefix,
        "created_at": created_at,
        "last_used_at": None,  # Future enhancement - not implemented yet
        "message": message,
    }


__all__ = [
    "authenticate_user_service",
    "change_user_password_service",
    "create_user_service",
    "deactivate_user_service",
    "generate_api_key",
    "generate_user_api_key",
    "get_user_api_key_info_service",
    "get_user_by_id_service",
    "get_user_project_context_service",
    "list_users_paginated_service",
    "list_users_service",
    "rotate_user_api_key_service",
    "set_user_project_context_service",
    "update_user_profile_service",
    "update_user_service",
]
