---

## inclusion: always

# Ouroboros Architecture Guide

## Project Overview

Ouroboros is a distributed password cracking management system built with FastAPI and SvelteKit. It coordinates multiple agents running hashcat to efficiently distribute password cracking tasks across a network of machines.

## Critical Requirements

### API Compatibility

**Agent API v1 (`/api/v1/client/*`)**

- MUST follow `contracts/v1_api_swagger.json` (OpenAPI 3.0.1) exactly
- Legacy compatibility with Ruby-on-Rails version
- Breaking changes prohibited
- Contract is authoritative source for all behavior

**Agent API v2 (`/api/v2/client/*`)**

- NOT YET IMPLEMENTED
- Will allow idiomatic FastAPI designs and breaking changes
- Cannot interfere with v1 API

**Testing Requirements**

- Validate API responses against OpenAPI specification
- Contract testing for specification compliance
- Integration tests verify exact schema matches

## Architecture

### Backend Stack

- **FastAPI**: Async Python web framework
- **PostgreSQL 16+**: Primary database with SQLAlchemy ORM
- **Redis**: Caching (Cashews) and task queues (Celery)
- **MinIO**: S3-compatible object storage for attack resources
- **Loguru**: Structured logging (never use standard Python logging)

### Core Domain Models

**Project**: Top-level security boundary isolating all resources
**Campaign**: Coordinated cracking operation targeting a single hash list
**Attack**: Specific hashcat configuration (mode, rules, masks, etc.)
**Task**: Discrete work unit assigned to an agent
**HashList**: Collection of hashes targeted by campaigns
**HashItem**: Individual hash with metadata (salt, username, etc. in JSONB)
**Agent**: Registered client executing tasks with capability benchmarks
**CrackResult**: Successfully cracked hash with discovery metadata
**Session**: Task execution lifecycle tracking
**User**: Authenticated entity with project-scoped permissions

### Key Relationships

- Project → Campaigns (1:many)
- Campaign → HashList (many:1)
- Campaign → Attacks (1:many)
- Attack → Tasks (1:many)
- HashList ↔ HashItems (many:many)
- Agent executes Tasks, reports CrackResults

### API Structure

**Agent API** (`/api/v1/client/*`)

- Agent registration, heartbeat, task management
- Router files: `app/api/v1/endpoints/agent/{resource}.py`
- Non-resource endpoints in `general.py`

**Web UI API** (`/api/v1/web/*`)

- Campaign management, monitoring, visualization
- Router files: `app/api/v1/endpoints/web/{resource}.py`

**Control API** (`/api/v1/control/*`)

- Future CLI/TUI interface
- Router files: `app/api/v1/endpoints/control/{resource}.py`

**Shared Infrastructure** (`/api/v1/`)

- Cross-interface endpoints (users, resources)
- Files: `app/api/v1/endpoints/users.py`, `resources.py`

### Frontend Stack

**SvelteKit Application** (`frontend/`)

- SPA with client-side routing and state management
- Separate `package.json` - run pnpm/npm commands from `frontend/`
- Communicates with backend via JSON REST API

**UI Libraries**

- Shadcn-Svelte: Primary component library
- Flowbite: Additional enterprise components
- Zod: Client-side validation
- Superforms: Modal-based forms
- Built-in dark mode and accessibility compliance

**Key Features**

- Agent management dashboard
- Attack configuration interface
- Real-time task monitoring
- Results visualization

## Core Concepts

### State Machines

Use finite state machines for entity lifecycle management:

**Agent States**: `registered` → `active` → `disconnected` → `reconnecting` → `retired`
**Session States**: `initialized` → `primed` → `executing` → `completed` → `archived`
**Task States**: `pending` → `dispatched` → `running` → `complete` → `validated`

- Use SQLAlchemy Enums for state fields
- Validate transitions via service methods
- Never allow direct state writes outside service layer

### Attack System

**Modes**: Dictionary, Mask, Hybrid Dictionary, Hybrid Mask
**Resources**: Word lists, rule lists, mask patterns, custom charsets
**Storage**: MinIO S3-compatible with UUID-based file names, presigned URLs
**Buckets**: `wordlists/`, `rules/`, `masks/`, `charsets/`, `temp/`

