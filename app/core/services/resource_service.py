import asyncio
from typing import TYPE_CHECKING, cast
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from minio.error import S3Error
from sqlalchemy import delete, desc, func, or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.authz import user_can_access_project_by_id
from app.core.config import settings
from app.core.exceptions import InvalidAgentTokenError
from app.core.services.storage_service import StorageService, get_storage_service
from app.core.tasks.resource_tasks import verify_upload_and_cleanup
from app.db.session import get_db
from app.models.agent import Agent
from app.models.attack import Attack, AttackMode, AttackState
from app.models.attack_resource_file import AttackResourceFile, AttackResourceType
from app.models.hash_type import HashType
from app.models.hash_upload_task import HashUploadStatus, HashUploadTask
from app.models.project import Project, ProjectUserAssociation
from app.models.upload_error_entry import UploadErrorEntry
from app.models.upload_resource_file import UploadResourceFile
from app.models.user import User, UserRole
from app.schemas.resource import (
    EDITABLE_RESOURCE_TYPES,
    EPHEMERAL_RESOURCE_TYPES,
    ResourceLine,
    ResourceLineValidationError,
    ResourceListItem,
    ResourceListResponse,
    ResourceUpdateRequest,
    UploadErrorEntryListResponse,
    UploadErrorEntryOut,
    UploadProcessingStep,
    UploadStatusOut,
)

from .project_service import ProjectNotFoundError

if TYPE_CHECKING:
    from fastapi import BackgroundTasks


def is_ephemeral_resource_type(resource_type: str) -> bool:
    return resource_type in EPHEMERAL_RESOURCE_TYPES


# --- Resource Line-Oriented Editing (File-Backed Only) ---


async def get_resource_download_url_service(
    resource_id: UUID,  # This has to be a UUID, not an int
    authorization: str,
) -> str:
    # Validate agent token
    if not authorization.startswith("Bearer csa_"):
        raise InvalidAgentTokenError("Invalid or missing agent token")
    token = authorization.removeprefix("Bearer ").strip()
    db_gen = get_db()
    db: AsyncSession = await anext(db_gen)
    try:
        agent = await db.execute(select(Agent).where(Agent.token == token))
        agent_obj = agent.scalar_one_or_none()
        if not agent_obj:
            raise InvalidAgentTokenError("Invalid or missing agent token")
        resource = await get_resource_or_404(resource_id, db)
        # Ephemeral resource: return internal endpoint URL
        if (
            resource.resource_type in EPHEMERAL_RESOURCE_TYPES
            or not resource.is_uploaded
        ):
            url = f"/api/v1/downloads/{resource_id}/ephemeral-download"
            logger.info(
                f"Agent {agent_obj.id} requested ephemeral download for resource {resource_id}"
            )
            return url
        # File-backed: presigned download URL
        storage_service = get_storage_service()
        url = storage_service.generate_presigned_download_url(
            bucket_name=settings.MINIO_BUCKET,
            object_name=str(resource_id),
            expiry=60 * 10,  # 10 minutes
        )
        logger.info(f"Presigned download URL generated for resource {resource_id}")
        return url
    finally:
        await db.aclose()


def is_resource_editable(resource: AttackResourceFile) -> bool:
    max_lines = settings.RESOURCE_EDIT_MAX_LINES
    max_bytes = settings.RESOURCE_EDIT_MAX_SIZE_MB * 1024 * 1024
    if resource.resource_type in EPHEMERAL_RESOURCE_TYPES:
        return False
    if resource.line_count > max_lines or resource.byte_size > max_bytes:
        return False
    return resource.resource_type in {
        AttackResourceType.MASK_LIST,
        AttackResourceType.RULE_LIST,
        AttackResourceType.WORD_LIST,
        AttackResourceType.CHARSET,
    }


async def _read_file_lines_from_storage(resource: AttackResourceFile) -> list[str]:
    """Read lines from MinIO for a file-backed resource."""
    storage_service = get_storage_service()
    bucket = settings.MINIO_BUCKET

    # Download file from MinIO as bytes
    def _download() -> bytes:
        obj = storage_service.client.get_object(bucket, str(resource.id))
        content = obj.read()
        obj.close()
        return content

    try:
        file_bytes = await asyncio.to_thread(_download)
        # Decode using resource.line_encoding
        text = file_bytes.decode(resource.line_encoding or "utf-8")
        # Split into lines
        return text.splitlines()
    except (HTTPException, UnicodeDecodeError, OSError) as e:
        raise HTTPException(
            status_code=400, detail=f"Failed to read file from storage: {e}"
        ) from e
    except Exception as e:
        # Defensive: catch minio.error.S3Error and similar
        if e.__class__.__name__ == "S3Error":
            raise HTTPException(
                status_code=400, detail=f"Failed to read file from storage: {e}"
            ) from e
        raise


async def get_resource_content_service(
    resource_id: UUID, db: AsyncSession
) -> tuple[AttackResourceFile | None, str | None, str | None, int, bool]:
    max_lines = settings.RESOURCE_EDIT_MAX_LINES
    max_bytes = settings.RESOURCE_EDIT_MAX_SIZE_MB * 1024 * 1024
    resource = await get_resource_or_404(resource_id, db)
    editable = is_resource_editable(resource)
    content_str = None
    error_message = None
    status_code = 200
    # Ephemeral/dynamic: use content field
    if resource.resource_type in EPHEMERAL_RESOURCE_TYPES or not resource.is_uploaded:
        if resource.resource_type == AttackResourceType.DYNAMIC_WORD_LIST:
            error_message = "This resource is read-only and cannot be edited inline."
            status_code = 403
        elif resource.line_count > max_lines or resource.byte_size > max_bytes:
            error_message = f"This resource is too large to edit inline (max {max_lines} lines, {max_bytes // 1024 // 1024}MB). Download and edit offline."
            status_code = 403
        elif resource.resource_type not in EDITABLE_RESOURCE_TYPES:
            error_message = "This resource type cannot be edited inline."
            status_code = 403
        else:
            lines = (
                resource.content["lines"]
                if resource.content and "lines" in resource.content
                else []
            )
            if not isinstance(lines, list):
                error_message = "Resource lines are not a list."
                status_code = 400
            else:
                content_str = "\n".join(lines)
    else:
        # File-backed: read from MinIO
        try:
            lines = await _read_file_lines_from_storage(resource)
        except HTTPException as e:
            error_message = str(e.detail)
            status_code = e.status_code
        else:
            if len(lines) > max_lines or resource.byte_size > max_bytes:
                error_message = f"This resource is too large to edit inline (max {max_lines} lines, {max_bytes // 1024 // 1024}MB). Download and edit offline."
                status_code = 403
            else:
                content_str = "\n".join(lines)
    return resource, content_str, error_message, status_code, editable


