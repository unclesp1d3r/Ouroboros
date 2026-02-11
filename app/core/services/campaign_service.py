from collections.abc import Sequence

from fastapi import HTTPException
from loguru import logger
from sqlalchemy import Result, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.services.attack_complexity_service import calculate_attack_complexity
from app.core.state_machines import CampaignStateMachine
from app.models.agent import Agent, AgentState
from app.models.attack import Attack, AttackState
from app.models.campaign import Campaign, CampaignState
from app.models.hash_list import HashList
from app.models.task import Task, TaskStatus
from app.models.user import User
from app.schemas.attack import AttackCreate, AttackOut, AttackSummary
from app.schemas.campaign import (
    CampaignAndAttackSummaries,
    CampaignCreate,
    CampaignMetrics,
    CampaignProgress,
    CampaignRead,
    CampaignUpdate,
)
from app.schemas.shared import CampaignTemplate


class CampaignNotFoundError(Exception):
    pass


class AttackNotFoundError(Exception):
    pass


async def _broadcast_campaign_update(
    campaign_id: int, project_id: int | None = None
) -> None:
    """Helper function to broadcast campaign updates."""
    try:
        from app.core.services.event_service import get_event_service

        event_service = get_event_service()
        await event_service.broadcast_campaign_update(campaign_id, project_id)
    except (ImportError, AttributeError, RuntimeError) as e:
        # Gracefully handle if broadcast is not available or fails
        logger.debug(f"Campaign event broadcasting failed: {e}")


async def list_campaigns_service(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 20,
    name_filter: str | None = None,
    project_id: int | None = None,
    project_ids: list[int] | None = None,
) -> tuple[list[CampaignRead], int]:
    """
    List campaigns, excluding unavailable campaigns and hash lists.

    Args:
        db: AsyncSession
        skip: The number of campaigns to skip
        limit: The number of campaigns to return
        name_filter: A filter to apply to the campaign names
        project_id: The ID of the project to filter campaigns by (for compatibility)
        project_ids: List of project IDs to filter campaigns by (preferred over project_id)

    Returns:
        tuple[list[CampaignRead], int]: A tuple containing the list of campaigns and the total number of campaigns
    """
    stmt = select(Campaign).where(Campaign.state != CampaignState.ARCHIVED)
    stmt = stmt.where(
        Campaign.is_unavailable.is_(False)
    )  # Exclude unavailable campaigns

    # Handle project filtering - prioritize project_ids over project_id
    if project_ids is not None:
        if project_ids:  # Only filter if list is not empty
            stmt = stmt.where(Campaign.project_id.in_(project_ids))
        else:
            # Empty list means no projects accessible, return empty result
            return [], 0
    elif project_id is not None:
        stmt = stmt.where(Campaign.project_id == project_id)

    if name_filter:
        stmt = stmt.where(Campaign.name.ilike(f"%{name_filter}%"))
    total = await db.execute(select(func.count()).select_from(stmt.subquery()))
    total_count = total.scalar_one()
    stmt = stmt.order_by(Campaign.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    campaigns = result.scalars().all()
    return [
        CampaignRead.model_validate(c, from_attributes=True) for c in campaigns
    ], total_count


async def get_campaign_service(campaign_id: int, db: AsyncSession) -> CampaignRead:
    """
    Get a campaign by ID, excluding unavailable campaigns and hash lists.

    Args:
        campaign_id: The ID of the campaign to get
        db: AsyncSession
    Returns:
        CampaignRead: The campaign
    Raises:
        CampaignNotFoundError: if campaign does not exist
    """
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise CampaignNotFoundError(f"Campaign {campaign_id} not found")
    return CampaignRead.model_validate(campaign, from_attributes=True)


async def create_campaign_service(
    data: CampaignCreate, db: AsyncSession
) -> CampaignRead:
    """
    Create a campaign.
    Excludes unavailable campaigns and hash lists.

    Args:
        data: The campaign to create
        db: AsyncSession
    Returns:
        CampaignRead: The created campaign
    Raises:
        HTTPException: if campaign is archived
        CampaignNotFoundError: if campaign does not exist
    """
    logger.debug(f"Entering create_campaign_service with data: {data}")
    campaign = Campaign(
        name=data.name,
        description=data.description,
        project_id=data.project_id,
        priority=data.priority,
        hash_list_id=data.hash_list_id,
        is_unavailable=data.is_unavailable,  # This field is only set to True if the campaign is created by the `HashUploadTask` model.
    )
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)
    logger.info(f"Campaign created: {data.name}")

    # SSE_TRIGGER: Campaign created
    await _broadcast_campaign_update(campaign.id, campaign.project_id)

    logger.debug("Exiting create_campaign_service")
    return CampaignRead.model_validate(campaign, from_attributes=True)


