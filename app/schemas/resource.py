from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.attack import AttackMode
from app.models.attack_resource_file import AttackResourceType

from .shared import PaginatedResponse

EDITABLE_RESOURCE_TYPES: set[AttackResourceType] = {
    AttackResourceType.MASK_LIST,
    AttackResourceType.RULE_LIST,
    AttackResourceType.WORD_LIST,
    AttackResourceType.CHARSET,
}

EPHEMERAL_RESOURCE_TYPES: set[AttackResourceType] = {
    AttackResourceType.DYNAMIC_WORD_LIST,
    AttackResourceType.EPHEMERAL_WORD_LIST,
    AttackResourceType.EPHEMERAL_MASK_LIST,
    AttackResourceType.EPHEMERAL_RULE_LIST,
}

MAX_FILE_LABEL_LENGTH = 50


class ResourceLine(BaseModel):
    id: Annotated[
        int, Field(description="Unique line identifier (index in file or DB)")
    ]
    index: Annotated[int, Field(description="Line index (0-based)")]
    content: Annotated[str, Field(description="Content of the line")]
    valid: Annotated[
        bool,
        Field(
            description="Whether the line is valid according to resource type validation"
        ),
    ]
    error_message: Annotated[
        str | None, Field(description="Validation error message, if any")
    ] = None


class ResourceLineValidationError(BaseModel):
    line_index: Annotated[int, Field(description="Index of the line with error")]
    content: Annotated[str, Field(description="Content of the line with error")]
    valid: Annotated[bool, Field(default=False, description="Always false for errors")]
    message: Annotated[str, Field(description="Validation error message")]


class ResourceUploadMeta(BaseModel):
    file_name: Annotated[str, Field(description="Original file name")]
    resource_type: Annotated[
        AttackResourceType | None, Field(description="Type of the resource")
    ] = None


class ResourceUploadResponse(BaseModel):
    resource_id: Annotated[UUID, Field(description="UUID of the created resource")]
    presigned_url: Annotated[
        str | None, Field(description="Presigned S3 upload URL (null for text blobs)")
    ]
    resource: Annotated[ResourceUploadMeta, Field(description="Resource metadata")]


class ResourceUploadFormSchema(BaseModel):
    allowed_resource_types: Annotated[
        list[AttackResourceType],
        Field(
            description="Allowed resource types for upload",
            examples=[["mask_list", "rule_list", "word_list", "charset"]],
        ),
    ]
    max_file_size_mb: Annotated[
        int, Field(description="Maximum file size in MB for upload", examples=[1])
    ]
    max_line_count: Annotated[
        int,
        Field(
            description="Maximum number of lines for in-browser editing",
            examples=[5000],
        ),
    ]
    minio_bucket: Annotated[
        str, Field(description="MinIO bucket name", examples=["ouroboros-resources"])
    ]
    minio_endpoint: Annotated[
        str, Field(description="MinIO endpoint", examples=["minio:9000"])
    ]
    minio_secure: bool = Field(description="Whether MinIO uses HTTPS", examples=[False])
    model_config = ConfigDict(extra="ignore")


class ResourceBase(BaseModel):
    id: UUID
    file_name: str
    file_label: str | None = None
    resource_type: AttackResourceType
    line_count: int | None = None
    byte_size: int | None = None
    checksum: str = ""
    updated_at: datetime | None = None
    line_format: str | None = None
    line_encoding: str | None = None
    used_for_modes: list[str] | None = None
    source: str | None = None
    project_id: int | None = None
    unrestricted: bool | None = None  # True if resource is not project-restricted
    is_uploaded: bool = False
    tags: list[str] | None = None
    model_config = ConfigDict(from_attributes=True, extra="ignore")


class ResourcePreviewResponse(ResourceBase):
    preview_lines: list[str]
    preview_error: str | None = None
    max_preview_lines: int


class ResourceContentResponse(ResourceBase):
    content: str
    editable: bool


class ResourceUploadedResponse(ResourceBase):
    """Response for upload verification: resource metadata only."""


class WordlistItem(BaseModel):
    id: UUID
    file_name: str
    line_count: int | None = None


class WordlistDropdownResponse(BaseModel):
    wordlists: list[WordlistItem]


class RulelistItem(BaseModel):
    id: UUID
    file_name: str
    line_count: int | None = None


class RulelistDropdownResponse(BaseModel):
    rulelists: list[RulelistItem]


class ResourceLinesResponse(BaseModel):
    lines: list[ResourceLine]
    resource_id: UUID


class ResourceListItem(ResourceBase):
    pass  # Inherits all fields from ResourceBase


class AttackBasic(BaseModel):
    id: int
    name: str


class ResourceDetailResponse(ResourceBase):
    attacks: list[AttackBasic]


class ResourceListResponse(PaginatedResponse[ResourceListItem]):
    resource_type: AttackResourceType | None = None


