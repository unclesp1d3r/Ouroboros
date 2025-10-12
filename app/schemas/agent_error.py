"""Pydantic schemas for the AgentError model in Ouroboros."""

from datetime import datetime
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.agent_error import Severity


class AgentErrorBase(BaseModel):
    """Base schema for AgentError."""

    message: Annotated[
        str, Field(..., description="The error message reported by the agent")
    ]
    severity: Annotated[Severity, Field(..., description="The severity of the error")]
    error_code: Annotated[
        str | None,
        Field(
            default=None, description="Optional error code for programmatic handling"
        ),
    ]
    details: Annotated[
        dict[str, Any] | None,
        Field(
            default=None,
            description="Optional structured data with additional error context",
        ),
    ]
    agent_id: Annotated[int, Field(..., description="ID of the reporting agent")]
    task_id: Annotated[
        int | None,
        Field(default=None, description="ID of the related task, if applicable"),
    ]


class AgentErrorCreate(AgentErrorBase):
    """Schema for creating a new AgentError."""


class AgentErrorUpdate(BaseModel):
    """Schema for updating an AgentError."""

    message: Annotated[
        str | None,
        Field(default=None, description="The error message reported by the agent"),
    ]
    severity: Annotated[
        Severity | None,
        Field(default=None, description="The severity of the error"),
    ]
    error_code: Annotated[
        str | None,
        Field(
            default=None, description="Optional error code for programmatic handling"
        ),
    ]
    details: Annotated[
        dict[str, Any] | None,
        Field(
            default=None,
            description="Optional structured data with additional error context",
        ),
    ]
    task_id: Annotated[
        int | None,
        Field(default=None, description="ID of the related task, if applicable"),
    ]


class AgentErrorOut(AgentErrorBase):
    """Schema for reading AgentError data."""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