async def list_wordlists_service(
    db: AsyncSession, q: str | None = None
) -> list[AttackResourceFile]:
    stmt = select(AttackResourceFile).where(
        AttackResourceFile.resource_type == AttackResourceType.WORD_LIST
    )
    if q:
        stmt = stmt.where(AttackResourceFile.file_name.ilike(f"%{q}%"))
    stmt = stmt.order_by(desc(AttackResourceFile.updated_at))
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def list_rulelists_service(
    db: AsyncSession, q: str | None = None
) -> list[AttackResourceFile]:
    stmt = select(AttackResourceFile).where(
        AttackResourceFile.resource_type == AttackResourceType.RULE_LIST
    )
    if q:
        stmt = stmt.where(AttackResourceFile.file_name.ilike(f"%{q}%"))
    stmt = stmt.order_by(desc(AttackResourceFile.updated_at))
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_resource_lines_service(
    resource_id: UUID,
    db: AsyncSession,
    page: int = 1,
    page_size: int = 100,
) -> list[ResourceLine]:
    resource = await get_resource_or_404(resource_id, db)
    if resource.resource_type not in EDITABLE_RESOURCE_TYPES:
        raise HTTPException(status_code=403, detail="Resource type not editable")
    # Ephemeral/dynamic: use content field
    if resource.resource_type in EPHEMERAL_RESOURCE_TYPES or not resource.is_uploaded:
        if not resource.content or "lines" not in resource.content:
            raise HTTPException(
                status_code=400, detail="Resource has no editable lines"
            )
        lines_raw = resource.content["lines"]
        if not isinstance(lines_raw, list):
            raise HTTPException(status_code=400, detail="Resource lines are not a list")
        lines: list[str] = cast("list[str]", lines_raw)
    else:
        # File-backed: read from MinIO
        lines = await _read_file_lines_from_storage(resource)
    start = (page - 1) * page_size
    end = start + page_size
    paged_lines = lines[start:end]
    result = []
    for idx, line in enumerate(paged_lines, start=start):
        valid, error = _validate_line(line, resource.resource_type)
        result.append(
            ResourceLine(
                id=idx,
                index=idx,
                content=line,
                valid=valid,
                error_message=error,
            )
        )
    return result


