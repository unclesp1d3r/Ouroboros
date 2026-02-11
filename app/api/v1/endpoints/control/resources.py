"""
Control API resources endpoints.

The Control API uses API key authentication and offset-based pagination.
All responses are JSON format.
Error responses must follow RFC9457 format.
"""

import asyncio
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.control_exceptions import (
    InternalServerError,
    InvalidResourceStateError,
    ProjectAccessDeniedError,
    ResourceNotFoundError,
)
from app.core.control_exceptions import (
    ResourceNotFoundError as ResourceNotFoundProblem,
)
from app.core.deps import get_current_control_user
from app.core.services.resource_service import (
    cancel_pending_resource,
    delete_resource_service,
    get_resource_or_404,
    update_resource_metadata_service,
)
from app.core.services.storage_service import get_storage_service
from app.db.session import get_db
from app.models.attack import Attack
from app.models.attack_resource_file import AttackResourceFile, AttackResourceType
from app.models.user import User
from app.schemas.resource import (
    EPHEMERAL_RESOURCE_TYPES,
    AttackBasic,
    ResourceBase,
    ResourceDetailResponse,
    ResourcePreviewResponse,
    ResourceUpdateRequest,
)
from app.schemas.shared import OffsetPaginatedResponse

router = APIRouter(prefix="/resources", tags=["Control - Resources"])


def _get_accessible_projects(user: User) -> list[int]:
    """Get list of project IDs the user has access to."""
    if user.project_associations:
        return [assoc.project_id for assoc in user.project_associations]
    return []


async def _validate_resource_access(resource: AttackResourceFile, user: User) -> None:
    """Validate that user has access to the resource's project."""
    # Unrestricted resources (project_id=None) are accessible to all authenticated users
    if resource.project_id is None:
        return

    accessible = _get_accessible_projects(user)
    if not accessible:
        raise ProjectAccessDeniedError(detail="User has no project access")
    if resource.project_id not in accessible:
        raise ProjectAccessDeniedError(
            detail=f"User does not have access to project {resource.project_id}"
        )


class ResourceOut(ResourceBase):
    """Resource output schema for Control API."""

    usage_count: int = 0


@router.get(
    "",
    summary="List resources",
    description="List resources with offset-based pagination and filtering. Supports filtering by type, project, and name search.",
)
async def list_resources(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_control_user)],
    limit: Annotated[
        int, Query(ge=1, le=100, description="Number of items to return")
    ] = 20,
    offset: Annotated[int, Query(ge=0, description="Number of items to skip")] = 0,
    resource_type: Annotated[
        AttackResourceType | None,
        Query(description="Filter by resource type"),
    ] = None,
    project_id: Annotated[int | None, Query(description="Filter by project ID")] = None,
    search: Annotated[
        str | None,
        Query(description="Search resources by name (case-insensitive partial match)"),
    ] = None,
) -> OffsetPaginatedResponse[ResourceOut]:
    """
    List resources with offset-based pagination and filtering.

    Access is scoped to projects the user has access to. Users can also see
    unrestricted resources (project_id=None).
    """
    try:
        accessible_projects = _get_accessible_projects(current_user)

        # Build base query - exclude ephemeral types
        stmt = select(AttackResourceFile).where(
            ~AttackResourceFile.resource_type.in_(EPHEMERAL_RESOURCE_TYPES)
        )

        # Filter by project access
        if project_id is not None:
            # User is filtering by specific project
            if project_id not in accessible_projects and not current_user.is_superuser:
                raise ProjectAccessDeniedError(
                    detail=f"User does not have access to project {project_id}"
                )
            stmt = stmt.where(AttackResourceFile.project_id == project_id)
        # Show resources from accessible projects + unrestricted resources
        elif not current_user.is_superuser:
            stmt = stmt.where(
                or_(
                    AttackResourceFile.project_id.is_(None),
                    AttackResourceFile.project_id.in_(accessible_projects),
                )
            )

        # Filter by resource type
        if resource_type is not None:
            stmt = stmt.where(AttackResourceFile.resource_type == resource_type)

        # Search by name
        if search:
            stmt = stmt.where(AttackResourceFile.file_name.ilike(f"%{search}%"))

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await db.scalar(count_stmt) or 0

        # Apply pagination and ordering
        stmt = stmt.order_by(AttackResourceFile.updated_at.desc())
        stmt = stmt.offset(offset).limit(limit)

        result = await db.execute(stmt)
        resources = list(result.scalars().all())

        # Build response with usage counts
        items = []
        for r in resources:
            # Count attacks using this resource
            usage_count = 0
            # Check word_list_id
            wl_count = await db.scalar(
                select(func.count()).where(Attack.word_list_id == r.id)
            )
            usage_count += wl_count or 0
            # Check left_rule (rule list linkage)
            rule_count = await db.scalar(
                select(func.count()).where(Attack.left_rule == str(r.guid))
            )
            usage_count += rule_count or 0

            items.append(
                ResourceOut(
                    id=r.id,
                    file_name=r.file_name,
                    file_label=r.file_label,
                    resource_type=r.resource_type,
                    line_count=r.line_count,
                    byte_size=r.byte_size,
                    checksum=r.checksum,
                    updated_at=r.updated_at,
                    line_format=r.line_format,
                    line_encoding=r.line_encoding,
                    used_for_modes=[
                        m.value if hasattr(m, "value") else str(m)
                        for m in r.used_for_modes
                    ]
                    if r.used_for_modes
                    else [],
                    source=r.source,
                    project_id=r.project_id,
                    unrestricted=(r.project_id is None),
                    is_uploaded=r.is_uploaded,
                    tags=r.tags,
                    usage_count=usage_count,
                )
            )

        return OffsetPaginatedResponse(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
        )
    except ProjectAccessDeniedError:
        raise
    except Exception as e:
        raise InternalServerError(detail=f"Failed to list resources: {e!s}") from e