### Task Distribution

- Keyspace slicing for parallel execution
- Real-time progress tracking
- Result collection and validation
- Error handling and retry logic

## Development Guidelines

### Service Layer Architecture

- All business logic in `app/core/services/`
- API endpoints are thin wrappers that delegate to services
- Service functions: `{action}_{resource}_service()`
- CRUD operations: `create_`, `get_`, `list_`, `update_`, `delete_`
- Services accept `AsyncSession` as first parameter
- Return Pydantic models, not raw SQLAlchemy objects

### Code Organization

- Models: `app/models/{resource}.py`
- Schemas: `app/schemas/{resource}.py` (Pydantic)
- Services: `app/core/services/{resource}_service.py`
- API routes: `app/api/v1/endpoints/{interface}/{resource}.py`
- Use Alembic for database migrations
- Type hints required throughout

### Logging

- Use Loguru exclusively (never standard Python logging)
- Structured, timestamped logs with consistent levels
- Use `logger.bind()` for context (task ID, agent ID)
- Emit to stdout for containerized environments

### Caching

- Use Cashews exclusively for all caching
- In-memory (`mem://`) for development, Redis for production
- Short TTLs (≤60s) unless justified
- Logical key prefixes: `campaign_stats:`, `agent_health:`
- Use tagging and `.invalidate()` for cache busting

### Authentication

**Web UI**: OAuth2 with password flow, HTTP-only cookies, CSRF protection
**Agent API**: Bearer tokens (`csa_<agent_id>_<random_string>`)
**Control API**: API keys (`cst_<user_id>_<random_string>`)

All tokens require HTTPS, automatic expiration, and audit logging.

### Error Handling

- Raise domain-specific exceptions in services
- Translate to HTTPException in endpoints
- Agent API v1: Match legacy error schema exactly
- Other APIs: Use FastAPI default `{"detail": "message"}`
- Never expose internal errors or stack traces

### Testing Strategy

- Unit tests for services (mock external dependencies)
- Integration tests for API endpoints (real database)
- Contract testing for API v1 specification compliance
- End-to-end tests for critical workflows

## Docker Configuration

### Required Services

- **app**: FastAPI (Python 3.13, uv, health checks)
- **db**: PostgreSQL 16+ (persistent volumes, backups)
- **redis**: Caching (Cashews) and task queues (Celery)
- **minio**: S3-compatible object storage
- **nginx**: Reverse proxy (SSL, rate limiting)

### Container Standards

- Non-root users in all containers
- Multi-stage builds for app image
- Health checks for all services
- Environment variables for configuration
- Named volumes for persistent data
- Single command deployment: `docker compose up -d`esources.
  - Monitor memory usage and optimize your application accordingly.
- **Rendering Optimization (if applicable):**
  - If your application involves rendering, optimize the rendering process (e.g., using caching, lazy loading).
- **Bundle Size Optimization:**
  - Minimize the size of your application bundle by removing unnecessary dependencies and assets.
  - Use tools like webpack or Parcel to optimize your bundle.
- **Lazy Loading Strategies:**
  - Implement lazy loading for resources that are not immediately needed.

## 4. Security Best Practices

- **Common Vulnerabilities and How to Prevent Them:**
  - **Image vulnerabilities:** Regularly scan your images for vulnerabilities using tools like Clair or Trivy.
  - **Configuration vulnerabilities:** Secure your container configurations to prevent unauthorized access.
  - **Network vulnerabilities:** Limit network exposure and use network policies to isolate containers.
  - **Privilege escalation:** Avoid running containers with unnecessary privileges.
- **Input Validation:**
  - Validate all input data to prevent injection attacks.
- **Authentication and Authorization Patterns:**
  - Implement robust authentication and authorization mechanisms.
  - Use secure protocols like HTTPS.
  - Store secrets securely using tools like HashiCorp Vault or Kubernetes Secrets.