async def add_resource_line_service(
    resource_id: UUID, db: AsyncSession, line: str
) -> ResourceLine:
    resource = await db.get(AttackResourceFile, resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    if not resource.content or "lines" not in resource.content:
        raise HTTPException(status_code=400, detail="Resource has no editable lines")
    lines = resource.content["lines"]
    if not isinstance(lines, list):
        raise HTTPException(status_code=400, detail="Resource lines are not a list")
    valid, error = _validate_line(line, resource.resource_type)
    if not valid:
        raise HTTPException(
            status_code=422,
            detail=[
                ResourceLineValidationError(
                    line_index=len(lines),
                    content=line,
                    valid=False,
                    message=error or "",
                ).model_dump(mode="json")
            ],
        )
    lines.append(line)
    resource.content["lines"] = list(lines)
    resource.line_count = len(lines)
    resource.byte_size = sum(len(line_str) for line_str in lines)
    await db.commit()
    await db.refresh(resource)
    return ResourceLine(
        id=len(lines) - 1,
        index=len(lines) - 1,
        content=line,
        valid=True,
        error_message=None,
    )


async def update_resource_line_service(
    resource_id: UUID, line_id: int, db: AsyncSession, line: str
) -> ResourceLine:
    resource = await db.get(AttackResourceFile, resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    if not resource.content or "lines" not in resource.content:
        raise HTTPException(status_code=400, detail="Resource has no editable lines")
    lines = resource.content["lines"]
    if not isinstance(lines, list):
        raise HTTPException(status_code=400, detail="Resource lines are not a list")
    if not (0 <= line_id < len(lines)):
        raise HTTPException(status_code=404, detail="Line not found")
    valid, error = _validate_line(line, resource.resource_type)
    if not valid:
        raise HTTPException(
            status_code=422,
            detail=[
                ResourceLineValidationError(
                    line_index=line_id, content=line, valid=False, message=error or ""
                ).model_dump(mode="json")
            ],
        )
    lines[line_id] = line
    resource.content["lines"] = list(lines)
    resource.byte_size = sum(len(line_str) for line_str in lines)
    await db.commit()
    await db.refresh(resource)
    return ResourceLine(
        id=line_id, index=line_id, content=line, valid=True, error_message=None
    )


async def delete_resource_line_service(
    resource_id: UUID, line_id: int, db: AsyncSession
) -> None:
    resource = await db.get(AttackResourceFile, resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    if not resource.content or "lines" not in resource.content:
        raise HTTPException(status_code=400, detail="Resource has no editable lines")
    lines = resource.content["lines"]
    if not isinstance(lines, list):
        raise HTTPException(status_code=400, detail="Resource lines are not a list")
    if not (0 <= line_id < len(lines)):
        raise HTTPException(status_code=404, detail="Line not found")
    lines.pop(line_id)
    resource.content["lines"] = list(lines)
    resource.line_count = len(lines)
    resource.byte_size = sum(len(line_str) for line_str in lines)
    await db.commit()
    await db.refresh(resource)


async def validate_resource_lines_service(
    resource_id: UUID, db: AsyncSession
) -> list[ResourceLineValidationError]:
    resource = await get_resource_or_404(resource_id, db)
    if resource.resource_type not in EDITABLE_RESOURCE_TYPES:
        raise HTTPException(status_code=403, detail="Resource type not editable")
    if not resource.content or "lines" not in resource.content:
        raise HTTPException(status_code=400, detail="Resource has no editable lines")
    lines = resource.content["lines"]
    if not isinstance(lines, list):
        raise HTTPException(status_code=400, detail="Resource lines are not a list")
    errors: list[ResourceLineValidationError] = []
    for idx, line in enumerate(lines):
        valid, error = _validate_line(line, resource.resource_type)
        if not valid:
            errors.append(
                ResourceLineValidationError(
                    line_index=idx,
                    content=line,
                    valid=False,
                    message=error or "Invalid line",
                )
            )
    return errors


# Validation helpers


def _validate_line(
    line: str, resource_type: AttackResourceType
) -> tuple[bool, str | None]:
    # TODO: Implement real validation for mask/rule/charset
    if resource_type == AttackResourceType.MASK_LIST and (not line or " " in line):
        return False, "Invalid mask syntax"
    if resource_type == AttackResourceType.RULE_LIST and line and line.startswith("+"):
        return False, "Unknown rule operator"
    # Add more rules as needed
    return True, None


async def list_resources_service(
    db: AsyncSession,
    resource_type: AttackResourceType | None = None,
    q: str = "",
    page: int = 1,
    page_size: int = 25,
) -> ResourceListResponse:
    stmt = select(AttackResourceFile)
    if resource_type:
        stmt = stmt.where(AttackResourceFile.resource_type == resource_type)
    if q:
        stmt = stmt.where(AttackResourceFile.file_name.ilike(f"%{q}%"))
    stmt = stmt.order_by(desc(AttackResourceFile.updated_at))
    total_count = await db.scalar(select(func.count()).select_from(stmt.subquery()))
    if total_count is None:
        total_count = 0
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    values = list(result.scalars().all())
    return ResourceListResponse(
        items=[
            ResourceListItem(
                id=r.id,
                file_name=r.file_name,
                resource_type=r.resource_type,
                line_count=r.line_count,
                byte_size=r.byte_size,
                updated_at=r.updated_at,
                line_format=r.line_format,
                line_encoding=r.line_encoding,
                used_for_modes=[
                    m.value if hasattr(m, "value") else str(m) for m in r.used_for_modes
                ]
                if r.used_for_modes
                else [],
                source=r.source,
                project_id=r.project_id,
                unrestricted=(r.project_id is None),
            )
            for r in values
        ],
        total=total_count,
        page=page,
        page_size=page_size,
        search=q,
        resource_type=resource_type,
    )


async def create_resource_and_presign_service(
    db: AsyncSession,
    file_name: str,
    resource_type: AttackResourceType,
    project_id: int | None = None,
    line_format: str | None = None,
    line_encoding: str | None = None,
    used_for_modes: list[str] | None = None,
    source: str | None = None,
    background_tasks: BackgroundTasks | None = None,
    file_label: str | None = None,
    tags: list[str] | None = None,
) -> tuple[AttackResourceFile, str]:
    """
    Atomically create an AttackResourceFile DB record and generate a presigned S3 upload URL.
    If any error occurs, ensure no orphaned DB record remains.
    Schedules a background task to verify upload after a timeout. TODO: Upgrade to Celery when Redis is available.
    """
    resource = AttackResourceFile(
        file_name=file_name,
        resource_type=resource_type,
        project_id=project_id,
        guid=uuid4(),
        source=source or "upload",
        line_format=line_format or _default_line_format(resource_type),
        line_encoding=line_encoding or _default_line_encoding(resource_type),
        used_for_modes=used_for_modes or _default_used_for_modes(resource_type),
        download_url="",  # Required, set empty for now
        checksum="",  # Required, set empty for now
        file_label=file_label,
        tags=tags,
    )
    try:
        db.add(resource)
        await db.commit()
        await db.refresh(resource)
    except SQLAlchemyError as err:
        await db.rollback()
        raise RuntimeError(f"Failed to create resource DB record: {err}") from err
    else:
        # Generate real presigned upload URL
        storage_service = get_storage_service()
        bucket_name = settings.MINIO_BUCKET
        await storage_service.ensure_bucket_exists(bucket_name)
        presigned_url = storage_service.generate_presigned_upload_url(
            bucket_name, str(resource.id)
        )
        # Schedule background verification task if provided
        if background_tasks is not None:
            timeout_seconds = getattr(settings, "RESOURCE_UPLOAD_TIMEOUT_SECONDS", 900)
            background_tasks.add_task(
                verify_upload_and_cleanup, str(resource.id), db, timeout_seconds
            )
        return resource, presigned_url


def _default_line_format(resource_type: AttackResourceType) -> str:
    if resource_type == AttackResourceType.MASK_LIST:
        return "mask"
    if resource_type == AttackResourceType.RULE_LIST:
        return "rule"
    if resource_type == AttackResourceType.CHARSET:
        return "charset"
    return "freeform"


def _default_line_encoding(resource_type: AttackResourceType) -> str:
    if resource_type in {
        AttackResourceType.MASK_LIST,
        AttackResourceType.RULE_LIST,
        AttackResourceType.CHARSET,
    }:
        return "ascii"
    return "utf-8"


def _default_used_for_modes(resource_type: AttackResourceType) -> list[str]:
    if resource_type == AttackResourceType.MASK_LIST:
        return ["mask"]
    if resource_type == AttackResourceType.RULE_LIST:
        return ["dictionary", "hybrid_dict_mask"]
    if resource_type == AttackResourceType.WORD_LIST:
        return ["dictionary", "hybrid_dict_mask"]
    if resource_type == AttackResourceType.CHARSET:
        return ["brute_force"]
    return []


async def get_resource_or_404(
    resource_id: UUID, db: AsyncSession
) -> AttackResourceFile:
    resource = await db.get(AttackResourceFile, resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    return resource


async def check_resource_editable(resource: AttackResourceFile) -> None:
    max_lines = settings.RESOURCE_EDIT_MAX_LINES
    max_bytes = settings.RESOURCE_EDIT_MAX_SIZE_MB * 1024 * 1024
    if resource.resource_type == AttackResourceType.DYNAMIC_WORD_LIST:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Editing not allowed for dynamic word lists.",
        )
    if resource.line_count > max_lines or resource.byte_size > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Resource too large for in-browser editing.",
        )
    if resource.resource_type not in {
        AttackResourceType.MASK_LIST,
        AttackResourceType.RULE_LIST,
        AttackResourceType.WORD_LIST,
        AttackResourceType.CHARSET,
    }:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Resource type not editable."
        )


async def check_project_access(
    resource: AttackResourceFile,
    current_user: User,
    db: AsyncSession,
) -> None:
    if not resource.project_id:
        return
    if not await user_can_access_project_by_id(
        current_user, resource.project_id, db=db
    ):
        raise HTTPException(status_code=403, detail="Not authorized for this project.")


# --- Orphan File Audit ---

from loguru import logger
from minio.error import MinioException


async def audit_orphan_resources_service(db: AsyncSession) -> dict[str, list[str]]:
    """
    Audit MinIO/S3 for orphaned resource files (objects not referenced in DB) and DB records with no object in storage.
    Returns a dict with two lists: orphaned_objects and orphaned_db_records.
    """
    storage_service: StorageService = get_storage_service()
    bucket_name = settings.MINIO_BUCKET

    # 1. List all objects in the bucket
    s3_objects = set()
    try:
        await storage_service.ensure_bucket_exists(
            bucket_name
        )  # Ensure bucket exists before listing
        async for obj_key in storage_service.list_objects(bucket_name):
            s3_objects.add(obj_key)
    except ConnectionError as e:
        logger.error(f"Could not list objects from S3 for orphan audit: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not connect to S3 storage: {e}",
        ) from e

    # 2. List all AttackResourceFile records and their expected object keys
    result = await db.execute(select(AttackResourceFile))
    db_resources = result.scalars().all()
    db_keys = set()
    db_key_to_id = {}
    for r in db_resources:
        # Assume object key is based on resource.id (UUID) or file_name
        # This must match the upload logic used in presign/put
        key = f"{r.id}"
        db_keys.add(key)
        db_key_to_id[key] = str(r.id)

    # 3. Orphaned objects: in S3 but not in DB
    orphaned_objects = [k for k in s3_objects if k not in db_keys]
    # 4. Orphaned DB records: in DB but not in S3
    orphaned_db_records = [db_key_to_id[k] for k in db_keys if k not in s3_objects]

    logger.info(f"Orphaned S3 objects: {orphaned_objects}")
    logger.info(f"Orphaned DB records: {orphaned_db_records}")
    return {
        "orphaned_objects": orphaned_objects,
        "orphaned_db_records": orphaned_db_records,
    }


async def verify_resource_upload_service(
    resource_id: UUID, db: AsyncSession
) -> AttackResourceFile:
    resource = await get_resource_or_404(resource_id, db)
    if resource.is_uploaded:
        raise HTTPException(
            status_code=409, detail="Resource already marked as uploaded."
        )
    storage_service = get_storage_service()
    bucket = settings.MINIO_BUCKET
    # Check file exists in MinIO
    try:
        stats = await storage_service.get_file_stats(bucket, str(resource_id))
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"File not found in storage: {e}"
        ) from e
    # Update resource metadata
    resource.byte_size = int(stats["byte_size"])
    resource.line_count = int(stats["line_count"])
    resource.checksum = str(stats["checksum"])
    resource.is_uploaded = True
    await db.commit()
    await db.refresh(resource)
    return resource


