"""
Control API tasks endpoints.

The Control API uses API key authentication and offset-based pagination.
All responses are JSON format.
Error responses must follow RFC9457 format.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.control_exceptions import (
    InternalServerError,
    InvalidResourceStateError,
    ProjectAccessDeniedError,
)
from app.core.control_exceptions import (
    TaskNotFoundError as TaskNotFoundProblem,
)
from app.core.deps import get_current_control_user
from app.db.session import get_db
from app.models.attack import Attack
from app.models.campaign import Campaign
from app.models.task import Task, TaskStatus
from app.models.user import User
from app.schemas.shared import OffsetPaginatedResponse
from app.schemas.task import TaskOut

router = APIRouter(prefix="/tasks", tags=["Control - Tasks"])


# =============================================================================
# Response Schemas
# =============================================================================


class TaskPerformance(BaseModel):
    """Task performance metrics."""

    task_id: Annotated[int, Field(description="Task ID")]
    progress_percent: Annotated[float, Field(description="Task progress percentage")]
    keyspace_total: Annotated[int, Field(description="Total keyspace for this task")]
    keyspace_processed: Annotated[int, Field(description="Keyspace processed so far")]
    speed: Annotated[int | None, Field(description="Current speed (hashes/sec)")]
    estimated_completion: Annotated[
        str | None, Field(description="Estimated completion time")
    ]

    model_config = ConfigDict(extra="forbid")


class TaskLogEntry(BaseModel):
    """A single task log entry."""

    timestamp: Annotated[str, Field(description="Log entry timestamp")]
    level: Annotated[str, Field(description="Log level (info, warning, error)")]
    message: Annotated[str, Field(description="Log message")]

    model_config = ConfigDict(extra="forbid")


class TaskLogs(BaseModel):
    """Task logs response."""

    task_id: Annotated[int, Field(description="Task ID")]
    entries: Annotated[list[TaskLogEntry], Field(description="Log entries")]

    model_config = ConfigDict(extra="forbid")


class TaskStatusResponse(BaseModel):
    """Task status response."""

    task_id: Annotated[int, Field(description="Task ID")]
    status: Annotated[str, Field(description="Current task status")]
    progress_percent: Annotated[float, Field(description="Task progress percentage")]
    agent_id: Annotated[int | None, Field(description="Assigned agent ID")]

    model_config = ConfigDict(extra="forbid")


# =============================================================================
# Helper Functions
# =============================================================================


def _get_accessible_projects(user: User) -> list[int]:
    """Get list of project IDs the user has access to."""
    if user.project_associations:
        return [assoc.project_id for assoc in user.project_associations]
    return []


async def _validate_task_access(task_id: int, user: User, db: AsyncSession) -> Task:
    """Validate that user has access to the task and return it."""
    result = await db.execute(
        select(Task)
        .options(selectinload(Task.attack).selectinload(Attack.campaign))
        .where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise TaskNotFoundProblem(detail=f"Task with ID {task_id} not found")

    # Check if task's campaign is in a project the user has access to
    accessible = _get_accessible_projects(user)
    if not accessible:
        raise ProjectAccessDeniedError(detail="User has no project access")

    if task.attack and task.attack.campaign:
        if task.attack.campaign.project_id not in accessible:
            raise ProjectAccessDeniedError(
                detail=f"User does not have access to task {task_id}"
            )
    else:
        raise ProjectAccessDeniedError(
            detail=f"Task {task_id} has no associated campaign"
        )

    return task


# =============================================================================
# Endpoints
# =============================================================================


@router.get(
    "",
    summary="List tasks",
    description="List tasks with offset-based pagination and filtering. Supports project scoping based on user permissions.",
)
async def list_tasks(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_control_user)],
    limit: Annotated[
        int, Query(ge=1, le=100, description="Number of items to return")
    ] = 10,
    offset: Annotated[int, Query(ge=0, description="Number of items to skip")] = 0,
    status: Annotated[
        str | None,
        Query(description="Filter by task status (pending, running, completed, etc.)"),
    ] = None,
    attack_id: Annotated[int | None, Query(description="Filter by attack ID")] = None,
    campaign_id: Annotated[
        int | None, Query(description="Filter by campaign ID")
    ] = None,
    agent_id: Annotated[
        int | None, Query(description="Filter by assigned agent ID")
    ] = None,
) -> OffsetPaginatedResponse[TaskOut]:
    """
    List tasks with offset-based pagination and filtering.

    Access is scoped to tasks in projects the user has access to.
    """
    try:
        # Get user's accessible projects
        accessible_projects = _get_accessible_projects(current_user)

        if not accessible_projects:
            raise ProjectAccessDeniedError(detail="User has no project access")

        # Build query with project scoping
        query = (
            select(Task)
            .join(Task.attack)
            .join(Attack.campaign)
            .where(Campaign.project_id.in_(accessible_projects))
        )

        # Apply filters
        if status:
            try:
                status_enum = TaskStatus(status.lower())
                query = query.where(Task.status == status_enum)
            except ValueError:
                pass  # Ignore invalid status

        if attack_id is not None:
            query = query.where(Task.attack_id == attack_id)

        if campaign_id is not None:
            query = query.where(Attack.campaign_id == campaign_id)

        if agent_id is not None:
            query = query.where(Task.agent_id == agent_id)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar_one()

        # Apply pagination
        query = query.offset(offset).limit(limit).order_by(Task.id.desc())

        # Execute query
        result = await db.execute(query)
        tasks = result.scalars().all()

        tasks_out = [TaskOut.model_validate(t, from_attributes=True) for t in tasks]

        return OffsetPaginatedResponse(
            items=tasks_out,
            total=total,
            limit=limit,
            offset=offset,
        )
    except ProjectAccessDeniedError:
        raise
    except Exception as e:
        raise InternalServerError(detail=f"Failed to list tasks: {e!s}") from e


@router.get(
    "/{task_id}",
    summary="Get task",
    description="Get a task by ID with full details.",
)
async def get_task(
    task_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_control_user)],
) -> TaskOut:
    """
    Get a task by ID.

    The user must have access to the project containing the task.
    """
    try:
        task = await _validate_task_access(task_id, current_user, db)
        return TaskOut.model_validate(task, from_attributes=True)
    except (TaskNotFoundProblem, ProjectAccessDeniedError):
        raise
    except Exception as e:
        raise InternalServerError(detail=f"Failed to get task: {e!s}") from e


@router.post(
    "/{task_id}/requeue",
    summary="Requeue task",
    description="Requeue a task for re-execution. Only failed or abandoned tasks can be requeued.",
)
async def requeue_task(
    task_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_control_user)],
) -> TaskOut:
    """
    Requeue a task for re-execution.

    Only tasks in failed or abandoned state can be requeued.
    The user must have access to the project containing the task.
    """
    try:
        task = await _validate_task_access(task_id, current_user, db)

        # Check task state - only allow requeue for failed/abandoned tasks
        allowed_states = {TaskStatus.FAILED, TaskStatus.ABANDONED}
        if task.status not in allowed_states:
            raise InvalidResourceStateError(
                detail=f"Cannot requeue task in '{task.status.value}' state. "
                f"Task must be in one of: {', '.join(s.value for s in allowed_states)}"
            )

        # Reset task to pending state
        task.status = TaskStatus.PENDING
        task.agent_id = None
        task.progress = 0.0

        await db.commit()
        await db.refresh(task)

        return TaskOut.model_validate(task, from_attributes=True)
    except (TaskNotFoundProblem, ProjectAccessDeniedError, InvalidResourceStateError):
        raise
    except Exception as e:
        raise InternalServerError(detail=f"Failed to requeue task: {e!s}") from e


@router.post(
    "/{task_id}/cancel",
    summary="Cancel task",
    description="Cancel a running or pending task.",
)
async def cancel_task(
    task_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_control_user)],
) -> TaskOut:
    """
    Cancel a task.

    Only tasks in pending or running state can be cancelled.
    The user must have access to the project containing the task.
    """
    try:
        task = await _validate_task_access(task_id, current_user, db)

        # Check task state - only allow cancel for pending/running tasks
        allowed_states = {TaskStatus.PENDING, TaskStatus.RUNNING}
        if task.status not in allowed_states:
            raise InvalidResourceStateError(
                detail=f"Cannot cancel task in '{task.status.value}' state. "
                f"Task must be in one of: {', '.join(s.value for s in allowed_states)}"
            )

        # Set task to abandoned state
        task.status = TaskStatus.ABANDONED

        await db.commit()
        await db.refresh(task)

        return TaskOut.model_validate(task, from_attributes=True)
    except (TaskNotFoundProblem, ProjectAccessDeniedError, InvalidResourceStateError):
        raise
    except Exception as e:
        raise InternalServerError(detail=f"Failed to cancel task: {e!s}") from e


@router.get(
    "/{task_id}/status",
    summary="Get task status",
    description="Get the current status of a task.",
)
async def get_task_status(
    task_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_control_user)],
) -> TaskStatusResponse:
    """
    Get the current status of a task.

    The user must have access to the project containing the task.
    """
    try:
        task = await _validate_task_access(task_id, current_user, db)

        return TaskStatusResponse(
            task_id=task.id,
            status=task.status.value,
            progress_percent=task.progress_percent,
            agent_id=task.agent_id,
        )
    except (TaskNotFoundProblem, ProjectAccessDeniedError):
        raise
    except Exception as e:
        raise InternalServerError(detail=f"Failed to get task status: {e!s}") from e


@router.get(
    "/{task_id}/performance",
    summary="Get task performance",
    description="Get performance metrics for a task.",
)
async def get_task_performance(
    task_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_control_user)],
) -> TaskPerformance:
    """
    Get task performance metrics.

    The user must have access to the project containing the task.
    """
    try:
        task = await _validate_task_access(task_id, current_user, db)

        # Calculate keyspace metrics
        keyspace_total = task.keyspace_total
        # Estimate keyspace processed from progress percentage
        progress = task.progress if task.progress is not None else 0.0
        keyspace_processed = (
            int(keyspace_total * progress / 100.0) if keyspace_total > 0 else 0
        )

        return TaskPerformance(
            task_id=task.id,
            progress_percent=progress,
            keyspace_total=keyspace_total,
            keyspace_processed=keyspace_processed,
            speed=None,  # Speed would come from real-time status updates
            estimated_completion=None,  # Would need ETA calculation
        )
    except (TaskNotFoundProblem, ProjectAccessDeniedError):
        raise
    except Exception as e:
        raise InternalServerError(
            detail=f"Failed to get task performance: {e!s}"
        ) from e


@router.get(
    "/{task_id}/logs",
    summary="Get task logs",
    description="Get the log entries for a task.",
)
async def get_task_logs(
    task_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_control_user)],
    limit: Annotated[
        int, Query(ge=1, le=100, description="Number of log entries to return")
    ] = 50,
) -> TaskLogs:
    """
    Get task log entries.

    Returns log entries from the task's execution.
    The user must have access to the project containing the task.
    """
    from app.models.task import TaskStatusUpdate as TaskStatusUpdateModel

    try:
        task = await _validate_task_access(task_id, current_user, db)

        # Get status updates as log entries
        result = await db.execute(
            select(TaskStatusUpdateModel)
            .where(TaskStatusUpdateModel.task_id == task_id)
            .order_by(TaskStatusUpdateModel.time.desc())
            .limit(limit)
        )
        status_updates = result.scalars().all()

        entries = [
            TaskLogEntry(
                timestamp=str(update.time) if update.time else "",
                level="info",
                message=f"Status: {update.status}, Session: {update.session}",
            )
            for update in status_updates
        ]

        return TaskLogs(task_id=task.id, entries=entries)
    except (TaskNotFoundProblem, ProjectAccessDeniedError):
        raise
    except Exception as e:
        raise InternalServerError(detail=f"Failed to get task logs: {e!s}") from e
