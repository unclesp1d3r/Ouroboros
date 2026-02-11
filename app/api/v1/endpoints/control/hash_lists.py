"""
Control API hash list endpoints.

The Control API uses API key authentication and offset-based pagination.
All responses are JSON format.
Error responses must follow RFC9457 format.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.control_exceptions import (
    HashListNotFoundError as HashListNotFoundProblem,
)
from app.core.control_exceptions import (
    InternalServerError,
    ProjectAccessDeniedError,
)
from app.core.deps import get_current_control_user
from app.core.services.hash_list_service import (
    HashListNotFoundError,
    HashListUpdateData,
    create_hash_list_service,
    delete_hash_list_service,
    get_hash_list_service,
    list_hash_list_items_service,
    list_hash_lists_service,
    update_hash_list_service,
)
from app.db.session import get_db
from app.models.campaign import Campaign
from app.models.hash_list import HashList
from app.models.user import User
from app.schemas.hash_item import HashItemOut
from app.schemas.hash_list import HashListCreate, HashListOut
from app.schemas.shared import OffsetPaginatedResponse

# =============================================================================
# Response Schemas
# =============================================================================


class HashListExportResponse(BaseModel):
    """Hash list export response with content."""

    hash_list_id: Annotated[int, Field(description="Hash list ID")]
    hash_list_name: Annotated[str, Field(description="Hash list name")]
    format: Annotated[str, Field(description="Export format")]
    total_items: Annotated[int, Field(description="Total hash items exported")]
    cracked_count: Annotated[int, Field(description="Number of cracked hashes")]
    content: Annotated[str, Field(description="Exported content")]

    model_config = ConfigDict(extra="forbid")


router = APIRouter(prefix="/hash-lists", tags=["Control - Hash Lists"])


def _get_accessible_projects(user: User) -> list[int]:
    """Get list of project IDs the user has access to."""
    if user.project_associations:
        return [assoc.project_id for assoc in user.project_associations]
    return []


async def _validate_project_access(
    user: User,
    project_id: int,
    db: AsyncSession,  # noqa: ARG001
) -> None:
    """Validate that user has access to the specified project."""
    accessible = _get_accessible_projects(user)
    if not accessible:
        raise ProjectAccessDeniedError(detail="User has no project access")
    if project_id not in accessible:
        raise ProjectAccessDeniedError(
            detail=f"User does not have access to project {project_id}"
        )


async def _validate_hash_list_access(
    hash_list_id: int, user: User, db: AsyncSession
) -> HashList:
    """Validate that user has access to the hash list and return it."""
    result = await db.execute(select(HashList).where(HashList.id == hash_list_id))
    hash_list = result.scalar_one_or_none()

    if not hash_list:
        raise HashListNotFoundProblem(
            detail=f"Hash list with ID {hash_list_id} not found"
        )

    await _validate_project_access(user, hash_list.project_id, db)
    return hash_list


@router.post(
    "",
    status_code=201,
    summary="Create hash list",
    description="Create a new hash list in the specified project.",
)
async def create_hash_list(
    data: HashListCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_control_user)],
) -> HashListOut:
    """
    Create a new hash list.

    The user must have access to the specified project.
    """
    try:
        await _validate_project_access(current_user, data.project_id, db)
        return await create_hash_list_service(data, db, current_user)
    except ProjectAccessDeniedError:
        raise
    except Exception as e:
        raise InternalServerError(detail=f"Failed to create hash list: {e!s}") from e


@router.get(
    "",
    summary="List hash lists",
    description="List hash lists with offset-based pagination and filtering. Supports project scoping based on user permissions.",
)
async def list_hash_lists(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_control_user)],
    limit: Annotated[
        int, Query(ge=1, le=100, description="Number of items to return")
    ] = 20,
    offset: Annotated[int, Query(ge=0, description="Number of items to skip")] = 0,
    name: Annotated[
        str | None,
        Query(description="Filter hash lists by name (case-insensitive partial match)"),
    ] = None,
    project_id: Annotated[
        int | None, Query(description="Filter hash lists by project ID")
    ] = None,
) -> OffsetPaginatedResponse[HashListOut]:
    """
    List hash lists with offset-based pagination and filtering.

    Access is scoped to projects the user has access to. If project_id is specified,
    the user must have access to that specific project.
    """
    try:
        accessible_projects = _get_accessible_projects(current_user)

        if not accessible_projects:
            raise ProjectAccessDeniedError(detail="User has no project access")

        # If project_id is specified, check if user has access to it
        if project_id is not None:
            if project_id not in accessible_projects:
                raise ProjectAccessDeniedError(
                    detail=f"User does not have access to project {project_id}"
                )
            # Use single project_id for filtering
            hash_lists, total = await list_hash_lists_service(
                db=db,
                skip=offset,
                limit=limit,
                name_filter=name,
                project_id=project_id,
            )
        else:
            # Get hash lists from all accessible projects
            # Note: list_hash_lists_service doesn't support project_ids list,
            # so we filter manually or iterate
            all_hash_lists = []
            total = 0
            for pid in accessible_projects:
                hl_list, count = await list_hash_lists_service(
                    db=db,
                    skip=0,
                    limit=10000,  # Get all for this project
                    name_filter=name,
                    project_id=pid,
                )
                all_hash_lists.extend(hl_list)
                total += count

            # Apply pagination manually
            hash_lists = all_hash_lists[offset : offset + limit]

        return OffsetPaginatedResponse(
            items=hash_lists,
            total=total,
            limit=limit,
            offset=offset,
        )
    except ProjectAccessDeniedError:
        raise
    except Exception as e:
        raise InternalServerError(detail=f"Failed to list hash lists: {e!s}") from e


@router.get(
    "/{hash_list_id}",
    summary="Get hash list",
    description="Get a hash list by ID.",
)
async def get_hash_list(
    hash_list_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_control_user)],
) -> HashListOut:
    """
    Get a hash list by ID.

    The user must have access to the project containing the hash list.
    """
    try:
        # Validate access first
        await _validate_hash_list_access(hash_list_id, current_user, db)
        return await get_hash_list_service(hash_list_id, db)
    except (HashListNotFoundProblem, ProjectAccessDeniedError):
        raise
    except HashListNotFoundError as exc:
        raise HashListNotFoundProblem(
            detail=f"Hash list with ID {hash_list_id} not found"
        ) from exc
    except Exception as e:
        raise InternalServerError(detail=f"Failed to get hash list: {e!s}") from e


@router.patch(
    "/{hash_list_id}",
    summary="Update hash list",
    description="Update hash list metadata (name, description).",
)
async def update_hash_list(
    hash_list_id: int,
    data: HashListUpdateData,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_control_user)],
) -> HashListOut:
    """
    Update hash list metadata.

    Only name, description, and is_unavailable can be updated.
    The user must have access to the project containing the hash list.
    """
    try:
        # Validate access first
        await _validate_hash_list_access(hash_list_id, current_user, db)
        return await update_hash_list_service(hash_list_id, data, db)
    except (HashListNotFoundProblem, ProjectAccessDeniedError):
        raise
    except HashListNotFoundError as exc:
        raise HashListNotFoundProblem(
            detail=f"Hash list with ID {hash_list_id} not found"
        ) from exc
    except Exception as e:
        raise InternalServerError(detail=f"Failed to update hash list: {e!s}") from e


@router.delete(
    "/{hash_list_id}",
    status_code=204,
    summary="Delete hash list",
    description="Delete a hash list. Cannot delete if used by campaigns.",
)
async def delete_hash_list(
    hash_list_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_control_user)],
) -> None:
    """
    Delete a hash list.

    The hash list cannot be deleted if it is currently being used by any campaigns.
    The user must have access to the project containing the hash list.
    """
    try:
        # Validate access first
        await _validate_hash_list_access(hash_list_id, current_user, db)

        # Check if hash list is used by any campaigns
        campaign_result = await db.execute(
            select(Campaign).where(Campaign.hash_list_id == hash_list_id).limit(1)
        )
        campaign = campaign_result.scalar_one_or_none()
        if campaign:
            from app.core.control_exceptions import InvalidResourceStateError

            raise InvalidResourceStateError(
                detail=f"Cannot delete hash list: it is used by campaign '{campaign.name}' (ID: {campaign.id})"
            )

        await delete_hash_list_service(hash_list_id, db)
    except (HashListNotFoundProblem, ProjectAccessDeniedError):
        raise
    except HashListNotFoundError as exc:
        raise HashListNotFoundProblem(
            detail=f"Hash list with ID {hash_list_id} not found"
        ) from exc
    except Exception as e:
        if "InvalidResourceStateError" in type(e).__name__:
            raise
        raise InternalServerError(detail=f"Failed to delete hash list: {e!s}") from e


# =============================================================================
# Hash Item Endpoints
# =============================================================================


@router.get(
    "/{hash_list_id}/items",
    summary="List hash items",
    description="List hash items in a hash list with offset-based pagination and filtering.",
)
async def list_hash_items(
    hash_list_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_control_user)],
    limit: Annotated[
        int, Query(ge=1, le=100, description="Number of items to return")
    ] = 20,
    offset: Annotated[int, Query(ge=0, description="Number of items to skip")] = 0,
    search: Annotated[
        str | None,
        Query(description="Search by hash value or plain text"),
    ] = None,
    status: Annotated[
        str | None,
        Query(description="Filter by status: 'cracked' or 'uncracked'"),
    ] = None,
) -> OffsetPaginatedResponse[HashItemOut]:
    """
    List hash items in a hash list with pagination and filtering.

    The user must have access to the project containing the hash list.
    """
    try:
        # Validate access first
        await _validate_hash_list_access(hash_list_id, current_user, db)

        items, total = await list_hash_list_items_service(
            hash_list_id=hash_list_id,
            db=db,
            skip=offset,
            limit=limit,
            search=search,
            status_filter=status,
        )

        return OffsetPaginatedResponse(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
        )
    except (HashListNotFoundProblem, ProjectAccessDeniedError):
        raise
    except HashListNotFoundError as exc:
        raise HashListNotFoundProblem(
            detail=f"Hash list with ID {hash_list_id} not found"
        ) from exc
    except Exception as e:
        raise InternalServerError(detail=f"Failed to list hash items: {e!s}") from e


# =============================================================================
# Export Endpoints
# =============================================================================


@router.get(
    "/{hash_list_id}/export/plaintext",
    summary="Export cracked passwords as plaintext",
    description="Export cracked passwords from a hash list as plain text, one per line.",
)
async def export_hash_list_plaintext(
    hash_list_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_control_user)],
) -> HashListExportResponse:
    """
    Export cracked passwords as plaintext.

    Returns only cracked passwords, one per line.
    The user must have access to the project containing the hash list.
    """
    from app.models.hash_item import HashItem
    from app.models.hash_list import hash_list_items

    try:
        hash_list = await _validate_hash_list_access(hash_list_id, current_user, db)

        # Get all cracked hash items
        stmt = (
            select(HashItem)
            .join(hash_list_items)
            .where(hash_list_items.c.hash_list_id == hash_list_id)
            .where(HashItem.plain_text.is_not(None))
        )
        result = await db.execute(stmt)
        cracked_items = result.scalars().all()

        # Get total count for statistics
        total_stmt = (
            select(HashItem)
            .join(hash_list_items)
            .where(hash_list_items.c.hash_list_id == hash_list_id)
        )
        total_result = await db.execute(total_stmt)
        total_items = len(list(total_result.scalars().all()))

        # Build plaintext content
        lines = [item.plain_text for item in cracked_items if item.plain_text]
        content = "\n".join(lines)

        return HashListExportResponse(
            hash_list_id=hash_list_id,
            hash_list_name=hash_list.name,
            format="plaintext",
            total_items=total_items,
            cracked_count=len(cracked_items),
            content=content,
        )
    except (HashListNotFoundProblem, ProjectAccessDeniedError):
        raise
    except HashListNotFoundError as exc:
        raise HashListNotFoundProblem(
            detail=f"Hash list with ID {hash_list_id} not found"
        ) from exc
    except Exception as e:
        raise InternalServerError(detail=f"Failed to export hash list: {e!s}") from e


@router.get(
    "/{hash_list_id}/export/potfile",
    summary="Export in potfile format",
    description="Export cracked hashes in hashcat potfile format (hash:plaintext).",
)
async def export_hash_list_potfile(
    hash_list_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_control_user)],
) -> HashListExportResponse:
    """
    Export cracked hashes in potfile format.

    Returns hash:plaintext pairs, one per line.
    The user must have access to the project containing the hash list.
    """
    from app.models.hash_item import HashItem
    from app.models.hash_list import hash_list_items

    try:
        hash_list = await _validate_hash_list_access(hash_list_id, current_user, db)

        # Get all cracked hash items
        stmt = (
            select(HashItem)
            .join(hash_list_items)
            .where(hash_list_items.c.hash_list_id == hash_list_id)
            .where(HashItem.plain_text.is_not(None))
        )
        result = await db.execute(stmt)
        cracked_items = result.scalars().all()

        # Get total count for statistics
        total_stmt = (
            select(HashItem)
            .join(hash_list_items)
            .where(hash_list_items.c.hash_list_id == hash_list_id)
        )
        total_result = await db.execute(total_stmt)
        total_items = len(list(total_result.scalars().all()))

        # Build potfile content (hash:plaintext format)
        lines = []
        for item in cracked_items:
            if item.plain_text:
                if item.salt:
                    lines.append(f"{item.hash}:{item.salt}:{item.plain_text}")
                else:
                    lines.append(f"{item.hash}:{item.plain_text}")
        content = "\n".join(lines)

        return HashListExportResponse(
            hash_list_id=hash_list_id,
            hash_list_name=hash_list.name,
            format="potfile",
            total_items=total_items,
            cracked_count=len(cracked_items),
            content=content,
        )
    except (HashListNotFoundProblem, ProjectAccessDeniedError):
        raise
    except HashListNotFoundError as exc:
        raise HashListNotFoundProblem(
            detail=f"Hash list with ID {hash_list_id} not found"
        ) from exc
    except Exception as e:
        raise InternalServerError(detail=f"Failed to export hash list: {e!s}") from e


@router.get(
    "/{hash_list_id}/export/csv",
    summary="Export as CSV",
    description="Export hash list data as CSV with hash, salt, plaintext, and status columns.",
)
async def export_hash_list_csv(
    hash_list_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_control_user)],
    include_uncracked: Annotated[
        bool, Query(description="Include uncracked hashes in export")
    ] = True,
) -> HashListExportResponse:
    """
    Export hash list data as CSV.

    Returns CSV with columns: id, hash, salt, plaintext, status.
    The user must have access to the project containing the hash list.
    """
    import csv
    import io

    from app.models.hash_item import HashItem
    from app.models.hash_list import hash_list_items

    try:
        hash_list = await _validate_hash_list_access(hash_list_id, current_user, db)

        # Build query
        stmt = (
            select(HashItem)
            .join(hash_list_items)
            .where(hash_list_items.c.hash_list_id == hash_list_id)
        )

        if not include_uncracked:
            stmt = stmt.where(HashItem.plain_text.is_not(None))

        result = await db.execute(stmt)
        items = result.scalars().all()

        # Count cracked
        cracked_count = sum(1 for item in items if item.plain_text)

        # Build CSV content
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "hash", "salt", "plaintext", "status"])

        for item in items:
            status = "cracked" if item.plain_text else "uncracked"
            writer.writerow(
                [
                    item.id,
                    item.hash,
                    item.salt or "",
                    item.plain_text or "",
                    status,
                ]
            )

        content = output.getvalue()

        return HashListExportResponse(
            hash_list_id=hash_list_id,
            hash_list_name=hash_list.name,
            format="csv",
            total_items=len(items),
            cracked_count=cracked_count,
            content=content,
        )
    except (HashListNotFoundProblem, ProjectAccessDeniedError):
        raise
    except HashListNotFoundError as exc:
        raise HashListNotFoundProblem(
            detail=f"Hash list with ID {hash_list_id} not found"
        ) from exc
    except Exception as e:
        raise InternalServerError(detail=f"Failed to export hash list: {e!s}") from e