async def refresh_resource_metadata_service(
    resource_id: UUID, db: AsyncSession
) -> AttackResourceFile:
    resource = await get_resource_or_404(resource_id, db)
    storage_service = get_storage_service()
    bucket = settings.MINIO_BUCKET
    # Check file exists in MinIO and fetch stats
    try:
        stats = await storage_service.get_file_stats(bucket, str(resource_id))
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"File not found in storage: {e}"
        ) from e
    # Update resource metadata
    resource.byte_size = int(stats["byte_size"])
    resource.line_count = int(stats["line_count"])
    resource.checksum = str(stats["checksum"])
    await db.commit()
    await db.refresh(resource)
    return resource


async def update_resource_metadata_service(
    resource: AttackResourceFile,
    patch: ResourceUpdateRequest,
    db: AsyncSession,
) -> AttackResourceFile:
    updated = False
    if patch.file_name is not None:
        resource.file_name = patch.file_name
        updated = True
    if patch.file_label is not None:
        resource.file_label = patch.file_label
        updated = True
    if patch.project_id is not None:
        resource.project_id = patch.project_id
        updated = True
    if patch.source is not None:
        resource.source = patch.source
        updated = True
    if patch.unrestricted is not None:
        if patch.unrestricted:
            resource.project_id = None
        updated = True
    if patch.tags is not None:
        resource.tags = patch.tags
        updated = True
    if patch.used_for_modes is not None:
        try:
            resource.used_for_modes = [AttackMode(m) for m in patch.used_for_modes]
        except ValueError as err:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid used_for_modes value.",
            ) from err
        updated = True
    if patch.line_format is not None:
        resource.line_format = patch.line_format
        updated = True
    if patch.line_encoding is not None:
        resource.line_encoding = patch.line_encoding
        updated = True
    if updated:
        await db.commit()
        await db.refresh(resource)
    return resource


async def delete_resource_service(resource_id: UUID, db: AsyncSession) -> None:
    """
    Hard delete a resource if not linked to any attack. If linked, raise 409 Conflict.
    Atomically delete from DB and MinIO/S3. Log all actions.
    """
    resource: AttackResourceFile = await get_resource_or_404(resource_id, db)
    # Forbid hard delete of forbidden resource types
    if (
        resource.resource_type in EPHEMERAL_RESOURCE_TYPES
        or resource.resource_type == AttackResourceType.DYNAMIC_WORD_LIST
    ):
        logger.warning(
            f"Attempted to delete forbidden resource type: {resource.resource_type}"
        )
        raise HTTPException(
            status_code=403, detail="This resource type cannot be deleted."
        )
    # Check for attack linkage (word_list_id, mask_list_id, left_rule)
    linked_attacks: list[Attack] = []
    # Check word_list_id
    result = await db.execute(select(Attack).where(Attack.word_list_id == resource_id))
    linked_attacks.extend(result.scalars().all())
    # Check mask_list_id if present in Attack model
    if hasattr(Attack, "__table__") and "mask_list_id" in Attack.__table__.columns:
        result = await db.execute(
            select(Attack).where(Attack.__table__.c.mask_list_id == resource_id)
        )
        linked_attacks.extend(result.scalars().all())
    # Check left_rule (for rule_list linkage by UUID string)
    result = await db.execute(
        select(Attack).where(Attack.left_rule == str(resource.guid))
    )
    linked_attacks.extend(result.scalars().all())
    if linked_attacks:
        logger.warning(
            f"Resource {resource_id} is linked to {len(linked_attacks)} attack(s), cannot delete."
        )
        raise HTTPException(
            status_code=409,
            detail="Resource is linked to one or more attacks and cannot be deleted.",
        )
    # Delete from MinIO/S3 if uploaded
    if resource.is_uploaded and resource.download_url:
        storage_service = get_storage_service()
        bucket = settings.MINIO_BUCKET
        try:
            await storage_service.ensure_bucket_exists(bucket)
            await asyncio.to_thread(
                storage_service.client.remove_object, bucket, str(resource_id)
            )
            logger.info(f"Deleted resource {resource_id} from MinIO bucket {bucket}.")
        except MinioException as e:
            logger.error(f"Failed to delete resource {resource_id} from MinIO: {e}")
            raise HTTPException(
                status_code=500, detail=f"Failed to delete resource from storage: {e}"
            ) from e
    # Delete from DB
    await db.delete(resource)
    await db.commit()
    logger.info(f"Resource {resource_id} deleted from DB.")


async def update_resource_content_service(
    resource_id: UUID,
    new_content: str,
    db: AsyncSession,
) -> AttackResourceFile:
    """
    Update the content of a resource for file-backed: overwrite in MinIO, refresh metadata. Returns an error if the resource is ephemeral.
    """
    resource = await get_resource_or_404(resource_id, db)
    if not is_resource_editable(resource):
        raise HTTPException(status_code=403, detail="Resource not editable.")

    lines = new_content.splitlines()
    line_count = len(lines)
    byte_size = len(new_content.encode(resource.line_encoding or "utf-8"))

    # Overwrite in MinIO
    storage_service = get_storage_service()
    bucket = settings.MINIO_BUCKET
    await storage_service.ensure_bucket_exists(bucket)
    # Write new content to MinIO
    import hashlib
    import io

    encoded = new_content.encode(resource.line_encoding or "utf-8")
    await asyncio.to_thread(
        storage_service.client.put_object,
        bucket,
        str(resource_id),
        io.BytesIO(encoded),
        len(encoded),
        content_type="text/plain",
    )
    # Refresh metadata (line count, byte size, checksum)
    sha256 = hashlib.sha256(encoded).hexdigest()
    resource.line_count = line_count
    resource.byte_size = byte_size
    resource.checksum = sha256
    resource.is_uploaded = True
    await db.commit()
    await db.refresh(resource)
    return resource


