"""OpenAPI documentation customization for Ouroboros APIs."""

from typing import Any

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


def custom_openapi(app: FastAPI) -> dict[str, Any]:
    """Generate customized OpenAPI schema with enhanced documentation."""
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        servers=app.servers,
    )

    # Add custom OpenAPI extensions
    openapi_schema["info"]["x-logo"] = {
        "url": "https://raw.githubusercontent.com/unclesp1d3r/Ouroboros/main/docs/assets/logo.png",
        "altText": "Ouroboros Logo",
    }

    # Add comprehensive tags for better organization
    openapi_schema["tags"] = [
        {
            "name": "Authentication",
            "description": "User authentication and session management endpoints. Handles login, logout, JWT token management, and project context switching.",
            "externalDocs": {
                "description": "Authentication Guide",
                "url": "https://docs.ouroboros.example.com/api/authentication",
            },
        },
        {
            "name": "Agent API",
            "description": "Legacy-compatible API for Ouroboros agents. Maintains strict backward compatibility with v1 specification for agent registration, task management, and result submission.",
            "externalDocs": {
                "description": "Agent API Documentation",
                "url": "https://docs.ouroboros.example.com/api/agent",
            },
        },
        {
            "name": "Web UI API",
            "description": "Rich API interface for the SvelteKit web application. Provides comprehensive campaign management, real-time updates, and administrative functions.",
            "externalDocs": {
                "description": "Web UI API Documentation",
                "url": "https://docs.ouroboros.example.com/api/web",
            },
        },
        {
            "name": "Control API",
            "description": "Programmatic API for CLI tools and automation. Features RFC9457-compliant error responses and batch operations for scripting and integration.",
            "externalDocs": {
                "description": "Control API Documentation",
                "url": "https://docs.ouroboros.example.com/api/control",
            },
        },
        {
            "name": "Campaigns",
            "description": "Campaign lifecycle management including creation, configuration, execution control, and progress monitoring.",
        },
        {
            "name": "Attacks",
            "description": "Attack configuration and management within campaigns. Supports dictionary, mask, hybrid, and brute-force attack modes.",
        },
        {
            "name": "Agents",
            "description": "Agent fleet management including registration, configuration, monitoring, and performance tracking.",
        },
        {
            "name": "Hash Lists",
            "description": "Hash list management including creation, import/export, and hash item operations.",
        },
        {
            "name": "Resources",
            "description": "Attack resource management including wordlists, rules, masks, and file operations.",
        },
        {
            "name": "Real-time",
            "description": "Server-Sent Events (SSE) endpoints for real-time updates and notifications.",
        },
        {
            "name": "System",
            "description": "System health monitoring, statistics, and administrative operations.",
        },
    ]

    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "AgentBearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "csa_<agent_id>_<token>",
            "description": "Agent API authentication using bearer tokens with format `csa_<agent_id>_<random_string>`",
        },
        "ControlBearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "cst_<user_id>_<token>",
            "description": "Control API authentication using API keys with format `cst_<user_id>_<random_string>`",
        },
        "JWTCookie": {
            "type": "apiKey",
            "in": "cookie",
            "name": "access_token",
            "description": "Web UI API authentication using JWT tokens in HTTP-only cookies",
        },
    }

    # Add common response schemas
    openapi_schema["components"]["schemas"]["AgentAPIError"] = {
        "type": "object",
        "properties": {
            "error": {
                "type": "string",
                "description": "Human-readable error message",
                "example": "Invalid authentication token",
            },
        },
        "required": ["error"],
        "description": "Standard error response format for Agent API (legacy compatibility)",
    }

    openapi_schema["components"]["schemas"]["WebUIAPIError"] = {
        "type": "object",
        "properties": {
            "detail": {
                "oneOf": [
                    {"type": "string", "description": "Simple error message"},
                    {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "loc": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Field location path",
                                },
                                "msg": {
                                    "type": "string",
                                    "description": "Error message",
                                },
                                "type": {"type": "string", "description": "Error type"},
                            },
                        },
                        "description": "Validation error details",
                    },
                ],
            },
        },
        "required": ["detail"],
        "description": "Standard error response format for Web UI API (FastAPI format)",
    }

    openapi_schema["components"]["schemas"]["ControlAPIProblemDetails"] = {
        "type": "object",
        "properties": {
            "type": {
                "type": "string",
                "format": "uri",
                "description": "URI identifying the problem type",
                "example": "https://ouroboros.example.com/problems/validation-error",
            },
            "title": {
                "type": "string",
                "description": "Human-readable summary of the problem",
                "example": "Validation Error",
            },
            "status": {
                "type": "integer",
                "description": "HTTP status code",
                "example": 422,
            },
            "detail": {
                "type": "string",
                "description": "Human-readable explanation of the problem",
                "example": "The request contains invalid data",
            },
            "instance": {
                "type": "string",
                "format": "uri",
                "description": "URI reference to the specific occurrence",
                "example": "/api/v1/control/campaigns/123",
            },
            "errors": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "field": {"type": "string"},
                        "message": {"type": "string"},
                        "code": {"type": "string"},
                    },
                },
                "description": "Field-specific error details",
            },
        },
        "required": ["type", "title", "status", "detail", "instance"],
        "description": "RFC9457 Problem Details error response format for Control API",
    }

    # Add common examples
    openapi_schema["components"]["examples"] = {
        "CampaignExample": {
            "summary": "Example campaign",
            "value": {
                "id": 123,
                "name": "Corporate Password Recovery 2024",
                "description": "Recovering passwords from corporate domain controller dump",
                "state": "active",
                "project_id": 1,
                "hash_list_id": 456,
                "priority": 50,
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-01T15:30:00Z",
            },
        },
        "AgentExample": {
            "summary": "Example agent",
            "value": {
                "id": 789,
                "client_signature": "Ouroboros-Agent/2.1.0",
                "hostname": "gpu-worker-01.corp.local",
                "operating_system": "linux",
                "state": "active",
                "last_seen": "2024-01-01T15:30:00Z",
            },
        },
        "ValidationErrorExample": {
            "summary": "Validation error response",
            "value": {
                "detail": [
                    {
                        "loc": ["name"],
                        "msg": "field required",
                        "type": "value_error.missing",
                    },
                    {
                        "loc": ["priority"],
                        "msg": "ensure this value is greater than or equal to 0",
                        "type": "value_error.number.not_ge",
                    },
                ],
            },
        },
        "ProblemDetailsExample": {
            "summary": "RFC9457 Problem Details error",
            "value": {
                "type": "https://ouroboros.example.com/problems/validation-error",
                "title": "Validation Error",
                "status": 422,
                "detail": "The request contains invalid data",
                "instance": "/api/v1/control/campaigns",
                "errors": [
                    {
                        "field": "name",
                        "message": "Campaign name is required",
                        "code": "required",
                    },
                ],
            },
        },
    }

    # Enhance path operations with better descriptions and examples
    for path, path_item in openapi_schema["paths"].items():
        for method, operation in path_item.items():
            if method in ["get", "post", "put", "patch", "delete"]:
                # Add appropriate tags based on path
                if "/api/v1/client/" in path or "/api/v1/agent/" in path:
                    if "tags" not in operation:
                        operation["tags"] = ["Agent API"]
                elif "/api/v1/web/" in path:
                    if "tags" not in operation:
                        operation["tags"] = ["Web UI API"]
                elif "/api/v1/control/" in path and "tags" not in operation:
                    operation["tags"] = ["Control API"]
                # Add security requirements based on API type
                if "/api/v1/client/" in path or "/api/v1/agent/" in path:
                    if path not in [
                        "/api/v1/client/authenticate",
                    ]:  # Exclude auth endpoints
                        operation["security"] = [{"AgentBearer": []}]
                elif "/api/v1/web/" in path:
                    if not any(
                        auth_path in path for auth_path in ["/auth/login", "/health"]
                    ):
                        operation["security"] = [{"JWTCookie": []}]
                elif "/api/v1/control/" in path:
                    operation["security"] = [{"ControlBearer": []}]

                # Add common error responses
                if "responses" not in operation:
                    operation["responses"] = {}

                # Add authentication error responses
                if "security" in operation:
                    operation["responses"]["401"] = {
                        "description": "Authentication required or invalid credentials",
                    }
                    operation["responses"]["403"] = {
                        "description": "Insufficient permissions for this operation",
                    }

                # Add rate limiting response
                operation["responses"]["429"] = {"description": "Rate limit exceeded"}

                # Add server error response
                operation["responses"]["500"] = {"description": "Internal server error"}

    app.openapi_schema = openapi_schema
    return app.openapi_schema


def setup_openapi_customization(app: FastAPI) -> None:
    """Set up custom OpenAPI schema generation for the FastAPI app."""
    app.openapi = lambda: custom_openapi(app)