@router.get(
    "/{resource_id}",
    summary="Get resource",
    description="Get a resource by ID with detailed metadata and usage statistics.",
)
async def get_resource(
    resource_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_control_user)],
) -> ResourceDetailResponse:
    """
    Get a resource by ID.

    Returns detailed metadata including usage statistics (attacks using this resource).
    The user must have access to the resource's project.
    """
    try:
        resource = await get_resource_or_404(resource_id, db)
        await _validate_resource_access(resource, current_user)

        # Get attacks using this resource
        attacks: list[AttackBasic] = []
        seen_ids: set[int] = set()

        # Check word_list_id
        wl_result = await db.execute(
            select(Attack).where(Attack.word_list_id == resource.id)
        )
        for attack in wl_result.scalars().all():
            if attack.id not in seen_ids:
                attacks.append(AttackBasic(id=attack.id, name=attack.name))
                seen_ids.add(attack.id)

        # Check left_rule (rule list linkage)
        rule_result = await db.execute(
            select(Attack).where(Attack.left_rule == str(resource.guid))
        )
        for attack in rule_result.scalars().all():
            if attack.id not in seen_ids:
                attacks.append(AttackBasic(id=attack.id, name=attack.name))
                seen_ids.add(attack.id)

        return ResourceDetailResponse(
            id=resource.id,
            file_name=resource.file_name,
            file_label=resource.file_label,
            resource_type=resource.resource_type,
            line_count=resource.line_count,
            byte_size=resource.byte_size,
            checksum=resource.checksum,
            updated_at=resource.updated_at,
            line_format=resource.line_format,
            line_encoding=resource.line_encoding,
            used_for_modes=[
                m.value if hasattr(m, "value") else str(m)
                for m in resource.used_for_modes
            ]
            if resource.used_for_modes
            else [],
            source=resource.source,
            project_id=resource.project_id,
            unrestricted=(resource.project_id is None),
            is_uploaded=resource.is_uploaded,
            tags=resource.tags,
            attacks=attacks,
        )
    except (ResourceNotFoundError, ResourceNotFoundProblem, ProjectAccessDeniedError):
        raise
    except HTTPException as e:
        if e.status_code == status.HTTP_404_NOT_FOUND:
            raise ResourceNotFoundProblem(
                detail=f"Resource with ID {resource_id} not found"
            ) from e
        raise InternalServerError(detail=f"Failed to get resource: {e.detail}") from e
    except Exception as e:
        raise InternalServerError(detail=f"Failed to get resource: {e!s}") from e


