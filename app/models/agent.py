"""Agent model for Ouroboros distributed cracking agents."""

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.project import project_agents
from app.models.user import User

if TYPE_CHECKING:
    from app.models.project import Project


class AgentState(enum.Enum):
    """Enum for agent states."""

    pending = "pending"
    active = "active"
    stopped = "stopped"
    error = "error"


class AgentType(enum.Enum):
    """Enum for agent types."""

    physical = "physical"
    virtual = "virtual"
    container = "container"


class OperatingSystemEnum(enum.Enum):
    linux = "linux"
    windows = "windows"
    macos = "macos"
    other = "other"


class Agent(Base):
    """Represents a distributed cracking agent in Ouroboros.

    Fields:
        - id (int): The ID of the agent.
        - client_signature (str): The client signature of the agent.
        - host_name (str): The host name of the agent.
        - custom_label (str | None): The custom label of the agent.
        - token (str): The token of the agent.
        - last_seen_at (datetime | None): The last time the agent was seen by the server.
        - last_ipaddress (str | None): The last IP address of the agent.
        - state (AgentState): The state of the agent.
        - enabled (bool): Whether the agent is enabled.
        - advanced_configuration (dict[str, Any] | None): The advanced configuration of the agent.
        - devices (list[str] | None): The devices of the agent.
        - agent_type (AgentType | None): The type of the agent.
        - operating_system (OperatingSystemEnum): The operating system of the agent.
        - user_id (UUID | None): The ID of the user that the agent belongs to.
        - user (User | None): The user that the agent belongs to.
        - projects (list[Project]): The projects that the agent belongs to.
        - tasks (list[Task]): The tasks that the agent is running.
        - benchmarks (list[HashcatBenchmark]): The benchmarks that the agent has run.

    Notes:
        - The `client_signature` field is used to identify the current version of the agent software.
        - The `host_name` field is the host name of the agent and is set by the agent based on the operating system information.
        - The `custom_label` field is an optional custom label set by the administrator to identify the agent and overrides the host name in the UI.
        - The `token` field is used to authenticate the agent with the server and is unique to each agent. It is also used to identify the agent by the Agent API.
        - The `last_seen_at` field is the last time the agent was seen by the server. It is updated by the server on every API request.
        - The `advanced_configuration` field is a JSON column that stores the advanced configuration of the agent and is intentionally flexible to allow for future expansion.
    """

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    client_signature: Mapped[str] = mapped_column(String(length=128), nullable=False)
    host_name: Mapped[str] = mapped_column(String(length=128), nullable=False)
    custom_label: Mapped[str | None] = mapped_column(
        String(length=128), unique=True, nullable=True, index=True
    )
    token: Mapped[str] = mapped_column(
        String(length=128), unique=True, nullable=False, index=True
    )
    last_seen_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_ipaddress: Mapped[str | None] = mapped_column(String(length=45), nullable=True)
    state: Mapped[AgentState] = mapped_column(
        Enum(AgentState), nullable=False, index=True
    )
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    advanced_configuration: Mapped[dict[str, Any] | None] = mapped_column(
        MutableDict.as_mutable(JSON), nullable=True
    )
    devices: Mapped[list[str] | None] = mapped_column(
        MutableList.as_mutable(JSON), nullable=True
    )
    agent_type: Mapped[AgentType | None] = mapped_column(Enum(AgentType), nullable=True)
    operating_system: Mapped[OperatingSystemEnum] = mapped_column(
        Enum(OperatingSystemEnum), nullable=False, default=OperatingSystemEnum.linux
    )
    user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    user: Mapped[User | None] = relationship("User")
    projects: Mapped[list["Project"]] = relationship(
        "Project", secondary=project_agents, back_populates="agents", lazy="selectin"
    )
    __table_args__ = (
        Index("ix_agent_token", "token", unique=True),
        Index("ix_agent_state", "state"),
        Index("ix_agent_custom_label", "custom_label", unique=True),
    )

    # Relationships
    tasks = relationship("Task", back_populates="agent")
    benchmarks = relationship(
        "HashcatBenchmark", back_populates="agent", cascade="all, delete-orphan"
    )
    device_performances = relationship(
        "AgentDevicePerformance", back_populates="agent", cascade="all, delete-orphan"
    )
    crack_results = relationship(
        "CrackResult", back_populates="agent", cascade="all, delete-orphan"
    )
    errors = relationship(
        "AgentError", back_populates="agent", cascade="all, delete-orphan"
    )

    @property
    def benchmark_map(self) -> dict[int, float]:
        """Return a map of hash_type_id to hash_speed for this agent."""
        return {b.hash_type_id: b.hash_speed for b in self.benchmarks}

    def can_handle_hash_type(self, hash_type_id: int) -> bool:
        """Return True if agent has a benchmark for the given hash_type_id."""
        return hash_type_id in self.benchmark_map