async def update_campaign_service(
    campaign_id: int, data: CampaignUpdate, db: AsyncSession
) -> CampaignRead:
    """
    Update a campaign.
    Excludes unavailable campaigns and hash lists.

    Args:
        campaign_id: The ID of the campaign to update
        data: The campaign to update
        db: AsyncSession - The database session
    Returns:
        CampaignRead: The updated campaign
    Raises:
        CampaignNotFoundError: if campaign does not exist
    """
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise CampaignNotFoundError(f"Campaign {campaign_id} not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(campaign, field, value)
    await db.commit()
    await db.refresh(campaign)

    # SSE_TRIGGER: Campaign updated
    await _broadcast_campaign_update(campaign.id, campaign.project_id)

    return CampaignRead.model_validate(campaign, from_attributes=True)


async def delete_campaign_service(campaign_id: int, db: AsyncSession) -> None:
    """
    Delete a campaign.
    Excludes unavailable campaigns and hash lists.

    Args:
        campaign_id: The ID of the campaign to delete
        db: AsyncSession - The database session
    Raises:
        CampaignNotFoundError: if campaign does not exist
    """
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise CampaignNotFoundError(f"Campaign {campaign_id} not found")

    project_id = campaign.project_id
    await db.delete(campaign)
    await db.commit()

    # SSE_TRIGGER: Campaign deleted
    await _broadcast_campaign_update(campaign_id, project_id)


async def attach_attack_to_campaign_service(
    campaign_id: int, attack_id: int, db: AsyncSession
) -> AttackOut:
    """
    Attach an attack to a campaign.
    Excludes unavailable campaigns and hash lists.

    Args:
        campaign_id: The campaign to attach the attack to
        attack_id: The attack to attach to the campaign
        db: AsyncSession
    Returns:
        AttackOut: The attached attack
    Raises:
        CampaignNotFoundError: if campaign does not exist
        AttackNotFoundError: if attack does not exist
    """
    # Find campaign
    campaign_result: Result[tuple[Campaign]] = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id)
    )
    campaign = campaign_result.scalar_one_or_none()
    if not campaign:
        raise CampaignNotFoundError(f"Campaign {campaign_id} not found")
    # Find attack
    attack_result: Result[tuple[Attack]] = await db.execute(
        select(Attack).where(Attack.id == attack_id)
    )
    attack = attack_result.scalar_one_or_none()
    if not attack:
        raise AttackNotFoundError(f"Attack {attack_id} not found")

    attack.campaign_id = campaign_id
    await db.commit()
    await db.refresh(attack)
    # --- Post-attach: re-sort attacks by complexity (ascending) ---
    # Fetch all attacks for this campaign
    attack_results: Result[tuple[Attack]] = await db.execute(
        select(Attack).where(Attack.campaign_id == campaign.id)
    )
    attacks: Sequence[Attack] = attack_results.scalars().all()
    # Calculate complexity for each attack
    attack_complexities: list[tuple[Attack, int]] = [
        (a, calculate_attack_complexity(a)) for a in attacks
    ]
    # Sort attacks in ascending order of complexity
    attack_complexities.sort(key=lambda x: x[1])
    # No-op: sort_order not present on Attack; skip assignment
    await db.commit()
    # --- End re-sort ---
    return AttackOut.model_validate(attack, from_attributes=True)