async def list_resources_for_modal_service(
    db: AsyncSession,
    current_user: User,
    resource_type: AttackResourceType | None = None,
    q: str | None = None,
) -> list[AttackResourceFile]:
    stmt = select(AttackResourceFile).where(
        ~AttackResourceFile.resource_type.in_(EPHEMERAL_RESOURCE_TYPES)
    )
    if resource_type:
        stmt = stmt.where(AttackResourceFile.resource_type == resource_type)
    if q:
        stmt = stmt.where(AttackResourceFile.file_name.ilike(f"%{q}%"))
    # Admins see all, others see only unrestricted or project-linked
    if not (current_user.is_superuser or current_user.role == UserRole.ADMIN):
        allowed_project_ids = [
            a.project_id for a in getattr(current_user, "project_associations", [])
        ]
        stmt = stmt.where(
            or_(
                AttackResourceFile.project_id.is_(None),
                AttackResourceFile.project_id.in_(allowed_project_ids),
            )
        )
    stmt = stmt.order_by(desc(AttackResourceFile.updated_at))
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_upload_resource_and_presign_service(
    db: AsyncSession,
    file_name: str,
    project_id: int,
    file_label: str | None,
    user: User,
) -> tuple[UploadResourceFile, str]:
    if not user.is_superuser and user.role != UserRole.ADMIN:
        try:
            if not await user_can_access_project_by_id(user, project_id, db=db):
                raise HTTPException(
                    status_code=403, detail="Not authorized for this project."
                )
        except ProjectNotFoundError as e:
            raise HTTPException(status_code=404, detail="Project not found.") from e
    resource = UploadResourceFile(
        file_name=file_name,
        project_id=project_id,
        guid=uuid4(),
        download_url="",
        checksum="",
        source="upload",
        line_count=0,
        byte_size=0,
        is_uploaded=False,
        file_label=file_label,
    )
    try:
        db.add(resource)
        await db.commit()
        await db.refresh(resource)
    except Exception as err:
        await db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to create upload resource: {err}"
        ) from err
    storage_service = get_storage_service()
    bucket_name = settings.MINIO_BUCKET
    await storage_service.ensure_bucket_exists(bucket_name)
    presigned_url = storage_service.generate_presigned_upload_url(
        bucket_name, str(resource.id)
    )
    return resource, presigned_url


async def create_upload_resource_and_task_service(
    db: AsyncSession,
    file_name: str,
    project_id: int,
    file_label: str | None,
    user: User,
) -> tuple[UploadResourceFile, str, HashUploadTask]:
    # Create UploadResourceFile
    resource, presigned_url = await create_upload_resource_and_presign_service(
        db=db,
        file_name=file_name,
        project_id=project_id,
        file_label=file_label,
        user=user,
    )
    # Create HashUploadTask linked to this resource

    task = HashUploadTask(
        user_id=user.id,
        filename=file_name,
        status=HashUploadStatus.PENDING,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    # Optionally: add a field to UploadResourceFile to link to task (not in model yet)
    return resource, presigned_url, task


async def create_upload_resource_and_task_for_text_service(
    db: AsyncSession,
    text_content: str,
    file_name: str,
    project_id: int,
    file_label: str | None,
    user: User,
    background_tasks: BackgroundTasks | None = None,
) -> tuple[UploadResourceFile, HashUploadTask]:
    """Create an UploadResourceFile for text content and associated HashUploadTask."""
    import hashlib

    if not user.is_superuser and user.role != UserRole.ADMIN:
        try:
            if not await user_can_access_project_by_id(user, project_id, db=db):
                raise HTTPException(
                    status_code=403, detail="Not authorized for this project."
                )
        except ProjectNotFoundError as e:
            raise HTTPException(status_code=404, detail="Project not found.") from e

    # Calculate content metadata following ephemeral resource patterns
    lines = text_content.splitlines()
    line_count = len(lines)
    encoded_content = text_content.encode("utf-8")
    byte_size = len(encoded_content)
    checksum = hashlib.sha256(encoded_content).hexdigest()

    # Create UploadResourceFile with content stored directly (ephemeral pattern)
    resource = UploadResourceFile(
        file_name=file_name,
        project_id=project_id,
        guid=uuid4(),
        download_url="",  # Not used for text blobs
        checksum=checksum,
        source="text_blob",
        line_count=line_count,
        byte_size=byte_size,
        is_uploaded=True,  # Mark as uploaded since content is stored directly
        file_label=file_label,
        content={"lines": lines, "raw_text": text_content},
    )

    try:
        db.add(resource)
        await db.commit()
        await db.refresh(resource)
    except Exception as err:
        await db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to create upload resource: {err}"
        ) from err

    # Create HashUploadTask linked to this resource
    task = HashUploadTask(
        user_id=user.id,
        filename=file_name,
        status=HashUploadStatus.PENDING,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)

    # Trigger background processing for text blobs
    # Note: In tests, this background task may not run due to session manager issues
    # Tests should manually call process_uploaded_hash_file if needed
    if background_tasks:
        from app.core.tasks.crackable_uploads_tasks import process_uploaded_hash_file
        from app.db.session import sessionmanager

        async def process_task() -> None:
            try:
                async with sessionmanager.session() as db_session:
                    await process_uploaded_hash_file(task.id, db_session)
            except RuntimeError as e:
                # Session manager not initialized (likely in test context)
                logger.warning(f"Background task failed: {e}")

        background_tasks.add_task(process_task)

    return resource, task


def _determine_step_status(
    task_status: str, has_condition: bool, current_step_name: str
) -> tuple[str, str | None]:
    """Helper to determine step status and current step."""
    if has_condition:
        return "completed", None
    if task_status == "failed":
        return "failed", None
    if task_status in ["running", "completed", "partial_failure"]:
        return "running", current_step_name
    return "pending", None


def _create_processing_step(
    step_name: str,
    status: str,
    task: HashUploadTask,
    error_message: str | None = None,
) -> UploadProcessingStep:
    """Helper to create a processing step."""
    started_at = None
    finished_at = None
    progress = 0

    if status != "pending" and task.started_at:
        started_at = task.started_at.isoformat()

    if status in ["completed", "failed"] and task.finished_at:
        finished_at = task.finished_at.isoformat()

    if status == "completed":
        progress = 100
    elif status == "running":
        progress = 50

    return UploadProcessingStep(
        step_name=step_name,
        status=status,
        started_at=started_at,
        finished_at=finished_at,
        error_message=error_message,
        progress_percentage=progress,
    )


