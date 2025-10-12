# Web UI API (v1)

## Overview

The Web UI API (`/api/v1/web/*`) powers the SvelteKit-based dashboard that human users interact with. These endpoints support views, forms, real-time updates, and administrative functions. Agents do not use these endpoints.

Key features:

- Campaign and attack management
- Agent fleet monitoring
- Resource management (wordlists, rules, masks)
- Real-time progress updates via Server-Sent Events (SSE)
- Hash list management and crackable uploads
- User and project administration

## Authentication

Web UI API endpoints require JWT token authentication via the `Authorization` header:

```http
Authorization: Bearer <jwt_token>
```

Tokens are obtained through the `/api/v1/web/auth/login` endpoint and can be refreshed using `/api/v1/web/auth/refresh`.

## Base URL

All Web UI API endpoints are prefixed with `/api/v1/web/`.

## Endpoints

### Authentication & User Management

#### `POST /api/v1/web/auth/login`

Authenticate user and receive JWT tokens.

**Request Body:** `LoginRequest` **Response:** `LoginResponse` with access and refresh tokens

#### `POST /api/v1/web/auth/logout`

Logout user and invalidate tokens.

**Response:** `204 No Content`

#### `POST /api/v1/web/auth/refresh`

Refresh JWT access token.

**Request Body:** `RefreshRequest` **Response:** `RefreshResponse` with new access token

#### `GET /api/v1/web/auth/me`

Get current user profile details.

**Response:** `UserProfile`

#### `PATCH /api/v1/web/auth/me`

Update current user's name and email.

**Request Body:** `UserProfileUpdate` **Response:** `UserProfile`

#### `POST /api/v1/web/auth/change_password`

Change current user's password.

**Request Body:** `ChangePasswordRequest` **Response:** `204 No Content`

#### `GET /api/v1/web/auth/context`

Get current user and project context.

**Response:** `AuthContext`

#### `POST /api/v1/web/auth/context`

Switch active project context.

**Request Body:** `ProjectContextRequest` **Response:** `AuthContext`

### User Administration (Admin Only)

#### `GET /api/v1/web/users/`

List all users (paginated, filterable).

**Query Parameters:**

- `page: int` - Page number
- `size: int` - Page size
- `search: str` - Search term

**Response:** `PaginatedResponse[UserResponse]`

#### `POST /api/v1/web/users/`

Create new user.

**Request Body:** `UserCreateRequest` **Response:** `UserResponse`

#### `GET /api/v1/web/users/{id}`

Get user details by ID.

**Response:** `UserResponse`

#### `PATCH /api/v1/web/users/{id}`

Update user information or role.

**Request Body:** `UserUpdateRequest` **Response:** `UserResponse`

#### `DELETE /api/v1/web/users/{id}`

Deactivate or delete user.

**Response:** `204 No Content`

### Project Management (Admin Only)

#### `GET /api/v1/web/projects/`

List all projects.

**Response:** `List[ProjectResponse]`

#### `POST /api/v1/web/projects/`

Create new project.

**Request Body:** `ProjectCreateRequest` **Response:** `ProjectResponse`

#### `GET /api/v1/web/projects/{id}`

Get project details.

**Response:** `ProjectResponse`

#### `PATCH /api/v1/web/projects/{id}`

Update project information and user assignments.

**Request Body:** `ProjectUpdateRequest` **Response:** `ProjectResponse`

#### `DELETE /api/v1/web/projects/{id}`

Archive project (soft delete).

**Response:** `204 No Content`

### Campaign Management

#### `GET /api/v1/web/campaigns/`

List campaigns (paginated, filterable).

**Query Parameters:**

- `page: int` - Page number
- `size: int` - Page size
- `search: str` - Search term
- `state: str` - Campaign state filter

**Response:** `PaginatedResponse[CampaignListResponse]`

#### `POST /api/v1/web/campaigns/`

Create new campaign.

**Request Body:** `CampaignCreateRequest` **Response:** `CampaignResponse`

#### `GET /api/v1/web/campaigns/{id}`

Get campaign details with attacks and tasks.

**Response:** `CampaignDetailResponse`

#### `PATCH /api/v1/web/campaigns/{id}`

Update campaign information.

**Request Body:** `CampaignUpdateRequest` **Response:** `CampaignResponse`

