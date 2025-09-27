# Agent API v2 Development Guide

## Overview

This guide covers the development of Agent API v2, the modernized interface for CipherSwarm agents. The v2 API provides enhanced features, improved security, and better error handling while maintaining backward compatibility with existing v1 agents.

## Project Structure

### Directory Organization

```
app/api/v2/
├── __init__.py
├── router.py                    # Main v2 API router
└── endpoints/
    ├── __init__.py
    ├── agents.py               # Agent registration and heartbeat
    ├── attacks.py              # Attack configuration
    ├── tasks.py                # Task assignment and progress
    └── resources.py            # Resource management
```

### Router Configuration

The v2 API uses a modular router structure defined in `app/api/v2/router.py`:

```python
from fastapi import APIRouter
from app.api.v2.endpoints.agents import router as agents_router
from app.api.v2.endpoints.attacks import router as attacks_router
from app.api.v2.endpoints.resources import router as resources_router
from app.api.v2.endpoints.tasks import router as tasks_router

api_router = APIRouter()
api_router.include_router(agents_router)
api_router.include_router(attacks_router)
api_router.include_router(tasks_router)
api_router.include_router(resources_router)
```

## Implementation Status

### Completed Components (v2.0.0)

#### ✅ Foundation Infrastructure

- **Router Structure**: Modular endpoint organization with proper FastAPI routing
- **Authentication Framework**: Token validation infrastructure and dependency injection
- **Error Handling**: Structured error responses with proper HTTP status codes
- **Rate Limiting**: Infrastructure for per-agent and global rate limiting

#### ✅ Endpoint Stubs

All endpoint modules have been created with proper documentation and TODO markers:

- `agents.py`: Agent registration and heartbeat endpoints
- `attacks.py`: Attack configuration retrieval
- `tasks.py`: Task assignment, progress tracking, and result submission
- `resources.py`: Secure resource access with presigned URLs

### Planned Implementation

#### 🚧 Phase 1: Core Agent Management

- [ ] Agent registration with secure token generation
- [ ] Heartbeat system with state machine implementation
- [ ] Authentication dependency with token validation
- [ ] Basic error handling and response formatting

#### 🚧 Phase 2: Task Distribution

- [ ] Task assignment with keyspace distribution
- [ ] Progress tracking with real-time updates
- [ ] Result submission with validation and duplicate detection
- [ ] Task lifecycle management

#### 🚧 Phase 3: Advanced Features

- [ ] Attack configuration with capability validation
- [ ] Resource management with presigned URLs
- [ ] Rate limiting with proper headers and backoff
- [ ] Comprehensive monitoring and metrics

#### 🚧 Phase 4: Testing and Documentation

- [ ] Unit tests for all service functions
- [ ] Integration tests for API endpoints
- [ ] Contract tests for API compatibility
- [ ] Performance testing and optimization

## Development Guidelines

### Code Organization

#### Service Layer Pattern

All business logic should be implemented in service functions under `app/core/services/`:

```python
# app/core/services/agent_service.py
async def register_agent_v2_service(
    db: AsyncSession, agent_data: AgentRegisterRequestV2
) -> AgentRegisterResponseV2:
    """Register a new agent with v2 API enhancements."""
    # Implementation here
    pass
```

#### Endpoint Implementation

Endpoints should be thin wrappers around service calls:

```python
# app/api/v2/endpoints/agents.py
@router.post("/register", response_model=AgentRegisterResponseV2)
async def register_agent(
    agent_data: AgentRegisterRequestV2, db: AsyncSession = Depends(get_db)
) -> AgentRegisterResponseV2:
    """Register a new agent with enhanced security."""
    return await register_agent_v2_service(db, agent_data)
```

### Schema Design

#### Request/Response Models

Create v2-specific schemas in `app/schemas/agent_v2.py`:

```python
from pydantic import BaseModel, Field
from typing import Annotated


class AgentRegisterRequestV2(BaseModel):
    signature: Annotated[str, Field(min_length=1, description="Agent signature")]
    hostname: Annotated[str, Field(min_length=1, description="Agent hostname")]
    agent_type: Annotated[str, Field(description="Agent type (e.g., 'hashcat')")]
    operating_system: Annotated[str, Field(description="Operating system")]


class AgentRegisterResponseV2(BaseModel):
    agent_id: Annotated[int, Field(description="Unique agent identifier")]
    token: Annotated[str, Field(description="Authentication token")]
```

### Authentication Implementation