def _build_processing_steps(
    task: HashUploadTask, resource: UploadResourceFile, hash_type_id: int | None
) -> tuple[list[UploadProcessingStep], str | None]:
    """Build all processing steps and determine current step."""
    processing_steps = []
    current_step = None
    has_raw_hashes = task.raw_hashes and len(task.raw_hashes) > 0

    # Step 1: File Upload
    upload_status = "completed" if resource.is_uploaded else "pending"
    processing_steps.append(_create_processing_step("file_upload", upload_status, task))

    # Step 2: Hash Extraction
    extraction_status, step = _determine_step_status(
        task.status, has_raw_hashes, "hash_extraction"
    )
    if step:
        current_step = step
    processing_steps.append(
        _create_processing_step(
            "hash_extraction",
            extraction_status,
            task,
            "Hash extraction failed" if extraction_status == "failed" else None,
        )
    )

    # Step 3: Hash Type Detection
    detection_status, step = _determine_step_status(
        task.status, bool(has_raw_hashes and hash_type_id), "hash_type_detection"
    )
    if step:
        current_step = step
    processing_steps.append(
        _create_processing_step(
            "hash_type_detection",
            detection_status,
            task,
            "Hash type detection failed" if detection_status == "failed" else None,
        )
    )

    # Step 4: Campaign Creation
    campaign_status, step = _determine_step_status(
        task.status, bool(task.campaign_id), "campaign_creation"
    )
    if step:
        current_step = step
    processing_steps.append(
        _create_processing_step(
            "campaign_creation",
            campaign_status,
            task,
            "Campaign creation failed" if campaign_status == "failed" else None,
        )
    )

    # Step 5: Hash List Creation
    hashlist_status, step = _determine_step_status(
        task.status, bool(task.hash_list_id), "hash_list_creation"
    )
    if step:
        current_step = step
    processing_steps.append(
        _create_processing_step(
            "hash_list_creation",
            hashlist_status,
            task,
            "Hash list creation failed" if hashlist_status == "failed" else None,
        )
    )

    return processing_steps, current_step


async def get_upload_status_service(
    db: AsyncSession,
    current_user: User,
    upload_id: int,
) -> UploadStatusOut:
    task = (
        await db.execute(
            select(HashUploadTask)
            .options(selectinload(HashUploadTask.raw_hashes))
            .where(HashUploadTask.id == upload_id)
        )
    ).scalar_one_or_none()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Upload task not found"
        )
    resource = (
        await db.execute(
            select(UploadResourceFile).where(
                UploadResourceFile.file_name == task.filename
            )
        )
    ).scalar_one_or_none()
    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload resource file not found",
        )
    project = (
        await db.execute(select(Project).where(Project.id == resource.project_id))
    ).scalar_one_or_none()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    assoc_result = await db.execute(
        select(ProjectUserAssociation).where(
            ProjectUserAssociation.project_id == project.id,
            ProjectUserAssociation.user_id == current_user.id,
        )
    )
    assoc = assoc_result.scalar_one_or_none()
    if not assoc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized for this project.",
        )

    # Build preview from raw hashes
    preview = [rh.hash for rh in (task.raw_hashes or [])][:5]
    hash_type_id = task.raw_hashes[0].hash_type_id if task.raw_hashes else None
    hash_type = None
    if hash_type_id:
        ht = await db.get(HashType, hash_type_id)
        hash_type = ht.name if ht else None

    # Determine validation state
    if task.status == "completed" and task.error_count == 0:
        validation_state = "valid"
    elif task.status == "failed":
        validation_state = "invalid"
    elif task.error_count > 0:
        validation_state = "partial"
    else:
        validation_state = "pending"

    # Build detailed processing steps
    processing_steps, current_step = _build_processing_steps(
        task, resource, hash_type_id
    )

    # Calculate overall progress
    completed_steps = sum(1 for step in processing_steps if step.status == "completed")
    total_steps = len(processing_steps)
    overall_progress = (
        int((completed_steps / total_steps) * 100) if total_steps > 0 else 0
    )

    # If task is completed, ensure 100% progress
    if task.status in ["completed", "partial_failure"]:
        overall_progress = 100

    # Count total hashes
    total_hashes_found = len(task.raw_hashes) if task.raw_hashes else None
    total_hashes_parsed = None
    if task.hash_list_id and total_hashes_found is not None:
        # For now, assume all found hashes were parsed successfully if we have a hash list
        # In a more sophisticated implementation, we could track this separately
        total_hashes_parsed = total_hashes_found - task.error_count

    return UploadStatusOut(
        status=task.status,
        started_at=task.started_at.isoformat() if task.started_at else None,
        finished_at=task.finished_at.isoformat() if task.finished_at else None,
        error_count=task.error_count,
        hash_type=hash_type,
        hash_type_id=hash_type_id,
        preview=preview,
        validation_state=validation_state,
        upload_resource_file_id=str(resource.id),
        upload_task_id=task.id,
        processing_steps=processing_steps,
        current_step=current_step,
        total_hashes_found=total_hashes_found,
        total_hashes_parsed=total_hashes_parsed,
        campaign_id=task.campaign_id,
        hash_list_id=task.hash_list_id,
        overall_progress_percentage=overall_progress,
    )


async def get_upload_errors_service(
    db: AsyncSession,
    current_user: User,
    upload_id: int,
    page: int = 1,
    page_size: int = 20,
) -> UploadErrorEntryListResponse:
    # Load the upload task
    task = (
        await db.execute(select(HashUploadTask).where(HashUploadTask.id == upload_id))
    ).scalar_one_or_none()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Upload task not found"
        )
    # Find the resource file to get project_id
    resource = (
        await db.execute(
            select(UploadResourceFile).where(
                UploadResourceFile.file_name == task.filename
            )
        )
    ).scalar_one_or_none()
    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload resource file not found",
        )
    project = (
        await db.execute(select(Project).where(Project.id == resource.project_id))
    ).scalar_one_or_none()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    assoc_result = await db.execute(
        select(ProjectUserAssociation).where(
            ProjectUserAssociation.project_id == project.id,
            ProjectUserAssociation.user_id == current_user.id,
        )
    )
    assoc = assoc_result.scalar_one_or_none()
    if not assoc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized for this project.",
        )
    # Paginate errors
    q = (
        select(UploadErrorEntry)
        .where(UploadErrorEntry.upload_id == upload_id)
        .order_by(UploadErrorEntry.line_number)
    )
    total = (await db.execute(q)).scalars().all()
    total_count = len(total)
    items = total[(page - 1) * page_size : page * page_size]
    items_out = [
        UploadErrorEntryOut.model_validate(e, from_attributes=True) for e in items
    ]
    return UploadErrorEntryListResponse(
        items=items_out,
        total=total_count,
        page=page,
        page_size=page_size,
        search=None,
    )


