"""
Control API attacks endpoints.

The Control API uses API key authentication and offset-based pagination.
All responses are JSON format.
Error responses must follow RFC9457 format.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.control_exceptions import (
    AttackNotFoundError as AttackNotFoundProblem,
)
from app.core.control_exceptions import (
    CampaignNotFoundError as CampaignNotFoundProblem,
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
    create_attack_service,
    delete_attack_service,
    estimate_attack_keyspace_and_complexity,
    get_attack_performance_summary_service,
    get_attack_service,
    pause_attack_service,
    resume_attack_service,
    start_attack_service,
    stop_attack_service,
    update_attack_service,
)
from app.core.services.campaign_service import CampaignNotFoundError
from app.core.state_machines import InvalidStateTransitionError
from app.db.session import get_db
from app.models.attack import Attack, AttackState
from app.models.attack_resource_file import AttackResourceFile
from app.models.campaign import Campaign
from app.models.user import User
from app.schemas.attack import (
    AttackCreate,
    AttackOut,
    AttackPerformanceSummary,
    AttackUpdate,
    EstimateAttackRequest,
)
from app.schemas.shared import OffsetPaginatedResponse

router = APIRouter(prefix="/attacks", tags=["Control - Attacks"])


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


async def _get_attack_with_access_check(
    attack_id: int, user: User, db: AsyncSession
) -> Attack:
    """Get attack and validate user has access to its campaign's project."""
    result = await db.execute(select(Attack).where(Attack.id == attack_id).options())
    attack = result.scalar_one_or_none()

    if not attack:
        raise AttackNotFoundProblem(detail=f"Attack with ID {attack_id} not found")

    # Get campaign to check project access
    campaign_result = await db.execute(
        select(Campaign).where(Campaign.id == attack.campaign_id)
    )
    campaign = campaign_result.scalar_one_or_none()

    if not campaign:
        raise CampaignNotFoundProblem(
            detail=f"Campaign with ID {attack.campaign_id} not found"
        )

    await _validate_project_access(user, campaign.project_id)
    return attack


async def _validate_campaign_access(
    campaign_id: int, user: User, db: AsyncSession
) -> Campaign:
    """Validate user has access to campaign's project and return campaign."""
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()

    if not campaign:
        raise CampaignNotFoundProblem(
            detail=f"Campaign with ID {campaign_id} not found"
        )

    await _validate_project_access(user, campaign.project_id)
    return campaign


# =============================================================================
# Validation and Estimation Schemas
# =============================================================================


class ResourceAvailability(BaseModel):
    """Resource availability status."""

    resource_id: Annotated[str, Field(description="Resource UUID")]
    status: Annotated[
        str, Field(description="Availability status: available, not_found, unavailable")
    ]
    name: Annotated[str | None, Field(None, description="Resource name if found")]

    model_config = ConfigDict(extra="forbid")


class AttackValidationResponse(BaseModel):
    """Response from attack validation."""

    valid: Annotated[bool, Field(description="Whether the attack config is valid")]
    errors: Annotated[list[str], Field(description="Validation errors")]
    warnings: Annotated[list[str], Field(description="Non-blocking warnings")]
    resource_availability: Annotated[
        list[ResourceAvailability], Field(description="Status of referenced resources")
    ]

    model_config = ConfigDict(extra="forbid")


class KeyspaceEstimateResponse(BaseModel):
    """Response from keyspace estimation."""

    keyspace: Annotated[int, Field(description="Estimated total keyspace")]
    complexity_score: Annotated[
        float, Field(description="Complexity score (higher = more complex)")
    ]

    model_config = ConfigDict(extra="forbid")


# =============================================================================
# CRUD Endpoints
# =============================================================================


