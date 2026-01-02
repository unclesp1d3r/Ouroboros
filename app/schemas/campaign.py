from datetime import datetime
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.campaign import CampaignState
from app.models.task import TaskStatus
from app.schemas.attack import AttackSummary
from app.schemas.shared import AttackTemplate


class CampaignBase(BaseModel):
    """Base schema for campaign operations containing common fields."""

    name: Annotated[
        str,
        Field(
            max_length=128,
            description="Human-readable campaign name. Must be unique within the project.",
            examples=["Corporate Password Audit 2024", "NTLM Hash Recovery"],
        ),
    ]
    description: Annotated[
        str | None,
        Field(
            max_length=1024,
            description="Optional detailed description of the campaign purpose and scope.",
            examples=["Recovering passwords from corporate domain controller dump"],
        ),
    ] = None
    project_id: Annotated[
        int,
        Field(
            description="ID of the project this campaign belongs to. Enforces multi-tenant isolation.",
            gt=0,
            examples=[1, 42],
        ),
    ]
    priority: Annotated[
        int,
        Field(
            description="Campaign execution priority. Higher values are processed first.",
            ge=0,
            le=100,
            examples=[0, 50, 100],
        ),
    ] = 0
    hash_list_id: Annotated[
        int,
        Field(
            description="ID of the hash list containing target hashes for this campaign.",
            gt=0,
            examples=[1, 123],
        ),
    ]
    is_unavailable: Annotated[
        bool,
        Field(
            description="True if the campaign is not yet ready for use. Set during async campaign creation from uploads."
        ),
    ] = False


