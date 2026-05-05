from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class HashUploadStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL_FAILURE = "partial_failure"
    FAILED = "failed"


class HashUploadTask(Base):
    """Model for a user-initiated hash upload and processing pipeline."""

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[HashUploadStatus] = mapped_column(
        String(32), default=HashUploadStatus.PENDING, nullable=False, index=True
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    error_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    hash_list_id: Mapped[int | None] = mapped_column(
        ForeignKey("hash_lists.id"), nullable=True
    )
    campaign_id: Mapped[int | None] = mapped_column(
        ForeignKey("campaigns.id"), nullable=True
    )

    errors = relationship(
        "UploadErrorEntry", back_populates="upload_task", cascade="all, delete-orphan"
    )
    raw_hashes = relationship(
        "RawHash", back_populates="upload_task", cascade="all, delete-orphan"
    )
