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

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authz import user_can_access_project_by_id
from app.core.deps import get_current_user
from app.core.services import template_service
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.shared import (
    AttackTemplateRecordCreate,
    AttackTemplateRecordOut,
    AttackTemplateRecordUpdate,
)

router = APIRouter(prefix="/templates", tags=["Templates"])


def is_admin(user: User) -> bool:
    return user.role == UserRole.ADMIN or user.is_superuser


@router.get("/")
async def list_templates(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    attack_mode: Annotated[str | None, Query()] = None,
    project_id: Annotated[int | None, Query()] = None,
    recommended: Annotated[bool | None, Query()] = None,
) -> list[AttackTemplateRecordOut]:
    """
    List recommended templates, filtered by attack_mode and project_id.
    Non-admins see all recommended templates and all global templates (project_ids is None).
    """
    if project_id and not user_can_access_project_by_id(current_user, project_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized"
        )
    return await template_service.list_templates_service(
        db=db,
        current_user=current_user,
        attack_mode=attack_mode,
        project_id=project_id,
        recommended=recommended,
    )


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_template(
    data: AttackTemplateRecordCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> AttackTemplateRecordOut:
    try:
        return await template_service.create_template_service(data, db, current_user)
    except PermissionError:
        raise HTTPException(status_code=403, detail="Admin only") from None


@router.get("/{template_id}")
async def get_template(
    template_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AttackTemplateRecordOut:
    try:
        return await template_service.get_template_service(template_id, db)
    except LookupError:
        raise HTTPException(status_code=404, detail="Template not found") from None


@router.patch("/{template_id}")
async def update_template(
    template_id: int,
    data: AttackTemplateRecordUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> AttackTemplateRecordOut:
    try:
        return await template_service.update_template_service(
            template_id, data, db, current_user
        )
    except PermissionError:
        raise HTTPException(status_code=403, detail="Admin only") from None
    except LookupError:
        raise HTTPException(status_code=404, detail="Template not found") from None


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    try:
        await template_service.delete_template_service(template_id, db, current_user)
    except PermissionError:
        raise HTTPException(status_code=403, detail="Admin only") from None
    except LookupError:
        raise HTTPException(status_code=404, detail="Template not found") from None