#### Token Format

Agent API v2 uses enhanced bearer tokens:

```
Format: csa_<agent_id>_<random_token>
Example: csa_123_abc123def456789...
```

#### Authentication Dependency

```python
# app/core/deps.py
async def get_current_agent_v2(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
) -> Agent:
    """Validate v2 agent token and return agent."""
    return await validate_agent_token_v2(db, token)
```

### Error Handling

#### Structured Error Responses

```python
class AgentAPIErrorV2(BaseModel):
    error: str
    message: str
    details: dict[str, Any] | None = None
    timestamp: datetime


# Usage in endpoints
@router.post("/heartbeat")
async def agent_heartbeat(
    heartbeat_data: AgentHeartbeatRequestV2,
    agent: Agent = Depends(get_current_agent_v2),
) -> None:
    try:
        await process_heartbeat_v2_service(db, agent, heartbeat_data)
    except RateLimitExceededError as e:
        raise HTTPException(
            status_code=429,
            detail=AgentAPIErrorV2(
                error="rate_limit_exceeded",
                message="Heartbeat sent too frequently",
                details={"retry_after": e.retry_after},
                timestamp=datetime.now(UTC),
            ).model_dump(),
        )
```

### State Machine Implementation

#### Agent States

```python
from enum import Enum


class AgentStateV2(str, Enum):
    REGISTERED = "registered"
    ACTIVE = "active"
    DISCONNECTED = "disconnected"
    RECONNECTING = "reconnecting"
    RETIRED = "retired"


# State transition validation
async def transition_agent_state(agent: Agent, new_state: AgentStateV2) -> bool:
    """Validate and perform agent state transition."""
    valid_transitions = {
        AgentStateV2.REGISTERED: [AgentStateV2.ACTIVE],
        AgentStateV2.ACTIVE: [AgentStateV2.DISCONNECTED, AgentStateV2.RETIRED],
        AgentStateV2.DISCONNECTED: [AgentStateV2.RECONNECTING, AgentStateV2.RETIRED],
        AgentStateV2.RECONNECTING: [AgentStateV2.ACTIVE, AgentStateV2.RETIRED],
        AgentStateV2.RETIRED: [],  # Terminal state
    }

    if new_state not in valid_transitions.get(agent.state, []):
        raise InvalidStateTransitionError(
            f"Cannot transition from {agent.state} to {new_state}"
        )

    agent.state = new_state
    return True
```

### Rate Limiting

#### Implementation Pattern

```python
from fastapi import Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)


@router.post("/heartbeat")
@limiter.limit("4/minute")  # 15-second minimum interval
async def agent_heartbeat(
    request: Request,
    heartbeat_data: AgentHeartbeatRequestV2,
    agent: Agent = Depends(get_current_agent_v2),
) -> None:
    """Process agent heartbeat with rate limiting."""
    await process_heartbeat_v2_service(db, agent, heartbeat_data)
```

## Testing Strategy

### Unit Tests

```python
# tests/unit/test_agent_v2_service.py
@pytest.mark.asyncio
async def test_register_agent_v2_service_success(db_session):
    """Test successful agent registration."""
    agent_data = AgentRegisterRequestV2(
        signature="test_signature",
        hostname="test-host",
        agent_type="hashcat",
        operating_system="linux",
    )

    result = await register_agent_v2_service(db_session, agent_data)

    assert result.agent_id is not None
    assert result.token.startswith("csa_")
    assert len(result.token.split("_")) == 3
```

### Integration Tests

```python
# tests/integration/v2/test_agent_endpoints.py
@pytest.mark.asyncio
async def test_agent_registration_endpoint(async_client):
    """Test agent registration endpoint."""
    response = await async_client.post(
        "/api/v2/client/agents/register",
        json={
            "signature": "test_signature",
            "hostname": "test-host",
            "agent_type": "hashcat",
            "operating_system": "linux",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert "agent_id" in data
    assert "token" in data
    assert data["token"].startswith("csa_")
```

### Contract Tests

```python
# tests/integration/v2/test_agent_contracts.py
def test_agent_registration_response_schema():
    """Validate registration response matches schema."""
    # Test that responses match OpenAPI specification
    # Validate field types, required fields, and constraints
    pass
```

## Migration Strategy

### Backward Compatibility

- v1 and v2 APIs run simultaneously
- No breaking changes to existing v1 endpoints
- Shared service layer for common operations
- Independent authentication systems

