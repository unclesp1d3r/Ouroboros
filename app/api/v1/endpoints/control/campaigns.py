"""
Control API campaigns endpoints.

The Control API uses API key authentication and offset-based pagination.
All responses are JSON format.
Error responses must follow RFC9457 format.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.control_exceptions import (
    AttackNotFoundError as AttackNotFoundProblem,
)
from app.core.control_exceptions import (
    CampaignNotFoundError as CampaignNotFoundProblem,
)
from app.core.control_exceptions import (
    HashListNotFoundError as HashListNotFoundProblem,
)
from app.core.control_exceptions import (
    InternalServerError,
    InvalidResourceStateError,
    ProjectAccessDeniedError,
)
from app.core.control_exceptions import (
    InvalidStateTransitionError as InvalidStateTransitionProblem,
)
from app.core.deps import get_current_control_user
from app.core.services.attack_service import (
    AttackNotFoundError,
    reorder_attacks_service,
)
from app.core.services.campaign_service import (
    CampaignNotFoundError,
    archive_campaign_service,
    create_campaign_service,
    delete_campaign_service,
    get_campaign_service,
    list_campaigns_service,
    pause_campaign_service,
    resume_campaign_service,
    start_campaign_service,
    stop_campaign_service,
    unarchive_campaign_service,
    update_campaign_service,
)
from app.core.state_machines import (
    InvalidStateTransitionError as StateMachineTransitionError,
)
from app.db.session import get_db
from app.models.agent import AgentState
from app.models.campaign import Campaign, CampaignState
from app.models.hash_list import HashList
from app.models.user import User
from app.schemas.attack import AttackOut
from app.schemas.campaign import CampaignCreate, CampaignRead, CampaignUpdate
from app.schemas.shared import OffsetPaginatedResponse

router = APIRouter(prefix="/campaigns", tags=["Control - Campaigns"])


# =============================================================================
# Reorder Request Schema
# =============================================================================


class AttackOrderItem(BaseModel):
    """Single attack order item."""

    attack_id: Annotated[int, Field(description="Attack ID")]
    priority: Annotated[
        int, Field(description="Priority/position (lower is higher priority)")
    ]

    model_config = ConfigDict(extra="forbid")


class ReorderAttacksRequest(BaseModel):
    """Request to reorder attacks within a campaign."""

    attack_order: Annotated[
        list[AttackOrderItem],
        Field(description="List of attack IDs with their new priorities"),
    ]

    model_config = ConfigDict(extra="forbid")


def _get_accessible_projects(user: User) -> list[int]:
    """Get list of project IDs the user has access to."""
    if user.project_associations:
        return [assoc.project_id for assoc in user.project_associations]
    return []


async def _validate_project_access(
    user: User,
    project_id: int,
) -> None:
    """Validate that user has access to the specified project."""
    accessible = _get_accessible_projects(user)
    if not accessible:
        raise ProjectAccessDeniedError(detail="User has no project access")
    if project_id not in accessible:
        raise ProjectAccessDeniedError(
            detail=f"User does not have access to project {project_id}"
        )


async def _validate_campaign_access(
    campaign_id: int, user: User, db: AsyncSession
) -> Campaign:
    """Validate that user has access to the campaign and return it."""
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()

    if not campaign:
        raise CampaignNotFoundProblem(
            detail=f"Campaign with ID {campaign_id} not found"
        )

    await _validate_project_access(user, campaign.project_id)
    return campaign


# =============================================================================
# Validation schemas
# =============================================================================


class ValidationError(BaseModel):
    """A validation error with type and detail."""

    type: Annotated[str, Field(description="Error type identifier")]
    detail: Annotated[str, Field(description="Human-readable error description")]
    resource_id: Annotated[
        int | None, Field(None, description="ID of related resource if applicable")
    ]

    model_config = ConfigDict(extra="forbid")


class ValidationWarning(BaseModel):
    """A validation warning (non-blocking)."""

    type: Annotated[str, Field(description="Warning type identifier")]
    detail: Annotated[str, Field(description="Human-readable warning description")]

    model_config = ConfigDict(extra="forbid")


class ValidationResponse(BaseModel):
    """Response from campaign pre-flight validation."""

    valid: Annotated[bool, Field(description="Whether the campaign is valid to start")]
    errors: Annotated[
        list[ValidationError], Field(description="Blocking validation errors")
    ]
    warnings: Annotated[
        list[ValidationWarning], Field(description="Non-blocking warnings")
    ]

    model_config = ConfigDict(extra="forbid")


@router.get(
    "",
    summary="List campaigns",
    description="List campaigns with offset-based pagination and filtering. Supports project scoping based on user permissions.",
)
async def list_campaigns(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_control_user)],
    limit: Annotated[
        int, Query(ge=1, le=100, description="Number of items to return")
    ] = 10,
    offset: Annotated[int, Query(ge=0, description="Number of items to skip")] = 0,
    name: Annotated[
        str | None,
        Query(description="Filter campaigns by name (case-insensitive partial match)"),
    ] = None,
    project_id: Annotated[
        int | None, Query(description="Filter campaigns by project ID")
    ] = None,
) -> OffsetPaginatedResponse[CampaignRead]:
    """
    List campaigns with offset-based pagination and filtering.

    Access is scoped to projects the user has access to. If project_id is specified,
    the user must have access to that specific project.

    TODO: Implement API key authentication as specified in the Control API requirements.
    """
    try:
        # Get user's accessible projects - inline logic instead of importing control_access
        accessible_projects = (
            [assoc.project_id for assoc in current_user.project_associations]
            if current_user.project_associations
            else []
        )

        if not accessible_projects:
            raise ProjectAccessDeniedError(detail="User has no project access")

        # If project_id is specified, check if user has access to it
        if project_id is not None:
            if project_id not in accessible_projects:
                raise ProjectAccessDeniedError(
                    detail=f"User does not have access to project {project_id}"
                )
            # Use single project_id for filtering
            campaigns, total = await list_campaigns_service(
                db=db,
                skip=offset,
                limit=limit,
                name_filter=name,
                project_id=project_id,
            )
        else:
            # Use multiple project_ids for filtering (much more efficient)
            campaigns, total = await list_campaigns_service(
                db=db,
                skip=offset,
                limit=limit,
                name_filter=name,
                project_ids=accessible_projects,
            )

        # Convert to offset-based paginated response format
        return OffsetPaginatedResponse(
            items=campaigns,
            total=total,
            limit=limit,
            offset=offset,
        )
    except ProjectAccessDeniedError:
        raise  # Re-raise project access errors
    except Exception as e:
        raise InternalServerError(detail=f"Failed to list campaigns: {e!s}") from e


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Create campaign",
    description="Create a new campaign in the specified project.",
)
async def create_campaign(
    data: CampaignCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_control_user)],
) -> CampaignRead:
    """
    Create a new campaign.

    The user must have access to the specified project.
    The hash list must exist and be accessible.
    """
    try:
        await _validate_project_access(current_user, data.project_id)

        # Validate hash list exists
        result = await db.execute(
            select(HashList).where(HashList.id == data.hash_list_id)
        )
        hash_list = result.scalar_one_or_none()
        if not hash_list:
            raise HashListNotFoundProblem(
                detail=f"Hash list with ID {data.hash_list_id} not found"
            )

        # Check hash list belongs to the same project or is global
        if hash_list.project_id is not None and hash_list.project_id != data.project_id:
            raise ProjectAccessDeniedError(
                detail=f"Hash list {data.hash_list_id} does not belong to project {data.project_id}"
            )

        return await create_campaign_service(data, db)
    except (ProjectAccessDeniedError, HashListNotFoundProblem):
        raise
    except Exception as e:
        raise InternalServerError(detail=f"Failed to create campaign: {e!s}") from e


@router.get(
    "/{campaign_id}",
    summary="Get campaign",
    description="Get a campaign by ID with full details.",
)
async def get_campaign(
    campaign_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_control_user)],
) -> CampaignRead:
    """
    Get a campaign by ID.

    The user must have access to the project containing the campaign.
    """
    try:
        # Validate access first
        await _validate_campaign_access(campaign_id, current_user, db)
        return await get_campaign_service(campaign_id, db)
    except (CampaignNotFoundProblem, ProjectAccessDeniedError):
        raise
    except CampaignNotFoundError as exc:
        raise CampaignNotFoundProblem(
            detail=f"Campaign with ID {campaign_id} not found"
        ) from exc
    except Exception as e:
        raise InternalServerError(detail=f"Failed to get campaign: {e!s}") from e


@router.patch(
    "/{campaign_id}",
    summary="Update campaign",
    description="Update campaign metadata (name, description, priority).",
)
async def update_campaign(
    campaign_id: int,
    data: CampaignUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_control_user)],
) -> CampaignRead:
    """
    Update campaign metadata.

    Only name, description, and priority can be updated.
    The user must have access to the project containing the campaign.
    """
    try:
        # Validate access first
        await _validate_campaign_access(campaign_id, current_user, db)
        return await update_campaign_service(campaign_id, data, db)
    except (CampaignNotFoundProblem, ProjectAccessDeniedError):
        raise
    except CampaignNotFoundError as exc:
        raise CampaignNotFoundProblem(
            detail=f"Campaign with ID {campaign_id} not found"
        ) from exc
    except Exception as e:
        raise InternalServerError(detail=f"Failed to update campaign: {e!s}") from e


@router.delete(
    "/{campaign_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete campaign",
    description="Delete a campaign. Cannot delete running or active campaigns.",
)
async def delete_campaign(
    campaign_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_control_user)],
) -> Response:
    """
    Delete a campaign.

    The campaign must be in draft, completed, archived, or error state.
    Running or paused campaigns cannot be deleted.
    The user must have access to the project containing the campaign.
    """
    try:
        # Validate access and get campaign
        campaign = await _validate_campaign_access(campaign_id, current_user, db)

        # Check campaign state - only allow deletion in certain states
        allowed_states = {
            CampaignState.DRAFT,
            CampaignState.COMPLETED,
            CampaignState.ARCHIVED,
            CampaignState.ERROR,
        }
        if campaign.state not in allowed_states:
            raise InvalidResourceStateError(
                detail=f"Cannot delete campaign in '{campaign.state.value}' state. "
                f"Campaign must be in one of: {', '.join(s.value for s in allowed_states)}"
            )

        await delete_campaign_service(campaign_id, db)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except (
        CampaignNotFoundProblem,
        ProjectAccessDeniedError,
        InvalidResourceStateError,
    ):
        raise
    except CampaignNotFoundError as exc:
        raise CampaignNotFoundProblem(
            detail=f"Campaign with ID {campaign_id} not found"
        ) from exc
    except Exception as e:
        raise InternalServerError(detail=f"Failed to delete campaign: {e!s}") from e


@router.post(
    "/{campaign_id}/validate",
    summary="Validate campaign",
    description="Run pre-flight validation to check if campaign is ready to start.",
)
async def validate_campaign(
    campaign_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_control_user)],
) -> ValidationResponse:
    """
    Run pre-flight validation for a campaign.

    Checks:
    - Hash list exists and is accessible
    - Campaign has at least one attack
    - All required resources (wordlists, rules) are available
    - Active agents are available for the project

    Returns validation result with errors (blocking) and warnings (non-blocking).
    """
    try:
        # Validate access and get campaign
        campaign = await _validate_campaign_access(campaign_id, current_user, db)

        errors: list[ValidationError] = []
        warnings: list[ValidationWarning] = []

        # Check hash list exists
        result = await db.execute(
            select(HashList).where(HashList.id == campaign.hash_list_id)
        )
        hash_list = result.scalar_one_or_none()
        if not hash_list:
            errors.append(
                ValidationError(
                    type="missing_hash_list",
                    detail=f"Hash list {campaign.hash_list_id} not found",
                    resource_id=campaign.hash_list_id,
                )
            )
        elif hash_list.is_unavailable:
            errors.append(
                ValidationError(
                    type="unavailable_hash_list",
                    detail=f"Hash list '{hash_list.name}' is marked as unavailable",
                    resource_id=campaign.hash_list_id,
                )
            )

        # Check campaign has attacks (load relationship)
        from app.models.attack import Attack

        attacks_result = await db.execute(
            select(Attack).where(Attack.campaign_id == campaign_id)
        )
        attacks = attacks_result.scalars().all()
        if not attacks:
            errors.append(
                ValidationError(
                    type="no_attacks",
                    detail="Campaign has no attacks configured",
                    resource_id=None,
                )
            )

        # Check for active agents in the project
        # Agents are associated with projects via project_agents association table
        from app.models.project import Project

        project_result = await db.execute(
            select(Project)
            .where(Project.id == campaign.project_id)
            .options()  # Use selectin from relationship definition
        )
        project = project_result.scalar_one_or_none()

        # Check if there are any active (enabled) agents for this project
        active_agents = []
        if project and project.agents:
            active_agents = [
                agent
                for agent in project.agents
                if agent.enabled and agent.state == AgentState.active
            ]

        if not active_agents:
            warnings.append(
                ValidationWarning(
                    type="no_agents",
                    detail=f"No active agents available for project {campaign.project_id}",
                )
            )

        # Check campaign state - should be in draft to start
        if campaign.state != CampaignState.DRAFT:
            if campaign.state == CampaignState.ACTIVE:
                warnings.append(
                    ValidationWarning(
                        type="already_active",
                        detail="Campaign is already active",
                    )
                )
            elif campaign.state == CampaignState.PAUSED:
                warnings.append(
                    ValidationWarning(
                        type="paused",
                        detail="Campaign is paused and can be resumed",
                    )
                )
            elif campaign.state in (CampaignState.COMPLETED, CampaignState.ARCHIVED):
                errors.append(
                    ValidationError(
                        type="invalid_state",
                        detail=f"Campaign is in '{campaign.state.value}' state and cannot be started",
                        resource_id=None,
                    )
                )

        return ValidationResponse(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )
    except (CampaignNotFoundProblem, ProjectAccessDeniedError):
        raise
    except Exception as e:
        raise InternalServerError(detail=f"Failed to validate campaign: {e!s}") from e


# =============================================================================
# Lifecycle Actions
# =============================================================================


@router.post(
    "/{campaign_id}/start",
    summary="Start campaign",
    description="Start a campaign. Campaign must be in draft state.",
)
async def start_campaign(
    campaign_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_control_user)],
) -> CampaignRead:
    """
    Start a campaign.

    The campaign must be in draft state. Starting will transition it to active state.
    The user must have access to the project containing the campaign.
    """
    try:
        # Validate access first
        await _validate_campaign_access(campaign_id, current_user, db)
        return await start_campaign_service(campaign_id, db)
    except (CampaignNotFoundProblem, ProjectAccessDeniedError):
        raise
    except CampaignNotFoundError as exc:
        raise CampaignNotFoundProblem(
            detail=f"Campaign with ID {campaign_id} not found"
        ) from exc
    except StateMachineTransitionError as exc:
        raise InvalidStateTransitionProblem(
            detail=f"Cannot start campaign: {exc.message}"
        ) from exc
    except Exception as e:
        raise InternalServerError(detail=f"Failed to start campaign: {e!s}") from e


@router.post(
    "/{campaign_id}/stop",
    summary="Stop campaign",
    description="Stop a running campaign. Campaign returns to draft state and can be restarted.",
)
async def stop_campaign(
    campaign_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_control_user)],
) -> CampaignRead:
    """
    Stop a running campaign.

    The campaign must be in active state. Stopping will transition it to draft state.
    Running tasks will be allowed to complete gracefully.
    The user must have access to the project containing the campaign.
    """
    try:
        # Validate access first
        await _validate_campaign_access(campaign_id, current_user, db)
        return await stop_campaign_service(campaign_id, db)
    except (CampaignNotFoundProblem, ProjectAccessDeniedError):
        raise
    except CampaignNotFoundError as exc:
        raise CampaignNotFoundProblem(
            detail=f"Campaign with ID {campaign_id} not found"
        ) from exc
    except StateMachineTransitionError as exc:
        raise InvalidStateTransitionProblem(
            detail=f"Cannot stop campaign: {exc.message}"
        ) from exc
    except Exception as e:
        raise InternalServerError(detail=f"Failed to stop campaign: {e!s}") from e


@router.post(
    "/{campaign_id}/pause",
    summary="Pause campaign",
    description="Pause a running campaign. Campaign can be resumed later.",
)
async def pause_campaign(
    campaign_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_control_user)],
) -> CampaignRead:
    """
    Pause a running campaign.

    The campaign must be in active state. Pausing will transition it to paused state.
    The user must have access to the project containing the campaign.
    """
    try:
        # Validate access first
        await _validate_campaign_access(campaign_id, current_user, db)
        return await pause_campaign_service(campaign_id, db)
    except (CampaignNotFoundProblem, ProjectAccessDeniedError):
        raise
    except CampaignNotFoundError as exc:
        raise CampaignNotFoundProblem(
            detail=f"Campaign with ID {campaign_id} not found"
        ) from exc
    except StateMachineTransitionError as exc:
        raise InvalidStateTransitionProblem(
            detail=f"Cannot pause campaign: {exc.message}"
        ) from exc
    except Exception as e:
        raise InternalServerError(detail=f"Failed to pause campaign: {e!s}") from e


@router.post(
    "/{campaign_id}/resume",
    summary="Resume campaign",
    description="Resume a paused campaign.",
)
async def resume_campaign(
    campaign_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_control_user)],
) -> CampaignRead:
    """
    Resume a paused campaign.

    The campaign must be in paused state. Resuming will transition it to active state.
    The user must have access to the project containing the campaign.
    """
    try:
        # Validate access first
        await _validate_campaign_access(campaign_id, current_user, db)
        return await resume_campaign_service(campaign_id, db)
    except (CampaignNotFoundProblem, ProjectAccessDeniedError):
        raise
    except CampaignNotFoundError as exc:
        raise CampaignNotFoundProblem(
            detail=f"Campaign with ID {campaign_id} not found"
        ) from exc
    except StateMachineTransitionError as exc:
        raise InvalidStateTransitionProblem(
            detail=f"Cannot resume campaign: {exc.message}"
        ) from exc
    except Exception as e:
        raise InternalServerError(detail=f"Failed to resume campaign: {e!s}") from e


@router.post(
    "/{campaign_id}/archive",
    summary="Archive campaign",
    description="Archive a campaign. Archived campaigns are hidden from default views.",
)
async def archive_campaign(
    campaign_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_control_user)],
) -> CampaignRead:
    """
    Archive a campaign.

    Campaigns can be archived from draft, active, paused, or completed states.
    Archived campaigns can be unarchived later.
    The user must have access to the project containing the campaign.
    """
    try:
        # Validate access first
        await _validate_campaign_access(campaign_id, current_user, db)
        return await archive_campaign_service(campaign_id, db)
    except (CampaignNotFoundProblem, ProjectAccessDeniedError):
        raise
    except CampaignNotFoundError as exc:
        raise CampaignNotFoundProblem(
            detail=f"Campaign with ID {campaign_id} not found"
        ) from exc
    except StateMachineTransitionError as exc:
        raise InvalidStateTransitionProblem(
            detail=f"Cannot archive campaign: {exc.message}"
        ) from exc
    except Exception as e:
        raise InternalServerError(detail=f"Failed to archive campaign: {e!s}") from e


@router.post(
    "/{campaign_id}/unarchive",
    summary="Unarchive campaign",
    description="Unarchive a campaign. Campaign returns to draft state.",
)
async def unarchive_campaign(
    campaign_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_control_user)],
) -> CampaignRead:
    """
    Unarchive a campaign.

    The campaign must be in archived state. Unarchiving will transition it to draft state.
    The user must have access to the project containing the campaign.
    """
    try:
        # Validate access first
        await _validate_campaign_access(campaign_id, current_user, db)
        return await unarchive_campaign_service(campaign_id, db)
    except (CampaignNotFoundProblem, ProjectAccessDeniedError):
        raise
    except CampaignNotFoundError as exc:
        raise CampaignNotFoundProblem(
            detail=f"Campaign with ID {campaign_id} not found"
        ) from exc
    except StateMachineTransitionError as exc:
        raise InvalidStateTransitionProblem(
            detail=f"Cannot unarchive campaign: {exc.message}"
        ) from exc
    except Exception as e:
        raise InternalServerError(detail=f"Failed to unarchive campaign: {e!s}") from e


# =============================================================================
# Attack Reordering Endpoint
# =============================================================================


@router.post(
    "/{campaign_id}/attacks/reorder",
    summary="Reorder attacks",
    description="Reorder attacks within a campaign by setting their priorities.",
)
async def reorder_attacks(
    campaign_id: int,
    data: ReorderAttacksRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_control_user)],
) -> list[AttackOut]:
    """
    Reorder attacks within a campaign.

    Updates the priority/position of attacks within a campaign.
    Lower priority numbers are executed first.
    The user must have access to the project containing the campaign.
    """
    try:
        # Validate access first
        await _validate_campaign_access(campaign_id, current_user, db)

        # Convert request to list of dicts for the service
        attack_order = [
            {"attack_id": item.attack_id, "priority": item.priority}
            for item in data.attack_order
        ]

        return await reorder_attacks_service(campaign_id, attack_order, db)
    except (CampaignNotFoundProblem, ProjectAccessDeniedError):
        raise
    except CampaignNotFoundError as exc:
        raise CampaignNotFoundProblem(
            detail=f"Campaign with ID {campaign_id} not found"
        ) from exc
    except AttackNotFoundError as exc:
        raise AttackNotFoundProblem(detail=str(exc)) from exc
    except Exception as e:
        raise InternalServerError(detail=f"Failed to reorder attacks: {e!s}") from e
