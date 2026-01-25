import pathlib
from functools import lru_cache
from uuid import UUID

from loguru import logger
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import InvalidAgentTokenError
from app.core.services.attack_complexity_service import AttackEstimationService
from app.models.agent import Agent
from app.models.attack import Attack, AttackMode, AttackState
from app.models.attack_resource_file import AttackResourceFile, AttackResourceType
from app.models.campaign import Campaign
from app.models.hash_type import HashType
from app.models.hashcat_benchmark import HashcatBenchmark
from app.models.task import TaskStatus
from app.schemas.attack import (
    AttackCreate,
    AttackMoveDirection,
    AttackOut,
    AttackPerformanceSummary,
    AttackResourceEstimationContext,
    AttackSummary,
    AttackUpdate,
    EstimateAttackRequest,
    EstimateAttackResponse,
)
from app.schemas.shared import AttackTemplate


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


class AttackAlreadyExistsError(Exception):
    pass


class AttackEditConfirmationError(Exception):
    def __init__(self, attack: Attack) -> None:
        self.attack: Attack = attack
        super().__init__(
            f"Edit confirmation required for attack in state {attack.state}"
        )


async def get_hash_type_for_attack(attack: Attack, db: AsyncSession) -> HashType:
    # Eagerly load campaign and hash_list to avoid MissingGreenlet
    result = await db.execute(
        select(Attack)
        .options(selectinload(Attack.campaign).selectinload(Campaign.hash_list))
        .where(Attack.id == attack.id)
    )
    attack_loaded = result.scalar_one()
    hash_type_id = attack_loaded.campaign.hash_list.hash_type_id
    result2 = await db.execute(select(HashType).filter(HashType.id == hash_type_id))
    return result2.scalar_one()


async def get_attack_config_service(
    attack_id: int,
    db: AsyncSession,
    authorization: str,
) -> Attack:
    if not authorization.startswith("Bearer csa_"):
        raise InvalidAgentTokenError("Invalid or missing agent token")
    token = authorization.removeprefix("Bearer ").strip()
    agent_result = await db.execute(select(Agent).filter(Agent.token == token))
    agent = agent_result.scalar_one_or_none()
    if not agent:
        raise InvalidAgentTokenError("Invalid agent token")
    result = await db.execute(select(Attack).filter(Attack.id == attack_id))
    attack = result.scalar_one_or_none()
    if not attack:
        raise AttackNotFoundError("Attack not found")

    # Validate agent capability for attack
    hash_type = await get_hash_type_for_attack(attack, db)
    benchmark_result = await db.execute(
        select(HashcatBenchmark).filter(
            HashcatBenchmark.agent_id == agent.id,
            HashcatBenchmark.hash_type_id == hash_type.id,
        )
    )
    benchmark = benchmark_result.scalar_one_or_none()
    if not benchmark:
        raise PermissionError(
            "Agent does not support required hash type for this attack"
        )
    return attack


async def move_attack_service(
    attack_id: int, direction: AttackMoveDirection, db: AsyncSession
) -> None:
    """
    Move an attack within its campaign by updating its position.

    Args:
        attack_id: The attack to move
        direction: One of AttackMoveDirection
        db: AsyncSession
    Raises:
        AttackNotFoundError: if attack not found or invalid direction
    """
    logger.info(f"Moving attack {attack_id} direction={direction}")
    result = await db.execute(select(Attack).where(Attack.id == attack_id))
    attack = result.scalar_one_or_none()
    if not attack:
        raise AttackNotFoundError(f"Attack {attack_id} not found")
    campaign_id = attack.campaign_id
    # Fetch all attacks in this campaign, ordered by position
    attacks_result = await db.execute(
        select(Attack)
        .where(Attack.campaign_id == campaign_id)
        .order_by(Attack.position)
    )
    attacks = list(attacks_result.scalars().all())
    idx = next((i for i, a in enumerate(attacks) if a.id == attack_id), None)
    if idx is None:
        raise AttackNotFoundError(f"Attack {attack_id} not found in campaign")
    # Move logic
    if direction == AttackMoveDirection.UP and idx > 0:
        attacks[idx - 1], attacks[idx] = attacks[idx], attacks[idx - 1]
    elif direction == AttackMoveDirection.DOWN and idx < len(attacks) - 1:
        attacks[idx], attacks[idx + 1] = attacks[idx + 1], attacks[idx]
    elif direction == AttackMoveDirection.TOP and idx > 0:
        attack_to_move = attacks.pop(idx)
        attacks.insert(0, attack_to_move)
    elif direction == AttackMoveDirection.BOTTOM and idx < len(attacks) - 1:
        attack_to_move = attacks.pop(idx)
        attacks.append(attack_to_move)
    # else: no-op if already at edge
    # Reassign positions
    for pos, a in enumerate(attacks):
        a.position = pos
    await db.commit()
    logger.info(f"Attack {attack_id} moved {direction} in campaign {campaign_id}")

    # SSE_TRIGGER: Attack moved within campaign
    await _broadcast_campaign_update(campaign_id, None)


