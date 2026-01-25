"""
Follow these rules for all endpoints in this file:
1. Must return Pydantic models as JSON (no TemplateResponse or render()).
2. Must use FastAPI parameter types: Query, Path, Body, Depends, etc. NEVER use dicts and NEVER parse inputs manually.
3. Must not parse inputs manually -- let FastAPI validate and raise 422s.
4. Must use dependency-injected context for auth/user/project state.
5. Must not include database logic -- delegate to a service layer (e.g. campaign_service).
6. Must not contain HTMX, Jinja, or fragment-rendering logic.
7. Must annotate live-update triggers with: # WS_TRIGGER: <event description>
"""

from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Body,
    Depends,
    Form,
    HTTPException,
    Path,
    status,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authz import user_can_access_project_by_id
from app.core.config import settings
from app.core.deps import get_current_user
from app.core.services.resource_service import (
    add_resource_line_service,
    check_project_access,
    check_resource_editable,
    create_resource_and_presign_service,
    delete_resource_line_service,
    delete_resource_service,
    get_resource_content_service,
    get_resource_lines_service,
    get_resource_or_404,
    is_resource_editable,
    list_resources_service,
    list_rulelists_service,
    list_wordlists_service,
    refresh_resource_metadata_service,
    update_resource_content_service,
    update_resource_line_service,
    validate_resource_lines_service,
)
from app.db.session import get_db
from app.models.attack_resource_file import AttackResourceFile, AttackResourceType
from app.models.user import User
from app.schemas.resource import (
    EDITABLE_RESOURCE_TYPES,
    EPHEMERAL_RESOURCE_TYPES,
    MAX_FILE_LABEL_LENGTH,
    AttackBasic,
    ResourceContentResponse,
    ResourceDetailResponse,
    ResourceLinesResponse,
    ResourceListResponse,
    ResourcePreviewResponse,
    ResourceUpdateRequest,
    ResourceUploadedResponse,
    ResourceUploadFormSchema,
    ResourceUploadMeta,
    ResourceUploadResponse,
    RulelistDropdownResponse,
    RulelistItem,
    WordlistDropdownResponse,
    WordlistItem,
)

router = APIRouter(prefix="/resources", tags=["Resources"])


async def _get_resource_if_accessable(
    resource_id: UUID,
    db: AsyncSession,
    current_user: User,
) -> AttackResourceFile:
    resource = await get_resource_or_404(resource_id, db)
    await check_project_access(resource, current_user, db)
    return resource


@router.get(
    "/{resource_id}/content",
    summary="Get raw editable text content for a resource",
    description="Return the raw text content for eligible resources (mask, rule, wordlist, charset). Enforces editability constraints.",
)
async def get_resource_content(
    resource_id: Annotated[
        UUID, Path(description="The resource ID to get the content for")
    ],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ResourceContentResponse:
    (
        resource_model,
        content_str,
        error_message,
        status_code,
        editable,
    ) = await get_resource_content_service(resource_id, db)
    if error_message:
        raise HTTPException(status_code=status_code, detail=error_message)

    if not resource_model:
        raise HTTPException(status_code=404, detail="Resource not found")

    final_content = content_str if content_str is not None else ""

    return ResourceContentResponse(
        id=resource_model.id,
        file_name=resource_model.file_name,
        resource_type=resource_model.resource_type,
        line_count=resource_model.line_count,
        byte_size=resource_model.byte_size,
        updated_at=resource_model.updated_at,
        line_format=resource_model.line_format,
        line_encoding=resource_model.line_encoding,
        used_for_modes=[
            m.value if hasattr(m, "value") else str(m)
            for m in resource_model.used_for_modes
        ]
        if resource_model.used_for_modes
        else [],
        source=resource_model.source,
        project_id=resource_model.project_id,
        unrestricted=(resource_model.project_id is None),
        content=final_content,
        editable=editable,
    )


@router.get(
    "/wordlists",
    summary="List all wordlist resources for dropdown",
    description="Return all wordlist resources, sorted by last modified, with search and entry count support.",
)
async def list_wordlists(
    db: Annotated[AsyncSession, Depends(get_db)],
    q: str | None = None,
) -> WordlistDropdownResponse:
    wordlist_models = await list_wordlists_service(db, q)
    wordlist_items = [
        WordlistItem(id=wl.id, file_name=wl.file_name, line_count=wl.line_count)
        for wl in wordlist_models
    ]
    return WordlistDropdownResponse(wordlists=wordlist_items)


@router.get(
    "/rulelists",
    summary="List all rule list resources for dropdown",
    description="Return all rule list resources, sorted by last modified, with search and entry count support.",
)
async def list_rulelists(
    db: Annotated[AsyncSession, Depends(get_db)],
    q: str | None = None,
) -> RulelistDropdownResponse:
    rulelist_models = await list_rulelists_service(db, q)
    rulelist_items = [
        RulelistItem(id=rl.id, file_name=rl.file_name, line_count=rl.line_count)
        for rl in rulelist_models
    ]
    return RulelistDropdownResponse(rulelists=rulelist_items)


# Helper: check if resource is editable
async def _check_editable(resource: AttackResourceFile) -> None:
    if resource.resource_type == AttackResourceType.DYNAMIC_WORD_LIST:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Editing not allowed for dynamic word lists.",
        )
    if (
        resource.line_count is not None
        and settings.RESOURCE_EDIT_MAX_LINES is not None
        and resource.line_count > settings.RESOURCE_EDIT_MAX_LINES
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Resource too large for in-browser editing.",
        )
    if (
        resource.byte_size is not None
        and settings.RESOURCE_EDIT_MAX_SIZE_MB is not None
        and resource.byte_size > settings.RESOURCE_EDIT_MAX_SIZE_MB * 1024 * 1024
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Resource too large for in-browser editing.",
        )
    if resource.resource_type not in EDITABLE_RESOURCE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Resource type not editable."
        )


