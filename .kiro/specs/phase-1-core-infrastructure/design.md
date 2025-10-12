# Design Document

## Overview

The Phase 1 Core Infrastructure design establishes the foundational architecture for Ouroboros v2, focusing on database models, authentication, and core API structure. This design leverages FastAPI's async capabilities, SQLAlchemy's ORM features, and PostgreSQL's robustness to create a scalable foundation for distributed password cracking management.

The architecture follows a layered approach with clear separation between API endpoints, business logic services, data models, and database access. All components are designed to support high concurrency and distributed operations while maintaining data consistency and security.

## Architecture

### Database Architecture

**Primary Database**: PostgreSQL 16+ with async SQLAlchemy ORM

- Connection pooling for optimal performance under load
- Async session management using dependency injection
- Alembic for schema migrations and version control
- Comprehensive indexing strategy for query performance

**Session Management Pattern**:

```python
# Dependency injection pattern
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session


# Usage in endpoints
@router.get("/users")
async def list_users(db: AsyncSession = Depends(get_db)):
    return await user_service.list_users(db)
```

**Base Model Pattern**:
All models inherit from a base class providing:

- Auto-incrementing `id` (primary key)
- `created_at` timestamp (auto-populated)
- `updated_at` timestamp (auto-updated)
- Consistent serialization methods

### Authentication & Authorization Architecture

**User Management System**:

- Integration with `fastapi-users` for robust authentication
- Role-based access control (admin, analyst, operator)
- Session tracking with IP address logging
- Account security features (failed attempts, token-based reset)
- Optional TOTP 2FA support

**Security Model**:

- JWT tokens for API authentication
- Secure password hashing using bcrypt
- Token-based password reset mechanism
- Account locking after failed attempts
- Audit trail for all authentication events

### Project-Based Organization

**Multi-tenancy Design**:

- Projects as primary organizational units
- Many-to-many relationships between users and projects
- Project-level access control and resource isolation
- Support for private projects and archival

## Components and Interfaces

### Core Models

#### User Model

```text
class User(Base):
    __tablename__ = "users"

    # Identity
    name: str (unique, indexed)
    email: str (unique, indexed)
    role: UserRole (enum: admin, analyst, operator)

    # Authentication tracking
    sign_in_count: int
    current_sign_in_at: datetime
    last_sign_in_at: datetime
    current_sign_in_ip: str
    last_sign_in_ip: str

    # Security
    reset_password_token: str (unique, indexed, nullable)
    unlock_token: str (nullable)
    failed_attempts: int (default: 0)

    # Relationships
    projects: Many-to-Many with Project
    agents: One-to-Many with Agent
```

#### Project Model

```text
class Project(Base):
    __tablename__ = "projects"

    name: str (unique, indexed)
    description: str
    private: bool (default: False)
    archived_at: datetime (nullable)
    notes: str (nullable)

    # Relationships
    users: Many-to-Many with User
    agents: Many-to-Many with Agent
    campaigns: One-to-Many with Campaign
```

#### Agent Model

```text
class Agent(Base):
    __tablename__ = "agents"

    # Identity
    client_signature: str
    host_name: str
    custom_label: str (unique, indexed, nullable)

    # Authentication
    token: str (unique, indexed)
    last_seen_at: datetime
    last_ipaddress: str

    # State management
    state: AgentState (enum, indexed)
    enabled: bool (default: True)

    # Configuration
    advanced_configuration: JSON
    devices: JSON Array
    agent_type: str (nullable)

    # Relationships
    operating_system_id: ForeignKey
    user_id: ForeignKey
    projects: Many-to-Many with Project
    tasks: One-to-Many with Task
    errors: One-to-Many with AgentError
```

#### Attack Model

```text
class Attack(Base):
    __tablename__ = "attacks"

    # Basic info
    name: str
    description: str
    state: AttackState (enum, indexed)
    hash_type: HashType (enum)

    # Attack configuration
    attack_mode: AttackMode (enum)
    mask: str (nullable)
    increment_mode: bool
    increment_minimum: int
    increment_maximum: int

    # Performance tuning
    optimized: bool
    workload_profile: int
    slow_candidate_generators: bool

    # Markov configuration
    disable_markov: bool
    classic_markov: bool
    markov_threshold: int

    # Rules and charsets
    left_rule: str (nullable)
    right_rule: str (nullable)
    custom_charset_1: str (nullable)
    custom_charset_2: str (nullable)
    custom_charset_3: str (nullable)
    custom_charset_4: str (nullable)

    # Scheduling
    priority: int
    start_time: datetime (nullable)
    end_time: datetime (nullable)

    # Relationships
    campaign_id: ForeignKey (indexed)
    rule_list_id: ForeignKey (nullable)
    word_list_id: ForeignKey (nullable)
    mask_list_id: ForeignKey (nullable)
    tasks: One-to-Many with Task
```

#### Task Model

```text
class Task(Base):
    __tablename__ = "tasks"

    # State tracking
    state: TaskState (enum, indexed)
    stale: bool (default: False)

    # Timing
    start_date: datetime (nullable)
    end_date: datetime (nullable)
    completed_at: datetime (nullable, indexed)

    # Progress tracking
    progress_percent: float
    progress_keyspace: int

    # Results
    result_json: JSON

    # Relationships
    agent_id: ForeignKey (indexed)
    attack_id: ForeignKey
    errors: One-to-Many with AgentError
```

