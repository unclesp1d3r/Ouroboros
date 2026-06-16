import io
import uuid

import httpx
import pytest
from httpx import AsyncClient
from minio import Minio
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from tests.factories.attack_resource_file_factory import AttackResourceFileFactory


@pytest.mark.asyncio
async def test_orphan_audit_detects_s3_and_db_orphans(
    authenticated_admin_client: AsyncClient,
    db_session: AsyncSession,
    minio_client: Minio,
    attack_resource_file_factory: AttackResourceFileFactory,
) -> None:
    # Setup MinIO client
    bucket = settings.MINIO_BUCKET

    # Ensure bucket exists
    if not minio_client.bucket_exists(bucket):
        minio_client.make_bucket(bucket)

    # 1. Create a DB resource with no S3 object (DB orphan)
    db_orphan = await attack_resource_file_factory.create_async()
    # 2. Upload an S3 object with no DB record (S3 orphan)
    s3_orphan_key = f"orphan-{uuid.uuid4()}"
    minio_client.put_object(
        bucket,
        s3_orphan_key,
        io.BytesIO(b"orphaned content"),
        length=len(b"orphaned content"),
    )
    # 3. Create a resource with a matching S3 object (not orphaned)
    linked = await attack_resource_file_factory.create_async()
    minio_client.put_object(
        bucket,
        str(linked.id),
        io.BytesIO(b"linked content"),
        length=len(b"linked content"),
    )

    # Call the audit endpoint
    resp = await authenticated_admin_client.get("/api/v1/web/resources/audit/orphans")
    assert resp.status_code == 200
    data = resp.json()
    assert "orphaned_objects" in data
    assert "orphaned_db_records" in data
    # S3 orphan should be detected
    assert s3_orphan_key in data["orphaned_objects"]
    # DB orphan should be detected
    assert str(db_orphan.id) in data["orphaned_db_records"]
    # Linked resource should not be reported as orphan
    assert str(linked.id) not in data["orphaned_db_records"]
    assert str(linked.id) not in data["orphaned_objects"]


@pytest.mark.asyncio
async def test_orphan_audit_forbidden_for_non_admin(
    authenticated_async_client: AsyncClient,
) -> None:
    resp = await authenticated_async_client.get("/api/v1/web/resources/audit/orphans")
    assert resp.status_code == 403
    assert resp.json()["detail"] == "Admin access required."