class CampaignCreate(CampaignBase):
    """Schema for creating a new campaign. All fields from CampaignBase are required."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Corporate Password Audit 2024",
                "description": "Recovering passwords from corporate domain controller dump",
                "project_id": 1,
                "priority": 50,
                "hash_list_id": 123,
                "is_unavailable": False,
            }
        }
    )


class CampaignUpdate(BaseModel):
    """Schema for updating an existing campaign. All fields are optional."""

    name: Annotated[
        str | None,
        Field(
            max_length=128,
            description="Updated campaign name. Must be unique within the project.",
            examples=["Corporate Password Audit 2024 - Phase 2"],
        ),
    ] = None
    description: Annotated[
        str | None,
        Field(
            max_length=1024,
            description="Updated campaign description.",
            examples=["Extended scope to include service accounts"],
        ),
    ] = None
    priority: Annotated[
        int | None,
        Field(
            description="Updated campaign priority. Higher values are processed first.",
            ge=0,
            le=100,
            examples=[75],
        ),
    ] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Corporate Password Audit 2024 - Updated",
                "description": "Extended scope to include service accounts",
                "priority": 75,
            }
        }
    )


class CampaignRead(CampaignBase):
    """Schema for reading campaign data including system-generated fields."""

    id: Annotated[
        int,
        Field(
            description="Unique campaign identifier assigned by the system.",
            examples=[1, 42, 123],
        ),
    ]
    state: Annotated[
        CampaignState,
        Field(
            description="Current campaign execution state. Controls task distribution and agent assignment.",
            examples=["draft", "active", "paused", "completed"],
        ),
    ]
    created_at: Annotated[
        datetime,
        Field(
            description="Timestamp when the campaign was created.",
            examples=["2024-01-01T12:00:00Z"],
        ),
    ]
    updated_at: Annotated[
        datetime,
        Field(
            description="Timestamp when the campaign was last modified.",
            examples=["2024-01-01T15:30:00Z"],
        ),
    ]

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 123,
                "name": "Corporate Password Audit 2024",
                "description": "Recovering passwords from corporate domain controller dump",
                "project_id": 1,
                "priority": 50,
                "hash_list_id": 456,
                "is_unavailable": False,
                "state": "active",
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-01T15:30:00Z",
            }
        },
    )


class CampaignProgress(BaseModel):
    total_tasks: Annotated[
        int, Field(description="Total number of tasks in the campaign")
    ] = 0
    active_agents: Annotated[
        int, Field(description="Number of active agents in the campaign", ge=0)
    ] = 0
    completed_tasks: Annotated[
        int, Field(description="Number of completed tasks in the campaign", ge=0)
    ] = 0
    pending_tasks: Annotated[
        int, Field(description="Number of pending tasks in the campaign", ge=0)
    ] = 0
    active_tasks: Annotated[
        int, Field(description="Number of active tasks in the campaign", ge=0)
    ] = 0
    failed_tasks: Annotated[
        int, Field(description="Number of failed tasks in the campaign", ge=0)
    ] = 0
    percentage_complete: Annotated[
        float, Field(..., description="Percentage of completed tasks", ge=0, le=100)
    ] = 0
    overall_status: Annotated[
        TaskStatus | None,
        Field(description="Overall status of the campaign", ge=0),
    ] = None
    active_attack_id: Annotated[
        int | None,
        Field(..., description="ID of the active attack in the campaign", ge=0),
    ] = None


class CampaignMetrics(BaseModel):
    total_hashes: Annotated[int, Field(description="Total number of hashes")]
    cracked_hashes: Annotated[int, Field(description="Number of cracked hashes")]
    uncracked_hashes: Annotated[int, Field(description="Number of uncracked hashes")]
    percent_cracked: Annotated[float, Field(description="Percentage of cracked hashes")]
    progress_percent: Annotated[float, Field(description="Progress percentage")]


class CampaignArchive(BaseModel):
    id: Annotated[int, Field(description="Campaign ID")]
    state: Annotated[CampaignState, Field(description="Campaign state")]


class CampaignWithAttacks(CampaignRead):
    attacks: Annotated[list[Any], Field(description="List of attacks")]


class CampaignExport(CampaignRead):
    attacks: Annotated[list[Any], Field(description="List of attacks")]
    hash_list_name: Annotated[str | None, Field(description="Hash list name")] = None


class ReorderAttacksRequest(BaseModel):
    attack_ids: Annotated[
        list[int], Field(description="List of attack IDs in the desired order")
    ]


class ReorderAttacksResponse(BaseModel):
    success: Annotated[bool, Field(description="Success")]
    new_order: Annotated[list[int], Field(description="New order of attack IDs")]


class CampaignDetailResponse(BaseModel):
    campaign: Annotated[CampaignRead, Field(description="Campaign")]
    attacks: Annotated[list[AttackSummary], Field(description="List of attacks")]


class CampaignListResponse(BaseModel):
    items: Annotated[list[CampaignRead], Field(description="List of campaigns")]
    total: Annotated[int, Field(description="Total number of campaigns")]
    page: Annotated[int, Field(description="Current page number")]
    size: Annotated[int, Field(description="Number of campaigns per page")]
    total_pages: Annotated[int, Field(description="Total number of pages")]


class CampaignTemplateAttack(AttackTemplate):
    attack_id: Annotated[int, Field(description="Attack ID")]
    template_id: Annotated[int, Field(description="Template ID")]
    priority: Annotated[int, Field(description="Priority")]
    hash_list_id: Annotated[int, Field(description="Hash list ID")]


class CampaignTemplate(BaseModel):
    schema_version: Annotated[str, Field(description="Schema version")]
    name: Annotated[str, Field(description="Campaign name")]
    description: Annotated[str | None, Field(description="Campaign description")] = None
    priority: Annotated[int | None, Field(description="Campaign priority", ge=0)] = None
    hash_list_id: Annotated[int | None, Field(description="Hash list ID")] = None
    attacks: Annotated[
        list[CampaignTemplateAttack], Field(description="List of attacks")
    ]


class CampaignAndAttackSummaries(BaseModel):
    campaign: Annotated[CampaignRead, Field(description="Campaign")]
    attacks: Annotated[list[AttackSummary], Field(description="List of attacks")]