class ResourceUpdateRequest(BaseModel):
    file_name: Annotated[str | None, Field(None, description="Resource file name")]
    file_label: Annotated[
        str | None,
        Field(
            None,
            max_length=MAX_FILE_LABEL_LENGTH,
            description=f"Freeform label for the resource (up to {MAX_FILE_LABEL_LENGTH} chars)",
        ),
    ]
    project_id: Annotated[
        int | None, Field(None, description="Project ID to associate with resource")
    ]
    source: Annotated[str | None, Field(None, description="Resource source")]
    unrestricted: Annotated[
        bool | None, Field(None, description="If true, resource is globally accessible")
    ]
    tags: Annotated[
        list[str] | None, Field(None, description="List of user-provided tags")
    ]
    used_for_modes: Annotated[
        list[AttackMode] | None,
        Field(None, description="List of attack modes this resource is used for"),
    ]
    line_format: Annotated[
        str | None, Field(None, description="Line format for resource")
    ]
    line_encoding: Annotated[
        str | None, Field(None, description="Line encoding for resource")
    ]
    model_config = ConfigDict(extra="forbid")


class UploadProcessingStep(BaseModel):
    """Represents a single step in the upload processing pipeline."""

    step_name: Annotated[str, Field(..., description="Name of the processing step")]
    status: Annotated[
        str,
        Field(
            ..., description="Status of this step: pending, running, completed, failed"
        ),
    ]
    started_at: Annotated[
        str | None, Field(None, description="ISO8601 start time for this step")
    ]
    finished_at: Annotated[
        str | None, Field(None, description="ISO8601 finish time for this step")
    ]
    error_message: Annotated[
        str | None, Field(None, description="Error message if step failed")
    ]
    progress_percentage: Annotated[
        int | None,
        Field(None, ge=0, le=100, description="Progress percentage for this step"),
    ]


class UploadStatusOut(BaseModel):
    status: Annotated[
        str,
        Field(
            ..., description="Current status of the upload task", examples=["completed"]
        ),
    ]
    started_at: Annotated[
        str | None,
        Field(
            None, description="ISO8601 start time", examples=["2024-06-01T12:00:00Z"]
        ),
    ]
    finished_at: Annotated[
        str | None,
        Field(
            None, description="ISO8601 finish time", examples=["2024-06-01T12:05:00Z"]
        ),
    ]
    error_count: Annotated[
        int, Field(..., description="Number of errors encountered", examples=[0])
    ]
    hash_type: Annotated[
        str | None,
        Field(None, description="Inferred hash type name", examples=["sha512crypt"]),
    ]
    hash_type_id: Annotated[
        int | None, Field(None, description="Inferred hash type ID", examples=[1800])
    ]
    preview: Annotated[
        list[str],
        Field(
            ...,
            description="Preview of extracted hashes",
            examples=[["abc123", "def456"]],
        ),
    ]
    validation_state: Annotated[
        str,
        Field(
            ...,
            description="Validation state: valid, invalid, partial, pending",
            examples=["valid"],
        ),
    ]
    upload_resource_file_id: Annotated[
        str, Field(..., description="UUID of the upload resource file")
    ]
    upload_task_id: Annotated[int, Field(..., description="ID of the upload task")]

    # Enhanced fields for detailed processing step tracking
    processing_steps: Annotated[
        list[UploadProcessingStep],
        Field(
            default_factory=list,
            description="Detailed information about each processing step",
        ),
    ]
    current_step: Annotated[
        str | None, Field(None, description="Name of the currently executing step")
    ]
    total_hashes_found: Annotated[
        int | None, Field(None, description="Total number of hashes found in the file")
    ]
    total_hashes_parsed: Annotated[
        int | None,
        Field(None, description="Total number of hashes successfully parsed"),
    ]
    campaign_id: Annotated[
        int | None, Field(None, description="ID of the created campaign, if available")
    ]
    hash_list_id: Annotated[
        int | None, Field(None, description="ID of the created hash list, if available")
    ]
    overall_progress_percentage: Annotated[
        int | None,
        Field(
            None,
            ge=0,
            le=100,
            description="Overall progress percentage of the upload task",
        ),
    ]

    model_config = ConfigDict(from_attributes=True)


class UploadErrorEntryOut(BaseModel):
    id: Annotated[int, Field(..., description="ID of the upload error entry")]
    upload_id: Annotated[int, Field(..., description="ID of the upload task")]
    line_number: Annotated[
        int | None, Field(..., description="Line number of the error")
    ]
    raw_line: Annotated[str, Field(..., description="Raw line that caused the error")]
    error_message: Annotated[str, Field(..., description="Error message")]

    model_config = ConfigDict(from_attributes=True)


class UploadErrorEntryListResponse(PaginatedResponse[UploadErrorEntryOut]):
    pass
