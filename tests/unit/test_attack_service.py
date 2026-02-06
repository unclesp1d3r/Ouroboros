"""
Unit tests for attack service.
"""

from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.services.attack_service import (
    _safe_int,
    attack_to_template,
    bulk_delete_attacks_service,
    create_attack_service,
    delete_attack_service,
    duplicate_attack_service,
    estimate_attack_keyspace_and_complexity,
    get_attack_list_service,
    get_attack_performance_summary_service,
    get_attack_service,
    move_attack_service,
    update_attack_service,
)
from app.models.attack import Attack, AttackMode
from app.schemas.attack import (
    AttackCreate,
    AttackMoveDirection,
    AttackUpdate,
    EstimateAttackRequest,
)
from tests.factories.attack_factory import AttackFactory
from tests.factories.campaign_factory import CampaignFactory
from tests.factories.project_factory import ProjectFactory


@pytest.mark.asyncio
async def test_create_attack_service_success(db_session: AsyncSession) -> None:
    """Test successful attack creation."""
    # Set factory sessions
    ProjectFactory.__async_session__ = db_session
    CampaignFactory.__async_session__ = db_session
    from tests.factories.hash_list_factory import HashListFactory
    from tests.utils.hash_type_utils import get_or_create_hash_type

    HashListFactory.__async_session__ = db_session

    # Create test data
    project = await ProjectFactory.create_async()

    # Create hash type and hash list
    hash_type = await get_or_create_hash_type(db_session, 0, "MD5")
    hash_list = await HashListFactory.create_async(
        project_id=project.id, hash_type_id=hash_type.id
    )

    campaign = await CampaignFactory.create_async(
        project_id=project.id, hash_list_id=hash_list.id
    )

    # Create attack data
    attack_data = AttackCreate(
        name="Dictionary Attack",
        attack_mode=AttackMode.DICTIONARY,
        campaign_id=campaign.id,
        increment_mode=False,
        increment_minimum=0,
        increment_maximum=0,
        hash_list_id=hash_list.id,
        hash_list_url="http://test.example.com/hashlist",
        hash_list_checksum="abc123",
    )

    # Create attack
    result = await create_attack_service(attack_data, db_session)

    assert result.name == "Dictionary Attack"
    assert result.attack_mode == AttackMode.DICTIONARY
    assert result.campaign_id == campaign.id
    assert result.priority == 0


@pytest.mark.asyncio
async def test_get_attack_service_success(db_session: AsyncSession) -> None:
    """Test successful attack retrieval."""
    # Set factory sessions
    AttackFactory.__async_session__ = db_session
    CampaignFactory.__async_session__ = db_session
    ProjectFactory.__async_session__ = db_session

    # Create test data with hash list
    from tests.factories.hash_list_factory import HashListFactory
    from tests.utils.hash_type_utils import get_or_create_hash_type

    HashListFactory.__async_session__ = db_session

    project = await ProjectFactory.create_async()

    # Create hash type and hash list
    hash_type = await get_or_create_hash_type(db_session, 0, "MD5")
    hash_list = await HashListFactory.create_async(
        project_id=project.id, hash_type_id=hash_type.id
    )

    campaign = await CampaignFactory.create_async(
        project_id=project.id, hash_list_id=hash_list.id
    )
    attack = await AttackFactory.create_async(campaign_id=campaign.id)

    # Get attack
    result = await get_attack_service(attack.id, db_session)

    assert result.id == attack.id
    assert result.name == attack.name
    assert result.campaign_id == campaign.id


@pytest.mark.asyncio
async def test_get_attack_list_service_success(db_session: AsyncSession) -> None:
    """Test successful attack listing."""
    # Set factory sessions
    AttackFactory.__async_session__ = db_session
    CampaignFactory.__async_session__ = db_session
    ProjectFactory.__async_session__ = db_session
    from tests.factories.hash_list_factory import HashListFactory
    from tests.utils.hash_type_utils import get_or_create_hash_type

    HashListFactory.__async_session__ = db_session

    # Create test data
    project = await ProjectFactory.create_async()
    hash_type = await get_or_create_hash_type(db_session, 0, "MD5")
    hash_list = await HashListFactory.create_async(
        project_id=project.id, hash_type_id=hash_type.id
    )
    campaign = await CampaignFactory.create_async(
        project_id=project.id, hash_list_id=hash_list.id
    )

    # Create test attacks
    await AttackFactory.create_async(
        name="Attack 1",
        campaign_id=campaign.id,
    )
    await AttackFactory.create_async(
        name="Attack 2",
        campaign_id=campaign.id,
    )

    # List attacks
    result, total, pages = await get_attack_list_service(db_session, page=1, size=20)

    assert len(result) >= 2  # May have other attacks from other tests
    assert total >= 2
    assert pages >= 1