async def duplicate_attack_service(attack_id: int, db: AsyncSession) -> AttackOut:
    """
    Duplicate an attack in-place, copying all fields except id, position, and timestamps.
    The clone is inserted at the end of the campaign's attack list.
    Returns the new attack as a Pydantic AttackOut schema.
    """
    result = await db.execute(select(Attack).where(Attack.id == attack_id))
    attack = result.scalar_one_or_none()
    if not attack:
        raise AttackNotFoundError(f"Attack {attack_id} not found")
    # Find max position in campaign
    max_pos_result = await db.execute(
        select(func.max(Attack.position)).where(
            Attack.campaign_id == attack.campaign_id
        )
    )
    max_position = max_pos_result.scalar() or 0
    # Use Pydantic v2 idiom to copy fields
    attack_out = AttackOut.model_validate(attack, from_attributes=True)
    clone_out = attack_out.model_copy(
        update={
            "name": f"{attack.name} (Copy)",
            "state": AttackState.PENDING,
            "template_id": attack.id,
        }
    )
    clone_data = clone_out.model_dump(
        exclude={
            "id",
            "position",
            "start_time",
            "end_time",
            "word_list",
            "rule_list",
            "mask_list",
        }
    )
    clone_data["position"] = max_position + 1
    clone = Attack(**clone_data)
    db.add(clone)
    await db.commit()
    await db.refresh(clone)

    # SSE_TRIGGER: Attack duplicated
    await _broadcast_campaign_update(attack.campaign_id, None)

    return AttackOut.model_validate(clone, from_attributes=True)


async def bulk_delete_attacks_service(
    attack_ids: list[int], db: AsyncSession
) -> dict[str, list[int]]:
    """
    Delete multiple attacks by their IDs in a single transaction.
    Returns a dict with 'deleted_ids' and 'not_found_ids'.
    Raises AttackNotFoundError if any ID does not exist.
    """
    logger.info(f"Bulk deleting attacks: {attack_ids}")
    if not attack_ids:
        return {"deleted_ids": [], "not_found_ids": []}
    # Fetch all attacks matching the IDs
    result = await db.execute(select(Attack).where(Attack.id.in_(attack_ids)))
    attacks = result.scalars().all()
    found_ids = {a.id for a in attacks}
    not_found_ids = [aid for aid in attack_ids if aid not in found_ids]
    if not attacks:
        raise AttackNotFoundError(f"No attacks found for IDs: {attack_ids}")
    # Collect campaign IDs for SSE triggers
    campaign_ids = {attack.campaign_id for attack in attacks}

    # Delete found attacks
    for attack in attacks:
        await db.delete(attack)
    await db.commit()
    logger.info(f"Deleted attacks: {found_ids}. Not found: {not_found_ids}")

    # SSE_TRIGGER: Attacks bulk deleted
    for campaign_id in campaign_ids:
        await _broadcast_campaign_update(campaign_id, None)

    return {"deleted_ids": list(found_ids), "not_found_ids": not_found_ids}


# Deprecated: use AttackEstimationService instead
class KeyspaceEstimator:
    @staticmethod
    def estimate(
        attack: AttackCreate, resources: AttackResourceEstimationContext
    ) -> int:
        return AttackEstimationService.estimate_keyspace(attack, resources)


def _safe_int(val: object, default: int) -> int:
    if isinstance(val, int):
        return val
    if isinstance(val, str) and val.isdigit():
        return int(val)
    return default


async def estimate_attack_keyspace_and_complexity(
    attack_data: EstimateAttackRequest,
) -> EstimateAttackResponse:
    """
    Estimate keyspace and complexity score for an unsaved attack config.
    Accepts an EstimateAttackRequest model.
    Returns an EstimateAttackResponse model.
    """
    # Use AttackCreate for attack fields, fill missing with defaults
    attack = AttackCreate.model_validate(attack_data.model_dump(exclude_none=True))
    resources = AttackResourceEstimationContext(
        wordlist_size=attack_data.wordlist_size
        if attack_data.wordlist_size is not None
        else 10000,
        rule_count=attack_data.rule_count if attack_data.rule_count is not None else 1,
    )
    keyspace = AttackEstimationService.estimate_keyspace(attack, resources)
    complexity = AttackEstimationService.calculate_complexity_from_keyspace(keyspace)
    return EstimateAttackResponse(keyspace=keyspace, complexity_score=complexity)


def _extract_wordlist(attack: Attack) -> tuple[UUID | None, list[str] | None]:
    wl = getattr(attack, "word_list", None)
    if wl is not None:
        if (
            hasattr(wl, "resource_type")
            and wl.resource_type == AttackResourceType.EPHEMERAL_WORD_LIST
            and wl.content
            and "lines" in wl.content
        ):
            return None, wl.content["lines"]
        if hasattr(wl, "guid"):
            return wl.guid, None
    return None, None


