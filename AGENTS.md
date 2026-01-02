# Ouroboros Agents Guide

This AGENTS.md file provides comprehensive guidance for AI agents working with the Ouroboros distributed password cracking management system.

---

## Project Overview

Ouroboros is a distributed password cracking management system built with FastAPI and SvelteKit. It coordinates multiple agents running hashcat to efficiently distribute password cracking tasks across a network of machines.

> [!NOTE]
> Treat .kiro/specs/ as the authoritative source for the project's requirements and architecture. The specs are numbered sequentially and serve as the implementation plan for the project.

### Key Components

- **Backend**: FastAPI application with PostgreSQL, SQLAlchemy ORM, JWT authentication
- **Frontend**: SvelteKit SPA with Shadcn-Svelte components and Tailwind CSS
- **Agent System**: Distributed Go-based agents (CipherSwarmAgent) that execute hashcat tasks
- **Storage**: MinIO S3-compatible storage for attack resources (wordlists, rules, masks)
- **Caching**: Cashews library for Redis-compatible caching
- **Task Queue**: Celery for background task processing

## Project Structure

```text
Ouroboros/
├── app/                          # FastAPI backend application
│   ├── api/v1/endpoints/         # API endpoints organized by interface
│   │   ├── agent/               # Agent API (/api/v1/client/*)
│   │   ├── web/                 # Web UI API (/api/v1/web/*)
│   │   ├── control/             # Control API (/api/v1/control/*)
│   │   └── *.py                 # Shared infrastructure APIs
│   ├── core/                    # Core application logic
│   ├── db/                      # Database configuration
│   ├── models/                  # SQLAlchemy database models
│   ├── schemas/                 # Pydantic request/response schemas
│   └── plugins/                 # Plugin system
├── frontend/                     # SvelteKit frontend application
│   ├── src/lib/components/      # Reusable Svelte components
│   ├── src/routes/              # SvelteKit routes
│   └── package.json             # Frontend dependencies (separate from backend)
├── tests/                       # Test suite
├── docs/                        # Documentation
├── alembic/                     # Database migrations
├── contracts/                   # API contract reference files (PROTECTED)
│   ├── v1_api_swagger.json      # Agent API v1 specification (PROTECTED)
│   ├── current_api_openapi.json # Current API OpenAPI specification (PROTECTED)
└── justfile                     # Development task runner

CipherSwarmAgent/                 # Go-based agent (separate project)
├── cmd/                         # CLI entrypoint
├── lib/                         # Core agent logic
└── main.go                      # Agent application entry point
```

## Critical API Compatibility Requirements

### Agent API v1 (`/api/v1/client/*`)

- **IMMUTABLE**: Must follow `contracts/v1_api_swagger.json` specification exactly
- **NO BREAKING CHANGES**: Locked to OpenAPI 3.0.1 specification
- **Legacy Compatibility**: Mirrors Ruby-on-Rails Ouroboros version
- **Testing**: All responses must validate against OpenAPI specification

### Agent API v2 (`/api/v2/client/*`)

- **NOT YET IMPLEMENTED**: Future FastAPI-native version
- **Breaking Changes Allowed**: With proper versioning and documentation
- **Cannot Interfere**: Must not affect v1 Agent API

### Router File Organization

Each API interface must be organized in separate directories:

| Endpoint Path                  | Router File                              |
| ------------------------------ | ---------------------------------------- |
| `/api/v1/client/agents/*`      | `app/api/v1/endpoints/agent/agent.py`    |
| `/api/v1/client/attacks/*`     | `app/api/v1/endpoints/agent/attacks.py`  |
| `/api/v1/client/tasks/*`       | `app/api/v1/endpoints/agent/tasks.py`    |
| `/api/v1/client/crackers/*`    | `app/api/v1/endpoints/agent/crackers.py` |
| `/api/v1/client/configuration` | `app/api/v1/endpoints/agent/general.py`  |
| `/api/v1/web/*`                | `app/api/v1/endpoints/web/`              |
| `/api/v1/control/*`            | `app/api/v1/endpoints/control/`          |

## Coding Standards

### Python Development

