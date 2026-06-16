from typing import Any

from fastapi import HTTPException, Request, Response, status
from fastapi.exception_handlers import http_exception_handler
from fastapi.responses import JSONResponse

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


def _build_rfc9457_response(request: Request, exc: HTTPException) -> JSONResponse:
    """Build an RFC9457-compliant Problem Details response from an HTTPException."""
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


# --- V1 Error Envelope Handler ---
# To enable strict v1 error envelope compliance, register this handler on the main FastAPI app for all /api/v1/client/* and /api/v1/agent/* endpoints.
# Also handles /api/v1/control/* endpoints with RFC9457 Problem Details format.
async def v1_http_exception_handler(request: Request, exc: Exception) -> Response:
    # Only handle HTTPException, otherwise re-raise
    if not isinstance(exc, HTTPException):
        raise exc

    # Handle Control API paths with RFC9457 Problem Details format
    if request.url.path.startswith("/api/v1/control/"):
        return _build_rfc9457_response(request, exc)

    # Only handle if route is /api/v1/agent/* or /api/v1/client/*
    if not request.url.path.startswith(
        "/api/v1/agent/"
    ) and not request.url.path.startswith("/api/v1/client/"):
        return await http_exception_handler(request, exc)

    if exc.status_code >= status.HTTP_400_BAD_REQUEST:
        detail = exc.detail
        if isinstance(detail, dict):
            # Return custom error object as-is (e.g., abandon returns {"state": [...]})
            return JSONResponse(status_code=exc.status_code, content=detail)
        # Otherwise, wrap in {"error": ...} for string or other types
        return JSONResponse(status_code=exc.status_code, content={"error": str(detail)})
    return JSONResponse(status_code=exc.status_code, content={"error": str(exc.detail)})
