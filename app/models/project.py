"""Project model and association table for Ouroboros workspaces/campaigns."""

import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Table,
)
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.agent import Agent
    from app.models.user import User

# Define the join tables inline here (canonical source)
project_agents = Table(
    "project_agents",
    Base.metadata,
    Column("project_id", ForeignKey("projects.id"), primary_key=True),
    Column("agent_id", ForeignKey("agents.id"), primary_key=True),
)


class ProjectUserRole(str, enum.Enum):
    member = "member"
    admin = "admin"


class ProjectUserAssociation(Base):
    """Model for a user's association with a project."""

    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id"), primary_key=True
    )
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)

    role: Mapped[ProjectUserRole] = mapped_column(
        Enum(ProjectUserRole), default=ProjectUserRole.member, nullable=False
    )

    project: Mapped["Project"] = relationship(back_populates="user_associations")
    user: Mapped["User"] = relationship(back_populates="project_associations")


class Project(Base):
    """Project model representing a workspace or campaign grouping.

    Supports many-to-many relationship with users and agents.
    """

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(
        String(length=128), unique=True, nullable=False, index=True
    )
    description: Mapped[str | None] = mapped_column(String(length=512), nullable=True)
    private: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    archived_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    notes: Mapped[str | None] = mapped_column(String(length=1024), nullable=True)
    user_associations = relationship(
        "ProjectUserAssociation", back_populates="project", cascade="all, delete-orphan"
    )
    users = association_proxy(
        "user_associations",
        "user",
        creator=lambda user: ProjectUserAssociation(user=user),  # type: ignore[reportUnknownLambdaType]
    )
    agents: Mapped[list["Agent"]] = relationship(
        "Agent", secondary=project_agents, back_populates="projects", lazy="selectin"
    )
    campaigns = relationship("Campaign", back_populates="project", lazy="selectin")