- **Data Protection Strategies:**
  - Encrypt sensitive data at rest and in transit.
  - Use appropriate access control mechanisms to protect data.
- **Secure API Communication:**
  - Use secure protocols like HTTPS for API communication.
  - Implement authentication and authorization for API endpoints.
  - Rate limit API requests to prevent abuse.

## 5. Testing Approaches

- **Unit Testing Strategies:**
  - Write unit tests to verify the functionality of individual components.
  - Use mocking and stubbing to isolate components during testing.
- **Integration Testing:**
  - Write integration tests to verify the interaction between different components.
  - Test the integration with external services and databases.
- **End-to-end Testing:**
  - Write end-to-end tests to verify the entire application flow.
  - Use tools like Selenium or Cypress to automate end-to-end tests.
- **Test Organization:**
  - Organize your tests into a clear and maintainable structure.
  - Use descriptive names for your test cases.
- **Mocking and Stubbing:**
  - Use mocking and stubbing to isolate components during testing.
  - Mock external services and databases to simulate different scenarios.

## 6. Common Pitfalls and Gotchas

- **Frequent Mistakes Developers Make:**
  - **Not using `.dockerignore`:** This can lead to large image sizes and slow build times.
  - **Not pinning package versions:** This can lead to unexpected build failures due to dependency updates.
  - **Exposing unnecessary ports:** This can increase the attack surface of your application.
  - **Not cleaning up after installing packages:** This can lead to larger image sizes.
  - **Using the shell form of `CMD` or `ENTRYPOINT`:** Use the exec form (`["executable", "param1", "param2"]`) to avoid shell injection vulnerabilities and signal handling issues.
- **Edge Cases to Be Aware Of:**
  - **File permissions:** Ensure that your application has the correct file permissions.
  - **Timezone configuration:** Configure the correct timezone for your container.
  - **Resource limits:** Set appropriate resource limits for your containers.
- **Version-Specific Issues:**
  - Be aware of version-specific issues and compatibility concerns.
  - Test your application with different Docker versions to ensure compatibility.
- **Compatibility Concerns:**
  - Ensure that your application is compatible with the base image you are using.
  - Test your application on different platforms to ensure cross-platform compatibility.
- **Debugging Strategies:**
  - Use `docker logs` to view container logs.
  - Use `docker exec` to execute commands inside a running container.
  - Use `docker inspect` to inspect container metadata.
  - Use a debugger to debug your application code.

## 7. Tooling and Environment

- **Recommended Development Tools:**
  - **Docker Desktop:** For local development and testing.
  - **Docker Compose:** For orchestrating multi-container applications.
  - **Visual Studio Code with Docker extension:** For enhanced Docker development experience.
  - **Container image scanners (e.g., Trivy, Clair):** For identifying vulnerabilities in container images.
- **Build Configuration:**
  - Use a consistent build configuration for all your images.
  - Automate the build process using a build tool (e.g., Make, Gradle).
- **Linting and Formatting:**
  - Use a linter to enforce code style and best practices.
  - Use a formatter to automatically format your code.
- **Deployment Best Practices:**
  - Use a container orchestration platform like Kubernetes or Docker Swarm.
  - Implement rolling updates and rollbacks.
  - Monitor your application for performance and availability.
- **CI/CD Integration:**
  - Integrate Docker into your CI/CD pipeline.
  - Automate the build, test, and deployment process.
  - Use tools like Jenkins, GitLab CI, or CircleCI.

---

## Additional Notes

- Always use a specific tag for the base image (e.g., `ubuntu:20.04`) instead of `latest` to ensure reproducibility.
- Use `.dockerignore` to exclude files and directories that are not needed in the image. This reduces the image size and improves build performance.
- When possible, use the official Docker images from Docker Hub. They are usually well-maintained and optimized.
- Consider using a tool like `docker-slim` to further reduce the size of your Docker images by removing unnecessary files and dependencies after the build process.
- Understand the Docker build context and ensure you're only including necessary files and directories. A large build context slows down builds and increases image sizes.
- Regularly update your base images to patch security vulnerabilities.
- Use environment variables to configure your application, making it more flexible and portable.
- Implement health checks in your Dockerfiles to ensure that your containers are running correctly. This can be done using the `HEALTHCHECK` instruction.
- Consider using a private Docker registry to store your images securely.
- Document your Dockerfiles and images to make them easier to understand and maintain.
- Review your Dockerfiles regularly to ensure they are up-to-date and following best practices.
- Consider using a Dockerfile linter like `hadolint` to identify potential issues and enforce best practices.

