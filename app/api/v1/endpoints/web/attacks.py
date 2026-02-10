"""
Follow these rules for all endpoints in this file:
1. Must return Pydantic models as JSON (no TemplateResponse or render()).
2. Must use FastAPI parameter types: Query, Path, Body, Depends, etc.
3. Must not parse inputs manually -- let FastAPI validate and raise 422s.
4. Must use dependency-injected context for auth/user/project state.
5. Must not include database logic -- delegate to a service layer (e.g. campaign_service).
6. Must not contain HTMX, Jinja, or fragment-rendering logic.
7. Must annotate live-update triggers with: # WS_TRIGGER: <event description>
"""

import io
from typing import Annotated, Any

from fastapi import (
    APIRouter,
    Body,
    Depends,
    HTTPException,
    Query,
    status,
)
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authz import user_can_access_project
from app.core.deps import get_current_user
from app.core.services.attack_complexity_service import AttackEstimationService
from app.core.services.attack_service import (
    AttackEditConfirmationError,
    AttackNotFoundError,
    bulk_delete_attacks_service,
    create_attack_service,
    delete_attack_service,
    duplicate_attack_service,
    estimate_attack_keyspace_and_complexity,
    export_attack_json_service,
    get_attack_list_service,
    get_attack_performance_summary_service,
    get_attack_service,
    get_campaign_attack_table_fragment_service,
    update_attack_service,
)
from app.core.state_machines import AttackStateMachine, InvalidStateTransitionError
from app.db.session import get_db
from app.models.attack import Attack
from app.models.campaign import Campaign
from app.models.user import User
from app.schemas.attack import (
    AttackBulkDeleteRequest,
    AttackCreate,
    AttackEditorContext,
    AttackMoveRequest,
    AttackOut,
    AttackPerformanceSummary,
    AttackSummary,
    AttackUpdate,
    BruteForceMaskRequest,
    BruteForceMaskResponse,
    EstimateAttackRequest,
    EstimateAttackResponse,
    MaskValidationRequest,
    MaskValidationResponse,
)
from app.schemas.error import ErrorObject
from app.schemas.schema_loader import validate_attack_template

router = APIRouter(prefix="/attacks", tags=["Attacks"])


@router.get(
    "/editor-modal",
    summary="Attack editor modal",
    description="Return the attack editor modal context for a new or imported attack.",
    status_code=status.HTTP_200_OK,
)
async def attack_editor_modal() -> AttackEditorContext:
    """
    Returns the context for the attack editor modal (empty for new attack).
    """
    return AttackEditorContext()


