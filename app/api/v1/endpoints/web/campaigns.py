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

from datetime import UTC, datetime
from typing import Annotated

from fastapi import (
    APIRouter,
    Body,
    Depends,
    HTTPException,
    Path,
    Query,
    Request,
    status,
)
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authz import (
    user_can_access_campaign_by_id,
    user_can_access_project,
    user_can_access_project_by_id,
)
from app.core.deps import get_current_user
from app.core.services.campaign_service import (
    AttackNotFoundError,
    CampaignNotFoundError,
    add_attack_to_campaign_service,
    archive_campaign_service,
    create_campaign_service,
    export_campaign_template_service,
    get_campaign_metrics_service,
    get_campaign_progress_service,
    get_campaign_with_attack_summaries_service,
    list_campaigns_service,
    relaunch_campaign_service,
    reorder_attacks_service,
    start_campaign_service,
    stop_campaign_service,
    update_campaign_service,
)
from app.db.session import get_db
from app.models.project import Project
from app.models.user import User
from app.schemas.attack import AttackCreate, AttackSummary
from app.schemas.campaign import (
    CampaignAndAttackSummaries,
    CampaignCreate,
    CampaignMetrics,
    CampaignProgress,
    CampaignRead,
    CampaignUpdate,
    CampaignWithAttacks,
    ReorderAttacksRequest,
    ReorderAttacksResponse,
)
from app.schemas.shared import CampaignTemplate

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])


class CampaignDetailResponse(BaseModel):
    campaign: CampaignRead
    attacks: list[AttackSummary]


class CampaignListResponse(BaseModel):
    items: list[CampaignRead]
    total: int
    page: int
    size: int
    total_pages: int


class AttackCampaignResponse(BaseModel):
    campaign: CampaignRead
    attacks: list[AttackSummary]


async def _check_user_has_access_to_campaign(
    campaign_id: int,
    action: str,
    db: AsyncSession,
    current_user: User,
) -> None:
    if not await user_can_access_campaign_by_id(current_user, campaign_id, action, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have access to campaign",
        )