#### `DELETE /api/v1/web/campaigns/{id}`

Archive/delete campaign.

**Response:** `204 No Content`

#### `POST /api/v1/web/campaigns/{id}/add_attack`

Add attack to campaign.

**Request Body:** `AttackCreateRequest` **Response:** `AttackResponse`

#### `POST /api/v1/web/campaigns/{id}/start`

Start campaign execution.

**Response:** `204 No Content`

#### `POST /api/v1/web/campaigns/{id}/stop`

Stop campaign execution.

**Response:** `204 No Content`

#### `POST /api/v1/web/campaigns/{id}/reorder_attacks`

Reorder attacks within campaign.

**Request Body:** `AttackReorderRequest` **Response:** `204 No Content`

#### `GET /api/v1/web/campaigns/{id}/progress`

Get campaign progress data for polling.

**Response:** `CampaignProgressResponse`

#### `GET /api/v1/web/campaigns/{id}/metrics`

Get campaign aggregate statistics.

**Response:** `CampaignMetricsResponse`

#### `POST /api/v1/web/campaigns/{id}/relaunch`

Relaunch failed or modified campaign.

**Response:** `204 No Content`

### Attack Management

#### `GET /api/v1/web/attacks/`

List attacks (paginated, searchable).

**Query Parameters:**

- `page: int` - Page number
- `size: int` - Page size
- `search: str` - Search term

**Response:** `PaginatedResponse[AttackListResponse]`

#### `POST /api/v1/web/attacks/`

Create attack with configuration validation.

**Request Body:** `AttackCreateRequest` **Response:** `AttackResponse`

#### `GET /api/v1/web/attacks/{id}`

View attack configuration and performance.

**Response:** `AttackDetailResponse`

#### `PATCH /api/v1/web/attacks/{id}`

Edit attack configuration.

**Request Body:** `AttackUpdateRequest` **Response:** `AttackResponse`

#### `DELETE /api/v1/web/attacks/{id}`

Delete attack.

**Response:** `204 No Content`

#### `POST /api/v1/web/attacks/validate`

Validate attack configuration and estimate keyspace.

**Request Body:** `AttackValidationRequest` **Response:** `AttackValidationResponse`

#### `POST /api/v1/web/attacks/estimate`

Estimate keyspace and complexity for unsaved attack.

**Request Body:** `AttackEstimationRequest` **Response:** `AttackEstimationResponse`

#### `POST /api/v1/web/attacks/{id}/move`

Move attack position within campaign.

**Request Body:** `AttackMoveRequest` **Response:** `204 No Content`

#### `POST /api/v1/web/attacks/{id}/duplicate`

Duplicate attack within campaign.

**Response:** `AttackResponse`

#### `DELETE /api/v1/web/attacks/bulk`

Delete multiple attacks by ID.

**Request Body:** `BulkDeleteRequest` **Response:** `204 No Content`

#### `GET /api/v1/web/attacks/{id}/performance`

Get attack performance diagnostics.

**Response:** `AttackPerformanceResponse`

### Agent Management

#### `GET /api/v1/web/agents/`

List and filter agents.

**Query Parameters:**

- `page: int` - Page number
- `size: int` - Page size
- `search: str` - Search term
- `state: str` - Agent state filter

**Response:** `PaginatedResponse[AgentListResponse]`

#### `POST /api/v1/web/agents/`

Register new agent and return token.

**Request Body:** `AgentCreateRequest` **Response:** `AgentCreateResponse` with token

#### `GET /api/v1/web/agents/{id}`

Get agent detail view.

**Response:** `AgentDetailResponse`

#### `PATCH /api/v1/web/agents/{id}`

Toggle agent enable/disable state.

**Request Body:** `AgentStateUpdateRequest` **Response:** `AgentResponse`

#### `PATCH /api/v1/web/agents/{id}/config`

Update agent configuration toggles.

**Request Body:** `AgentConfigUpdateRequest` **Response:** `204 No Content`

#### `PATCH /api/v1/web/agents/{id}/devices`

Toggle individual backend devices.

**Request Body:** `AgentDeviceUpdateRequest` **Response:** `204 No Content`

#### `POST /api/v1/web/agents/{id}/benchmark`

Trigger new benchmark run.

**Response:** `204 No Content`