def _enforce_editable(resource: AttackResourceFile) -> None:
    if not is_resource_editable(resource):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Editing is disabled for this resource (read-only or too large).",
        )


@router.get(
    "/{resource_id}/lines",
    summary="List lines in a file-backed resource (paginated, optionally validated)",
    description="Return a paginated list of lines in the resource for in-browser editing. Supports ?validate=true for batch validation.",
)
async def list_resource_lines(
    resource_id: Annotated[UUID, Path()],
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    page: int = 1,
    page_size: int = 100,
    validate: bool = False,
) -> ResourceLinesResponse:
    resource_model = await _get_resource_if_accessable(resource_id, db, current_user)

    if resource_model.resource_type not in EDITABLE_RESOURCE_TYPES:
        raise HTTPException(
            status_code=403,
            detail="Ephemeral resources are not editable via this endpoint.",
        )
    _enforce_editable(resource_model)
    lines = await get_resource_lines_service(resource_id, db, page, page_size)
    if validate:
        from app.core.services.resource_service import _validate_line

        validated_lines = []
        for line in lines:
            valid, error = _validate_line(line.content, resource_model.resource_type)
            validated_lines.append(
                type(line)(
                    id=line.id,
                    index=line.index,
                    content=line.content,
                    valid=valid,
                    error_message=error,
                )
            )
        lines = validated_lines
    return ResourceLinesResponse(lines=lines, resource_id=resource_id)


@router.post(
    "/{resource_id}/lines",
    summary="Add a new line to a file-backed resource (204 No Content)",
    description="Add a new line to the resource. Returns 204 No Content on success, 422 JSON on validation error.",
    status_code=204,
)
async def add_resource_line(
    resource_id: Annotated[UUID, Path()],
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    line: Annotated[str, Body(embed=True, description="Line content to add")],
) -> None:
    resource_model: AttackResourceFile = await _get_resource_if_accessable(
        resource_id, db, current_user
    )

    _enforce_editable(resource_model)
    await add_resource_line_service(resource_id, db, line)


@router.patch(
    "/{resource_id}/lines/{line_id}",
    summary="Update a line in a file-backed resource (204 No Content)",
    description="Update an existing line in the resource. Returns 204 No Content on success, 422 JSON on validation error.",
    status_code=204,
)
async def update_resource_line(
    resource_id: Annotated[UUID, Path()],
    line_id: Annotated[int, Path()],
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    line: Annotated[str, Body(embed=True, description="New line content")],
) -> None:
    resource_model: AttackResourceFile = await _get_resource_if_accessable(
        resource_id, db, current_user
    )

    _enforce_editable(resource_model)
    await update_resource_line_service(resource_id, line_id, db, line)