async def detach_attack_from_campaign_service(
    campaign_id: int, attack_id: int, db: AsyncSession
) -> dict[str, bool | int]:
    """
    Detach an attack from a campaign.
    Excludes unavailable campaigns and hash lists.

    Args:
        campaign_id: The campaign to detach the attack from
        attack_id: The attack to detach from the campaign
        db: AsyncSession
    Returns:
        dict[str, bool | int]: A dictionary containing the attack ID and a boolean indicating if the attack was deleted
    Raises:
        CampaignNotFoundError: if campaign does not exist
    """
    # Find campaign
    campaign_result: Result[tuple[Campaign]] = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id)
    )
    campaign = campaign_result.scalar_one_or_none()
    if not campaign:
        raise CampaignNotFoundError(f"Campaign {campaign_id} not found")
    # Find attack
    attack_result: Result[tuple[Attack]] = await db.execute(
        select(Attack).where(Attack.id == attack_id)
    )
    attack = attack_result.scalar_one_or_none()
    if not attack:
        raise AttackNotFoundError(f"Attack {attack_id} not found")
    # Only allow delete if currently attached to this campaign
    if attack.campaign_id != campaign_id:
        raise ValueError(
            f"Attack {attack_id} is not attached to campaign {campaign_id}"
        )
    await db.delete(attack)
    await db.commit()
    return {"id": attack_id, "deleted": True}


async def get_campaign_progress_service(
    campaign_id: int, db: AsyncSession
) -> CampaignProgress:
    """
    Get the progress of a campaign.
    Excludes unavailable campaigns and hash lists.

    Args:
        campaign_id: The campaign to get the progress of
        db: AsyncSession
    Returns:
        CampaignProgress: The progress of the campaign
    Raises:
        CampaignNotFoundError: if campaign does not exist
    """
    # Ensure campaign exists
    campaign_result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id)
    )
    campaign = campaign_result.scalar_one_or_none()
    if not campaign:
        raise CampaignNotFoundError(f"Campaign {campaign_id} not found")
    # Get all attacks for the campaign
    result_ids: Result[tuple[int]] = await db.execute(
        select(Attack.id).where(Attack.campaign_id == campaign_id)
    )
    attack_ids: Sequence[int] = result_ids.scalars().all()
    if not attack_ids:
        return CampaignProgress(active_agents=0, total_tasks=0)
    # Count total tasks for these attacks
    count_result: Result[tuple[int]] = await db.execute(
        select(func.count(Task.id)).where(Task.attack_id.in_(attack_ids))
    )
    total_tasks = count_result.scalar_one() or 0
    # Find unique agent_ids assigned to these tasks
    agent_ids_result: Result[tuple[int | None]] = await db.execute(
        select(Task.agent_id).where(
            Task.attack_id.in_(attack_ids), Task.agent_id.isnot(None)
        )
    )
    agent_ids: set[int | None] = {row[0] for row in agent_ids_result.all()}
    if not agent_ids:
        return CampaignProgress(active_agents=0, total_tasks=total_tasks)
    # Count agents in 'active' state
    agent_count_result: Result[tuple[int]] = await db.execute(
        select(func.count(Agent.id)).where(
            Agent.id.in_(agent_ids), Agent.state == AgentState.active
        )
    )
    active_agents = agent_count_result.scalar_one() or 0
    logger.info(
        f"Campaign progress calculated for campaign_id={campaign_id}: active_agents={active_agents}, total_tasks={total_tasks}"
    )
    return CampaignProgress(active_agents=active_agents, total_tasks=total_tasks)


# --- Task retry stub ---
def mark_task_for_retry(task: Task) -> None:
    """Mark a task for retry: set to pending and increment retry_count."""
    task.status = TaskStatus.PENDING
    if hasattr(task, "retry_count") and task.retry_count is not None:
        task.retry_count += 1
    else:
        task.retry_count = 1


