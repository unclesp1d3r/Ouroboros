"""
Unit tests for resource cleanup job logic.

Tests for:
- cleanup_stale_pending_resources: periodic cleanup of stale pending resources
- cleanup_stale_resource: cleanup of individual resources
- Idempotency and concurrency safety
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tasks.resource_tasks import cleanup_stale_pending_resources
from app.models.attack_resource_file import AttackResourceFile, AttackResourceType
from tests.factories.attack_resource_file_factory import AttackResourceFileFactory


@pytest.mark.asyncio
async def test_cleanup_stale_pending_resources_deletes_old_pending(
    db_session: AsyncSession,
) -> None:
    """Test that cleanup deletes pending resources older than threshold."""
    # Create a stale pending resource (created 25 hours ago)
    stale_resource = AttackResourceFileFactory.build(
        file_name="stale-resource.txt",
        resource_type=AttackResourceType.WORD_LIST,
        is_uploaded=False,
    )
    stale_resource.created_at = datetime.now(UTC) - timedelta(hours=25)
    db_session.add(stale_resource)
    await db_session.commit()

    stale_id = stale_resource.id

    # Mock the storage service to avoid MinIO calls
    with patch(
        "app.core.services.resource_service.get_storage_service"
    ) as mock_storage:
        mock_service = MagicMock()
        mock_storage.return_value = mock_service
        # Simulate object not found in MinIO
        from minio.error import S3Error

        mock_service.client.stat_object.side_effect = S3Error(
            code="NoSuchKey",
            message="Object not found",
            resource="test",
            request_id="test",
            host_id="test",
            response=None,
        )

        # Run cleanup
        summary = await cleanup_stale_pending_resources(db_session)

    assert summary["deleted"] >= 1
    assert summary["errors"] == 0

    # Verify resource is gone
    from sqlalchemy import select

    result = await db_session.execute(
        select(AttackResourceFile).where(AttackResourceFile.id == stale_id)
    )
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_cleanup_stale_pending_resources_ignores_recent(
    db_session: AsyncSession,
) -> None:
    """Test that cleanup ignores recently created pending resources."""
    # Create a recent pending resource (created 1 hour ago)
    recent_resource = AttackResourceFileFactory.build(
        file_name="recent-resource.txt",
        resource_type=AttackResourceType.WORD_LIST,
        is_uploaded=False,
    )
    recent_resource.created_at = datetime.now(UTC) - timedelta(hours=1)
    db_session.add(recent_resource)
    await db_session.commit()

    recent_id = recent_resource.id

    # Run cleanup (should not delete anything)
    summary = await cleanup_stale_pending_resources(db_session)

    assert summary["deleted"] == 0

    # Verify resource still exists
    from sqlalchemy import select

    result = await db_session.execute(
        select(AttackResourceFile).where(AttackResourceFile.id == recent_id)
    )
    assert result.scalar_one_or_none() is not None


@pytest.mark.asyncio
async def test_cleanup_stale_pending_resources_ignores_uploaded(
    db_session: AsyncSession,
) -> None:
    """Test that cleanup ignores uploaded resources regardless of age."""
    # Create an old but uploaded resource (created 48 hours ago)
    uploaded_resource = AttackResourceFileFactory.build(
        file_name="uploaded-resource.txt",
        resource_type=AttackResourceType.WORD_LIST,
        is_uploaded=True,
    )
    uploaded_resource.created_at = datetime.now(UTC) - timedelta(hours=48)
    db_session.add(uploaded_resource)
    await db_session.commit()

    uploaded_id = uploaded_resource.id

    # Run cleanup (should not delete anything)
    summary = await cleanup_stale_pending_resources(db_session)

    assert summary["deleted"] == 0

    # Verify resource still exists
    from sqlalchemy import select

    result = await db_session.execute(
        select(AttackResourceFile).where(AttackResourceFile.id == uploaded_id)
    )
    assert result.scalar_one_or_none() is not None


@pytest.mark.asyncio
async def test_cleanup_stale_pending_resources_no_stale_resources(
    db_session: AsyncSession,
) -> None:
    """Test cleanup when there are no stale resources."""
    # Create only recent and uploaded resources
    recent = AttackResourceFileFactory.build(
        file_name="recent.txt",
        is_uploaded=False,
    )
    recent.created_at = datetime.now(UTC) - timedelta(hours=1)

    uploaded = AttackResourceFileFactory.build(
        file_name="uploaded.txt",
        is_uploaded=True,
    )
    uploaded.created_at = datetime.now(UTC) - timedelta(hours=48)

    db_session.add_all([recent, uploaded])
    await db_session.commit()

    # Run cleanup
    summary = await cleanup_stale_pending_resources(db_session)

    assert summary["deleted"] == 0
    assert summary["errors"] == 0


@pytest.mark.asyncio
async def test_cleanup_stale_pending_resources_handles_storage_errors(
    db_session: AsyncSession,
) -> None:
    """Test cleanup handles storage errors gracefully and continues."""
    # Create two stale resources
    stale1 = AttackResourceFileFactory.build(
        file_name="stale1.txt",
        is_uploaded=False,
    )
    stale1.created_at = datetime.now(UTC) - timedelta(hours=25)

    stale2 = AttackResourceFileFactory.build(
        file_name="stale2.txt",
        is_uploaded=False,
    )
    stale2.created_at = datetime.now(UTC) - timedelta(hours=25)

    db_session.add_all([stale1, stale2])
    await db_session.commit()

    # Mock storage service to fail on first resource, succeed on second
    call_count = 0

    def mock_stat_object(bucket: str, resource_id: str) -> None:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise OSError("Connection refused")
        from minio.error import S3Error

        raise S3Error(
            code="NoSuchKey",
            message="Object not found",
            resource="test",
            request_id="test",
            host_id="test",
            response=None,
        )

    with patch(
        "app.core.services.resource_service.get_storage_service"
    ) as mock_storage:
        mock_service = MagicMock()
        mock_storage.return_value = mock_service
        mock_service.client.stat_object.side_effect = mock_stat_object

        # Run cleanup
        summary = await cleanup_stale_pending_resources(db_session)

    # One should have been deleted successfully, one should have errored
    assert summary["deleted"] >= 1
    assert summary["errors"] >= 1


@pytest.mark.asyncio
async def test_cleanup_stale_pending_resources_idempotent(
    db_session: AsyncSession,
) -> None:
    """Test cleanup is idempotent - running twice doesn't cause issues."""
    # Create a stale pending resource
    stale_resource = AttackResourceFileFactory.build(
        file_name="stale.txt",
        is_uploaded=False,
    )
    stale_resource.created_at = datetime.now(UTC) - timedelta(hours=25)
    db_session.add(stale_resource)
    await db_session.commit()

    with patch(
        "app.core.services.resource_service.get_storage_service"
    ) as mock_storage:
        mock_service = MagicMock()
        mock_storage.return_value = mock_service
        from minio.error import S3Error

        mock_service.client.stat_object.side_effect = S3Error(
            code="NoSuchKey",
            message="Object not found",
            resource="test",
            request_id="test",
            host_id="test",
            response=None,
        )

        # First run deletes the resource
        summary1 = await cleanup_stale_pending_resources(db_session)
        assert summary1["deleted"] == 1

        # Second run finds nothing to delete
        summary2 = await cleanup_stale_pending_resources(db_session)
        assert summary2["deleted"] == 0
        assert summary2["errors"] == 0


