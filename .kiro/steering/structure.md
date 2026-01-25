# Ouroboros Project Structure

## Root Directory Layout

```
Ouroboros/
├── app/                    # Backend Python application
├── frontend/               # SvelteKit frontend application
├── alembic/               # Database migrations
├── tests/                 # Backend test suite
├── scripts/               # Utility and development scripts
├── docs/                  # Documentation (MkDocs)
├── config/                # Configuration files (Casbin policies)
├── contracts/             # API contracts and OpenAPI specs
├── project_spec/          # Project requirements and specifications
├── .kiro/                 # Kiro AI assistant configuration
├── .github/               # GitHub Actions workflows
└── docker-compose*.yml    # Docker orchestration files
```

## Backend Structure (`app/`)

```text
app/
├── __init__.py
├── main.py                # FastAPI application entry point
├── api/                   # API route definitions
│   ├── routes/           # Shared route utilities
│   ├── v1/               # API version 1
│   │   └── endpoints/    # API endpoints organized by interface
│   │       ├── agent/    # Agent API (/api/v1/client/*)
│   │       ├── web/      # Web UI API (/api/v1/web/*)
│   │       ├── control/  # Control API (/api/v1/control/*)
│   │       └── *.py      # Shared infrastructure APIs
│   └── v2/               # API version 2 endpoints
├── core/                  # Core application logic
│   ├── auth.py           # Authentication logic
│   ├── authz.py          # Authorization (Casbin)
│   ├── config.py         # Application configuration
│   ├── deps.py           # FastAPI dependencies
│   ├── exceptions.py     # Custom exceptions
│   ├── logging.py        # Logging configuration
│   ├── permissions.py    # Permission definitions
│   ├── security.py       # Security utilities
│   ├── services/         # Business logic services
│   └── tasks/            # Background task definitions
├── db/                    # Database configuration
│   ├── config.py         # Database settings
│   ├── health.py         # Database health checks
│   └── session.py        # SQLAlchemy session management
├── models/                # SQLAlchemy ORM models
│   ├── base.py           # Base model class
│   ├── user.py           # User model
│   ├── agent.py          # Agent model
│   ├── campaign.py       # Campaign model
│   ├── attack.py         # Attack model
│   ├── task.py           # Task model
│   ├── hash_list.py      # Hash list model
│   └── ...               # Other domain models
├── schemas/               # Pydantic schemas for API
│   ├── auth.py           # Authentication schemas
│   ├── user.py           # User schemas
│   ├── agent.py          # Agent schemas
│   └── ...               # Other API schemas
├── plugins/               # Plugin system
│   ├── base.py           # Base plugin class
│   ├── dispatcher.py     # Plugin dispatcher
│   └── shadow_plugin.py  # Shadow file plugin
└── resources/             # Static resources
    ├── rules/            # Hashcat rule files
    └── hash_modes.json   # Hashcat mode definitions
```

## Frontend Structure (`frontend/`)

```
frontend/
├── src/
│   ├── lib/              # Shared components and utilities
│   ├── routes/           # SvelteKit routes (pages)
│   ├── app.html          # HTML template
│   └── app.d.ts          # TypeScript declarations
├── static/               # Static assets
├── tests/                # Frontend tests
├── e2e/                  # End-to-end tests
├── build/                # Build output
├── package.json          # Node.js dependencies
├── svelte.config.js      # SvelteKit configuration
├── vite.config.ts        # Vite build configuration
├── tailwind.config.js    # TailwindCSS configuration
├── tsconfig.json         # TypeScript configuration
└── playwright.config.ts  # Playwright test configuration
```

## Database Migrations (`alembic/`)

```
alembic/
├── versions/             # Migration files (auto-generated)
├── env.py               # Alembic environment configuration
├── script.py.mako       # Migration template
└── README               # Alembic documentation
```

## Testing Structure (`tests/`)

```
tests/
├── conftest.py          # Pytest configuration and fixtures
├── factories/           # Test data factories
├── unit/                # Unit tests
├── integration/         # Integration tests
├── e2e/                 # End-to-end tests
├── db/                  # Database-specific tests
└── utils/               # Test utilities
```

## Key Configuration Files

- **`pyproject.toml`**: Python project configuration, dependencies, and tool settings
- **`justfile`**: Task runner with all development commands
- **`.env`**: Environment variables for local development
- **`docker-compose.yml`**: Production Docker orchestration
- **`docker-compose.dev.yml`**: Development Docker orchestration
- **`alembic.ini`**: Database migration configuration
- **`.pre-commit-config.yaml`**: Pre-commit hook configuration
- **`mkdocs.yml`**: Documentation site configuration

## Naming Conventions

### Python (Backend)

- **Files**: `snake_case.py`
- **Classes**: `PascalCase`
- **Functions/Variables**: `snake_case`
- **Constants**: `UPPER_SNAKE_CASE`
- **Database Tables**: `snake_case` (auto-generated from model names)

### TypeScript/Svelte (Frontend)

- **Files**: `kebab-case.svelte`, `camelCase.ts`
- **Components**: `PascalCase.svelte`
- **Functions/Variables**: `camelCase`
- **Constants**: `UPPER_SNAKE_CASE`

### API Endpoints

- **Routes**: `/kebab-case` (e.g., `/hash-lists`, `/crack-results`)
- **Query Parameters**: `snake_case`
- **JSON Fields**: `snake_case` (backend) → `camelCase` (frontend via serialization)

## Import Patterns

### Backend

```python
# Absolute imports from app root
from app.models.user import User
from app.schemas.auth import TokenResponse
from app.core.deps import get_current_user
```

### Frontend

```typescript
// Alias imports using @/* for lib
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
```

## File Organization Principles

1. **Domain-Driven**: Models, schemas, and routes organized by business domain
2. **Layered Architecture**: Clear separation between API, business logic, and data layers
3. **Feature-Based**: Frontend routes mirror API structure where possible
4. **Shared Utilities**: Common code in `core/` (backend) and `lib/` (frontend)
5. **Configuration Centralization**: All config in dedicated files, not scattered