async def raise_campaign_priority_service(
    campaign_id: int, _user: User, db: AsyncSession
) -> CampaignRead:
    """
    Raise the priority of a campaign.
    Excludes unavailable campaigns and hash lists.

    Args:
        campaign_id: The campaign to raise the priority of
        _user: The user raising the priority
        db: AsyncSession
    Returns:
        CampaignRead: The updated campaign
    Raises:
        CampaignNotFoundError: if campaign does not exist
        HTTPException: if campaign is archived

    TODO: Add permission check for user to raise priority of campaign
    """
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    campaign.priority += 1
    await db.commit()
    await db.refresh(campaign)
    return CampaignRead.model_validate(campaign, from_attributes=True)


async def reorder_attacks_service(
    campaign_id: int, attack_ids: list[int], db: AsyncSession
) -> list[int]:
    """
    Reorder attacks within a campaign by updating their position field.

    Args:
        campaign_id: The campaign to update
        attack_ids: List of attack IDs in the desired order
        db: AsyncSession
    Raises:
        CampaignNotFoundError: if campaign does not exist
        AttackNotFoundError: if any attack does not belong to the campaign
    """
    logger.info(f"Reordering attacks for campaign_id={campaign_id}: {attack_ids}")
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise CampaignNotFoundError(f"Campaign {campaign_id} not found")
    # Fetch all attacks for this campaign
    attacks_result = await db.execute(
        select(Attack).where(Attack.campaign_id == campaign_id)
    )
    attacks = attacks_result.scalars().all()
    attack_map = {a.id: a for a in attacks}
    if set(attack_ids) != set(attack_map.keys()):
        raise AttackNotFoundError("Attack IDs do not match campaign's attacks")
    # Update position for each attack
    for pos, attack_id in enumerate(attack_ids):
        attack = attack_map[attack_id]
        attack.position = pos
    await db.commit()
    logger.info(f"Attack order updated for campaign_id={campaign_id}")

    # SSE_TRIGGER: Campaign attacks reordered
    await _broadcast_campaign_update(campaign_id, campaign.project_id)

    return attack_ids


async def start_campaign_service(campaign_id: int, db: AsyncSession) -> CampaignRead:
    """
    Start a campaign by setting its state to ACTIVE.
    Excludes unavailable campaigns and hash lists.

    Args:
        campaign_id: The campaign to start
        db: AsyncSession
    Returns:
        CampaignRead: The updated campaign
    Raises:
        CampaignNotFoundError: if campaign does not exist
        InvalidStateTransitionError: if transition is not valid
    """
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise CampaignNotFoundError(f"Campaign {campaign_id} not found")
    if campaign.state == CampaignState.ACTIVE:
        logger.info(f"Campaign {campaign_id} is already active.")
        return CampaignRead.model_validate(campaign, from_attributes=True)

    # Validate state transition using state machine (raises InvalidStateTransitionError if invalid)
    CampaignStateMachine.validate_action(campaign.state, "start")

    campaign.state = CampaignState.ACTIVE
    await db.commit()
    await db.refresh(campaign)
    logger.info(f"Campaign {campaign_id} started.")

    # SSE_TRIGGER: Campaign started
    await _broadcast_campaign_update(campaign.id, campaign.project_id)

    return CampaignRead.model_validate(campaign, from_attributes=True)


async def stop_campaign_service(campaign_id: int, db: AsyncSession) -> CampaignRead:
    """
    Stop a campaign by setting its state to DRAFT.
    Excludes unavailable campaigns and hash lists.

    Args:
        campaign_id: The campaign to stop
        db: AsyncSession
    Returns:
        CampaignRead: The updated campaign
    Raises:
        CampaignNotFoundError: if campaign does not exist
        InvalidStateTransitionError: if transition is not valid
    """
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise CampaignNotFoundError(f"Campaign {campaign_id} not found")
    if campaign.state == CampaignState.DRAFT:
        logger.info(f"Campaign {campaign_id} is already stopped (draft state).")
        return CampaignRead.model_validate(campaign, from_attributes=True)

    # Validate state transition using state machine (raises InvalidStateTransitionError if invalid)
    CampaignStateMachine.validate_action(campaign.state, "stop")

    campaign.state = CampaignState.DRAFT
    await db.commit()
    await db.refresh(campaign)
    logger.info(f"Campaign {campaign_id} stopped (set to draft).")

    # SSE_TRIGGER: Campaign stopped
    await _broadcast_campaign_update(campaign.id, campaign.project_id)

    return CampaignRead.model_validate(campaign, from_attributes=True)