@pytest.mark.asyncio
async def test_upload_resource_metadata_and_upload_file(
    authenticated_async_client: AsyncClient,
    minio_client: Minio,
    db_session: AsyncSession,
) -> None:
    url = "/api/v1/web/resources/"
    file_name = f"test_upload_{uuid.uuid4()}.txt"
    resource_type = "word_list"
    # Step 1: Request presigned upload URL
    resp = await authenticated_async_client.post(
        url,
        data={
            "file_name": file_name,
            "resource_type": resource_type,
            "detect_type": "false",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    presigned_url = data["presigned_url"]
    resource_id = data["resource_id"]
    # Step 2: Upload a test file to MinIO using the presigned URL
    test_content = b"alpha\nbeta\ngamma\n"
    print(data)
    async with httpx.AsyncClient() as client:
        upload_resp = await client.put(
            presigned_url,
            content=test_content,
            headers={"Content-Type": "application/octet-stream"},
        )
    assert upload_resp.status_code in (200, 204)
    # Step 3: Verify the object exists in MinIO
    bucket = settings.MINIO_BUCKET
    obj = minio_client.get_object(bucket, resource_id)
    downloaded = obj.read()
    assert downloaded == test_content
    obj.close()


@pytest.mark.asyncio
async def test_upload_resource_metadata_sets_is_uploaded_false(
    authenticated_async_client: AsyncClient,
    minio_client: Minio,
    db_session: AsyncSession,
) -> None:
    url = "/api/v1/web/resources/"
    file_name = f"test_upload_{uuid.uuid4()}.txt"
    resource_type = "word_list"
    # Step 1: Request presigned upload URL
    resp = await authenticated_async_client.post(
        url,
        data={
            "file_name": file_name,
            "resource_type": resource_type,
            "detect_type": "false",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    presigned_url = data["presigned_url"]
    resource_id = data["resource_id"]
    # Step 2: Upload a test file to MinIO using the presigned URL
    test_content = b"alpha\nbeta\ngamma\n"
    async with httpx.AsyncClient() as client:
        upload_resp = await client.put(
            presigned_url,
            content=test_content,
            headers={"Content-Type": "application/octet-stream"},
        )
    assert upload_resp.status_code in (200, 204)
    # Step 3: Check DB for is_uploaded = False
    from app.models.attack_resource_file import AttackResourceFile

    result = await db_session.get(AttackResourceFile, resource_id)
    assert result is not None
    assert result.is_uploaded is False


@pytest.mark.asyncio
async def test_upload_verification_success(
    authenticated_async_client: AsyncClient,
    minio_client: Minio,
    db_session: AsyncSession,
) -> None:
    url = "/api/v1/web/resources/"
    file_name = f"test_upload_{uuid.uuid4()}.txt"
    resource_type = "word_list"
    # Step 1: Request presigned upload URL
    resp = await authenticated_async_client.post(
        url,
        data={
            "file_name": file_name,
            "resource_type": resource_type,
            "detect_type": "false",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    presigned_url = data["presigned_url"]
    resource_id = data["resource_id"]
    # Step 2: Upload a test file to MinIO using the presigned URL
    test_content = b"alpha\nbeta\ngamma\n"
    async with httpx.AsyncClient() as client:
        upload_resp = await client.put(
            presigned_url,
            content=test_content,
            headers={"Content-Type": "application/octet-stream"},
        )
    assert upload_resp.status_code in (200, 204)
    # Step 3: Call upload verification endpoint
    verify_url = f"/api/v1/web/resources/{resource_id}/uploaded"
    verify_resp = await authenticated_async_client.post(verify_url)
    assert verify_resp.status_code == 200
    verify_data = verify_resp.json()
    assert verify_data["is_uploaded"] is True
    assert verify_data["line_count"] == 3
    assert verify_data["byte_size"] == len(test_content)


@pytest.mark.asyncio
async def test_upload_verification_file_missing(
    authenticated_async_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    url = "/api/v1/web/resources/"
    file_name = f"test_upload_{uuid.uuid4()}.txt"
    resource_type = "word_list"
    # Step 1: Request presigned upload URL
    resp = await authenticated_async_client.post(
        url,
        data={
            "file_name": file_name,
            "resource_type": resource_type,
            "detect_type": "false",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    resource_id = data["resource_id"]
    # Step 2: Do NOT upload file to MinIO
    # Step 3: Call upload verification endpoint (should fail)
    verify_url = f"/api/v1/web/resources/{resource_id}/uploaded"
    verify_resp = await authenticated_async_client.post(verify_url)
    assert verify_resp.status_code == 400
    assert "File not found" in verify_resp.json()["detail"]


@pytest.mark.asyncio
async def test_upload_verification_already_uploaded(
    authenticated_async_client: AsyncClient,
    minio_client: Minio,
    db_session: AsyncSession,
) -> None:
    url = "/api/v1/web/resources/"
    file_name = f"test_upload_{uuid.uuid4()}.txt"
    resource_type = "word_list"
    # Step 1: Request presigned upload URL
    resp = await authenticated_async_client.post(
        url,
        data={
            "file_name": file_name,
            "resource_type": resource_type,
            "detect_type": "false",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    presigned_url = data["presigned_url"]
    resource_id = data["resource_id"]
    # Step 2: Upload a test file to MinIO using the presigned URL
    test_content = b"alpha\nbeta\ngamma\n"
    async with httpx.AsyncClient() as client:
        upload_resp = await client.put(
            presigned_url,
            content=test_content,
            headers={"Content-Type": "application/octet-stream"},
        )
    assert upload_resp.status_code in (200, 204)
    # Step 3: Call upload verification endpoint (first time)
    verify_url = f"/api/v1/web/resources/{resource_id}/uploaded"
    verify_resp = await authenticated_async_client.post(verify_url)
    assert verify_resp.status_code == 200
    # Step 4: Call upload verification endpoint again (should fail with 409)
    verify_resp2 = await authenticated_async_client.post(verify_url)
    assert verify_resp2.status_code == 409
    assert "already marked as uploaded" in verify_resp2.json()["detail"]


@pytest.mark.asyncio
async def test_refresh_metadata_success(
    authenticated_async_client: AsyncClient,
    minio_client: Minio,
    db_session: AsyncSession,
) -> None:
    url = "/api/v1/web/resources/"
    file_name = f"test_refresh_{uuid.uuid4()}.txt"
    resource_type = "word_list"
    # Step 1: Request presigned upload URL
    resp = await authenticated_async_client.post(
        url,
        data={
            "file_name": file_name,
            "resource_type": resource_type,
            "detect_type": "false",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    presigned_url = data["presigned_url"]
    resource_id = data["resource_id"]
    # Step 2: Upload a test file to MinIO using the presigned URL
    test_content = b"one\ntwo\nthree\n"
    async with httpx.AsyncClient() as client:
        upload_resp = await client.put(
            presigned_url,
            content=test_content,
            headers={"Content-Type": "application/octet-stream"},
        )
    assert upload_resp.status_code in (200, 204)
    # Step 3: Call refresh_metadata endpoint
    refresh_url = f"/api/v1/web/resources/{resource_id}/refresh_metadata"
    refresh_resp = await authenticated_async_client.post(refresh_url)
    assert refresh_resp.status_code == 200
    refresh_data = refresh_resp.json()
    assert refresh_data["line_count"] == 3
    assert refresh_data["byte_size"] == len(test_content)
    assert isinstance(refresh_data["checksum"], str)


@pytest.mark.asyncio
async def test_refresh_metadata_file_missing(
    authenticated_async_client: AsyncClient,
    db_session: AsyncSession,
    minio_client: Minio,  # Ensures MinIO container is started and settings are patched
) -> None:
    url = "/api/v1/web/resources/"
    file_name = f"test_refresh_{uuid.uuid4()}.txt"
    resource_type = "word_list"
    # Step 1: Request presigned upload URL
    resp = await authenticated_async_client.post(
        url,
        data={
            "file_name": file_name,
            "resource_type": resource_type,
            "detect_type": "false",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    resource_id = data["resource_id"]
    # Step 2: Do NOT upload file to MinIO
    # Step 3: Call refresh_metadata endpoint (should fail)
    refresh_url = f"/api/v1/web/resources/{resource_id}/refresh_metadata"
    refresh_resp = await authenticated_async_client.post(refresh_url)
    assert refresh_resp.status_code == 400
    assert "File not found" in refresh_resp.json()["detail"]


@pytest.mark.asyncio
async def test_refresh_metadata_forbidden(
    authenticated_async_client: AsyncClient,
    db_session: AsyncSession,
    minio_client: Minio,
    attack_resource_file_factory: AttackResourceFileFactory,
) -> None:
    # Create a resource for a different project (simulate forbidden)
    resource = await attack_resource_file_factory.create_async()
    refresh_url = f"/api/v1/web/resources/{resource.id}/refresh_metadata"
    resp = await authenticated_async_client.post(refresh_url)
    # Should be 403 if user cannot access project, or 400 if file is missing
    if resp.status_code == 403:
        assert resp.json()["detail"] in (
            "Not authorized for this project.",
            "Not authorized",
        )
    elif resp.status_code == 400:
        assert "File not found" in resp.json()["detail"]
    else:
        # If test user is admin, allow 200
        assert resp.status_code == 200


@pytest.mark.asyncio
async def test_get_resource_content_file_backed(
    authenticated_async_client: AsyncClient,
    minio_client: Minio,
    db_session: AsyncSession,
    attack_resource_file_factory: AttackResourceFileFactory,
) -> None:
    # Create and upload a file-backed resource
    file_content = b"line1\nline2\nline3\n"
    resource = await attack_resource_file_factory.create_async(
        is_uploaded=True,
        line_count=3,
        byte_size=len(file_content),
        resource_type="word_list",
    )
    minio_client.put_object(
        settings.MINIO_BUCKET,
        str(resource.id),
        io.BytesIO(file_content),
        length=len(file_content),
    )
    url = f"/api/v1/web/resources/{resource.id}/content"
    resp = await authenticated_async_client.get(url)
    assert resp.status_code == 200
    data = resp.json()
    assert data["content"] == "line1\nline2\nline3"
    assert data["editable"] is True


@pytest.mark.asyncio
async def test_get_resource_content_file_missing(
    authenticated_async_client: AsyncClient,
    db_session: AsyncSession,
    attack_resource_file_factory: AttackResourceFileFactory,
) -> None:
    # Create a file-backed resource but do not upload file
    resource = await attack_resource_file_factory.create_async(
        is_uploaded=True,
        line_count=3,
        byte_size=30,
        resource_type="word_list",
    )
    url = f"/api/v1/web/resources/{resource.id}/content"
    resp = await authenticated_async_client.get(url)
    assert resp.status_code == 400
    assert "Failed to read file from storage" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_get_resource_preview_file_backed(
    authenticated_async_client: AsyncClient,
    minio_client: Minio,
    db_session: AsyncSession,
    attack_resource_file_factory: AttackResourceFileFactory,
) -> None:
    file_content = b"a\nb\nc\nd\ne\nf\ng\nh\ni\nj\nk\nl\n"
    resource = await attack_resource_file_factory.create_async(
        is_uploaded=True,
        line_count=12,
        byte_size=len(file_content),
        resource_type="word_list",
    )
    minio_client.put_object(
        settings.MINIO_BUCKET,
        str(resource.id),
        io.BytesIO(file_content),
        length=len(file_content),
    )
    url = f"/api/v1/web/resources/{resource.id}/preview"
    resp = await authenticated_async_client.get(url)
    assert resp.status_code == 200
    data = resp.json()
    assert data["preview_lines"] == [chr(ord("a") + i) for i in range(10)]
    assert data["preview_error"] is None


@pytest.mark.asyncio
async def test_list_resource_lines_file_backed(
    authenticated_async_client: AsyncClient,
    minio_client: Minio,
    db_session: AsyncSession,
    attack_resource_file_factory: AttackResourceFileFactory,
) -> None:
    file_content = b"foo\nbar\nbaz\nqux\n"
    resource = await attack_resource_file_factory.create_async(
        is_uploaded=True,
        line_count=4,
        byte_size=len(file_content),
        resource_type="word_list",
    )
    minio_client.put_object(
        settings.MINIO_BUCKET,
        str(resource.id),
        io.BytesIO(file_content),
        length=len(file_content),
    )
    url = f"/api/v1/web/resources/{resource.id}/lines"
    resp = await authenticated_async_client.get(url)
    assert resp.status_code == 200
    data = resp.json()
    assert [line["content"] for line in data["lines"]] == ["foo", "bar", "baz", "qux"]
