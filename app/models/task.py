from datetime import datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy import Enum as SQLAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

# Magic value for task completion percentage
TASK_COMPLETION_PERCENT: float = 100.0


class TaskStatus(StrEnum):
    """Enum for task statuses."""

    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    ABANDONED = "abandoned"


class Task(Base):
    """Model for cracking tasks."""

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    attack_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("attacks.id"), nullable=False
    )
    agent_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("agents.id"), nullable=True
    )
    start_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    status: Mapped[TaskStatus] = mapped_column(
        SQLAEnum(TaskStatus), default=TaskStatus.PENDING, nullable=False
    )
    skip: Mapped[int | None] = mapped_column(Integer, nullable=True)
    limit: Mapped[int | None] = mapped_column(Integer, nullable=True)

    retry_count: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )

    # Error handling
    error_message: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    error_details: Mapped[dict[str, Any] | None] = mapped_column(
        MutableDict.as_mutable(JSONB), nullable=True
    )

    # Progress tracking
    progress: Mapped[float | None] = mapped_column(Float, default=0.0, nullable=True)
    estimated_completion: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    attack = relationship("Attack", back_populates="tasks")
    agent = relationship("Agent", back_populates="tasks")
    status_updates = relationship(
        "TaskStatusUpdate", back_populates="task", cascade="all, delete-orphan"
    )
    results = relationship(
        "HashcatResult", back_populates="task", cascade="all, delete-orphan"
    )
    errors = relationship(
        "AgentError", back_populates="task", cascade="all, delete-orphan"
    )

    @property
    def keyspace_total(self) -> int:
        # Assume keyspace_total is stored in error_details or as a direct attribute in the future
        if self.error_details and "keyspace_total" in self.error_details:
            value = self.error_details["keyspace_total"]
            if isinstance(value, int):
                return value
            try:
                return int(value)
            except ValueError, TypeError:
                return 0
        return 0

    @property
    def progress_percent(self) -> float:
        return self.progress if self.progress is not None else 0.0

    @property
    def is_complete(self) -> bool:
        result_submitted = False
        if self.error_details and "result_submitted" in self.error_details:
            result_submitted = bool(self.error_details["result_submitted"])
        return self.progress_percent >= TASK_COMPLETION_PERCENT or result_submitted


class TaskStatusUpdate(Base):
    """Model for a task status update."""

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id = mapped_column(Integer, ForeignKey("tasks.id"), nullable=False, index=True)
    original_line = mapped_column(String(1024), nullable=False)
    time = mapped_column(DateTime(timezone=True), nullable=False)
    session = mapped_column(String(128), nullable=False)
    status = mapped_column(Integer, nullable=False)
    target = mapped_column(String(256), nullable=False)
    progress = mapped_column(MutableDict.as_mutable(JSONB), nullable=False)
    restore_point = mapped_column(Integer, nullable=False)
    recovered_hashes = mapped_column(MutableDict.as_mutable(JSONB), nullable=False)
    recovered_salts = mapped_column(MutableDict.as_mutable(JSONB), nullable=False)
    rejected = mapped_column(Integer, nullable=False)
    time_start = mapped_column(DateTime(timezone=True), nullable=False)
    estimated_stop = mapped_column(DateTime(timezone=True), nullable=False)
    # Relationships
    hashcat_guess = relationship(
        "HashcatGuess",
        uselist=False,
        back_populates="status_update",
        cascade="all, delete-orphan",
    )
    device_statuses = relationship(
        "DeviceStatus", back_populates="status_update", cascade="all, delete-orphan"
    )
    task = relationship("Task", back_populates="status_updates")


class HashcatGuess(Base):
    """Model for a hashcat guess."""

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    status_update_id = mapped_column(
        Integer, ForeignKey("task_status_updates.id"), nullable=False, index=True
    )
    guess_base = mapped_column(String(256), nullable=False)
    guess_base_count = mapped_column(Integer, nullable=False)
    guess_base_offset = mapped_column(Integer, nullable=False)
    guess_base_percentage = mapped_column(Float, nullable=False)
    guess_mod = mapped_column(String(256), nullable=False)
    guess_mod_count = mapped_column(Integer, nullable=False)
    guess_mod_offset = mapped_column(Integer, nullable=False)
    guess_mod_percentage = mapped_column(Float, nullable=False)
    guess_mode = mapped_column(Integer, nullable=False)
    status_update = relationship("TaskStatusUpdate", back_populates="hashcat_guess")


class DeviceStatus(Base):
    """Model for a device status."""

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    status_update_id = mapped_column(
        Integer, ForeignKey("task_status_updates.id"), nullable=False, index=True
    )
    device_id = mapped_column(Integer, nullable=False)
    device_name = mapped_column(String(128), nullable=False)
    device_type = mapped_column(String(16), nullable=False)
    speed = mapped_column(Integer, nullable=False)
    utilization = mapped_column(Integer, nullable=False)
    temperature = mapped_column(Integer, nullable=False)
    status_update = relationship("TaskStatusUpdate", back_populates="device_statuses")


class HashcatResult(Base):
    """Model for a hashcat result."""

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id = mapped_column(Integer, ForeignKey("tasks.id"), nullable=False, index=True)
    timestamp = mapped_column(DateTime(timezone=True), nullable=False)
    hash = mapped_column(String(512), nullable=False)
    plain_text = mapped_column(String(512), nullable=False)
    task = relationship("Task", back_populates="results")
