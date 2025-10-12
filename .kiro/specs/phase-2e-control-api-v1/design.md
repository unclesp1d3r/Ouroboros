# Design Document

## Overview

The Control API v1 is a machine-readable REST API that provides programmatic access to all Ouroboros functionality. It serves as the backend for the `csadmin` command-line tool and enables automation scripts, third-party integrations, and monitoring systems to interact with Ouroboros programmatically.

The design philosophy emphasizes maximum reuse of existing service layer functions, consistent behavior with the Web UI API, and machine-optimized response formats. The API uses API key authentication, RFC9457-compliant error handling, and offset-based pagination suitable for programmatic consumption.

## Architecture

### Service Layer Reuse Strategy

The Control API is designed as a thin wrapper around existing service layer functions to minimize development effort and ensure consistency:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web UI API    │    │  Control API    │    │   Agent API     │
│  /api/v1/web/*  │    │/api/v1/control/*│    │/api/v1/client/* │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │  Service Layer  │
                    │ app/core/services/│
                    └─────────────────┘
                                 │
                    ┌─────────────────┐
                    │  Data Layer     │
                    │ SQLAlchemy ORM  │
                    └─────────────────┘
```

### Key Design Principles

1. **Service Layer Reuse**: All endpoints delegate to existing service functions
2. **Schema Compatibility**: Reuse existing Pydantic schemas where possible
3. **Consistent Behavior**: Maintain same business logic as Web UI API
4. **Machine Optimization**: JSON-only responses, offset pagination, structured errors
5. **Security Parity**: Same authentication and authorization rules as Web UI

## Components and Interfaces

### Authentication System

**API Key Format**: `cst_<user_id>_<random_string>`

```python
# Database Schema Addition
class User(Base):
    # ... existing fields ...
    api_key: Mapped[str | None] = mapped_column(
        String(128), unique=True, nullable=True, index=True
    )


# Authentication Dependency
async def get_current_control_user(
    authorization: str = Header(None), db: AsyncSession = Depends(get_db)
) -> User:
    """Authenticate user via API key with project associations."""
    # Validate Bearer token format
    # Lookup user by api_key
    # Load project associations
    # Return authenticated user
```

### Error Handling System

**RFC9457 Problem Details Format**:

```json
{
  "type": "campaign-not-found",
  "title": "Campaign Not Found",
  "status": 404,
  "detail": "Campaign with ID 'camp_123' does not exist or is not accessible",
  "instance": "/api/v1/control/campaigns/camp_123"
}
```

**Custom Exception Classes**:

```python
from fastapi_problem.error import NotFoundProblem, BadRequestProblem


class CampaignNotFoundError(NotFoundProblem):
    title = "Campaign Not Found"


class InvalidAttackConfigError(BadRequestProblem):
    title = "Invalid Attack Configuration"
```

### Project Scoping System

**Access Control Utilities**:

```python
async def get_user_accessible_projects(user: User, db: AsyncSession) -> list[int]:
    """Get list of project IDs that the user has access to."""


async def filter_campaigns_by_project_access(
    query: Select, user: User, db: AsyncSession
) -> Select:
    """Add project filtering to campaign queries."""
```

### Pagination System

**Offset-Based Pagination**:

```python
# Request Parameters
offset: int = 0  # Starting record
limit: int = 10  # Number of records

# Response Format (reusing existing PaginatedResponse)
{"items": [...], "total": 150, "page": 1, "page_size": 10}


# Conversion Utilities
def control_to_web_pagination(offset: int, limit: int) -> tuple[int, int]:
    """Convert offset-based to page-based pagination."""
    page = (offset // limit) + 1
    page_size = limit
    return page, page_size
```

## Data Models

### Reused Schemas

The Control API reuses existing Pydantic schemas from the Web UI API:

- **Campaign Management**: `CampaignRead`, `CampaignCreate`, `CampaignUpdate`
- **Attack Management**: `AttackRead`, `AttackCreate`, `AttackUpdate`
- **User Management**: `UserRead`, `UserCreate`, `UserUpdate`
- **Project Management**: `ProjectRead`, `ProjectCreate`, `ProjectUpdate`
- **Agent Management**: `AgentRead`, `AgentUpdate`
- **Template Management**: `CampaignTemplate`, `AttackTemplate`
- **Pagination**: `PaginatedResponse[T]`, `OffsetPagination`

### New Control-Specific Schemas

```python
# API Key Information (without exposing actual key)
class ApiKeyInfo(BaseModel):
    has_key: bool
    key_prefix: str | None  # e.g., "cst_123_..."
    created_at: datetime | None
    last_used: datetime | None


# System Health Response
class SystemHealth(BaseModel):
    status: str  # "healthy", "degraded", "unhealthy"
    components: dict[str, ComponentHealth]
    timestamp: datetime


class ComponentHealth(BaseModel):
    status: str
    latency_ms: float | None
    error_message: str | None


# System Statistics
class SystemStats(BaseModel):
    campaigns: CampaignStats
    agents: AgentStats
    tasks: TaskStats
    performance: PerformanceStats
```

## Error Handling

### Error Response Strategy

All errors return RFC9457 Problem Details format using the `fastapi-problem` library:

```python
# Configuration
from fastapi_problem.handler import add_exception_handler, new_exception_handler

eh = new_exception_handler()
add_exception_handler(app, eh)


# Usage in endpoints
@router.get("/campaigns/{campaign_id}")
async def get_campaign(
    campaign_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_control_user),
):
    try:
        campaign = await get_campaign_service(db, campaign_id)
        return campaign
    except CampaignNotFoundError:
        raise CampaignNotFoundError(
            detail=f"Campaign with ID '{campaign_id}' not found"
        )
```

### Error Type Mapping

| HTTP Status | Error Type                | Usage                                           |
| ----------- | ------------------------- | ----------------------------------------------- |
| 400         | `invalid-request`         | Malformed requests, validation errors           |
| 401         | `authentication-required` | Missing or invalid API key                      |
| 403         | `access-denied`           | Insufficient permissions, project access denied |
| 404         | `resource-not-found`      | Campaign, attack, agent, etc. not found         |
| 409         | `resource-conflict`       | State conflicts, referential integrity          |
| 422         | `validation-failed`       | Business rule violations                        |
| 500         | `internal-error`          | Unexpected server errors                        |

## Testing Strategy

### Unit Testing

Test service layer functions independently:

```python
@pytest.mark.asyncio
async def test_create_campaign_service():
    # Test service function directly
    campaign_data = CampaignCreate(...)
    result = await create_campaign_service(db, campaign_data, user)
    assert result.name == campaign_data.name
```

### Integration Testing

Test Control API endpoints with real database:

```python
@pytest.mark.asyncio
async def test_control_create_campaign(client, auth_headers):
    response = await client.post(
        "/api/v1/control/campaigns/",
        json={"name": "Test Campaign", "project_id": 1},
        headers=auth_headers,
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Test Campaign"
```

### Contract Testing

Verify API responses match expected schemas:

```python
def test_campaign_response_schema():
    response = client.get("/api/v1/control/campaigns/1")
    data = response.json()
    # Validate against CampaignRead schema
    campaign = CampaignRead(**data)
    assert campaign.id == 1
```

### Authentication Testing

Test API key authentication and project scoping:

```python
def test_api_key_authentication():
    # Test valid API key
    response = client.get(
        "/api/v1/control/campaigns/", headers={"Authorization": "Bearer cst_123_abc"}
    )
    assert response.status_code == 200

    # Test invalid API key
    response = client.get(
        "/api/v1/control/campaigns/", headers={"Authorization": "Bearer invalid"}
    )
    assert response.status_code == 401
```

## Implementation Phases

### Phase 1: Foundation (Core Infrastructure)

- API key authentication system
- RFC9457 error handling
- Project scoping utilities
- Pagination conversion utilities
- Basic endpoint structure

### Phase 2: Core Resources (Building Blocks)

- System health and statistics endpoints
- User management endpoints
- Project management endpoints
- Hash list management endpoints

### Phase 3: Attack Resources (Content Management)

- Resource file management endpoints
- Hash type detection endpoints
- Template import/export endpoints

### Phase 4: Campaign and Attack Management (Core Business Logic)

- Campaign management endpoints
- Attack management endpoints
- Campaign/attack lifecycle control

### Phase 5: Agent and Task Management (Runtime Operations)

- Agent management endpoints
- Task management endpoints
- Performance monitoring endpoints

### Phase 6: Advanced Features (Enhanced Functionality)

- Crackable upload endpoints
- Live monitoring endpoints
- Advanced analytics endpoints

## Security Considerations

### API Key Security

- API keys use cryptographically secure random generation
- Keys are hashed in database storage
- Keys include user ID for efficient lookup
- Key rotation invalidates old keys immediately
- Failed authentication attempts are logged and rate-limited

### Project Isolation

- All endpoints enforce project scoping
- Users can only access resources from assigned projects
- Admin users respect project boundaries unless explicitly overridden
- Cross-project data leakage is prevented through query filtering

### Input Validation

- All inputs validated using Pydantic schemas
- Business rule validation performed in service layer
- SQL injection prevented through ORM usage
- File uploads validated for type and content

### Rate Limiting

- API key-based rate limiting to prevent abuse
- Different limits for different endpoint categories
- Burst allowances for legitimate automation
- Rate limit headers included in responses

## Performance Considerations

### Caching Strategy

- System health data cached with 30-second TTL
- User project associations cached with 5-minute TTL
- Expensive computations cached with appropriate TTL
- Cache invalidation on relevant data changes

### Database Optimization

- Appropriate indexes on frequently queried fields
- Query optimization for list endpoints
- Connection pooling for concurrent requests
- Read replicas for read-heavy operations

### Response Optimization

- Pagination to limit response sizes
- Field selection for large objects
- Compression for large responses
- Streaming for file downloads

### Monitoring and Alerting

- Response time monitoring for all endpoints
- Error rate tracking and alerting
- API key usage monitoring
- Resource utilization tracking

## Deployment Considerations

### Configuration

- API key settings in environment variables
- Rate limiting configuration
- Cache backend configuration (Redis/memory)
- Error reporting configuration

### Documentation

- OpenAPI specification generation
- API key management documentation
- Integration examples and tutorials
- Error handling guidance

### Monitoring

- Health check endpoints for load balancers
- Metrics collection for observability
- Log aggregation for debugging
- Performance monitoring dashboards