async def get_campaign_with_attack_summaries_service(
    campaign_id: int, db: AsyncSession
) -> CampaignAndAttackSummaries:
    """
    Get a campaign with its attacks and tasks, ordered by position.
    Excludes unavailable campaigns and hash lists.

    Args:
        campaign_id: The campaign to get
        db: AsyncSession
    Returns:
        CampaignAndAttackSummaries: The campaign and its attacks
    """
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise CampaignNotFoundError(f"Campaign {campaign_id} not found")
    # Fetch attacks for this campaign, ordered by position, eagerly loading tasks
    attacks_result = await db.execute(
        select(Attack)
        .where(Attack.campaign_id == campaign_id)
        .order_by(Attack.position)
        .options(selectinload(Attack.tasks))
    )
    attacks = attacks_result.scalars().all()
    summaries = []
    for attack in attacks:
        # Type label
        type_label = attack.attack_mode.value.replace("_", " ").title()
        # Length: mask length or wordlist length (if available)
        length = None
        if attack.mask:
            length = len(attack.mask)
        # Settings summary (simple, can be expanded)
        settings_summary = f"Mode: {type_label}, Hash Mode: {attack.hash_mode}"
        # Keyspace: sum of all task keyspaces if available
        keyspace = None
        if attack.tasks:
            keyspace = sum(getattr(t, "keyspace_total", 0) or 0 for t in attack.tasks)
        # Complexity
        complexity_score = attack.complexity_score
        summaries.append(
            AttackSummary(
                id=attack.id,
                name=attack.name,
                attack_mode=attack.attack_mode,
                type_label=type_label,
                length=length,
                settings_summary=settings_summary,
                keyspace=keyspace,
                complexity_score=complexity_score,
            )
        )
    return CampaignAndAttackSummaries(
        campaign=CampaignRead.model_validate(campaign, from_attributes=True),
        attacks=summaries,
    )


async def archive_campaign_service(campaign_id: int, db: AsyncSession) -> CampaignRead:
    """
    Archive a campaign by setting its state to ARCHIVED.
    Excludes unavailable campaigns and hash lists.

    Args:
        campaign_id: The campaign to archive
        db: AsyncSession
    Returns:
        CampaignRead: The updated campaign
    Raises:
        CampaignNotFoundError: if campaign does not exist
        InvalidStateTransitionError: if transition is not valid
    """
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise CampaignNotFoundError(f"Campaign {campaign_id} not found")
    if campaign.state == CampaignState.ARCHIVED:
        return CampaignRead.model_validate(campaign, from_attributes=True)

    # Validate state transition using state machine (raises InvalidStateTransitionError if invalid)
    CampaignStateMachine.validate_action(campaign.state, "archive")

    campaign.state = CampaignState.ARCHIVED
    await db.commit()
    await db.refresh(campaign)

    # SSE_TRIGGER: Campaign archived
    await _broadcast_campaign_update(campaign.id, campaign.project_id)

    return CampaignRead.model_validate(campaign, from_attributes=True)