- **Formatting**: Use `ruff format` with 119 character line limit
- **Type Hints**: Always use type hints, prefer `| None` over `Optional[]`
- **Strings**: Use double quotes (`"`) for all strings
- **Imports**: Group as stdlib, third-party, local with 2 lines between top-level definitions
- **Logging**: Use `loguru` exclusively, never standard Python `logging`
- **Caching**: Use `cashews` exclusively, never `functools.lru_cache` or other mechanisms
- **Time Handling**: Use `datetime.now(datetime.UTC)` instead of deprecated `datetime.utcnow()`
- **Pydantic**: Always use v2 conventions with `Annotated` for field definitions

#### Type Hints Best Practices

```python
# ✅ Good
from typing import Annotated
from pydantic import Field

name: Annotated[str, Field(min_length=1, description="User's full name")]
age: Annotated[int, Field(ge=0, le=120)]

# ❌ Avoid
name: str = Field(..., min_length=1, description="User's full name")
```

#### Error Handling Patterns

```python
# ✅ Good - Early returns and guard clauses
async def process_resource(resource_id: int) -> Resource:
    if not resource_id:
        raise ValueError("Resource ID is required")

    resource = await get_resource(resource_id)
    if not resource:
        raise ResourceNotFound(f"Resource {resource_id} not found")

    return await process_resource_data(resource)
```

### FastAPI Development

- **All APIs must be versioned**: Use `/api/v1/...` prefix
- **Response Models**: Define Pydantic response models for all endpoints
- **Error Handling**: Use `HTTPException` for API errors, custom exceptions for business logic
- **Dependencies**: Use dependency injection for auth, database sessions, and user context
- **Documentation**: Include comprehensive docstrings with Args, Returns, and Raises sections

#### Control API Error Handling

- **RFC9457 Compliance**: All Control API endpoints must return errors in `application/problem+json` format
- **Required Fields**: `type`, `title`, `status`, `detail`, `instance`, and relevant extensions

### Frontend Development (SvelteKit)

- **Component Library**: Use Shadcn-Svelte and Flowbite as primary UI libraries
- **Styling**: Use Tailwind CSS with utility-first approach
- **Forms**: Use Superforms with Zod validation
- **State Management**: Use SvelteKit stores and `$app/state` (not deprecated `$app/stores`)
- **Package Management**: Run `pnpm`/`npm` commands from `frontend/` directory
- **Idiomatic Svelte**: Follow Svelte 5 conventions and best practices

### Database Development

- **ORM**: Use SQLAlchemy 2.0 with async patterns
- **Migrations**: Use Alembic for all schema changes
- **Models**: Define relationships clearly with proper foreign keys and join tables
- **Multi-tenancy**: Enforce project-level isolation for all data access

#### Service Layer Architecture Patterns

All business logic should be implemented in service functions, not in API endpoints:

```python
# ✅ Service Function Structure
async def create_campaign_service(
    db: AsyncSession, campaign_data: CampaignCreate, current_user: User
) -> Campaign:
    """Create a new campaign with business validation."""
    # Validation
    if await _campaign_name_exists(db, campaign_data.name, campaign_data.project_id):
        raise CampaignExistsError("Campaign name already exists in project")

    # Business logic
    campaign = Campaign(**campaign_data.model_dump())
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)
    return campaign


# ✅ Service Function Naming Conventions
# CRUD: create_*, get_*, list_*, update_*, delete_*
# Business: estimate_keyspace_*, reorder_attacks_*, start_campaign_*
```

#### Database Patterns

**Session Management:**

```python
# ✅ Session management with dependency injection
from app.core.deps import get_db


@router.get("/campaigns")
async def list_campaigns(db: AsyncSession = Depends(get_db)):
    return await campaign_service.list_campaigns_service(db)
```

**Pagination Pattern:**

```python
# ✅ Pagination pattern
async def list_campaigns_service(
    db: AsyncSession, skip: int = 0, limit: int = 20
) -> tuple[list[Campaign], int]:
    query = select(Campaign).offset(skip).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()

    count_query = select(func.count(Campaign.id))
    total = await db.scalar(count_query)

    return list(items), total or 0
```

### Go Development (CipherSwarmAgent)

- **Version**: Go 1.22 or later
- **CLI Framework**: Use Cobra for command-line interface
- **API Contract**: Must match Agent API v1 specification exactly
- **Configuration**: Support environment variables, CLI flags, and YAML config files
- **Error Handling**: Implement exponential backoff for API requests

## Authentication Strategies

### Web UI Authentication

- OAuth2 with Password flow and refresh tokens
- Session-based with secure HTTP-only cookies
- CSRF protection for forms
- Argon2 password hashing