#### `GET /api/v1/web/agents/{id}/benchmarks`

View agent benchmark summary.

**Response:** `AgentBenchmarkSummaryResponse`

#### `GET /api/v1/web/agents/{id}/errors`

Fetch agent error log stream.

**Response:** `List[AgentErrorResponse]`

#### `GET /api/v1/web/agents/{id}/performance`

Get agent performance time series data.

**Response:** `AgentPerformanceResponse`

#### `GET /api/v1/web/agents/{id}/hardware`

Get agent hardware details.

**Response:** `AgentHardwareResponse`

#### `PATCH /api/v1/web/agents/{id}/hardware`

Update hardware limits and platform toggles.

**Request Body:** `AgentHardwareUpdateRequest` **Response:** `204 No Content`

#### `GET /api/v1/web/agents/{id}/capabilities`

Show agent benchmark results and capabilities.

**Response:** `AgentCapabilitiesResponse`

#### `POST /api/v1/web/agents/{id}/test_presigned`

Validate presigned URL access for agent.

**Request Body:** `PresignedUrlTestRequest` **Response:** `PresignedUrlTestResponse`

### Resource Management

#### `GET /api/v1/web/resources/`

List all attack resources (filterable by type).

**Query Parameters:**

- `page: int` - Page number
- `size: int` - Page size
- `resource_type: str` - Filter by resource type
- `search: str` - Search term

**Response:** `PaginatedResponse[ResourceListResponse]`

#### `POST /api/v1/web/resources/`

Upload new resource with metadata.

**Request Body:** `ResourceUploadRequest` **Response:** `ResourceUploadResponse` with presigned URL

#### `GET /api/v1/web/resources/{id}`

Get resource metadata and linking information.

**Response:** `ResourceDetailResponse`

#### `PATCH /api/v1/web/resources/{id}`

Update resource metadata.

**Request Body:** `ResourceUpdateRequest` **Response:** `ResourceResponse`

#### `DELETE /api/v1/web/resources/{id}`

Delete resource (if not linked to attacks).

**Response:** `204 No Content`

#### `GET /api/v1/web/resources/{id}/preview`

Get small content preview of resource.

**Response:** `ResourcePreviewResponse`

#### `GET /api/v1/web/resources/{id}/content`

Get raw editable text content.

**Response:** `ResourceContentResponse`

#### `PATCH /api/v1/web/resources/{id}/content`

Save updated resource content.

**Request Body:** `ResourceContentUpdateRequest` **Response:** `204 No Content`

#### `POST /api/v1/web/resources/{id}/refresh_metadata`

Recalculate resource hash, size, and linkage.

**Response:** `204 No Content`

### Line-Oriented Resource Editing

#### `GET /api/v1/web/resources/{id}/lines`

Get paginated list of resource lines.

**Query Parameters:**

- `page: int` - Page number
- `size: int` - Page size
- `validate: bool` - Include validation results

**Response:** `PaginatedResponse[ResourceLineResponse]`

#### `POST /api/v1/web/resources/{id}/lines`

Add new line to resource.

**Request Body:** `ResourceLineCreateRequest` **Response:** `ResourceLineResponse`

#### `PATCH /api/v1/web/resources/{id}/lines/{line_id}`

Update existing resource line.

**Request Body:** `ResourceLineUpdateRequest` **Response:** `ResourceLineResponse`

#### `DELETE /api/v1/web/resources/{id}/lines/{line_id}`

Delete resource line.

**Response:** `204 No Content`

### Hash List Management

#### `GET /api/v1/web/hash_lists/`

List hash lists (paginated, searchable).

**Query Parameters:**

- `page: int` - Page number
- `size: int` - Page size
- `search: str` - Search term

**Response:** `PaginatedResponse[HashListResponse]`

#### `POST /api/v1/web/hash_lists/`

Create new hash list.

**Request Body:** `HashListCreateRequest` **Response:** `HashListResponse`

#### `GET /api/v1/web/hash_lists/{id}`

View hash list details.

**Response:** `HashListDetailResponse`

#### `PATCH /api/v1/web/hash_lists/{id}`

Update hash list information.

**Request Body:** `HashListUpdateRequest` **Response:** `HashListResponse`

#### `DELETE /api/v1/web/hash_lists/{id}`

