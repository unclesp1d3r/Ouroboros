"""Test Control API error handling with RFC9457 Problem Details format."""

from typing import Never

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.api.v1.endpoints.agent.v1_http_exception_handler import (
    v1_http_exception_handler,
)
from app.core.control_exceptions import (
    CampaignNotFoundError,
    InsufficientPermissionsError,
    InternalServerError,
    InvalidAttackConfigError,
    InvalidStateTransitionProblem,
    ProjectAccessDeniedError,
)
from app.core.control_rfc9457_middleware import ControlRFC9457Middleware


@pytest.fixture
def test_app() -> FastAPI:
    """Create a test FastAPI app with Control RFC9457 middleware and exception handler."""
    app = FastAPI()

    # Add Control API RFC9457 middleware
    app.add_middleware(ControlRFC9457Middleware)

    # Register HTTPException handler for Control API paths
    app.add_exception_handler(HTTPException, v1_http_exception_handler)

    # Add test routes that raise custom exceptions (using Control API paths)
    @app.get("/api/v1/control/test/campaign-not-found", response_model=None)
    async def test_campaign_not_found() -> Never:
        raise CampaignNotFoundError(detail="Campaign with ID 'test-123' not found")

    @app.get("/api/v1/control/test/insufficient-permissions", response_model=None)
    async def test_insufficient_permissions() -> Never:
        raise InsufficientPermissionsError(detail="User lacks required permissions")

    @app.get("/api/v1/control/test/invalid-attack-config", response_model=None)
    async def test_invalid_attack_config() -> Never:
        raise InvalidAttackConfigError(detail="Attack configuration is invalid")

    @app.get("/api/v1/control/test/project-access-denied", response_model=None)
    async def test_project_access_denied() -> Never:
        raise ProjectAccessDeniedError(detail="Access denied to project 'test-project'")

    @app.get("/api/v1/control/test/internal-server-error", response_model=None)
    async def test_internal_server_error() -> Never:
        raise InternalServerError(detail="An internal server error occurred")

    @app.get("/api/v1/control/test/invalid-state-transition", response_model=None)
    async def test_invalid_state_transition() -> Never:
        raise InvalidStateTransitionProblem(
            from_state="archived",
            to_state="active",
            action="start",
            entity_type="campaign",
            valid_transitions=["completed", "draft"],
        )

    # HTTPException test routes
    @app.get("/api/v1/control/test/http-400", response_model=None)
    async def test_http_400() -> Never:
        raise HTTPException(status_code=400, detail="Invalid request")

    @app.get("/api/v1/control/test/http-401", response_model=None)
    async def test_http_401() -> Never:
        raise HTTPException(status_code=401, detail="Authentication required")

    @app.get("/api/v1/control/test/http-403", response_model=None)
    async def test_http_403() -> Never:
        raise HTTPException(status_code=403, detail="Access denied")

    @app.get("/api/v1/control/test/http-404", response_model=None)
    async def test_http_404() -> Never:
        raise HTTPException(status_code=404, detail="Resource not found")

    @app.get("/api/v1/control/test/http-409", response_model=None)
    async def test_http_409() -> Never:
        raise HTTPException(status_code=409, detail="Resource conflict")

    @app.get("/api/v1/control/test/http-422", response_model=None)
    async def test_http_422() -> Never:
        raise HTTPException(status_code=422, detail="Validation failed")

    @app.get("/api/v1/control/test/http-500", response_model=None)
    async def test_http_500() -> Never:
        raise HTTPException(status_code=500, detail="Server error")

    @app.get("/api/v1/control/test/http-dict-detail", response_model=None)
    async def test_http_dict_detail() -> Never:
        raise HTTPException(
            status_code=422, detail={"field": "name", "error": "required"}
        )

    @app.get("/api/v1/control/test/http-unknown-status", response_model=None)
    async def test_http_unknown_status() -> Never:
        raise HTTPException(status_code=418, detail="I'm a teapot")

    # Non-Control API routes for path scoping tests
    @app.get("/api/v1/web/test/http-error", response_model=None)
    async def test_web_http_error() -> Never:
        raise HTTPException(status_code=404, detail="Not found")

    @app.get("/api/v1/client/test/http-error", response_model=None)
    async def test_client_http_error() -> Never:
        raise HTTPException(status_code=404, detail="Not found")

    return app


@pytest.fixture
def client(test_app: FastAPI) -> TestClient:
    """Create a test client."""
    return TestClient(test_app)


def test_campaign_not_found_error_format(client: TestClient) -> None:
    """Test that CampaignNotFoundError returns RFC9457 format."""
    response = client.get("/api/v1/control/test/campaign-not-found")

    assert response.status_code == 404
    assert response.headers["content-type"] == "application/problem+json"

    data = response.json()
    assert "type" in data
    assert "title" in data
    assert "status" in data
    assert "detail" in data
    assert "instance" in data

    assert data["title"] == "Campaign Not Found"
    assert data["status"] == 404
    assert data["detail"] == "Campaign with ID 'test-123' not found"
    assert data["instance"] == "/api/v1/control/test/campaign-not-found"


