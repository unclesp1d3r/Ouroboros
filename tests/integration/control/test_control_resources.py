"""
Integration tests for Control API resources endpoints.

The Control API uses API key authentication and offset-based pagination.
All responses must be JSON format.
Error responses must follow RFC9457 format.
"""

from http import HTTPStatus
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from testcontainers.minio import MinioContainer  # type: ignore[import-untyped]

from app.models.attack_resource_file import AttackResourceFile, AttackResourceType
from app.models.project import ProjectUserAssociation, ProjectUserRole
from app.models.user import User
from tests.factories.project_factory import ProjectFactory


async def create_resource(
    db_session: AsyncSession,
    project_id: int | None = None,
    resource_type: AttackResourceType = AttackResourceType.WORD_LIST,
    is_uploaded: bool = True,
    file_name: str = "test-resource.txt",
) -> AttackResourceFile:
    """Helper to create a resource for testing."""
    resource = AttackResourceFile(
        id=uuid4(),
        project_id=project_id,
        file_name=file_name,
        download_url="https://example.com/test",
        checksum="abc123",
        guid=uuid4(),
        resource_type=resource_type,
        line_format="freeform",
        line_encoding="utf-8",
        used_for_modes=[],
        source="upload",
        line_count=100,
        byte_size=1024,
        is_uploaded=is_uploaded,
    )
    db_session.add(resource)
    await db_session.commit()
    await db_session.refresh(resource)
    return resource