def _extract_rulelist(
    attack: Attack,
) -> tuple[UUID | None, list[str] | None]:
    rl = getattr(attack, "left_rule", None)
    if rl is not None:
        if isinstance(rl, AttackResourceFile):
            if (
                hasattr(rl, "resource_type")
                and str(rl.resource_type) == "ephemeral_rule_list"
                and rl.content
                and "lines" in rl.content
            ):
                val = rl.content["lines"]
                return None, val if isinstance(val, list) else None
            if hasattr(rl, "guid"):
                return rl.guid, None
        elif isinstance(rl, str):
            return None, None
    return None, None


def _extract_masklist(attack: Attack) -> tuple[UUID | None, list[str] | None]:
    mask_list = getattr(attack, "mask_list", None)
    if mask_list is not None:
        if (
            hasattr(mask_list, "resource_type")
            and str(mask_list.resource_type) == "ephemeral_mask_list"
            and mask_list.content
            and "lines" in mask_list.content
        ):
            return None, mask_list.content["lines"]
        if hasattr(mask_list, "guid"):
            return mask_list.guid, None
        if (
            hasattr(mask_list, "resource_type")
            and str(mask_list.resource_type) == "mask_list"
            and mask_list.content
            and "lines" in mask_list.content
        ):
            return None, mask_list.content["lines"]
    return None, None


def attack_to_template(attack: Attack) -> AttackTemplate:
    """
    Convert an Attack SQLAlchemy model to an AttackTemplate Pydantic model for save/load export.
    Follows the schema requirements from docs/v2_rewrite_implementation_plan/phase-2-api-implementation.md
    and phase-2-api-implementation-part-2.md (see 'shared-schema-saveload' and 'web-ui-api-campaign-management-save-load-schema-design').

    - Exports all editable fields: mode, position, comment, min/max length, etc.
    - For linked resources (wordlist, rulelist, masklist), exports their stable UUID (guid) if not ephemeral.
    - For ephemeral resources, inlines their content (wordlist_inline, rules_inline, masks_inline).
    - Field names and types match the schema exactly.
    """
    wordlist_guid, wordlist_inline = _extract_wordlist(attack)
    rulelist_guid, rules_inline = _extract_rulelist(attack)
    masklist_guid, masks_inline = _extract_masklist(attack)
    masks = [attack.mask] if getattr(attack, "mask", None) else None
    if masks:
        filtered_masks = [m for m in masks if isinstance(m, str) and m is not None]
        masks_out = filtered_masks if filtered_masks else None
    else:
        masks_out = None

    return AttackTemplate(
        mode=attack.attack_mode,
        position=getattr(attack, "position", None),
        comment=getattr(
            attack, "description", None
        ),  # Use description instead of comment
        min_length=getattr(attack, "increment_minimum", None),
        max_length=getattr(attack, "increment_maximum", None),
        wordlist_guid=wordlist_guid,
        rulelist_guid=rulelist_guid,
        masklist_guid=masklist_guid,
        wordlist_inline=wordlist_inline,
        rules_inline=rules_inline if isinstance(rules_inline, list) else None,
        masks=masks_out,
        masks_inline=masks_inline,
    )


async def export_attack_template_service(
    attack_id: int, db: AsyncSession
) -> AttackTemplate:
    """
    Export a single Attack as an AttackTemplate for save/load workflows.
    Ensures compliance with the shared schema (see docs).
    """
    result = await db.execute(select(Attack).where(Attack.id == attack_id))
    attack = result.scalar_one_or_none()
    if not attack:
        raise AttackNotFoundError(f"Attack {attack_id} not found")
    return attack_to_template(attack)


async def _check_attack_resource(
    resource_id: UUID | None,
    allowed_types: set[AttackResourceType],
    field_name: str,
    db: AsyncSession,
    mode_enum: AttackMode,
) -> None:
    if not resource_id:
        return
    resource = await db.get(AttackResourceFile, resource_id)
    if not resource:
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"{field_name} resource not found.",
        )
    if resource.resource_type not in allowed_types:
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"{field_name} resource type {resource.resource_type} is not allowed for attack mode {mode_enum}.",
        )


# --- Built-in hashcat rule file loading (MIT-licensed, see upstream for updates) ---
# These files are bundled in app/resources/rules/ and are not user-editable.
_LEETSPEAK_RULE_PATH = (
    pathlib.Path(__file__).parent.parent / "resources/rules/leetspeak.rule"
)
_COMBINATOR_RULE_PATH = (
    pathlib.Path(__file__).parent.parent / "resources/rules/combinator.rule"
)


@lru_cache(maxsize=2)
def _load_builtin_rulefile_lines(rulefile: str) -> list[str]:
    """
    Load lines from a bundled hashcat rule file (MIT-licensed).
    Only non-empty, non-comment lines are returned.

    Note: Uses functools.lru_cache instead of cashews (exception to AGENTS.md)
    because this is a synchronous function memoizing static bundled resources
    that never change. The files are small, only 2 are cached, and this avoids
    the overhead of async/Redis for simple in-memory memoization.
    """
    path = {
        "leetspeak.rule": _LEETSPEAK_RULE_PATH,
        "combinator.rule": _COMBINATOR_RULE_PATH,
    }.get(rulefile)
    if not path or not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]