@pytest.mark.asyncio
@patch("app.core.services.attack_service._broadcast_campaign_update")
async def test_update_attack_service_success(
    mock_broadcast: AsyncMock,
    db_session: AsyncSession,
) -> None:
    """Test successful attack update."""
    # Set factory sessions
    AttackFactory.__async_session__ = db_session
    CampaignFactory.__async_session__ = db_session
    ProjectFactory.__async_session__ = db_session

    # Create test data with hash list
    from tests.factories.hash_list_factory import HashListFactory
    from tests.utils.hash_type_utils import get_or_create_hash_type

    HashListFactory.__async_session__ = db_session

    project = await ProjectFactory.create_async()

    # Create hash type and hash list
    hash_type = await get_or_create_hash_type(db_session, 0, "MD5")
    hash_list = await HashListFactory.create_async(
        project_id=project.id, hash_type_id=hash_type.id
    )

    campaign = await CampaignFactory.create_async(
        project_id=project.id, hash_list_id=hash_list.id
    )
    attack = await AttackFactory.create_async(
        name="Original Attack",
        campaign_id=campaign.id,
    )

    # Update attack
    update_data = AttackUpdate(
        name="Updated Attack",
        optimized=False,
    )
    result = await update_attack_service(attack.id, update_data, db_session)

    assert result.id == attack.id
    assert result.name == "Updated Attack"
    assert result.optimized is False


@pytest.mark.asyncio
@patch("app.core.services.attack_service._broadcast_campaign_update")
async def test_delete_attack_service_success(
    mock_broadcast: AsyncMock,
    db_session: AsyncSession,
) -> None:
    """Test successful attack deletion."""
    # Set factory sessions
    AttackFactory.__async_session__ = db_session
    CampaignFactory.__async_session__ = db_session
    ProjectFactory.__async_session__ = db_session

    # Create test data with hash list
    from tests.factories.hash_list_factory import HashListFactory
    from tests.utils.hash_type_utils import get_or_create_hash_type

    HashListFactory.__async_session__ = db_session

    project = await ProjectFactory.create_async()

    # Create hash type and hash list
    hash_type = await get_or_create_hash_type(db_session, 0, "MD5")
    hash_list = await HashListFactory.create_async(
        project_id=project.id, hash_type_id=hash_type.id
    )

    campaign = await CampaignFactory.create_async(
        project_id=project.id, hash_list_id=hash_list.id
    )
    attack = await AttackFactory.create_async(campaign_id=campaign.id)

    attack_id = attack.id

    # Delete attack
    result = await delete_attack_service(attack_id, db_session)

    assert result["deleted"] is True
    assert result["id"] == attack_id


@pytest.mark.asyncio
async def test_estimate_attack_keyspace_and_complexity_dictionary() -> None:
    """Test attack keyspace estimation for dictionary attack."""
    # Create estimation request with all required fields
    request_data = EstimateAttackRequest(
        name="Test Dictionary Attack",
        description="Test description",
        attack_mode=AttackMode.DICTIONARY,
        mask=None,
        custom_charset_1=None,
        custom_charset_2=None,
        custom_charset_3=None,
        custom_charset_4=None,
        increment_mode=False,
        increment_minimum=1,
        increment_maximum=8,
        # Required fields for AttackCreate validation
        hash_list_id=1,
        hash_list_url="http://test.example.com/hashlist",
        hash_list_checksum="abc123",
        # Add mock word count for estimation
        wordlist_size=10000,
        rule_count=100,
    )

    # Estimate keyspace
    result = await estimate_attack_keyspace_and_complexity(request_data)

    assert result.keyspace > 0
    assert result.complexity_score >= 0


