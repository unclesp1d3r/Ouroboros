"""
Hash List Web API endpoints.

Follow these rules for all endpoints in this file:
1. Must return Pydantic models as JSON (no TemplateResponse or render()).
2. Must use FastAPI parameter types: Query, Path, Body, Depends, etc.
3. Must not parse inputs manually -- let FastAPI validate and raise 422s.
4. Must use dependency-injected context for auth/user/project state.
5. Must not include database logic -- delegate to a service layer (hash_list_service).
6. Must not contain HTMX, Jinja, or fragment-rendering logic.
7. Must annotate live-update triggers with: #SSE_TRIGGER: <event description>
"""

import csv
import io
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authz import user_can_access_project_by_id
from app.core.deps import get_current_user
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
from app.models.user import User
from app.schemas.hash_item import HashItemOut
from app.schemas.hash_list import HashListCreate, HashListOut
from app.schemas.shared import PaginatedResponse

router = APIRouter(prefix="/hash_lists", tags=["Hash Lists"])


async def _check_user_has_access_to_project(
    project_id: int,
    action: str,
    db: AsyncSession,
    current_user: User,
) -> None:
    """Check if user has access to project."""
    if not await user_can_access_project_by_id(current_user, project_id, action, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have access to project",
        )


def _generate_csv_content(hash_items: list[HashItemOut]) -> str:
    """Generate CSV content from hash items."""
    output = io.StringIO()
    writer = csv.writer(output, dialect=csv.excel)

    # Write header
    writer.writerow(["id", "hash", "salt", "meta", "plain_text"])

    # Write data rows
    for item in hash_items:
        writer.writerow(
            [
                item.id,
                item.hash or "",
                item.salt or "",
                str(item.meta) if item.meta else "",
                item.plain_text or "",
            ]
        )

    content = output.getvalue()
    output.close()
    return content


def _generate_tsv_content(hash_items: list[HashItemOut]) -> str:
    """Generate TSV content from hash items."""
    output = io.StringIO()
    writer = csv.writer(output, dialect=csv.excel_tab)

    # Write header
    writer.writerow(["id", "hash", "salt", "meta", "plain_text"])

    # Write data rows
    for item in hash_items:
        writer.writerow(
            [
                item.id,
                item.hash or "",
                item.salt or "",
                str(item.meta) if item.meta else "",
                item.plain_text or "",
            ]
        )

    content = output.getvalue()
    output.close()
    return content


@router.post(
    "/",
    summary="Create a new hash list",
    description="Create a new hash list in the specified project.",
    status_code=status.HTTP_201_CREATED,
)
async def create_hash_list(
    hash_list_data: HashListCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> HashListOut:
    """Create a new hash list."""
    try:
        # Check user has write access to the project
        await _check_user_has_access_to_project(
            hash_list_data.project_id, "write", db, current_user
        )

        return await create_hash_list_service(hash_list_data, db, current_user)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e


@router.get(
    "/",
    summary="List hash lists",
    description="List hash lists with pagination and filtering.",
)
async def list_hash_lists(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    size: Annotated[int, Query(ge=1, le=100, description="Page size")] = 20,
    name: Annotated[str | None, Query(description="Filter by name; optional")] = None,
    project_id: Annotated[
        int | None, Query(description="Filter by project ID; optional")
    ] = None,
) -> PaginatedResponse[HashListOut]:
    """List hash lists with pagination and filtering."""
    # If project_id is specified, check access
    if project_id is not None:
        await _check_user_has_access_to_project(project_id, "read", db, current_user)

    skip = (page - 1) * size
    hash_lists, total = await list_hash_lists_service(
        db, skip=skip, limit=size, name_filter=name, project_id=project_id
    )

    return PaginatedResponse[HashListOut](
        items=hash_lists,
        total=total,
        page=page,
        page_size=size,
        search=name,
    )


@router.get(
    "/{hash_list_id}",
    summary="Get hash list by ID",
    description="Get a hash list by its ID.",
)
async def get_hash_list(
    hash_list_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> HashListOut:
    """Get a hash list by ID."""
    try:
        hash_list = await get_hash_list_service(hash_list_id, db)

        # Check user has read access to the project
        await _check_user_has_access_to_project(
            hash_list.project_id, "read", db, current_user
        )
    except HashListNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    else:
        return hash_list


@router.get(
    "/{hash_list_id}/items",
    summary="List hash items in hash list",
    description="List hash items in a hash list with pagination, search, and filtering. Supports CSV/TSV export.",
    response_model=None,  # Disable automatic response model generation for union types
)
async def list_hash_list_items(
    hash_list_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    size: Annotated[int, Query(ge=1, le=100, description="Page size")] = 20,
    search: Annotated[
        str | None, Query(description="Search by hash value or plaintext; optional")
    ] = None,
    status_filter: Annotated[
        str | None,
        Query(description="Filter by status: 'cracked', 'uncracked'; optional"),
    ] = None,
    export_format: Annotated[
        str | None, Query(description="Export format: 'csv', 'tsv'; optional")
    ] = None,
) -> PaginatedResponse[HashItemOut] | StreamingResponse:
    """List hash items in a hash list with pagination, search, and filtering."""
    try:
        # First get the hash list to check project access
        hash_list = await get_hash_list_service(hash_list_id, db)

        # Check user has read access to the project
        await _check_user_has_access_to_project(
            hash_list.project_id, "read", db, current_user
        )

        # For export formats, get all items (no pagination)
        if export_format in ("csv", "tsv"):
            hash_items, _ = await list_hash_list_items_service(
                hash_list_id,
                db,
                skip=0,
                limit=10000,
                search=search,
                status_filter=status_filter,
            )

            if export_format == "csv":
                content = _generate_csv_content(hash_items)
                media_type = "text/csv"
                filename = f"hash_list_{hash_list_id}_items.csv"
            else:  # tsv
                content = _generate_tsv_content(hash_items)
                media_type = "text/tab-separated-values"
                filename = f"hash_list_{hash_list_id}_items.tsv"

            return StreamingResponse(
                io.BytesIO(content.encode("utf-8")),
                media_type=media_type,
                headers={"Content-Disposition": f"attachment; filename={filename}"},
            )

        # Regular JSON response with pagination
        skip = (page - 1) * size
        hash_items, total = await list_hash_list_items_service(
            hash_list_id,
            db,
            skip=skip,
            limit=size,
            search=search,
            status_filter=status_filter,
        )

        return PaginatedResponse[HashItemOut](
            items=hash_items,
            total=total,
            page=page,
            page_size=size,
            search=search,
        )

    except HashListNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.patch(
    "/{hash_list_id}",
    summary="Update hash list",
    description="Update a hash list by its ID.",
)
async def update_hash_list(
    hash_list_id: int,
    data: HashListUpdateData,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> HashListOut:
    """Update a hash list."""
    try:
        # First get the hash list to check project access
        hash_list = await get_hash_list_service(hash_list_id, db)

        # Check user has write access to the project
        await _check_user_has_access_to_project(
            hash_list.project_id, "write", db, current_user
        )

        return await update_hash_list_service(hash_list_id, data, db)
    except HashListNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.delete(
    "/{hash_list_id}",
    summary="Delete hash list",
    description="Delete a hash list by its ID.",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_hash_list(
    hash_list_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    """Delete a hash list."""
    try:
        # First get the hash list to check project access
        hash_list = await get_hash_list_service(hash_list_id, db)

        # Check user has write access to the project
        await _check_user_has_access_to_project(
            hash_list.project_id, "write", db, current_user
        )

        await delete_hash_list_service(hash_list_id, db)
    except HashListNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
