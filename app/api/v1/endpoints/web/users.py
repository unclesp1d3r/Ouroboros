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

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authz import user_can
from app.core.deps import get_current_user
from app.core.services.user_service import (
    PaginatedUserList,
    create_user_service,
    deactivate_user_service,
    get_user_by_id_service,
    list_users_paginated_service,
    update_user_service,
)
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserRead, UserUpdate

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.get(
    "",
    summary="List users",
    description="Admin-only: List users. Returns a paginated list of users.",
)
async def list_users(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Users per page")] = 20,
    search: Annotated[str | None, Query(description="Search by name or email")] = None,
) -> PaginatedUserList:
    if not (
        getattr(current_user, "is_superuser", False)
        or user_can(current_user, "system", "read_users")
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized"
        )
    return await list_users_paginated_service(
        db, page=page, page_size=page_size, search=search
    )


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
    description="Admin-only: Create a new user. Returns the created user.",
)
async def create_user(
    user_in: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserRead:
    if not (
        getattr(current_user, "is_superuser", False)
        or user_can(current_user, "system", "create_users")
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized"
        )
    try:
        return await create_user_service(db, user_in)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e


@router.get(
    "/{user_id}",
    summary="View user detail",
    description="Admin-only: View user detail as an HTML fragment.",
)
async def get_user_detail(
    user_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserRead:
    if not (
        getattr(current_user, "is_superuser", False)
        or user_can(current_user, "system", "read_users")
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized"
        )
    try:
        return await get_user_by_id_service(db, user_id)
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        ) from None


@router.patch(
    "/{user_id}",
    summary="Update user info or role",
    description="Admin-only: Update user info or role. Returns updated user detail fragment.",
)
async def update_user(
    user_id: UUID,
    payload: UserUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserRead:
    if not (
        getattr(current_user, "is_superuser", False)
        or user_can(current_user, "system", "update_users")
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized"
        )
    try:
        return await update_user_service(db, user_id, payload)
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        ) from None
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(e)
        ) from None


@router.delete(
    "/{user_id}",
    summary="Deactivate (soft delete) a user",
    description="Admin-only: Deactivate (soft delete) a user. Returns updated user detail fragment.",
)
async def deactivate_user(
    user_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserRead:
    if not (
        getattr(current_user, "is_superuser", False)
        or user_can(current_user, "system", "delete_users")
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized"
        )
    try:
        return await deactivate_user_service(db, user_id)
    except NoResultFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        ) from e