@router.get(
    "/{resource_id}/preview",
    summary="Preview resource content",
    description="Get a preview of the first N lines of a resource file.",
)
async def preview_resource(
    resource_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_control_user)],
    lines: Annotated[
        int, Query(ge=1, le=500, description="Number of lines to preview")
    ] = 100,
) -> ResourcePreviewResponse:
    """
    Get a preview of the first N lines of a resource file.

    Returns the first `lines` lines of the resource content.
    For ephemeral resources, reads from the content field.
    For file-backed resources, reads from MinIO storage.
    """
    try:
        resource = await get_resource_or_404(resource_id, db)
        await _validate_resource_access(resource, current_user)

        preview_lines: list[str] = []
        preview_error: str | None = None

        # Check if ephemeral/not uploaded - use content field
        if (
            resource.resource_type in EPHEMERAL_RESOURCE_TYPES
            or not resource.is_uploaded
        ):
            if resource.content and "lines" in resource.content:
                all_lines = resource.content["lines"]
                if isinstance(all_lines, list):
                    preview_lines = [str(line) for line in all_lines[:lines]]
                else:
                    preview_error = "Resource content is not in expected format"
            else:
                preview_error = "Resource has no content available for preview"
        else:
            # File-backed: read from MinIO
            try:
                storage_service = get_storage_service()
                bucket = settings.MINIO_BUCKET

                def _download() -> bytes:
                    obj = storage_service.client.get_object(bucket, str(resource.id))
                    # Read only enough bytes for preview (estimate ~100 bytes per line)
                    max_bytes = lines * 200
                    content = obj.read(max_bytes)
                    obj.close()
                    return content

                file_bytes = await asyncio.to_thread(_download)
                text = file_bytes.decode(
                    resource.line_encoding or "utf-8", errors="replace"
                )
                all_lines = text.splitlines()
                preview_lines = all_lines[:lines]
            except (OSError, UnicodeDecodeError, ConnectionError) as e:
                preview_error = f"Failed to read file from storage: {e!s}"

        return ResourcePreviewResponse(
            id=resource.id,
            file_name=resource.file_name,
            file_label=resource.file_label,
            resource_type=resource.resource_type,
            line_count=resource.line_count,
            byte_size=resource.byte_size,
            checksum=resource.checksum,
            updated_at=resource.updated_at,
            line_format=resource.line_format,
            line_encoding=resource.line_encoding,
            used_for_modes=[
                m.value if hasattr(m, "value") else str(m)
                for m in resource.used_for_modes
            ]
            if resource.used_for_modes
            else [],
            source=resource.source,
            project_id=resource.project_id,
            unrestricted=(resource.project_id is None),
            is_uploaded=resource.is_uploaded,
            tags=resource.tags,
            preview_lines=preview_lines,
            preview_error=preview_error,
            max_preview_lines=lines,
        )
    except (ResourceNotFoundError, ResourceNotFoundProblem, ProjectAccessDeniedError):
        raise
    except HTTPException as e:
        if e.status_code == status.HTTP_404_NOT_FOUND:
            raise ResourceNotFoundProblem(
                detail=f"Resource with ID {resource_id} not found"
            ) from e
        raise InternalServerError(
            detail=f"Failed to preview resource: {e.detail}"
        ) from e
    except Exception as e:
        raise InternalServerError(detail=f"Failed to preview resource: {e!s}") from e


@router.patch(
    "/{resource_id}",
    summary="Update resource metadata",
    description="Update resource metadata (name, description, tags). Cannot modify file content.",
)
async def update_resource(
    resource_id: UUID,
    data: ResourceUpdateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_control_user)],
) -> ResourceOut:
    """
    Update resource metadata.

    Only metadata fields can be updated (name, label, tags, etc.).
    File content cannot be modified through this endpoint.
    The user must have access to the resource's project.
    """
    try:
        resource = await get_resource_or_404(resource_id, db)
        await _validate_resource_access(resource, current_user)

        # If changing project_id, validate access to new project
        if data.project_id is not None and data.project_id != resource.project_id:
            accessible = _get_accessible_projects(current_user)
            if data.project_id not in accessible and not current_user.is_superuser:
                raise ProjectAccessDeniedError(
                    detail=f"User does not have access to project {data.project_id}"
                )

        updated = await update_resource_metadata_service(resource, data, db)

        # Calculate usage count
        usage_count = 0
        wl_count = await db.scalar(
            select(func.count()).where(Attack.word_list_id == updated.id)
        )
        usage_count += wl_count or 0
        rule_count = await db.scalar(
            select(func.count()).where(Attack.left_rule == str(updated.guid))
        )
        usage_count += rule_count or 0

        return ResourceOut(
            id=updated.id,
            file_name=updated.file_name,
            file_label=updated.file_label,
            resource_type=updated.resource_type,
            line_count=updated.line_count,
            byte_size=updated.byte_size,
            checksum=updated.checksum,
            updated_at=updated.updated_at,
            line_format=updated.line_format,
            line_encoding=updated.line_encoding,
            used_for_modes=[
                m.value if hasattr(m, "value") else str(m)
                for m in updated.used_for_modes
            ]
            if updated.used_for_modes
            else [],
            source=updated.source,
            project_id=updated.project_id,
            unrestricted=(updated.project_id is None),
            is_uploaded=updated.is_uploaded,
            tags=updated.tags,
            usage_count=usage_count,
        )
    except (ResourceNotFoundError, ResourceNotFoundProblem, ProjectAccessDeniedError):
        raise
    except HTTPException as e:
        if e.status_code == status.HTTP_404_NOT_FOUND:
            raise ResourceNotFoundProblem(
                detail=f"Resource with ID {resource_id} not found"
            ) from e
        raise InternalServerError(
            detail=f"Failed to update resource: {e.detail}"
        ) from e
    except Exception as e:
        raise InternalServerError(detail=f"Failed to update resource: {e!s}") from e