# Expanded modifier-to-rule mapping for dictionary attacks (see new_dictionary_attack_editor.md)
# Each key is 'modifier:option' and maps to a hashcat rule line or a special loader for rule files.
# This mapping is used to generate ephemeral rule lists for attacks with UI modifiers.
MODIFIER_HASHCAT_RULE_MAP: dict[str, str] = {
    # Change case
    "change_case:uppercase": "u",  # Convert to uppercase
    "change_case:lowercase": "l",  # Convert to lowercase
    "change_case:capitalize": "c",  # Capitalize first letter
    "change_case:toggle": "t",  # Toggle case
    # Change chars order
    "change_chars_order:duplicate": "d",  # Duplicate word
    "change_chars_order:reverse": "r",  # Reverse word
    # Substitute chars (handled specially below)
    "substitute_chars:leetspeak": "__LOAD_BUILTIN_RULEFILE__:leetspeak.rule",
    "substitute_chars:combinator": "__LOAD_BUILTIN_RULEFILE__:combinator.rule",
}


async def _load_rulefile_lines(rulefile_name: str, db: AsyncSession) -> list[str]:
    """
    Load all rule lines from an AttackResourceFile with file_name=rulefile_name and resource_type=RULE_LIST.
    Returns a list of rule lines, or an empty list if not found.
    """
    from sqlalchemy import select

    from app.models.attack_resource_file import AttackResourceFile, AttackResourceType

    result = await db.execute(
        select(AttackResourceFile)
        .where(AttackResourceFile.file_name == rulefile_name)
        .where(AttackResourceFile.resource_type == AttackResourceType.RULE_LIST)
    )
    rulefile = result.scalar_one_or_none()
    if rulefile and rulefile.content and "lines" in rulefile.content:
        lines = rulefile.content["lines"]
        if isinstance(lines, list) and all(isinstance(line, str) for line in lines):
            return lines
        return []
    return []


async def create_ephemeral_rulelist_for_modifiers(
    modifiers: list[str], db: AsyncSession
) -> AttackResourceFile | None:
    """
    Given a list of modifier option keys (e.g., 'change_case:uppercase'),
    create an ephemeral AttackResourceFile of type EPHEMERAL_RULE_LIST with the correct rule lines.
    - For simple options, add the mapped hashcat rule line.
    - For 'substitute_chars' options, load all rules from the referenced built-in file.
    Returns the AttackResourceFile or None if no valid modifiers.
    This function is async because it may need to load rule files from the DB for other cases.
    """
    from uuid import uuid4

    from app.models.attack_resource_file import AttackResourceType

    if not modifiers:
        return None
    rule_lines: list[str] = []
    for mod in modifiers:
        rule = MODIFIER_HASHCAT_RULE_MAP.get(mod)
        if rule is None:
            continue  # Unknown modifier option, skip
        if rule.startswith("__LOAD_BUILTIN_RULEFILE__:"):
            # Special case: load all lines from the bundled rule file
            rulefile_name = rule.split(":", 1)[1]
            lines = _load_builtin_rulefile_lines(rulefile_name)
            rule_lines.extend(lines)
        elif rule.startswith("__LOAD_RULEFILE__:"):
            # Legacy: load from DB resource (should not be used for built-ins)
            rulefile_name = rule.split(":", 1)[1]
            lines = await _load_rulefile_lines(rulefile_name, db)
            rule_lines.extend(lines)
        else:
            rule_lines.append(rule)
    if not rule_lines:
        return None
    # Create the ephemeral rule list resource
    ephemeral_resource = AttackResourceFile(
        id=uuid4(),
        file_name="ephemeral_rulelist.rule",
        download_url="",  # Not downloadable from MinIO
        checksum="",  # Not applicable
        guid=uuid4(),
        resource_type=AttackResourceType.EPHEMERAL_RULE_LIST,  # Ephemeral, attack-scoped
        line_format="rule",
        line_encoding="ascii",
        used_for_modes=[AttackMode.DICTIONARY],
        source="ephemeral",
        line_count=len(rule_lines),
        byte_size=sum(len(r) for r in rule_lines),
        content={"lines": rule_lines},
    )
    db.add(ephemeral_resource)
    return ephemeral_resource


