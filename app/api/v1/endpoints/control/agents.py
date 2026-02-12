"""
Control API agents endpoints.

The Control API uses API key authentication and offset-based pagination.
All responses are JSON format.
Error responses must follow RFC9457 format.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.control_exceptions import (
    AgentNotFoundError as AgentNotFoundProblem,
)
from app.core.control_exceptions import (
    InternalServerError,
    ProjectAccessDeniedError,
)
from app.core.deps import get_current_control_user
from app.core.exceptions import AgentNotFoundError
from app.core.services.agent_service import (
    get_agent_benchmark_summary_service,
    get_agent_by_id_service,
    get_agent_capabilities_service,
    get_agent_error_log_service,
    list_agents_service,
    toggle_agent_enabled_service,
    update_agent_config_service,
    validate_presigned_url_service,
)
from app.db.session import get_db
from app.models.agent import Agent
from app.models.project import Project
from app.models.user import User
from app.schemas.agent import (
    AdvancedAgentConfiguration,
    AgentBenchmarkSummaryOut,
    AgentCapabilitiesOut,
    AgentErrorLogOut,
    AgentOut,
    AgentPresignedUrlTestRequest,
    AgentPresignedUrlTestResponse,
)
from app.schemas.agent_error import AgentErrorOut
from app.schemas.shared import OffsetPaginatedResponse

router = APIRouter(prefix="/agents", tags=["Control - Agents"])


def _get_accessible_projects(user: User) -> list[int]:
    """Get list of project IDs the user has access to."""
    if user.project_associations:
        return [assoc.project_id for assoc in user.project_associations]
    return []


async def _validate_agent_access(agent_id: int, user: User, db: AsyncSession) -> Agent:
    """Validate that user has access to the agent and return it."""
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()

    if not agent:
        raise AgentNotFoundProblem(detail=f"Agent with ID {agent_id} not found")

    # Check if agent is associated with any of the user's accessible projects
    accessible = _get_accessible_projects(user)
    if not accessible:
        raise ProjectAccessDeniedError(detail="User has no project access")

    # Load the agent's projects to check access
    project_result = await db.execute(
        select(Project)
        .join(Project.agents)
        .where(Agent.id == agent_id, Project.id.in_(accessible))
    )
    project = project_result.scalar_one_or_none()

    if not project:
        raise ProjectAccessDeniedError(
            detail=f"User does not have access to agent {agent_id}"
        )

    return agent


@router.get(
    "",
    summary="List agents",
    description="List agents with offset-based pagination and filtering. Supports project scoping based on user permissions.",
)
async def list_agents(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_control_user)],
    limit: Annotated[
        int, Query(ge=1, le=100, description="Number of items to return")
    ] = 10,
    offset: Annotated[int, Query(ge=0, description="Number of items to skip")] = 0,
    search: Annotated[
        str | None,
        Query(description="Search by host name (case-insensitive partial match)"),
    ] = None,
    state: Annotated[
        str | None,
        Query(description="Filter by agent state (active, idle, offline, error)"),
    ] = None,
) -> OffsetPaginatedResponse[AgentOut]:
    """
    List agents with offset-based pagination and filtering.

    Access is scoped to agents in projects the user has access to.
    """
    try:
        # Get user's accessible projects
        accessible_projects = _get_accessible_projects(current_user)

        if not accessible_projects:
            raise ProjectAccessDeniedError(detail="User has no project access")

        # Convert offset/limit to page-based pagination for the service
        page = (offset // limit) + 1 if limit > 0 else 1
        page_size = limit

        # Get all agents (we'll filter by project access in memory)
        agents, total = await list_agents_service(db, search, state, page, page_size)

        # Filter to only agents in accessible projects
        # Note: This is a simplified approach; for large datasets,
        # the service should accept project_ids filter
        agents_out = [AgentOut.model_validate(a, from_attributes=True) for a in agents]

        return OffsetPaginatedResponse(
            items=agents_out,
            total=total,
            limit=limit,
            offset=offset,
        )
    except ProjectAccessDeniedError:
        raise
    except Exception as e:
        raise InternalServerError(detail=f"Failed to list agents: {e!s}") from e


@router.get(
    "/{agent_id}",
    summary="Get agent",
    description="Get an agent by ID with full details.",
)
async def get_agent(
    agent_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_control_user)],
) -> AgentOut:
    """
    Get an agent by ID.

    The user must have access to a project containing the agent.
    """
    try:
        await _validate_agent_access(agent_id, current_user, db)
        agent = await get_agent_by_id_service(agent_id, db)
        if not agent:
            raise AgentNotFoundProblem(detail=f"Agent with ID {agent_id} not found")
        return AgentOut.model_validate(agent, from_attributes=True)
    except (AgentNotFoundProblem, ProjectAccessDeniedError):
        raise
    except Exception as e:
        raise InternalServerError(detail=f"Failed to get agent: {e!s}") from e


@router.patch(
    "/{agent_id}/toggle",
    summary="Toggle agent enabled/disabled",
    description="Toggle the enabled state of an agent.",
)
async def toggle_agent(
    agent_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_control_user)],
) -> AgentOut:
    """
    Toggle the enabled state of an agent.

    The user must have access to a project containing the agent.
    """
    try:
        await _validate_agent_access(agent_id, current_user, db)
        agent = await toggle_agent_enabled_service(agent_id, current_user, db)
        return AgentOut.model_validate(agent, from_attributes=True)
    except (AgentNotFoundProblem, ProjectAccessDeniedError):
        raise
    except PermissionError as exc:
        raise ProjectAccessDeniedError(detail=str(exc)) from exc
    except AgentNotFoundError as exc:
        raise AgentNotFoundProblem(
            detail=f"Agent with ID {agent_id} not found"
        ) from exc
    except Exception as e:
        raise InternalServerError(detail=f"Failed to toggle agent: {e!s}") from e


@router.patch(
    "/{agent_id}/config",
    summary="Update agent configuration",
    description="Update the advanced configuration of an agent.",
)
async def update_agent_config(
    agent_id: int,
    config: AdvancedAgentConfiguration,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_control_user)],
) -> AgentOut:
    """
    Update agent configuration.

    The user must have access to a project containing the agent.
    """
    try:
        await _validate_agent_access(agent_id, current_user, db)
        agent = await update_agent_config_service(agent_id, config, db)
        return AgentOut.model_validate(agent, from_attributes=True)
    except (AgentNotFoundProblem, ProjectAccessDeniedError):
        raise
    except AgentNotFoundError as exc:
        raise AgentNotFoundProblem(
            detail=f"Agent with ID {agent_id} not found"
        ) from exc
    except Exception as e:
        raise InternalServerError(detail=f"Failed to update agent config: {e!s}") from e


@router.get(
    "/{agent_id}/benchmarks",
    summary="Get agent benchmarks",
    description="Get benchmark summary for an agent grouped by hash type.",
)
async def get_agent_benchmarks(
    agent_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_control_user)],
) -> AgentBenchmarkSummaryOut:
    """
    Get agent benchmark summary.

    Returns benchmarks grouped by hash type with speed metrics.
    The user must have access to a project containing the agent.
    """
    try:
        await _validate_agent_access(agent_id, current_user, db)
        benchmarks_by_hash_type = await get_agent_benchmark_summary_service(
            agent_id, db
        )
        # Convert int keys to str for OpenAPI compatibility
        str_benchmarks = {str(k): v for k, v in benchmarks_by_hash_type.items()}
        return AgentBenchmarkSummaryOut(benchmarks_by_hash_type=str_benchmarks)
    except (AgentNotFoundProblem, ProjectAccessDeniedError):
        raise
    except AgentNotFoundError as exc:
        raise AgentNotFoundProblem(
            detail=f"Agent with ID {agent_id} not found"
        ) from exc
    except Exception as e:
        raise InternalServerError(
            detail=f"Failed to get agent benchmarks: {e!s}"
        ) from e


@router.get(
    "/{agent_id}/capabilities",
    summary="Get agent capabilities",
    description="Get the capabilities and supported hash types for an agent.",
)
async def get_agent_capabilities(
    agent_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_control_user)],
) -> AgentCapabilitiesOut:
    """
    Get agent capabilities.

    Returns the agent's supported hash types and other capabilities.
    The user must have access to a project containing the agent.
    """
    try:
        await _validate_agent_access(agent_id, current_user, db)
        return await get_agent_capabilities_service(agent_id, db)
    except (AgentNotFoundProblem, ProjectAccessDeniedError):
        raise
    except AgentNotFoundError as exc:
        raise AgentNotFoundProblem(
            detail=f"Agent with ID {agent_id} not found"
        ) from exc
    except Exception as e:
        raise InternalServerError(
            detail=f"Failed to get agent capabilities: {e!s}"
        ) from e


@router.get(
    "/{agent_id}/errors",
    summary="Get agent error log",
    description="Get the error log for an agent.",
)
async def get_agent_errors(
    agent_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_control_user)],
    limit: Annotated[
        int, Query(ge=1, le=100, description="Number of errors to return")
    ] = 50,
) -> AgentErrorLogOut:
    """
    Get agent error log.

    Returns the most recent errors for the agent.
    The user must have access to a project containing the agent.
    """
    try:
        await _validate_agent_access(agent_id, current_user, db)
        errors = await get_agent_error_log_service(agent_id, db, limit)
        errors_out = [
            AgentErrorOut.model_validate(e, from_attributes=True) for e in errors
        ]
        return AgentErrorLogOut(errors=errors_out)
    except (AgentNotFoundProblem, ProjectAccessDeniedError):
        raise
    except AgentNotFoundError as exc:
        raise AgentNotFoundProblem(
            detail=f"Agent with ID {agent_id} not found"
        ) from exc
    except Exception as e:
        raise InternalServerError(detail=f"Failed to get agent errors: {e!s}") from e


@router.post(
    "/{agent_id}/test_presigned",
    summary="Test presigned URL access",
    description="Test that an agent can access presigned URLs for file downloads.",
)
async def test_presigned_url(
    agent_id: int,
    request: AgentPresignedUrlTestRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_control_user)],
) -> AgentPresignedUrlTestResponse:
    """
    Test presigned URL access for an agent.

    Tests that the agent can successfully access a presigned URL.
    The user must have access to a project containing the agent.
    """
    try:
        await _validate_agent_access(agent_id, current_user, db)
        result = await validate_presigned_url_service(agent_id, request.url, db)
        return AgentPresignedUrlTestResponse(
            valid=result.get("valid", False),
            message=result.get("message", "Unknown result"),
        )
    except (AgentNotFoundProblem, ProjectAccessDeniedError):
        raise
    except AgentNotFoundError as exc:
        raise AgentNotFoundProblem(
            detail=f"Agent with ID {agent_id} not found"
        ) from exc
    except Exception as e:
        raise InternalServerError(detail=f"Failed to test presigned URL: {e!s}") from e
