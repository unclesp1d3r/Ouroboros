import pathlib
import re
from typing import Annotated
from uuid import uuid4

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Form,
    HTTPException,
    Path,
    Query,
    Request,
    status,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_current_user
from app.core.logging import logger
from app.core.services.resource_service import (
    create_upload_resource_and_task_for_text_service,
    create_upload_resource_and_task_service,
    delete_upload_service,
    get_upload_errors_service,
    get_upload_status_service,
    launch_campaign_service,
)
from app.db.session import get_db
from app.models.project import Project, ProjectUserAssociation
from app.models.user import User
from app.schemas.resource import (
    ResourceUploadMeta,
    ResourceUploadResponse,
    UploadErrorEntryListResponse,
    UploadStatusOut,
)

router = APIRouter(prefix="/uploads", tags=["Uploads"])

ALLOWED_EXTENSIONS = {".shadow", ".pdf", ".zip", ".7z", ".docx"}
FILENAME_REGEX = re.compile(r"^[\w,\s-]+\.[A-Za-z0-9]{1,8}$")  # Basic filename check


def validate_upload_filename(filename: str) -> None:
    ext = pathlib.Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        logger.warning(
            f"File extension '{ext}' is not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )
        raise HTTPException(
            status_code=400,
            detail=f"File extension '{ext}' is not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )
    if not FILENAME_REGEX.match(filename):
        logger.warning(
            f"File name '{filename}' does not match regex {FILENAME_REGEX.pattern}",
        )
        raise HTTPException(
            status_code=400,
            detail="Invalid file name. Only alphanumeric, dash, underscore, space, and a single extension are allowed.",
        )


def validate_upload_size(request: Request) -> None:
    max_size = settings.UPLOAD_MAX_SIZE
    content_length = request.headers.get("content-length")
    if content_length is not None:
        try:
            size = int(content_length)
        except ValueError as e:
            logger.exception(f"Invalid Content-Length header: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Content-Length header.",
            ) from e
        if size > max_size:
            logger.warning(
                f"Upload size exceeds maximum allowed ({max_size // (1024 * 1024)}MB).",
            )
            raise HTTPException(
                status_code=400,
                detail=f"Upload size exceeds maximum allowed ({max_size // (1024 * 1024)}MB).",
            )


@router.post(
    "/",
    summary="Upload file or pasted hash blob",
    description="Create an UploadResourceFile DB record and HashUploadTask. For files, return a presigned S3 upload URL. For text blobs, store content directly and trigger processing.",
    status_code=status.HTTP_201_CREATED,
)
async def upload_resource_metadata(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    project_id: Annotated[int, Form()],
    file_name: Annotated[str | None, Form()] = None,
    file_label: Annotated[str | None, Form()] = None,
    text_content: Annotated[str | None, Form()] = None,
) -> ResourceUploadResponse:
    # Validate that either file_name or text_content is provided
    if text_content is None and file_name is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Either 'file_name' or 'text_content' must be provided.",
        )

    if text_content is not None and file_name is not None:
        # Both provided - this is allowed, file_name will be used for text blob
        pass
    elif text_content is not None:
        # Text blob upload - no file size validation needed
        pass
    else:
        # File upload - enforce upload size limit
        validate_upload_size(request)

    # Check project existence
    project = (
        await db.execute(select(Project).where(Project.id == project_id))
    ).scalar_one_or_none()
    if not project:
        logger.warning(f"Project {project_id} not found.")
        raise HTTPException(status_code=404, detail="Project not found.")
    # Check user membership
    assoc = (
        await db.execute(
            select(ProjectUserAssociation).where(
                ProjectUserAssociation.project_id == project_id,
                ProjectUserAssociation.user_id == current_user.id,
            )
        )
    ).scalar_one_or_none()
    if not assoc:
        logger.warning(
            f"User {current_user.id} is not authorized for project {project_id}.",
        )
        raise HTTPException(status_code=403, detail="Not authorized for this project.")

    if text_content is not None:
        # Handle text blob upload
        # Generate a filename for the text blob if not provided
        text_file_name = file_name or f"pasted_hashes_{uuid4().hex[:8]}.txt"

        resource, _ = await create_upload_resource_and_task_for_text_service(
            db=db,
            text_content=text_content,
            file_name=text_file_name,
            project_id=project_id,
            file_label=file_label,
            user=current_user,
            background_tasks=background_tasks,
        )
        logger.info(
            f"Created upload resource and task for text blob '{file_name}' in project {project_id} for user {current_user.email}.",
        )
        return ResourceUploadResponse(
            resource_id=resource.id,
            presigned_url=None,  # No presigned URL for text blobs
            resource=ResourceUploadMeta(
                file_name=resource.file_name,
            ),
        )
    # Handle file upload
    if not file_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File name is required.",
        )
    validate_upload_filename(file_name)
    resource, presigned_url, _ = await create_upload_resource_and_task_service(
        db=db,
        file_name=file_name,
        project_id=project_id,
        file_label=file_label,
        user=current_user,
    )
    logger.info(
        f"Created upload resource and task for file '{file_name}' in project {project_id} for user {current_user.email}.",
    )
    return ResourceUploadResponse(
        resource_id=resource.id,
        presigned_url=presigned_url,
        resource=ResourceUploadMeta(
            file_name=resource.file_name,
        ),
    )


@router.get(
    "/{upload_id}/status",
    summary="Get status of a hash upload task",
    description="Return the status and metadata for a hash upload task, including hash type, preview, and validation state.",
)
async def get_upload_status(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    upload_id: Annotated[int, Path(description="Upload task ID")],
) -> UploadStatusOut:
    return await get_upload_status_service(db, current_user, upload_id)


@router.get(
    "/{upload_id}/errors",
    summary="Get paginated list of failed lines for an upload task",
    description="Return paginated UploadErrorEntry objects for a given upload task.",
)
async def get_upload_errors(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    upload_id: Annotated[int, Path(description="Upload task ID")],
    page: Annotated[int, Query(ge=1, le=100)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> UploadErrorEntryListResponse:
    return await get_upload_errors_service(db, current_user, upload_id, page, page_size)


@router.post(
    "/{upload_id}/launch_campaign",
    summary="Generate resources and create campaign with default attacks",
    description="Finalize the upload by creating default attacks and making the campaign available for use. The campaign and hash list will be marked as available.",
    status_code=status.HTTP_200_OK,
)
async def launch_campaign(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    upload_id: Annotated[int, Path(description="Upload task ID")],
) -> dict[str, object]:
    """
    Launch campaign by creating default attacks and making it available.
    """
    return await launch_campaign_service(db, current_user, upload_id)


@router.delete(
    "/{upload_id}",
    summary="Remove discarded or invalid upload",
    description="Delete an upload task and all associated resources. Only allowed if the upload has not been converted into a fully formed campaign/hash_list with attacks.",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_upload(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    upload_id: Annotated[int, Path(description="Upload task ID")],
) -> None:
    """
    Delete an upload task and all associated resources.

    This includes:
    - The HashUploadTask
    - The associated UploadResourceFile (and S3 object if uploaded)
    - All RawHash records
    - All UploadErrorEntry records
    - The Campaign and HashList if they were created but not launched

    Only allowed if the upload task has not been converted into a fully formed
    campaign/hash_list (i.e., if the campaign and hash list are still marked
    as unavailable).
    """
    await delete_upload_service(db, current_user, upload_id)
