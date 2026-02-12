"""
Integration tests for Control API attacks endpoints.

The Control API uses API key authentication and offset-based pagination.
All responses must be JSON format.
Error responses must follow RFC9457 format.
"""

from http import HTTPStatus
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attack import AttackState
from app.models.attack_resource_file import AttackResourceFile, AttackResourceType
from app.models.project import ProjectUserAssociation, ProjectUserRole
from app.models.user import User
from tests.factories.attack_factory import AttackFactory
from tests.factories.campaign_factory import CampaignFactory
from tests.factories.hash_list_factory import HashListFactory
from tests.factories.project_factory import ProjectFactory


async def create_wordlist_resource(
    db_session: AsyncSession,
    project_id: int | None = None,
    is_uploaded: bool = True,
    file_name: str = "test-wordlist.txt",
) -> AttackResourceFile:
    """Helper to create a wordlist resource for testing."""
    resource = AttackResourceFile(
        id=uuid4(),
        file_name=file_name,
        download_url=f"http://test/{file_name}",
        checksum="abc123",
        guid=uuid4(),
        resource_type=AttackResourceType.WORD_LIST,
        line_format="freeform",
        line_encoding="utf-8",
        used_for_modes=["dictionary"],
        source="upload",
        line_count=1000,
        byte_size=10000,
        is_uploaded=is_uploaded,
        project_id=project_id,
    )
    db_session.add(resource)
    await db_session.commit()
    await db_session.refresh(resource)
    return resource


# =============================================================================
# List Attacks Tests
# =============================================================================