### Service Layer Architecture

**Service Organization**:

- One service file per domain (e.g., `user_service.py`, `agent_service.py`)
- Services contain all business logic and validation
- API endpoints are thin wrappers that delegate to services
- Services return Pydantic models, not raw SQLAlchemy objects

**Service Function Patterns**:

```python
# CRUD operations
async def create_user_service(db: AsyncSession, user_data: UserCreate) -> User:
    pass


async def get_user_service(db: AsyncSession, user_id: int) -> User:
    pass


async def list_users_service(
    db: AsyncSession, skip: int, limit: int
) -> Tuple[List[User], int]:
    pass


async def update_user_service(
    db: AsyncSession, user_id: int, update_data: UserUpdate
) -> User:
    pass


async def delete_user_service(db: AsyncSession, user_id: int) -> None:
    pass


# Business operations
async def authenticate_user_service(
    db: AsyncSession, email: str, password: str
) -> User:
    pass


async def register_agent_service(db: AsyncSession, agent_data: AgentCreate) -> Agent:
    pass
```

### API Structure

**Endpoint Organization**:

- `/api/v1/users` - User management (shared)
- `/api/v1/projects` - Project management (shared)
- `/api/v1/agents` - Agent management (shared)
- `/api/v1/attacks` - Attack configuration (shared)
- `/api/v1/tasks` - Task management (shared)
- `/health` - System health checks

**Response Patterns**:

- Consistent JSON responses using Pydantic schemas
- Proper HTTP status codes (201 for creation, 204 for deletion, etc.)
- Pagination support for list endpoints
- Error responses with structured detail messages

## Data Models

### Enum Definitions

```python
class UserRole(str, Enum):
    ADMIN = "admin"
    ANALYST = "analyst"
    OPERATOR = "operator"


class AgentState(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    ERROR = "error"
    OFFLINE = "offline"
    DISABLED = "disabled"


class AttackMode(str, Enum):
    DICTIONARY = "dictionary"
    BRUTE_FORCE = "brute_force"
    HYBRID_DICT = "hybrid_dict"
    HYBRID_MASK = "hybrid_mask"


class TaskState(str, Enum):
    PENDING = "pending"
    DISPATCHED = "dispatched"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
```

### Relationship Patterns

**Many-to-Many Associations**:

```python
# User-Project association
user_project_association = Table(
    "user_projects",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id")),
    Column("project_id", Integer, ForeignKey("projects.id")),
)

# Agent-Project association
agent_project_association = Table(
    "agent_projects",
    Base.metadata,
    Column("agent_id", Integer, ForeignKey("agents.id")),
    Column("project_id", Integer, ForeignKey("projects.id")),
)
```

**Foreign Key Relationships**:

- All foreign keys include proper constraints and indexes
- Cascade delete rules defined where appropriate
- Nullable foreign keys for optional relationships

### Indexing Strategy

**Primary Indexes**:

- Unique indexes on natural keys (email, name, token)
- Composite indexes for common query patterns
- State-based indexes for filtering operations
- Timestamp indexes for temporal queries

**Performance Considerations**:

- Indexes on frequently queried columns
- Partial indexes for conditional queries
- Covering indexes for read-heavy operations

## Error Handling

### Exception Hierarchy

```python
class CipherSwarmException(Exception):
    """Base exception for all Ouroboros errors"""

    pass


class UserNotFoundError(CipherSwarmException):
    """Raised when a user is not found"""

    pass


class AgentRegistrationError(CipherSwarmException):
    """Raised when agent registration fails"""

    pass


class InvalidStateTransitionError(CipherSwarmException):
    """Raised when an invalid state transition is attempted"""

    pass
```

### Error Response Format

```python
# Standard error response
{
    "detail": "User not found",
    "error_code": "USER_NOT_FOUND",
    "timestamp": "2024-01-15T10:30:00Z",
}

# Validation error response
{
    "detail": [
        {
            "loc": ["body", "email"],
            "msg": "field required",
            "type": "value_error.missing",
        }
    ]
}
```

## Testing Strategy

### Unit Testing

**Service Layer Tests**:

- Test all CRUD operations with valid and invalid data
- Test business logic and validation rules
- Mock external dependencies
- Test error conditions and edge cases

**Model Tests**:

- Test model creation and validation
- Test relationship integrity
- Test enum constraints
- Test index effectiveness

### Integration Testing

**Database Tests**:

- Test with real PostgreSQL database
- Test transaction handling and rollback
- Test concurrent operations
- Test migration scripts

**API Tests**:

- Test all endpoints with various inputs
- Test authentication and authorization
- Test error responses and status codes
- Test pagination and filtering

### Test Data Management

**Factory Pattern**:

```python
class UserFactory(Factory):
    class Meta:
        model = User

    name = Faker("name")
    email = Faker("email")
    role = UserRole.ANALYST
    sign_in_count = 0
    failed_attempts = 0
```

**Test Database Setup**:

- Isolated test database per test run
- Automatic cleanup after tests
- Consistent test data using factories
- Transaction rollback for test isolation