Delete hash list.

**Response:** `204 No Content`

#### `GET /api/v1/web/hash_lists/{id}/items`

List hash items in hash list.

**Query Parameters:**

- `page: int` - Page number
- `size: int` - Page size
- `search: str` - Search term
- `status: str` - Filter by cracked/uncracked

**Response:** `PaginatedResponse[HashItemResponse]`

### Crackable Uploads

#### `POST /api/v1/web/uploads/`

Upload file or paste hash blob for processing.

**Request Body:** `UploadRequest` (multipart or JSON) **Response:** `UploadResponse` with upload ID and task ID

#### `GET /api/v1/web/uploads/{id}/status`

Get upload analysis status and results.

**Response:** `UploadStatusResponse`

#### `POST /api/v1/web/uploads/{id}/launch_campaign`

Generate resources and create campaign from upload.

**Request Body:** `LaunchCampaignRequest` **Response:** `CampaignResponse`

#### `GET /api/v1/web/uploads/{id}/errors`

Get upload extraction errors and warnings.

**Response:** `UploadErrorResponse`

#### `DELETE /api/v1/web/uploads/{id}`

Remove discarded or invalid upload.

**Response:** `204 No Content`

### Hash Guessing

#### `POST /api/v1/web/hash/guess`

Analyze and guess hash types from input.

**Request Body:** `HashGuessRequest` **Response:** `HashGuessResponse`

### Live Event Feeds (Server-Sent Events)

#### `GET /api/v1/web/live/campaigns`

SSE stream for campaign/attack/task state changes.

**Response:** Server-Sent Events stream

#### `GET /api/v1/web/live/agents`

SSE stream for agent status and performance updates.

**Response:** Server-Sent Events stream

#### `GET /api/v1/web/live/toasts`

SSE stream for crack results and system notifications.

**Response:** Server-Sent Events stream

### UI Support & Utilities

#### `GET /api/v1/web/modals/agents`

Get agent list for dropdown population.

**Response:** `List[AgentOptionResponse]`

#### `GET /api/v1/web/modals/resources`

Get resource list for selector population.

**Query Parameters:**

- `resource_type: str` - Filter by resource type

**Response:** `List[ResourceOptionResponse]`

#### `GET /api/v1/web/modals/hash_types`

Get hash type list for dropdown population.

**Response:** `List[HashTypeOptionResponse]`

#### `GET /api/v1/web/modals/rule_explanation`

Get rule explanation data for modal.

**Query Parameters:**

- `rule: str` - Rule to explain

**Response:** `RuleExplanationResponse`

#### `GET /api/v1/web/dashboard/summary`

Get dashboard summary data for widgets.

**Response:** `DashboardSummaryResponse`

#### `GET /api/v1/web/health/overview`

Get system health overview.

**Response:** `HealthOverviewResponse`

#### `GET /api/v1/web/health/components`

Get detailed health of core services.

**Response:** `HealthComponentsResponse`

### Templates

#### `GET /api/v1/web/templates/`

List attack/campaign templates.

**Response:** `List[TemplateResponse]`

#### `POST /api/v1/web/templates/`

Create new template.

**Request Body:** `TemplateCreateRequest` **Response:** `TemplateResponse`

#### `GET /api/v1/web/templates/{id}`

Get template details.

**Response:** `TemplateDetailResponse`

#### `PATCH /api/v1/web/templates/{id}`

Update template.

**Request Body:** `TemplateUpdateRequest` **Response:** `TemplateResponse`

#### `DELETE /api/v1/web/templates/{id}`

Delete template.

**Response:** `204 No Content`

---

## Schema Objects

### Authentication Schemas

::: app.schemas.user.LoginRequest options: show_root_heading: true show_source: false

::: app.schemas.auth.LoginResult options: show_root_heading: true show_source: false

::: app.schemas.auth.ContextResponse options: show_root_heading: true show_source: false

::: app.schemas.auth.SetContextRequest options: show_root_heading: true show_source: false

### User Schemas

::: app.schemas.user.UserRead options: show_root_heading: true show_source: false

::: app.schemas.user.UserCreate options: show_root_heading: true show_source: false

::: app.schemas.user.UserUpdate options: show_root_heading: true show_source: false

### Project Schemas

