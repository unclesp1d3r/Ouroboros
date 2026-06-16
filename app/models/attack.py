from datetime import datetime
from enum import Enum
from uuid import UUID

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy import Enum as SQLAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class AttackMode(str, Enum):
    """Enum for attack modes."""

    DICTIONARY = "dictionary"
    MASK = "mask"
    HYBRID_DICTIONARY = "hybrid_dictionary"
    HYBRID_MASK = "hybrid_mask"


class AttackState(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    ABANDONED = "abandoned"


class WordlistSource(str, Enum):
    EXISTING = "existing"
    PREVIOUS_PASSWORDS = "previous_passwords"


class Attack(Base):
    """Model for password cracking attacks."""

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Basic attack configuration
    attack_mode: Mapped[AttackMode] = mapped_column(
        SQLAEnum(AttackMode), default=AttackMode.DICTIONARY, nullable=False
    )
    attack_mode_hashcat: Mapped[int] = mapped_column(Integer, default=0)
    hash_mode: Mapped[int] = mapped_column(Integer, default=0)

    # Attack parameters
    mask: Mapped[str | None] = mapped_column(String(255), nullable=True)
    increment_mode: Mapped[bool] = mapped_column(Boolean, default=False)
    increment_minimum: Mapped[int] = mapped_column(Integer, default=0)
    increment_maximum: Mapped[int] = mapped_column(Integer, default=0)
    optimized: Mapped[bool] = mapped_column(Boolean, default=False)
    slow_candidate_generators: Mapped[bool] = mapped_column(Boolean, default=False)
    workload_profile: Mapped[int] = mapped_column(Integer, default=3)

    # Markov configuration
    disable_markov: Mapped[bool] = mapped_column(Boolean, default=False)
    classic_markov: Mapped[bool] = mapped_column(Boolean, default=False)
    markov_threshold: Mapped[int] = mapped_column(Integer, default=0)

    # Rule configuration
    left_rule: Mapped[str | None] = mapped_column(String(255), nullable=True)
    right_rule: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Custom charsets
    custom_charset_1: Mapped[str | None] = mapped_column(String(255), nullable=True)
    custom_charset_2: Mapped[str | None] = mapped_column(String(255), nullable=True)
    custom_charset_3: Mapped[str | None] = mapped_column(String(255), nullable=True)
    custom_charset_4: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Resource references
    hash_list_id: Mapped[int] = mapped_column(Integer, nullable=False)
    word_list_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("attack_resource_files.id"), nullable=True
    )
    rule_list_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("attack_resource_files.id"), nullable=True
    )  # NOTE: Alembic migration required for new column.
    mask_list_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("attack_resource_files.id"), nullable=True
    )  # NOTE: Alembic migration required for new column.
    charset_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("attack_resource_files.id"), nullable=True
    )  # NOTE: Alembic migration required for new column.

    # URLs and checksums
    hash_list_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    hash_list_checksum: Mapped[str] = mapped_column(String(64), nullable=False)

    # Additional fields
    name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    state: Mapped[AttackState] = mapped_column(
        SQLAEnum(AttackState), default=AttackState.PENDING, nullable=False, index=True
    )

    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    position: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, index=True
    )
    # New fields for UI/UX
    complexity_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    start_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    end_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    campaign_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("campaigns.id"), nullable=False, index=True
    )
    template_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("attacks.id"), nullable=True
    )

    # Dictionary attack modifiers (e.g., change_case, substitute_chars)
    modifiers: Mapped[list[str] | None] = mapped_column(
        JSON, nullable=True, default=None
    )  # NOTE: Alembic migration required for new column.

    # Wordlist source: 'existing' or 'previous_passwords'
    wordlist_source: Mapped[WordlistSource | None] = mapped_column(
        SQLAEnum(WordlistSource), nullable=True
    )

    # Relationships
    word_list = relationship(
        "AttackResourceFile",
        foreign_keys=[word_list_id],
        backref="word_list_attacks",
    )
    rule_list = relationship(
        "AttackResourceFile",
        foreign_keys=[rule_list_id],
        backref="rule_list_attacks",
    )
    mask_list = relationship(
        "AttackResourceFile",
        foreign_keys=[mask_list_id],
        backref="mask_list_attacks",
    )
    charset = relationship(
        "AttackResourceFile",
        foreign_keys=[charset_id],
        backref="charset_attacks",
    )
    tasks = relationship("Task", back_populates="attack", lazy="selectin")
    campaign = relationship("Campaign", back_populates="attacks")
    template = relationship("Attack", remote_side="Attack.id", backref="clones")
    crack_results = relationship(
        "CrackResult", back_populates="attack", cascade="all, delete-orphan"
    )

    @property
    def progress_percent(self) -> float:
        tasks = self.tasks or []
        if not tasks:
            return 0.0
        total_keyspace = float(sum(float(t.keyspace_total) for t in tasks))
        if total_keyspace > 0:
            weighted_sum = float(
                sum(
                    (float(t.progress_percent) / 100.0) * float(t.keyspace_total)
                    for t in tasks
                )
            )
            return weighted_sum / total_keyspace * 100.0
        # Fallback: simple average
        return float(sum(float(t.progress_percent) for t in tasks)) / float(len(tasks))

    @property
    def is_complete(self) -> bool:
        tasks = self.tasks or []
        if not tasks:
            return False
        return all(t.is_complete for t in tasks)
