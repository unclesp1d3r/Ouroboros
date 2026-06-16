# Ouroboros Agents Guide

Distributed password cracking management system built with FastAPI (backend) and SvelteKit (frontend). Coordinates Go-based agents (CipherSwarmAgent) running hashcat across multiple machines.

> **Authoritative specs**: `.kiro/specs/` contains numbered implementation specs.

---

## Critical Rules

### Protected Files - NEVER Modify Without Permission

| Directory    | Contents                                                           |
| ------------ | ------------------------------------------------------------------ |
| `contracts/` | API contract specs (v1_api_swagger.json, current_api_openapi.json) |
| `alembic/`   | Database migrations                                                |
| `.cursor/`   | Cursor configuration                                               |
| `.github/`   | GitHub workflows                                                   |

### Agent API v1 - IMMUTABLE

- **Endpoint**: `/api/v1/client/*`
- **Contract**: Must match `contracts/v1_api_swagger.json` exactly
- **Breaking changes**: NEVER allowed - locked to OpenAPI 3.0.1
- **Validation**: All responses must validate against spec

### Required Library Substitutions

| Never Use             | Always Use Instead           |
| --------------------- | ---------------------------- |
| `logging` (stdlib)    | `loguru`                     |
| `functools.lru_cache` | `cashews`                    |
| `datetime.utcnow()`   | `datetime.now(datetime.UTC)` |
| `Optional[T]`         | `T \| None`                  |

### Git Rules

- **NO direct pushes to `main`** - PRs only
- **Never commit on behalf of maintainer** - always open PRs
- **Use handle 'UncleSp1d3r'** - never real name in commits/docs
- **Conventional commits**: `<type>(scope): description`

---

## Project Structure

```text
Ouroboros/
├── app/                          # FastAPI backend
│   ├── api/v1/endpoints/
│   │   ├── agent/               # Agent API (/api/v1/client/*)
│   │   ├── web/                 # Web UI API (/api/v1/web/*)
│   │   └── control/             # Control API (/api/v1/control/*)
│   ├── core/                    # Core logic, exceptions, deps
│   ├── models/                  # SQLAlchemy models
│   └── schemas/                 # Pydantic schemas
├── frontend/                     # SvelteKit SPA
├── tests/                       # pytest test suite
├── contracts/                   # API contracts (PROTECTED)
└── justfile                     # Task runner
```

### Router Organization

| Endpoint Path                  | Router File                              |
| ------------------------------ | ---------------------------------------- |
| `/api/v1/client/agents/*`      | `app/api/v1/endpoints/agent/agent.py`    |
| `/api/v1/client/attacks/*`     | `app/api/v1/endpoints/agent/attacks.py`  |
| `/api/v1/client/tasks/*`       | `app/api/v1/endpoints/agent/tasks.py`    |
| `/api/v1/client/crackers/*`    | `app/api/v1/endpoints/agent/crackers.py` |
| `/api/v1/client/configuration` | `app/api/v1/endpoints/agent/general.py`  |
| `/api/v1/web/*`                | `app/api/v1/endpoints/web/`              |
| `/api/v1/control/*`            | `app/api/v1/endpoints/control/`          |

---

## Quick Reference

### Essential Commands

```bash
just install              # Setup dependencies
just dev                  # Backend dev server
just docker-dev-up-watch  # Fullstack with hot reload
just docker-dev-down      # Stop dev stack
just test-backend         # Run backend tests
just check                # Lint + type check
just ci-check             # Full CI validation (before PR)
```

### Testing Tiers - Use Smallest Tier That Covers Changes

| Tier     | Command                      | Use When                        |
| -------- | ---------------------------- | ------------------------------- |
| Backend  | `just test-backend`          | Backend logic, services, models |
| Frontend | `pnpm test` (from frontend/) | UI components, client logic     |
| E2E      | `just test-e2e`              | Complete user workflows         |

**Skip testing** for verification-only tasks (no code changes). **Run `just ci-check`** only when PR-ready or touching multiple tiers.

### Dependency Management

- **Python**: `uv add PACKAGE` / `uv add --dev PACKAGE` / `uv remove PACKAGE`
- **Frontend**: `pnpm` from `frontend/` directory
- **Never edit** `pyproject.toml` dependencies manually

---

## Coding Standards

### Python