::: app.schemas.project.ProjectRead options: show_root_heading: true show_source: false

::: app.schemas.project.ProjectCreate options: show_root_heading: true show_source: false

::: app.schemas.project.ProjectUpdate options: show_root_heading: true show_source: false

### Campaign Schemas

::: app.schemas.campaign.CampaignRead options: show_root_heading: true show_source: false

::: app.schemas.campaign.CampaignCreate options: show_root_heading: true show_source: false

::: app.schemas.campaign.CampaignUpdate options: show_root_heading: true show_source: false

::: app.schemas.campaign.CampaignDetailResponse options: show_root_heading: true show_source: false

::: app.schemas.campaign.CampaignListResponse options: show_root_heading: true show_source: false

::: app.schemas.campaign.CampaignProgress options: show_root_heading: true show_source: false

::: app.schemas.campaign.CampaignMetrics options: show_root_heading: true show_source: false

### Attack Schemas

::: app.schemas.attack.AttackOut options: show_root_heading: true show_source: false

::: app.schemas.attack.AttackCreate options: show_root_heading: true show_source: false

::: app.schemas.attack.AttackUpdate options: show_root_heading: true show_source: false

::: app.schemas.attack.EstimateAttackResponse options: show_root_heading: true show_source: false

::: app.schemas.attack.EstimateAttackRequest options: show_root_heading: true show_source: false

### Agent Schemas

::: app.schemas.agent.AgentOut options: show_root_heading: true show_source: false

::: app.schemas.agent.AgentRegisterRequest options: show_root_heading: true show_source: false

::: app.schemas.agent.AgentRegisterResponse options: show_root_heading: true show_source: false

::: app.schemas.agent.AgentResponse options: show_root_heading: true show_source: false

### Resource Schemas

::: app.schemas.resource.ResourceBase options: show_root_heading: true show_source: false

::: app.schemas.resource.ResourceUploadResponse options: show_root_heading: true show_source: false

::: app.schemas.resource.ResourceUpdateRequest options: show_root_heading: true show_source: false

::: app.schemas.resource.ResourceLinesResponse options: show_root_heading: true show_source: false

::: app.schemas.resource.ResourceDetailResponse options: show_root_heading: true show_source: false

::: app.schemas.resource.ResourceListResponse options: show_root_heading: true show_source: false

### Hash List Schemas

::: app.schemas.hash_list.HashListOut options: show_root_heading: true show_source: false

::: app.schemas.hash_list.HashListCreate options: show_root_heading: true show_source: false

::: app.schemas.hash_item.HashItemOut options: show_root_heading: true show_source: false

### Health Schemas

::: app.schemas.health.SystemHealthOverview options: show_root_heading: true show_source: false

::: app.schemas.health.SystemHealthComponents options: show_root_heading: true show_source: false

::: app.schemas.health.AgentHealthSummary options: show_root_heading: true show_source: false

### Shared Schemas

::: app.schemas.shared.PaginatedResponse options: show_root_heading: true show_source: false

---

## Error Handling

The Web UI API uses standard FastAPI error responses with detailed error information:

```json
{
  "detail": "Error message description"
}
```

For validation errors, the response includes field-specific details:

```json
{
  "detail": [
    {
      "loc": [
        "field_name"
      ],
      "msg": "Field validation error",
      "type": "value_error"
    }
  ]
}
```

Common HTTP status codes:

- `200` - Success
- `201` - Created
- `204` - Success (No Content)
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `409` - Conflict
- `422` - Validation Error
- `500` - Internal Server Error

## Real-time Updates

The Web UI API supports real-time updates through Server-Sent Events (SSE). Clients can subscribe to event streams for:

- Campaign progress updates
- Agent status changes
- New crack results (toast notifications)

SSE endpoints provide lightweight trigger notifications that prompt clients to fetch updated data, rather than pushing complete data through the stream.

## Project Context

All Web UI API endpoints respect project context. Users can only access data within their assigned projects, and all operations are scoped to the currently selected project context. Project context is managed through the `/api/v1/web/auth/context` endpoints.

## Pagination

List endpoints support pagination with standard query parameters:

- `page: int` - Page number (1-based)
- `size: int` - Items per page (default: 20, max: 100)

Responses include pagination metadata in the `PaginatedResponse` wrapper.