@router.get(
    "",
    summary="List attacks",
    description="List attacks with offset-based pagination and filtering.",
)
async def list_attacks(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_control_user)],
    limit: Annotated[
        int, Query(ge=1, le=100, description="Number of items to return")
    ] = 20,
    offset: Annotated[int, Query(ge=0, description="Number of items to skip")] = 0,
    campaign_id: Annotated[
        int | None, Query(description="Filter by campaign ID")
    ] = None,
    state: Annotated[
        AttackState | None, Query(description="Filter by attack state")
    ] = None,
) -> OffsetPaginatedResponse[AttackOut]:
    """
    List attacks with offset-based pagination and filtering.

    Results are scoped to campaigns the user has access to.
    """
    try:
        # Get user's accessible projects
        accessible_projects = _get_accessible_projects(current_user)
        if not accessible_projects:
            raise ProjectAccessDeniedError(detail="User has no project access")

        # If campaign_id is specified, validate access
        if campaign_id is not None:
            await _validate_campaign_access(campaign_id, current_user, db)

        # Build query
        query = (
            select(Attack)
            .join(Campaign, Attack.campaign_id == Campaign.id)
            .where(Campaign.project_id.in_(accessible_projects))
        )

        # Apply filters
        if campaign_id is not None:
            query = query.where(Attack.campaign_id == campaign_id)
        if state is not None:
            query = query.where(Attack.state == state)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # Get paginated results
        query = query.order_by(Attack.position, Attack.id).offset(offset).limit(limit)
        result = await db.execute(query)
        attacks = result.scalars().all()

        items = [AttackOut.model_validate(a, from_attributes=True) for a in attacks]

        return OffsetPaginatedResponse(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
        )
    except ProjectAccessDeniedError:
        raise
    except CampaignNotFoundProblem:
        raise
    except Exception as e:
        raise InternalServerError(detail=f"Failed to list attacks: {e!s}") from e


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Create attack",
    description="Create a new attack in the specified campaign.",
)
async def create_attack(
    data: AttackCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_control_user)],
) -> AttackOut:
    """
    Create a new attack.

    The user must have access to the campaign's project.
    Referenced resources (wordlist, rules, masks) must exist.
    """
    try:
        # Validate campaign access
        if data.campaign_id is None:
            raise CampaignNotFoundProblem(detail="campaign_id is required")

        await _validate_campaign_access(data.campaign_id, current_user, db)

        # Create the attack using existing service
        return await create_attack_service(data, db)
    except (CampaignNotFoundProblem, ProjectAccessDeniedError):
        raise
    except CampaignNotFoundError as exc:
        raise CampaignNotFoundProblem(detail=str(exc)) from exc
    except Exception as e:
        raise InternalServerError(detail=f"Failed to create attack: {e!s}") from e


@router.get(
    "/{attack_id}",
    summary="Get attack",
    description="Get an attack by ID with full details.",
)
async def get_attack(
    attack_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_control_user)],
) -> AttackOut:
    """
    Get an attack by ID.

    The user must have access to the campaign's project.
    """
    try:
        # Validate access first
        await _get_attack_with_access_check(attack_id, current_user, db)
        attack = await get_attack_service(attack_id, db)
        return AttackOut.model_validate(attack, from_attributes=True)
    except (AttackNotFoundProblem, ProjectAccessDeniedError, CampaignNotFoundProblem):
        raise
    except Exception as e:
        raise InternalServerError(detail=f"Failed to get attack: {e!s}") from e


@router.patch(
    "/{attack_id}",
    summary="Update attack",
    description="Update attack configuration. Cannot update running attacks.",
)
async def update_attack(
    attack_id: int,
    data: AttackUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_control_user)],
) -> AttackOut:
    """
    Update attack configuration.

    Cannot update attacks that are currently running.
    The user must have access to the campaign's project.
    """
    try:
        # Validate access and get attack
        attack = await _get_attack_with_access_check(attack_id, current_user, db)

        # Prevent updating running attacks
        if attack.state == AttackState.RUNNING:
            raise InvalidResourceStateError(
                detail="Cannot update attack while it is running. Stop the attack first."
            )

        return await update_attack_service(attack_id, data, db)
    except (
        AttackNotFoundProblem,
        ProjectAccessDeniedError,
        CampaignNotFoundProblem,
        InvalidResourceStateError,
    ):
        raise
    except Exception as e:
        raise InternalServerError(detail=f"Failed to update attack: {e!s}") from e


@router.delete(
    "/{attack_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete attack",
    description="Delete an attack. Cannot delete running attacks.",
)
async def delete_attack(
    attack_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_control_user)],
) -> Response:
    """
    Delete an attack.

    Cannot delete attacks that are currently running.
    The user must have access to the campaign's project.
    """
    try:
        # Validate access and get attack
        attack = await _get_attack_with_access_check(attack_id, current_user, db)

        # Prevent deleting running attacks
        if attack.state == AttackState.RUNNING:
            raise InvalidResourceStateError(
                detail="Cannot delete attack while it is running. Stop the attack first."
            )

        await delete_attack_service(attack_id, db)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except (
        AttackNotFoundProblem,
        ProjectAccessDeniedError,
        CampaignNotFoundProblem,
        InvalidResourceStateError,
    ):
        raise
    except Exception as e:
        raise InternalServerError(detail=f"Failed to delete attack: {e!s}") from e