@router.delete(
    "/{resource_id}/lines/{line_id}",
    summary="Delete a line from a file-backed resource (204 No Content)",
    description="Delete a line from the resource. Returns 204 No Content on success.",
    status_code=204,
)
async def delete_resource_line(
    resource_id: Annotated[UUID, Path()],
    line_id: Annotated[int, Path()],
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    resource_model: AttackResourceFile = await _get_resource_if_accessable(
        resource_id, db, current_user
    )

    _enforce_editable(resource_model)
    await delete_resource_line_service(resource_id, line_id, db)


@router.get(
    "/{resource_id}/lines/validate",
    summary="Validate all lines in a file-backed resource (JSON, batch validation)",
    description="Return a JSON list of ResourceLineValidationError for all invalid lines in the resource. Returns 204 No Content if all lines are valid.",
)
async def validate_resource_lines(
    resource_id: Annotated[UUID, Path()],
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, object] | None:
    resource_model = await _get_resource_if_accessable(resource_id, db, current_user)

    if resource_model.resource_type not in EDITABLE_RESOURCE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Resource type not editable."
        )

    await check_resource_editable(resource_model)
    errors = await validate_resource_lines_service(resource_id, db)
    if not errors:
        return None
    return {"errors": [e.model_dump(mode="json") for e in errors]}


@router.get(
    "/",
    summary="List all resources (paginated, filterable)",
    description="Return a paginated, filterable list of all resources for the resource browser.",
)
async def list_resources(
    db: Annotated[AsyncSession, Depends(get_db)],
    resource_type: AttackResourceType | None = None,
    q: str = "",
    page: int = 1,
    page_size: int = 25,
) -> ResourceListResponse:
    return await list_resources_service(
        db=db,
        resource_type=resource_type,
        q=q,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/",
    summary="Upload metadata, request presigned upload URL",
    description="Create an AttackResourceFile DB record and return a presigned S3 upload URL. If upload fails, ensure no orphaned DB record remains.",
    status_code=201,
)
async def upload_resource_metadata(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    background_tasks: BackgroundTasks,
    file_name: Annotated[str, Form(...)],
    resource_type: Annotated[str, Form(...)],
    project_id: Annotated[int | None, Form()] = None,
    detect_type: Annotated[bool, Form()] = False,
    line_format: Annotated[str | None, Form()] = None,
    line_encoding: Annotated[str | None, Form()] = None,
    used_for_modes: Annotated[str | None, Form()] = None,  # comma-separated
    source: Annotated[str | None, Form()] = None,
    file_label: Annotated[str | None, Form(max_length=MAX_FILE_LABEL_LENGTH)] = None,
    tags: Annotated[str | None, Form()] = None,  # JSON-encoded list of strings
) -> ResourceUploadResponse:
    """
    Upload resource metadata and request a presigned upload URL. If detect_type is true, infer resource_type from file_name extension.
    Schedules a background task to verify upload after a timeout. TODO: Upgrade to Celery when Redis is available.
    """
    # Optionally detect resource_type from file_name
    if detect_type:
        ext = file_name.lower().rsplit(".", 1)[-1] if "." in file_name else None
        ext_map = {
            "txt": AttackResourceType.WORD_LIST,
            "dict": AttackResourceType.WORD_LIST,
            "wordlist": AttackResourceType.WORD_LIST,
            "rule": AttackResourceType.RULE_LIST,
            "rules": AttackResourceType.RULE_LIST,
            "mask": AttackResourceType.MASK_LIST,
            "masks": AttackResourceType.MASK_LIST,
            "charset": AttackResourceType.CHARSET,
            "charsets": AttackResourceType.CHARSET,
        }
        if ext and ext in ext_map:
            resource_type_enum = ext_map[ext]
        else:
            raise HTTPException(
                status_code=400,
                detail="Could not detect resource_type from file_name extension.",
            )
    else:
        try:
            resource_type_enum = AttackResourceType(resource_type)
        except ValueError as err:
            raise HTTPException(
                status_code=400, detail="Invalid resource_type"
            ) from err
    # Parse used_for_modes if provided
    used_for_modes_list = (
        [m.strip() for m in used_for_modes.split(",") if m.strip()]
        if used_for_modes
        else None
    )
    # Parse tags if provided (expecting JSON-encoded list)
    import json

    tags_list = None
    if tags:
        try:
            tags_list = json.loads(tags)
            if not isinstance(tags_list, list) or not all(
                isinstance(t, str) for t in tags_list
            ):
                raise ValueError
        except (ValueError, TypeError) as err:
            raise HTTPException(
                status_code=422, detail="tags must be a JSON-encoded list of strings."
            ) from err

    # Create DB record and presigned URL atomically
    try:
        if project_id and not (
            await user_can_access_project_by_id(current_user, project_id, db=db)
        ):
            raise HTTPException(
                status_code=403, detail="Not authorized for this project."
            )
        resource, presigned_url = await create_resource_and_presign_service(
            db=db,
            file_name=file_name,
            resource_type=resource_type_enum,
            project_id=project_id,
            line_format=line_format,
            line_encoding=line_encoding,
            used_for_modes=used_for_modes_list,
            source=source,
            background_tasks=background_tasks,
            file_label=file_label,
            tags=tags_list,
        )
    except RuntimeError as err:
        raise HTTPException(
            status_code=500, detail=f"Failed to create resource: {err}"
        ) from err
    return ResourceUploadResponse(
        resource_id=resource.id,
        presigned_url=presigned_url,
        resource=ResourceUploadMeta(
            file_name=resource.file_name,
            resource_type=resource.resource_type,
        ),
    )