async def update_attack_service(
    attack_id: int,
    data: AttackUpdate,
    db: AsyncSession,
    confirm: bool = False,
) -> AttackOut:
    """
    Update an attack. If the attack is not pending and confirm is not set, raise AttackEditConfirmationError.
    If confirmed or pending, reset state to PENDING and clear times, then update fields.
    Only allow state transitions via this service (FSM rule).
    """
    result = await db.execute(select(Attack).where(Attack.id == attack_id))
    attack = result.scalar_one_or_none()
    if not attack:
        raise AttackNotFoundError(f"Attack {attack_id} not found")
    # If not pending and not confirmed, require confirmation
    if attack.state != AttackState.PENDING and not confirm:
        raise AttackEditConfirmationError(attack)
    # If confirmed or pending, reset state and update
    if attack.state != AttackState.PENDING or confirm:
        attack.state = AttackState.PENDING
        attack.start_time = None
        attack.end_time = None
        # Reset all associated tasks to PENDING for reprocessing
        if hasattr(attack, "tasks") and attack.tasks:
            for task in attack.tasks:
                task.status = TaskStatus.PENDING
                task.agent_id = None
                if hasattr(task, "retry_count") and task.retry_count is not None:
                    task.retry_count += 1
                else:
                    task.retry_count = 1
                task.error_message = None
                task.error_details = None
                task.progress = 0.0
            logger.info(
                f"Reset all tasks for attack_id={attack_id} to PENDING for reprocessing."
            )
    # If dictionary attack and modifiers are set, create ephemeral rule list
    modifiers = data.modifiers if data.modifiers is not None else []
    if (
        getattr(data, "attack_mode", None) == "dictionary"
        or getattr(attack, "attack_mode", None) == "dictionary"
    ) and modifiers:
        ephemeral_rulelist = await create_ephemeral_rulelist_for_modifiers(
            modifiers, db
        )
        if ephemeral_rulelist:
            await db.flush()
            # Store the ephemeral rule list's GUID (not DB id) for UI/test compatibility
            attack.left_rule = str(ephemeral_rulelist.guid)
    # Brute force charset derivation for MASK+increment_mode attacks (on update)
    if (
        getattr(data, "attack_mode", None) == "mask"
        or getattr(attack, "attack_mode", None) == AttackMode.MASK
    ):
        increment_mode = getattr(data, "increment_mode", None)
        if increment_mode is None:
            increment_mode = getattr(attack, "increment_mode", False)
        charset_options = getattr(data, "charset_options", None)
        length = getattr(data, "increment_maximum", None)
        if length is None:
            length = getattr(attack, "increment_maximum", 0)
        if (
            charset_options
            and increment_mode
            and isinstance(length, int)
            and length > 0
        ):
            from app.core.services.attack_complexity_service import (
                AttackEstimationService,
            )

            charset_result = (
                AttackEstimationService.generate_brute_force_mask_and_charset(
                    charset_options, length
                )
            )
            logger.debug(
                f"[BruteForce Derivation][Update] charset_options={charset_options} length={length} -> custom_charset_1={charset_result['custom_charset']}"
            )
            data.custom_charset_1 = charset_result["custom_charset"]
    # Update fields from AttackUpdate
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(attack, field) and value is not None:
            # Only set modifiers if value is a list (avoid dict/None)
            if field == "modifiers" and not isinstance(value, list):
                setattr(attack, field, None)
                continue
            setattr(attack, field, value)
    # Defensive: ensure attack.modifiers is a list or None before returning
    if hasattr(attack, "modifiers") and not (
        isinstance(attack.modifiers, list) or attack.modifiers is None
    ):
        attack.modifiers = None
    await db.commit()
    await db.refresh(attack)

    # SSE_TRIGGER: Attack updated
    await _broadcast_campaign_update(attack.campaign_id, None)

    return AttackOut.model_validate(attack, from_attributes=True)


def _create_ephemeral_wordlist(
    data: AttackCreate, db: AsyncSession
) -> AttackResourceFile | None:
    from uuid import uuid4

    if (
        data.attack_mode == AttackMode.DICTIONARY
        and data.wordlist_inline is not None
        and len(data.wordlist_inline) > 0
    ):
        ephemeral_resource = AttackResourceFile(
            id=uuid4(),
            file_name="ephemeral_wordlist.txt",
            download_url="",  # Not downloadable from MinIO
            checksum="",  # Not applicable
            guid=uuid4(),
            resource_type=AttackResourceType.EPHEMERAL_WORD_LIST,
            line_format="freeform",
            line_encoding="utf-8",
            used_for_modes=[AttackMode.DICTIONARY],
            source="ephemeral",
            line_count=len(data.wordlist_inline),
            byte_size=sum(len(w) for w in data.wordlist_inline),
            content={"lines": data.wordlist_inline},
        )
        db.add(ephemeral_resource)
        # Async flush must be awaited by caller
        return ephemeral_resource
    return None


