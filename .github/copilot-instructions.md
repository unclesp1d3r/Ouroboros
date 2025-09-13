# CipherSwarm Development Guide for AI Agents

CipherSwarm is a distributed password cracking management system with FastAPI backend, SvelteKit frontend, and Go-based agents. This guide provides essential patterns for immediate productivity.

## 🏗️ Architecture Overview

### Three-API Design

- **Agent API v1** (`/api/v1/client/*`): IMMUTABLE legacy compatibility - must match `contracts/v1_api_swagger.json`
- **Web API** (`/api/v1/web/*`): SvelteKit frontend endpoints with session auth
- **Control API** (`/api/v1/control/*`): External automation with API keys, RFC9457 error format

### Key Components

- **Backend**: FastAPI + PostgreSQL + SQLAlchemy ORM + Redis caching (cashews)
- **Frontend**: SvelteKit 5 + Shadcn-Svelte + Tailwind CSS
- **Storage**: MinIO S3-compatible for attack resources
- **Task Queue**: Celery for background processing

## 🚀 Essential Commands

```bash
# Development workflow (use 'just' for all tasks)
just install          # Setup deps and pre-commit hooks
just ci-check         # REQUIRED before any commit
just test-backend     # Python tests with coverage
just test-frontend    # Frontend unit + integration tests
just test-e2e         # Full-stack Docker tests

# Frontend commands (run from frontend/ directory)
pnpm dev              # Development server
pnpm check            # Type checking and linting
```

## 🎯 Critical Development Patterns

### Python Standards

```python
# Use loguru for ALL logging (never standard logging)
from loguru import logger

logger.bind(task_id=task.id).info("Processing started")

# Use cashews for ALL caching (never functools.lru_cache)
from cashews import cache


@cache(ttl=300, tags=["campaign"])
async def get_stats(campaign_id: int):
    return await calculate_stats(campaign_id)


# Modern datetime handling
from datetime import datetime

created_at = datetime.now(datetime.UTC)  # Never datetime.utcnow()

# Type hints with Annotated for Pydantic
from typing import Annotated
from pydantic import Field

name: Annotated[str, Field(min_length=1, description="User's full name")]
```

### API Development

```python
# Router organization by interface
app/api/v1/endpoints/
├── agent/         # /api/v1/client/* (Agent API v1)
├── web/           # /api/v1/web/* (SvelteKit frontend)
└── control/       # /api/v1/control/* (External APIs)

# Control API error format (RFC9457)
return JSONResponse(
    status_code=400,
    content={
        "type": "https://example.com/problems/invalid-request",
        "title": "Invalid Request", 
        "status": 400,
        "detail": "The request parameters are invalid",
        "instance": "/api/v1/control/campaigns/123"
    },
    headers={"Content-Type": "application/problem+json"}
)
```

### SvelteKit 5 Patterns

```typescript
// Use .svelte.ts for stores with runes
// campaigns.svelte.ts
export const campaignsStore = {
    get campaigns() {
        return campaignState.campaigns;
    },
    async loadCampaigns() {
        // Implementation
    }
};

// Never export $derived directly - causes build errors
// ❌ export const campaigns = $derived(state.campaigns);
// ✅ Use getter methods in store objects
```

### Database & Testing

```python
# Use factories for all test data
from tests.factories.user_factory import UserFactory

user = await UserFactory.create(name="Test User")

# Test helper for user + project setup
from tests.utils.test_helpers import create_user_with_api_key_and_project_access

user_id, project_id, api_key = await create_user_with_api_key_and_project_access(db)

# Always use project-scoped queries
stmt = select(Campaign).filter(Campaign.project_id == project.id)
```

## 🔒 Security & Multi-tenancy

- **Project isolation**: All data access must filter by `project_id`
- **Agent auth**: Bearer tokens with format `csa_<agent_id>_<random>`
- **Control auth**: API keys with format `cst_<user_id>_<random>`
- **Web auth**: JWT + session cookies with CSRF protection

## 📁 Key File Locations

```
app/core/deps.py              # Authentication dependencies
app/models/                   # SQLAlchemy models with relationships
app/schemas/                  # Pydantic request/response models
frontend/src/lib/components/  # Reusable Svelte components
tests/factories/              # Test data factories
contracts/                    # PROTECTED API specifications
```

## ⚠️ Protected Areas

**NEVER modify without explicit permission:**

- `contracts/` - API compatibility specifications
- `alembic/` - Database migrations
- `.cursor/` and `.github/` - Development tooling

## 🧪 Test Architecture

- **Layer 1**: Backend unit/integration (`just test-backend`)
- **Layer 2**: Frontend with mocked APIs (`just test-frontend`)
- **Layer 3**: Full-stack E2E with Docker (`just test-e2e`)

## 🔧 Package Management

- **Python**: Use `uv add PACKAGE` (never edit pyproject.toml manually)
- **Frontend**: Use `pnpm` from `frontend/` directory
- **Dependencies**: Use `uv` exclusively, never pip

## 🎨 Component Libraries

- **Primary**: Shadcn-Svelte components in `frontend/src/lib/components/ui/`
- **Styling**: Tailwind CSS utility-first approach
- **Forms**: Superforms with Zod validation
- **State**: SvelteKit 5 runes with `.svelte.ts` store files

Remember: Always run `just ci-check` before committing. This validates formatting, types, tests, and API compatibility.