def test_insufficient_permissions_error_format(client: TestClient) -> None:
    """Test that InsufficientPermissionsError returns RFC9457 format."""
    response = client.get("/api/v1/control/test/insufficient-permissions")

    assert response.status_code == 403
    assert response.headers["content-type"] == "application/problem+json"

    data = response.json()
    assert data["title"] == "Insufficient Permissions"
    assert data["status"] == 403
    assert data["detail"] == "User lacks required permissions"


def test_invalid_attack_config_error_format(client: TestClient) -> None:
    """Test that InvalidAttackConfigError returns RFC9457 format."""
    response = client.get("/api/v1/control/test/invalid-attack-config")

    assert response.status_code == 400
    assert response.headers["content-type"] == "application/problem+json"

    data = response.json()
    assert data["title"] == "Invalid Attack Configuration"
    assert data["status"] == 400
    assert data["detail"] == "Attack configuration is invalid"


def test_project_access_denied_error_format(client: TestClient) -> None:
    """Test that ProjectAccessDeniedError returns RFC9457 format."""
    response = client.get("/api/v1/control/test/project-access-denied")

    assert response.status_code == 403
    assert response.headers["content-type"] == "application/problem+json"

    data = response.json()
    assert data["title"] == "Project Access Denied"
    assert data["status"] == 403
    assert data["detail"] == "Access denied to project 'test-project'"


def test_error_response_has_required_fields(client: TestClient) -> None:
    """Test that error responses contain all required RFC9457 fields."""
    response = client.get("/api/v1/control/test/campaign-not-found")

    data = response.json()

    # Required fields according to RFC9457
    required_fields = ["type", "title", "status", "detail", "instance"]

    for field in required_fields:
        assert field in data, f"Required field '{field}' missing from error response"

    # Verify field types
    assert isinstance(data["type"], str)
    assert isinstance(data["title"], str)
    assert isinstance(data["status"], int)
    assert isinstance(data["detail"], str)
    assert isinstance(data["instance"], str)


def test_internal_server_error_format(client: TestClient) -> None:
    """Test that InternalServerError returns RFC9457 format."""
    response = client.get("/api/v1/control/test/internal-server-error")

    assert response.status_code == 500
    assert response.headers["content-type"] == "application/problem+json"

    data = response.json()
    assert data["title"] == "Internal Server Error"
    assert data["status"] == 500
    assert data["detail"] == "An internal server error occurred"


def test_invalid_state_transition_error_format(client: TestClient) -> None:
    """Test that InvalidStateTransitionProblem returns RFC9457 format with extension fields."""
    response = client.get("/api/v1/control/test/invalid-state-transition")

    assert response.status_code == 409
    assert response.headers["content-type"] == "application/problem+json"

    data = response.json()
    # Required RFC9457 fields
    assert data["title"] == "Invalid State Transition"
    assert data["status"] == 409
    assert "archived" in data["detail"]
    assert "active" in data["detail"]

    # Extension fields specific to state transition errors
    assert data["current_state"] == "archived"
    assert data["attempted_state"] == "active"
    assert data["action"] == "start"
    assert data["entity_type"] == "campaign"
    assert data["valid_transitions"] == ["completed", "draft"]


def test_error_type_format(client: TestClient) -> None:
    """Test that error type follows kebab-case convention."""
    response = client.get("/api/v1/control/test/campaign-not-found")

    data = response.json()
    error_type = data["type"]

    # Should be kebab-case format
    assert "-" in error_type
    assert error_type.islower()
    assert " " not in error_type


# HTTPException conversion tests


def test_http_exception_400_format(client: TestClient) -> None:
    """Test that HTTPException with 400 status returns RFC9457 format."""
    response = client.get("/api/v1/control/test/http-400")

    assert response.status_code == 400
    assert response.headers["content-type"] == "application/problem+json"

    data = response.json()
    assert data["type"] == "about:blank"
    assert data["title"] == "Bad Request"
    assert data["status"] == 400
    assert data["detail"] == "Invalid request"
    assert data["instance"] == "/api/v1/control/test/http-400"


def test_http_exception_401_format(client: TestClient) -> None:
    """Test that HTTPException with 401 status returns RFC9457 format."""
    response = client.get("/api/v1/control/test/http-401")

    assert response.status_code == 401
    assert response.headers["content-type"] == "application/problem+json"

    data = response.json()
    assert data["type"] == "about:blank"
    assert data["title"] == "Unauthorized"
    assert data["status"] == 401
    assert data["detail"] == "Authentication required"