async def pause_campaign_service(campaign_id: int, db: AsyncSession) -> CampaignRead:
    """
    Pause a campaign by setting its state to PAUSED.

    Args:
        campaign_id: The campaign to pause
        db: AsyncSession
    Returns:
        CampaignRead: The updated campaign
    Raises:
        CampaignNotFoundError: if campaign does not exist
        InvalidStateTransitionError: if transition is not valid
    """
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise CampaignNotFoundError(f"Campaign {campaign_id} not found")
    if campaign.state == CampaignState.PAUSED:
        logger.info(f"Campaign {campaign_id} is already paused.")
        return CampaignRead.model_validate(campaign, from_attributes=True)

    # Validate state transition using state machine (raises InvalidStateTransitionError if invalid)
    CampaignStateMachine.validate_action(campaign.state, "pause")

    campaign.state = CampaignState.PAUSED
    await db.commit()
    await db.refresh(campaign)
    logger.info(f"Campaign {campaign_id} paused.")

    # SSE_TRIGGER: Campaign paused
    await _broadcast_campaign_update(campaign.id, campaign.project_id)

    return CampaignRead.model_validate(campaign, from_attributes=True)


async def resume_campaign_service(campaign_id: int, db: AsyncSession) -> CampaignRead:
    """
    Resume a paused campaign by setting its state to ACTIVE.

    Args:
        campaign_id: The campaign to resume
        db: AsyncSession
    Returns:
        CampaignRead: The updated campaign
    Raises:
        CampaignNotFoundError: if campaign does not exist
        InvalidStateTransitionError: if transition is not valid
    """
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise CampaignNotFoundError(f"Campaign {campaign_id} not found")
    if campaign.state == CampaignState.ACTIVE:
        logger.info(f"Campaign {campaign_id} is already active.")
        return CampaignRead.model_validate(campaign, from_attributes=True)

    # Validate state transition using state machine (raises InvalidStateTransitionError if invalid)
    CampaignStateMachine.validate_action(campaign.state, "resume")

    campaign.state = CampaignState.ACTIVE
    await db.commit()
    await db.refresh(campaign)
    logger.info(f"Campaign {campaign_id} resumed.")

    # SSE_TRIGGER: Campaign resumed
    await _broadcast_campaign_update(campaign.id, campaign.project_id)

    return CampaignRead.model_validate(campaign, from_attributes=True)


async def unarchive_campaign_service(
    campaign_id: int, db: AsyncSession
) -> CampaignRead:
    """
    Unarchive a campaign by setting its state to DRAFT.

    Args:
        campaign_id: The campaign to unarchive
        db: AsyncSession
    Returns:
        CampaignRead: The updated campaign
    Raises:
        CampaignNotFoundError: if campaign does not exist
        InvalidStateTransitionError: if transition is not valid
    """
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise CampaignNotFoundError(f"Campaign {campaign_id} not found")
    if campaign.state == CampaignState.DRAFT:
        logger.info(f"Campaign {campaign_id} is already in draft state.")
        return CampaignRead.model_validate(campaign, from_attributes=True)

    # Validate state transition using state machine (raises InvalidStateTransitionError if invalid)
    CampaignStateMachine.validate_action(campaign.state, "unarchive")

    campaign.state = CampaignState.DRAFT
    await db.commit()
    await db.refresh(campaign)
    logger.info(f"Campaign {campaign_id} unarchived (set to draft).")

    # SSE_TRIGGER: Campaign unarchived
    await _broadcast_campaign_update(campaign.id, campaign.project_id)

    return CampaignRead.model_validate(campaign, from_attributes=True)