@pytest.mark.asyncio
async def test_list_attacks_happy_path(
    api_key_client: tuple[AsyncClient, User, str],
    attack_factory: AttackFactory,
    campaign_factory: CampaignFactory,
    hash_list_factory: HashListFactory,
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test basic attack listing with default pagination."""
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

    # Create attacks
    await attack_factory.create_async(
        name="Attack Alpha",
        campaign_id=campaign.id,
        hash_list_id=hash_list.id,
        hash_list_url="http://test/hash.txt",
        hash_list_checksum="abc123",
    )
    await attack_factory.create_async(
        name="Attack Beta",
        campaign_id=campaign.id,
        hash_list_id=hash_list.id,
        hash_list_url="http://test/hash.txt",
        hash_list_checksum="abc123",
    )

    # List attacks
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.get("/api/v1/control/attacks", headers=headers)
    assert resp.status_code == HTTPStatus.OK

    data = resp.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 2
    assert len(data["items"]) >= 2


@pytest.mark.asyncio
async def test_list_attacks_filter_by_campaign(
    api_key_client: tuple[AsyncClient, User, str],
    attack_factory: AttackFactory,
    campaign_factory: CampaignFactory,
    hash_list_factory: HashListFactory,
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test filtering attacks by campaign ID."""
    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Create two campaigns
    hash_list = await hash_list_factory.create_async(project_id=project.id)
    campaign1 = await campaign_factory.create_async(
        name="Campaign 1",
        project_id=project.id,
        hash_list_id=hash_list.id,
    )
    campaign2 = await campaign_factory.create_async(
        name="Campaign 2",
        project_id=project.id,
        hash_list_id=hash_list.id,
    )

    # Create attacks in each campaign
    await attack_factory.create_async(
        name="Attack in Campaign 1",
        campaign_id=campaign1.id,
        hash_list_id=hash_list.id,
        hash_list_url="http://test/hash.txt",
        hash_list_checksum="abc123",
    )
    await attack_factory.create_async(
        name="Attack in Campaign 2",
        campaign_id=campaign2.id,
        hash_list_id=hash_list.id,
        hash_list_url="http://test/hash.txt",
        hash_list_checksum="abc123",
    )

    # Filter by campaign1
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.get(
        f"/api/v1/control/attacks?campaign_id={campaign1.id}", headers=headers
    )
    assert resp.status_code == HTTPStatus.OK

    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "Attack in Campaign 1"


@pytest.mark.asyncio
async def test_list_attacks_project_scoping(
    api_key_client: tuple[AsyncClient, User, str],
    attack_factory: AttackFactory,
    campaign_factory: CampaignFactory,
    hash_list_factory: HashListFactory,
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test that attacks from inaccessible projects are not returned."""
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

    # Create campaigns and attacks in each project
    hash_list1 = await hash_list_factory.create_async(project_id=project1.id)
    hash_list2 = await hash_list_factory.create_async(project_id=project2.id)

    campaign1 = await campaign_factory.create_async(
        name="Accessible Campaign",
        project_id=project1.id,
        hash_list_id=hash_list1.id,
    )
    campaign2 = await campaign_factory.create_async(
        name="Inaccessible Campaign",
        project_id=project2.id,
        hash_list_id=hash_list2.id,
    )

    await attack_factory.create_async(
        name="Accessible Attack",
        campaign_id=campaign1.id,
        hash_list_id=hash_list1.id,
        hash_list_url="http://test/hash.txt",
        hash_list_checksum="abc123",
    )
    await attack_factory.create_async(
        name="Inaccessible Attack",
        campaign_id=campaign2.id,
        hash_list_id=hash_list2.id,
        hash_list_url="http://test/hash.txt",
        hash_list_checksum="abc123",
    )

    # List attacks - should only see accessible attack
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.get("/api/v1/control/attacks", headers=headers)
    assert resp.status_code == HTTPStatus.OK

    data = resp.json()
    names = [item["name"] for item in data["items"]]
    assert "Accessible Attack" in names
    assert "Inaccessible Attack" not in names


# =============================================================================
# Get Attack Tests
# =============================================================================


@pytest.mark.asyncio
async def test_get_attack_happy_path(
    api_key_client: tuple[AsyncClient, User, str],
    attack_factory: AttackFactory,
    campaign_factory: CampaignFactory,
    hash_list_factory: HashListFactory,
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test getting an attack by ID."""
    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Create attack
    hash_list = await hash_list_factory.create_async(project_id=project.id)
    campaign = await campaign_factory.create_async(
        name="Test Campaign",
        project_id=project.id,
        hash_list_id=hash_list.id,
    )
    attack = await attack_factory.create_async(
        name="Test Attack",
        campaign_id=campaign.id,
        hash_list_id=hash_list.id,
        hash_list_url="http://test/hash.txt",
        hash_list_checksum="abc123",
    )

    # Get attack
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.get(
        f"/api/v1/control/attacks/{attack.id}", headers=headers
    )
    assert resp.status_code == HTTPStatus.OK

    data = resp.json()
    assert data["name"] == "Test Attack"
    assert data["id"] == attack.id


@pytest.mark.asyncio
async def test_get_attack_not_found(
    api_key_client: tuple[AsyncClient, User, str],
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test getting a non-existent attack returns 404."""
    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Try to get non-existent attack
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.get("/api/v1/control/attacks/99999", headers=headers)
    assert resp.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.asyncio
async def test_get_attack_unauthorized_project(
    api_key_client: tuple[AsyncClient, User, str],
    attack_factory: AttackFactory,
    campaign_factory: CampaignFactory,
    hash_list_factory: HashListFactory,
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test getting attack from unauthorized project returns 403."""
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

    # Create attack in project2
    hash_list = await hash_list_factory.create_async(project_id=project2.id)
    campaign = await campaign_factory.create_async(
        name="Inaccessible",
        project_id=project2.id,
        hash_list_id=hash_list.id,
    )
    attack = await attack_factory.create_async(
        name="Inaccessible Attack",
        campaign_id=campaign.id,
        hash_list_id=hash_list.id,
        hash_list_url="http://test/hash.txt",
        hash_list_checksum="abc123",
    )

    # Try to get attack
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.get(
        f"/api/v1/control/attacks/{attack.id}", headers=headers
    )
    assert resp.status_code == HTTPStatus.FORBIDDEN


# =============================================================================
# Delete Attack Tests
# =============================================================================


@pytest.mark.asyncio
async def test_delete_attack_happy_path(
    api_key_client: tuple[AsyncClient, User, str],
    attack_factory: AttackFactory,
    campaign_factory: CampaignFactory,
    hash_list_factory: HashListFactory,
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test deleting an attack."""
    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Create attack
    hash_list = await hash_list_factory.create_async(project_id=project.id)
    campaign = await campaign_factory.create_async(
        name="Test Campaign",
        project_id=project.id,
        hash_list_id=hash_list.id,
    )
    attack = await attack_factory.create_async(
        name="To Delete",
        campaign_id=campaign.id,
        hash_list_id=hash_list.id,
        hash_list_url="http://test/hash.txt",
        hash_list_checksum="abc123",
        state="pending",
    )

    # Delete attack
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.delete(
        f"/api/v1/control/attacks/{attack.id}", headers=headers
    )
    assert resp.status_code == HTTPStatus.NO_CONTENT

    # Verify it's gone
    resp = await async_client.get(
        f"/api/v1/control/attacks/{attack.id}", headers=headers
    )
    assert resp.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.asyncio
async def test_delete_running_attack_fails(
    api_key_client: tuple[AsyncClient, User, str],
    attack_factory: AttackFactory,
    campaign_factory: CampaignFactory,
    hash_list_factory: HashListFactory,
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test that deleting a running attack fails with 400."""
    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Create running attack
    hash_list = await hash_list_factory.create_async(project_id=project.id)
    campaign = await campaign_factory.create_async(
        name="Test Campaign",
        project_id=project.id,
        hash_list_id=hash_list.id,
    )
    attack = await attack_factory.create_async(
        name="Running Attack",
        campaign_id=campaign.id,
        hash_list_id=hash_list.id,
        hash_list_url="http://test/hash.txt",
        hash_list_checksum="abc123",
        state="running",
    )

    # Try to delete - should fail
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.delete(
        f"/api/v1/control/attacks/{attack.id}", headers=headers
    )
    assert resp.status_code == HTTPStatus.BAD_REQUEST


# =============================================================================
# Validate Attack Tests
# =============================================================================


@pytest.mark.asyncio
async def test_validate_attack_valid_config(
    api_key_client: tuple[AsyncClient, User, str],
    campaign_factory: CampaignFactory,
    hash_list_factory: HashListFactory,
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test validating a valid attack configuration."""
    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Create campaign and wordlist
    hash_list = await hash_list_factory.create_async(project_id=project.id)
    campaign = await campaign_factory.create_async(
        name="Test Campaign",
        project_id=project.id,
        hash_list_id=hash_list.id,
    )
    wordlist = await create_wordlist_resource(db_session, project_id=project.id)

    # Validate attack config
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "name": "Test Attack",
        "campaign_id": campaign.id,
        "attack_mode": "dictionary",
        "hash_list_id": hash_list.id,
        "hash_list_url": "http://test/hash.txt",
        "hash_list_checksum": "abc123",
        "word_list_id": str(wordlist.id),
    }

    resp = await async_client.post(
        "/api/v1/control/attacks/validate", headers=headers, json=payload
    )
    assert resp.status_code == HTTPStatus.OK

    data = resp.json()
    assert data["valid"] is True
    assert len(data["errors"]) == 0


@pytest.mark.asyncio
async def test_validate_attack_missing_campaign(
    api_key_client: tuple[AsyncClient, User, str],
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test validating attack with missing campaign returns error."""
    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Validate attack config with non-existent campaign
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "name": "Test Attack",
        "campaign_id": 99999,
        "attack_mode": "dictionary",
        "hash_list_id": 1,
        "hash_list_url": "http://test/hash.txt",
        "hash_list_checksum": "abc123",
    }

    resp = await async_client.post(
        "/api/v1/control/attacks/validate", headers=headers, json=payload
    )
    assert resp.status_code == HTTPStatus.OK

    data = resp.json()
    assert data["valid"] is False
    assert any("Campaign 99999 not found" in e for e in data["errors"])


@pytest.mark.asyncio
async def test_validate_attack_missing_wordlist(
    api_key_client: tuple[AsyncClient, User, str],
    campaign_factory: CampaignFactory,
    hash_list_factory: HashListFactory,
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test validating attack with missing wordlist returns error."""
    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Create campaign
    hash_list = await hash_list_factory.create_async(project_id=project.id)
    campaign = await campaign_factory.create_async(
        name="Test Campaign",
        project_id=project.id,
        hash_list_id=hash_list.id,
    )

    # Validate with non-existent wordlist
    fake_uuid = str(uuid4())
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "name": "Test Attack",
        "campaign_id": campaign.id,
        "attack_mode": "dictionary",
        "hash_list_id": hash_list.id,
        "hash_list_url": "http://test/hash.txt",
        "hash_list_checksum": "abc123",
        "word_list_id": fake_uuid,
    }

    resp = await async_client.post(
        "/api/v1/control/attacks/validate", headers=headers, json=payload
    )
    assert resp.status_code == HTTPStatus.OK

    data = resp.json()
    assert data["valid"] is False
    assert any(fake_uuid in e for e in data["errors"])


# =============================================================================
# Estimate Keyspace Tests
# =============================================================================


@pytest.mark.asyncio
async def test_estimate_keyspace_mask_attack(
    api_key_client: tuple[AsyncClient, User, str],
    project_factory: ProjectFactory,
    db_session: AsyncSession,
) -> None:
    """Test estimating keyspace for a mask attack."""
    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Estimate keyspace for mask attack
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "name": "Mask Attack",
        "attack_mode": "mask",
        "mask": "?d?d?d?d",  # 4 digit PIN
    }

    resp = await async_client.post(
        "/api/v1/control/attacks/estimate", headers=headers, json=payload
    )
    assert resp.status_code == HTTPStatus.OK

    data = resp.json()
    assert "keyspace" in data
    assert "complexity_score" in data
    assert data["keyspace"] > 0


# =============================================================================
# Lifecycle Tests
# =============================================================================


@pytest.mark.asyncio
async def test_start_attack_happy_path(
    api_key_client: tuple[AsyncClient, User, str],
    project_factory: ProjectFactory,
    campaign_factory: CampaignFactory,
    attack_factory: AttackFactory,
    hash_list_factory: HashListFactory,
    db_session: AsyncSession,
) -> None:
    """Test starting an attack successfully."""
    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Create hash list, campaign and attack
    hash_list = await hash_list_factory.create_async(project_id=project.id)
    campaign = await campaign_factory.create_async(
        project_id=project.id, hash_list_id=hash_list.id
    )
    attack = await attack_factory.create_async(campaign_id=campaign.id)

    # Start attack
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.post(
        f"/api/v1/control/attacks/{attack.id}/start", headers=headers
    )
    assert resp.status_code == HTTPStatus.OK

    data = resp.json()
    assert data["id"] == attack.id
    assert data["state"] == "running"


@pytest.mark.asyncio
async def test_start_attack_invalid_state(
    api_key_client: tuple[AsyncClient, User, str],
    project_factory: ProjectFactory,
    campaign_factory: CampaignFactory,
    attack_factory: AttackFactory,
    hash_list_factory: HashListFactory,
    db_session: AsyncSession,
) -> None:
    """Test starting an attack that is already running fails."""
    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Create hash list, campaign and completed attack
    hash_list = await hash_list_factory.create_async(project_id=project.id)
    campaign = await campaign_factory.create_async(
        project_id=project.id, hash_list_id=hash_list.id
    )
    attack = await attack_factory.create_async(
        campaign_id=campaign.id, state=AttackState.COMPLETED
    )

    # Try to start completed attack
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.post(
        f"/api/v1/control/attacks/{attack.id}/start", headers=headers
    )
    assert resp.status_code == HTTPStatus.CONFLICT


@pytest.mark.asyncio
async def test_pause_attack_happy_path(
    api_key_client: tuple[AsyncClient, User, str],
    project_factory: ProjectFactory,
    campaign_factory: CampaignFactory,
    attack_factory: AttackFactory,
    hash_list_factory: HashListFactory,
    db_session: AsyncSession,
) -> None:
    """Test pausing a running attack successfully."""
    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Create hash list, campaign and running attack
    hash_list = await hash_list_factory.create_async(project_id=project.id)
    campaign = await campaign_factory.create_async(
        project_id=project.id, hash_list_id=hash_list.id
    )
    attack = await attack_factory.create_async(
        campaign_id=campaign.id, state=AttackState.RUNNING
    )

    # Pause attack
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.post(
        f"/api/v1/control/attacks/{attack.id}/pause", headers=headers
    )
    assert resp.status_code == HTTPStatus.OK

    data = resp.json()
    assert data["id"] == attack.id
    assert data["state"] == "paused"


@pytest.mark.asyncio
async def test_stop_attack_happy_path(
    api_key_client: tuple[AsyncClient, User, str],
    project_factory: ProjectFactory,
    campaign_factory: CampaignFactory,
    attack_factory: AttackFactory,
    hash_list_factory: HashListFactory,
    db_session: AsyncSession,
) -> None:
    """Test stopping a running attack successfully."""
    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Create hash list, campaign and running attack
    hash_list = await hash_list_factory.create_async(project_id=project.id)
    campaign = await campaign_factory.create_async(
        project_id=project.id, hash_list_id=hash_list.id
    )
    attack = await attack_factory.create_async(
        campaign_id=campaign.id, state=AttackState.RUNNING
    )

    # Stop attack
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.post(
        f"/api/v1/control/attacks/{attack.id}/stop", headers=headers
    )
    assert resp.status_code == HTTPStatus.OK

    data = resp.json()
    assert data["id"] == attack.id
    assert data["state"] == "abandoned"


@pytest.mark.asyncio
async def test_resume_attack_happy_path(
    api_key_client: tuple[AsyncClient, User, str],
    project_factory: ProjectFactory,
    campaign_factory: CampaignFactory,
    attack_factory: AttackFactory,
    hash_list_factory: HashListFactory,
    db_session: AsyncSession,
) -> None:
    """Test resuming a paused attack successfully."""
    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Create hash list, campaign and paused attack
    hash_list = await hash_list_factory.create_async(project_id=project.id)
    campaign = await campaign_factory.create_async(
        project_id=project.id, hash_list_id=hash_list.id
    )
    attack = await attack_factory.create_async(
        campaign_id=campaign.id, state=AttackState.PAUSED
    )

    # Resume attack
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.post(
        f"/api/v1/control/attacks/{attack.id}/resume", headers=headers
    )
    assert resp.status_code == HTTPStatus.OK

    data = resp.json()
    assert data["id"] == attack.id
    assert data["state"] == "running"


@pytest.mark.asyncio
async def test_get_attack_metrics_happy_path(
    api_key_client: tuple[AsyncClient, User, str],
    project_factory: ProjectFactory,
    campaign_factory: CampaignFactory,
    attack_factory: AttackFactory,
    hash_list_factory: HashListFactory,
    db_session: AsyncSession,
) -> None:
    """Test getting attack metrics successfully."""
    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Create hash list, campaign and attack
    hash_list = await hash_list_factory.create_async(project_id=project.id)
    campaign = await campaign_factory.create_async(
        project_id=project.id, hash_list_id=hash_list.id
    )
    attack = await attack_factory.create_async(campaign_id=campaign.id)

    # Get metrics
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = await async_client.get(
        f"/api/v1/control/attacks/{attack.id}/metrics", headers=headers
    )
    assert resp.status_code == HTTPStatus.OK

    data = resp.json()
    assert "hashes_per_sec" in data
    assert "total_hashes" in data
    assert "agent_count" in data


# =============================================================================
# Reorder Tests
# =============================================================================


@pytest.mark.asyncio
async def test_reorder_attacks_happy_path(
    api_key_client: tuple[AsyncClient, User, str],
    project_factory: ProjectFactory,
    campaign_factory: CampaignFactory,
    attack_factory: AttackFactory,
    hash_list_factory: HashListFactory,
    db_session: AsyncSession,
) -> None:
    """Test reordering attacks successfully."""
    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Create hash list, campaign and multiple attacks
    hash_list = await hash_list_factory.create_async(project_id=project.id)
    campaign = await campaign_factory.create_async(
        project_id=project.id, hash_list_id=hash_list.id
    )
    attack1 = await attack_factory.create_async(campaign_id=campaign.id, position=0)
    attack2 = await attack_factory.create_async(campaign_id=campaign.id, position=1)
    attack3 = await attack_factory.create_async(campaign_id=campaign.id, position=2)

    # Reorder attacks (reverse order)
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "attack_order": [
            {"attack_id": attack3.id, "priority": 0},
            {"attack_id": attack2.id, "priority": 1},
            {"attack_id": attack1.id, "priority": 2},
        ]
    }
    resp = await async_client.post(
        f"/api/v1/control/campaigns/{campaign.id}/attacks/reorder",
        headers=headers,
        json=payload,
    )
    assert resp.status_code == HTTPStatus.OK

    data = resp.json()
    assert len(data) == 3


@pytest.mark.asyncio
async def test_reorder_attacks_invalid_attack(
    api_key_client: tuple[AsyncClient, User, str],
    project_factory: ProjectFactory,
    campaign_factory: CampaignFactory,
    attack_factory: AttackFactory,
    hash_list_factory: HashListFactory,
    db_session: AsyncSession,
) -> None:
    """Test reordering with invalid attack ID fails."""
    async_client, user, api_key = api_key_client

    # Create project and associate user
    project = await project_factory.create_async()
    assoc = ProjectUserAssociation(
        project_id=project.id, user_id=user.id, role=ProjectUserRole.member
    )
    db_session.add(assoc)
    await db_session.commit()

    # Create hash list, campaign and attack
    hash_list = await hash_list_factory.create_async(project_id=project.id)
    campaign = await campaign_factory.create_async(
        project_id=project.id, hash_list_id=hash_list.id
    )
    attack = await attack_factory.create_async(campaign_id=campaign.id)

    # Try to reorder with non-existent attack
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "attack_order": [
            {"attack_id": attack.id, "priority": 0},
            {"attack_id": 99999, "priority": 1},  # Non-existent
        ]
    }
    resp = await async_client.post(
        f"/api/v1/control/campaigns/{campaign.id}/attacks/reorder",
        headers=headers,
        json=payload,
    )
    assert resp.status_code == HTTPStatus.NOT_FOUND
