"""
Integration tests for Control API hash lists endpoints.

The Control API uses API key authentication and offset-based pagination.
All responses must be JSON format.
Error responses must follow RFC9457 format.
"""

from http import HTTPStatus

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import ProjectUserAssociation, ProjectUserRole
from app.models.user import User
from tests.factories.campaign_factory import CampaignFactory
from tests.factories.hash_list_factory import HashListFactory
from tests.factories.project_factory import ProjectFactory


@pytest.mark.asyncio
async def test_create_hash_list_happy_path(
    api_key_client: tuple[AsyncClient, User, str],
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test creating a hash list."""
    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Create hash list
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "name": "Test Hash List",
        "description": "A test hash list",
        "project_id": project.id,
        "hash_type_id": 0,  # MD5
        "is_unavailable": False,
    }
    resp = await async_client.post(
        "/api/v1/control/hash-lists", headers=headers, json=payload
    )
    assert resp.status_code == HTTPStatus.CREATED

    data = resp.json()
    assert data["name"] == "Test Hash List"
    assert data["description"] == "A test hash list"
    assert data["project_id"] == project.id
    assert data["hash_type_id"] == 0
    assert data["is_unavailable"] is False
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_create_hash_list_unauthorized_project(
    api_key_client: tuple[AsyncClient, User, str],
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test that creating hash list in unauthorized project returns 403."""
    async_client, _user, api_key = api_key_client

    # Create project but don't associate user
    project = await project_factory.create_async()

    # Try to create hash list
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "name": "Test Hash List",
        "project_id": project.id,
        "hash_type_id": 0,
    }
    resp = await async_client.post(
        "/api/v1/control/hash-lists", headers=headers, json=payload
    )
    assert resp.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.asyncio