async def launch_campaign_service(
    db: AsyncSession,
    current_user: User,
    upload_id: int,
) -> dict[str, object]:
    """
    Launch campaign by creating default attacks and making it available.

    Args:
        db: Database session
        current_user: Current authenticated user
        upload_id: Upload task ID

    Returns:
        Dictionary with success message and campaign/hash list IDs

    Raises:
        HTTPException: If upload task not found, not authorized, or task not completed successfully
    """
    from app.core.logging import logger
    from app.models.campaign import Campaign
    from app.models.hash_list import HashList

    # Load the upload task
    task = (
        await db.execute(select(HashUploadTask).where(HashUploadTask.id == upload_id))
    ).scalar_one_or_none()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Upload task not found"
        )

    # Check task is completed successfully
    if task.status not in [
        HashUploadStatus.COMPLETED,
        HashUploadStatus.PARTIAL_FAILURE,
    ]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot launch campaign for upload with status: {task.status}",
        )

    # Verify campaign and hash list exist
    if not task.campaign_id or not task.hash_list_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Campaign or hash list not created yet",
        )

    # Find the resource file to get project_id for authorization
    resource = (
        await db.execute(
            select(UploadResourceFile).where(
                UploadResourceFile.file_name == task.filename
            )
        )
    ).scalar_one_or_none()
    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload resource file not found",
        )

    # Check user authorization for the project
    project = (
        await db.execute(select(Project).where(Project.id == resource.project_id))
    ).scalar_one_or_none()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    assoc_result = await db.execute(
        select(ProjectUserAssociation).where(
            ProjectUserAssociation.project_id == project.id,
            ProjectUserAssociation.user_id == current_user.id,
        )
    )
    assoc = assoc_result.scalar_one_or_none()
    if not assoc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized for this project.",
        )

    # Load campaign and hash list
    campaign = await db.get(Campaign, task.campaign_id)
    hash_list = await db.get(HashList, task.hash_list_id)

    if not campaign or not hash_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign or hash list not found",
        )

    # Check if already launched (not unavailable)
    if not campaign.is_unavailable and not hash_list.is_unavailable:
        logger.info(f"Campaign {campaign.id} already launched for upload {upload_id}")
        return {
            "message": "Campaign already launched",
            "campaign_id": campaign.id,
            "hash_list_id": hash_list.id,
        }

    # Create default dictionary attack if none exist
    existing_attacks = await db.execute(
        select(Attack).where(Attack.campaign_id == campaign.id)
    )
    attack_count = len(list(existing_attacks.scalars().all()))

    if attack_count == 0:
        # Create a basic dictionary attack with a common wordlist
        # Try to find a common wordlist resource
        common_wordlist = (
            await db.execute(
                select(AttackResourceFile)
                .where(AttackResourceFile.resource_type == AttackResourceType.WORD_LIST)
                .where(
                    or_(
                        AttackResourceFile.project_id == project.id,
                        AttackResourceFile.project_id.is_(None),  # Unrestricted
                    )
                )
                .where(AttackResourceFile.is_uploaded)
                .order_by(
                    AttackResourceFile.line_count.desc()
                )  # Prefer larger wordlists
                .limit(1)
            )
        ).scalar_one_or_none()

        # Create the default attack
        default_attack = Attack(
            name="Default Dictionary Attack",
            description="Automatically generated dictionary attack for uploaded hashes",
            attack_mode=AttackMode.DICTIONARY,
            campaign_id=campaign.id,
            hash_list_id=hash_list.id,
            hash_list_url="",  # Not used for campaign-based attacks
            hash_list_checksum="",  # Not used for campaign-based attacks
            word_list_id=common_wordlist.id if common_wordlist else None,
            state=AttackState.PENDING,
            position=0,
            priority=1,
        )
        db.add(default_attack)

        logger.info(f"Created default dictionary attack for campaign {campaign.id}")

    # Mark campaign and hash list as available
    campaign.is_unavailable = False
    hash_list.is_unavailable = False

    # Commit changes
    await db.commit()

    logger.info(f"Campaign {campaign.id} launched successfully for upload {upload_id}")

    return {
        "message": "Campaign launched successfully",
        "campaign_id": campaign.id,
        "hash_list_id": hash_list.id,
    }


async def delete_upload_service(
    db: AsyncSession,
    current_user: User,
    upload_id: int,
) -> None:
    """
    Delete an upload task and all associated resources.

    This includes:
    - The HashUploadTask
    - The associated UploadResourceFile (and S3 object if uploaded)
    - All RawHash records
    - All UploadErrorEntry records
    - The Campaign and HashList if they were created but not launched

    Args:
        db: Database session
        current_user: Current authenticated user
        upload_id: ID of the upload task to delete

    Raises:
        HTTPException: If task not found, access denied, or task cannot be deleted
    """
    from app.models.campaign import Campaign
    from app.models.hash_list import HashList

    # Load the upload task with relationships
    task = (
        await db.execute(
            select(HashUploadTask)
            .options(
                selectinload(HashUploadTask.raw_hashes),
                selectinload(HashUploadTask.errors),
            )
            .where(HashUploadTask.id == upload_id)
        )
    ).scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Upload task not found"
        )

    # Find the associated upload resource file
    resource = (
        await db.execute(
            select(UploadResourceFile).where(
                UploadResourceFile.file_name == task.filename
            )
        )
    ).scalar_one_or_none()

    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload resource file not found",
        )

    # Check project access
    if resource.project_id:
        project = await db.get(Project, resource.project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
            )

        # Verify user has access to the project
        if not current_user.is_superuser and current_user.role != UserRole.ADMIN:
            assoc = (
                await db.execute(
                    select(ProjectUserAssociation).where(
                        ProjectUserAssociation.project_id == resource.project_id,
                        ProjectUserAssociation.user_id == current_user.id,
                    )
                )
            ).scalar_one_or_none()

            if not assoc:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized for this project.",
                )

    # Prevent deletion if campaign/hash list are available (i.e., launched)
    if task.campaign_id:
        campaign = await db.get(Campaign, task.campaign_id)
        if campaign and not campaign.is_unavailable:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot delete upload - campaign has been launched and is in use",
            )

    if task.hash_list_id:
        hash_list = await db.get(HashList, task.hash_list_id)
        if hash_list and not hash_list.is_unavailable:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot delete upload - hash list has been launched and is in use",
            )

    logger.info(f"Deleting upload task {upload_id} and associated resources")

    # Store references to campaign and hash list before clearing foreign keys
    campaign = None
    hash_list = None

    if task.campaign_id:
        campaign = await db.get(Campaign, task.campaign_id)
        task.campaign_id = None  # Clear foreign key reference

    if task.hash_list_id:
        hash_list = await db.get(HashList, task.hash_list_id)
        task.hash_list_id = None  # Clear foreign key reference

    # Commit the foreign key clearing first
    await db.commit()

    # Delete raw hashes (should cascade, but being explicit)
    for raw_hash in task.raw_hashes or []:
        await db.delete(raw_hash)

    # Delete error entries (should cascade, but being explicit)
    for error_entry in task.errors or []:
        await db.delete(error_entry)

    # Delete the UploadResourceFile and its S3 object
    if resource.is_uploaded and resource.download_url:
        storage_service = get_storage_service()
        bucket = settings.MINIO_BUCKET
        try:
            await storage_service.ensure_bucket_exists(bucket)
            await asyncio.to_thread(
                storage_service.client.remove_object, bucket, str(resource.id)
            )
            logger.info(
                f"Deleted upload resource {resource.id} from MinIO bucket {bucket}"
            )
        except S3Error as e:
            if "NoSuchKey" in str(e) or "not found" in str(e).lower():
                # Object doesn't exist in storage, that's fine
                logger.info(
                    f"Upload resource {resource.id} not found in MinIO (already deleted or never uploaded)"
                )
            else:
                raise
        except OSError as e:
            logger.error(
                f"Failed to delete upload resource {resource.id} from MinIO: {e}"
            )
            # Continue with database cleanup even if S3 cleanup fails

    await db.delete(resource)
    logger.info(f"Deleted upload resource file {resource.id}")

    # Delete the upload task (now has no foreign key dependencies)
    await db.delete(task)
    logger.info(f"Deleted upload task {upload_id}")

    # Finally, delete the Campaign and HashList if they were created but not launched
    if campaign and campaign.is_unavailable:
        # Delete any attacks associated with this campaign
        attacks = (
            (await db.execute(select(Attack).where(Attack.campaign_id == campaign.id)))
            .scalars()
            .all()
        )

        for attack in attacks:
            await db.delete(attack)

        await db.delete(campaign)
        logger.info(f"Deleted unavailable campaign {campaign.id}")

    if hash_list and hash_list.is_unavailable:
        # Delete any hash items associated with this hash list
        from app.models.hash_list import hash_list_items

        # First delete the association records
        await db.execute(
            delete(hash_list_items).where(
                hash_list_items.c.hash_list_id == hash_list.id
            )
        )

        await db.delete(hash_list)
        logger.info(f"Deleted unavailable hash list {hash_list.id}")

    await db.commit()
    logger.info(f"Successfully deleted upload {upload_id} and all associated resources")