### Agent API Authentication

- Bearer token authentication
- Token format: `csa_<agent_id>_<random_string>`
- One token per agent, bound to agent ID
- Automatic token invalidation on agent removal

### Control API Authentication

- API key-based authentication using bearer tokens
- Token format: `cst_<user_id>_<random_string>`
- Multiple active keys per user supported
- Configurable permissions and scopes

## Database Models and Relationships

### Core Models

- **Project**: Top-level organizational boundary (multi-tenancy)
- **Campaign**: Coordinated cracking attempts targeting a hash list
- **Attack**: Specific cracking configuration within a campaign
- **Task**: Discrete work unit assigned to a single agent
- **HashList**: Set of hashes targeted by campaigns
- **HashItem**: Individual hash with metadata (stored as JSONB)
- **Agent**: Registered client capable of executing tasks
- **CrackResult**: Successfully cracked hash record
- **User**: Authenticated entity with project-scoped permissions

### Key Relationships

- Project → Campaigns (one-to-many)
- User ↔ Projects (many-to-many)
- Campaign → Attacks (one-to-many)
- Attack → Tasks (one-to-many)
- Campaign → HashList (many-to-one)
- HashList ↔ HashItems (many-to-many)

## Testing Requirements

### Three-Tier Testing Architecture

Ouroboros uses a strategic three-tier testing architecture:

#### Tier 1: Backend (`just test-backend`)

- **Technology**: pytest + testcontainers + polyfactory
- **Scope**: API endpoints, services, models with real PostgreSQL
- **Coverage**: Focused on `app/` directory
- **Speed**: Fast (seconds)
- **When to use**: Testing backend logic, services, database operations

#### Tier 2: Frontend (`just test-frontend`)

- **Technology**: Vitest + Playwright with mocked APIs
- **Scope**: UI components, user interactions, client-side logic
- **Speed**: Fast (seconds)
- **When to use**: Testing UI components and frontend logic in isolation

#### Tier 3: Full E2E (`just test-e2e`)

- **Technology**: Playwright against full Docker stack
- **Scope**: Complete user workflows across real backend
- **Data**: Uses `scripts/seed_e2e_data.py` for test data
- **Speed**: Slow (minutes)
- **When to use**: Validating complete user workflows end-to-end

**Testing Strategy Guidelines:**

- Run the **smallest tier** that exercises your changes
- Use `just ci-check` only when PR-ready or touching multiple tiers
- For verification-only tasks (no code changes), testing is not required

### Backend Testing

```bash
# Run all tests
just test-backend

# Run with coverage
just coverage

# Run linting and type checking
just check

# Full CI check (REQUIRED before PR submission)
just ci-check
```

### Frontend Testing

```bash
# From frontend/ directory
pnpm test

# E2E tests (requires backend running)
pnpm test:e2e

# Lint and type check
pnpm check
```

### Test Patterns

- Use `pytest` for all Python tests
- Use test factories in `tests/factories/`
- Use helper functions from `tests/utils/test_helpers.py`
- For Control API tests, use `create_user_with_api_key_and_project_access()`
- Validate API responses against OpenAPI specifications

## Development Workflow

### Quickstart Commands

```bash
# 1) Setup
just install

# 2) Backend dev only (hot reload)
just dev

# 3) Fullstack dev (Docker, hot reload, migrations, seed, logs)
just docker-dev-up-watch

# 4) Stop dev stack
just docker-dev-down

# 5) Open docs/UI
open http://localhost:8000/docs     # Swagger UI
open http://localhost:8000/redoc    # ReDoc
open http://localhost:5173          # SvelteKit Frontend

# 6) Full CI checks (heavy - only before PR)
just ci-check
```

### Common Just Commands

**Setup & Maintenance:**

- `just install` - Install Python/JS dependencies and pre-commit hooks
- `just update-deps` - Update uv and pnpm dependencies

**Linting & Formatting:**

- `just check` - Run all code and commit checks
- `just format` - Auto-format code with ruff and prettier
- `just format-check` - Check formatting only
- `just lint` - Run all linting checks

**Development Servers:**

- `just dev` - Backend only (alias for `dev-backend`)
- `just dev-backend` - Run migrations + start FastAPI dev server
- `just dev-frontend` - Start SvelteKit dev server only
- `just dev-fullstack` - Start both in Docker with hot reload