@pytest.mark.asyncio
async def test_list_resources_happy_path(
    api_key_client: tuple[AsyncClient, User, str],
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test listing resources with default pagination."""
    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Create resources
    await create_resource(db_session, project_id=project.id, file_name="wordlist1.txt")
    await create_resource(db_session, project_id=project.id, file_name="wordlist2.txt")

    # Test the endpoint
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.get("/api/v1/control/resources", headers=headers)
    assert resp.status_code == HTTPStatus.OK

    data = resp.json()
    assert "items" in data
    assert "total" in data
    assert "limit" in data
    assert "offset" in data
    assert data["total"] >= 2
    assert len(data["items"]) >= 2


@pytest.mark.asyncio
async def test_list_resources_pagination(
    api_key_client: tuple[AsyncClient, User, str],
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test offset-based pagination."""
    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Create multiple resources
    for i in range(5):
        await create_resource(
            db_session, project_id=project.id, file_name=f"wordlist{i:02d}.txt"
        )

    # Test first page
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.get(
        "/api/v1/control/resources?limit=2&offset=0", headers=headers
    )
    assert resp.status_code == HTTPStatus.OK

    data = resp.json()
    assert data["total"] >= 5
    assert data["limit"] == 2
    assert data["offset"] == 0
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_list_resources_type_filter(
    api_key_client: tuple[AsyncClient, User, str],
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test filtering resources by type."""
    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Create resources of different types
    await create_resource(
        db_session,
        project_id=project.id,
        file_name="wordlist.txt",
        resource_type=AttackResourceType.WORD_LIST,
    )
    await create_resource(
        db_session,
        project_id=project.id,
        file_name="rules.rule",
        resource_type=AttackResourceType.RULE_LIST,
    )

    # Test type filter
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.get(
        "/api/v1/control/resources?resource_type=word_list", headers=headers
    )
    assert resp.status_code == HTTPStatus.OK

    data = resp.json()
    assert data["total"] >= 1
    for item in data["items"]:
        assert item["resource_type"] == "word_list"


@pytest.mark.asyncio
async def test_list_resources_search_filter(
    api_key_client: tuple[AsyncClient, User, str],
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test searching resources by name."""
    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Create resources
    await create_resource(db_session, project_id=project.id, file_name="rockyou.txt")
    await create_resource(db_session, project_id=project.id, file_name="common.txt")

    # Test search filter
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.get(
        "/api/v1/control/resources?search=rocky", headers=headers
    )
    assert resp.status_code == HTTPStatus.OK

    data = resp.json()
    assert data["total"] >= 1
    for item in data["items"]:
        assert "rocky" in item["file_name"].lower()


@pytest.mark.asyncio
async def test_list_resources_project_scoping(
    api_key_client: tuple[AsyncClient, User, str],
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test that resources are properly scoped to user's projects."""
    async_client, user, api_key = api_key_client

    # Create two projects
    project1 = await project_factory.create_async()
    project2 = await project_factory.create_async()

    # Associate user only with project1
    assoc = ProjectUserAssociation(
        project_id=project1.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Create resources in both projects
    await create_resource(
        db_session, project_id=project1.id, file_name="accessible.txt"
    )
    await create_resource(
        db_session, project_id=project2.id, file_name="inaccessible.txt"
    )

    # Test that only resources from accessible project are returned
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.get("/api/v1/control/resources", headers=headers)
    assert resp.status_code == HTTPStatus.OK

    data = resp.json()
    # Should only see project1 resources (and unrestricted ones)
    for item in data["items"]:
        if item["project_id"] is not None:
            assert item["project_id"] == project1.id


@pytest.mark.asyncio
async def test_list_resources_unrestricted_visible(
    api_key_client: tuple[AsyncClient, User, str],
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test that unrestricted resources (project_id=None) are visible to all users."""
    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Create an unrestricted resource
    await create_resource(db_session, project_id=None, file_name="global-wordlist.txt")

    # Test that unrestricted resource is visible
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.get(
        "/api/v1/control/resources?search=global", headers=headers
    )
    assert resp.status_code == HTTPStatus.OK

    data = resp.json()
    assert data["total"] >= 1
    assert any(item["file_name"] == "global-wordlist.txt" for item in data["items"])


@pytest.mark.asyncio
async def test_get_resource_happy_path(
    api_key_client: tuple[AsyncClient, User, str],
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test getting a resource by ID."""
    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Create resource
    resource = await create_resource(
        db_session, project_id=project.id, file_name="test-resource.txt"
    )

    # Get resource
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.get(
        f"/api/v1/control/resources/{resource.id}", headers=headers
    )
    assert resp.status_code == HTTPStatus.OK

    data = resp.json()
    assert data["id"] == str(resource.id)
    assert data["file_name"] == "test-resource.txt"
    assert "attacks" in data  # Detail response includes attacks


@pytest.mark.asyncio
async def test_get_resource_not_found(
    api_key_client: tuple[AsyncClient, User, str],
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test getting a non-existent resource returns 404."""
    async_client, user, api_key = api_key_client

    # Create project and associate user (so user has some access)
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Try to get non-existent resource
    headers = {"Authorization": f"Bearer {api_key}"}
    fake_id = uuid4()
    resp = await async_client.get(
        f"/api/v1/control/resources/{fake_id}", headers=headers
    )
    assert resp.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.asyncio
async def test_get_resource_unauthorized_project(
    api_key_client: tuple[AsyncClient, User, str],
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test that accessing resource from unauthorized project returns 403."""
    async_client, user, api_key = api_key_client

    # Create two projects
    project1 = await project_factory.create_async()
    project2 = await project_factory.create_async()

    # Associate user only with project1
    assoc = ProjectUserAssociation(
        project_id=project1.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Create resource in project2
    resource = await create_resource(
        db_session, project_id=project2.id, file_name="inaccessible.txt"
    )

    # Try to access resource
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.get(
        f"/api/v1/control/resources/{resource.id}", headers=headers
    )
    assert resp.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.asyncio
async def test_preview_resource_happy_path(
    api_key_client: tuple[AsyncClient, User, str],
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test previewing resource content."""
    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Create resource with content (not uploaded, so uses content field)
    resource = AttackResourceFile(
        id=uuid4(),
        project_id=project.id,
        file_name="test.txt",
        download_url="",
        checksum="",
        guid=uuid4(),
        resource_type=AttackResourceType.WORD_LIST,
        line_count=3,
        byte_size=20,
        is_uploaded=False,
        content={"lines": ["password", "123456", "admin"]},
    )
    db_session.add(resource)
    await db_session.commit()
    await db_session.refresh(resource)

    # Preview resource
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.get(
        f"/api/v1/control/resources/{resource.id}/preview?lines=10", headers=headers
    )
    assert resp.status_code == HTTPStatus.OK

    data = resp.json()
    assert "preview_lines" in data
    assert data["preview_lines"] == ["password", "123456", "admin"]
    assert data["preview_error"] is None


@pytest.mark.asyncio
async def test_update_resource_happy_path(
    api_key_client: tuple[AsyncClient, User, str],
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test updating resource metadata."""
    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Create resource
    resource = await create_resource(
        db_session, project_id=project.id, file_name="original-name.txt"
    )

    # Update resource
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {"file_name": "updated-name.txt", "file_label": "My Wordlist"}
    resp = await async_client.patch(
        f"/api/v1/control/resources/{resource.id}", headers=headers, json=payload
    )
    assert resp.status_code == HTTPStatus.OK

    data = resp.json()
    assert data["file_name"] == "updated-name.txt"
    assert data["file_label"] == "My Wordlist"


@pytest.mark.asyncio
async def test_update_resource_tags(
    api_key_client: tuple[AsyncClient, User, str],
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test updating resource tags."""
    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Create resource
    resource = await create_resource(db_session, project_id=project.id)

    # Update resource with tags
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {"tags": ["common", "english"]}
    resp = await async_client.patch(
        f"/api/v1/control/resources/{resource.id}", headers=headers, json=payload
    )
    assert resp.status_code == HTTPStatus.OK

    data = resp.json()
    assert data["tags"] == ["common", "english"]


@pytest.mark.asyncio
async def test_delete_resource_happy_path(
    api_key_client: tuple[AsyncClient, User, str],
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test deleting a resource."""
    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Create resource (not uploaded, so no MinIO cleanup needed)
    resource = await create_resource(
        db_session, project_id=project.id, is_uploaded=False
    )

    # Delete resource
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.delete(
        f"/api/v1/control/resources/{resource.id}", headers=headers
    )
    assert resp.status_code == HTTPStatus.NO_CONTENT

    # Verify it's gone
    resp = await async_client.get(
        f"/api/v1/control/resources/{resource.id}", headers=headers
    )
    assert resp.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.asyncio
async def test_resources_unauthenticated(
    async_client: AsyncClient,
) -> None:
    """Test that unauthenticated requests are rejected."""
    resp = await async_client.get("/api/v1/control/resources")
    assert resp.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.asyncio
async def test_pending_resources_visible(
    api_key_client: tuple[AsyncClient, User, str],
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test that pending resources (is_uploaded=false) are visible but marked correctly."""
    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Create pending resource
    await create_resource(
        db_session, project_id=project.id, is_uploaded=False, file_name="pending.txt"
    )

    # List resources
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.get(
        "/api/v1/control/resources?search=pending", headers=headers
    )
    assert resp.status_code == HTTPStatus.OK

    data = resp.json()
    assert data["total"] >= 1
    pending_items = [
        item for item in data["items"] if item["file_name"] == "pending.txt"
    ]
    assert len(pending_items) >= 1
    assert pending_items[0]["is_uploaded"] is False


@pytest.mark.asyncio
async def test_initiate_upload_happy_path(
    api_key_client: tuple[AsyncClient, User, str],
    project_factory: ProjectFactory,
    db_session: AsyncSession,
    minio_container: MinioContainer,
) -> None:
    """Test initiating an upload returns resource ID and presigned URL."""
    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Initiate upload
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "file_name": "rockyou.txt",
        "resource_type": "word_list",
        "project_id": project.id,
    }
    resp = await async_client.post(
        "/api/v1/control/resources/initiate-upload", headers=headers, json=payload
    )
    assert resp.status_code == HTTPStatus.CREATED

    data = resp.json()
    assert "resource_id" in data
    assert "upload_url" in data
    assert "expires_in_seconds" in data
    assert data["expires_in_seconds"] == 3600


@pytest.mark.asyncio
async def test_initiate_upload_with_optional_fields(
    api_key_client: tuple[AsyncClient, User, str],
    project_factory: ProjectFactory,
    db_session: AsyncSession,
    minio_container: MinioContainer,
) -> None:
    """Test initiating upload with optional metadata fields."""
    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Initiate upload with optional fields
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "file_name": "custom-rules.rule",
        "resource_type": "rule_list",
        "project_id": project.id,
        "file_label": "My Custom Rules",
        "tags": ["custom", "ruleset"],
        "line_format": "rule",
        "line_encoding": "ascii",
    }
    resp = await async_client.post(
        "/api/v1/control/resources/initiate-upload", headers=headers, json=payload
    )
    assert resp.status_code == HTTPStatus.CREATED

    data = resp.json()
    assert "resource_id" in data
    assert "upload_url" in data


@pytest.mark.asyncio
async def test_initiate_upload_unauthorized_project(
    api_key_client: tuple[AsyncClient, User, str],
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test initiating upload to unauthorized project returns 403."""
    async_client, _user, api_key = api_key_client

    # Create project but don't associate user
    project = await project_factory.create_async()

    # Try to initiate upload
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "file_name": "test.txt",
        "resource_type": "word_list",
        "project_id": project.id,
    }
    resp = await async_client.post(
        "/api/v1/control/resources/initiate-upload", headers=headers, json=payload
    )
    assert resp.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.asyncio
async def test_initiate_upload_no_project(
    api_key_client: tuple[AsyncClient, User, str],
    project_factory: ProjectFactory,
    db_session: AsyncSession,
    minio_container: MinioContainer,
) -> None:
    """Test initiating upload without project_id creates global resource."""
    async_client, user, api_key = api_key_client

    # Create project and associate user (user needs some access)
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Initiate upload without project_id
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "file_name": "global-wordlist.txt",
        "resource_type": "word_list",
    }
    resp = await async_client.post(
        "/api/v1/control/resources/initiate-upload", headers=headers, json=payload
    )
    assert resp.status_code == HTTPStatus.CREATED

    data = resp.json()
    assert "resource_id" in data


@pytest.mark.asyncio
async def test_confirm_upload_not_found(
    api_key_client: tuple[AsyncClient, User, str],
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test confirming upload for non-existent resource returns 404."""
    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Try to confirm non-existent resource
    headers = {"Authorization": f"Bearer {api_key}"}
    fake_id = uuid4()
    resp = await async_client.post(
        f"/api/v1/control/resources/{fake_id}/confirm-upload", headers=headers
    )
    assert resp.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.asyncio
async def test_confirm_upload_unauthorized_project(
    api_key_client: tuple[AsyncClient, User, str],
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test confirming upload for resource in unauthorized project returns 403."""
    async_client, user, api_key = api_key_client

    # Create two projects
    project1 = await project_factory.create_async()
    project2 = await project_factory.create_async()

    # Associate user only with project1
    assoc = ProjectUserAssociation(
        project_id=project1.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Create pending resource in project2
    resource = await create_resource(
        db_session, project_id=project2.id, is_uploaded=False
    )

    # Try to confirm upload
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.post(
        f"/api/v1/control/resources/{resource.id}/confirm-upload", headers=headers
    )
    assert resp.status_code == HTTPStatus.FORBIDDEN
