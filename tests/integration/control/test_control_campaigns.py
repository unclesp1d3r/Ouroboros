"""
Integration tests for Control API campaigns endpoints.

The Control API uses API key authentication and offset-based pagination.
All responses must be JSON by default, with optional MsgPack support.
Error responses must follow RFC9457 format.
"""

from http import HTTPStatus

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import ProjectUserAssociation, ProjectUserRole
from app.models.user import User
from tests.factories.attack_factory import AttackFactory
from tests.factories.campaign_factory import CampaignFactory
from tests.factories.hash_list_factory import HashListFactory
from tests.factories.project_factory import ProjectFactory


@pytest.mark.asyncio
async def test_list_campaigns_happy_path(
    api_key_client: tuple[AsyncClient, User, str],
    campaign_factory: CampaignFactory,
    project_factory: ProjectFactory,
    hash_list_factory: HashListFactory,
    db_session: AsyncSession,
) -> None:
    """Test basic campaign listing with default pagination."""
    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Create hash list and campaigns
    hash_list = await hash_list_factory.create_async(project_id=project.id)
    await campaign_factory.create_async(
        name="Campaign Alpha",
        project_id=project.id,
        hash_list_id=hash_list.id,
    )
    await campaign_factory.create_async(
        name="Campaign Beta",
        project_id=project.id,
        hash_list_id=hash_list.id,
    )

    # Test the endpoint with API key authentication
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.get("/api/v1/control/campaigns", headers=headers)
    assert resp.status_code == HTTPStatus.OK

    data = resp.json()
    assert "items" in data
    assert "total" in data
    assert "limit" in data
    assert "offset" in data

    assert data["total"] == 2
    assert data["limit"] == 10
    assert data["offset"] == 0
    assert len(data["items"]) == 2

    # Check campaign data structure
    campaign_names = {item["name"] for item in data["items"]}
    assert campaign_names == {"Campaign Alpha", "Campaign Beta"}