def _create_ephemeral_masklist(
    data: AttackCreate, db: AsyncSession
) -> AttackResourceFile | None:
    from uuid import uuid4

    from pydantic import ValidationError

    from app.core.services.attack_complexity_service import AttackEstimationService

    if (
        data.attack_mode == AttackMode.MASK
        and data.masks_inline is not None
        and len(data.masks_inline) > 0
    ):
        invalid_lines = []
        for idx, mask in enumerate(data.masks_inline):
            valid, error = AttackEstimationService.validate_mask_syntax(mask)
            if not valid:
                invalid_lines.append(
                    {
                        "loc": ("masks_inline", idx),
                        "msg": error,
                        "type": "value_error.mask",
                    }
                )
        if invalid_lines:
            raise ValidationError(invalid_lines)
        ephemeral_mask_resource = AttackResourceFile(
            id=uuid4(),
            file_name="ephemeral_masklist.txt",
            download_url="",  # Not downloadable from MinIO
            checksum="",  # Not applicable
            guid=uuid4(),
            resource_type=AttackResourceType.EPHEMERAL_MASK_LIST,
            line_format="mask",
            line_encoding="ascii",
            used_for_modes=[AttackMode.MASK],
            source="ephemeral",
            line_count=len(data.masks_inline),
            byte_size=sum(len(m) for m in data.masks_inline),
            content={"lines": data.masks_inline},
        )
        db.add(ephemeral_mask_resource)
        # Async flush must be awaited by caller
        return ephemeral_mask_resource
    return None


def _derive_brute_force_charset(data: AttackCreate) -> str | None:
    if (
        getattr(data, "attack_mode", None) == AttackMode.MASK
        and getattr(data, "increment_mode", False)
        and hasattr(data, "charset_options")
        and getattr(data, "charset_options", None)
    ):
        charset_options = getattr(data, "charset_options", None)
        length = getattr(data, "increment_maximum", 0)
        if length is None:
            length = 0
        if charset_options and isinstance(length, int) and length > 0:
            from app.core.services.attack_complexity_service import (
                AttackEstimationService,
            )

            charset_result = (
                AttackEstimationService.generate_brute_force_mask_and_charset(
                    charset_options, length
                )
            )
            logger.debug(
                f"[BruteForce Derivation] charset_options={charset_options} length={length} -> custom_charset_1={charset_result['custom_charset']}"
            )
            return charset_result["custom_charset"]
    return None


async def create_attack_service(
    data: AttackCreate,
    db: AsyncSession,
) -> AttackOut:
    """
    Create a new attack, including ephemeral mask lists (masks_inline), ephemeral wordlists (wordlist_inline),
    ephemeral rule lists (for modifiers), and dynamic previous passwords wordlist.
    Returns the new attack as a Pydantic AttackOut schema.
    """
    word_list_id = None
    mask_list_id = None
    rule_list_id = None
    # 1. Ephemeral wordlist takes precedence if provided
    ephemeral_wordlist = _create_ephemeral_wordlist(data, db)
    if ephemeral_wordlist:
        await db.flush()  # Get PK if needed
        word_list_id = ephemeral_wordlist.id
    # 2. Ephemeral mask list support with per-line validation
    ephemeral_masklist = _create_ephemeral_masklist(data, db)
    if ephemeral_masklist:
        await db.flush()
        mask_list_id = ephemeral_masklist.id
    # 3. Ephemeral rule list for modifiers
    modifiers = data.modifiers if data.modifiers is not None else []
    if modifiers:
        ephemeral_rulelist = await create_ephemeral_rulelist_for_modifiers(
            modifiers, db
        )
        if ephemeral_rulelist:
            await db.flush()
            # Store the ephemeral rule list's GUID (not DB id) for UI/test compatibility
            rule_list_id = str(getattr(ephemeral_rulelist, "guid", rule_list_id))
    # 4. Brute force charset derivation for MASK+increment_mode attacks
    custom_charset_1 = _derive_brute_force_charset(data)
    if custom_charset_1:
        data.custom_charset_1 = custom_charset_1
    # Prepare ORM model data
    attack_kwargs = data.model_dump(exclude_unset=True)
    if word_list_id is not None:
        attack_kwargs["word_list_id"] = word_list_id
    if mask_list_id is not None:
        attack_kwargs["mask_list_id"] = mask_list_id
    if rule_list_id is not None:
        attack_kwargs["left_rule"] = rule_list_id
    # Remove fields not present in the Attack model
    attack_kwargs.pop("rule_list_id", None)
    attack_kwargs.pop("mask_list_id", None)
    attack_kwargs.pop("wordlist_inline", None)
    attack_kwargs.pop("masks_inline", None)
    attack_kwargs.pop("charset_options", None)
    attack = Attack(**attack_kwargs)
    db.add(attack)
    await db.commit()
    await db.refresh(attack)

    # SSE_TRIGGER: Attack created
    await _broadcast_campaign_update(attack.campaign_id, None)

    return AttackOut.model_validate(attack, from_attributes=True)


async def get_attack_service(
    attack_id: int,
    db: AsyncSession,
) -> Attack:
    """
    Fetch an Attack by ID, eagerly loading word_list. Raise AttackNotFoundError if not found.
    """
    from app.models.attack import Attack

    result = await db.execute(
        select(Attack)
        .options(selectinload(Attack.word_list))
        .where(Attack.id == attack_id)
    )
    attack = result.scalar_one_or_none()
    if not attack:
        raise AttackNotFoundError(f"Attack {attack_id} not found")
    return attack


