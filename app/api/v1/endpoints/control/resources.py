"""
Control API resources endpoints.

The Control API uses API key authentication and RFC9457 error responses.
This module provides endpoints for resource management operations including
manual cancellation of pending uploads.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_control_user
from app.core.services.resource_service import cancel_pending_resource
from app.db.session import get_db
from app.models.user import User

router = APIRouter(prefix="/resources", tags=["Control - Resources"])


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
                        "type": "about:blank",
                        "title": "Invalid Resource State",
                        "status": 400,
                        "detail": "Cannot cancel resource that is already uploaded. Use DELETE to remove uploaded resources.",
                    }
                }
            },
        },
        403: {
            "description": "User does not have access to the resource's project",
            "content": {
                "application/problem+json": {
                    "example": {
                        "type": "about:blank",
                        "title": "Project Access Denied",
                        "status": 403,
                        "detail": "User does not have access to project 123",
                    }
                }
            },
        },
        404: {
            "description": "Resource not found",
            "content": {
                "application/problem+json": {
                    "example": {
                        "type": "about:blank",
                        "title": "Resource Not Found",
                        "status": 404,
                        "detail": "Resource 123e4567-e89b-12d3-a456-426614174000 not found",
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

    Returns 204 No Content on success.
    """
    await cancel_pending_resource(resource_id, db, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