async def add_attack_to_campaign_service(
    campaign_id: int, data: AttackCreate, db: AsyncSession
) -> AttackOut:
    """
    Add an attack to a campaign.
    Excludes unavailable campaigns and hash lists.

    Args:
        campaign_id: The campaign to add the attack to
        data: The attack to add
        db: AsyncSession
    Returns:
        AttackOut: The added attack
    Raises:
        CampaignNotFoundError: if campaign does not exist
        HTTPException: if campaign is archived
    """
    # Find campaign
    campaign_result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id)
    )
    campaign = campaign_result.scalar_one_or_none()
    if not campaign:
        raise CampaignNotFoundError(f"Campaign {campaign_id} not found")
    # Find max position in campaign
    max_pos_result = await db.execute(
        select(func.max(Attack.position)).where(Attack.campaign_id == campaign_id)
    )
    max_position = max_pos_result.scalar() or 0
    # Create attack, set campaign_id and position
    attack_data = data.model_dump()
    attack_data["campaign_id"] = campaign_id
    attack_data["position"] = max_position + 1

    # Ephemeral wordlist support
    wordlist_inline = attack_data.pop("wordlist_inline", None)
    if wordlist_inline:
        from uuid import uuid4

        from app.models.attack_resource_file import (
            AttackResourceFile,
            AttackResourceType,
        )

        ephemeral_resource = AttackResourceFile(
            id=uuid4(),
            file_name="ephemeral_wordlist.txt",
            download_url="",  # Not downloadable from MinIO
            checksum="",  # Not applicable
            guid=uuid4(),
            resource_type=AttackResourceType.EPHEMERAL_WORD_LIST,
            line_format="freeform",
            line_encoding="utf-8",
            used_for_modes=[attack_data.get("attack_mode", "dictionary")],
            source="ephemeral",
            line_count=len(wordlist_inline),
            byte_size=sum(len(w) for w in wordlist_inline),
            content={"lines": wordlist_inline},
        )
        db.add(ephemeral_resource)
        await db.flush()  # Get PK if needed
        # Link to attack (assume word_list_id is available)
        attack_data["word_list_id"] = ephemeral_resource.id

    # Ephemeral mask list support
    masks_inline = attack_data.pop("masks_inline", None)
    if masks_inline:
        from uuid import uuid4

        from app.models.attack_resource_file import (
            AttackResourceFile,
            AttackResourceType,
        )

        ephemeral_mask_resource = AttackResourceFile(
            id=uuid4(),
            file_name="ephemeral_masklist.txt",
            download_url="",  # Not downloadable from MinIO
            checksum="",  # Not applicable
            guid=uuid4(),
            resource_type=AttackResourceType.EPHEMERAL_MASK_LIST,
            line_format="mask",
            line_encoding="ascii",
            used_for_modes=[attack_data.get("attack_mode", "mask")],
            source="ephemeral",
            line_count=len(masks_inline),
            byte_size=sum(len(m) for m in masks_inline),
            content={"lines": masks_inline},
        )
        db.add(ephemeral_mask_resource)
        await db.flush()
        attack_data["mask_list_id"] = ephemeral_mask_resource.id

    # Remove fields not present in the Attack model
    attack_data.pop("rule_list_id", None)
    attack_data.pop("mask_list_id", None)
    attack = Attack(**attack_data)
    db.add(attack)
    await db.commit()
    await db.refresh(attack)

    # SSE_TRIGGER: Attack added to campaign
    await _broadcast_campaign_update(campaign_id, campaign.project_id)

    return AttackOut.model_validate(attack, from_attributes=True)


