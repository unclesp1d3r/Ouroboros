from datetime import datetime
from enum import StrEnum
from typing import Annotated, Any, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.attack import AttackMode, AttackState, WordlistSource
from app.models.attack_resource_file import AttackResourceType


class AttackResourceFileOut(BaseModel):
    id: UUID
    download_url: str
    checksum: str
    file_name: str
    guid: UUID
    resource_type: Annotated[
        AttackResourceType, Field(description="Type of resource file")
    ]
    line_format: Annotated[
        str, Field(description="Format of each line in the resource file")
    ]
    line_encoding: Annotated[
        str, Field(description="Encoding of the resource file lines")
    ]
    used_for_modes: Annotated[
        list[AttackMode],
        Field(description="Attack modes this resource is compatible with"),
    ]
    source: Annotated[
        str,
        Field(description="Source of the resource file (upload, generated, linked)"),
    ]
    line_count: Annotated[
        int, Field(description="Number of lines in the resource file")
    ]
    byte_size: Annotated[int, Field(description="Size of the resource file in bytes")]
    content: dict[str, list[str]] | None = (
        None  # List of lines for ephemeral wordlists, masks, and rules; also used for previous passwords wordlist
    )
    is_uploaded: bool = False

    model_config = ConfigDict(from_attributes=True)


class AttackBase(BaseModel):
    """Base schema for attack operations containing common fields."""

    name: Annotated[
        str,
        Field(
            max_length=128,
            description="Human-readable attack name describing the strategy or approach.",
            examples=[
                "Dictionary Attack - Common Passwords",
                "Mask Attack - 8 Digit Numeric",
                "Hybrid Dictionary + Rules",
            ],
        ),
    ]
    description: Annotated[
        str | None,
        Field(
            max_length=1024,
            description="Optional detailed description of the attack strategy and expected outcomes.",
            examples=[
                "Using rockyou.txt wordlist with best64 rules for common password patterns"
            ],
        ),
    ] = None
    state: Annotated[
        AttackState,
        Field(
            description="Current attack execution state. Controls task generation and agent assignment.",
            examples=["pending", "running", "completed", "failed"],
        ),
    ] = AttackState.PENDING
    attack_mode: AttackMode
    attack_mode_hashcat: int = 0
    hash_mode: int = 0
    mask: str | None = None
    increment_mode: bool = False
    increment_minimum: int = 0
    increment_maximum: int = 0
    optimized: bool = False
    slow_candidate_generators: bool = False
    workload_profile: int = 3
    disable_markov: bool = False
    classic_markov: bool = False
    markov_threshold: int = 0
    left_rule: str | None = None
    right_rule: str | None = None
    custom_charset_1: str | None = None
    custom_charset_2: str | None = None
    custom_charset_3: str | None = None
    custom_charset_4: str | None = None
    hash_list_id: int
    hash_list_url: str
    hash_list_checksum: str
    priority: int = 0
    position: int = 0
    start_time: datetime | None = None
    end_time: datetime | None = None
    campaign_id: int | None = None
    template_id: int | None = None


class AttackCreate(AttackBase):
    modifiers: list[str] | None = (
        None  # Dictionary attack modifiers (e.g., change_case, substitute_chars)
    )
    wordlist_source: WordlistSource | None = None  # 'existing' or 'previous_passwords'
    word_list_id: UUID | None = None
    rule_list_id: UUID | None = None
    mask_list_id: UUID | None = None
    wordlist_inline: list[str] | None = None  # Ephemeral wordlist for this attack
    masks_inline: list[str] | None = None  # Ephemeral mask list for this attack

    @staticmethod
    def validate_resource_type_compatibility_static(
        attack_mode: AttackMode | str | None,
        word_list_id: int | None,
        mask_list_id: int | None,
        rule_list_id: int | None,
    ) -> None:
        from app.models.attack import AttackMode

        allowed = {
            AttackMode.DICTIONARY: {"word_list", "rule_list"},
            AttackMode.MASK: {"mask_list"},
            AttackMode.HYBRID_DICTIONARY: {"word_list", "mask_list"},
            AttackMode.HYBRID_MASK: {"mask_list", "word_list"},
        }
        mode = attack_mode
        if mode is not None and not isinstance(mode, AttackMode):
            try:
                mode = AttackMode(mode)
            except ValueError:
                return
        if mode is not None and mode in allowed:
            if word_list_id is not None and "word_list" not in allowed[mode]:
                raise ValueError(f"word_list_id is not allowed for attack_mode {mode}")
            if mask_list_id is not None and "mask_list" not in allowed[mode]:
                raise ValueError(f"mask_list_id is not allowed for attack_mode {mode}")
            if rule_list_id is not None and "rule_list" not in allowed[mode]:
                raise ValueError(f"rule_list_id is not allowed for attack_mode {mode}")

    @model_validator(mode="after")
    def validate_resource_type_compatibility(self) -> Self:
        attack_mode = getattr(self, "attack_mode", None)
        if attack_mode is not None:
            self.validate_resource_type_compatibility_static(
                attack_mode,
                getattr(self, "word_list_id", None),
                getattr(self, "mask_list_id", None),
                getattr(self, "rule_list_id", None),
            )
        return self