**Docker Workflows:**

- `just docker-dev-up-watch` - Start dev stack + follow logs
- `just docker-dev-down` - Stop dev stack
- `just docker-prod-up` / `just docker-prod-down` - Production compose

**Documentation:**

- `just docs` - Serve MkDocs locally (port 9090)
- `just docs-test` - Test documentation build

**Database:**

- `just db-reset` - Drop, recreate, and migrate test database

**Release Management:**

- `just release` - Generate CHANGELOG.md with git-cliff
- `just release-preview` - Preview changelog without writing

### Git Workflow

#### Branch Strategy

- **Long-lived branches:**

  - `main`: Primary development branch (v2 codebase)
  - `v1-archive`: Archived v1 stable (maintenance-only, rarely updated)

- **Short-lived branches:**

  - `feature/<area>/<desc>`: New features off `main`
  - `hotfix/<desc>`: Emergency fixes off `main`
  - `release/<version>`: Release preparation off `main`

#### Development Workflows

**Standard Development:**

```bash
git checkout main && git pull
git checkout -b feature/api/new-feature
just dev  # develop with hot reload
just test-backend  # smallest tier covering changes
git commit -m "feat(api): add project quotas"
gh pr create --base main
```

**Hotfixes:**

```bash
git checkout main && git pull
git checkout -b hotfix/critical-security-fix
# fix the issue...
just test-backend
git commit -m "fix(auth): patch security vulnerability"
gh pr create --base main
```

**Releases:**

```bash
git checkout main && git pull
git checkout -b release/v2.1.0
# stabilization work...
just ci-check  # full validation
git commit -m "chore(release): prepare v2.1.0"
gh pr create --base main
```

### Git Conventions