# /api/v1/web/attacks/{attack_id}/move
@router.post(
    "/{attack_id}/move",
    summary="Move attack within campaign",
    description="Reposition an attack within its campaign (up, down, top, bottom).",
    status_code=status.HTTP_200_OK,
    responses={404: {"model": ErrorObject}, 403: {"model": ErrorObject}},
)
async def move_attack(
    attack_id: int,
    data: AttackMoveRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> AttackEditorContext:
    attack = await db.execute(select(Attack).where(Attack.id == attack_id))
    attack_obj = attack.scalar_one_or_none()
    if not attack_obj:
        raise HTTPException(status_code=404, detail="Attack not found")
    campaign = await db.execute(
        select(Campaign).where(Campaign.id == attack_obj.campaign_id)
    )
    campaign_obj = campaign.scalar_one_or_none()
    if not campaign_obj or not user_can_access_project(
        current_user, campaign_obj.project, action="update"
    ):
        raise HTTPException(status_code=403, detail="Not authorized for this project.")
    try:
        attacks = await get_campaign_attack_table_fragment_service(
            attack_id, data.direction, db
        )
    except AttackNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    # TODO: Return the updated attack list context (replace with appropriate response model)
    return AttackEditorContext(attack=attacks)


# /api/v1/web/attacks/{attack_id}/duplicate
@router.post(
    "/{attack_id}/duplicate",
    summary="Duplicate attack in-place",
    description="Clone an attack in-place and insert the copy at the end of the campaign's attack list.",
    status_code=status.HTTP_201_CREATED,
    responses={404: {"model": ErrorObject}},
)
async def duplicate_attack(
    attack_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AttackOut:
    # TODO: Add authentication/authorization
    try:
        new_attack = await duplicate_attack_service(attack_id, db)
        return AttackOut.model_validate(new_attack, from_attributes=True)
    except AttackNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


# /api/v1/web/attacks/bulk
@router.delete(
    "/bulk",
    summary="Bulk delete attacks",
    description="Delete multiple attacks by their IDs in a single request.",
    status_code=status.HTTP_200_OK,
)
async def bulk_delete_attacks(
    data: AttackBulkDeleteRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, list[int]]:
    # TODO: Add authentication/authorization
    if not data.attack_ids:
        return {"deleted_ids": [], "not_found_ids": []}
    try:
        result = await bulk_delete_attacks_service(data.attack_ids, db)
    except AttackNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    return result


def _set_default(data: dict[str, Any], key: str, value: object) -> None:
    if key not in data or data[key] is None:
        data[key] = value


def _patch_dictionary_attack_payload(data: dict[str, Any]) -> dict[str, Any]:
    # Legacy field mapping
    if "attack_mode" not in data and "mode" in data:
        data["attack_mode"] = data["mode"]
    if "min_length" in data and "increment_minimum" not in data:
        data["increment_minimum"] = data["min_length"]
    if "max_length" in data and "increment_maximum" not in data:
        data["increment_maximum"] = data["max_length"]
    # Set required numeric fields
    _set_default(data, "hash_type_id", 0)
    _set_default(data, "hash_mode", 0)
    _set_default(data, "min_length", 1)
    _set_default(data, "max_length", 1)
    _set_default(data, "wordlist_size", 10000)
    _set_default(data, "rule_count", 1)
    _set_default(data, "attack_mode_hashcat", 0)
    _set_default(data, "state", "pending")
    _set_default(data, "campaign_id", 0)
    _set_default(data, "hash_list_id", 0)
    _set_default(data, "name", "Test Attack")
    _set_default(data, "description", "")
    # Set required string fields
    _set_default(data, "hash_list_url", "dummy")
    _set_default(data, "hash_list_checksum", "dummy")
    # Set all legacy resource fields to None if not present
    for field in [
        "wordlist_guid",
        "rulelist_guid",
        "masklist_guid",
        "wordlist_inline",
        "rules_inline",
        "masks_inline",
        "position",
        "comment",
        "rule_file",
    ]:
        if field not in data:
            data[field] = None
    return data


def _patch_legacy_attack_payload(data: dict[str, Any]) -> dict[str, Any]:
    if data.get("attack_mode") == "dictionary" or data.get("mode") == "dictionary":
        return _patch_dictionary_attack_payload(data)
    return data


@router.post(
    "/estimate",
    summary="Estimate keyspace and complexity for unsaved attack config",
    description="Return keyspace and complexity score for the given attack config (unsaved).",
    status_code=status.HTTP_200_OK,
    responses={400: {"model": ErrorObject}},
)
async def estimate_attack(
    attack_data: EstimateAttackRequest,
) -> dict[str, Any]:
    """
    Accepts attack config as JSON, returns keyspace and complexity as JSON.
    """
    try:
        result: EstimateAttackResponse = await estimate_attack_keyspace_and_complexity(
            attack_data
        )
    except (ValueError, TypeError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    else:
        return {
            "message": f"Keyspace Estimate: {result.keyspace}, Complexity Score: {result.complexity_score}",
            "keyspace": result.keyspace,
            "complexity_score": result.complexity_score,
        }


@router.get(
    "/{attack_id}/export",
    summary="Export attack as JSON",
    description="Export a single attack as a JSON file using the AttackTemplate schema.",
    status_code=status.HTTP_200_OK,
)
async def export_attack_json(
    attack_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> StreamingResponse:
    # TODO: Add authentication/authorization
    try:
        template = await export_attack_json_service(attack_id, db)
    except AttackNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    json_bytes = template.model_dump_json().encode()
    return StreamingResponse(
        io.BytesIO(json_bytes),
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=attack_{attack_id}.json"
        },
    )


@router.post(
    "/import_json",
    summary="Import attack from JSON",
    description="Import an attack from a JSON file or payload and prefill the attack editor modal.",
    status_code=status.HTTP_200_OK,
    responses={400: {"model": ErrorObject}},
)
async def import_attack_json(
    data: Annotated[dict[str, Any], Body()],
) -> dict[str, Any]:
    """
    Accepts JSON payload, returns an AttackEditorContext for the editor modal (not persisted).
    """
    try:
        template = validate_attack_template(data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid template: {e}"
        ) from e
    return {
        "message": "Attack template imported successfully.",
        "attack": template.model_dump(),
        "imported": True,
    }


@router.post(
    "/validate",
    summary="Validate attack configuration (dry-run)",
    description="Validate an attack config and return either errors or a keyspace/complexity summary as JSON.",
    status_code=status.HTTP_200_OK,
    responses={400: {"model": ErrorObject}},
)
async def validate_attack(
    data: Annotated[dict[str, Any], Body()],
) -> dict[str, Any]:
    """
    Accepts attack config as JSON, returns keyspace and complexity as JSON if valid.
    """
    try:
        data = _patch_legacy_attack_payload(data)
        attack_req = EstimateAttackRequest.model_validate(data)
        # Compute keyspace/complexity
        result = await estimate_attack_keyspace_and_complexity(attack_req)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Validation failed. Please correct the highlighted fields.",
        ) from e
    except (ValueError, TypeError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    else:
        return {
            "message": f"Attack Validated. Keyspace: {result.keyspace}, Complexity Score: {result.complexity_score}",
            "keyspace": result.keyspace,
            "complexity_score": result.complexity_score,
        }


@router.post(
    "",
    summary="Create a new attack",
    description="Create a new attack, supporting ephemeral mask lists via masks_inline.",
    status_code=status.HTTP_201_CREATED,
)
async def create_attack(
    data: AttackCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AttackOut:
    # TODO: Add authentication/authorization
    try:
        attack = await create_attack_service(data, db)
        return AttackOut.model_validate(attack, from_attributes=True)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=e.errors()
        ) from e


@router.get("")
async def list_attacks(
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
    q: Annotated[
        str | None, Query(description="Search query for attack name/description")
    ] = None,
) -> dict[str, Any]:
    """
    Returns a paginated, searchable list of attacks as JSON for the SvelteKit dashboard.
    """
    attacks, _, _ = await get_attack_list_service(db, page=page, size=size, q=q)
    return {
        "items": [a.model_dump() for a in attacks],
        "page": page,
        "size": size,
        "q": q,
    }


@router.get(
    "/attack_table_body",
    summary="Attack table body fragment",
    description="Returns the attack list for the campaign as AttackSummary objects.",
    status_code=status.HTTP_200_OK,
)
async def attack_table_body_fragment(
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
    q: Annotated[
        str | None, Query(description="Search query for attack name/description")
    ] = None,
) -> list[AttackSummary]:
    """
    Returns a list of attack summary objects for the table body.
    """
    attacks, _, _ = await get_attack_list_service(db, page=page, size=size, q=q)
    return attacks


@router.get(
    "/{attack_id}",
    summary="Get attack by ID",
    description="Get a single attack by its ID as JSON.",
    status_code=status.HTTP_200_OK,
)
async def get_attack(
    attack_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AttackOut:
    try:
        attack = await get_attack_service(attack_id, db)
        return AttackOut.model_validate(attack, from_attributes=True)
    except AttackNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post(
    "/brute_force_mask",
    summary="Generate brute force mask and custom charset",
    description="Given charset options and length, return the mask and custom charset string for brute force attacks.",
    status_code=status.HTTP_200_OK,
)
async def brute_force_mask(
    data: BruteForceMaskRequest,
) -> BruteForceMaskResponse:
    """
    Accepts a JSON body with 'charset_options' (list[str]) and 'length' (int).
    Returns a dict with 'mask' and 'custom_charset'.
    """
    result = AttackEstimationService.generate_brute_force_mask_and_charset(
        data.charset_options, data.length
    )
    return BruteForceMaskResponse(**result)


@router.get(
    "/{attack_id}/performance",
    summary="Attack performance summary",
    description="Return an AttackPerformanceSummary object with hashes/sec, total hashes, agent count, and ETA for the attack.",
    status_code=status.HTTP_200_OK,
)
async def attack_performance_summary(
    attack_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    try:
        perf = await get_attack_performance_summary_service(attack_id, db)
        return {
            "message": "Performance Summary",
            "data": perf.model_dump(),
        }
    except AttackNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post(
    "/{attack_id}/disable_live_updates",
    summary="Toggle live updates for attack (UI only)",
    description="Enable or disable live updates for this attack for the current user. Returns a JSON object with enabled status.",
    status_code=status.HTTP_200_OK,
)
async def disable_live_updates(
    attack_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    enabled: bool | None = None,
) -> dict[str, Any]:
    try:
        await get_attack_service(attack_id, db)
    except AttackNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    status_str = "Enabled" if enabled else "Disabled"
    return {"message": f"Live Updates {status_str}"}


@router.get(
    "/{attack_id}/view-modal",
    summary="View attack config and performance modal",
    description="Return a dict with attack config and performance for the dashboard view modal.",
    status_code=status.HTTP_200_OK,
)
async def view_attack_modal(
    attack_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, AttackOut | AttackPerformanceSummary | None]:
    """
    Returns a dict with attack config and performance summary for the dashboard view modal.
    """
    try:
        perf = await get_attack_performance_summary_service(attack_id, db)
    except AttackNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Attack not found"
        ) from e
    return {
        "attack": perf.attack,
        "performance": perf,
    }


@router.delete(
    "/{attack_id}",
    summary="Delete attack",
    description="Delete an attack by ID. If not started, deletes from DB. If started, marks as abandoned and stops tasks. Cleans up ephemeral resources.",
    status_code=status.HTTP_200_OK,
)
async def delete_attack(
    attack_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, bool | int]:
    # Authorization: fetch attack and campaign, check project access
    attack_obj = (
        await db.execute(select(Attack).where(Attack.id == attack_id))
    ).scalar_one_or_none()
    if not attack_obj:
        raise HTTPException(status_code=404, detail="Attack not found")
    campaign_obj = (
        await db.execute(select(Campaign).where(Campaign.id == attack_obj.campaign_id))
    ).scalar_one_or_none()
    if not campaign_obj or not user_can_access_project(
        current_user, campaign_obj.project, action="delete"
    ):
        raise HTTPException(status_code=403, detail="Not authorized for this project.")
    try:
        result = await delete_attack_service(attack_id, db)
    except AttackNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except InvalidStateTransitionError as e:
        from app.models.attack import AttackState

        if isinstance(e.from_state, AttackState):
            valid_actions = AttackStateMachine.get_valid_actions(e.from_state)
            detail = f"Cannot abort attack from state '{e.from_state.value}'. Valid actions: {valid_actions}"
        else:
            detail = f"Cannot abort attack from state '{e.from_state.value}'."
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        ) from e
    return result


@router.post(
    "/validate_mask",
    summary="Validate hashcat mask syntax",
    description="Validate a hashcat mask string for syntax correctness. Returns valid/error JSON.",
    status_code=status.HTTP_200_OK,
    response_model=MaskValidationResponse,
)
async def validate_mask(
    data: MaskValidationRequest,
) -> MaskValidationResponse | JSONResponse:
    """
    Validate a hashcat mask string for syntax correctness. Returns valid/error JSON.
    """
    valid, error = AttackEstimationService.validate_mask_syntax(data.mask)
    if valid:
        return MaskValidationResponse(valid=True, error=None)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=MaskValidationResponse(valid=False, error=error).model_dump(),
    )


@router.patch(
    "/{attack_id}",
    summary="Edit attack configuration",
    description="Edit an attack. If the attack is running or completed, require confirmation before resetting to pending and applying changes.",
    status_code=status.HTTP_200_OK,
)
async def edit_attack(
    attack_id: int,
    data: AttackUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    try:
        attack = await update_attack_service(
            attack_id, data, db, confirm=getattr(data, "confirm", False)
        )
        return {
            "message": f"Attack '{attack.name}' updated successfully.",
            "data": AttackOut.model_validate(attack, from_attributes=True).model_dump(),
        }
    except AttackEditConfirmationError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"This attack is currently {e.attack.state.value}. Editing will reset it to pending and reprocess. Confirm to proceed.",
        ) from e
    except AttackNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