class AttackUpdate(BaseModel):
    name: Annotated[str | None, Field(max_length=128)] = None
    description: Annotated[str | None, Field(max_length=1024)] = None
    state: AttackState | None = None
    attack_mode: AttackMode | None = None
    attack_mode_hashcat: int | None = None
    hash_mode: int | None = None
    mask: str | None = None
    increment_mode: bool | None = None
    increment_minimum: int | None = None
    increment_maximum: int | None = None
    optimized: bool | None = None
    slow_candidate_generators: bool | None = None
    workload_profile: int | None = None
    disable_markov: bool | None = None
    classic_markov: bool | None = None
    markov_threshold: int | None = None
    left_rule: str | None = None
    right_rule: str | None = None
    custom_charset_1: str | None = None
    custom_charset_2: str | None = None
    custom_charset_3: str | None = None
    custom_charset_4: str | None = None
    hash_list_id: int | None = None
    word_list_id: UUID | None = None
    rule_list_id: UUID | None = None
    mask_list_id: UUID | None = None
    hash_list_url: str | None = None
    hash_list_checksum: str | None = None
    priority: int | None = None
    position: int | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    campaign_id: int | None = None
    template_id: int | None = None
    modifiers: list[str] | None = (
        None  # Dictionary attack modifiers (e.g., change_case, substitute_chars)
    )
    wordlist_source: WordlistSource | None = None  # 'existing' or 'previous_passwords'
    confirm: bool | None = None  # Required for edit confirmation flow
    wordlist_inline: list[str] | None = None  # Ephemeral wordlist for this attack
    masks_inline: list[str] | None = None  # Ephemeral mask list for this attack

    @model_validator(mode="after")
    def validate_resource_type_compatibility(self) -> Self:
        attack_mode = getattr(self, "attack_mode", None)
        if attack_mode is not None:
            AttackCreate.validate_resource_type_compatibility_static(
                attack_mode,
                getattr(self, "word_list_id", None),
                getattr(self, "mask_list_id", None),
                getattr(self, "rule_list_id", None),
            )
        return self


class AttackOut(BaseModel):
    id: int
    name: str
    description: str | None
    state: AttackState
    attack_mode: AttackMode
    attack_mode_hashcat: int
    hash_mode: int
    mask: str | None
    increment_mode: bool
    increment_minimum: int
    increment_maximum: int
    optimized: bool
    slow_candidate_generators: bool
    workload_profile: int
    disable_markov: bool
    classic_markov: bool
    markov_threshold: int
    left_rule: str | None
    right_rule: str | None
    custom_charset_1: str | None
    custom_charset_2: str | None
    custom_charset_3: str | None
    custom_charset_4: str | None
    hash_list_id: int
    word_list: AttackResourceFileOut | None = None
    rule_list: AttackResourceFileOut | None = None
    mask_list: AttackResourceFileOut | None = None
    hash_list_url: str
    hash_list_checksum: str
    priority: int
    position: int
    start_time: datetime | None
    end_time: datetime | None
    campaign_id: int | None
    template_id: int | None
    modifiers: list[str] | None = (
        None  # Dictionary attack modifiers (e.g., change_case, substitute_chars)
    )

    model_config = ConfigDict(from_attributes=True)


