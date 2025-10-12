# Design Document

## Overview

The Agent API v2 is a modernized RESTful API that enables secure communication between Ouroboros agents and the central server. This API provides endpoints for agent registration, authentication, task management, and result reporting while maintaining backward compatibility with the existing v1 agent API.

The design follows FastAPI best practices with service layer architecture, comprehensive input validation, and proper error handling. The API supports both the new v2 endpoints and legacy v1 endpoints to ensure smooth migration for existing agent deployments.

## Architecture

### API Structure

The Agent API v2 follows a layered architecture pattern:

```
┌─────────────────────────────────────────┐
│           API Endpoints (v2)            │
│     /api/v2/client/agents/*             │
└─────────────────────────────────────────┘
                    │
┌─────────────────────────────────────────┐
│          Service Layer                  │
│    app/core/services/agent_service.py   │
└─────────────────────────────────────────┘
                    │
┌─────────────────────────────────────────┐
│         Data Layer                      │
│    SQLAlchemy Models + PostgreSQL       │
└─────────────────────────────────────────┘
```

### Endpoint Organization

**Agent API v2 Endpoints** (`/api/v2/client/agents/`):

- `POST /register` - Agent registration
- `POST /heartbeat` - Agent heartbeat and state updates
- `GET /attacks/{attack_id}` - Attack configuration retrieval
- `GET /tasks/next` - Task assignment
- `POST /tasks/{task_id}/progress` - Progress updates
- `POST /tasks/{task_id}/results` - Result submission
- `GET /resources/{resource_id}/url` - Presigned URL generation

**Legacy API v1 Endpoints** (`/api/v1/client/`):

- Maintained for backward compatibility
- Existing endpoints preserved with identical behavior
- Gradual migration path for existing agents

## Components and Interfaces

### Authentication System

**Token Format**: `csa_<agent_id>_<random_token>`

- Prefix `csa_` identifies agent tokens
- Agent ID enables quick lookup
- Random token provides cryptographic security

**Authentication Flow**:

1. Agent registers with signature, hostname, and type
2. Server generates unique token and stores agent record
3. Agent includes token in `Authorization: Bearer <token>` header
4. Server validates token and associates requests with agent

**Token Validation Service**:

```python
async def validate_agent_token(authorization: str, db: AsyncSession) -> Agent:
    if not authorization.startswith("Bearer csa_"):
        raise InvalidAgentTokenError("Invalid token format")

    token = authorization.removeprefix("Bearer ").strip()
    agent = await db.execute(select(Agent).filter(Agent.token == token))

    if not agent:
        raise InvalidAgentTokenError("Invalid agent token")

    return agent.scalar_one()
```

### Agent Registration

**Registration Process**:

1. Agent submits registration request with metadata
2. Server validates input and checks for existing agents
3. Server creates agent record with pending state
4. Server generates secure token and returns credentials
5. Agent stores token for subsequent requests

**Registration Schema**:

```python
class AgentRegisterRequestV2(BaseModel):
    signature: str = Field(..., description="Unique agent signature")
    hostname: str = Field(..., description="Agent hostname")
    agent_type: AgentType = Field(..., description="Agent type")
    operating_system: OperatingSystemEnum = Field(..., description="OS")
    capabilities: dict[str, Any] | None = Field(None, description="Agent capabilities")
```

### Heartbeat System

**Heartbeat Mechanism**:

- Agents send heartbeats every 15-60 seconds
- Rate limiting prevents abuse (max 1 per 15 seconds)
- Updates `last_seen_at`, `last_ipaddress`, and agent state
- Tracks missed heartbeats for connection monitoring

**State Management**:

- `pending` - Newly registered, awaiting benchmark
- `active` - Online and available for tasks
- `error` - Encountered error, needs attention
- `offline` - Disconnected or shutdown

**Heartbeat Processing**:

```python
async def process_heartbeat(
    request: Request, data: AgentHeartbeatRequest, agent: Agent, db: AsyncSession
) -> None:
    agent.last_seen_at = datetime.now(UTC)
    agent.last_ipaddress = request.client.host
    agent.state = data.state

    await db.commit()
    await broadcast_agent_update(agent.id)
```

### Task Distribution System

**Task Assignment Logic**:

1. Agent requests next available task
2. Server checks agent capabilities against hash types
3. Server finds suitable task from active campaigns
4. Server assigns task with keyspace chunk
5. Server returns task configuration and resources

**Capability Validation**:

```python
async def can_handle_hash_type(
    agent_id: int, hash_type_id: int, db: AsyncSession
) -> bool:
    benchmark = await db.execute(
        select(HashcatBenchmark)
        .where(HashcatBenchmark.agent_id == agent_id)
        .where(HashcatBenchmark.hash_type_id == hash_type_id)
    )
    return benchmark.scalar_one_or_none() is not None
```

**Task Assignment Constraints**:

- One task per agent maximum
- Agent must have benchmark for hash type
- Task must be from active campaign
- Keyspace must be available for assignment

### Progress Tracking

**Progress Updates**:

- Agents report progress percentage and keyspace processed
- Updates stored in task record for monitoring
- Real-time updates via Server-Sent Events
- Progress validation prevents invalid values

**Progress Schema**:

```python
class TaskProgressUpdateV2(BaseModel):
    progress_percent: float = Field(..., ge=0, le=100)
    keyspace_processed: int = Field(..., ge=0)
    estimated_completion: datetime | None = None
    current_speed: float | None = Field(None, ge=0)
```

### Result Collection

**Result Submission**:

- Agents submit cracked hashes with metadata
- Results validated against hash list
- Duplicate detection prevents redundant storage
- Campaign statistics updated automatically

**Result Processing**:

1. Validate agent authorization for task
2. Parse and validate cracked hash data
3. Update HashItem with plain text
4. Create CrackResult record
5. Update campaign progress statistics
6. Broadcast success notification

### Resource Management

**Presigned URL Generation**:

- Secure access to wordlists, rules, and masks
- Time-limited URLs (default 1 hour)
- Hash verification for integrity
- MinIO/S3 compatible storage

**Resource Access Flow**:

1. Agent requests resource URL
2. Server validates agent authorization
3. Server generates presigned URL
4. Agent downloads resource using URL
5. Agent verifies hash before use

## Data Models

> [!NOTE]
> The model examples below use SQLAlchemy Column definitions with proper types (Integer, JSON, DateTime(timezone=True), etc.) instead of Pydantic Field(...) syntax. This ensures the examples reflect valid SQLAlchemy model code with appropriate defaults, nullable attributes, and timezone-aware DateTime columns.

### Agent Model Extensions

**New Fields for v2**:

```python
from sqlalchemy import Column, Integer, JSON, DateTime, Boolean
from sqlalchemy.sql import func


class Agent(Base):
    # Existing fields...
    api_version = Column(Integer, nullable=False, default=2, server_default="2")
    capabilities = Column(JSON, nullable=True)
    last_heartbeat_at = Column(DateTime(timezone=True), nullable=True)
    missed_heartbeats = Column(Integer, nullable=False, default=0, server_default="0")
```

### Task Model Updates

**Enhanced Task Tracking**:

```python
from sqlalchemy import Column, BigInteger, DateTime, Float, CheckConstraint


class Task(Base):
    # Existing fields...
    keyspace_start = Column(BigInteger, nullable=False)
    keyspace_end = Column(BigInteger, nullable=False)
    estimated_completion = Column(DateTime(timezone=True), nullable=True)
    current_speed = Column(Float, nullable=True)

    __table_args__ = (
        CheckConstraint("keyspace_end >= keyspace_start", name="valid_keyspace_range"),
        {"comment": "Tasks with BigInteger keyspace support and range validation"},
    )
```

### Authentication Token Model

**Token Management**:

```python
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func


class AgentToken(Base):
    id = Column(Integer, primary_key=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    token_hash = Column(String, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        server_default=func.now(),
    )
    expires_at = Column(DateTime(timezone=True), nullable=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, server_default="true")
```

## Error Handling

### Error Response Format

**Standardized Error Responses**:

```python
class APIErrorResponse(BaseModel):
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable message")
    details: dict[str, Any] | None = Field(None, description="Additional details")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
```

### Error Categories

**Authentication Errors (401)**:

- Invalid or missing token
- Expired token
- Malformed authorization header

**Authorization Errors (403)**:

- Agent not authorized for resource
- Insufficient permissions
- Disabled agent account

**Validation Errors (422)**:

- Invalid request payload
- Missing required fields
- Invalid enum values

**Rate Limiting Errors (429)**:

- Too many heartbeats
- Excessive API requests
- Temporary throttling

**Resource Errors (404/409)**:

- Task not found
- Agent not found
- Resource conflicts

### Error Handling Strategy

**Service Layer Error Handling**:

```python
async def register_agent_service(
    data: AgentRegisterRequest, db: AsyncSession
) -> AgentRegisterResponse:
    try:
        # Registration logic
        return AgentRegisterResponse(agent_id=agent.id, token=token)
    except IntegrityError as e:
        if "unique constraint" in str(e):
            raise AgentAlreadyExistsError("Agent with this signature already exists")
        raise DatabaseError("Registration failed") from e
    except Exception as e:
        logger.error(f"Unexpected error in agent registration: {e}")
        raise InternalServerError("Registration failed") from e
```

**Endpoint Error Translation**:

```python
@router.post("/register")
async def register_agent(
    data: AgentRegisterRequest, db: AsyncSession
) -> AgentRegisterResponse:
    try:
        return await register_agent_service(data, db)
    except AgentAlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail="Internal server error")
```

## Testing Strategy

### Unit Testing

**Service Layer Tests**:

- Mock database dependencies
- Test business logic in isolation
- Validate error handling paths
- Test edge cases and boundary conditions

**Test Structure**:

```python
@pytest.mark.asyncio
async def test_register_agent_service_success():
    # Arrange
    mock_db = AsyncMock()
    request_data = AgentRegisterRequest(
        signature="test-sig",
        hostname="test-host",
        agent_type=AgentType.physical,
        operating_system=OperatingSystemEnum.linux,
    )

    # Act
    result = await register_agent_service(request_data, mock_db)

    # Assert
    assert result.agent_id > 0
    assert result.token.startswith("csa_")
    mock_db.commit.assert_called_once()
```

### Integration Testing

**API Endpoint Tests**:

- Test complete request/response cycle
- Use real database with test data
- Validate HTTP status codes and headers
- Test authentication and authorization

**Database Integration**:

```python
@pytest.mark.asyncio
async def test_agent_registration_endpoint(
    client: AsyncClient, db_session: AsyncSession
):
    # Arrange
    payload = {
        "signature": "integration-test-sig",
        "hostname": "test-host",
        "agent_type": "physical",
        "operating_system": "linux",
    }

    # Act
    response = await client.post("/api/v2/client/agents/register", json=payload)

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert "agent_id" in data
    assert "token" in data
    assert data["token"].startswith("csa_")

    # Verify database state
    agent = await db_session.get(Agent, data["agent_id"])
    assert agent is not None
    assert agent.host_name == "test-host"
```

### Contract Testing

**API Specification Validation**:

- Validate responses against OpenAPI schema
- Test backward compatibility with v1 API
- Verify error response formats
- Test rate limiting behavior

**Backward Compatibility Tests**:

```python
@pytest.mark.asyncio
async def test_v1_api_compatibility(client: AsyncClient):
    # Test that v1 endpoints still work
    response = await client.get(
        "/api/v1/client/authenticate", headers={"Authorization": "Bearer csa_123_token"}
    )

    # Should match existing v1 response format exactly
    assert response.status_code in [200, 401]
    if response.status_code == 200:
        data = response.json()
        assert "authenticated" in data
        assert "agent_id" in data
```

### Performance Testing

**Load Testing Scenarios**:

- Multiple agents registering simultaneously
- High-frequency heartbeat processing
- Concurrent task assignments
- Bulk result submissions

**Performance Benchmarks**:

- Registration: < 100ms per request
- Heartbeat: < 50ms per request
- Task assignment: < 200ms per request
- Result submission: < 500ms per request

## Security Considerations

### Authentication Security

**Token Security**:

- Cryptographically secure random tokens
- Minimum 128-bit entropy
- No predictable patterns
- Secure storage with hashing

**Token Lifecycle**:

- Optional expiration dates
- Token revocation capability
- Usage tracking and monitoring
- Automatic cleanup of expired tokens

### Input Validation

**Request Validation**:

- Pydantic models for all inputs
- Field-level validation rules
- SQL injection prevention
- XSS protection for string fields

**Rate Limiting**:

- Per-agent rate limits
- Global system rate limits
- Exponential backoff for violations
- Temporary blocking for abuse

### Network Security

**Transport Security**:

- HTTPS required for all communications
- TLS 1.2+ minimum version
- Certificate validation
- HSTS headers for web clients

**API Security Headers**:

```python
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response
```

## Deployment Considerations

### Configuration Management

**Environment Variables**:

```bash
# Agent API Configuration
AGENT_TOKEN_EXPIRY_HOURS=24
AGENT_HEARTBEAT_TIMEOUT_SECONDS=300
AGENT_MAX_MISSED_HEARTBEATS=3
AGENT_RATE_LIMIT_PER_MINUTE=60

# Resource Management
RESOURCE_PRESIGNED_URL_EXPIRY_HOURS=1
RESOURCE_MAX_FILE_SIZE_MB=1024
```

### Monitoring and Observability

**Metrics Collection**:

- Agent registration rate
- Heartbeat frequency and failures
- Task assignment latency
- Result submission rate
- Error rates by endpoint

**Logging Strategy**:

```python
logger.info(
    "Agent registered",
    extra={
        "agent_id": agent.id,
        "host_name": agent.host_name,  # Use schema field name
        "agent_type": agent.agent_type.value,
        "ip_address": request.client.host,
    },
)
```

**Security Note**: The logging system automatically redacts sensitive fields like `authorization`, `token`, and other credential-related data from all log messages. This prevents accidental exposure of sensitive information in logs.

### Scalability Planning

**Horizontal Scaling**:

- Stateless API design
- Database connection pooling
- Redis for session storage
- Load balancer compatibility

**Performance Optimization**:

- Database query optimization
- Connection pooling
- Async request processing
- Caching for frequently accessed data

## Migration Strategy

### Backward Compatibility

**Dual API Support**:

- v1 and v2 APIs run simultaneously
- Shared service layer for common operations
- Gradual migration of agents
- Feature parity maintenance

**Migration Path**:

1. Deploy v2 API alongside v1
2. Update agent software to support v2
3. Migrate agents in phases
4. Monitor for compatibility issues
5. Deprecate v1 API after full migration

### Data Migration

**Database Schema Updates**:

- Add new fields with default values
- Maintain existing field compatibility
- Create migration scripts for data transformation
- Backup and rollback procedures

**Configuration Migration**:

- Update agent configuration files
- Provide migration tools
- Document breaking changes
- Support both formats during transition