Follow [Conventional Commits](https://www.conventionalcommits.org):

```text
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

#### Commit Types

- `feat`: New feature (MINOR version)
- `fix`: Bug fix (PATCH version)
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Test additions/corrections
- `build`: Build system changes
- `ci`: CI configuration changes
- `chore`: Maintenance tasks

#### Scopes

- `(auth)`: Authentication and authorization
- `(api)`: API endpoints and routes
- `(cli)`: Command-line interface
- `(models)`: Data models and schemas
- `(docs)`: Documentation
- `(deps)`: Dependencies

#### Golden Rules

1. **NO direct pushes** to `main` - PRs only
2. **Agent API v1 compatibility** - maintain existing contracts
3. **Rebase before PR** - stay synced with `main`
4. **Test locally first** - run appropriate test tier before opening PR
5. **PR scope manageable** - under ~400 lines when feasible
6. **v1-archive is read-only** - only emergency security patches if absolutely needed

### Dependency Management

- **Python**: Use `uv` for all dependency management
  - `uv add PACKAGE_NAME` to install packages
  - `uv add --dev PACKAGE_NAME` for dev dependencies
  - `uv remove PACKAGE_NAME` to uninstall
- **Frontend**: Use `pnpm` from `frontend/` directory
- **Never edit** `pyproject.toml` dependencies manually

### Protected Files and Directories

**NEVER modify these without explicit permission:**

- `contracts/` (API contract reference files)
- `alembic/` (database migrations)
- `.cursor/` (cursor configuration)
- `.github/` (GitHub workflows)

## Docker Development Environment

### Environment Variables

Key environment variables from `docker-compose.yml` and `docker-compose.dev.yml`:

- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_HOST/PORT` - Redis cache connection
- `CELERY_BROKER_URL/RESULT_BACKEND` - Task queue configuration
- `SECRET_KEY` - JWT signing secret
- `FIRST_SUPERUSER/PASSWORD` - Initial admin user
- `BACKEND_CORS_ORIGINS` - Frontend origins for CORS

### Health Endpoints

- `/api-info` - API metadata (name, version, docs links)
- `/health` - Simple health check for Docker

### Docker Commands

**Development Environment:**

```bash
# Start fullstack with migrations, seeding, and log following
just docker-dev-up-watch

# Stop and clean up
just docker-dev-down
```

**Production Environment:**

```bash
just docker-prod-up      # Start production stack
just docker-prod-down    # Stop production stack
```

## Security Guidelines

### General Security

- **HTTPS Only**: Never serve over plain HTTP in production
- **No Hard-coded Secrets**: Use pydantic-settings and environment variables
- **Strong JWT Secrets**: Use rotating secrets with short token lifetimes
- **CSRF Protection**: Implement CSRF tokens for state-changing requests
- **Rate Limiting**: Apply per-user and per-IP rate limiting
- **Error Handling**: Never leak stack traces or internal errors to clients

### Database Security

- **Parameterized Queries**: Always use SQLAlchemy ORM, never raw SQL
- **Minimal Permissions**: Database user should have minimum required permissions
- **SSL Connections**: Require SSL for all database connections
- **Migration Review**: Review all Alembic migrations before production

### API Security

- **Input Validation**: Validate all input with Pydantic models
- **Output Sanitization**: Escape user-displayed data in templates
- **Access Control**: Use dependency injection for user context and auth
- **Security Headers**: Set standard security headers (HSTS, X-Frame-Options, etc.)

## Performance Guidelines

### Caching Strategy

```python
# Use Cashews for all caching
from cashews import cache


@cache(ttl=60)  # 60 second TTL
async def expensive_operation():
    return await perform_calculation()


# Cache with tags for invalidation
@cache(ttl=300, tags=["campaign", "stats"])
async def get_campaign_stats(campaign_id: int):
    return await calculate_stats(campaign_id)
```

### Database Optimization

- Use async SQLAlchemy operations for I/O-bound tasks
- Implement proper indexing for frequently queried fields
- Use lazy loading for large datasets
- Optimize Pydantic models for serialization performance

### Frontend Optimization

- Use SvelteKit's built-in optimizations
- Implement proper component lazy loading
- Optimize bundle size with tree shaking
- Use Tailwind CSS purging for production builds

## Programmatic Checks

Before submitting any changes, run these validation commands:

### Backend Validation

```bash
# Full CI check (REQUIRED)
just ci-check

# Individual checks
just check          # Linting and type checking
just test           # Run test suite
just test-cov       # Run tests with coverage
```

### Frontend Validation

```bash
# From frontend/ directory
pnpm check          # Type checking and linting
pnpm test           # Unit tests
pnpm build          # Production build check
```

### Docker Validation

```bash
# Build and test containers
docker compose build
docker compose up -d
docker compose exec app just ci-check
```

## Error Handling Patterns

### Custom Exceptions

Define custom exceptions in `app/core/exceptions.py`:

```python
class CipherSwarmException(Exception):
    """Base exception for Ouroboros"""

    pass


class ResourceNotFound(CipherSwarmException):
    """Resource not found exception"""

    pass


class CampaignNotFoundError(Exception):
    """Raised when a campaign is not found."""

    pass
```

### Service Layer Error Patterns

```python
# ✅ Custom domain exceptions in services
class CampaignNotFoundError(Exception):
    """Raised when a campaign is not found."""

    pass


# ✅ Exception translation in endpoints
try:
    campaign = await get_campaign_service(db, campaign_id)
except CampaignNotFoundError:
    raise HTTPException(status_code=404, detail="Campaign not found")
```

### API Error Responses

```python
# FastAPI error handling
from fastapi import HTTPException

# Standard HTTP exception
raise HTTPException(status_code=404, detail="Agent not found")

# Control API RFC9457 compliance
return JSONResponse(
    status_code=400,
    content={
        "type": "https://example.com/problems/invalid-request",
        "title": "Invalid Request",
        "status": 400,
        "detail": "The request parameters are invalid",
        "instance": "/api/v1/control/campaigns/123",
    },
    headers={"Content-Type": "application/problem+json"},
)
```

## Resource Management

### MinIO Storage Structure

```text
Buckets:
├── wordlists/          # Dictionary attack word lists
├── rules/              # Hashcat rule files
├── masks/              # Mask pattern files
├── charsets/           # Custom charset definitions
└── temp/               # Temporary storage for uploads
```

### File Upload Handling

- Direct uploads to MinIO buckets
- Progress tracking for large files
- MD5 checksum verification
- Virus scanning for uploads
- File type verification

## Monitoring and Logging

### Logging Standards

```python
from loguru import logger

# Structured logging with context
logger.bind(task_id=task.id, agent_id=agent.id).info("Task started")

# Error logging with exception details
try:
    result = await process_task()
except Exception as e:
    logger.bind(task_id=task.id).error(f"Task failed: {e}")
    raise
```

### Performance Monitoring

- Container metrics collection
- Application performance tracking
- Resource usage monitoring
- Alert configuration for critical issues

## Debugging and Development Tools

### Backend Debugging

- **VS Code**: Use provided launch configurations for debugging the backend
- **Command Line**: Use `pytest --pdb` to drop into debugger on test failures
- **Logs**: Check Docker logs with `docker compose logs -f backend`

### Frontend Debugging

- **Browser DevTools**: Use browser's developer tools for debugging the frontend
- **Svelte DevTools**: Install Svelte DevTools browser extension
- **Network Tab**: Monitor API requests and responses
- **Console**: Check for JavaScript errors and warnings

## SDK and Client Development

### Rust Client Development

When developing Rust clients for the Ouroboros API:

- **Code Generation**: Use OpenAPI Generator for Rust client code from current API schema
- **Linting**: Enforce `cargo clippy -- -D warnings` for strict checking
- **Testing**: Recommend `criterion` for benchmarks, `insta` for snapshot testing
- **Organization**: Keep generated SDK code in separate packages/repositories

### SDK Best Practices

- Generate from `contracts/current_api_openapi.json` specification
- Maintain separate versioning for SDK releases
- Include comprehensive examples and documentation
- Test against live API endpoints in CI/CD

## User Preferences and Project Conventions

### Maintainer Preferences

- **Code Review**: Prefer coderabbit.ai over GitHub Copilot auto-reviews
- **Milestones**: Named as version numbers (e.g., `v2.0`) with descriptive summaries
- **Identity**: Always use handle 'UncleSp1d3r', never real name in commits or documentation
- **Commits**: Never commit on behalf of maintainer; always open PRs for review

### Branch and PR Conventions

- PRs must target `main` branch
- Keep PR scope manageable (under ~400 lines when feasible)
- Include descriptive PR titles following conventional commit format
- Link related issues in PR description
- Ensure CI checks pass before requesting review

## First Tasks Checklist for New AI Agents

When starting work on Ouroboros:

1. **Setup**: Run `just install` to install dependencies
2. **Start Development**: Run `just docker-dev-up-watch` for fullstack environment
3. **Verify URLs**:
   - <http://localhost:8000/docs> (Swagger UI)
   - <http://localhost:8000/redoc> (ReDoc)
   - <http://localhost:5173> (Frontend)
4. **Read Documentation**:
   - This AGENTS.md file (comprehensive agent rules)
   - `.cursor/rules/` (project-specific patterns)
   - Project README.md (overview and features)
5. **Choose Test Strategy**: Select smallest tier covering your changes
6. **API Compliance**:
   - If touching `/api/v1/client/*`, validate against `contracts/v1_api_swagger.json`
   - If touching Control API, ensure RFC9457 `application/problem+json` responses
7. **Validate Changes**: Run appropriate test suite before marking complete

### Onboarding Verification

Before starting work, verify:

- ✅ Development environment runs successfully
- ✅ All documentation links are accessible
- ✅ Test commands work correctly
- ✅ Understanding of API compatibility requirements
- ✅ Familiarity with protected files and directories
- ✅ Knowledge of required libraries (loguru, cashews, datetime.UTC)

## AI Agent Guidelines

When working with this codebase:

1. **Follow Existing Patterns**: Match the established code organization and style
2. **Respect API Contracts**: Never break Agent API v1 compatibility
3. **Use Proper Tools**: Use the specified libraries (loguru, cashews, etc.)
4. **Validate Changes**: Always run appropriate test tier before completing tasks
5. **Security First**: Follow security guidelines for all code changes
6. **Test Thoroughly**: Write and run appropriate tests for all changes
7. **Document Changes**: Update relevant documentation when making changes
8. **No Direct Commits**: Always open PRs; never push directly to main or commit on behalf of maintainer

### Common Pitfalls to Avoid

- Using standard Python `logging` instead of `loguru`
- Using `functools.lru_cache` instead of `cashews`
- Using `datetime.utcnow()` instead of `datetime.now(datetime.UTC)`
- Modifying protected files without permission
- Breaking Agent API v1 compatibility
- Skipping the appropriate test validation step
- Hard-coding secrets or configuration values
- Using deprecated Svelte patterns in frontend code
- Running `just ci-check` for verification-only tasks (no code changes)
- Pushing directly to `main` branch

This AGENTS.md file serves as the definitive guide for AI agents working with Ouroboros. All code changes must comply with these standards and pass the programmatic checks before submission.
