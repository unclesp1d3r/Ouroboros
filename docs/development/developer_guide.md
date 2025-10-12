# Ouroboros Developer Guide

Ouroboros is a distributed password cracking management system built with FastAPI and SvelteKit. It coordinates multiple agents running hashcat to efficiently distribute password cracking tasks across a network of machines.

---

## Table of Contents

<!-- mdformat-toc start --slug=gitlab --no-anchors --maxlevel=3 --minlevel=1 -->

- [Ouroboros Developer Guide](#ouroboros-developer-guide)
  - [Table of Contents](#table-of-contents)
  - [1. Project Architecture & Core Concepts](#1-project-architecture-core-concepts)
    - [Project Overview](#project-overview)
    - [Data Models & Relationships](#data-models-relationships)
    - [API Interfaces & Router Mapping](#api-interfaces-router-mapping)
    - [Project Context Management](#project-context-management)
    - [Real-time Updates (Server-Sent Events)](#real-time-updates-server-sent-events)
    - [Hash List Management](#hash-list-management)
    - [Crackable Uploads](#crackable-uploads)
    - [Attack Resource Management](#attack-resource-management)
    - [Agent, Attack, and Task Lifecycle](#agent-attack-and-task-lifecycle)
    - [Resource Storage & Security](#resource-storage-security)
    - [Docker, Deployment, and Scaling](#docker-deployment-and-scaling)
    - [Logging, Caching, and Authentication](#logging-caching-and-authentication)
    - [Testing & Validation](#testing-validation)
  - [2. UI Style & Component Guide](#2-ui-style-component-guide)
    - [Color & Theme](#color-theme)
    - [Layout & Spacing](#layout-spacing)
    - [Typography](#typography)
    - [Components](#components)
    - [Behavioral Expectations](#behavioral-expectations)
    - [Branding & Iconography](#branding-iconography)
    - [Responsive & Accessibility](#responsive-accessibility)
  - [3. Code Style & Structure](#3-code-style-structure)
  - [4. API Design & Conventions](#4-api-design-conventions)
    - [New API Patterns](#new-api-patterns)
  - [5. Testing & Quality Assurance](#5-testing-quality-assurance)
    - [Current Test Infrastructure (Phase 2 Complete)](#current-test-infrastructure-phase-2-complete)
    - [Testing Frameworks & Tools](#testing-frameworks-tools)
    - [Specialized Test Areas](#specialized-test-areas)
    - [Future Enhancements](#future-enhancements)
  - [6. Tooling & Dependency Management](#6-tooling-dependency-management)
  - [7. Security Best Practices](#7-security-best-practices)
  - [8. Frontend & UX Guidelines](#8-frontend-ux-guidelines)
  - [9. Git & Commit Standards](#9-git-commit-standards)
  - [10. Protected Zones](#10-protected-zones)

<!-- mdformat-toc end -->

---

## 1. Project Architecture & Core Concepts

### Project Overview

- **Distributed password cracking** with FastAPI, SvelteKit, and Hashcat agents
- **Multi-versioned API**: v1 (legacy, OpenAPI 3.0.1, strict contract), v2 (FastAPI-native, idiomatic, breaking changes allowed)
- **Backend stack**: FastAPI, SQLAlchemy, Celery, Cashews, MinIO, Redis, Nginx
- **Frontend**: SvelteKit, JSON API, Shadcn-Svelte + Flowbite components

### Data Models & Relationships

- **Project**: Top-level boundary; isolates agents, campaigns, hash lists, users
- **Campaign**: Group of attacks targeting a hash list; belongs to one project
- **Attack**: Cracking config (mode, rules, masks, charsets); belongs to one campaign
- **Task**: Unit of work assigned to an agent; belongs to one attack
- **HashList**: Set of hashes; linked to campaigns (many-to-one)
- **HashItem**: Individual hash; can belong to many hash lists (many-to-many)
- **Agent**: Registered client; reports benchmarks, maintains heartbeat
- **CrackResult**: Record of a cracked hash; links attack, hash item, agent
- **AgentError**: Fault reported by agent; always belongs to one agent, may link to attack
- **Session**: Tracks task execution lifecycle
- **Audit**: Log of user/system actions
- **User**: Authenticated entity; role- and project-scoped
- **AttackResourceFile**: Reusable cracking resources (wordlists, rules, masks, charsets)

#### Relationships

- Project has many Campaigns; Campaign belongs to one Project
- User may belong to many Projects; Project may have many Users (many-to-many)
- Campaign has many Attacks; Attack belongs to one Campaign
- Attack has one or more Tasks; Task belongs to one Attack
- Campaign is associated with a single HashList; HashList can be associated with many Campaigns (many-to-one)
- HashList has many HashItems; HashItem can belong to many HashLists (many-to-many)
- CrackResult is associated with one Attack, one HashItem, and one Agent
- AgentError always belongs to one Agent, may be associated with one Attack
- Join tables (e.g., AgentsProjects) enforce multi-tenancy and cross-linking

### API Interfaces & Router Mapping

- **Agent API** (`/api/v1/client/*`):
  - Endpoints: agents, attacks, tasks, crackers, configuration, authenticate
  - Each resource in its own router file under `app/api/v1/endpoints/agent/`
  - Root-level endpoints grouped in `general.py`
- **Web UI API** (`/api/v1/web/*`):
  - Endpoints: campaigns, attacks, agents, dashboard, hash_lists, resources, uploads, live events
  - Routers in `app/api/v1/endpoints/web/`
  - Includes real-time SSE endpoints under `/live/*`
- **Control API** (`/api/v1/control/*`):
  - Endpoints: campaigns, attacks, agents, stats
  - Routers in `app/api/v1/endpoints/control/`
  - RFC9457-compliant error responses
- **Shared Infrastructure API**: e.g., `/api/v1/users`, `/api/v1/resources/{id}/download`
  - Endpoints used by all major interfaces, implemented in shared routers

### Project Context Management

Ouroboros enforces strict project-based isolation. Users can belong to multiple projects, and the system tracks an "active project" context for each user session:

- **Context Endpoints**:
  - `GET /api/v1/web/auth/context` - Get current user + project context
  - `POST /api/v1/web/auth/context` - Switch active project
- **Behavior**: Active project determines scope for campaigns, attacks, agents, resources
- **Security**: Users can only switch to projects they're assigned to
- **UI Integration**: Project selector in sidebar/navbar, triggers context switch
- **Session Management**: Active project stored in secure HTTP-only cookies
- **Access Control**: All Web UI endpoints respect active project context

### Real-time Updates (Server-Sent Events)

Ouroboros v2 uses Server-Sent Events (SSE) for real-time notifications:

- **Architecture**: In-memory event broadcasting, no Redis dependency
- **Event Types**: Campaign updates, agent status, toast notifications
- **SSE Endpoints**:
  - `GET /api/v1/web/live/campaigns` - Campaign/attack/task state changes
  - `GET /api/v1/web/live/agents` - Agent status and performance updates
  - `GET /api/v1/web/live/toasts` - Crack results and system notifications
- **Message Format**: Lightweight JSON triggers (`{"trigger": "refresh", "timestamp": "..."}`)
- **Client Behavior**: SSE triggers targeted fetch requests, no direct data push
- **Security**: JWT authentication, project-scoped filtering
- **Event Service**: `app/core/services/event_service.py` handles broadcasting
- **Integration**: Service layer methods trigger events with `# SSE_TRIGGER:` comments

### Hash List Management

Hash lists are fundamental components for organizing and managing target hashes:

- **Core Features**: Create, view, update, delete hash lists within project scope
- **Hash Items**: Individual hashes with metadata (salt, encoding, user-defined JSONB data)
- **Status Tracking**: Cracked vs uncracked status, progress monitoring
- **Export Support**: TSV and CSV export of hash items
- **Project Isolation**: Hash lists are project-scoped, never shared across projects
- **Cross-project Updates**: Hash cracks update all instances but don't reveal source
- **Dynamic Generation**: Agent downloads contain only uncracked hashes
- **Zap Lists**: Agents receive updates when hashes are cracked by other agents

### Crackable Uploads

Streamlined workflow for non-technical users to upload and process various file types:

- **Supported Inputs**:
  - File uploads (`.zip`, `.docx`, `.pdf`, `.kdbx`) for hash extraction
  - Pasted hash text (shadow files, NTLM pairs, secretsdump output)
- **Processing Pipeline**:
  - Automatic hash detection and validation using name-that-hash
  - Hash type identification with confidence scores
  - Campaign and attack generation with default configurations
  - Preview/confirmation before launch
  - Background processing with real-time status updates
- **Upload Endpoints**:
  - `POST /api/v1/web/uploads/` - Upload file or hash data
  - `GET /api/v1/web/uploads/{id}/status` - Check processing status
  - `POST /api/v1/web/uploads/{id}/launch_campaign` - Create campaign from upload
  - `GET /api/v1/web/uploads/{id}/errors` - View processing errors
  - `DELETE /api/v1/web/uploads/{id}` - Remove failed uploads
- **Dynamic Wordlists**: Auto-generate wordlists from usernames/passwords in uploads

### Attack Resource Management

Comprehensive system for managing reusable cracking resources:

- **Resource Types**: `mask_list`, `rule_list`, `word_list`, `charset`, `dynamic_word_list`
- **Storage**: MinIO S3-compatible backend with metadata in database
- **Editing**: Line-oriented editing for small files (configurable thresholds), download/reupload for large files
- **Ephemeral Resources**: Attack-specific resources that don't persist beyond attack lifecycle
- **Validation**: Per-line syntax validation for masks, rules, charsets
- **Export/Import**: JSON-based attack and campaign templates with resource references
- **AttackResourceFile Model**: Enhanced with `guid`, `resource_type`, `line_count`, `byte_size`, `content` fields
- **Edit Restrictions**: Configurable via `RESOURCE_EDIT_MAX_SIZE_MB` and `RESOURCE_EDIT_MAX_LINES`
- **Line Editing API**:
  - `GET /api/v1/web/resources/{id}/content` - Get editable content
  - `PUT /api/v1/web/resources/{id}/content` - Update content with validation
  - `POST /api/v1/web/resources/{id}/lines` - Add new lines
  - `DELETE /api/v1/web/resources/{id}/lines/{line_id}` - Remove lines

### Agent, Attack, and Task Lifecycle

- **Agent States**: `pending` → `active` → `stopped` → `error`
- **Attack Modes**: dictionary, mask, hybrid, brute force (UI-friendly incremental)
- **Attack Features**: Position ordering, complexity scoring, user comments, lifecycle states
- **Task Lifecycle**: creation → assignment → progress → result → completion/abandonment
- **Task Features**: keyspace distribution, progress tracking, real-time status, error handling
- **Enhanced Attack Model**: Added `position`, `comment`, `complexity_score` fields for UI ordering

### Resource Storage & Security

- **MinIO S3** for all static attack resources (wordlists, rules, masks, charsets)
- **File organization**: UUID-based names, metadata for original filename/version
- **Security**: Bucket policies, presigned URLs, role-based access, server-side encryption, TLS, virus scanning, file type verification
- **Monitoring**: Access logs, usage metrics, error tracking, quotas
- **Web UI requirements**: Direct file uploads, progress tracking, checksum verification, resource management, file preview, tagging, categorization
- **MinIO Bucket Structure**:
  - `wordlists/`: Dictionary attack word lists
  - `rules/`: Hashcat rule files
  - `masks/`: Mask pattern files
  - `charsets/`: Custom charset definitions
  - `temp/`: Temporary storage for uploads

### Docker, Deployment, and Scaling

#### Required Services (Docker Compose)

- `app`: FastAPI application (Python 3.13, uv, health checks, graceful shutdown)
- `db`: PostgreSQL 16+ (persistent volume, automated backups)
- `redis`: Redis (session storage, rate limiting, task queue backend)
- `minio`: MinIO (S3-compatible object storage for attack resources)
- `nginx`: Nginx reverse proxy (SSL termination, static file serving)
- _(Optional)_: Prometheus, Grafana, Node exporter, Cadvisor for monitoring

#### File/Directory Layout

- All service Dockerfiles under `docker/<service>/Dockerfile[.dev|.prod]`
- Compose files: `docker-compose.yml`, `docker-compose.dev.yml`, `docker-compose.prod.yml` at project root
- `.dockerignore` at project root; must exclude `.venv`, `node_modules`, test artifacts, and secrets

#### Dockerfile & Compose Conventions

- Use Python 3.13 base image for app, `uv` as package manager
- Health checks for all long-running services
- All containers run as non-root users
- Multi-stage builds for app image
- Expose only required ports
- Use environment variables for all secrets/config
- Named volumes for persistent data (db, redis, minio)
- `depends_on` for service startup order
- `.env` or `env.example` for environment variable documentation
- All services must have restart policies set (`unless-stopped` or `always`)
- Nginx mounts `./static` and `./certs` for static files and SSL

#### Security

- No hardcoded secrets in Dockerfiles or Compose
- All secrets/configs injected via environment variables or secrets files
- All images regularly scanned for vulnerabilities
- Containers must run as non-root, with resource limits and read-only root where possible

#### Best Practices

- Use `.dockerignore` to reduce build context
- Pin package versions
- Clean up after installing packages
- Use exec form of `CMD`/`ENTRYPOINT`
- Set file permissions, configure timezone, set resource limits
- Use health checks, automate builds, and integrate with CI/CD
- Use container image scanners (e.g., Trivy, Clair)
- Document Dockerfiles and images

#### Deployment & Scaling

- Single-command deployment: `docker compose up -d`
- Automated database migrations
- Health check monitoring
- Backup and restore procedures
- Log aggregation
- Monitoring and alerting
- Zero-downtime updates and rollback
- Service replication, load balancing, DB clustering, cache distribution, storage expansion

### Logging, Caching, and Authentication

- **Logging**: All logs via `loguru`, structured, context-bound, stdout for containers
- **Caching**: Cashews only, short TTLs (≤60s), logical key prefixes, use decorators, invalidate on data change
- **Authentication**:
  - Web UI: OAuth2 (password flow), session cookies, CSRF, Argon2 passwords, project context management
  - Agent API: Bearer tokens (`csa_<agent_id>_<random>`), one per agent, auto-rotation, rate limiting
  - Control API: API keys (`cst_<user_id>_<random>`), per-user, scopes, expiration, revocation
  - All tokens: HTTPS only, auto-expire, revocable, audit-logged

### Testing & Validation

- **Current Status**: 712+ tests passing with comprehensive coverage
- **Test Organization**: 106 unit tests, 36 integration tests, contract compliance testing
- **Coverage**: 80%+ across all modules with XML reporting
- **Levels**: Unit (core logic), integration (API endpoints), contract (API compliance)
- **QA**: Type checking, linting, doc coverage, security scanning
- **Specialized Testing**:
  - SSE Testing: Mock event service for async testing, verify event broadcasting
  - Resource Testing: File upload/download, validation, line editing
  - Project Context Testing: Verify isolation and context switching
  - Crackable Upload Testing: File processing, hash detection, campaign generation
  - Agent API v1 Contract Testing: Full OpenAPI specification compliance validation

---

## 2. UI Style & Component Guide

### Color & Theme

- **Base**: Catppuccin Macchiato palette (see style-guide for full table)
- **Accent**: DarkViolet `#9400D3` (aliased as `accent` in DaisyUI)
- **Surface/Foreground**: Use `surface0`, `crust`, `text`, `subtext0` for backgrounds/foregrounds
- **No true black**; always ensure contrast for accessibility

### Layout & Spacing

- **Base**: Shadcn-Svelte + Flowbite Svelte components (migrated from DaisyUI)
- **Spacing**: `p-4` for containers, `grid-cols-6` for dashboard lists
- **Modals**: Use SvelteKit modal patterns and Shadcn-Svelte modal components

### Typography

- **Font**: System default, Shadcn-Svelte `font-sans`
- **Headings**: `text-xl` (section), `text-lg` (card/modal)
- **Body**: `text-base`, meta/help: `text-sm`

### Components

- **Buttons**: Primary (`bg-accent text-white`), Secondary (`border-accent text-accent`)
- **Badges**: Success (`bg-green-500`), Warning (`bg-yellow-400`), Error (`bg-red-600`), Info (`bg-blue-500`)
- **Modals**: Shadcn-Svelte layout, always insert into SvelteKit modal root
- **Toasts**: Persistent container in SvelteKit layout, Shadcn-Svelte toast class
- **Tables**: Shadcn-Svelte/Flowbite Svelte table, alternating row color, icon column for state/action
- **Tooltips/Validation**: Use Shadcn-Svelte/Flowbite Svelte, style tokens for info/error

### Behavioral Expectations

- Use SvelteKit form actions and JSON API for fragments, SvelteKit stores for live updates
- Modal forms submit via SvelteKit actions, return JSON API responses
- SSE updates trigger targeted fetch requests for data refresh
- Real-time updates via EventSource connections to `/api/v1/web/live/*` endpoints
- Project context switching via dropdown in sidebar/navbar

### Branding & Iconography

- **Motif**: Hexagons as overlays or decoration (inline SVG/local asset only)
- **Icons**: Lucide outline SVGs, themed with `fill="currentColor"`, stored locally
- **Attack type icons**: See style-guide for mapping

### Responsive & Accessibility

- **Min width**: 768px, no horizontal scroll on core views
- **Tables/charts**: Wrap in `overflow-x-auto`, pinned headers if feasible
- **Sidebar**: Collapses below `lg` breakpoint
- **No pixel units**: Use Shadcn-Svelte/Flowbite Svelte spacing utilities
- **All modals, alerts, components**: Keyboard accessible, ARIA-compliant

---

## 3. Code Style & Structure

- **Python Style**: `ruff format`, 4-space indent, 119-char lines, double quotes, type hints everywhere, `Annotated` for Pydantic fields, snake_case, PascalCase for models, no global mutable state, context managers, no print in prod
- **Layered Architecture**: All business logic in `app/core/services/`, never in route handlers, service methods return validated Pydantic schemas
- **Error Handling**: FastAPI `HTTPException`, custom exceptions in `app/core/exceptions.py`, RFC9457 for Control API, legacy schema for Agent API v1
- **Background Tasks**: FastAPI BackgroundTasks or `asyncio.create_task`, jobs in `app/jobs/`, idempotent/restartable
- **Type Checking**: Mypy with strict config, gradual adoption, CI integration
- **SSE Integration**: Use `# SSE_TRIGGER: <description>` comments to mark event broadcasting points

---

## 4. API Design & Conventions

- **RESTful, versioned, documented, all endpoints use Pydantic models**
- **Agent API**: v1 (must match `contracts/v1_api_swagger.json`), v2 (idiomatic, breaking changes allowed)
- **Web UI API**: `/api/v1/web/*` returns JSON API responses, SvelteKit handles rendering, full-page in SvelteKit routes, partials in SvelteKit components
- **Real-time Updates**: SSE endpoints under `/api/v1/web/live/*` for event notifications
- **Project Context**: All Web UI endpoints respect active project context from user session
- **Schema & Validation**: All request/response models in `app/schemas/`, use `example`/`description`, Pydantic v2 idioms
- **Error Handling**: Consistent error envelopes, never expose stack traces, log with loguru
- **Authentication**: JWT for API, OAuth2 for web, CSRF for forms, Argon2 passwords
- **Caching**: Cashews only, short TTLs, logical key prefixes, invalidate on data change

### New API Patterns

- **Hash List Management**: CRUD operations with project scoping, export capabilities
- **Crackable Uploads**: Multi-step upload → process → preview → launch workflow
- **Resource Management**: Line-oriented editing, validation, ephemeral vs persistent resources
- **Attack Configuration**: Complex validation, keyspace estimation, template export/import
- **Live Updates**: Event broadcasting with project filtering, lightweight trigger messages
- **Project Context**: Session-based active project tracking with secure cookie storage

---

## 5. Testing & Quality Assurance

### Current Test Infrastructure (Phase 2 Complete)

- **Test Coverage**: 712+ tests passing, 80%+ coverage across all modules
- **Test Organization**: 106 unit tests, 36 integration tests, comprehensive contract testing
- **Test Types**: Unit (service layer), Integration (API endpoints), Contract (Agent API v1 compliance)
- **Test Data**: Polyfactory-based factories in `tests/factories/`, isolated database sessions
- **CI Integration**: `just ci-check` runs all tests, lint, type check, and coverage reporting

### Testing Frameworks & Tools

- **Backend**: pytest with async SQLAlchemy support, testcontainers for isolation
- **Contract Testing**: Agent API v1 validation against `contracts/v1_api_swagger.json`
- **Coverage**: XML reporting with 80% minimum threshold
- **Linting**: Ruff for Python, stylelint for CSS, YAML lint for workflows
- **CI/CD**: GitHub Actions with automated test execution and coverage reporting

### Specialized Test Areas

- **SSE Testing**: Mock event service for async testing, verify event broadcasting
- **Resource Testing**: File upload/download, validation, line editing workflows
- **Project Context Testing**: Verify isolation and context switching security
- **Crackable Upload Testing**: File processing, hash detection, campaign generation
- **Authentication Testing**: JWT, bearer tokens, API keys, session management
- **Database Testing**: Transaction isolation, migration testing, constraint validation

### Future Enhancements

- **End-to-End Testing**: Full browser automation with Playwright (planned)
- **Performance Testing**: Load testing for high-throughput scenarios
- **Security Testing**: Automated vulnerability scanning integration
- **Frontend Testing**: SvelteKit component and integration testing

For detailed testing information, see [Testing Guide](testing.md).

---

## 6. Tooling & Dependency Management

- **Python**: Use `uv` for all dependency management (`uv add/remove`), never edit `pyproject.toml` or `poetry.lock` directly
- **MkDocs**: All docs in `docs/`, nav in `mkdocs.yml`, use includes/macros for reuse
- **GitHub Actions**: Workflows in `.github/workflows/`, use secrets, cache, and artifact best practices

---

## 7. Security Best Practices

- **Input Validation**: All input validated with Pydantic, never trust client data
- **Database**: Only use SQLAlchemy ORM, never raw SQL, SSL for prod DB
- **Web**: CSRF tokens for all state-changing requests, strict CORS, secure cookies, CSP headers
- **Project Isolation**: Strict project-based access control, context validation
- **Resource Security**: Presigned URLs, file type validation, virus scanning
- **General**: No secrets in code, use env vars, audit logs for auth/admin events

---

## 8. Frontend & UX Guidelines

- **SvelteKit**: Use for all dynamic updates, minimal JS, prefer Svelte stores for interactivity
- **Shadcn-Svelte & Flowbite**: Use for UI components and layout, no custom CSS unless needed
- **Svelte**: Components in `src/lib/`, use slots, props, and context, escape all user data
- **Accessibility**: All modals, alerts, and components must be keyboard accessible and ARIA-compliant
- **Dashboard**: Campaigns in cards, attacks expandable, live status with SSE polling
- **Real-time Features**: EventSource connections for live updates, graceful fallback for connection issues
- **Project Context**: Project selector in sidebar/navbar with context switching

---

## 9. Git & Commit Standards

- **Commits**: Conventional Commits: `type(scope): description`, imperative mood, no periods, use `!` for breaking changes
- **Branching**: Feature branches, short-lived, rebase/merge often, PRs for all changes
- **.gitignore**: Exclude build artifacts, secrets, and temp files
- **No secrets in repo**: Use env vars and secret managers

---

## 10. Protected Zones

- **Never auto-edit**: `alembic/`, `.cursor/`, `.github/`, `contracts/v1_api_swagger.json`
- **Markdown/docs**: Maintain by hand and keep updated when major changes are made

---

For full details and examples, see the `.cursor/rules/` directory and referenced `.mdc` files.