# =============================================================================
# Validation and Estimation Endpoints
# =============================================================================


@router.post(
    "/validate",
    summary="Validate attack configuration",
    description="Validate attack configuration before creation.",
)
async def validate_attack_config(
    data: AttackCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_control_user)],
) -> AttackValidationResponse:
    """
    Validate attack configuration.

    Checks:
    - Campaign exists and user has access
    - Referenced resources exist and are available
    - Attack mode is compatible with provided resources

    Returns validation result without creating the attack.
    """
    try:
        errors: list[str] = []
        warnings: list[str] = []
        resource_availability: list[ResourceAvailability] = []

        # Validate campaign access
        if data.campaign_id is None:
            errors.append("campaign_id is required")
        else:
            try:
                await _validate_campaign_access(data.campaign_id, current_user, db)
            except CampaignNotFoundProblem:
                errors.append(f"Campaign {data.campaign_id} not found")
            except ProjectAccessDeniedError:
                errors.append(f"No access to campaign {data.campaign_id}")

        # Check wordlist if specified
        if data.word_list_id is not None:
            result = await db.execute(
                select(AttackResourceFile).where(
                    AttackResourceFile.id == data.word_list_id
                )
            )
            resource = result.scalar_one_or_none()
            if resource is None:
                resource_availability.append(
                    ResourceAvailability(
                        resource_id=str(data.word_list_id),
                        status="not_found",
                        name=None,
                    )
                )
                errors.append(f"Wordlist {data.word_list_id} not found")
            elif not resource.is_uploaded:
                resource_availability.append(
                    ResourceAvailability(
                        resource_id=str(data.word_list_id),
                        status="unavailable",
                        name=resource.file_name,
                    )
                )
                warnings.append(f"Wordlist '{resource.file_name}' is not yet uploaded")
            else:
                resource_availability.append(
                    ResourceAvailability(
                        resource_id=str(data.word_list_id),
                        status="available",
                        name=resource.file_name,
                    )
                )

        # Check rule list if specified
        if data.rule_list_id is not None:
            result = await db.execute(
                select(AttackResourceFile).where(
                    AttackResourceFile.id == data.rule_list_id
                )
            )
            resource = result.scalar_one_or_none()
            if resource is None:
                resource_availability.append(
                    ResourceAvailability(
                        resource_id=str(data.rule_list_id),
                        status="not_found",
                        name=None,
                    )
                )
                errors.append(f"Rule list {data.rule_list_id} not found")
            elif not resource.is_uploaded:
                resource_availability.append(
                    ResourceAvailability(
                        resource_id=str(data.rule_list_id),
                        status="unavailable",
                        name=resource.file_name,
                    )
                )
                warnings.append(f"Rule list '{resource.file_name}' is not yet uploaded")
            else:
                resource_availability.append(
                    ResourceAvailability(
                        resource_id=str(data.rule_list_id),
                        status="available",
                        name=resource.file_name,
                    )
                )

        # Check mask list if specified
        if data.mask_list_id is not None:
            result = await db.execute(
                select(AttackResourceFile).where(
                    AttackResourceFile.id == data.mask_list_id
                )
            )
            resource = result.scalar_one_or_none()
            if resource is None:
                resource_availability.append(
                    ResourceAvailability(
                        resource_id=str(data.mask_list_id),
                        status="not_found",
                        name=None,
                    )
                )
                errors.append(f"Mask list {data.mask_list_id} not found")
            elif not resource.is_uploaded:
                resource_availability.append(
                    ResourceAvailability(
                        resource_id=str(data.mask_list_id),
                        status="unavailable",
                        name=resource.file_name,
                    )
                )
                warnings.append(f"Mask list '{resource.file_name}' is not yet uploaded")
            else:
                resource_availability.append(
                    ResourceAvailability(
                        resource_id=str(data.mask_list_id),
                        status="available",
                        name=resource.file_name,
                    )
                )

        return AttackValidationResponse(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            resource_availability=resource_availability,
        )
    except ProjectAccessDeniedError:
        raise
    except Exception as e:
        raise InternalServerError(detail=f"Failed to validate attack: {e!s}") from e