@router.delete(
    "/{resource_id}",
    status_code=204,
    summary="Delete resource",
    description="Delete a resource. Cannot delete if used by any attacks.",
)
async def delete_resource(
    resource_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_control_user)],
) -> None:
    """
    Delete a resource.

    The resource cannot be deleted if it is currently being used by any attacks.
    The user must have access to the resource's project.
    """
    try:
        resource = await get_resource_or_404(resource_id, db)
        await _validate_resource_access(resource, current_user)

        # The service function handles the attack linkage check
        await delete_resource_service(resource_id, db)
    except (ResourceNotFoundError, ResourceNotFoundProblem, ProjectAccessDeniedError):
        raise
    except InvalidResourceStateError:
        raise
    except HTTPException as e:
        if e.status_code == status.HTTP_404_NOT_FOUND:
            raise ResourceNotFoundProblem(
                detail=f"Resource with ID {resource_id} not found"
            ) from e
        if e.status_code == status.HTTP_409_CONFLICT:
            raise InvalidResourceStateError(
                detail="Cannot delete resource: it is used by one or more attacks"
            ) from e
        raise InternalServerError(
            detail=f"Failed to delete resource: {e.detail}"
        ) from e
    except Exception as e:
        if "409" in str(e) or "linked" in str(e).lower():
            raise InvalidResourceStateError(
                detail="Cannot delete resource: it is used by one or more attacks"
            ) from e
        raise InternalServerError(detail=f"Failed to delete resource: {e!s}") from e


@router.delete(
    "/{resource_id}/cancel",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel pending resource upload",
    description=(
        "Cancel a pending resource upload that has not yet been completed. "
        "This will delete the resource record from the database and remove any "
        "associated storage objects. Only pending (non-uploaded) resources can be cancelled. "
        "For already-uploaded resources, use the standard DELETE endpoint instead."
    ),
    responses={
        204: {"description": "Resource cancelled successfully"},
        400: {
            "description": "Invalid resource state - resource is already uploaded",
            "content": {
                "application/problem+json": {
                    "example": {
                        "type": "invalid-resource-state",
                        "title": "Invalid Resource State",
                        "status": 400,
                        "detail": "Cannot cancel resource that is already uploaded. Use DELETE to remove uploaded resources.",
                        "instance": "/api/v1/control/resources/123e4567-e89b-12d3-a456-426614174000/cancel",
                    }
                }
            },
        },
        403: {
            "description": "User does not have access to the resource's project",
            "content": {
                "application/problem+json": {
                    "example": {
                        "type": "project-access-denied",
                        "title": "Project Access Denied",
                        "status": 403,
                        "detail": "User does not have access to project 123",
                        "instance": "/api/v1/control/resources/123e4567-e89b-12d3-a456-426614174000/cancel",
                    }
                }
            },
        },
        404: {
            "description": "Resource not found",
            "content": {
                "application/problem+json": {
                    "example": {
                        "type": "resource-not-found",
                        "title": "Resource Not Found",
                        "status": 404,
                        "detail": "Resource 123e4567-e89b-12d3-a456-426614174000 not found",
                        "instance": "/api/v1/control/resources/123e4567-e89b-12d3-a456-426614174000/cancel",
                    }
                }
            },
        },
    },
)
async def cancel_pending_resource_upload(
    resource_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_control_user)],
) -> Response:
    """
    Cancel a pending resource upload.

    This endpoint allows users to manually cancel a resource upload that is still
    in the pending state (not yet marked as uploaded). This is useful for cleaning
    up abandoned uploads without waiting for the automatic cleanup job.

    The operation will:
    1. Validate the user has access to the resource's project
    2. Verify the resource is in pending state (is_uploaded=False)
    3. Delete any associated object from MinIO storage
    4. Delete the resource record from the database

    Args:
        resource_id: UUID of the resource to cancel.
        db: Database session (injected).
        current_user: Authenticated user from API key (injected).

    Returns:
        Response: 204 No Content on success.

    Raises:
        ResourceNotFoundError: If resource doesn't exist.
        ProjectAccessDeniedError: If user lacks project access.
        InvalidResourceStateError: If resource is already uploaded.
    """
    await cancel_pending_resource(resource_id, db, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