@pytest.mark.asyncio
async def test_list_campaigns_pagination(
    api_key_client: tuple[AsyncClient, User, str],
    campaign_factory: CampaignFactory,
    project_factory: ProjectFactory,
    hash_list_factory: HashListFactory,
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

    # Create hash list and multiple campaigns
    hash_list = await hash_list_factory.create_async(project_id=project.id)
    campaigns = []
    for i in range(5):
        campaign = await campaign_factory.create_async(
            name=f"Campaign {i:02d}",
            project_id=project.id,
            hash_list_id=hash_list.id,
        )
        campaigns.append(campaign)

    # Test first page
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.get(
        "/api/v1/control/campaigns?limit=2&offset=0", headers=headers
    )
    assert resp.status_code == HTTPStatus.OK

    data = resp.json()
    assert data["total"] == 5
    assert data["limit"] == 2
    assert data["offset"] == 0
    assert len(data["items"]) == 2

    # Test second page
    resp = await async_client.get(
        "/api/v1/control/campaigns?limit=2&offset=2", headers=headers
    )
    assert resp.status_code == HTTPStatus.OK

    data = resp.json()
    assert data["total"] == 5
    assert data["limit"] == 2
    assert data["offset"] == 2
    assert len(data["items"]) == 2

    # Test last page
    resp = await async_client.get(
        "/api/v1/control/campaigns?limit=2&offset=4", headers=headers
    )
    assert resp.status_code == HTTPStatus.OK

    data = resp.json()
    assert data["total"] == 5
    assert data["limit"] == 2
    assert data["offset"] == 4
    assert len(data["items"]) == 1


@pytest.mark.asyncio
async def test_list_campaigns_name_filter(
    api_key_client: tuple[AsyncClient, User, str],
    campaign_factory: CampaignFactory,
    project_factory: ProjectFactory,
    hash_list_factory: HashListFactory,
    db_session: AsyncSession,
) -> None:
    """Test filtering campaigns by name."""
    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Create hash list and campaigns
    hash_list = await hash_list_factory.create_async(project_id=project.id)
    await campaign_factory.create_async(
        name="Alpha Campaign",
        project_id=project.id,
        hash_list_id=hash_list.id,
    )
    await campaign_factory.create_async(
        name="Beta Campaign",
        project_id=project.id,
        hash_list_id=hash_list.id,
    )
    await campaign_factory.create_async(
        name="Alpha Test",
        project_id=project.id,
        hash_list_id=hash_list.id,
    )

    # Test name filter
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.get(
        "/api/v1/control/campaigns?name=Alpha", headers=headers
    )
    assert resp.status_code == HTTPStatus.OK

    data = resp.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2

    campaign_names = {item["name"] for item in data["items"]}
    assert campaign_names == {"Alpha Campaign", "Alpha Test"}


@pytest.mark.asyncio
async def test_list_campaigns_project_scoping(
    api_key_client: tuple[AsyncClient, User, str],
    campaign_factory: CampaignFactory,
    project_factory: ProjectFactory,
    hash_list_factory: HashListFactory,
    db_session: AsyncSession,
) -> None:
    """Test that campaigns are properly scoped to user's projects."""
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

    # Create hash lists and campaigns in both projects
    hash_list1 = await hash_list_factory.create_async(project_id=project1.id)
    hash_list2 = await hash_list_factory.create_async(project_id=project2.id)

    await campaign_factory.create_async(
        name="Accessible Campaign",
        project_id=project1.id,
        hash_list_id=hash_list1.id,
    )
    await campaign_factory.create_async(
        name="Inaccessible Campaign",
        project_id=project2.id,
        hash_list_id=hash_list2.id,
    )

    # Test that only campaigns from accessible project are returned
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.get("/api/v1/control/campaigns", headers=headers)
    assert resp.status_code == HTTPStatus.OK

    data = resp.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["name"] == "Accessible Campaign"


@pytest.mark.asyncio
async def test_list_campaigns_specific_project_filter(
    api_key_client: tuple[AsyncClient, User, str],
    campaign_factory: CampaignFactory,
    project_factory: ProjectFactory,
    hash_list_factory: HashListFactory,
    db_session: AsyncSession,
) -> None:
    """Test filtering campaigns by specific project ID."""
    async_client, user, api_key = api_key_client

    # Create two projects and associate user with both
    project1 = await project_factory.create_async()
    project2 = await project_factory.create_async()

    assoc1 = ProjectUserAssociation(
        project_id=project1.id, user_id=user.id, role=ProjectUserRole.member
    )
    assoc2 = ProjectUserAssociation(
        project_id=project2.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add_all([assoc1, assoc2])
    await db_session.commit()

    # Create hash lists and campaigns in both projects
    hash_list1 = await hash_list_factory.create_async(project_id=project1.id)
    hash_list2 = await hash_list_factory.create_async(project_id=project2.id)

    await campaign_factory.create_async(
        name="Project 1 Campaign",
        project_id=project1.id,
        hash_list_id=hash_list1.id,
    )
    await campaign_factory.create_async(
        name="Project 2 Campaign",
        project_id=project2.id,
        hash_list_id=hash_list2.id,
    )

    # Test filtering by project1
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.get(
        f"/api/v1/control/campaigns?project_id={project1.id}", headers=headers
    )
    assert resp.status_code == HTTPStatus.OK

    data = resp.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["name"] == "Project 1 Campaign"

    # Test filtering by project2
    resp = await async_client.get(
        f"/api/v1/control/campaigns?project_id={project2.id}", headers=headers
    )
    assert resp.status_code == HTTPStatus.OK

    data = resp.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["name"] == "Project 2 Campaign"


@pytest.mark.asyncio
async def test_list_campaigns_unauthorized_project(
    api_key_client: tuple[AsyncClient, User, str],
    campaign_factory: CampaignFactory,
    project_factory: ProjectFactory,
    hash_list_factory: HashListFactory,
    db_session: AsyncSession,
) -> None:
    """Test that accessing unauthorized project returns 403."""
    async_client, user, api_key = api_key_client

    # Create two projects, associate user only with project1
    project1 = await project_factory.create_async()
    project2 = await project_factory.create_async()

    assoc = ProjectUserAssociation(
        project_id=project1.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Try to access project2 campaigns
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.get(
        f"/api/v1/control/campaigns?project_id={project2.id}", headers=headers
    )
    assert resp.status_code == HTTPStatus.FORBIDDEN

    data = resp.json()
    assert f"User does not have access to project {project2.id}" in data["detail"]


@pytest.mark.asyncio
async def test_list_campaigns_no_project_access(
    api_key_client: tuple[AsyncClient, User, str],
    db_session: AsyncSession,
) -> None:
    """Test that user with no project access gets 403."""
    async_client, _user, api_key = api_key_client

    # User has no project associations
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.get("/api/v1/control/campaigns", headers=headers)
    assert resp.status_code == HTTPStatus.FORBIDDEN

    data = resp.json()
    assert "User has no project access" in data["detail"]


@pytest.mark.asyncio
async def test_list_campaigns_pagination_limits(
    api_key_client: tuple[AsyncClient, User, str],
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test pagination parameter validation."""
    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Test limit too high
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.get(
        "/api/v1/control/campaigns?limit=101", headers=headers
    )
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

    # Test limit too low
    resp = await async_client.get("/api/v1/control/campaigns?limit=0", headers=headers)
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

    # Test negative offset
    resp = await async_client.get(
        "/api/v1/control/campaigns?offset=-1", headers=headers
    )
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_list_campaigns_empty_result(
    api_key_client: tuple[AsyncClient, User, str],
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test listing campaigns when none exist."""
    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Test empty result
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.get("/api/v1/control/campaigns", headers=headers)
    assert resp.status_code == HTTPStatus.OK

    data = resp.json()
    assert data["total"] == 0
    assert data["limit"] == 10
    assert data["offset"] == 0
    assert len(data["items"]) == 0


@pytest.mark.asyncio
async def test_list_campaigns_unauthenticated(
    async_client: AsyncClient,
) -> None:
    """Test that unauthenticated requests are rejected."""
    resp = await async_client.get("/api/v1/control/campaigns")
    assert resp.status_code == HTTPStatus.UNAUTHORIZED


# =============================================================================
# Campaign CRUD Tests (T7: Campaign CRUD & Validation)
# =============================================================================


@pytest.mark.asyncio
async def test_create_campaign_happy_path(
    api_key_client: tuple[AsyncClient, User, str],
    hash_list_factory: HashListFactory,
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test creating a campaign."""
    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Create hash list
    hash_list = await hash_list_factory.create_async(project_id=project.id)

    # Create campaign
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "name": "Test Campaign",
        "description": "A test campaign",
        "project_id": project.id,
        "hash_list_id": hash_list.id,
        "priority": 50,
    }
    resp = await async_client.post(
        "/api/v1/control/campaigns", headers=headers, json=payload
    )
    assert resp.status_code == HTTPStatus.CREATED

    data = resp.json()
    assert data["name"] == "Test Campaign"
    assert data["description"] == "A test campaign"
    assert data["project_id"] == project.id
    assert data["hash_list_id"] == hash_list.id
    assert data["priority"] == 50
    assert data["state"] == "draft"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_create_campaign_unauthorized_project(
    api_key_client: tuple[AsyncClient, User, str],
    hash_list_factory: HashListFactory,
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test that creating campaign in unauthorized project returns 403."""
    async_client, _user, api_key = api_key_client

    # Create project but don't associate user
    project = await project_factory.create_async()
    hash_list = await hash_list_factory.create_async(project_id=project.id)

    # Try to create campaign
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "name": "Test Campaign",
        "project_id": project.id,
        "hash_list_id": hash_list.id,
    }
    resp = await async_client.post(
        "/api/v1/control/campaigns", headers=headers, json=payload
    )
    assert resp.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.asyncio
async def test_create_campaign_hash_list_not_found(
    api_key_client: tuple[AsyncClient, User, str],
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test that creating campaign with non-existent hash list returns 404."""
    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Try to create campaign with non-existent hash list
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "name": "Test Campaign",
        "project_id": project.id,
        "hash_list_id": 99999,
    }
    resp = await async_client.post(
        "/api/v1/control/campaigns", headers=headers, json=payload
    )
    assert resp.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.asyncio
async def test_get_campaign_happy_path(
    api_key_client: tuple[AsyncClient, User, str],
    campaign_factory: CampaignFactory,
    hash_list_factory: HashListFactory,
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test getting a campaign by ID."""
    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Create hash list and campaign
    hash_list = await hash_list_factory.create_async(project_id=project.id)
    campaign = await campaign_factory.create_async(
        name="Test Campaign", project_id=project.id, hash_list_id=hash_list.id
    )

    # Get campaign
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.get(
        f"/api/v1/control/campaigns/{campaign.id}", headers=headers
    )
    assert resp.status_code == HTTPStatus.OK

    data = resp.json()
    assert data["id"] == campaign.id
    assert data["name"] == "Test Campaign"


@pytest.mark.asyncio
async def test_get_campaign_not_found(
    api_key_client: tuple[AsyncClient, User, str],
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test getting a non-existent campaign returns 404."""
    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Try to get non-existent campaign
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.get("/api/v1/control/campaigns/99999", headers=headers)
    assert resp.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.asyncio
async def test_get_campaign_unauthorized_project(
    api_key_client: tuple[AsyncClient, User, str],
    campaign_factory: CampaignFactory,
    hash_list_factory: HashListFactory,
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test that accessing campaign from unauthorized project returns 403."""
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

    # Create campaign in project2
    hash_list = await hash_list_factory.create_async(project_id=project2.id)
    campaign = await campaign_factory.create_async(
        name="Inaccessible", project_id=project2.id, hash_list_id=hash_list.id
    )

    # Try to access campaign
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.get(
        f"/api/v1/control/campaigns/{campaign.id}", headers=headers
    )
    assert resp.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.asyncio
async def test_update_campaign_happy_path(
    api_key_client: tuple[AsyncClient, User, str],
    campaign_factory: CampaignFactory,
    hash_list_factory: HashListFactory,
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test updating campaign metadata."""
    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Create hash list and campaign
    hash_list = await hash_list_factory.create_async(project_id=project.id)
    campaign = await campaign_factory.create_async(
        name="Original Name",
        description="Original description",
        project_id=project.id,
        hash_list_id=hash_list.id,
    )

    # Update campaign
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {"name": "Updated Name", "description": "Updated description"}
    resp = await async_client.patch(
        f"/api/v1/control/campaigns/{campaign.id}", headers=headers, json=payload
    )
    assert resp.status_code == HTTPStatus.OK

    data = resp.json()
    assert data["name"] == "Updated Name"
    assert data["description"] == "Updated description"


@pytest.mark.asyncio
async def test_delete_campaign_draft_state(
    api_key_client: tuple[AsyncClient, User, str],
    campaign_factory: CampaignFactory,
    hash_list_factory: HashListFactory,
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test deleting a campaign in draft state."""
    from app.models.campaign import CampaignState

    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Create hash list and campaign
    hash_list = await hash_list_factory.create_async(project_id=project.id)
    campaign = await campaign_factory.create_async(
        name="To Delete",
        project_id=project.id,
        hash_list_id=hash_list.id,
        state=CampaignState.DRAFT,
    )

    # Delete campaign
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.delete(
        f"/api/v1/control/campaigns/{campaign.id}", headers=headers
    )
    assert resp.status_code == HTTPStatus.NO_CONTENT

    # Verify it's gone
    resp = await async_client.get(
        f"/api/v1/control/campaigns/{campaign.id}", headers=headers
    )
    assert resp.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.asyncio
async def test_delete_campaign_active_state_fails(
    api_key_client: tuple[AsyncClient, User, str],
    campaign_factory: CampaignFactory,
    hash_list_factory: HashListFactory,
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test that deleting an active campaign returns 400."""
    from app.models.campaign import CampaignState

    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Create active campaign
    hash_list = await hash_list_factory.create_async(project_id=project.id)
    campaign = await campaign_factory.create_async(
        name="Active Campaign",
        project_id=project.id,
        hash_list_id=hash_list.id,
        state=CampaignState.ACTIVE,
    )

    # Try to delete active campaign
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.delete(
        f"/api/v1/control/campaigns/{campaign.id}", headers=headers
    )
    assert resp.status_code == HTTPStatus.BAD_REQUEST

    data = resp.json()
    assert "active" in data["detail"].lower()


@pytest.mark.asyncio
async def test_delete_campaign_paused_state_fails(
    api_key_client: tuple[AsyncClient, User, str],
    campaign_factory: CampaignFactory,
    hash_list_factory: HashListFactory,
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test that deleting a paused campaign returns 400."""
    from app.models.campaign import CampaignState

    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Create paused campaign
    hash_list = await hash_list_factory.create_async(project_id=project.id)
    campaign = await campaign_factory.create_async(
        name="Paused Campaign",
        project_id=project.id,
        hash_list_id=hash_list.id,
        state=CampaignState.PAUSED,
    )

    # Try to delete paused campaign
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.delete(
        f"/api/v1/control/campaigns/{campaign.id}", headers=headers
    )
    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.asyncio
async def test_delete_campaign_completed_state_succeeds(
    api_key_client: tuple[AsyncClient, User, str],
    campaign_factory: CampaignFactory,
    hash_list_factory: HashListFactory,
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test that deleting a completed campaign succeeds."""
    from app.models.campaign import CampaignState

    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Create completed campaign
    hash_list = await hash_list_factory.create_async(project_id=project.id)
    campaign = await campaign_factory.create_async(
        name="Completed Campaign",
        project_id=project.id,
        hash_list_id=hash_list.id,
        state=CampaignState.COMPLETED,
    )

    # Delete completed campaign
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.delete(
        f"/api/v1/control/campaigns/{campaign.id}", headers=headers
    )
    assert resp.status_code == HTTPStatus.NO_CONTENT


# =============================================================================
# Campaign Validation Tests (T7: Campaign CRUD & Validation)
# =============================================================================


@pytest.mark.asyncio
async def test_validate_campaign_valid(
    api_key_client: tuple[AsyncClient, User, str],
    attack_factory: AttackFactory,
    campaign_factory: CampaignFactory,
    hash_list_factory: HashListFactory,
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test validating a campaign that is ready to start."""
    from app.models.campaign import CampaignState

    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Create hash list and campaign with attack
    hash_list = await hash_list_factory.create_async(project_id=project.id)
    campaign = await campaign_factory.create_async(
        name="Valid Campaign",
        project_id=project.id,
        hash_list_id=hash_list.id,
        state=CampaignState.DRAFT,
    )

    # Create attack for campaign
    await attack_factory.create_async(campaign_id=campaign.id)

    # Validate campaign
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.post(
        f"/api/v1/control/campaigns/{campaign.id}/validate", headers=headers
    )
    assert resp.status_code == HTTPStatus.OK

    data = resp.json()
    assert data["valid"] is True
    assert data["errors"] == []
    assert "warnings" in data


@pytest.mark.asyncio
async def test_validate_campaign_no_attacks(
    api_key_client: tuple[AsyncClient, User, str],
    campaign_factory: CampaignFactory,
    hash_list_factory: HashListFactory,
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test validating a campaign with no attacks returns error."""
    from app.models.campaign import CampaignState

    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Create hash list and campaign without attacks
    hash_list = await hash_list_factory.create_async(project_id=project.id)
    campaign = await campaign_factory.create_async(
        name="No Attacks Campaign",
        project_id=project.id,
        hash_list_id=hash_list.id,
        state=CampaignState.DRAFT,
    )

    # Validate campaign
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.post(
        f"/api/v1/control/campaigns/{campaign.id}/validate", headers=headers
    )
    assert resp.status_code == HTTPStatus.OK

    data = resp.json()
    assert data["valid"] is False
    assert len(data["errors"]) >= 1
    error_types = [e["type"] for e in data["errors"]]
    assert "no_attacks" in error_types


@pytest.mark.asyncio
async def test_validate_campaign_unavailable_hash_list(
    api_key_client: tuple[AsyncClient, User, str],
    attack_factory: AttackFactory,
    campaign_factory: CampaignFactory,
    hash_list_factory: HashListFactory,
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test validating a campaign with unavailable hash list returns error."""
    from app.models.campaign import CampaignState

    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Create unavailable hash list and campaign
    hash_list = await hash_list_factory.create_async(
        project_id=project.id, is_unavailable=True
    )
    campaign = await campaign_factory.create_async(
        name="Unavailable Hash List Campaign",
        project_id=project.id,
        hash_list_id=hash_list.id,
        state=CampaignState.DRAFT,
    )

    # Create attack for campaign
    await attack_factory.create_async(campaign_id=campaign.id)

    # Validate campaign
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.post(
        f"/api/v1/control/campaigns/{campaign.id}/validate", headers=headers
    )
    assert resp.status_code == HTTPStatus.OK

    data = resp.json()
    assert data["valid"] is False
    error_types = [e["type"] for e in data["errors"]]
    assert "unavailable_hash_list" in error_types


@pytest.mark.asyncio
async def test_validate_campaign_not_found(
    api_key_client: tuple[AsyncClient, User, str],
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test validating a non-existent campaign returns 404."""
    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Try to validate non-existent campaign
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.post(
        "/api/v1/control/campaigns/99999/validate", headers=headers
    )
    assert resp.status_code == HTTPStatus.NOT_FOUND


# =============================================================================
# Campaign Lifecycle Tests (T8: Campaign Lifecycle Actions)
# =============================================================================


@pytest.mark.asyncio
async def test_start_campaign_happy_path(
    api_key_client: tuple[AsyncClient, User, str],
    campaign_factory: CampaignFactory,
    hash_list_factory: HashListFactory,
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test starting a campaign (draft -> active)."""
    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Create campaign in draft state
    hash_list = await hash_list_factory.create_async(project_id=project.id)
    campaign = await campaign_factory.create_async(
        name="Draft Campaign",
        project_id=project.id,
        hash_list_id=hash_list.id,
        state="draft",
    )

    # Start the campaign
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.post(
        f"/api/v1/control/campaigns/{campaign.id}/start", headers=headers
    )
    assert resp.status_code == HTTPStatus.OK
    data = resp.json()
    assert data["state"] == "active"


@pytest.mark.asyncio
async def test_start_campaign_invalid_state(
    api_key_client: tuple[AsyncClient, User, str],
    campaign_factory: CampaignFactory,
    hash_list_factory: HashListFactory,
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test starting an already active campaign returns 409."""
    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Create campaign in active state
    hash_list = await hash_list_factory.create_async(project_id=project.id)
    campaign = await campaign_factory.create_async(
        name="Active Campaign",
        project_id=project.id,
        hash_list_id=hash_list.id,
        state="active",
    )

    # Try to start (should be idempotent, returns 200 with same state)
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.post(
        f"/api/v1/control/campaigns/{campaign.id}/start", headers=headers
    )
    # The service is idempotent - returns OK if already in target state
    assert resp.status_code == HTTPStatus.OK
    data = resp.json()
    assert data["state"] == "active"


@pytest.mark.asyncio
async def test_stop_campaign_happy_path(
    api_key_client: tuple[AsyncClient, User, str],
    campaign_factory: CampaignFactory,
    hash_list_factory: HashListFactory,
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test stopping a campaign (active -> draft)."""
    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Create campaign in active state
    hash_list = await hash_list_factory.create_async(project_id=project.id)
    campaign = await campaign_factory.create_async(
        name="Active Campaign",
        project_id=project.id,
        hash_list_id=hash_list.id,
        state="active",
    )

    # Stop the campaign
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.post(
        f"/api/v1/control/campaigns/{campaign.id}/stop", headers=headers
    )
    assert resp.status_code == HTTPStatus.OK
    data = resp.json()
    assert data["state"] == "draft"


@pytest.mark.asyncio
async def test_stop_campaign_invalid_state(
    api_key_client: tuple[AsyncClient, User, str],
    campaign_factory: CampaignFactory,
    hash_list_factory: HashListFactory,
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test stopping a draft campaign returns 409."""
    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Create campaign in draft state
    hash_list = await hash_list_factory.create_async(project_id=project.id)
    campaign = await campaign_factory.create_async(
        name="Draft Campaign",
        project_id=project.id,
        hash_list_id=hash_list.id,
        state="draft",
    )

    # Try to stop a draft campaign
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.post(
        f"/api/v1/control/campaigns/{campaign.id}/stop", headers=headers
    )
    # Idempotent - already in draft state
    assert resp.status_code == HTTPStatus.OK


@pytest.mark.asyncio
async def test_pause_campaign_happy_path(
    api_key_client: tuple[AsyncClient, User, str],
    campaign_factory: CampaignFactory,
    hash_list_factory: HashListFactory,
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test pausing a campaign (active -> paused)."""
    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Create campaign in active state
    hash_list = await hash_list_factory.create_async(project_id=project.id)
    campaign = await campaign_factory.create_async(
        name="Active Campaign",
        project_id=project.id,
        hash_list_id=hash_list.id,
        state="active",
    )

    # Pause the campaign
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.post(
        f"/api/v1/control/campaigns/{campaign.id}/pause", headers=headers
    )
    assert resp.status_code == HTTPStatus.OK
    data = resp.json()
    assert data["state"] == "paused"


@pytest.mark.asyncio
async def test_pause_campaign_invalid_state(
    api_key_client: tuple[AsyncClient, User, str],
    campaign_factory: CampaignFactory,
    hash_list_factory: HashListFactory,
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test pausing a draft campaign returns 409."""
    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Create campaign in draft state
    hash_list = await hash_list_factory.create_async(project_id=project.id)
    campaign = await campaign_factory.create_async(
        name="Draft Campaign",
        project_id=project.id,
        hash_list_id=hash_list.id,
        state="draft",
    )

    # Try to pause a draft campaign
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.post(
        f"/api/v1/control/campaigns/{campaign.id}/pause", headers=headers
    )
    assert resp.status_code == HTTPStatus.CONFLICT


@pytest.mark.asyncio
async def test_resume_campaign_happy_path(
    api_key_client: tuple[AsyncClient, User, str],
    campaign_factory: CampaignFactory,
    hash_list_factory: HashListFactory,
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test resuming a campaign (paused -> active)."""
    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Create campaign in paused state
    hash_list = await hash_list_factory.create_async(project_id=project.id)
    campaign = await campaign_factory.create_async(
        name="Paused Campaign",
        project_id=project.id,
        hash_list_id=hash_list.id,
        state="paused",
    )

    # Resume the campaign
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.post(
        f"/api/v1/control/campaigns/{campaign.id}/resume", headers=headers
    )
    assert resp.status_code == HTTPStatus.OK
    data = resp.json()
    assert data["state"] == "active"


@pytest.mark.asyncio
async def test_resume_campaign_invalid_state(
    api_key_client: tuple[AsyncClient, User, str],
    campaign_factory: CampaignFactory,
    hash_list_factory: HashListFactory,
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test resuming a draft campaign returns 409."""
    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Create campaign in draft state
    hash_list = await hash_list_factory.create_async(project_id=project.id)
    campaign = await campaign_factory.create_async(
        name="Draft Campaign",
        project_id=project.id,
        hash_list_id=hash_list.id,
        state="draft",
    )

    # Try to resume a draft campaign
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.post(
        f"/api/v1/control/campaigns/{campaign.id}/resume", headers=headers
    )
    assert resp.status_code == HTTPStatus.CONFLICT


@pytest.mark.asyncio
async def test_archive_campaign_from_draft(
    api_key_client: tuple[AsyncClient, User, str],
    campaign_factory: CampaignFactory,
    hash_list_factory: HashListFactory,
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test archiving a campaign from draft state."""
    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Create campaign in draft state
    hash_list = await hash_list_factory.create_async(project_id=project.id)
    campaign = await campaign_factory.create_async(
        name="Draft Campaign",
        project_id=project.id,
        hash_list_id=hash_list.id,
        state="draft",
    )

    # Archive the campaign
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.post(
        f"/api/v1/control/campaigns/{campaign.id}/archive", headers=headers
    )
    assert resp.status_code == HTTPStatus.OK
    data = resp.json()
    assert data["state"] == "archived"


@pytest.mark.asyncio
async def test_archive_campaign_from_active(
    api_key_client: tuple[AsyncClient, User, str],
    campaign_factory: CampaignFactory,
    hash_list_factory: HashListFactory,
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test archiving a campaign from active state."""
    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Create campaign in active state
    hash_list = await hash_list_factory.create_async(project_id=project.id)
    campaign = await campaign_factory.create_async(
        name="Active Campaign",
        project_id=project.id,
        hash_list_id=hash_list.id,
        state="active",
    )

    # Archive the campaign
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.post(
        f"/api/v1/control/campaigns/{campaign.id}/archive", headers=headers
    )
    assert resp.status_code == HTTPStatus.OK
    data = resp.json()
    assert data["state"] == "archived"


@pytest.mark.asyncio
async def test_unarchive_campaign_happy_path(
    api_key_client: tuple[AsyncClient, User, str],
    campaign_factory: CampaignFactory,
    hash_list_factory: HashListFactory,
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test unarchiving a campaign (archived -> draft)."""
    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Create campaign in archived state
    hash_list = await hash_list_factory.create_async(project_id=project.id)
    campaign = await campaign_factory.create_async(
        name="Archived Campaign",
        project_id=project.id,
        hash_list_id=hash_list.id,
        state="archived",
    )

    # Unarchive the campaign
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.post(
        f"/api/v1/control/campaigns/{campaign.id}/unarchive", headers=headers
    )
    assert resp.status_code == HTTPStatus.OK
    data = resp.json()
    assert data["state"] == "draft"


@pytest.mark.asyncio
async def test_unarchive_campaign_invalid_state(
    api_key_client: tuple[AsyncClient, User, str],
    campaign_factory: CampaignFactory,
    hash_list_factory: HashListFactory,
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test unarchiving an active campaign returns 409."""
    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Create campaign in active state (cannot be unarchived)
    hash_list = await hash_list_factory.create_async(project_id=project.id)
    campaign = await campaign_factory.create_async(
        name="Active Campaign",
        project_id=project.id,
        hash_list_id=hash_list.id,
        state="active",
    )

    # Try to unarchive an active campaign (only archived can be unarchived)
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.post(
        f"/api/v1/control/campaigns/{campaign.id}/unarchive", headers=headers
    )
    assert resp.status_code == HTTPStatus.CONFLICT


@pytest.mark.asyncio
async def test_lifecycle_action_not_found(
    api_key_client: tuple[AsyncClient, User, str],
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test lifecycle action on non-existent campaign returns 404."""
    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Try lifecycle action on non-existent campaign
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.post(
        "/api/v1/control/campaigns/99999/start", headers=headers
    )
    assert resp.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.asyncio
async def test_lifecycle_action_unauthorized_project(
    api_key_client: tuple[AsyncClient, User, str],
    campaign_factory: CampaignFactory,
    hash_list_factory: HashListFactory,
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test lifecycle action on campaign from unauthorized project returns 403."""
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

    # Create campaign in project2
    hash_list = await hash_list_factory.create_async(project_id=project2.id)
    campaign = await campaign_factory.create_async(
        name="Inaccessible",
        project_id=project2.id,
        hash_list_id=hash_list.id,
        state="draft",
    )

    # Try to start campaign in unauthorized project
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.post(
        f"/api/v1/control/campaigns/{campaign.id}/start", headers=headers
    )
    assert resp.status_code == HTTPStatus.FORBIDDEN


# =============================================================================
# Campaign Progress and Metrics Tests (T11: Campaign Status & Metrics)
# =============================================================================


@pytest.mark.asyncio
async def test_get_campaign_progress_happy_path(
    api_key_client: tuple[AsyncClient, User, str],
    campaign_factory: CampaignFactory,
    hash_list_factory: HashListFactory,
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test getting campaign progress."""
    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Create hash list and campaign
    hash_list = await hash_list_factory.create_async(project_id=project.id)
    campaign = await campaign_factory.create_async(
        name="Test Campaign",
        project_id=project.id,
        hash_list_id=hash_list.id,
    )

    # Get campaign progress
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.get(
        f"/api/v1/control/campaigns/{campaign.id}/progress", headers=headers
    )
    assert resp.status_code == HTTPStatus.OK

    data = resp.json()
    assert "active_agents" in data
    assert "total_tasks" in data
    assert data["active_agents"] >= 0
    assert data["total_tasks"] >= 0


@pytest.mark.asyncio
async def test_get_campaign_progress_not_found(
    api_key_client: tuple[AsyncClient, User, str],
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test getting progress for non-existent campaign returns 404."""
    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Try to get progress for non-existent campaign
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.get(
        "/api/v1/control/campaigns/99999/progress", headers=headers
    )
    assert resp.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.asyncio
async def test_get_campaign_progress_unauthorized_project(
    api_key_client: tuple[AsyncClient, User, str],
    campaign_factory: CampaignFactory,
    hash_list_factory: HashListFactory,
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test getting progress for campaign in unauthorized project returns 403."""
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

    # Create campaign in project2
    hash_list = await hash_list_factory.create_async(project_id=project2.id)
    campaign = await campaign_factory.create_async(
        name="Inaccessible",
        project_id=project2.id,
        hash_list_id=hash_list.id,
    )

    # Try to get progress
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.get(
        f"/api/v1/control/campaigns/{campaign.id}/progress", headers=headers
    )
    assert resp.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.asyncio
async def test_get_campaign_metrics_happy_path(
    api_key_client: tuple[AsyncClient, User, str],
    campaign_factory: CampaignFactory,
    hash_list_factory: HashListFactory,
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test getting campaign metrics."""
    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Create hash list and campaign
    hash_list = await hash_list_factory.create_async(project_id=project.id)
    campaign = await campaign_factory.create_async(
        name="Test Campaign",
        project_id=project.id,
        hash_list_id=hash_list.id,
    )

    # Get campaign metrics
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.get(
        f"/api/v1/control/campaigns/{campaign.id}/metrics", headers=headers
    )
    assert resp.status_code == HTTPStatus.OK

    data = resp.json()
    assert "total_hashes" in data
    assert "cracked_hashes" in data
    assert "uncracked_hashes" in data
    assert "percent_cracked" in data
    assert "progress_percent" in data
    assert data["total_hashes"] >= 0
    assert data["cracked_hashes"] >= 0
    assert data["uncracked_hashes"] >= 0
    assert 0 <= data["percent_cracked"] <= 100
    assert 0 <= data["progress_percent"] <= 100


@pytest.mark.asyncio
async def test_get_campaign_metrics_not_found(
    api_key_client: tuple[AsyncClient, User, str],
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test getting metrics for non-existent campaign returns 404."""
    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Try to get metrics for non-existent campaign
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.get(
        "/api/v1/control/campaigns/99999/metrics", headers=headers
    )
    assert resp.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.asyncio
async def test_get_campaign_metrics_unauthorized_project(
    api_key_client: tuple[AsyncClient, User, str],
    campaign_factory: CampaignFactory,
    hash_list_factory: HashListFactory,
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test getting metrics for campaign in unauthorized project returns 403."""
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

    # Create campaign in project2
    hash_list = await hash_list_factory.create_async(project_id=project2.id)
    campaign = await campaign_factory.create_async(
        name="Inaccessible",
        project_id=project2.id,
        hash_list_id=hash_list.id,
    )

    # Try to get metrics
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.get(
        f"/api/v1/control/campaigns/{campaign.id}/metrics", headers=headers
    )
    assert resp.status_code == HTTPStatus.FORBIDDEN