## By following these guidelines, you can create efficient, maintainable, and secure Docker-based applications

description: globs: alwaysApply: true

---

## Basics

- Validate all input with Pydantic, never trust client data.
- Use dependency injection for user context / auth.
- Escape any user-displayed data if rendered via `templates/`.

## Cursor Rules

- Always validate with Pydantic models before saving to DB.
- NEVER write raw SQL unless explicitly asked.
- If writing file input/output logic, sanitize paths and limit file extensions.
- Protect admin-only routes with dependency-based access rules.

## Additional Security Best Practices for Ouroboros (Trusted LAN, Internal Use)

### FastAPI

- Enforce HTTPS for all deployments, even on internal networks. Never serve the API over plain HTTP in production. Use SSL/TLS termination at the proxy or application layer.
- Never hard-code secrets or credentials. Use pydantic-settings in [config.py](mdc:app/core/config.py)
- Use strong, rotating secrets for JWT signing. Set short token lifetimes and implement token revocation/rotation.
- For any session-based or cookie-authenticated endpoints, implement CSRF tokens and validate them on all state-changing requests.
- Restrict CORS: Only allow trusted origins, methods, and headers. Never use `allow_origins=["*"]` in production.
- Apply per-user and per-IP rate limiting to all public endpoints to prevent brute force and abuse, even in trusted environments.
- Never leak stack traces or internal server errors to clients. Always return generic error messages and log details server-side.
- Set maximum request body and file upload sizes to prevent DoS via large payloads.

### SQLAlchemy & Postgres

- Always use SQLAlchemy's parameterized queries and ORM features. Never concatenate SQL strings.
- The application database user should have only the minimum permissions required (no superuser, no schema changes in production).
- Require SSL connections to the Postgres database in production, even on internal networks.
- Review all Alembic migrations for destructive or unsafe operations before applying to production.
- Enable Postgres logging for failed logins, schema changes, and suspicious queries.

### General

- Set standard security headers: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`, `Strict-Transport-Security`.
- Integrate DAST/SAST tools (e.g., Escape, Bandit) into CI/CD for regular vulnerability scanning.
- Monitor and update dependencies for security patches (use Dependabot or similar).
- Log all authentication events, admin actions, and failed access attempts. Monitor logs for anomalies.

---

description: globs: app/core/services/\*_/_.py alwaysApply: false

---

# Service Layer Architecture Patterns for Ouroboros

## Service Layer Organization

### File Structure

- All services located in `app/core/services/`
- One service file per domain: `{resource}_service.py`
- Service files contain related business logic functions
- Import services in endpoints, not models directly

### Service Naming Conventions

- Service files: `{resource}_service.py` (e.g., `hash_list_service.py`, `campaign_service.py`)
- Service functions: `{action}_{resource}_service()` pattern
- CRUD operations: `create_`, `get_`, `list_`, `update_`, `delete_`
- Business operations: `{business_action}_{resource}_service()`

## Service Function Patterns

### Standard CRUD Operations

```text
# Create
async def create_hash_list_service(
    db: AsyncSession, hash_list_data: HashListCreate
) -> HashList:
    """Create a new hash list."""


# Read (single)
async def get_hash_list_service(db: AsyncSession, hash_list_id: int) -> HashList:
    """Get a hash list by ID."""


# Read (multiple with pagination)
async def list_hash_lists_service(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 20,
    name_filter: str | None = None,
    project_id: int | None = None,
) -> tuple[list[HashList], int]:
    """List hash lists with pagination and filtering."""


# Update
async def update_hash_list_service(
    db: AsyncSession,
    hash_list_id: int,
    update_data: HashListUpdateData,
) -> HashList:
    """Update a hash list."""


