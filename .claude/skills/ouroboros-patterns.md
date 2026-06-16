# Ouroboros Development Patterns

## Overview

This skill captures the coding patterns, conventions, and workflows specific to the Ouroboros project - a distributed password cracking management system built with FastAPI backend and SvelteKit frontend.

## Commit Conventions

### Format

```
<type>(<scope>): <description>
```

### Commit Types (by frequency)

| Type    | Usage                     | Example                                                             |
| ------- | ------------------------- | ------------------------------------------------------------------- |
| `chore` | Maintenance, deps, config | `chore(deps): bump docker/login-action from 3.6.0 to 3.7.0`         |
| `fix`   | Bug fixes                 | `fix(api): improve error handling and add get_valid_actions method` |
| `feat`  | New features              | `feat(api): implement Agent API v2 with enhanced features`          |
| `docs`  | Documentation             | `docs: link CLAUDE.md to AGENTS.md for reference`                   |
| `test`  | Tests                     | `test(state-machines): add tests for get_valid_actions method`      |
| `ci`    | CI/CD changes             | `ci: add pre-commit hooks workflow`                                 |

### Common Scopes

| Scope            | Area                        |
| ---------------- | --------------------------- |
| `api`            | API endpoints (any version) |
| `deps`           | Dependencies                |
| `docs`           | Documentation               |
| `auth`           | Authentication              |
| `security`       | Security fixes              |
| `state-machines` | State machine logic         |

## Architecture Patterns

### Three-API Architecture

```
/api/v1/client/*   - Agent API (IMMUTABLE - locked to OpenAPI 3.0.1)
/api/v1/web/*      - Web UI API (OAuth2 + refresh tokens)
/api/v1/control/*  - Control API (API key bearer, RFC9457 errors)
```

### Service Layer Pattern

All APIs delegate to shared service functions in `app/core/services/`:

- `create_*`, `get_*`, `list_*`, `update_*`, `delete_*` naming
- Business logic lives in services, not endpoints
- Domain exceptions raised by services, translated to HTTP by endpoints

### State Machine Pattern

Campaign and Attack entities use state machines (`app/core/state_machines.py`):

- State transitions validated before execution
- `get_valid_actions()` returns allowed actions from current state
- Invalid transitions raise `InvalidResourceStateError`

## Error Handling

### Control API (RFC9457)

```python
{
    "type": "https://example.com/problems/invalid-request",
    "title": "Invalid Request",
    "status": 400,
    "detail": "The request parameters are invalid",
    "instance": "/api/v1/control/campaigns/123",
    "valid_actions": ["start", "archive"],  # Extension fields
}
```

### Service Layer Pattern

```python
# Service raises domain exception
class CampaignNotFoundError(Exception):
    pass


# Endpoint translates to HTTP
try:
    campaign = await get_campaign_service(db, campaign_id)
except CampaignNotFoundError:
    raise HTTPException(status_code=404, detail="Campaign not found")
```

## Required Substitutions

| Never Use             | Always Use                   |
| --------------------- | ---------------------------- |
| `logging` (stdlib)    | `loguru`                     |
| `functools.lru_cache` | `cashews`                    |
| `datetime.utcnow()`   | `datetime.now(datetime.UTC)` |
| `Optional[T]`         | `T \| None`                  |

## Pydantic v2 Pattern

```python
from typing import Annotated
from pydantic import Field


class QueueStatus(BaseModel):
    name: Annotated[str, Field(description="Queue name", min_length=1)]
    pending_jobs: Annotated[int | None, Field(description="Pending jobs", ge=0)] = 0
```

## Testing Tiers

| Tier     | Command             | Use When                        |
| -------- | ------------------- | ------------------------------- |
| Backend  | `just test-backend` | Backend logic, services, models |
| Frontend | `pnpm test`         | UI components, client logic     |
| E2E      | `just test-e2e`     | Complete user workflows         |

Run smallest tier that covers changes. Run `just ci-check` only when PR-ready.

## Protected Files

Never modify without permission:

- `contracts/` - API contract specs
- `alembic/` - Database migrations
- `.cursor/` - Cursor configuration
- `.github/` - GitHub workflows

## Spec-Driven Development

Authoritative specs in `.kiro/specs/`:

- Phased implementation (phase-1 through phase-6)
- Each phase has: `design.md`, `requirements.md`, `tasks.md`
- Control API spec: `.kiro/specs/phase-2e-control-api-v1/`