class AttackOutV1(BaseModel):
    id: Annotated[int, Field(..., description="The id of the attack")]
    attack_mode: Annotated[
        str, Field(..., description="Attack mode name")
    ]  # must be str for OpenAPI enum
    attack_mode_hashcat: Annotated[int, Field(..., description="hashcat attack mode")]
    mask: Annotated[
        str | None, Field(default=None, description="A hashcat mask string")
    ]
    increment_mode: Annotated[
        bool, Field(..., description="Enable hashcat increment mode")
    ]
    increment_minimum: Annotated[
        int, Field(..., description="The start of the increment range")
    ]
    increment_maximum: Annotated[
        int, Field(..., description="The end of the increment range")
    ]
    optimized: Annotated[bool, Field(..., description="Enable hashcat optimized mode")]
    slow_candidate_generators: Annotated[
        bool, Field(..., description="Enable slow candidate generators")
    ]
    workload_profile: Annotated[
        int, Field(..., description="The hashcat workload profile")
    ]
    disable_markov: Annotated[
        bool, Field(..., description="Disable hashcat markov mode")
    ]
    classic_markov: Annotated[
        bool, Field(..., description="Enable hashcat classic markov mode")
    ]
    markov_threshold: Annotated[
        int, Field(..., description="The hashcat markov threshold")
    ]
    left_rule: Annotated[
        str | None,
        Field(default=None, description="The left-hand rule for combinator attacks"),
    ]
    right_rule: Annotated[
        str | None,
        Field(default=None, description="The right-hand rule for combinator attacks"),
    ]
    custom_charset_1: Annotated[
        str | None,
        Field(default=None, description="Custom charset 1 for hashcat mask attacks"),
    ]
    custom_charset_2: Annotated[
        str | None,
        Field(default=None, description="Custom charset 2 for hashcat mask attacks"),
    ]
    custom_charset_3: Annotated[
        str | None,
        Field(default=None, description="Custom charset 3 for hashcat mask attacks"),
    ]
    custom_charset_4: Annotated[
        str | None,
        Field(default=None, description="Custom charset 4 for hashcat mask attacks"),
    ]
    hash_list_id: Annotated[int, Field(..., description="The id of the hash list")]
    word_list: Annotated[
        AttackResourceFileOut | None,
        Field(default=None, description="Word list resource file"),
    ]
    rule_list: Annotated[
        AttackResourceFileOut | None,
        Field(default=None, description="Rule list resource file"),
    ]
    mask_list: Annotated[
        AttackResourceFileOut | None,
        Field(default=None, description="Mask list resource file"),
    ]
    hash_mode: Annotated[int, Field(..., description="The hashcat hash mode")]
    hash_list_url: Annotated[
        str | None,
        Field(default=None, description="The download URL for the hash list"),
    ]
    hash_list_checksum: Annotated[
        str | None, Field(default=None, description="The MD5 checksum of the hash list")
    ]
    url: Annotated[str | None, Field(default=None, description="The URL to the attack")]
    model_config = ConfigDict(extra="forbid", from_attributes=True)


class AttackMoveDirection(StrEnum):
    UP = "up"
    DOWN = "down"
    TOP = "top"
    BOTTOM = "bottom"


class AttackMoveRequest(BaseModel):
    direction: Annotated[
        AttackMoveDirection, Field(..., description="Direction to move the attack")
    ]


class AttackBulkDeleteRequest(BaseModel):
    attack_ids: Annotated[
        list[int], Field(..., description="List of attack IDs to delete")
    ]


class AttackSummary(BaseModel):
    id: int
    name: str
    attack_mode: AttackMode
    type_label: str
    length: int | None = None
    settings_summary: str
    keyspace: int | None = None
    complexity_score: int | None = None
    comment: str | None = None

    model_config = ConfigDict(from_attributes=True)


class BruteForceMaskRequest(BaseModel):
    charset_options: Annotated[
        list[str],
        Field(description="List of charset options, e.g. ['lowercase', 'numbers']"),
    ]
    length: Annotated[int, Field(description="Length of the mask to generate")]


