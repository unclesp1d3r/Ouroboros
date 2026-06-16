# Control API (v1)

## Overview

The Control API (`/api/v1/control/*`) is designed for command-line interface (CLI) and Terminal User Interface (TUI) clients. This API provides programmatic access to Ouroboros functionality for automation, scripting, and advanced users who prefer command-line tools.

Key features:

- Campaign management and monitoring
- Batch operations and scripting support
- Hash analysis and guessing
- Real-time monitoring capabilities
- RFC9457-compliant error responses

## Authentication

Control API endpoints require API key authentication via the `Authorization` header:

```http
Authorization: Bearer cst_<user_id>_<random_string>
```

API keys are generated through the web interface and can be scoped with specific permissions. Multiple active keys per user are supported.

## Base URL

All Control API endpoints are prefixed with `/api/v1/control/`.

## Error Handling

The Control API implements [RFC9457](https://datatracker.ietf.org/doc/html/rfc9457) (Problem Details for HTTP APIs) for consistent error responses. All errors are returned as `application/problem+json` with the required fields:

```json
{
  "type": "https://ouroboros.example.com/problems/validation-error",
  "title": "Validation Error",
  "status": 422,
  "detail": "The request contains invalid data",
  "instance": "/api/v1/control/campaigns/123",
  "errors": [
    {
      "field": "name",
      "message": "Campaign name is required"
    }
  ]
}
```

Required fields:

- `type`: URI identifying the problem type
- `title`: Human-readable summary
- `status`: HTTP status code
- `detail`: Human-readable explanation
- `instance`: URI reference to the specific occurrence

## Endpoints

### Campaign Management

#### `GET /api/v1/control/campaigns/`

List campaigns with filtering and pagination support.

**Query Parameters:**

- `page: int` - Page number (default: 1)
- `size: int` - Items per page (default: 20, max: 100)
- `search: str` - Search term for campaign names
- `state: str` - Filter by campaign state (`draft`, `active`, `paused`, `completed`, `archived`)
- `project_id: int` - Filter by project ID

**Response:** `PaginatedResponse[CampaignListResponse]`

**Example:**

```bash
curl -H "Authorization: Bearer cst_123_abc..." \
    "/api/v1/control/campaigns/?state=active&page=1&size=10"
```

#### `POST /api/v1/control/campaigns/`

Create a new campaign.

**Request Body:** `CampaignCreateRequest` **Response:** `CampaignResponse`

**Example:**

```bash
curl -X POST \
    -H "Authorization: Bearer cst_123_abc..." \
    -H "Content-Type: application/json" \
    -d '{"name": "Test Campaign", "hash_list_id": 1, "project_id": 1}' \
    "/api/v1/control/campaigns/"
```

#### `GET /api/v1/control/campaigns/{id}`

Get detailed campaign information including attacks and progress.

**Parameters:**

- `id: int` - Campaign ID

**Response:** `CampaignDetailResponse`

#### `PATCH /api/v1/control/campaigns/{id}`

Update campaign configuration.

**Parameters:**

- `id: int` - Campaign ID

**Request Body:** `CampaignUpdateRequest` **Response:** `CampaignResponse`

#### `DELETE /api/v1/control/campaigns/{id}`

Archive or delete campaign.

**Parameters:**

- `id: int` - Campaign ID

**Response:** `204 No Content`

#### `POST /api/v1/control/campaigns/{id}/start`

Start campaign execution.

**Parameters:**

- `id: int` - Campaign ID

**Response:** `204 No Content`

#### `POST /api/v1/control/campaigns/{id}/stop`

Stop campaign execution.

**Parameters:**

- `id: int` - Campaign ID

**Response:** `204 No Content`

#### `GET /api/v1/control/campaigns/{id}/status`

Get real-time campaign status and progress.

**Parameters:**

- `id: int` - Campaign ID

**Response:** `CampaignStatusResponse`

**Example:**

```bash
# Monitor campaign progress
curl -H "Authorization: Bearer cst_123_abc..." \
    "/api/v1/control/campaigns/123/status"
```

#### `GET /api/v1/control/campaigns/{id}/metrics`

Get campaign performance metrics and statistics.

**Parameters:**

- `id: int` - Campaign ID

**Response:** `CampaignMetricsResponse`

#### `POST /api/v1/control/campaigns/{id}/export`

Export campaign configuration to JSON.

**Parameters:**

- `id: int` - Campaign ID

**Response:** `CampaignExportResponse`

### Hash Analysis

#### `POST /api/v1/control/hash/guess`

Analyze hash input and guess hash types.

**Request Body:** `HashGuessRequest` **Response:** `HashGuessResponse`

**Example:**

```bash
curl -X POST \
    -H "Authorization: Bearer cst_123_abc..." \
    -H "Content-Type: application/json" \
    -d '{"hash_input": "$2b$12$example..."}' \
    "/api/v1/control/hash/guess"
```

#### `POST /api/v1/control/hash/validate`

Validate hash format and compatibility.

**Request Body:** `HashValidationRequest` **Response:** `HashValidationResponse`

### Batch Operations

#### `POST /api/v1/control/campaigns/bulk_start`

Start multiple campaigns simultaneously.

**Request Body:** `BulkCampaignStartRequest` **Response:** `BulkOperationResponse`

#### `POST /api/v1/control/campaigns/bulk_stop`

Stop multiple campaigns simultaneously.

**Request Body:** `BulkCampaignStopRequest` **Response:** `BulkOperationResponse`

#### `GET /api/v1/control/campaigns/bulk_status`

Get status of multiple campaigns.

**Query Parameters:**

- `campaign_ids: List[int]` - Comma-separated campaign IDs

**Response:** `BulkCampaignStatusResponse`

### System Information

#### `GET /api/v1/control/system/health`

Get system health and component status.

**Response:** `SystemHealthResponse`

#### `GET /api/v1/control/system/stats`

Get system-wide statistics and metrics.

**Response:** `SystemStatsResponse`

#### `GET /api/v1/control/agents/summary`

Get agent fleet summary and status.

**Response:** `AgentSummaryResponse`

## Schema Objects

### Shared Schemas

::: app.schemas.shared.PaginatedResponse options: show_root_heading: true show_source: false

## Usage Examples

### Basic Campaign Management

```bash
# List active campaigns
curl -H "Authorization: Bearer cst_123_abc..." \
    "/api/v1/control/campaigns/?state=active"

# Get campaign details
curl -H "Authorization: Bearer cst_123_abc..." \
    "/api/v1/control/campaigns/123"

# Start a campaign
curl -X POST \
    -H "Authorization: Bearer cst_123_abc..." \
    "/api/v1/control/campaigns/123/start"

# Monitor progress
curl -H "Authorization: Bearer cst_123_abc..." \
    "/api/v1/control/campaigns/123/status"
```

### Hash Analysis

```bash
# Analyze unknown hash
curl -X POST \
    -H "Authorization: Bearer cst_123_abc..." \
    -H "Content-Type: application/json" \
    -d '{"hash_input": "5d41402abc4b2a76b9719d911017c592"}' \
    "/api/v1/control/hash/guess"
```

### Batch Operations

```bash
# Start multiple campaigns
curl -X POST \
    -H "Authorization: Bearer cst_123_abc..." \
    -H "Content-Type: application/json" \
    -d '{"campaign_ids": [123, 124, 125]}' \
    "/api/v1/control/campaigns/bulk_start"

# Check status of multiple campaigns
curl -H "Authorization: Bearer cst_123_abc..." \
    "/api/v1/control/campaigns/bulk_status?campaign_ids=123,124,125"
```

## Rate Limiting

Control API endpoints are subject to rate limiting to prevent abuse:

- **Standard endpoints**: 100 requests per minute per API key
- **Bulk operations**: 10 requests per minute per API key
- **Status/monitoring endpoints**: 300 requests per minute per API key

Rate limit headers are included in responses:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

## Pagination

List endpoints support pagination with standard query parameters:

- `page: int` - Page number (1-based, default: 1)
- `size: int` - Items per page (default: 20, max: 100)

Responses include pagination metadata:

```json
{
  "items": [],
  "total": 150,
  "page": 1,
  "size": 20,
  "pages": 8
}
```

## Filtering and Searching

Many endpoints support filtering and searching:

- `search: str` - Full-text search across relevant fields
- `state: str` - Filter by entity state
- `project_id: int` - Filter by project (where applicable)
- `created_after: datetime` - Filter by creation date
- `created_before: datetime` - Filter by creation date

## API Key Management

API keys for the Control API are managed through the web interface:

1. Navigate to User Settings → API Keys
2. Click "Generate New Key"
3. Configure permissions and expiration
4. Copy the generated key (shown only once)

Key features:

- Multiple active keys per user
- Configurable permissions and scopes
- Optional expiration dates
- Usage monitoring and logging
- Emergency revocation capabilities

## Future Enhancements

The Control API is designed for extensibility. Planned features include:

- **Streaming responses**: Long-running operations with progress updates
- **WebSocket support**: Real-time monitoring and notifications
- **Advanced filtering**: Complex query syntax for power users
- **Export formats**: Multiple output formats (JSON, CSV, XML)
- **Webhook integration**: Event-driven automation
- **Template management**: Campaign and attack templates

## Compatibility

The Control API follows semantic versioning and maintains backward compatibility within major versions. Breaking changes will be introduced only in new major versions with appropriate migration guides.