# Delete
async def delete_hash_list_service(db: AsyncSession, hash_list_id: int) -> None:
    """Delete a hash list."""
```

### Business Logic Operations

```text
async def reorder_attacks_service(
    db: AsyncSession,
    campaign_id: int,
    attack_ids: list[int],
) -> list[Attack]:
    """Reorder attacks within a campaign."""


async def estimate_attack_keyspace_service(
    attack_data: AttackEstimateRequest,
) -> AttackEstimateResponse:
    """Estimate keyspace and complexity for an attack configuration."""
```

## Error Handling in Services

### Custom Exceptions

- Define domain-specific exceptions in service files
- Use descriptive exception names and messages
- Raise exceptions for business rule violations

```text
class HashListNotFoundError(Exception):
    """Raised when a hash list is not found."""

    pass


class HashListInUseError(Exception):
    """Raised when attempting to delete a hash list that is in use."""

    pass


async def delete_hash_list_service(db: AsyncSession, hash_list_id: int) -> None:
    hash_list = await get_hash_list_service(db, hash_list_id)

    # Check business rules
    if await _hash_list_has_active_campaigns(db, hash_list_id):
        raise HashListInUseError(
            f"Hash list {hash_list_id} is in use by active campaigns"
        )

    await db.delete(hash_list)
    await db.commit()
```

### Exception Translation

- Services raise domain exceptions
- Endpoints translate to HTTP exceptions
- Keep HTTP concerns out of service layer

```text
# In endpoint
try:
    await delete_hash_list_service(db, hash_list_id)
except HashListNotFoundError:
    raise HTTPException(status_code=404, detail="Hash list not found")
except HashListInUseError as e:
    raise HTTPException(status_code=409, detail=str(e))
```

## Data Access Patterns

### Database Session Usage

- Always accept `AsyncSession` as first parameter
- Use dependency injection for session management
- Let endpoints handle session lifecycle

### Query Patterns

```text
# Simple get by ID
async def get_hash_list_service(db: AsyncSession, hash_list_id: int) -> HashList:
    hash_list = await db.get(HashList, hash_list_id)
    if not hash_list:
        raise HashListNotFoundError(f"Hash list {hash_list_id} not found")
    return hash_list


# Complex query with filtering
async def list_hash_lists_service(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 20,
    name_filter: str | None = None,
    project_id: int | None = None,
) -> tuple[list[HashList], int]:
    query = select(HashList)

    if name_filter:
        query = query.where(HashList.name.ilike(f"%{name_filter}%"))
    if project_id:
        query = query.where(HashList.project_id == project_id)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)

    # Get paginated results
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()

    return list(items), total or 0
```

### Transaction Management

- Services handle individual operations
- Let endpoints manage transaction boundaries for complex operations
- Use explicit commits when needed

## Input/Output Patterns

### Input Validation

- Accept Pydantic models for complex input
- Use primitive types for simple parameters
- Validate business rules in service layer

```text
async def create_hash_list_service(
    db: AsyncSession, hash_list_data: HashListCreate
) -> HashList:
    # Business validation
    if await _hash_list_name_exists(db, hash_list_data.name, hash_list_data.project_id):
        raise ValueError(
            f"Hash list name '{hash_list_data.name}' already exists in project"
        )

    hash_list = HashList(**hash_list_data.model_dump())
    db.add(hash_list)
    await db.commit()
    await db.refresh(hash_list)
    return hash_list
```

### Output Types

- Return domain models (SQLAlchemy models) from services
- Let endpoints handle serialization to response schemas
- Return tuples for operations that need multiple values

```text
# Return model
async def get_hash_list_service(...) -> HashList:

# Return tuple for pagination
async def list_hash_lists_service(...) -> tuple[list[HashList], int]:

# Return None for delete operations
async def delete_hash_list_service(...) -> None:
```

## Service Dependencies

### Service-to-Service Calls

- Services can call other services
- Import service functions directly
- Avoid circular dependencies

```text
from app.core.services.campaign_service import get_campaigns_by_hash_list_service