@pytest.mark.asyncio
async def test_estimate_attack_keyspace_and_complexity_mask() -> None:
    """Test attack keyspace estimation for mask attack."""
    # Create estimation request with all required fields
    request_data = EstimateAttackRequest(
        name="Test Mask Attack",
        description="Test description",
        attack_mode=AttackMode.MASK,
        mask="?l?l?l?d?d",  # 3 lowercase + 2 digits
        custom_charset_1=None,
        custom_charset_2=None,
        custom_charset_3=None,
        custom_charset_4=None,
        increment_mode=False,
        increment_minimum=1,
        increment_maximum=8,
        # Required fields for AttackCreate validation
        hash_list_id=1,
        hash_list_url="http://test.example.com/hashlist",
        hash_list_checksum="abc123",
    )

    # Estimate keyspace
    result = await estimate_attack_keyspace_and_complexity(request_data)

    # Expected: 26^3 * 10^2 = 1,757,600
    assert result.keyspace == 1757600
    assert result.complexity_score >= 0


@pytest.mark.asyncio
@patch("app.core.services.attack_service._broadcast_campaign_update")
async def test_move_attack_service_up(
    mock_broadcast: AsyncMock,
    db_session: AsyncSession,
) -> None:
    """Test moving attack up in priority order."""
    # Set factory sessions
    AttackFactory.__async_session__ = db_session
    CampaignFactory.__async_session__ = db_session
    ProjectFactory.__async_session__ = db_session

    # Create test data with hash list
    from tests.factories.hash_list_factory import HashListFactory
    from tests.utils.hash_type_utils import get_or_create_hash_type

    HashListFactory.__async_session__ = db_session

    project = await ProjectFactory.create_async()

    # Create hash type and hash list
    hash_type = await get_or_create_hash_type(db_session, 0, "MD5")
    hash_list = await HashListFactory.create_async(
        project_id=project.id, hash_type_id=hash_type.id
    )

    campaign = await CampaignFactory.create_async(
        project_id=project.id, hash_list_id=hash_list.id
    )

    # Create attacks with specific order
    attack1 = await AttackFactory.create_async(
        name="Attack 1",
        campaign_id=campaign.id,
        position=0,
    )
    attack2 = await AttackFactory.create_async(
        name="Attack 2",
        campaign_id=campaign.id,
        position=1,
    )

    # Move attack 2 up (should become priority 1)
    await move_attack_service(attack2.id, AttackMoveDirection.UP, db_session)

    # Verify order changed by refetching from database
    attack1_result = await db_session.execute(
        select(Attack).where(Attack.id == attack1.id)
    )
    updated_attack1 = attack1_result.scalar_one()

    attack2_result = await db_session.execute(
        select(Attack).where(Attack.id == attack2.id)
    )
    updated_attack2 = attack2_result.scalar_one()

    assert updated_attack2.position == 0
    assert updated_attack1.position == 1


@pytest.mark.asyncio
async def test_duplicate_attack_service_success(db_session: AsyncSession) -> None:
    """Test successful attack duplication."""
    # Set factory sessions
    AttackFactory.__async_session__ = db_session
    CampaignFactory.__async_session__ = db_session
    ProjectFactory.__async_session__ = db_session

    # Create test data with hash list
    from tests.factories.hash_list_factory import HashListFactory
    from tests.utils.hash_type_utils import get_or_create_hash_type

    HashListFactory.__async_session__ = db_session

    project = await ProjectFactory.create_async()

    # Create hash type and hash list
    hash_type = await get_or_create_hash_type(db_session, 0, "MD5")
    hash_list = await HashListFactory.create_async(
        project_id=project.id, hash_type_id=hash_type.id
    )

    campaign = await CampaignFactory.create_async(
        project_id=project.id, hash_list_id=hash_list.id
    )
    original_attack = await AttackFactory.create_async(
        name="Original Attack",
        campaign_id=campaign.id,
        position=0,
    )

    # Duplicate attack
    result = await duplicate_attack_service(original_attack.id, db_session)

    assert result.name == "Original Attack (Copy)"
    assert result.campaign_id == campaign.id
    assert result.position == 1  # Should be next in order
    assert result.id != original_attack.id


