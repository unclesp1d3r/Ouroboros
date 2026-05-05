from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class LoginResultLevel(StrEnum):
    """Enumeration of login result levels."""

    SUCCESS = "success"
    ERROR = "error"


class LoginResult(BaseModel):
    """Schema for authentication response containing login status and tokens."""

    message: Annotated[
        str,
        Field(
            description="Human-readable result message indicating login success or failure reason.",
            examples=[
                "Login successful.",
                "Invalid credentials.",
                "Account is disabled.",
            ],
        ),
    ]
    level: Annotated[
        LoginResultLevel,
        Field(
            description="Result level indicating success or error status.",
            examples=["success", "error"],
        ),
    ]
    access_token: Annotated[
        str | None,
        Field(
            description="JWT access token for authenticated requests. Only present on successful login.",
            examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."],
            default=None,
        ),
    ]

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "message": "Login successful.",
                    "level": "success",
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                },
                {
                    "message": "Invalid credentials.",
                    "level": "error",
                    "access_token": None,
                },
            ]
        }
    )


class ProjectContextDetail(BaseModel):
    """Schema for project context information in authentication responses."""

    id: Annotated[
        int, Field(description="Unique project identifier.", examples=[1, 42, 123])
    ]
    name: Annotated[
        str,
        Field(
            description="Human-readable project name.",
            examples=["Corporate Security", "Penetration Testing", "Research Project"],
        ),
    ]

    model_config = ConfigDict(
        json_schema_extra={"example": {"id": 1, "name": "Corporate Security"}}
    )


class UserContextDetail(BaseModel):
    """Schema for user context information in authentication responses."""

    id: Annotated[
        str,
        Field(
            description="Unique user identifier (UUID format).",
            examples=["123e4567-e89b-12d3-a456-426614174000"],
        ),
    ]
    email: Annotated[
        str,
        Field(
            description="User's email address.",
            examples=["admin@example.com", "analyst@corp.local"],
        ),
    ]
    name: Annotated[
        str,
        Field(
            description="User's full display name.",
            examples=["John Smith", "Security Administrator"],
        ),
    ]
    role: Annotated[
        str,
        Field(
            description="User's role determining access permissions.",
            examples=["admin", "analyst", "operator"],
        ),
    ]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "admin@example.com",
                "name": "System Administrator",
                "role": "admin",
            }
        }
    )


class ContextResponse(BaseModel):
    """Schema for user and project context information."""

    user: Annotated[
        UserContextDetail,
        Field(
            description="Current user's context information including role and permissions."
        ),
    ]
    active_project: Annotated[
        ProjectContextDetail | None,
        Field(
            description="Currently selected project context. Null if no project is selected.",
            examples=[{"id": 1, "name": "Corporate Security"}, None],
        ),
    ]
    available_projects: Annotated[
        list[ProjectContextDetail],
        Field(
            description="List of projects the user has access to and can switch between.",
            examples=[
                [
                    {"id": 1, "name": "Corporate Security"},
                    {"id": 2, "name": "Research Project"},
                ]
            ],
        ),
    ]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "email": "admin@example.com",
                    "name": "System Administrator",
                    "role": "admin",
                },
                "active_project": {"id": 1, "name": "Corporate Security"},
                "available_projects": [
                    {"id": 1, "name": "Corporate Security"},
                    {"id": 2, "name": "Research Project"},
                ],
            }
        }
    )


class SetContextRequest(BaseModel):
    """Schema for switching the active project context."""

    project_id: Annotated[
        int,
        Field(
            description="ID of the project to set as the active context. User must have access to this project.",
            gt=0,
            examples=[1, 42, 123],
        ),
    ]

    model_config = ConfigDict(json_schema_extra={"example": {"project_id": 1}})