async def export_attack_json_service(
    attack_id: int,
    db: AsyncSession,
) -> AttackTemplate:
    """
    Fetch an Attack by ID (eagerly loading word_list), convert to AttackTemplate, and return the template.
    """
    from app.models.attack import Attack

    result = await db.execute(
        select(Attack)
        .options(selectinload(Attack.word_list))
        .where(Attack.id == attack_id)
    )
    attack = result.scalar_one_or_none()
    if not attack:
        raise AttackNotFoundError(f"Attack {attack_id} not found")
    return attack_to_template(attack)


async def get_campaign_attack_table_fragment_service(
    attack_id: int,
    direction: AttackMoveDirection,
    db: AsyncSession,
) -> list[AttackSummary]:
    """
    Move an attack within its campaign and return the updated attack summaries for the campaign.

    Args:
        attack_id: The attack to move
        direction: One of AttackMoveDirection
        db: AsyncSession
    Returns:
        List of attack summaries for the campaign (for table rendering)

    Raises:
        AttackNotFoundError: if attack or campaign not found
    """
    # Move the attack
    await move_attack_service(attack_id, direction, db)
    # Fetch the campaign_id for this attack
    result = await db.execute(select(Attack).where(Attack.id == attack_id))
    attack = result.scalar_one_or_none()
    if not attack or not attack.campaign_id:
        raise AttackNotFoundError(f"Attack {attack_id} or its campaign not found")
    campaign_id = attack.campaign_id
    # Fetch updated attack summaries for the campaign
    from app.core.services.campaign_service import (
        get_campaign_with_attack_summaries_service,
    )

    campaign_data = await get_campaign_with_attack_summaries_service(campaign_id, db)
    return campaign_data.attacks


# --- Progress/ETA utility extraction ---


def calculate_progress_and_eta(
    total_hashes: int, progress_percent: float, hashes_per_sec: float
) -> tuple[int, int | None]:
    """
    Calculate hashes_done and ETA (seconds) given total_hashes, progress_percent, and hashes_per_sec.
    Returns (hashes_done, eta). ETA is None if not computable.

    Args:
        total_hashes: Total number of hashes to process
        progress_percent: Current progress percentage (0-100)
        hashes_per_sec: Estimated hashes per second

    Returns:
        Tuple of (hashes_done, eta)
    """
    hashes_done = int((progress_percent / 100.0) * total_hashes) if total_hashes else 0
    eta = None
    if hashes_per_sec > 0 and total_hashes > 0:
        remaining = total_hashes - hashes_done
        eta = int(remaining / hashes_per_sec)
    return hashes_done, eta


async def get_attack_performance_summary_service(
    attack_id: int, db: AsyncSession
) -> AttackPerformanceSummary:
    """
    Aggregate hashes/sec, total hashes, agent count, and ETA for the attack.
    Returns an AttackPerformanceSummary object.
    """
    from loguru import logger
    from sqlalchemy import select

    from app.models.attack import Attack
    from app.models.hashcat_benchmark import HashcatBenchmark
    from app.models.task import Task

    result = await db.execute(
        select(Attack)
        .options(selectinload(Attack.tasks).selectinload(Task.agent))
        .where(Attack.id == attack_id)
    )
    attack = result.scalar_one_or_none()
    if not attack:
        logger.error(f"Attack {attack_id} not found for performance summary")
        raise AttackNotFoundError(f"Attack {attack_id} not found")

    tasks = attack.tasks or []
    agents = {t.agent for t in tasks if t.agent is not None}
    agent_count = len(agents)
    total_hashes = sum(t.keyspace_total for t in tasks)

    # Aggregate hashes/sec from agent benchmarks for this hash_type
    hash_type = await get_hash_type_for_attack(attack, db)
    hashes_per_sec = 0.0
    if agent_count > 0:
        agent_ids = [a.id for a in agents]
        bench_result = await db.execute(
            select(HashcatBenchmark.agent_id, HashcatBenchmark.hash_speed)
            .where(HashcatBenchmark.agent_id.in_(agent_ids))
            .where(HashcatBenchmark.hash_type_id == hash_type.id)
        )
        speeds = [row.hash_speed for row in bench_result.all()]
        hashes_per_sec = sum(speeds)

    # Calculate progress and ETA
    progress = attack.progress_percent
    from app.core.services.attack_service import calculate_progress_and_eta

    hashes_done, eta = calculate_progress_and_eta(
        total_hashes, progress, hashes_per_sec
    )
    # Defensive: ensure attack.modifiers is a list or None before returning
    if hasattr(attack, "modifiers") and not (
        isinstance(attack.modifiers, list) or attack.modifiers is None
    ):
        attack.modifiers = None
    return AttackPerformanceSummary(
        hashes_per_sec=hashes_per_sec,
        total_hashes=total_hashes,
        agent_count=agent_count,
        eta=eta,
        progress=progress,
        hashes_done=hashes_done,
        attack=AttackOut.model_validate(attack, from_attributes=True),
    )


