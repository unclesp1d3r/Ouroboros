from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import JSON, String
from sqlalchemy import Enum as SQLAEnum
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Mapped, mapped_column

from app.models.attack import AttackMode
from app.models.base import Base


class AttackResourceType(StrEnum):
    MASK_LIST = "mask_list"
    RULE_LIST = "rule_list"
    WORD_LIST = "word_list"
    CHARSET = "charset"
    DYNAMIC_WORD_LIST = "dynamic_word_list"
    EPHEMERAL_WORD_LIST = "ephemeral_word_list"  # For inline, attack-scoped wordlists
    EPHEMERAL_MASK_LIST = "ephemeral_mask_list"  # For inline, attack-scoped mask lists
    EPHEMERAL_RULE_LIST = "ephemeral_rule_list"  # For inline, attack-scoped rule lists


class AttackResourceFile(Base):
    """Model for attack resource files (wordlists, rules, masks).

    Fields:
        - id (UUID): The ID of the attack resource file.
        - project_id (int | None): The ID of the project that the attack resource file belongs to.
        - file_name (str): The name of the attack resource file.
        - download_url (str): The URL to download the attack resource file.
        - checksum (str): The checksum of the attack resource file.
        - guid (UUID): The GUID of the attack resource file.
        - resource_type (AttackResourceType): The type of the attack resource file.
        - line_format (str): The format of the attack resource file.
        - line_encoding (str): The encoding of the attack resource file.
        - used_for_modes (list[AttackMode]): The modes that the attack resource file is used for.
        - source (str): The source of the attack resource file.
        - line_count (int): The number of lines in the attack resource file.
        - byte_size (int): The size of the attack resource file in bytes.
        - content (dict[str, object] | None): The content of the attack resource file.
        - is_uploaded (bool): Whether the attack resource file is uploaded.
        - file_label (str | None): The label of the attack resource file.
        - tags (list[str] | None): The tags of the attack resource file.

    Notes:
        - The `project_id` field is an optional foreign key to the project that the attack resource file belongs to and is unset if the attack resource file is shared across projects.
        - The `checksum` field is a SHA-256 hash of the file content. It is used to verify the integrity of the file and is provided to the agent to determine if the file needs to be downloaded again.
        - The `content` field is a JSON column that stores the content of an ephemeral attack resource file. This is used for inline wordlists, masks, and rules, which are not stored in file storage system.
        - The `is_uploaded` field is a boolean flag that indicates whether the attack resource file is uploaded to the server.
        - The `file_label` field is a string that is a user-defined override of the file name.
        - The `tags` field is an optional list of user-defined tags for organizating the attack resource files.
    """

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    project_id: Mapped[int | None] = mapped_column(nullable=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    download_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    guid: Mapped[UUID] = mapped_column(default=uuid4, unique=True, nullable=False)
    resource_type: Mapped[AttackResourceType] = mapped_column(
        SQLAEnum(AttackResourceType),
        default=AttackResourceType.WORD_LIST,
        nullable=False,
    )
    line_format: Mapped[str] = mapped_column(
        String(32), nullable=False, default="freeform"
    )
    line_encoding: Mapped[str] = mapped_column(
        String(16), nullable=False, default="utf-8"
    )
    used_for_modes: Mapped[list[AttackMode]] = mapped_column(
        JSON, default=list, nullable=False
    )
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="upload")
    line_count: Mapped[int] = mapped_column(nullable=False, default=0)
    byte_size: Mapped[int] = mapped_column(nullable=False, default=0)
    # New: JSON content for ephemeral/dynamic resources (e.g., inline wordlists, masks)
    content: Mapped[dict[str, object] | None] = mapped_column(
        MutableDict.as_mutable(JSON), nullable=True, default=None
    )
    is_uploaded: Mapped[bool] = mapped_column(nullable=False, default=False)
    file_label: Mapped[str | None] = mapped_column(
        String(50), nullable=True, default=None
    )
    tags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True, default=None)
    # NOTE: Alembic migration required for new resource_type column, metadata columns, and line_count and byte_size columns.

    def __repr__(self) -> str:
        return (
            f"<AttackResourceFile(id={self.id}, file_name={self.file_name}, resource_type={self.resource_type}, "
            f"line_format={self.line_format}, line_encoding={self.line_encoding}, used_for_modes={[m.value for m in self.used_for_modes]}, source={self.source}, "
            f"line_count={self.line_count}, byte_size={self.byte_size}, is_uploaded={self.is_uploaded})>"
        )