class AttackResourceEstimationContext(BaseModel):
    wordlist_size: Annotated[
        int, Field(10000, description="Number of words in the wordlist")
    ]
    rule_count: Annotated[int, Field(1, description="Number of rules applied")]
    # Add more fields as needed for future estimation logic


class EstimateAttackRequest(BaseModel):
    """
    Request model for attack keyspace/complexity estimation.
    Accepts partial or full attack config fields for unsaved attacks.
    """

    name: Annotated[
        str | None,
        Field(default=None, description="Attack name", examples=["Test Attack"]),
    ]
    description: Annotated[
        str | None,
        Field(default=None, description="Attack description", examples=["Test"]),
    ]
    state: AttackState | None = None
    hash_type_id: int | None = None
    attack_mode: AttackMode | None = None
    attack_mode_hashcat: int | None = None
    hash_mode: int | None = None
    mask: str | None = None
    increment_mode: bool | None = None
    increment_minimum: int | None = None
    increment_maximum: int | None = None
    optimized: bool | None = None
    slow_candidate_generators: bool | None = None
    workload_profile: int | None = None
    disable_markov: bool | None = None
    classic_markov: bool | None = None
    markov_threshold: int | None = None
    left_rule: str | None = None
    right_rule: str | None = None
    custom_charset_1: str | None = None
    custom_charset_2: str | None = None
    custom_charset_3: str | None = None
    custom_charset_4: str | None = None
    hash_list_id: int | None = None
    hash_list_url: str | None = None
    hash_list_checksum: str | None = None
    priority: int | None = None
    position: int | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    campaign_id: int | None = None
    template_id: int | None = None
    wordlist_size: int | None = None
    rule_count: int | None = None


class EstimateAttackResponse(BaseModel):
    keyspace: Annotated[
        int, Field(description="Estimated keyspace", examples=[1000000])
    ]
    complexity_score: Annotated[
        int, Field(description="Complexity score (1-5)", examples=[3])
    ]


class AttackPerformanceSummary(BaseModel):
    """
    Performance summary for an attack, including speed, progress, and agent participation.
    """

    hashes_per_sec: Annotated[
        float,
        Field(
            ...,
            description="Aggregate hashes per second across all agents",
            examples=[12345.67],
        ),
    ]
    total_hashes: Annotated[
        int,
        Field(..., description="Total number of hashes to process", examples=[1000000]),
    ]
    agent_count: Annotated[
        int,
        Field(
            ...,
            description="Number of agents participating in the attack",
            examples=[3],
        ),
    ]
    eta: Annotated[
        int | None,
        Field(
            None, description="Estimated time to completion in seconds", examples=[3600]
        ),
    ]
    progress: Annotated[
        float, Field(..., description="Progress percentage (0-100)", examples=[42.5])
    ]
    hashes_done: Annotated[
        int,
        Field(..., description="Number of hashes processed so far", examples=[425000]),
    ]
    attack: Annotated[AttackOut, Field(..., description="Attack details")]


class AttackEditorContext(BaseModel):
    """
    Context for the attack editor modal (empty for new attack or prefilled for import).
    """

    attack: Any = None
    imported: bool = False
    keyspace: int = 0
    complexity: int = 0
    complexity_score: int = 1
    modifiers: list[str] | None = None  # Selected UI modifiers
    rule_file_uuid: str | None = None  # Mapped rule file UUID (if any)


class BruteForceMaskResponse(BaseModel):
    mask: str = Field(
        ..., description="Generated mask string, e.g. '?1?1?1'", examples=["?1?1?1"]
    )
    custom_charset: str = Field(
        ..., description="Custom charset string, e.g. '?1=?l?d'", examples=["?1=?l?d"]
    )


class MaskValidationRequest(BaseModel):
    mask: str = Field(
        ..., description="Hashcat mask string to validate", examples=["?l?l?d?d"]
    )


class MaskValidationResponse(BaseModel):
    valid: bool = Field(..., description="Whether the mask is valid", examples=[True])
    error: str | None = Field(
        None,
        description="Validation error message if invalid",
        examples=["Invalid mask syntax"],
    )