- **Format**: `ruff format`, 119 char line limit, double quotes
- **Type hints**: Always use, prefer `T | None` over `Optional[T]`
- **Pydantic**: v2 with `Annotated` field definitions
- **Imports**: stdlib, third-party, local (2 blank lines between top-level defs)

```python
# Pydantic v2 pattern
from typing import Annotated
from pydantic import Field

name: Annotated[str, Field(min_length=1, description="User's full name")]
```

### FastAPI

- All APIs versioned: `/api/v1/...`
- Business logic in service functions, not endpoints
- Service naming: `create_*`, `get_*`, `list_*`, `update_*`, `delete_*`

### Control API - RFC9457 Errors

All Control API errors must return `application/problem+json`:

```python
{
    "type": "https://example.com/problems/invalid-request",
    "title": "Invalid Request",
    "status": 400,
    "detail": "The request parameters are invalid",
    "instance": "/api/v1/control/campaigns/123",
}
```

### Frontend (SvelteKit)

- **UI**: Shadcn-Svelte + Flowbite + Tailwind CSS
- **Forms**: Superforms with Zod validation
- **State**: `$app/state` (not deprecated `$app/stores`)
- **Svelte 5** conventions
- Run commands from `frontend/` directory

### Database

- SQLAlchemy 2.0 async patterns
- Alembic for migrations
- Multi-tenancy: enforce project-level isolation

---

## Authentication

| Interface   | Method                  | Token Format              |
| ----------- | ----------------------- | ------------------------- |
| Web UI      | OAuth2 + refresh tokens | Session cookies           |
| Agent API   | Bearer token            | `csa_<agent_id>_<random>` |
| Control API | API key bearer          | `cst_<user_id>_<random>`  |

---

## Core Models

- **Project**: Multi-tenancy boundary
- **Campaign**: Cracking attempts targeting a hash list
- **Attack**: Cracking configuration within campaign
- **Task**: Work unit assigned to single agent
- **HashList/HashItem**: Hashes to crack
- **Agent**: Registered hashcat executor

**Relationships**: Project -> Campaigns -> Attacks -> Tasks; Campaign -> HashList \<-> HashItems

---

## Git Workflow

### Branches

- `main`: Primary development (PRs target here)
- `feature/<area>/<desc>`: New features
- `hotfix/<desc>`: Emergency fixes
- `v1-archive`: Read-only archive

### Commit Types

`feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`

### Scopes

`auth`, `api`, `cli`, `models`, `docs`, `deps`

### Workflow

```bash
git checkout main && git pull
git checkout -b feature/api/new-feature
# develop...
just test-backend  # smallest tier covering changes
git commit -m "feat(api): add project quotas"
gh pr create --base main
```

---

## Error Handling

### Services

Services raise domain exceptions; endpoints translate to HTTP:

```python
# Service
class CampaignNotFoundError(Exception):
    pass


# Endpoint
try:
    campaign = await get_campaign_service(db, campaign_id)
except CampaignNotFoundError:
    raise HTTPException(status_code=404, detail="Campaign not found")
```

### Logging

```python
from loguru import logger

logger.bind(task_id=task.id, agent_id=agent.id).info("Task started")
```

---

## Environment

### Key Variables

`DATABASE_URL`, `REDIS_HOST`, `SECRET_KEY`, `FIRST_SUPERUSER`, `BACKEND_CORS_ORIGINS`

### URLs

- Swagger: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Frontend: http://localhost:5173

### Health Endpoints

- `/api-info` - API metadata
- `/health` - Docker health check

---

## Security Essentials

- HTTPS only in production
- No hardcoded secrets (use env vars)
- SQLAlchemy ORM only (no raw SQL)
- Pydantic validation for all input
- Never leak stack traces to clients

---

## Storage (MinIO)

Buckets: `wordlists/`, `rules/`, `masks/`, `charsets/`, `temp/`

---

## Common Pitfalls

- Using stdlib `logging` instead of `loguru`
- Using `lru_cache` instead of `cashews`
- Using `datetime.utcnow()` instead of `datetime.now(datetime.UTC)`
- Modifying protected files without permission
- Breaking Agent API v1 compatibility
- Pushing directly to `main`
- Running `just ci-check` for verification-only tasks
- Using deprecated `$app/stores` in Svelte