async def delete_hash_list_service(db: AsyncSession, hash_list_id: int) -> None:
    # Check if hash list is used in campaigns
    campaigns = await get_campaigns_by_hash_list_service(db, hash_list_id)
    if campaigns:
        raise HashListInUseError("Hash list is used in active campaigns")

    # Proceed with deletion
    hash_list = await get_hash_list_service(db, hash_list_id)
    await db.delete(hash_list)
    await db.commit()
```

### External Dependencies

- Keep external service calls in service layer
- Use dependency injection for external services
- Mock external dependencies in tests

## Business Logic Patterns

### Validation Logic

- Implement business rules in services
- Separate validation from data access
- Use helper functions for complex validation

```text
async def _validate_hash_list_deletion(db: AsyncSession, hash_list_id: int) -> None:
    """Validate that a hash list can be safely deleted."""
    # Check for active campaigns
    campaigns = await get_active_campaigns_by_hash_list(db, hash_list_id)
    if campaigns:
        raise HashListInUseError("Cannot delete hash list with active campaigns")

    # Check for running tasks
    tasks = await get_running_tasks_by_hash_list(db, hash_list_id)
    if tasks:
        raise HashListInUseError("Cannot delete hash list with running tasks")
```

### State Management

- Handle entity state transitions in services
- Validate state changes according to business rules
- Use enums for state values

```text
async def start_campaign_service(db: AsyncSession, campaign_id: int) -> Campaign:
    campaign = await get_campaign_service(db, campaign_id)

    if campaign.state != CampaignState.DRAFT:
        raise InvalidStateTransitionError(
            f"Cannot start campaign in state {campaign.state}"
        )

    campaign.state = CampaignState.ACTIVE
    campaign.started_at = datetime.utcnow()
    await db.commit()
    await db.refresh(campaign)

    return campaign
```

## Performance Considerations

### Query Optimization

- Use appropriate joins and eager loading
- Implement pagination for large result sets
- Cache expensive computations when appropriate

### Async Patterns

- Use async/await consistently
- Avoid blocking operations in async functions
- Use async database operations

## Testing Services

### Unit Testing

- Test services independently of endpoints
- Mock external dependencies
- Test both success and error paths

### Integration Testing

- Test services with real database
- Verify data persistence and retrieval
- Test complex business logic scenarios

```text
@pytest.mark.asyncio
async def test_create_hash_list_service_success(db_session):
    project = await ProjectFactory.create_async()
    hash_list_data = HashListCreate(
        name="Test Hash List",
        description="Test description",
        project_id=project.id,
        hash_type_id=0,
    )

    result = await create_hash_list_service(db_session, hash_list_data)

    assert result.name == "Test Hash List"
    assert result.project_id == project.id

    # Verify persistence
    saved = await get_hash_list_service(db_session, result.id)
    assert saved.name == "Test Hash List"
```

---

description: globs: app/core/**/\*.py,app/api/**/_.py,app/api/v1/endpoints/\*\*/_.py alwaysApply: false

---

## Layered Architecture

Keep API endpoints thin. Business logic should be in service classes under `app/services`.

- Every `/api/v1/web/*` route must delegate to a service for:
  - Validation
  - Access control
  - Computation
  - DB writes/reads

Services should return Pydantic models. Endpoints should format them as JSONResponse with status codes.

✅ Test services independently from the API layer.

All business logic must live in services. These should:

- Contain reusable methods (e.g., `assign_agent_to_session()`)
- Take Pydantic data models, interact with SQLAlchemy models, and return data models (Pydantic)
- Be invoked by API routes or background jobs
- The methods should aspire to be reusable when possible
- Return strongly typed objects. DO NOT return `dict[str, Any]`

## Guidelines for Cursor

- NEVER place DB logic in FastAPI route handlers.
- Each route should call a `service/*` method with relevant input.
- Service methods should be unit-testable and accept explicit arguments.
- Service methods must return validated Pydantic `*Out` schemas, not raw DB models.
- Handle all task/agent/session mutations here — no side effects in route handlers.