async def test_list_hash_lists_happy_path(
    api_key_client: tuple[AsyncClient, User, str],
    hash_list_factory: HashListFactory,
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test listing hash lists with default pagination."""
    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Create hash lists
    await hash_list_factory.create_async(name="Hash List Alpha", project_id=project.id)
    await hash_list_factory.create_async(name="Hash List Beta", project_id=project.id)

    # Test the endpoint
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.get("/api/v1/control/hash-lists", headers=headers)
    assert resp.status_code == HTTPStatus.OK

    data = resp.json()
    assert "items" in data
    assert "total" in data
    assert "limit" in data
    assert "offset" in data
    assert data["total"] == 2
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_list_hash_lists_pagination(
    api_key_client: tuple[AsyncClient, User, str],
    hash_list_factory: HashListFactory,
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

    # Create multiple hash lists
    for i in range(5):
        await hash_list_factory.create_async(
            name=f"Hash List {i:02d}", project_id=project.id
        )

    # Test first page
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.get(
        "/api/v1/control/hash-lists?limit=2&offset=0", headers=headers
    )
    assert resp.status_code == HTTPStatus.OK

    data = resp.json()
    assert data["total"] == 5
    assert data["limit"] == 2
    assert data["offset"] == 0
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_list_hash_lists_name_filter(
    api_key_client: tuple[AsyncClient, User, str],
    hash_list_factory: HashListFactory,
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test filtering hash lists by name."""
    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Create hash lists
    await hash_list_factory.create_async(name="Alpha Hash List", project_id=project.id)
    await hash_list_factory.create_async(name="Beta Hash List", project_id=project.id)
    await hash_list_factory.create_async(name="Alpha Test", project_id=project.id)

    # Test name filter
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.get(
        "/api/v1/control/hash-lists?name=Alpha", headers=headers
    )
    assert resp.status_code == HTTPStatus.OK

    data = resp.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_list_hash_lists_project_scoping(
    api_key_client: tuple[AsyncClient, User, str],
    hash_list_factory: HashListFactory,
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test that hash lists are properly scoped to user's projects."""
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

    # Create hash lists in both projects
    await hash_list_factory.create_async(
        name="Accessible Hash List", project_id=project1.id
    )
    await hash_list_factory.create_async(
        name="Inaccessible Hash List", project_id=project2.id
    )

    # Test that only hash lists from accessible project are returned
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.get("/api/v1/control/hash-lists", headers=headers)
    assert resp.status_code == HTTPStatus.OK

    data = resp.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["name"] == "Accessible Hash List"


@pytest.mark.asyncio
async def test_get_hash_list_happy_path(
    api_key_client: tuple[AsyncClient, User, str],
    hash_list_factory: HashListFactory,
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test getting a hash list by ID."""
    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Create hash list
    hash_list = await hash_list_factory.create_async(
        name="Test Hash List", project_id=project.id
    )

    # Get hash list
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.get(
        f"/api/v1/control/hash-lists/{hash_list.id}", headers=headers
    )
    assert resp.status_code == HTTPStatus.OK

    data = resp.json()
    assert data["id"] == hash_list.id
    assert data["name"] == "Test Hash List"


@pytest.mark.asyncio
async def test_get_hash_list_not_found(
    api_key_client: tuple[AsyncClient, User, str],
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test getting a non-existent hash list returns 404."""
    async_client, user, api_key = api_key_client

    # Create project and associate user (so user has some access)
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Try to get non-existent hash list
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.get("/api/v1/control/hash-lists/99999", headers=headers)
    assert resp.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.asyncio
async def test_get_hash_list_unauthorized_project(
    api_key_client: tuple[AsyncClient, User, str],
    hash_list_factory: HashListFactory,
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test that accessing hash list from unauthorized project returns 403."""
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

    # Create hash list in project2
    hash_list = await hash_list_factory.create_async(
        name="Inaccessible", project_id=project2.id
    )

    # Try to access hash list
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.get(
        f"/api/v1/control/hash-lists/{hash_list.id}", headers=headers
    )
    assert resp.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.asyncio
async def test_update_hash_list_happy_path(
    api_key_client: tuple[AsyncClient, User, str],
    hash_list_factory: HashListFactory,
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test updating hash list metadata."""
    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Create hash list
    hash_list = await hash_list_factory.create_async(
        name="Original Name", description="Original description", project_id=project.id
    )

    # Update hash list
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {"name": "Updated Name", "description": "Updated description"}
    resp = await async_client.patch(
        f"/api/v1/control/hash-lists/{hash_list.id}", headers=headers, json=payload
    )
    assert resp.status_code == HTTPStatus.OK

    data = resp.json()
    assert data["name"] == "Updated Name"
    assert data["description"] == "Updated description"


@pytest.mark.asyncio
async def test_delete_hash_list_happy_path(
    api_key_client: tuple[AsyncClient, User, str],
    hash_list_factory: HashListFactory,
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test deleting a hash list."""
    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Create hash list
    hash_list = await hash_list_factory.create_async(
        name="To Delete", project_id=project.id
    )

    # Delete hash list
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.delete(
        f"/api/v1/control/hash-lists/{hash_list.id}", headers=headers
    )
    assert resp.status_code == HTTPStatus.NO_CONTENT

    # Verify it's gone
    resp = await async_client.get(
        f"/api/v1/control/hash-lists/{hash_list.id}", headers=headers
    )
    assert resp.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.asyncio
async def test_delete_hash_list_in_use_by_campaign(
    api_key_client: tuple[AsyncClient, User, str],
    hash_list_factory: HashListFactory,
    campaign_factory: CampaignFactory,
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test that deleting hash list used by campaign returns 400."""
    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Create hash list and campaign using it
    hash_list = await hash_list_factory.create_async(
        name="In Use", project_id=project.id
    )
    await campaign_factory.create_async(
        name="Test Campaign", project_id=project.id, hash_list_id=hash_list.id
    )

    # Try to delete hash list
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.delete(
        f"/api/v1/control/hash-lists/{hash_list.id}", headers=headers
    )
    assert resp.status_code == HTTPStatus.BAD_REQUEST

    data = resp.json()
    assert "used by campaign" in data["detail"]


@pytest.mark.asyncio
async def test_list_hash_lists_no_project_access(
    api_key_client: tuple[AsyncClient, User, str],
    db_session: AsyncSession,
) -> None:
    """Test that user with no project access gets 403."""
    async_client, _user, api_key = api_key_client

    # User has no project associations
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.get("/api/v1/control/hash-lists", headers=headers)
    assert resp.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.asyncio
async def test_hash_lists_unauthenticated(
    async_client: AsyncClient,
) -> None:
    """Test that unauthenticated requests are rejected."""
    resp = await async_client.get("/api/v1/control/hash-lists")
    assert resp.status_code == HTTPStatus.UNAUTHORIZED