### Deployment Strategy

1. **Phase 1**: Deploy v2 infrastructure alongside v1
2. **Phase 2**: Implement core v2 endpoints
3. **Phase 3**: Test v2 functionality with development agents
4. **Phase 4**: Gradual migration of production agents
5. **Phase 5**: Monitor performance and error rates

### Feature Flags

```python
# app/core/config.py
class Settings(BaseSettings):
    ENABLE_AGENT_API_V2: bool = False
    AGENT_V2_RATE_LIMIT_ENABLED: bool = True
    AGENT_V2_TOKEN_EXPIRY_HOURS: int = 24


# Usage in main.py
if settings.ENABLE_AGENT_API_V2:
    from app.api.v2.router import api_router as api_v2_router

    app.include_router(api_v2_router, prefix="/api/v2")
```

## Performance Considerations

### Database Optimization

- Use appropriate indexes for agent lookups
- Implement connection pooling for high concurrency
- Cache frequently accessed agent data
- Optimize token validation queries

### Caching Strategy

```python
from cashews import cache


@cache(ttl=300, key="agent_config:{agent_id}")
async def get_agent_configuration(agent_id: int) -> dict:
    """Cache agent configuration for 5 minutes."""
    return await fetch_agent_config_from_db(agent_id)
```

### Rate Limiting Optimization

- Use Redis for distributed rate limiting
- Implement sliding window algorithms
- Provide proper retry-after headers
- Monitor rate limit violations

## Security Considerations

### Token Security

- Use cryptographically secure random generation
- Implement token expiration and rotation
- Store token hashes, not plaintext
- Audit all token operations

### Input Validation

- Comprehensive Pydantic validation
- SQL injection prevention
- XSS protection for any rendered content
- File upload validation and scanning

### Authorization

- Resource-level access control
- Project-scoped permissions where applicable
- Audit logging for all operations
- Rate limiting per agent and globally

## Monitoring and Observability

### Logging

```python
from app.core.logging import logger


async def register_agent_v2_service(
    db: AsyncSession, agent_data: AgentRegisterRequestV2
) -> AgentRegisterResponseV2:
    """Register a new agent with v2 API enhancements."""
    logger.info(
        "Agent registration attempt",
        signature=agent_data.signature,
        hostname=agent_data.hostname,
        agent_type=agent_data.agent_type,
    )

    try:
        # Registration logic
        result = await create_agent(db, agent_data)

        logger.info(
            "Agent registered successfully",
            agent_id=result.agent_id,
            hostname=agent_data.hostname,
        )

        return result
    except Exception as e:
        logger.error(
            "Agent registration failed", error=str(e), signature=agent_data.signature
        )
        raise
```

### Metrics Collection

- Track registration rates and success/failure ratios
- Monitor heartbeat intervals and missed heartbeats
- Measure task assignment latency and throughput
- Collect error rates by endpoint and error type

## Future Enhancements

### Planned Features

- **Advanced Capability Negotiation**: Dynamic capability matching between agents and tasks
- **Distributed Task Coordination**: Enhanced coordination for multi-agent tasks
- **Enhanced Security Features**: Certificate-based authentication, mutual TLS
- **Performance Optimizations**: Connection pooling, advanced caching strategies
- **Extended Monitoring**: Comprehensive metrics, alerting, and analytics

### API Evolution

- **v3 Planning**: Consider lessons learned from v2 implementation
- **GraphQL Support**: Potential GraphQL interface for complex queries
- **WebSocket Integration**: Real-time bidirectional communication
- **gRPC Support**: High-performance binary protocol for agent communication

## Contributing

### Development Workflow

1. Create feature branch from `main`
2. Implement endpoint with corresponding service function
3. Add comprehensive tests (unit, integration, contract)
4. Update documentation and OpenAPI specs
5. Submit pull request with detailed description

### Code Review Checklist

- [ ] Service layer implementation follows patterns
- [ ] Proper error handling and validation
- [ ] Comprehensive test coverage
- [ ] Documentation updated
- [ ] Security considerations addressed
- [ ] Performance implications considered

### Documentation Requirements

- Update API documentation for new endpoints
- Add examples and usage patterns
- Document breaking changes and migration paths
- Update architectural diagrams and specifications

## Resources

- [Agent API v2 Documentation](../api/agent-api-v2.md)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic v2 Documentation](https://docs.pydantic.dev/latest/)
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [CipherSwarm Architecture Overview](../architecture/overview.md)
