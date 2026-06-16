from datetime import UTC, datetime

from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class HashcatBenchmark(Base):
    """Model for storing hashcat benchmark results for an agent/device/hash type."""

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    agent_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("agents.id"), nullable=False, index=True
    )
    hash_type_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("hash_types.id"), nullable=False
    )
    runtime: Mapped[int] = mapped_column(BigInteger, nullable=False)  # ms
    hash_speed: Mapped[float] = mapped_column(Float, nullable=False)  # hashes/sec
    device: Mapped[str] = mapped_column(String(length=128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    agent = relationship("Agent", back_populates="benchmarks")
    hash_type = relationship("HashType")