def test_http_exception_403_format(client: TestClient) -> None:
    """Test that HTTPException with 403 status returns RFC9457 format."""
    response = client.get("/api/v1/control/test/http-403")

    assert response.status_code == 403
    assert response.headers["content-type"] == "application/problem+json"

    data = response.json()
    assert data["type"] == "about:blank"
    assert data["title"] == "Forbidden"
    assert data["status"] == 403
    assert data["detail"] == "Access denied"


def test_http_exception_404_format(client: TestClient) -> None:
    """Test that HTTPException with 404 status returns RFC9457 format."""
    response = client.get("/api/v1/control/test/http-404")

    assert response.status_code == 404
    assert response.headers["content-type"] == "application/problem+json"

    data = response.json()
    assert data["type"] == "about:blank"
    assert data["title"] == "Not Found"
    assert data["status"] == 404
    assert data["detail"] == "Resource not found"
    assert data["instance"] == "/api/v1/control/test/http-404"


def test_http_exception_409_format(client: TestClient) -> None:
    """Test that HTTPException with 409 status returns RFC9457 format."""
    response = client.get("/api/v1/control/test/http-409")

    assert response.status_code == 409
    assert response.headers["content-type"] == "application/problem+json"

    data = response.json()
    assert data["type"] == "about:blank"
    assert data["title"] == "Conflict"
    assert data["status"] == 409
    assert data["detail"] == "Resource conflict"


def test_http_exception_422_format(client: TestClient) -> None:
    """Test that HTTPException with 422 status returns RFC9457 format."""
    response = client.get("/api/v1/control/test/http-422")

    assert response.status_code == 422
    assert response.headers["content-type"] == "application/problem+json"

    data = response.json()
    assert data["type"] == "about:blank"
    assert data["title"] == "Unprocessable Entity"
    assert data["status"] == 422
    assert data["detail"] == "Validation failed"


def test_http_exception_500_format(client: TestClient) -> None:
    """Test that HTTPException with 500 status returns RFC9457 format."""
    response = client.get("/api/v1/control/test/http-500")

    assert response.status_code == 500
    assert response.headers["content-type"] == "application/problem+json"

    data = response.json()
    assert data["type"] == "about:blank"
    assert data["title"] == "Internal Server Error"
    assert data["status"] == 500
    assert data["detail"] == "Server error"


def test_http_exception_dict_detail_format(client: TestClient) -> None:
    """Test that HTTPException with dictionary detail includes extension fields."""
    response = client.get("/api/v1/control/test/http-dict-detail")

    assert response.status_code == 422
    assert response.headers["content-type"] == "application/problem+json"

    data = response.json()
    # Required RFC9457 fields
    assert data["type"] == "about:blank"
    assert data["title"] == "Unprocessable Entity"
    assert data["status"] == 422
    assert data["instance"] == "/api/v1/control/test/http-dict-detail"

    # Extension fields from the dictionary detail
    assert data["field"] == "name"
    assert data["error"] == "required"


def test_http_exception_unknown_status_format(client: TestClient) -> None:
    """Test that HTTPException with unknown status code uses default title."""
    response = client.get("/api/v1/control/test/http-unknown-status")

    assert response.status_code == 418
    assert response.headers["content-type"] == "application/problem+json"

    data = response.json()
    assert data["type"] == "about:blank"
    assert data["title"] == "HTTP Error"  # Default title for unknown status
    assert data["status"] == 418
    assert data["detail"] == "I'm a teapot"


def test_http_exception_has_required_fields(client: TestClient) -> None:
    """Test that HTTPException responses contain all required RFC9457 fields."""
    response = client.get("/api/v1/control/test/http-404")

    data = response.json()

    # Required fields according to RFC9457
    required_fields = ["type", "title", "status", "detail", "instance"]

    for field in required_fields:
        assert field in data, f"Required field '{field}' missing from error response"

    # Verify field types
    assert isinstance(data["type"], str)
    assert isinstance(data["title"], str)
    assert isinstance(data["status"], int)
    assert isinstance(data["detail"], str)
    assert isinstance(data["instance"], str)


def test_middleware_only_affects_control_api_web_path(client: TestClient) -> None:
    """Test that middleware does NOT convert HTTPException on Web API paths."""
    response = client.get("/api/v1/web/test/http-error")

    assert response.status_code == 404
    # Should NOT be RFC9457 format - FastAPI default JSON response
    assert response.headers["content-type"] == "application/json"

    data = response.json()
    # FastAPI default format uses "detail" key directly
    assert data == {"detail": "Not found"}


def test_middleware_only_affects_control_api_client_path(client: TestClient) -> None:
    """Test that middleware does NOT convert HTTPException on Client API paths."""
    response = client.get("/api/v1/client/test/http-error")

    assert response.status_code == 404
    # Should NOT be RFC9457 format - uses agent/client error envelope format
    assert response.headers["content-type"] == "application/json"

    data = response.json()
    # Agent/Client API format uses "error" key (legacy compatibility)
    assert data == {"error": "Not found"}
