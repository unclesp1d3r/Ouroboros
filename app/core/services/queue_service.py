"""Queue monitoring service for background tasks and system processing."""

from datetime import UTC, datetime, timedelta
from typing import Any

import redis.asyncio as aioredis
from cashews import cache
from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.hash_upload_task import HashUploadStatus, HashUploadTask
from app.models.task import Task, TaskStatus
from app.schemas.queue import (
    BackgroundTaskStats,
    QueueHealth,
    QueueStatus,
    QueueStatusResponse,
    QueueType,
    RecentActivityStats,
    StatusEnum,
    TaskTypeStats,
)

# Constants
QUEUE_DEPTH_THRESHOLD = 100  # Threshold for considering queue depth concerning


async def _get_redis_queue_info() -> dict[str, Any]:
    """Get Redis queue information if available."""
    queue_info: dict[str, Any] = {
        "redis_available": False,
        "celery_queues": {},
        "redis_memory_usage": None,
        "redis_connections": None,
    }

    try:
        redis = aioredis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            decode_responses=True,
        )

        # Test connection - ping() returns True on success or raises RedisError on failure
        await redis.ping()  # pyright: ignore[reportGeneralTypeIssues]
        queue_info["redis_available"] = True

        # Get Redis info
        info = await redis.info()
        queue_info["redis_memory_usage"] = info.get("used_memory")
        queue_info["redis_connections"] = info.get("connected_clients")

        # Check for Celery queues (if they exist)
        # Note: This is a placeholder for future Celery implementation
        # Currently the system uses asyncio tasks, not Celery
        celery_queues = ["default", "estimation", "resources", "maintenance"]
        for queue_name in celery_queues:
            try:
                # Check if queue exists in Redis
                queue_length = await redis.llen(f"celery:{queue_name}")  # pyright: ignore[reportGeneralTypeIssues]
                queue_info["celery_queues"][queue_name] = {
                    "length": queue_length,
                    "status": "active" if queue_length >= 0 else "inactive",
                }
            except aioredis.ResponseError as e:
                # Queue doesn't exist - this is expected for placeholder queues
                logger.debug(f"Queue {queue_name} not found: {e}")
                queue_info["celery_queues"][queue_name] = {
                    "length": 0,
                    "status": "inactive",
                }
            except (aioredis.RedisError, ConnectionError) as e:
                # Connection or Redis error - this indicates a problem
                logger.error(f"Failed to check queue {queue_name}: {e}")
                queue_info["celery_queues"][queue_name] = {
                    "length": None,
                    "status": "error",
                    "error": str(e),
                }

        await redis.aclose()

    except (aioredis.RedisError, ConnectionError, OSError) as e:
        logger.warning(f"Failed to get Redis queue info: {e}")

    return queue_info


async def _get_background_task_stats(db: AsyncSession) -> BackgroundTaskStats:
    """Get statistics about background tasks and processing."""
    # Get task statistics
    total_tasks = await db.scalar(select(func.count()).select_from(Task))
    pending_tasks = await db.scalar(
        select(func.count()).select_from(Task).where(Task.status == TaskStatus.PENDING)
    )
    running_tasks = await db.scalar(
        select(func.count()).select_from(Task).where(Task.status == TaskStatus.RUNNING)
    )
    failed_tasks = await db.scalar(
        select(func.count()).select_from(Task).where(Task.status == TaskStatus.FAILED)
    )

    # Get upload task statistics
    total_uploads = await db.scalar(select(func.count()).select_from(HashUploadTask))
    pending_uploads = await db.scalar(
        select(func.count())
        .select_from(HashUploadTask)
        .where(HashUploadTask.status == HashUploadStatus.PENDING)
    )
    running_uploads = await db.scalar(
        select(func.count())
        .select_from(HashUploadTask)
        .where(HashUploadTask.status == HashUploadStatus.RUNNING)
    )
    failed_uploads = await db.scalar(
        select(func.count())
        .select_from(HashUploadTask)
        .where(HashUploadTask.status == HashUploadStatus.FAILED)
    )

    # Get recent task activity (last hour)
    one_hour_ago = datetime.now(UTC) - timedelta(hours=1)
    recent_tasks = await db.scalar(
        select(func.count()).select_from(Task).where(Task.start_date >= one_hour_ago)
    )

    return BackgroundTaskStats(
        cracking_tasks=TaskTypeStats(
            total=total_tasks or 0,
            pending=pending_tasks or 0,
            running=running_tasks or 0,
            failed=failed_tasks or 0,
        ),
        upload_tasks=TaskTypeStats(
            total=total_uploads or 0,
            pending=pending_uploads or 0,
            running=running_uploads or 0,
            failed=failed_uploads or 0,
        ),
        recent_activity=RecentActivityStats(
            tasks_last_hour=recent_tasks or 0,
        ),
    )


