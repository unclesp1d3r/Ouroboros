from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy import Enum as SQLAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class CampaignState(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"


class Campaign(Base):
    """Campaign model: operational grouping under a Project. Each campaign is associated with a required HashList.

    Fields:
        - name (str): The name of the campaign.
        - description (str | None): The description of the campaign.
        - created_at (datetime): The timestamp when the campaign was created.
        - updated_at (datetime): The timestamp when the campaign was last updated.
        - project_id (int): The ID of the project that the campaign belongs to.
        - priority (int): The priority of the campaign.
        - hash_list_id (int): The ID of the hash list that the campaign is associated with.
        - is_unavailable (bool): True if the campaign is not yet ready for use (e.g., being processed by upload pipeline).
        - state (CampaignState): The state of the campaign.
        - hash_list (HashList): The hash list that the campaign is associated with.
        - project (Project): The project that the campaign belongs to.
        - attacks (list[Attack]): The attacks that the campaign is associated with.
    """

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(length=128), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(length=512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id"), nullable=False, index=True
    )
    priority: Mapped[int] = mapped_column(default=0, nullable=False)
    hash_list_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("hash_lists.id"), nullable=False, index=True
    )
    is_unavailable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    state: Mapped[CampaignState] = mapped_column(
        SQLAEnum(CampaignState), default=CampaignState.DRAFT, nullable=False, index=True
    )

    hash_list = relationship("HashList")
    project = relationship("Project", back_populates="campaigns")
    attacks = relationship("Attack", back_populates="campaign", lazy="selectin")

    @property
    def progress_percent(self) -> float:
        """
        Returns the progress percentage of the campaign.
        This is the average of the progress percentages of the attacks in the campaign.
        """
        attacks = self.attacks or []
        if not attacks:
            return 0.0
        return float(sum(a.progress_percent for a in attacks)) / float(len(attacks))

    @property
    def is_complete(self) -> bool:
        """
        Returns True if all attacks in the campaign are complete.
        """
        attacks = self.attacks or []
        if not attacks:
            return False
        return all(a.is_complete for a in attacks)