async def get_attack_list_service(
    db: AsyncSession, page: int = 1, size: int = 20, q: str | None = None
) -> tuple[list[AttackSummary], int, int]:
    stmt = select(Attack)
    if q:
        stmt = stmt.where(
            or_(Attack.name.ilike(f"%{q}%"), Attack.description.ilike(f"%{q}%"))
        )
    stmt = stmt.order_by(Attack.id.desc())
    total = (
        await db.execute(select(func.count()).select_from(stmt.subquery()))
    ).scalar_one()
    total_pages = (total + size - 1) // size if size else 1
    offset = (page - 1) * size
    stmt = stmt.offset(offset).limit(size)
    result = await db.execute(stmt)
    attacks = result.scalars().all()
    # Eager load tasks for summary fields
    for attack in attacks:
        await db.refresh(attack, attribute_names=["tasks"])
    summaries = []
    for attack in attacks:
        type_label = attack.attack_mode.value.replace("_", " ").title()
        length = None
        if attack.mask:
            length = len(attack.mask)
        settings_summary = f"Mode: {type_label}, Hash Mode: {attack.hash_mode}"
        keyspace = None
        if attack.tasks:
            keyspace = sum(getattr(t, "keyspace_total", 0) or 0 for t in attack.tasks)
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
                comment=getattr(attack, "comment", None),
            )
        )
    return summaries, total, total_pages


async def delete_attack_service(
    attack_id: int, db: AsyncSession
) -> dict[str, bool | int]:
    """
    Delete a single attack by ID. If the attack has not started, delete from DB.
    If the attack has started, mark as abandoned and stop the attack.
    Clean up ephemeral resources. Unlink non-ephemeral resources.
    """
    from sqlalchemy import select

    from app.models.attack_resource_file import AttackResourceFile, AttackResourceType

    result = await db.execute(select(Attack).where(Attack.id == attack_id))
    attack = result.scalar_one_or_none()
    if not attack:
        raise AttackNotFoundError(f"Attack {attack_id} not found")

    # Helper: delete ephemeral resource if present
    async def _delete_ephemeral_resource(
        resource_id: UUID | None, expected_type: AttackResourceType
    ) -> None:
        if not resource_id:
            return
        resource = await db.get(AttackResourceFile, resource_id)
        if resource and resource.resource_type == expected_type:
            await db.delete(resource)

    # Clean up ephemeral resources
    await _delete_ephemeral_resource(
        getattr(attack, "word_list_id", None), AttackResourceType.EPHEMERAL_WORD_LIST
    )
    await _delete_ephemeral_resource(
        getattr(attack, "mask_list_id", None), AttackResourceType.EPHEMERAL_MASK_LIST
    )
    # left_rule may be a UUID string for ephemeral rule list
    left_rule = getattr(attack, "left_rule", None)
    if left_rule:
        # Try to parse as UUID and delete if ephemeral
        try:
            import uuid

            rule_resource_result = await db.execute(
                select(AttackResourceFile).where(
                    AttackResourceFile.guid == uuid.UUID(str(left_rule))
                )
            )
            rule_resource = rule_resource_result.scalar_one_or_none()
            if (
                rule_resource
                and rule_resource.resource_type
                == AttackResourceType.EPHEMERAL_RULE_LIST
            ):
                await db.delete(rule_resource)
        except (ValueError, TypeError, AttributeError) as exc:
            logger.warning(
                f"Failed to delete ephemeral rule resource for attack {attack_id}: {exc}"
            )

    # Store campaign_id for SSE trigger
    campaign_id = attack.campaign_id

    # If the attack has not started, delete from DB
    if attack.state in [AttackState.PENDING, None]:
        await db.delete(attack)
        await db.commit()

        # SSE_TRIGGER: Attack deleted
        await _broadcast_campaign_update(campaign_id, None)

        return {"id": attack_id, "deleted": True}
    # If the attack has started, mark as abandoned and stop tasks
    attack.state = AttackState.ABANDONED
    # Stop all tasks for this attack
    if hasattr(attack, "tasks") and attack.tasks:
        for task in attack.tasks:
            task.status = TaskStatus.ABANDONED
    await db.commit()

    # SSE_TRIGGER: Attack abandoned
    await _broadcast_campaign_update(campaign_id, None)

    return {"id": attack_id, "deleted": True}


__all__ = [
    "AttackNotFoundError",
    "InvalidAgentTokenError",
    "bulk_delete_attacks_service",
    "create_attack_service",
    "delete_attack_service",
    "duplicate_attack_service",
    "estimate_attack_keyspace_and_complexity",
    "export_attack_json_service",
    "export_attack_template_service",
    "get_attack_config_service",
    "get_attack_list_service",
    "get_attack_performance_summary_service",
    "get_attack_service",
    "get_campaign_attack_table_fragment_service",
    "move_attack_service",
    "update_attack_service",
]