# /api/v1/web/campaigns/{campaign_id}/reorder_attacks
@router.post(
    "/{campaign_id}/reorder_attacks",
    summary="Reorder attacks in a campaign",
    description="Accepts a list of attack IDs and updates their order (position) within the campaign.",
    status_code=status.HTTP_200_OK,
)
async def reorder_attacks(
    campaign_id: int,
    data: ReorderAttacksRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ReorderAttacksResponse:
    try:
        await _check_user_has_access_to_campaign(campaign_id, "write", db, current_user)
        new_order = await reorder_attacks_service(campaign_id, data.attack_ids, db)
        return ReorderAttacksResponse(success=True, new_order=new_order)
    except CampaignNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except AttackNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


# /api/v1/web/campaigns/{campaign_id}/start
@router.post(
    "/{campaign_id}/start",
    summary="Start Campaign Execution",
    description="""
    Start a campaign by transitioning it from 'draft' state to 'active' state.

    This endpoint initiates the campaign execution process, which will:
    - Validate that the campaign has at least one attack configured
    - Check that the associated hash list contains hashes to crack
    - Verify that agents are available to execute tasks
    - Generate tasks for the campaign's attacks
    - Begin distributing tasks to available agents

    **Prerequisites:**
    - Campaign must be in 'draft' state
    - Campaign must have at least one attack configured
    - Associated hash list must contain hashes
    - User must have 'write' access to the campaign

    **State Transitions:**
    - `draft` -> `active`: Campaign starts successfully
    - Other states will result in a 400 Bad Request error

    **Real-time Updates:**
    Starting a campaign triggers SSE events for real-time UI updates.
    """,
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Campaign started successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 123,
                        "name": "Corporate Password Recovery 2024",
                        "state": "active",
                        "project_id": 1,
                        "hash_list_id": 456,
                        "priority": 50,
                        "created_at": "2024-01-01T12:00:00Z",
                        "updated_at": "2024-01-01T15:30:00Z",
                    }
                }
            },
        },
        400: {
            "description": "Campaign cannot be started",
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_state": {
                            "summary": "Campaign not in draft state",
                            "value": {
                                "detail": "Campaign must be in draft state to start"
                            },
                        },
                        "no_attacks": {
                            "summary": "No attacks configured",
                            "value": {
                                "detail": "Campaign must have at least one attack to start"
                            },
                        },
                        "no_hashes": {
                            "summary": "Empty hash list",
                            "value": {
                                "detail": "Hash list must contain hashes to crack"
                            },
                        },
                    }
                }
            },
        },
        403: {
            "description": "Insufficient permissions",
            "content": {
                "application/json": {
                    "example": {"detail": "User does not have write access to campaign"}
                }
            },
        },
        404: {
            "description": "Campaign not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Campaign with ID 123 not found"}
                }
            },
        },
    },
    tags=["Campaigns", "Campaign Lifecycle"],
)
async def start_campaign(
    campaign_id: Annotated[
        int,
        Path(
            description="Unique identifier of the campaign to start",
            examples=[123],
            gt=0,
        ),
    ],
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> CampaignRead:
    try:
        await _check_user_has_access_to_campaign(campaign_id, "write", db, current_user)
        return await start_campaign_service(campaign_id, db)
    except CampaignNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


# /api/v1/web/campaigns/{campaign_id}/stop
@router.post(
    "/{campaign_id}/stop",
    summary="Stop campaign",
    description="Set campaign state to draft (stopped).",
    status_code=status.HTTP_200_OK,
)
async def stop_campaign(
    campaign_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> CampaignRead:
    try:
        await _check_user_has_access_to_campaign(campaign_id, "write", db, current_user)
        return await stop_campaign_service(campaign_id, db)
    except CampaignNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get(
    "/{campaign_id}",
    summary="Campaign detail view",
    description="Get campaign detail and attack summaries.",
)
async def campaign_detail(
    campaign_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> CampaignDetailResponse:
    try:
        await _check_user_has_access_to_campaign(campaign_id, "read", db, current_user)
        service_data: CampaignAndAttackSummaries = (
            await get_campaign_with_attack_summaries_service(campaign_id, db)
        )
        return CampaignDetailResponse(
            campaign=service_data.campaign, attacks=service_data.attacks
        )
    except CampaignNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


async def get_active_project_id(request: Request) -> int | None:
    val = request.cookies.get("active_project_id")
    try:
        return int(val) if val else None
    except (ValueError, TypeError):
        return None


@router.get(
    "",
    summary="List campaigns",
    description="List campaigns with pagination and filtering.",
)
async def list_campaigns(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
    name: Annotated[str | None, Query()] = None,
) -> CampaignListResponse:
    active_project_id = await get_active_project_id(request)
    if not active_project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active project selected.",
        )

    if not any(
        assoc.project_id == active_project_id and assoc.user_id == current_user.id
        for assoc in current_user.project_associations
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized for this project.",
        )

    skip = (page - 1) * size
    campaigns_raw, total = await list_campaigns_service(
        db, skip=skip, limit=size, name_filter=name, project_id=active_project_id
    )
    campaigns_validated = [CampaignRead.model_validate(c) for c in campaigns_raw]
    total_pages = (total + size - 1) // size if size else 1
    return CampaignListResponse(
        items=campaigns_validated,
        total=total,
        page=page,
        size=size,
        total_pages=total_pages,
    )


@router.post(
    "",
    summary="Create a new campaign",
    description="Create a new campaign.",
    status_code=status.HTTP_201_CREATED,
)
async def create_campaign(
    campaign_data: CampaignCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> CampaignRead:
    if not await user_can_access_project_by_id(
        current_user, campaign_data.project_id, action="write", db=db
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create campaigns in this project.",
        )

    try:
        created_campaign_obj = await create_campaign_service(campaign_data, db)
        return CampaignRead.model_validate(created_campaign_obj)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.patch(
    "/{campaign_id}",
    summary="Update campaign",
    description="Update campaign fields.",
)
async def update_campaign(
    campaign_id: int,
    campaign_update_data: CampaignUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> CampaignRead:
    await _check_user_has_access_to_campaign(campaign_id, "write", db, current_user)
    try:
        return await update_campaign_service(campaign_id, campaign_update_data, db)
    except CampaignNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.delete(
    "/{campaign_id}",
    summary="Archive (soft-delete) campaign",
    description="Archive a campaign by setting its state to ARCHIVED.",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def archive_campaign(
    campaign_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Response:  # Return Response for 204 No Content
    try:
        await _check_user_has_access_to_campaign(campaign_id, "write", db, current_user)
        await archive_campaign_service(campaign_id, db)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except CampaignNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post(
    "/{campaign_id}/add_attack",
    summary="Add attack to campaign",
    description="Create a new attack and attach it to the specified campaign.",
    status_code=status.HTTP_201_CREATED,
)
async def add_attack_to_campaign(
    campaign_id: int,
    data: AttackCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> AttackCampaignResponse:
    try:
        await _check_user_has_access_to_campaign(campaign_id, "write", db, current_user)
        await add_attack_to_campaign_service(campaign_id, data, db)
        detail_data: CampaignAndAttackSummaries = (
            await get_campaign_with_attack_summaries_service(campaign_id, db)
        )
        return AttackCampaignResponse(
            campaign=detail_data.campaign, attacks=detail_data.attacks
        )
    except CampaignNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.get(
    "/{campaign_id}/progress",
    summary="Get campaign progress",
    description="Returns progress/status for the campaign.",
)
async def campaign_progress(
    campaign_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> CampaignProgress:
    try:
        await _check_user_has_access_to_campaign(campaign_id, "read", db, current_user)
        return await get_campaign_progress_service(campaign_id, db)
    except CampaignNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get(
    "/{campaign_id}/metrics",
    summary="Get campaign metrics",
    description="Returns aggregate metrics for the campaign.",
)
async def campaign_metrics(
    campaign_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> CampaignMetrics:
    try:
        await _check_user_has_access_to_campaign(campaign_id, "read", db, current_user)
        return await get_campaign_metrics_service(campaign_id, db)
    except CampaignNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post(
    "/{campaign_id}/relaunch",
    summary="Relaunch failed or modified attacks in a campaign",
    description="Relaunches failed attacks or those with modified resources. Requires explicit confirmation.",
    status_code=status.HTTP_200_OK,
)
async def relaunch_campaign(
    campaign_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> CampaignDetailResponse:
    try:
        await _check_user_has_access_to_campaign(campaign_id, "write", db, current_user)
        service_data: CampaignAndAttackSummaries = await relaunch_campaign_service(
            campaign_id, db
        )
        return CampaignDetailResponse(
            campaign=service_data.campaign, attacks=service_data.attacks
        )
    except CampaignNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e


@router.get(
    "/{campaign_id}/export",
    summary="Export campaign as JSON",
    description="Export a single campaign as a JSON file using the CampaignTemplate schema.",
    status_code=status.HTTP_200_OK,
)
async def export_campaign_json(
    campaign_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> CampaignTemplate:
    try:
        await _check_user_has_access_to_campaign(campaign_id, "read", db, current_user)
        return await export_campaign_template_service(campaign_id, db)
    except CampaignNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post(
    "/import_json",
    summary="Import campaign from JSON",
    description="Import a campaign from a JSON file or payload. Creates a new campaign based on the template and returns the campaign with its attacks, not persisted to the database.",
    status_code=status.HTTP_201_CREATED,
)
async def import_campaign_json(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    payload_data: Annotated[
        CampaignTemplate, Body(..., description="Campaign template")
    ],
) -> CampaignWithAttacks:
    try:
        campaign_template = CampaignTemplate.model_validate(payload_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid campaign template: {e}",
        ) from e

    active_project_id = await get_active_project_id(request)
    project_to_import_into = await db.get(Project, active_project_id)
    if not project_to_import_into:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target project {active_project_id} for import not found.",
        )

    if not user_can_access_project(
        current_user, project_to_import_into, action="write"
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Not authorized to create campaigns in project {active_project_id}.",
        )

    # Build a CampaignWithAttacks response for prepopulating the editor
    now = datetime.now(UTC)

    return CampaignWithAttacks.model_validate(
        {
            "id": 0,
            "name": campaign_template.name,
            "description": campaign_template.description,
            "project_id": active_project_id,
            "hash_list_id": campaign_template.hash_list_id,
            "state": "draft",
            "created_at": now,
            "updated_at": now,
            "priority": getattr(campaign_template, "priority", 1),
            "attacks": campaign_template.attacks or [],
        }
    )


@router.get(
    "/{campaign_id}/attacks",
    summary="Get attacks for a campaign",
    description="Returns the list of attacks associated with a campaign.",
)
async def campaign_attacks_list(
    campaign_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[AttackSummary]:
    try:
        await _check_user_has_access_to_campaign(campaign_id, "read", db, current_user)
        return (
            await get_campaign_with_attack_summaries_service(campaign_id, db)
        ).attacks
    except CampaignNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
