"""Pydantic schemas for the Project model in Ouroboros."""

from datetime import datetime
from typing import TYPE_CHECKING, Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

if TYPE_CHECKING:
    from app.models.project import ProjectUserAssociation
    from app.models.user import User


class ProjectRead(BaseModel):
    """Schema for reading project data."""

    id: int
    name: str
    description: str | None = None
    private: bool
    archived_at: datetime | None = None
    notes: str | None = None
    users: list[UUID]
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

    @field_validator("users", mode="before")
    @classmethod
    def validate_users(
        cls, v: list[User] | list[ProjectUserAssociation] | list[str] | list[UUID]
    ) -> list[UUID]:
        """Convert User objects or user associations to UUIDs."""
        if not v:
            return []

        result = []
        for item in v:
            # Import here to avoid circular imports
            from app.models.project import ProjectUserAssociation
            from app.models.user import User

            if isinstance(item, ProjectUserAssociation):
                result.append(item.user_id)
            elif isinstance(item, User):
                result.append(item.id)
            elif isinstance(item, (str, UUID)):
                result.append(UUID(str(item)) if isinstance(item, str) else item)  # type: ignore[reportUnnecessaryIsInstance]
            else:
                # This should not happen with proper typing, but handle gracefully
                result.append(item)
        return result


class ProjectCreate(BaseModel):
    """Schema for creating a new project."""

    name: str
    description: str | None = None
    private: bool = False
    archived_at: datetime | None = None
    notes: str | None = None
    users: list[UUID] | None = None


class ProjectUpdate(BaseModel):
    """Schema for updating project data."""

    name: Annotated[str | None, Field(min_length=1, max_length=255)] = None
    description: Annotated[str | None, Field(max_length=1024)] = None
    private: Annotated[bool | None, Field(default=False)] = None
    archived_at: Annotated[datetime | None, Field(default=None)] = None
    notes: Annotated[str | None, Field(max_length=1024)] = None
    users: Annotated[list[UUID] | None, Field(default=None)] = None