@cache(ttl="30s", key="queue_status")
async def get_queue_status_service(db: AsyncSession) -> QueueStatusResponse:
    """Get comprehensive queue status information."""
    # Get Redis/Celery queue information
    redis_info = await _get_redis_queue_info()

    # Get background task statistics
    task_stats = await _get_background_task_stats(db)

    # Determine overall queue health
    queue_health = QueueHealth.healthy
    if not redis_info["redis_available"]:
        queue_health = (
            QueueHealth.degraded
        )  # Redis unavailable but asyncio tasks still work

    # Check for concerning queue depths
    total_pending = task_stats.cracking_tasks.pending + task_stats.upload_tasks.pending
    if total_pending > QUEUE_DEPTH_THRESHOLD:
        queue_health = QueueHealth.degraded

    # Create queue status objects
    queues: list[QueueStatus] = []

    # Add cracking task queue status
    queues.append(
        QueueStatus(
            name="cracking_tasks",
            type=QueueType.asyncio,
            pending_jobs=task_stats.cracking_tasks.pending,
            running_jobs=task_stats.cracking_tasks.running,
            failed_jobs=task_stats.cracking_tasks.failed,
            status=StatusEnum.active
            if task_stats.cracking_tasks.running > 0
            else StatusEnum.idle,
        )
    )

    # Add upload task queue status
    queues.append(
        QueueStatus(
            name="upload_processing",
            type=QueueType.asyncio,
            pending_jobs=task_stats.upload_tasks.pending,
            running_jobs=task_stats.upload_tasks.running,
            failed_jobs=task_stats.upload_tasks.failed,
            status=StatusEnum.active
            if task_stats.upload_tasks.running > 0
            else StatusEnum.idle,
        )
    )

    # Add Celery queues if Redis is available
    if redis_info["redis_available"]:
        for queue_name, queue_data in redis_info["celery_queues"].items():
            # Convert string status to enum
            if queue_data["status"] == "active":
                celery_status = StatusEnum.active
            elif queue_data["status"] == "error":
                celery_status = StatusEnum.error
            else:
                celery_status = StatusEnum.inactive

            queues.append(
                QueueStatus(
                    name=f"celery_{queue_name}",
                    type=QueueType.celery,
                    pending_jobs=queue_data["length"],
                    running_jobs=0,  # Celery running jobs are harder to track
                    failed_jobs=0,  # Would need additional Redis keys
                    status=celery_status,
                    error=queue_data.get("error"),
                )
            )

    return QueueStatusResponse(
        overall_status=queue_health,
        redis_available=redis_info["redis_available"],
        redis_memory_usage=redis_info["redis_memory_usage"],
        redis_connections=redis_info["redis_connections"],
        queues=queues,
        total_pending_jobs=total_pending,
        total_running_jobs=(
            task_stats.cracking_tasks.running + task_stats.upload_tasks.running
        ),
        recent_activity=task_stats.recent_activity,
    )