@pytest.mark.asyncio
async def test_bulk_delete_attacks_service_success(db_session: AsyncSession) -> None:
    """Test successful bulk attack deletion."""
    # Set factory sessions
    AttackFactory.__async_session__ = db_session
    CampaignFactory.__async_session__ = db_session
    ProjectFactory.__async_session__ = db_session

    # Create test data with hash list
    from tests.factories.hash_list_factory import HashListFactory
    from tests.utils.hash_type_utils import get_or_create_hash_type

    HashListFactory.__async_session__ = db_session

    project = await ProjectFactory.create_async()

    # Create hash type and hash list
    hash_type = await get_or_create_hash_type(db_session, 0, "MD5")
    hash_list = await HashListFactory.create_async(
        project_id=project.id, hash_type_id=hash_type.id
    )

    campaign = await CampaignFactory.create_async(
        project_id=project.id, hash_list_id=hash_list.id
    )

    # Create test attacks
    attack1 = await AttackFactory.create_async(campaign_id=campaign.id)
    attack2 = await AttackFactory.create_async(campaign_id=campaign.id)

    # Bulk delete attacks
    result = await bulk_delete_attacks_service([attack1.id, attack2.id], db_session)

    assert len(result["deleted_ids"]) == 2
    assert attack1.id in result["deleted_ids"]
    assert attack2.id in result["deleted_ids"]
    assert len(result["not_found_ids"]) == 0


@pytest.mark.asyncio
async def test_get_attack_performance_summary_service_success(
    db_session: AsyncSession,
) -> None:
    """Test successful attack performance summary retrieval."""
    # Set factory sessions
    AttackFactory.__async_session__ = db_session
    CampaignFactory.__async_session__ = db_session
    ProjectFactory.__async_session__ = db_session

    # Create test data with hash list
    from tests.factories.hash_list_factory import HashListFactory
    from tests.utils.hash_type_utils import get_or_create_hash_type

    HashListFactory.__async_session__ = db_session

    project = await ProjectFactory.create_async()

    # Create hash type and hash list
    hash_type = await get_or_create_hash_type(db_session, 0, "MD5")
    hash_list = await HashListFactory.create_async(
        project_id=project.id, hash_type_id=hash_type.id
    )

    campaign = await CampaignFactory.create_async(
        project_id=project.id, hash_list_id=hash_list.id
    )
    attack = await AttackFactory.create_async(campaign_id=campaign.id)

    # Get performance summary
    result = await get_attack_performance_summary_service(attack.id, db_session)

    assert result.attack.id == attack.id
    assert result.total_hashes >= 0
    assert result.hashes_done >= 0
    assert result.agent_count >= 0
    assert result.progress >= 0.0
    assert result.progress <= 100.0
    assert result.hashes_per_sec >= 0.0


def test_attack_to_template() -> None:
    """Test attack to template conversion."""
    # Create a mock attack with correct field names from the Attack model
    attack = Attack(
        id=1,
        name="Test Attack",
        attack_mode=AttackMode.DICTIONARY,
        position=1,
        optimized=True,
        slow_candidate_generators=False,
        increment_mode=False,
        increment_minimum=0,
        increment_maximum=0,
        left_rule=None,
        right_rule=None,
        custom_charset_1=None,
        custom_charset_2=None,
        custom_charset_3=None,
        custom_charset_4=None,
        mask=None,
        description="Test description",
        hash_list_id=1,
        hash_list_url="http://test.com",
        hash_list_checksum="abc123",
        campaign_id=1,
    )

    # Convert to template
    template = attack_to_template(attack)

    assert template.mode == AttackMode.DICTIONARY
    assert template.position == 1
    assert template.comment == "Test description"
    assert template.min_length == 0
    assert template.max_length == 0


def test_safe_int() -> None:
    """Test _safe_int utility function."""
    assert _safe_int(42, 0) == 42
    assert _safe_int("42", 0) == 42
    assert _safe_int("invalid", 10) == 10
    assert _safe_int(None, 5) == 5
    assert _safe_int(3.14, 0) == 0  # Non-int, non-string


# --- State machine integration tests ---