@router.post(
    "/{resource_id}/uploaded",
    summary="Verify resource upload and update metadata",
    description="Client notifies server that file was uploaded. Updates is_uploaded and refreshes size, line count, and checksum.",
)
async def verify_resource_uploaded(
    resource_id: Annotated[UUID, Path(description="Resource ID to verify upload for")],
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ResourceUploadedResponse:
    await _get_resource_if_accessable(resource_id, db, current_user)
    from app.core.services.resource_service import verify_resource_upload_service

    updated = await verify_resource_upload_service(resource_id, db)
    return ResourceUploadedResponse.model_validate(updated, from_attributes=True)


@router.post(
    "/{resource_id}/refresh_metadata",
    summary="Refresh resource metadata (size, line count, checksum)",
    description="Re-fetch file stats from MinIO and update the resource metadata. Returns updated resource metadata.",
)
async def refresh_resource_metadata(
    resource_id: Annotated[
        UUID, Path(description="Resource ID to refresh metadata for")
    ],
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ResourceUploadedResponse:
    _: AttackResourceFile = await _get_resource_if_accessable(
        resource_id, db, current_user
    )
    updated_resource = await refresh_resource_metadata_service(resource_id, db)
    return ResourceUploadedResponse.model_validate(
        updated_resource, from_attributes=True
    )


@router.get(
    "/audit/orphans",
    summary="Audit orphaned resource files in S3/MinIO and DB (admin only)",
    description="Admin tool: Returns orphaned S3 objects (not referenced in DB) and orphaned DB records (no object in storage).",
)
async def audit_orphan_resources(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, list[str]]:
    # Only allow admin users
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required."
        )
    from app.core.services.resource_service import audit_orphan_resources_service

    return await audit_orphan_resources_service(db)


@router.get(
    "/upload",
    summary="Get resource upload form schema",
    description="Return JSON schema and constraints for the resource upload form, including allowed types and limits.",
)
async def get_resource_upload_form() -> ResourceUploadFormSchema:
    """
    Returns the schema and constraints for the resource upload form.
    """
    from app.core.config import settings

    return ResourceUploadFormSchema(
        allowed_resource_types=list(EDITABLE_RESOURCE_TYPES),
        max_file_size_mb=settings.RESOURCE_EDIT_MAX_SIZE_MB,
        max_line_count=settings.RESOURCE_EDIT_MAX_LINES,
        minio_bucket=settings.MINIO_BUCKET,
        minio_endpoint=settings.MINIO_ENDPOINT,
        minio_secure=settings.MINIO_SECURE,
    )


# --- Routes after this point must go last due to the way FastAPI handles route matching ---


@router.get(
    "/{resource_id}",
    summary="Get resource detail (metadata + linking)",
    description="Return resource metadata and all attacks using this resource.",
)
async def get_resource_detail(
    resource_id: Annotated[UUID, Path()],
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ResourceDetailResponse:
    resource_model = await _get_resource_if_accessable(resource_id, db, current_user)
    from app.models.attack import Attack

    attack_models: list[Attack] = []
    if resource_model.resource_type == AttackResourceType.WORD_LIST:
        result = await db.execute(
            select(Attack).where(Attack.word_list_id == resource_id)
        )
        attack_models = list(result.scalars().all())
    attack_basics = [AttackBasic(id=a.id, name=a.name) for a in attack_models]

    return ResourceDetailResponse(
        id=resource_model.id,
        file_name=resource_model.file_name,
        file_label=resource_model.file_label,
        resource_type=resource_model.resource_type,
        line_count=resource_model.line_count,
        byte_size=resource_model.byte_size,
        updated_at=resource_model.updated_at,
        line_format=resource_model.line_format,
        line_encoding=resource_model.line_encoding,
        used_for_modes=[
            m.value if hasattr(m, "value") else str(m)
            for m in resource_model.used_for_modes
        ]
        if resource_model.used_for_modes
        else [],
        source=resource_model.source,
        project_id=resource_model.project_id,
        unrestricted=(resource_model.project_id is None),
        tags=resource_model.tags,
        attacks=attack_basics,
    )


@router.get(
    "/{resource_id}/preview",
    summary="Get a small content preview for a resource",
    description="Return the first few lines of the resource for preview purposes. Enforces project access.",
)
async def get_resource_preview(
    resource_id: Annotated[UUID, Path()],
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ResourcePreviewResponse:
    resource_model = await _get_resource_if_accessable(resource_id, db, current_user)
    max_preview_lines = 10
    preview_lines = []
    preview_error = None
    # Ephemeral/dynamic: use content field
    if resource_model.resource_type in EDITABLE_RESOURCE_TYPES and (
        resource_model.resource_type
        in [
            AttackResourceType.EPHEMERAL_WORD_LIST,
            AttackResourceType.EPHEMERAL_MASK_LIST,
            AttackResourceType.EPHEMERAL_RULE_LIST,
        ]
        or not resource_model.is_uploaded
    ):
        if resource_model.content and "lines" in resource_model.content:
            lines = resource_model.content["lines"]
            if isinstance(lines, list):
                preview_lines = lines[:max_preview_lines]
            else:
                preview_error = "Resource lines are not a list."
        else:
            preview_error = "No preview available for this resource type."
    # File-backed: fetch from MinIO
    elif (
        resource_model.resource_type in EDITABLE_RESOURCE_TYPES
        and resource_model.is_uploaded
    ):
        from app.core.services.resource_service import _read_file_lines_from_storage

        try:
            lines = await _read_file_lines_from_storage(resource_model)
            preview_lines = lines[:max_preview_lines]
        except HTTPException as e:
            preview_error = f"Failed to load preview: {e.detail}"
        except (UnicodeDecodeError, OSError) as e:
            preview_error = f"Failed to load preview: {e}"
    else:
        preview_error = "No preview available for this resource type."
    return ResourcePreviewResponse(
        id=resource_model.id,
        file_name=resource_model.file_name,
        resource_type=resource_model.resource_type,
        line_count=resource_model.line_count,
        byte_size=resource_model.byte_size,
        updated_at=resource_model.updated_at,
        line_format=resource_model.line_format,
        line_encoding=resource_model.line_encoding,
        used_for_modes=[
            m.value if hasattr(m, "value") else str(m)
            for m in resource_model.used_for_modes
        ]
        if resource_model.used_for_modes
        else [],
        source=resource_model.source,
        project_id=resource_model.project_id,
        unrestricted=(resource_model.project_id is None),
        preview_lines=preview_lines,
        preview_error=preview_error,
        max_preview_lines=max_preview_lines,
    )


@router.get(
    "/{resource_id}/edit",
    summary="Get resource metadata for editing",
    description="Return resource metadata for editing (for edit form population).",
)
async def get_resource_edit_metadata(
    resource_id: Annotated[UUID, Path()],
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ResourceDetailResponse:
    resource_model: AttackResourceFile = await _get_resource_if_accessable(
        resource_id, db, current_user
    )
    from app.models.attack import Attack

    attack_models: list[Attack] = []
    if resource_model.resource_type == AttackResourceType.WORD_LIST:
        result = await db.execute(
            select(Attack).where(Attack.word_list_id == resource_id)
        )
        attack_models = list(result.scalars().all())
    attack_basics = [AttackBasic(id=a.id, name=a.name) for a in attack_models]
    return ResourceDetailResponse(
        id=resource_model.id,
        file_name=resource_model.file_name,
        file_label=resource_model.file_label,
        resource_type=resource_model.resource_type,
        line_count=resource_model.line_count,
        byte_size=resource_model.byte_size,
        checksum=resource_model.checksum,
        updated_at=resource_model.updated_at,
        line_format=resource_model.line_format,
        line_encoding=resource_model.line_encoding,
        used_for_modes=[
            m.value if hasattr(m, "value") else str(m)
            for m in resource_model.used_for_modes
        ]
        if resource_model.used_for_modes
        else [],
        source=resource_model.source,
        project_id=resource_model.project_id,
        unrestricted=(resource_model.project_id is None),
        is_uploaded=resource_model.is_uploaded,
        tags=resource_model.tags,
        attacks=attack_basics,
    )


@router.patch(
    "/{resource_id}",
    summary="Update resource metadata",
    description="Update resource metadata fields (file_name, file_label, project_id, source, unrestricted, tags). Returns updated resource.",
)
async def update_resource_metadata(
    resource_id: Annotated[UUID, Path()],
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    patch: ResourceUpdateRequest,
) -> ResourceDetailResponse:
    resource_model = await _get_resource_if_accessable(resource_id, db, current_user)
    # Enforce edit restrictions
    if (
        resource_model.resource_type in EPHEMERAL_RESOURCE_TYPES
        or resource_model.resource_type not in EDITABLE_RESOURCE_TYPES
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Editing not allowed for this resource type.",
        )
    updated = False
    # Update each field if provided
    if patch.file_name:
        resource_model.file_name = patch.file_name
        updated = True
    if patch.file_label:
        resource_model.file_label = patch.file_label
        updated = True
    if patch.project_id:
        resource_model.project_id = patch.project_id
        updated = True
    if patch.source:
        resource_model.source = patch.source
        updated = True
    if patch.unrestricted is not None:  # False is valid
        if patch.unrestricted:
            resource_model.project_id = None
        elif patch.project_id is None and resource_model.project_id is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="project_id required when unrestricted is False.",
            )
        updated = True
    if patch.tags is not None:  # Empty list is valid
        resource_model.tags = patch.tags
        updated = True
    if patch.used_for_modes:
        resource_model.used_for_modes = patch.used_for_modes
        updated = True
    if patch.line_format:
        resource_model.line_format = patch.line_format
        updated = True
    if patch.line_encoding:
        resource_model.line_encoding = patch.line_encoding
        updated = True
    if updated:
        await db.commit()
        await db.refresh(resource_model)
    from app.models.attack import Attack

    attack_models: list[Attack] = []
    if resource_model.resource_type == AttackResourceType.WORD_LIST:
        result = await db.execute(
            select(Attack).where(Attack.word_list_id == resource_id)
        )
        attack_models = list(result.scalars().all())
    attack_basics: list[AttackBasic] = [
        AttackBasic(id=a.id, name=a.name) for a in attack_models
    ]
    return ResourceDetailResponse(
        id=resource_model.id,
        file_name=resource_model.file_name,
        file_label=resource_model.file_label,
        resource_type=resource_model.resource_type,
        line_count=resource_model.line_count,
        byte_size=resource_model.byte_size,
        checksum=resource_model.checksum,
        updated_at=resource_model.updated_at,
        line_format=resource_model.line_format,
        line_encoding=resource_model.line_encoding,
        used_for_modes=[
            m.value if hasattr(m, "value") else str(m)
            for m in resource_model.used_for_modes
        ]
        if resource_model.used_for_modes
        else [],
        source=resource_model.source,
        project_id=resource_model.project_id,
        unrestricted=(resource_model.project_id is None),
        is_uploaded=resource_model.is_uploaded,
        tags=resource_model.tags,
        attacks=attack_basics,
    )


@router.delete(
    "/{resource_id}",
    summary="Remove or disable resource (hard delete)",
    description="Hard delete: remove from DB and S3/MinIO if not linked to any attack. Returns 204 No Content. Returns 409 if linked.",
    status_code=204,
)
async def delete_resource(
    resource_id: Annotated[UUID, Path()],
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    await _get_resource_if_accessable(resource_id, db, current_user)
    await delete_resource_service(resource_id, db)
    # WS_TRIGGER: resource deleted


@router.patch(
    "/{resource_id}/content",
    summary="Update resource content (inline edit)",
    description="Update the content of a resource (file-backed). Only allowed for editable, non-dynamic, non-oversize resources. Triggers metadata refresh.",
    status_code=204,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": "Updated resource content successfully"
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Unauthorized: missing or invalid authentication"
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "Resource not editable or too large for in-browser editing"
        },
        status.HTTP_404_NOT_FOUND: {"description": "Resource not found"},
    },
)
async def update_resource_content(
    resource_id: Annotated[UUID, Path(description="The resource ID to update")],
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    content: Annotated[str, Form(description="The new content to update")],
) -> None:
    await _get_resource_if_accessable(resource_id, db, current_user)
    await update_resource_content_service(resource_id, content, db)


# --- Do not add any routes after this point ---
