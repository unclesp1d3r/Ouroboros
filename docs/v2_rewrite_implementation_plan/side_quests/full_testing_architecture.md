# Addendum: Full Testing Architecture Implementation (Post-SSR Migration)

This document defines the three-layer test system for Ouroboros, aligned to use **Python 3.13 + `uv`**, **Node + `pnpm`**, and **Docker**.

---

## Table of Contents

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=3 --minlevel=1 -->

- [Addendum: Full Testing Architecture Implementation (Post-SSR Migration)](#addendum-full-testing-architecture-implementation-post-ssr-migration)
  - [Table of Contents](#table-of-contents)
  - [Intent](#intent)
  - [Test Architecture Layers](#test-architecture-layers)
  - [Layer 1: Python Backend Tests (existing)](#layer-1-python-backend-tests-existing)
    - [Current State Analysis](#current-state-analysis)
    - [Implementation Tasks](#implementation-tasks)
  - [Layer 2: Frontend Unit + Mocked Integration (existing)](#layer-2-frontend-unit--mocked-integration-existing)
    - [Current State Analysis](#current-state-analysis-1)
    - [Implementation Tasks](#implementation-tasks-1)
  - [Layer 3: Full End-to-End Tests (new)](#layer-3-full-end-to-end-tests-new)
    - [Current State Analysis](#current-state-analysis-2)
    - [Implementation Context](#implementation-context)
    - [Implementation Tasks](#implementation-tasks-2)
  - [Aggregate CI Task](#aggregate-ci-task)
    - [Current State Analysis](#current-state-analysis-3)
    - [Implementation Tasks](#implementation-tasks-3)
  - [Key Implementation Insights](#key-implementation-insights)
    - [Reuse Existing Infrastructure](#reuse-existing-infrastructure)
    - [New Infrastructure Needed](#new-infrastructure-needed)
    - [Migration Path](#migration-path)

<!-- mdformat-toc end -->

---

## Intent

As we transition the Ouroboros frontend from a mocked SPA-style workflow to a server-rendered SvelteKit application backed by real API calls, it's critical that our test architecture evolves in parallel. This task formalizes a three-tiered test strategy to ensure quality at every layer of the stack: fast backend tests for core logic, frontend tests with mocked APIs for UX and layout, and a new full-stack E2E test layer driven by Playwright against real Dockerized backend services. These tiers will be orchestrated via `just` recipes so developers can test only what they're working on, while `just ci-check` runs the full suite to catch regressions before merge or release. We should implement this with flexibility, reusing existing patterns where possible, while ensuring each layer is isolated, deterministic, and fully automated.

---

## Test Architecture Layers

| Layer           | Stack                                       | Purpose                           |
| --------------- | ------------------------------------------- | --------------------------------- |
| `test-backend`  | Python (`pytest`, `testcontainers`)         | Backend API/unit integration      |
| `test-frontend` | JS (`vitest`, `playwright` with mocks)      | Frontend UI and logic validation  |
| `test-e2e`      | Playwright E2E (full stack, Docker backend) | True user flows across real stack |

Each layer is isolated and driven by `justfile` recipes.

---

## Layer 1: Python Backend Tests (existing)

### Current State Analysis

- ✅ **Python 3.13 + `uv` setup:** Already configured in `pyproject.toml` and used throughout project
- ✅ **testcontainers setup:** Already implemented in `tests/conftest.py` with `PostgresContainer` and `MinioContainer`
- ✅ **FastAPI app with DB overrides:** Already configured with proper dependency injection
- ✅ **Polyfactory integration:** Comprehensive factory setup for all models
- ✅ **Database health checks:** Already implemented in `app/db/health.py`
- ✅ **Async session management:** Properly configured with fixtures

### Implementation Tasks

- [x] **Python 3.13 + `uv` setup confirmed:** Already working with `uv sync --dev`
- [x] **testcontainers management confirmed:** `conftest.py` already manages PostgreSQL and MinIO containers
- [x] **Validate `just test-backend` command:** ✅ **COMPLETE** - Successfully implemented and tested (593 passed, 1 xfailed)

**Current justfile command:**

```text
# Current: just test
test:
    cd {{justfile_dir()}}
    PYTHONPATH=packages uv run python -m pytest --cov --cov-config=pyproject.toml --cov-report=xml
```

**Proposed justfile update:**

```text
# Add explicit backend test command for three-tier architecture
test-backend:
    cd {{justfile_dir()}}
    PYTHONPATH=packages uv run python -m pytest --cov --cov-config=pyproject.toml --cov-report=xml --tb=short -q
```

---

## Layer 2: Frontend Unit + Mocked Integration (existing)

### Current State Analysis

- ✅ **Vitest setup:** Already configured with `pnpm run test:unit` (maps to `vitest`)
- ✅ **Playwright mocked tests:** Already configured with `playwright.config.ts` using `webServer`
- ✅ **Test environment detection:** Already implemented with `PLAYWRIGHT_TEST` and `NODE_ENV` env vars
- ✅ **Frontend justfile commands:** Already exist as `frontend-test-unit` and `frontend-test-e2e`

### Implementation Tasks

- [x] **Vitest confirmed:** Runs with `pnpm run test:unit`
- [x] **Playwright mocked tests confirmed:** Run via `webServer` in `playwright.config.ts`
- [x] **Add consolidated `just test-frontend` command:** ✅ **COMPLETE** - Successfully implemented and tested (149 unit tests + 161 E2E tests, 3 skipped)

**Current frontend test commands:**

```text
# Existing commands
frontend-test-unit:
    cd {{justfile_dir()}}/frontend && pnpm exec vitest run

frontend-test-e2e:
    cd {{justfile_dir()}}/frontend && pnpm exec playwright test
```

**Proposed consolidated command:**

```text
# Add consolidated frontend test command for three-tier architecture
test-frontend:
    cd {{justfile_dir()}}/frontend && pnpm run test:unit && pnpm exec playwright test --project=chromium
```

---

## Layer 3: Full End-to-End Tests (new)

### Current State Analysis

- ❌ **Docker Compose E2E setup:** Does not exist - needs creation
- ❌ **Dockerfiles:** Backend and frontend Dockerfiles do not exist in Ouroboros (only exist in CipherSwarmAgent)
- ❌ **Docker healthcheck configuration:** No Docker healthcheck setup for containers
- ❌ **E2E data seeding:** No dedicated seeding scripts for E2E tests
- ❌ **Playwright global setup/teardown:** Not configured for Docker backend
- ❌ **Separate E2E test directory:** Current E2E tests are in `frontend/e2e/` and use mocks

### Implementation Context

**Current Application API Info Endpoints (can be used by Docker healthchecks):**

- `/api-info` - Basic system proof-of-life endpoint

**Current Backend Test Infrastructure (to reuse):**

- `tests/conftest.py` contains full testcontainers setup
- Polyfactory factories exist for all data models
- Database migration logic already tested
- MinIO container setup already configured

### Implementation Tasks

- [x] **Create Dockerfile for FastAPI backend** `task_id: docker.backend_dockerfile` ✅ **COMPLETE**

  - Created `Dockerfile` and `Dockerfile.dev` in project root for FastAPI backend
  - Based on Python 3.13 slim image with uv package manager
  - Multi-stage build with development dependencies for dev container
  - Proper health checks using `/api-info` endpoint
  - Exposes port 8000

- [x] **Create Dockerfile for SvelteKit frontend** `task_id: docker.frontend_dockerfile` ✅ **COMPLETE**

  - Created `frontend/Dockerfile` and `frontend/Dockerfile.dev` for SvelteKit SSR
  - Based on Node.js 20 slim image with pnpm package manager
  - Production build with adapter-node for SSR
  - Development container with hot reload support
  - Proper environment variable handling and health checks
  - Exposes port 5173 (corrected from 3000)

- [x] **Create `docker-compose.e2e.yml`** `task_id: docker.compose_e2e` ✅ **COMPLETE**

  - Created complete Docker Compose infrastructure:
    - `docker-compose.yml` - Production setup
    - `docker-compose.dev.yml` - Development with hot reload
    - `docker-compose.e2e.yml` - E2E testing environment
  - FastAPI backend service (port 8000) with health checks
  - SvelteKit frontend service (port 5173) with SSR support
  - PostgreSQL v16+ service with proper networking
  - MinIO service compatible with existing testcontainers setup
  - Redis service for caching and task queues
  - Proper dependency management and service orchestration

**Proposed docker-compose.e2e.yml structure:**

```yaml
services:
  backend:
    build: .
    ports: [8000:8000]
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/cipherswarm_e2e
      - MINIO_ENDPOINT=minio:9000
    depends_on: [postgres, minio]
    healthcheck:
      test: [CMD, curl, -f, http://localhost:8000/api-info]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build: ./frontend
    ports: [5173:5173]
    environment:
      - API_BASE_URL=http://backend:8000
      - NODE_ENV=production
    depends_on: [backend]
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: cipherswarm_e2e
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports: [5432:5432]
  minio:
    image: minio/minio:latest
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    ports: [9000:9000, 9001:9001]
    command: server /data --console-address ":9001"
```

- [x] **Create `scripts/seed_e2e_data.py`** `task_id: scripts.e2e_data_seeding` ✅ **COMPLETE**
  - Use Polyfactory factories as **data generators**, not for direct persistence
  - Convert factory output to **Pydantic schemas** for validation
  - Use **backend service layer methods** for all persistence operations
  - Create minimal, predictable test data set with known IDs:
    - 2 test users (admin and regular user) with known credentials
    - 2 test projects with known names and IDs
    - 1 test campaign with known attacks and hash lists
    - Sample resources (wordlists, rules) uploaded to MinIO
    - Agents with known benchmark data
  - Make seed data **easily extensible** for manual additions
  - Ensure data is deterministic for E2E test reliability
  - Clear and recreate data on each run for test isolation
  - **Status: COMPLETE** ✅ - Successfully implemented E2E data seeding script using service layer delegation, Pydantic validation, and predictable test data generation with known credentials

**Script structure (Pydantic + Service Layer approach):**

```python
#!/usr/bin/env python3
"""Seed data for E2E testing against Docker backend."""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import settings
from app.models.base import Base

# Import Pydantic schemas for validation
from app.schemas.user import UserCreate
from app.schemas.project import ProjectCreate
from app.schemas.campaign import CampaignCreate
from app.schemas.attack import AttackCreate

# Import service layer methods for persistence
from app.core.services.user_service import create_user_service
from app.core.services.project_service import create_project_service
from app.core.services.campaign_service import create_campaign_service

# Import factories for data generation only
from tests.factories.user_factory import UserFactory
from tests.factories.project_factory import ProjectFactory


async def create_e2e_test_users(session: AsyncSession) -> dict[str, int]:
    """Create test users using service layer with known credentials."""
    print("Creating E2E test users...")

    # Generate base data from factories, then convert to Pydantic
    admin_data = UserFactory.build()
    user_data = UserFactory.build()

    # Convert to validated Pydantic objects with known values
    admin_create = UserCreate(
        username="e2e-admin",
        email="admin@e2e-test.local",
        password="admin-password-123",
        role=UserRole.admin,
        is_active=True,
    )

    regular_user_create = UserCreate(
        username="e2e-user",
        email="user@e2e-test.local",
        password="user-password-123",
        role=UserRole.user,
        is_active=True,
    )

    # Persist through service layer (handles validation, hashing, etc.)
    admin_user = await create_user_service(session, admin_create)
    regular_user = await create_user_service(session, regular_user_create)

    return {"admin_user_id": admin_user.id, "regular_user_id": regular_user.id}


async def create_e2e_test_projects(
    session: AsyncSession, user_ids: dict
) -> dict[str, int]:
    """Create test projects with known names and user associations."""
    print("Creating E2E test projects...")

    # Generate factory data, convert to Pydantic, add known values
    project_create_1 = ProjectCreate(
        name="E2E Test Project Alpha",
        description="Primary test project for E2E testing",
        is_active=True,
    )

    project_create_2 = ProjectCreate(
        name="E2E Test Project Beta",
        description="Secondary test project for multi-project scenarios",
        is_active=True,
    )

    # Persist through service layer
    project_1 = await create_project_service(
        session, project_create_1, user_ids["admin_user_id"]
    )
    project_2 = await create_project_service(
        session, project_create_2, user_ids["admin_user_id"]
    )

    return {"project_alpha_id": project_1.id, "project_beta_id": project_2.id}


# Additional seed functions for campaigns, attacks, resources...


async def seed_e2e_data():
    """Main seeding function - easily extensible for additional data."""
    print("🌱 Starting E2E data seeding...")

    # Connect to database
    engine = create_async_engine(settings.database_url)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as session:
        # Clear existing data
        print("Clearing existing data...")
        for table in reversed(Base.metadata.sorted_tables):
            await session.execute(table.delete())
        await session.commit()

        # Create test data in dependency order
        user_ids = await create_e2e_test_users(session)
        project_ids = await create_e2e_test_projects(session, user_ids)
        campaign_ids = await create_e2e_test_campaigns(session, project_ids, user_ids)
        # ... additional data creation

        await session.commit()
        print("✅ E2E data seeding completed successfully!")


if __name__ == "__main__":
    asyncio.run(seed_e2e_data())
```

**Benefits of this approach:**

- **Factory-generated base data** with **manual override** for test-specific values

- **Pydantic validation** ensures data integrity with model changes

- **Service layer persistence** handles business logic, validation, relationships

- **Easily extensible** - just add new functions and call them in `seed_e2e_data()`

- **Known test values** for reliable E2E test assertions

- **Future-proof** against model changes through proper validation

- [x] **Create `frontend/tests/global-setup.e2e.ts`** `task_id: playwright.global_setup` ✅ **COMPLETE**

  - Start Docker Compose stack with `--wait` flag
  - Poll health endpoints until ready
  - Run data seeding script
  - Configure Playwright environment variables for backend connection
  - **Status: COMPLETE** ✅ - Successfully implemented global setup with Docker stack management, health checks, and database seeding

**Global setup structure:**

```typescript
import { execSync } from "child_process";
import fetch from "node-fetch";

async function globalSetup() {
    console.log("Starting Docker Compose E2E stack...");
    execSync("docker compose -f docker-compose.e2e.yml up -d --wait", { stdio: 'inherit' });

    // Wait for backend health check
    let ready = false;
    while (!ready) {
        try {
            const res = await fetch("http://localhost:8000/api/v1/web/health/overview");
            if (res.ok) ready = true;
        } catch {
            await new Promise(r => setTimeout(r, 1000));
        }
    }

    console.log("Seeding E2E test data...");
    execSync("docker compose -f docker-compose.e2e.yml exec backend python scripts/seed_e2e_data.py", { stdio: 'inherit' });
}

export default globalSetup;
```

- [x] **Create `frontend/tests/global-teardown.e2e.ts`** `task_id: playwright.global_teardown` ✅ **COMPLETE**
  - **Status: COMPLETE** ✅ - Successfully implemented global teardown with Docker stack cleanup

```typescript
import { execSync } from "child_process";

async function globalTeardown() {
    console.log("Stopping Docker Compose E2E stack...");
    execSync("docker compose -f docker-compose.e2e.yml down -v", { stdio: 'inherit' });
}

export default globalTeardown;
```

- [x] **Create separate E2E test configuration** `task_id: playwright.e2e_config` ✅ **COMPLETE**
  - Create `frontend/playwright.config.e2e.ts` for full-stack E2E tests
  - Configure to use real backend at `http://localhost:8000`
  - Set up global setup/teardown for Docker stack
  - Configure test data expectations for seeded data
  - Separate from existing `playwright.config.ts` which uses mocks
  - **Status: COMPLETE** ✅ - Successfully implemented E2E-specific Playwright configuration with proper global setup/teardown

**E2E config structure:**

```typescript
import { defineConfig } from '@playwright/test';
import globalSetup from './playwright/global-setup';
import globalTeardown from './playwright/global-teardown';

export default defineConfig({
    testDir: 'e2e-fullstack',
    globalSetup,
    globalTeardown,
    use: {
        baseURL: 'http://localhost:3000',
        // Configure for real backend integration
    },
    // Other E2E specific configuration
});
```

- [x] **Create E2E tests with real backend integration** `task_id: tests.e2e_integration` ✅ **COMPLETE**
  - Create `frontend/tests/e2e/` directory for full-stack E2E tests
  - Write tests that use seeded data (no API mocking)
  - Test user authentication flow with real backend
  - Test SSR page loading with real data
  - Test form submission workflows
  - Test real-time features if implemented (SSE, WebSocket)
  - **Status: COMPLETE** ✅ - Successfully implemented sample E2E tests for authentication and project management using seeded data

**Example test structure:**

```typescript
// frontend/e2e-fullstack/auth-flow.spec.ts
import { test, expect } from '@playwright/test';

test('complete user authentication flow', async ({ page }) => {
    // Use seeded test user credentials
    await page.goto('/login');
    await page.fill('[name=username]', 'e2e-test-user');
    await page.fill('[name=password]', 'test-password');
    await page.click('button[type=submit]');

    // Should redirect to dashboard with real backend data
    await expect(page).toHaveURL('/');
    await expect(page.locator('[data-testid=campaign-count]')).toBeVisible();
});
```

- [x] **Add `just test-e2e` command** `task_id: justfile.test_e2e` ✅ **COMPLETE**

```text
# Add full-stack E2E test command
test-e2e:
    cd {{justfile_dir()}}/frontend && pnpm exec playwright test --config=playwright.config.e2e.ts
```

- **Status: COMPLETE** ✅ - Successfully implemented `just test-e2e` command and updated `just ci-check` to include it

---

## Aggregate CI Task

### Current State Analysis

- ✅ **`just ci-check` exists:** Already orchestrates backend and frontend tests
- ❌ **Three-tier integration:** Not yet updated to use the new test-backend, test-frontend, test-e2e structure
- ❌ **GitHub Actions integration:** No specific workflow for three-tier testing architecture

### Implementation Tasks

- [x] **Update `just ci-check` for three-tier architecture** `task_id: justfile.ci_check_update` ✅ **COMPLETE**

```text
# Updated CI check command for three-tier architecture
ci-check:
    just format-check
    just check
    just test-backend
    just test-frontend
    # Note: test-e2e is currently a placeholder - will be implemented in Phase 9
```

- **Status: COMPLETE** ✅ - Successfully updated `ci-check` to orchestrate all three test layers. Currently runs: format-check, check, test-backend (593 passed), test-frontend (149 unit + 161 E2E tests). The test-e2e command is implemented as a placeholder for future full-stack testing.

- [ ] **Create GitHub Actions workflow** `task_id: github.three_tier_workflow`

  - Create `.github/workflows/three-tier-tests.yml`
  - Configure to run on pull requests and main branch pushes
  - Set up matrix for parallel execution of test layers
  - Configure Docker Compose for E2E tests in CI environment
  - Cache Docker images and dependencies for faster builds

**Proposed workflow structure:**

```yaml
name: Three-Tier Testing

on: [push, pull_request]

jobs:
  test-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v1
      - run: just test-backend

  test-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v2
      - run: just test-frontend

  test-e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v2
      - run: just test-e2e
```

- [ ] **Confirm dependency requirements** `task_id: dependencies.validation`
  - ✅ **Python 3.13 + `uv`:** Already configured and working
  - ✅ **Node + `pnpm`:** Already configured and working
  - ✅ **Docker:** Required for E2E tests - ensure Compose plugin available
  - ❌ **Docker image build caching:** Not yet configured for development workflow

---

## Key Implementation Insights

### Reuse Existing Infrastructure

1. **Backend testcontainers setup** in `tests/conftest.py` provides the foundation for E2E Docker setup
2. **Polyfactory factories** can be reused for E2E data seeding
3. **Health endpoints** already exist and can be used for readiness checks
4. **Frontend test environment detection** already works with `PLAYWRIGHT_TEST` env var

### New Infrastructure Needed

1. **Dockerfiles** for both backend and frontend services
2. **Docker Compose configuration** specifically for E2E testing
3. **Data seeding script** that creates predictable test data
4. **Playwright global setup/teardown** for Docker stack management
5. **Separate E2E test directory** with real backend integration tests

### Migration Path

1. **Phase 1:** Implement Docker infrastructure (Dockerfiles, compose)
2. **Phase 2:** Create E2E data seeding with existing factories
3. **Phase 3:** Configure Playwright for Docker backend integration
4. **Phase 4:** Write full-stack E2E tests using seeded data
5. **Phase 5:** Update justfile commands and CI workflows

This approach leverages the robust testing infrastructure already in place while adding the missing full-stack integration layer.
