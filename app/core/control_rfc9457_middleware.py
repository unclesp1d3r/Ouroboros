"""
RFC9457 middleware for Control API routes only.

This middleware intercepts exceptions on Control API routes (/api/v1/control/*)
and converts them to RFC9457-compliant problem details responses. Supports
extension fields for InvalidStateTransitionProblem errors (current_state,
attempted_state, action, entity_type, valid_transitions).
"""

from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.control_exceptions import (
    AgentNotFoundError,
    AttackNotFoundError,
    CampaignNotFoundError,
    HashItemNotFoundError,
    HashListNotFoundError,
    InsufficientPermissionsError,
    InternalServerError,
    InvalidAttackConfigError,
    InvalidHashFormatError,
    InvalidResourceFormatError,
    InvalidResourceStateError,
    InvalidStateTransitionProblem,
    ProjectAccessDeniedError,
    ProjectNotFoundError,
    ResourceNotFoundError,
    TaskNotFoundError,
    UserConflictError,
    UserNotFoundError,
)

# Status code to title mapping for RFC9457 Problem Details
_STATUS_TITLES = {
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    409: "Conflict",
    422: "Unprocessable Entity",
    500: "Internal Server Error",
}


class ControlRFC9457Middleware(BaseHTTPMiddleware):
    """Middleware that applies RFC9457 error handling only to Control API routes."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process request and handle Control API exceptions with RFC9457 format."""
        # Only apply RFC9457 handling to Control API routes
        if not request.url.path.startswith("/api/v1/control/"):
            return await call_next(request)

        try:
            return await call_next(request)

        except InvalidStateTransitionProblem as exc:
            # Convert InvalidStateTransitionProblem to RFC9457 format with extension fields
            content: dict = {
                "type": exc.type,
                "title": exc.title,
                "status": exc.status_code,
                "detail": exc.detail,
                "instance": str(request.url.path),
                # Extension fields - always present on InvalidStateTransitionProblem
                "current_state": exc.current_state,
                "attempted_state": exc.attempted_state,
                "action": exc.action,
                "entity_type": exc.entity_type,
                "valid_transitions": exc.valid_transitions,
            }
            return JSONResponse(
                status_code=exc.status_code,
                content=content,
                headers={"Content-Type": "application/problem+json"},
            )
        except (
            CampaignNotFoundError,
            AttackNotFoundError,
            AgentNotFoundError,
            HashListNotFoundError,
            HashItemNotFoundError,
            ResourceNotFoundError,
            UserNotFoundError,
            UserConflictError,
            ProjectNotFoundError,
            TaskNotFoundError,
            InvalidAttackConfigError,
            InvalidHashFormatError,
            InvalidResourceFormatError,
            InvalidResourceStateError,
            InsufficientPermissionsError,
            InternalServerError,
            ProjectAccessDeniedError,
        ) as exc:
            # Convert custom exceptions to RFC9457 format
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "type": exc.type,
                    "title": exc.title,
                    "status": exc.status_code,
                    "detail": exc.detail,
                    "instance": str(request.url.path),
                },
                headers={"Content-Type": "application/problem+json"},
            )
        except HTTPException as exc:
            # Convert HTTPException to RFC9457 format for Control API routes
            title = _STATUS_TITLES.get(exc.status_code, "HTTP Error")

            # Build base problem response
            problem: dict = {
                "type": "about:blank",
                "title": title,
                "status": exc.status_code,
                "instance": str(request.url.path),
            }

            # Support problem extensions when detail is a dictionary
            if isinstance(exc.detail, dict):
                detail_dict: dict[str, Any] = exc.detail
                # Merge extension fields, but preserve required RFC9457 fields
                extensions = {
                    key: value
                    for key, value in detail_dict.items()
                    if key not in ("type", "title", "status", "instance")
                }
                problem.update(extensions)
                # Always set detail: use 'detail' from dict if present, otherwise fallback to title
                problem["detail"] = detail_dict.get("detail", title)
            else:
                problem["detail"] = str(exc.detail) if exc.detail else title

            return JSONResponse(
                status_code=exc.status_code,
                content=problem,
                headers={"Content-Type": "application/problem+json"},
            )

        except Exception:
            # Let other exceptions bubble up to be handled by existing handlers
            raise
