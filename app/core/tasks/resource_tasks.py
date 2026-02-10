import asyncio
from datetime import UTC, datetime, timedelta

from minio.error import S3Error
from sqlalchemy import delete
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.core.logging import logger
from app.core.services.storage_service import get_storage_service
from app.models.attack_resource_file import AttackResourceFile


async def verify_upload_and_cleanup(
    resource_id: str, db: AsyncSession, timeout_seconds: int
) -> None:
    """
    Background task to verify if the file was uploaded to MinIO. If not, delete the resource from DB.
    TODO: Upgrade to Celery when Redis is available.
    """
    await asyncio.sleep(timeout_seconds)
    # Re-check DB in case resource was verified
    async with db as session:
        result = await session.execute(
            select(AttackResourceFile).where(AttackResourceFile.id == resource_id)
        )
        resource_obj = result.scalar_one_or_none()
        if not resource_obj:
            return  # Already deleted or verified
        if getattr(resource_obj, "is_uploaded", False):
            logger.info(
                f"Resource {resource_id} already marked as uploaded. Skipping cleanup."
            )
            return
    storage_service = get_storage_service()
    bucket = settings.MINIO_BUCKET
    try:
        exists = await storage_service.bucket_exists(bucket)
        if not exists:
            logger.error(f"Bucket {bucket} does not exist")
            return  # Bucket gone, nothing to do
        # Try to get object
        try:
            obj = storage_service.client.stat_object(bucket, str(resource_id))
            if obj:
                logger.info(
                    f"File {resource_id} exists in MinIO, appears to be uploaded successfully. Skipping cleanup."
                )
                return  # File exists, do nothing
        except (S3Error, OSError) as e:
            logger.error(f"Error checking file existence in MinIO: {e}")
            return  # File not found, nothing to do
        # Delete resource from DB
        async with db as session:
            await session.execute(
                delete(AttackResourceFile).where(AttackResourceFile.id == resource_id)
            )
            await session.commit()
            logger.info(f"Resource {resource_id} not found in MinIO, deleted from DB")
    except (SQLAlchemyError, OSError) as e:
        logger.error(f"Background upload verification failed: {e}")


async def cleanup_stale_pending_resources(db: AsyncSession) -> dict[str, int]:
    """
    Clean up stale pending resources that haven't been uploaded within the configured age threshold.

    Queries for resources where is_uploaded=False and created_at < (now - age threshold).
    Uses skip_locked to prevent concurrent cleanup conflicts without blocking.
    Commits after each resource to minimize lock duration during I/O operations.

    Args:
        db: Database session from sessionmanager.session()

    Returns:
        Dictionary with cleanup summary: {deleted: int, errors: int}
    """
    from app.core.services.resource_service import cleanup_stale_resource

    age_hours = settings.RESOURCE_CLEANUP_AGE_HOURS
    cutoff_time = datetime.now(UTC) - timedelta(hours=age_hours)

    deleted = 0
    errors = 0

    try:
        # Query for stale pending resource IDs only (no FOR UPDATE lock on query)
        # Each resource will be processed individually with its own lock
        result = await db.execute(
            select(AttackResourceFile.id)
            .where(AttackResourceFile.is_uploaded == False)  # noqa: E712
            .where(AttackResourceFile.created_at < cutoff_time)
        )
        stale_resource_ids = [row[0] for row in result.fetchall()]

        if not stale_resource_ids:
            logger.debug("No stale pending resources found for cleanup")
            return {"deleted": 0, "errors": 0}

        logger.bind(
            stale_count=len(stale_resource_ids),
            age_threshold_hours=age_hours,
        ).info("Found stale pending resources for cleanup")

        # Process each stale resource individually to minimize lock duration
        for resource_id in stale_resource_ids:
            try:
                # Lock and fetch the resource for this specific deletion
                result = await db.execute(
                    select(AttackResourceFile)
                    .where(AttackResourceFile.id == resource_id)
                    .with_for_update(skip_locked=True)
                )
                resource = result.scalar_one_or_none()

                if resource is None:
                    # Resource was already deleted or locked by another worker
                    continue

                # Skip if resource was uploaded while we were processing
                if resource.is_uploaded:
                    continue

                success = await cleanup_stale_resource(resource, db)
                if success:
                    deleted += 1
                    # Commit after each successful deletion to release lock quickly
                    await db.commit()
                else:
                    errors += 1
                    await db.rollback()

            except Exception as e:  # noqa: BLE001 - Defensive catch-all for background cleanup
                logger.bind(
                    resource_id=str(resource_id),
                    error=str(e),
                ).error("Exception during stale resource cleanup")
                errors += 1
                await db.rollback()
                # Continue processing other resources

    except Exception as e:
        logger.bind(error=str(e)).error("Failed to query stale pending resources")
        await db.rollback()
        raise

    return {"deleted": deleted, "errors": errors}


async def run_periodic_cleanup() -> None:
    """
    Background task that runs periodically to clean up stale pending resources.

    Runs in an infinite loop with configurable sleep interval (default 1 hour).
    Opens fresh database sessions via sessionmanager.session().
    Logs cleanup summary after each run.
    Handles exceptions to prevent task crash.
    """
    from app.db.session import sessionmanager

    interval_hours = settings.RESOURCE_CLEANUP_INTERVAL_HOURS
    interval_seconds = interval_hours * 3600

    logger.bind(
        interval_hours=interval_hours,
        age_threshold_hours=settings.RESOURCE_CLEANUP_AGE_HOURS,
    ).info("Starting periodic resource cleanup task")

    while True:
        try:
            # Wait before first run to allow system to stabilize
            await asyncio.sleep(interval_seconds)

            logger.debug("Running periodic resource cleanup")

            async with sessionmanager.session() as db:
                summary = await cleanup_stale_pending_resources(db)

            logger.bind(
                deleted=summary["deleted"],
                errors=summary["errors"],
            ).info("Periodic resource cleanup completed")

        except asyncio.CancelledError:
            logger.info("Periodic resource cleanup task cancelled")
            raise  # Re-raise to allow proper task cancellation
        except Exception as e:  # noqa: BLE001 - Defensive catch-all for background task
            logger.bind(error=str(e)).error("Periodic resource cleanup failed")
            # Continue running, don't crash the task