@pytest.mark.asyncio
async def test_cleanup_stale_pending_resources_deletes_from_minio(
    db_session: AsyncSession,
) -> None:
    """Test cleanup deletes object from MinIO when it exists."""
    # Create a stale pending resource
    stale_resource = AttackResourceFileFactory.build(
        file_name="stale.txt",
        is_uploaded=False,
    )
    stale_resource.created_at = datetime.now(UTC) - timedelta(hours=25)
    db_session.add(stale_resource)
    await db_session.commit()

    with patch(
        "app.core.services.resource_service.get_storage_service"
    ) as mock_storage:
        mock_service = MagicMock()
        mock_storage.return_value = mock_service
        # Simulate object exists in MinIO
        mock_service.client.stat_object.return_value = MagicMock()
        mock_service.client.remove_object.return_value = None

        # Run cleanup
        summary = await cleanup_stale_pending_resources(db_session)

    assert summary["deleted"] == 1
    # Verify remove_object was called with the resource ID
    mock_service.client.remove_object.assert_called()


@pytest.mark.asyncio
async def test_cleanup_multiple_stale_resources(
    db_session: AsyncSession,
) -> None:
    """Test cleanup handles multiple stale resources correctly."""
    # Create 5 stale pending resources
    stale_resources = []
    for i in range(5):
        resource = AttackResourceFileFactory.build(
            file_name=f"stale{i}.txt",
            is_uploaded=False,
        )
        resource.created_at = datetime.now(UTC) - timedelta(hours=25 + i)
        stale_resources.append(resource)

    db_session.add_all(stale_resources)
    await db_session.commit()

    with patch(
        "app.core.services.resource_service.get_storage_service"
    ) as mock_storage:
        mock_service = MagicMock()
        mock_storage.return_value = mock_service
        from minio.error import S3Error

        mock_service.client.stat_object.side_effect = S3Error(
            code="NoSuchKey",
            message="Object not found",
            resource="test",
            request_id="test",
            host_id="test",
            response=None,
        )

        # Run cleanup
        summary = await cleanup_stale_pending_resources(db_session)

    assert summary["deleted"] == 5
    assert summary["errors"] == 0