@pytest.mark.asyncio
@patch("app.core.services.attack_service._broadcast_campaign_update")
async def test_delete_attack_service_aborts_running_attack(
    mock_broadcast: AsyncMock,
    db_session: AsyncSession,
) -> None:
    """Test that delete_attack_service marks RUNNING attack as ABANDONED."""
    from app.models.attack import AttackState
    from tests.factories.hash_list_factory import HashListFactory
    from tests.utils.hash_type_utils import get_or_create_hash_type

    # Set factory sessions
    AttackFactory.__async_session__ = db_session
    CampaignFactory.__async_session__ = db_session
    ProjectFactory.__async_session__ = db_session
    HashListFactory.__async_session__ = db_session

    project = await ProjectFactory.create_async()
    hash_type = await get_or_create_hash_type(db_session, 0, "MD5")
    hash_list = await HashListFactory.create_async(
        project_id=project.id, hash_type_id=hash_type.id
    )
    campaign = await CampaignFactory.create_async(
        project_id=project.id, hash_list_id=hash_list.id
    )
    attack = await AttackFactory.create_async(
        campaign_id=campaign.id,
        state=AttackState.RUNNING,
    )

    # Delete running attack (should abort instead of delete)
    result = await delete_attack_service(attack.id, db_session)

    assert result["deleted"] is True
    assert result["id"] == attack.id

    # Verify attack is marked as ABANDONED (not actually deleted)
    attack_result = await db_session.execute(
        select(Attack).where(Attack.id == attack.id)
    )
    updated_attack = attack_result.scalar_one()
    assert updated_attack.state == AttackState.ABANDONED


@pytest.mark.asyncio
@patch("app.core.services.attack_service._broadcast_campaign_update")
async def test_delete_attack_service_aborts_paused_attack(
    mock_broadcast: AsyncMock,
    db_session: AsyncSession,
) -> None:
    """Test that delete_attack_service marks PAUSED attack as ABANDONED."""
    from app.models.attack import AttackState
    from tests.factories.hash_list_factory import HashListFactory
    from tests.utils.hash_type_utils import get_or_create_hash_type

    # Set factory sessions
    AttackFactory.__async_session__ = db_session
    CampaignFactory.__async_session__ = db_session
    ProjectFactory.__async_session__ = db_session
    HashListFactory.__async_session__ = db_session

    project = await ProjectFactory.create_async()
    hash_type = await get_or_create_hash_type(db_session, 0, "MD5")
    hash_list = await HashListFactory.create_async(
        project_id=project.id, hash_type_id=hash_type.id
    )
    campaign = await CampaignFactory.create_async(
        project_id=project.id, hash_list_id=hash_list.id
    )
    attack = await AttackFactory.create_async(
        campaign_id=campaign.id,
        state=AttackState.PAUSED,
    )

    # Delete paused attack (should abort instead of delete)
    result = await delete_attack_service(attack.id, db_session)

    assert result["deleted"] is True
    assert result["id"] == attack.id

    # Verify attack is marked as ABANDONED (not actually deleted)
    attack_result = await db_session.execute(
        select(Attack).where(Attack.id == attack.id)
    )
    updated_attack = attack_result.scalar_one()
    assert updated_attack.state == AttackState.ABANDONED


@pytest.mark.asyncio
@patch("app.core.services.attack_service._broadcast_campaign_update")
async def test_delete_attack_service_rejects_completed_attack_abort(
    mock_broadcast: AsyncMock,
    db_session: AsyncSession,
) -> None:
    """Test that delete_attack_service rejects aborting a COMPLETED attack."""
    from app.core.state_machines import InvalidStateTransitionError
    from app.models.attack import AttackState
    from tests.factories.hash_list_factory import HashListFactory
    from tests.utils.hash_type_utils import get_or_create_hash_type

    # Set factory sessions
    AttackFactory.__async_session__ = db_session
    CampaignFactory.__async_session__ = db_session
    ProjectFactory.__async_session__ = db_session
    HashListFactory.__async_session__ = db_session

    project = await ProjectFactory.create_async()
    hash_type = await get_or_create_hash_type(db_session, 0, "MD5")
    hash_list = await HashListFactory.create_async(
        project_id=project.id, hash_type_id=hash_type.id
    )
    campaign = await CampaignFactory.create_async(
        project_id=project.id, hash_list_id=hash_list.id
    )
    attack = await AttackFactory.create_async(
        campaign_id=campaign.id,
        state=AttackState.COMPLETED,
    )

    # Attempt to delete a completed attack - should raise InvalidStateTransitionError
    with pytest.raises(InvalidStateTransitionError) as exc_info:
        await delete_attack_service(attack.id, db_session)

    assert exc_info.value.from_state == AttackState.COMPLETED
    assert exc_info.value.action == "abort"