@router.post(
    "/estimate",
    summary="Estimate attack keyspace",
    description="Estimate keyspace and complexity for an attack configuration.",
)
async def estimate_keyspace(
    data: EstimateAttackRequest,
    _db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: Annotated[User, Depends(get_current_control_user)],
) -> KeyspaceEstimateResponse:
    """
    Estimate attack keyspace and complexity.

    Returns keyspace (number of password candidates) and complexity score.
    """
    try:
        result = await estimate_attack_keyspace_and_complexity(data)

        return KeyspaceEstimateResponse(
            keyspace=result.keyspace,
            complexity_score=result.complexity_score,
        )
    except Exception as e:
        raise InternalServerError(detail=f"Failed to estimate keyspace: {e!s}") from e


# =============================================================================
# Lifecycle Endpoints
# =============================================================================


@router.post(
    "/{attack_id}/start",
    summary="Start attack",
    description="Start an attack, transitioning it from PENDING to RUNNING.",
)
async def start_attack(
    attack_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_control_user)],
) -> AttackOut:
    """
    Start an attack.

    The attack must be in PENDING state.
    The user must have access to the campaign's project.
    """
    try:
        await _get_attack_with_access_check(attack_id, current_user, db)
        return await start_attack_service(attack_id, db)
    except (
        AttackNotFoundProblem,
        ProjectAccessDeniedError,
        CampaignNotFoundProblem,
    ):
        raise
    except InvalidStateTransitionError as e:
        raise InvalidStateTransitionProblem(detail=str(e)) from e
    except Exception as e:
        raise InternalServerError(detail=f"Failed to start attack: {e!s}") from e


@router.post(
    "/{attack_id}/stop",
    summary="Stop attack",
    description="Stop an attack, transitioning it to ABANDONED state.",
)
async def stop_attack(
    attack_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_control_user)],
) -> AttackOut:
    """
    Stop an attack.

    The attack must be in RUNNING or PAUSED state.
    The user must have access to the campaign's project.
    """
    try:
        await _get_attack_with_access_check(attack_id, current_user, db)
        return await stop_attack_service(attack_id, db)
    except (
        AttackNotFoundProblem,
        ProjectAccessDeniedError,
        CampaignNotFoundProblem,
    ):
        raise
    except InvalidStateTransitionError as e:
        raise InvalidStateTransitionProblem(detail=str(e)) from e
    except Exception as e:
        raise InternalServerError(detail=f"Failed to stop attack: {e!s}") from e


@router.post(
    "/{attack_id}/pause",
    summary="Pause attack",
    description="Pause a running attack.",
)
async def pause_attack(
    attack_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_control_user)],
) -> AttackOut:
    """
    Pause an attack.

    The attack must be in RUNNING state.
    The user must have access to the campaign's project.
    """
    try:
        await _get_attack_with_access_check(attack_id, current_user, db)
        return await pause_attack_service(attack_id, db)
    except (
        AttackNotFoundProblem,
        ProjectAccessDeniedError,
        CampaignNotFoundProblem,
    ):
        raise
    except InvalidStateTransitionError as e:
        raise InvalidStateTransitionProblem(detail=str(e)) from e
    except Exception as e:
        raise InternalServerError(detail=f"Failed to pause attack: {e!s}") from e


@router.post(
    "/{attack_id}/resume",
    summary="Resume attack",
    description="Resume a paused attack.",
)
async def resume_attack(
    attack_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_control_user)],
) -> AttackOut:
    """
    Resume an attack.

    The attack must be in PAUSED state.
    The user must have access to the campaign's project.
    """
    try:
        await _get_attack_with_access_check(attack_id, current_user, db)
        return await resume_attack_service(attack_id, db)
    except (
        AttackNotFoundProblem,
        ProjectAccessDeniedError,
        CampaignNotFoundProblem,
    ):
        raise
    except InvalidStateTransitionError as e:
        raise InvalidStateTransitionProblem(detail=str(e)) from e
    except Exception as e:
        raise InternalServerError(detail=f"Failed to resume attack: {e!s}") from e


# =============================================================================
# Metrics Endpoint
# =============================================================================


@router.get(
    "/{attack_id}/metrics",
    summary="Get attack metrics",
    description="Get performance metrics for an attack.",
)
async def get_attack_metrics(
    attack_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_control_user)],
) -> AttackPerformanceSummary:
    """
    Get attack performance metrics.

    Returns hash rate, progress, ETA, crack count, and task information.
    The user must have access to the campaign's project.
    """
    try:
        await _get_attack_with_access_check(attack_id, current_user, db)
        return await get_attack_performance_summary_service(attack_id, db)
    except (
        AttackNotFoundProblem,
        ProjectAccessDeniedError,
        CampaignNotFoundProblem,
    ):
        raise
    except Exception as e:
        raise InternalServerError(detail=f"Failed to get attack metrics: {e!s}") from e