async def get_campaign_metrics_service(
    campaign_id: int, db: AsyncSession
) -> CampaignMetrics:
    """
    Get metrics for a campaign.
    Excludes unavailable campaigns and hash lists.

    Args:
        campaign_id: The campaign to get metrics for
        db: AsyncSession
    Returns:
        CampaignMetrics: The metrics for the campaign
    Raises:
        CampaignNotFoundError: if campaign does not exist
    """
    # Eagerly load hash_list and its items
    result = await db.execute(
        select(Campaign)
        .options(
            selectinload(Campaign.hash_list).selectinload(HashList.items),
            selectinload(Campaign.attacks),
        )
        .where(Campaign.id == campaign_id)
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise CampaignNotFoundError(f"Campaign {campaign_id} not found")
    hash_list: HashList | None = campaign.hash_list
    if not hash_list:
        return CampaignMetrics(
            total_hashes=0,
            cracked_hashes=0,
            uncracked_hashes=0,
            percent_cracked=0.0,
            progress_percent=0.0,
        )
    total_hashes = len(hash_list.items)
    cracked_hashes = hash_list.cracked_count
    uncracked_hashes = hash_list.uncracked_count
    percent_cracked = (
        (cracked_hashes / total_hashes * 100.0) if total_hashes > 0 else 0.0
    )
    progress_percent = campaign.progress_percent
    return CampaignMetrics(
        total_hashes=total_hashes,
        cracked_hashes=cracked_hashes,
        uncracked_hashes=uncracked_hashes,
        percent_cracked=round(percent_cracked, 2),
        progress_percent=round(progress_percent, 2),
    )


async def relaunch_campaign_service(
    campaign_id: int, db: AsyncSession
) -> CampaignAndAttackSummaries:
    """
    Relaunch failed attacks or attacks with modified resources in a campaign.
    Resets their state to PENDING and marks associated tasks for retry.
    Excludes unavailable campaigns and hash lists.

    Args:
        campaign_id: The campaign to relaunch
        db: AsyncSession
    Returns:
        CampaignAndAttackSummaries: The updated campaign and attack summaries
    Raises:
        CampaignNotFoundError: if campaign does not exist
        HTTPException: if campaign is archived
    """
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise CampaignNotFoundError(f"Campaign {campaign_id} not found")
    if campaign.state == CampaignState.ARCHIVED:
        raise HTTPException(
            status_code=400, detail="Cannot relaunch an archived campaign."
        )

    # Eagerly load attacks and their tasks
    attacks_result = await db.execute(
        select(Attack)
        .where(Attack.campaign_id == campaign_id)
        .options(selectinload(Attack.tasks))
    )
    attacks = attacks_result.scalars().all()
    if not attacks:
        raise HTTPException(
            status_code=400, detail="No attacks found for this campaign."
        )

    # Find attacks to relaunch: failed or resource-modified (placeholder: only failed for now)
    to_relaunch = [a for a in attacks if a.state == AttackState.FAILED]
    # TODO: Add resource-modified logic when resource tracking is implemented

    if not to_relaunch:
        raise HTTPException(
            status_code=400, detail="No failed or modified attacks to relaunch."
        )

    for attack in to_relaunch:
        attack.state = AttackState.PENDING
        # Reset all tasks for this attack
        for task in attack.tasks:
            task.status = TaskStatus.PENDING
            task.agent_id = None
            task.retry_count += 1
            task.error_message = None
            task.error_details = None
            task.progress = 0.0
    await db.commit()

    # SSE_TRIGGER: Campaign relaunched
    await _broadcast_campaign_update(campaign_id, campaign.project_id)

    # Return updated campaign and attack summaries
    return await get_campaign_with_attack_summaries_service(campaign_id, db)


async def export_campaign_template_service(
    campaign_id: int, db: AsyncSession
) -> CampaignTemplate:
    """
    Export a Campaign and all its Attacks as a CampaignTemplate for save/load workflows.
    Ensures compliance with the shared schema (see docs/v2_rewrite_implementation_plan/phase-2-api-implementation.md and phase-2-api-implementation-part-2.md).
    - Exports all editable campaign fields (name, description, etc.)
    - Exports all attacks using attack_to_template, preserving order and all required fields
    - Does not include project/user/internal DB IDs
    Excludes unavailable campaigns and hash lists.

    Args:
        campaign_id: The campaign to export
        db: AsyncSession
    Returns:
        CampaignTemplate: The exported campaign template
    Raises:
        CampaignNotFoundError: if campaign does not exist
    """
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise CampaignNotFoundError(f"Campaign {campaign_id} not found")
    # Fetch all attacks for this campaign, ordered by position
    attacks_result = await db.execute(
        select(Attack)
        .where(Attack.campaign_id == campaign_id)
        .order_by(Attack.position)
    )
    attacks = attacks_result.scalars().all()
    # Map each attack to AttackTemplate using shared helper
    from app.core.services.attack_service import attack_to_template

    attack_templates = [attack_to_template(a) for a in attacks]
    # Build and return the CampaignTemplate
    return CampaignTemplate(
        name=campaign.name,
        description=getattr(campaign, "description", None),
        attacks=attack_templates,
        hash_list_id=campaign.hash_list_id,
        # schema_version is handled by CampaignTemplate defaults
    )