async def cleanup_stale_resource(
    resource: AttackResourceFile, db: AsyncSession
) -> bool:
    """
    Clean up a single stale pending resource.

    Deletes the resource from MinIO storage (if exists) and the database.
    Uses structured logging for observability.

    Args:
        resource: The AttackResourceFile to clean up
        db: Database session (should already have the resource locked)

    Returns:
        True if cleanup was successful, False if an error occurred
    """
    from datetime import UTC, datetime

    resource_id = str(resource.id)
    age_hours = (datetime.now(UTC) - resource.created_at).total_seconds() / 3600

    try:
        storage_service = get_storage_service()
        bucket = settings.MINIO_BUCKET

        # Check if object exists in MinIO and delete if so
        try:
            await asyncio.to_thread(
                storage_service.client.stat_object, bucket, resource_id
            )
            # Object exists, delete it
            await asyncio.to_thread(
                storage_service.client.remove_object, bucket, resource_id
            )
            logger.bind(
                resource_id=resource_id,
                age_hours=round(age_hours, 2),
                project_id=resource.project_id,
                storage_deleted=True,
            ).info("Deleted stale resource from MinIO storage")
        except S3Error as e:
            if "NoSuchKey" in str(e) or "not found" in str(e).lower():
                # Object doesn't exist, that's fine
                logger.bind(
                    resource_id=resource_id,
                    age_hours=round(age_hours, 2),
                    project_id=resource.project_id,
                    storage_deleted=False,
                ).debug(
                    "Stale resource not found in MinIO (already deleted or never uploaded)"
                )
            else:
                raise

        # Delete database record
        await db.delete(resource)
        logger.bind(
            resource_id=resource_id,
            age_hours=round(age_hours, 2),
            project_id=resource.project_id,
            outcome="deleted",
        ).info("Cleaned up stale pending resource")

        return True

    except asyncio.CancelledError:
        # Re-raise to allow graceful task cancellation
        raise
    except Exception as e:  # noqa: BLE001 - Defensive catch-all for background cleanup
        logger.bind(
            resource_id=resource_id,
            age_hours=round(age_hours, 2),
            project_id=resource.project_id,
            error=str(e),
            error_type=type(e).__name__,
        ).error("Failed to clean up stale pending resource")
        await db.rollback()
        return False


async def cancel_pending_resource(
    resource_id: UUID, db: AsyncSession, current_user: User
) -> None:
    """
    Cancel a pending resource upload.

    Validates user access, checks resource state, and performs cleanup.
    Raises appropriate RFC9457 exceptions for error cases.

    Args:
        resource_id: The UUID of the resource to cancel
        db: Database session
        current_user: The authenticated user making the request

    Raises:
        ResourceNotFoundError: If resource doesn't exist
        ProjectAccessDeniedError: If user doesn't have access to the resource's project
        InvalidResourceStateError: If resource is already uploaded
    """
    from app.core.control_exceptions import (
        InvalidResourceStateError,
        ProjectAccessDeniedError,
        ResourceNotFoundError,
    )

    # Get the resource
    resource = await db.get(AttackResourceFile, resource_id)
    if not resource:
        raise ResourceNotFoundError(detail=f"Resource {resource_id} not found")

    # Check project access
    # For unrestricted resources (project_id=None), require superuser access
    if resource.project_id is None:
        if not current_user.is_superuser:
            raise ProjectAccessDeniedError(
                detail="Only superusers can cancel unrestricted resources"
            )
    else:
        accessible_projects = [
            assoc.project_id for assoc in (current_user.project_associations or [])
        ]
        if (
            resource.project_id not in accessible_projects
            and not current_user.is_superuser
        ):
            raise ProjectAccessDeniedError(
                detail=f"User does not have access to project {resource.project_id}"
            )

    # Check resource state
    if resource.is_uploaded:
        raise InvalidResourceStateError(
            detail="Cannot cancel resource that is already uploaded. Use DELETE to remove uploaded resources."
        )

    # Perform cleanup
    success = await cleanup_stale_resource(resource, db)
    if not success:
        from app.core.control_exceptions import InternalServerError

        raise InternalServerError(detail="Failed to clean up resource")

    # Commit the deletion
    await db.commit()

    # Log the manual cancellation (use user_id instead of email for PII compliance)
    logger.bind(
        resource_id=str(resource_id),
        user_id=current_user.id,
        project_id=resource.project_id,
        action="manual_cancel",
    ).info("Resource upload cancelled by user")
