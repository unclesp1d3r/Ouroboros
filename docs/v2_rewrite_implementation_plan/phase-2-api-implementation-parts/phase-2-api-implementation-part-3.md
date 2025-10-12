# Control API (API V1 Control)

The Control API powers the Ouroboros command-line (`csadmin`) and scripting interface. It exposes programmatic access to all major backend operations—campaigns, attacks, agents, hashlists, tasks, and stats—while enforcing scoped permissions based on the associated user and their API key. Unlike the Web UI API, this interface is designed purely for structured, machine-readable workflows.

If in doubt, refer to the migration plan for the Web API (found in `docs/v2_rewrite_implementation_plan/phase-2-api-implementation-parts/phase-2-api-implementation-part-2.md`) to identify areas that should have functional parity with the Web API, as well as the architecture documentation (found in `docs/architecture/*.md`). Finally, refer to the strategy document (found in `docs/strategy.md`) to understand the overall goals and intent of the project.

The Control API should be implemented in a way that is consistent with the Web API, and should be a thin wrapper around the existing services. The principal difference is that the Control API is designed for machine-readable workflows, and the Web API is designed for human-readable workflows, with the authentication and error responses being the main differences. Wherever possible, the Control API should reuse the existing services and schemas from the Web API.

Now that cashews is available, consider it when implementing an endpoint to improve performance.

---

## Table of Contents

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=2 --minlevel=1 -->

- [Control API (API V1 Control)](#control-api-api-v1-control)
  - [Table of Contents](#table-of-contents)
  - [Implementation Context Added](#implementation-context-added)
  - [Service Layer Reuse Strategy](#service-layer-reuse-strategy)
  - [Implementation Order and Dependencies](#implementation-order-and-dependencies)
  - [Authentication (Phase 1)](#authentication-phase-1)
  - [Error Handling (Phase 1)](#error-handling-phase-1)
  - [Response Format Strategy (Phase 1)](#response-format-strategy-phase-1)
  - [Project Scoping (Phase 1)](#project-scoping-phase-1)
  - [Pagination (Phase 1)](#pagination-phase-1)
  - [System Health and Stats (Phase 2)](#system-health-and-stats-phase-2)
  - [User Management (Phase 2)](#user-management-phase-2)
  - [Project Management (Phase 2)](#project-management-phase-2)
  - [HashList and HashItem Management (Phase 2)](#hashlist-and-hashitem-management-phase-2)
  - [Hash Type Detection (Phase 3)](#hash-type-detection-phase-3)
  - [Resource File Management (Phase 3)](#resource-file-management-phase-3)
  - [Campaign Management (Phase 4)](#campaign-management-phase-4)
  - [Attack Management (Phase 4)](#attack-management-phase-4)
  - [Template Import Export (Phase 4)](#template-import-export-phase-4)
  - [Agent Management (Phase 5)](#agent-management-phase-5)
  - [Task Management (Phase 5)](#task-management-phase-5)
  - [Crackable Uploads (Phase 6)](#crackable-uploads-phase-6)
  - [Live Monitoring (Phase 6)](#live-monitoring-phase-6)
  - [State Management (Implementation Note)](#state-management-implementation-note)

<!-- mdformat-toc end -->

---

## Implementation Context Added

This document has been enhanced with detailed implementation context for:

1. **🔐 API Key Authentication**: Complete database schema, dependency injection, and permission enforcement patterns
2. **📦 Content Negotiation**: MsgPack support implementation with fallback to JSON
3. **📁 Schema Compatibility**: Reuse existing `CampaignTemplate` and `AttackTemplate` from `app/schemas/shared.py`
4. **Pagination and Filtering**: Leverage existing `PaginatedResponse[T]` schema with conversion utilities
5. **🚨 Error Handling**: RFC9457-compliant error responses with standardized exception types (see `https://github.com/NRWLDev/fastapi-problem`)
6. **🔄 State Management**: State validation and progress calculation based on core algorithm rules
7. **Project Scoping**: Multi-tenant access control and data filtering utilities

## Service Layer Reuse Strategy

**Critical Implementation Principle**: The Control API maximizes reuse of existing service layer functions to minimize development effort and maintain consistency:

**✅ IMPLEMENTATION STATUS**: The foundation has been successfully implemented with a simplified authentication system using a single API key per user, reusing existing Web UI authentication patterns, and leveraging shared service functions wherever possible.

### Existing Services to Reuse

- `app/core/services/campaign_service.py` → All campaign operations
- `app/core/services/attack_service.py` → All attack operations
- `app/core/services/agent_service.py` → All agent operations
- `app/core/services/resource_service.py` → Resource file management
- `app/core/services/health_service.py` → System health checks
- `app/core/services/dashboard_service.py` → System statistics
- `app/core/services/hash_guess_service.py` → Hash type detection and validation
- `app/core/services/event_service.py` → Event broadcasting (SSE triggers)

### Existing Schemas to Reuse

- `app/schemas/shared.py` → `PaginatedResponse[T]`, `CampaignTemplate`, `AttackTemplate`
- All existing Pydantic schemas for requests/responses

### Implementation Pattern

```python
# Control API endpoints should be thin wrappers around existing services
@router.get("/campaigns")
async def list_campaigns_control(
    offset: int = 0,
    limit: int = 10,
    user: User = Depends(get_current_control_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[CampaignRead]:
    # 1. Convert pagination parameters
    # 2. Call existing service function
    # 3. Return in Control API format
    campaigns, total = await list_campaigns_service(db, skip=offset, limit=limit)
    page, page_size = control_to_web_pagination(offset, limit)
    return PaginatedResponse(
        items=campaigns, total=total, page=page, page_size=page_size
    )
```

All areas now include specific implementation code examples, database schema changes, and detailed task breakdowns focused on **maximizing reuse** of existing infrastructure.

---

## Implementation Order and Dependencies

The following sections define the logical implementation order, with foundational components first:

### Phase 1: Foundation (Core Infrastructure)

1. **Authentication System** - Must be implemented first as all other endpoints depend on it
2. **Error Handling** - Essential for proper API responses
3. **Content Negotiation** - Basic response format handling
4. **Project Scoping** - Multi-tenant access control
5. **Pagination Utilities** - Required for all list endpoints

### Phase 2: Core Resources (Building Blocks)

1. **System Health and Stats** - Simple read-only endpoints for validation
2. **User Management** - Basic CRUD operations
3. **Project Management** - Required for campaign/resource scoping
4. **Hash List Management** - Foundational for campaigns

### Phase 3: Attack Resources (Content Management)

1. **Resource File Management** - Required for attacks
2. **Hash Type Detection** - Required for campaign creation

### Phase 4: Campaign and Attack Management (Core Business Logic)

1. **Campaign Management** - Core workflow functionality
2. **Attack Management** - Depends on campaigns and resources
3. **Template Import Export** - Advanced campaign/attack functionality

### Phase 5: Agent and Task Management (Runtime Operations)

1. **Agent Management** - Runtime system control
2. **Task Management** - Operational monitoring and control

### Phase 6: Advanced Features (Enhanced Functionality)

1. **Crackable Uploads** - Advanced workflow automation
2. **Live Monitoring** - Real-time status updates
3. **Advanced Analytics** - Performance optimization features

---

## Authentication (Phase 1)

The Control API uses **persistent API keys** rather than JWT-based sessions.

### API Key Structure

- Every user is issued a **single API key** at account creation that grants the same permissions as if the user was accessing the system via the Web UI (no distinction between read-only and full access keys)

- All requests must send the API key via:

  ```http
  Authorization: Bearer <api_key>
  ```

- **API Key Format**: `cst_<user_id>_<random_string>` (similar to agent tokens but with `cst` prefix for "Ouroboros TUI")

### Database Schema

The `User` model has been updated with a single API key field:

```python
class User(Base):
    # ... existing fields ...
    api_key: Mapped[str | None] = mapped_column(
        String(128), unique=True, nullable=True, index=True
    )
```

**Note**: The previous dual API key system (`api_key_full` and `api_key_readonly`) has been simplified to a single `api_key` field. Migration has been completed to consolidate existing keys.

### Authentication Dependency

Create a Control API authentication dependency:

```python
async def get_current_control_user(
    authorization: str = Header(None), db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get the current authenticated user from API key for Control API.
    Uses the same logic as the Web UI authentication with pre-loaded relationships.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing or invalid Authorization header")

    api_key = authorization.replace("Bearer ", "").strip()

    # Validate format: cst_<uuid>_<random>
    if not api_key.startswith("cst_"):
        raise HTTPException(401, "Invalid API key format")

    # Look up user by api_key with pre-loaded project associations
    result = await db.execute(
        select(User)
        .where(User.api_key == api_key)
        .options(selectinload(User.project_associations))
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(401, "Invalid API key")

    if not user.is_active:
        raise HTTPException(403, "Inactive user")

    return user
```

### Implementation Tasks

- [x] Add API key field to User model and create migration ✅ **COMPLETED** `task_id:control.auth.user_model_fields`
- [x] Add functionality to create the API key in the database during user creation ✅ **COMPLETED** `task_id:control.auth.create_keys`
- [x] Implement `get_current_control_user` dependency ✅ **COMPLETED** `task_id:control.auth.api_key_dependency`
- [x] Add API key generation utility functions (format: `cst_<user_id>_<random>`) ✅ **COMPLETED** `task_id:control.auth.key_generation`
- [x] Add a test to verify that a user with an API key can access endpoints ✅ **COMPLETED** `task_id:control.auth.api_key_test`
- [x] Add functionality to allow a user to rotate their API key ✅ **COMPLETED** `task_id:control.auth.rotate_keys`

---

## Error Handling (Phase 1)

All errors must return machine-parseable JSON in RFC9457 format. We'll use the [`fastapi-problem`](https://github.com/NRWLDev/fastapi-problem) library for automatic compliance.

```json
{
  "type": "campaign-not-found",
  "title": "Campaign Not Found",
  "status": 404,
  "detail": "Campaign with ID 'camp_123' does not exist or is not accessible",
  "instance": "/api/v1/control/campaigns/camp_123"
}
```

### FastAPI-Problem Integration

Add the dependency and configure error handling:

```bash
# Add dependency
uv add fastapi-problem
```

```python
# app/api/v1/endpoints/control/__init__.py
from fastapi import APIRouter
from fastapi_problem.handler import add_exception_handler, new_exception_handler

control_router = APIRouter(prefix="/api/v1/control", tags=["control"])

# Configure RFC9457 error handling
eh = new_exception_handler()
add_exception_handler(app, eh)  # Register globally or per router
```

### Custom Control API Exceptions

Define domain-specific error types using the library's base classes:

```python
# app/core/control_exceptions.py
from fastapi_problem.error import NotFoundProblem, BadRequestProblem, ForbiddenProblem


class CampaignNotFoundError(NotFoundProblem):
    title = "Campaign Not Found"


class AttackNotFoundError(NotFoundProblem):
    title = "Attack Not Found"


class AgentNotFoundError(NotFoundProblem):
    title = "Agent Not Found"


class InvalidAttackConfigError(BadRequestProblem):
    title = "Invalid Attack Configuration"


class InsufficientPermissionsError(ForbiddenProblem):
    title = "Insufficient Permissions"


class ProjectAccessDeniedError(ForbiddenProblem):
    title = "Project Access Denied"


# Usage in endpoints:
# raise CampaignNotFoundError(detail=f"Campaign with ID '{campaign_id}' not found")
```

### Implementation Tasks

- [x] Add `fastapi-problem` dependency ✅ **COMPLETED** `task_id:control.error.add_dependency` - Includes adding the new_exception_handler to the app
- [x] Create custom Control API exception classes ✅ **COMPLETED** `task_id:control.error.custom_exceptions`
- [x] Configure exception handler for Control API router ✅ **COMPLETED** `task_id:control.error.configure_handler`
- [x] Update all Control API endpoints to use custom exceptions ✅ **COMPLETED** `task_id:control.error.update_endpoints`

---

## Response Format Strategy (Phase 1)

- All responses are **JSON** by default, using Pydantic v2 models
- MsgPack support was considered but abandoned in favor of focusing on JSON only for simplicity
- All endpoints return structured JSON responses using existing Pydantic schemas

---

## Project Scoping (Phase 1)

All routes in `/api/v1/control/*` must enforce **project scoping** — a user can only access agents, campaigns, and attacks from projects they're assigned to. The project scoping should use the same services as the Web API.

### Project Scoping Implementation

Create project access checking utilities:

```python
async def get_user_accessible_projects(user: User, db: AsyncSession) -> list[int]:
    """Get list of project IDs that the user has access to."""
    # Query user's project associations
    # Return list of project IDs


async def check_project_access(user: User, project_id: int, db: AsyncSession) -> bool:
    """Check if user has access to a specific project."""
    accessible_projects = await get_user_accessible_projects(user, db)
    return project_id in accessible_projects


def require_project_access(project_id: int):
    """Dependency factory to check project access."""

    async def _check_access(
        user: User = Depends(get_current_control_user),
        db: AsyncSession = Depends(get_db),
    ):
        if not await check_project_access(user, project_id, db):
            raise HTTPException(403, f"Access denied to project {project_id}")
        return user

    return _check_access
```

### Data Filtering by Project

All list endpoints must filter by user's accessible projects:

```python
async def filter_campaigns_by_project_access(
    query: Select, user: User, db: AsyncSession
) -> Select:
    """Add project filtering to campaign queries."""
    accessible_projects = await get_user_accessible_projects(user, db)
    return query.where(Campaign.project_id.in_(accessible_projects))
```

### Implementation Tasks

- [x] Create project access utilities and dependencies ✅ **COMPLETED** `task_id:control.access.project_utilities`
- [x] Add project filtering to all list endpoints ✅ **COMPLETED** `task_id:control.access.project_filtering`
- [x] Add project access checks to detail endpoints `task_id:control.access.detail_checks`

---

## Pagination (Phase 1)

- **Reuse Existing**: Control API must use the existing `PaginatedResponse[T]` from `app/schemas/shared.py`
- Convert between Web UI pagination (page-based) and Control API pagination (offset-based):

```python
from app.schemas.shared import PaginatedResponse


def web_to_control_pagination(page: int, page_size: int) -> tuple[int, int]:
    """Convert page-based to offset-based pagination."""
    offset = (page - 1) * page_size
    limit = page_size
    return offset, limit


def control_to_web_pagination(offset: int, limit: int) -> tuple[int, int]:
    """Convert offset-based to page-based pagination."""
    page = (offset // limit) + 1
    page_size = limit
    return page, page_size
```

### Reuse Existing Service Functions

All Control API list endpoints should leverage existing service layer functions:

```python
# Campaign listing - reuse existing service
from app.core.services.campaign_service import list_campaigns_service


async def control_list_campaigns(
    offset: int = 0,
    limit: int = 10,
    project_id: int | None = None,
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[CampaignRead]:
    # Convert offset/limit to page/page_size for existing service
    page, page_size = control_to_web_pagination(offset, limit)
    campaigns, total = await list_campaigns_service(
        db=db, skip=offset, limit=limit, project_id=project_id
    )
    return PaginatedResponse(
        items=campaigns, total=total, page=page, page_size=page_size
    )
```

### Implementation Tasks

- [x] Create pagination conversion utilities ✅ **COMPLETED** `task_id:control.pagination.conversion_utils`
- [x] Adapt existing service functions for Control API pagination `task_id:control.pagination.service_adaptation` ✅ **COMPLETED** (there's now an OffsetPagination class in the shared.py file and we should use that instead with the control API)

---

## System Health and Stats (Phase 2)

These endpoints provide status introspection and control-plane telemetry for `csadmin` dashboards or monitoring tooling. They can be queried manually or polled from background health checks or TUI dashboards.

### Implementation Tasks

**Reuse Existing Services**: All endpoints should leverage existing service layer functions:

- [x] `GET /api/v1/control/system/status` - System health → Use `health_service.py` functions ✅ **COMPLETED** `task_id:control.system.status`
- [x] `GET /api/v1/control/system/version` - API version → Create version service or use existing config ✅ **COMPLETED** `task_id:control.system.version`
- [x] `GET /api/v1/control/system/queues` - Queue status → Create queue monitoring service ✅ **COMPLETED** `task_id:control.system.queue_depth`
- [x] `GET /api/v1/control/system/stats` - System stats → Use `dashboard_service.py` for `DashboardSummary` schema ✅ **COMPLETED** `task_id:control.system.summary`

---

## User Management (Phase 2)

These endpoints provide administrative access to user accounts and API key management.

### Implementation Tasks

**Reuse Existing Services**: All endpoints should leverage existing service layer functions:

- [x] `GET /api/v1/control/users` - List users → Use existing user listing service `task_id:control.user.list`
- [x] `GET /api/v1/control/users/{id}` - User detail → Use existing user detail service ✅ **COMPLETED** `task_id:control.user.detail`
- [x] `POST /api/v1/control/users/` - Create user → Use existing user creation service ✅ **COMPLETED** `task_id:control.user.create`
- [x] `PATCH /api/v1/control/users/{id}` - Update user → Use existing user update service ✅ **COMPLETED** `task_id:control.user.update`
- [x] `DELETE /api/v1/control/users/{id}` - Delete user → Use existing user deletion service ✅ **COMPLETED** `task_id:control.user.delete`
- [x] `POST /api/v1/control/users/{id}/rotate-keys` - Rotate API keys → Create key rotation service `task_id:control.user.rotate_keys` ✅ **COMPLETED**
- [x] `GET /api/v1/control/users/{id}/api-keys` - View API key info → Create key info service `task_id:control.user.api_key_info` ✅ **COMPLETED**

---

## Project Management (Phase 2)

These endpoints provide administrative access to project management and user assignments.

### Implementation Tasks

**Reuse Existing Services**: All endpoints should leverage existing service layer functions:

- [x] `GET /api/v1/control/projects` - List projects → Use existing project listing service ✅ **COMPLETED** `task_id:control.project.list`
- [x] `GET /api/v1/control/projects/{id}` - Project detail → Use existing project detail service ✅ **COMPLETED** `task_id:control.project.detail`
- [x] `POST /api/v1/control/projects/` - Create project → Use existing project creation service ✅ **COMPLETED** `task_id:control.project.create`
- [x] `PATCH /api/v1/control/projects/{id}` - Update project → Use existing project update service ✅ **COMPLETED** `task_id:control.project.update`
- [x] `DELETE /api/v1/control/projects/{id}` - Delete project → Use existing project deletion service ✅ **COMPLETED** `task_id:control.project.delete`
- [x] `GET /api/v1/control/projects/{id}/users` - List project users → Create project user listing service ✅ **COMPLETED** `task_id:control.project.list_users`
- [ ] `POST /api/v1/control/projects/{id}/users` - Add user to project → Create user assignment service `task_id:control.project.add_user`
- [ ] `DELETE /api/v1/control/projects/{id}/users/{user_id}` - Remove user from project → Create user removal service `task_id:control.project.remove_user`

---

## HashList and HashItem Management (Phase 2)

These endpoints support importing, exporting, filtering, and inspecting hash lists and individual hash items. Export formats include plaintext-only wordlists, JtR `.pot` files, and CSV metadata dumps. Ingested files can be simple hash lines or CSV/JSON with structured metadata (e.g., source system, associated username, tags).

### Implementation Tasks

**Reuse Existing Services**: All endpoints should leverage existing service layer functions (check for hash list services):

- [ ] `GET /api/v1/control/hashlists` - List hash lists → Use existing hash list service `task_id:control.hashlist.list`
- [ ] `GET /api/v1/control/hashlists/{id}` - Hash list detail → Use existing hash list service `task_id:control.hashlist.detail`
- [ ] `POST /api/v1/control/hashlists/` - Create hash list → Use existing hash list service `task_id:control.hashlist.create`
- [ ] `PATCH /api/v1/control/hashlists/{id}` - Update hash list → Use existing hash list service `task_id:control.hashlist.update`
- [ ] `DELETE /api/v1/control/hashlists/{id}` - Delete hash list → Use existing hash list service `task_id:control.hashlist.delete`
- [ ] `POST /api/v1/control/hashlists/import` - Import hashlists → Use existing hash import service `task_id:control.hashlist.import`
- [ ] `GET /api/v1/control/hashlists/{id}/export/plaintext` - Export plaintext → Create export service `task_id:control.hashlist.export_plaintext`
- [ ] `GET /api/v1/control/hashlists/{id}/export/potfile` - Export pot file → Create export service `task_id:control.hashlist.export_potfile`
- [ ] `GET /api/v1/control/hashlists/{id}/export/csv` - Export CSV → Create export service `task_id:control.hashlist.export_csv`
- [ ] `GET /api/v1/control/hashitems` - List hash items → Create hash item listing service `task_id:control.hashitem.list_filtered`
- [ ] `GET /api/v1/control/hashitems/{id}` - Hash item detail → Create hash item detail service `task_id:control.hashitem.detail`

---

## Hash Type Detection (Phase 3)

These endpoints provide hash type detection and validation capabilities for automated workflows.

### Implementation Tasks

**Reuse Existing Services**: All endpoints should leverage existing service layer functions:

- [x] `POST /api/v1/control/hash/guess` - Detect hash type → Use `hash_guess_service.py` ✅ **COMPLETED** `task_id:control.hash.guess`
- [ ] `POST /api/v1/control/hash/validate` - Validate hash format → Use hash validation service `task_id:control.hash.validate`
- [ ] `GET /api/v1/control/hash/types` - List supported hash types → Use existing hash type service `task_id:control.hash.types`

---

## Resource File Management (Phase 3)

These endpoints allow users to upload, inspect, assign, and delete custom resource files: wordlists, rule files, and mask files. This supports scripted population of project resources, ephemeral file tracking, and file reuse across campaigns.

### Implementation Tasks

**Reuse Existing Services**: All endpoints should leverage existing service layer functions from `app/core/services/resource_service.py`:

- [ ] `GET /api/v1/control/resources` - List resources → Use existing resource listing service (check `resource_service.py`) `task_id:control.resource.list`
- [ ] `GET /api/v1/control/resources/{id}` - Resource detail → Use existing resource detail service `task_id:control.resource.detail`
- [ ] `POST /api/v1/control/resources/` - Upload resource → Use existing resource upload service `task_id:control.resource.upload`
- [ ] `PATCH /api/v1/control/resources/{id}` - Update resource metadata → Use existing resource update service `task_id:control.resource.update`
- [ ] `DELETE /api/v1/control/resources/{id}` - Delete resource → Use existing resource deletion service `task_id:control.resource.delete`
- [ ] `GET /api/v1/control/resources/{id}/content` - Get resource content → Use existing content service `task_id:control.resource.content`
- [ ] `PATCH /api/v1/control/resources/{id}/content` - Update resource content → Use existing content update service `task_id:control.resource.update_content`
- [ ] `POST /api/v1/control/resources/{id}/assign` - Assign resource → Use existing resource assignment service `task_id:control.resource.assign`
- [ ] `GET /api/v1/control/resources/{id}/lines` - Get resource lines → Use existing line service `task_id:control.resource.lines`
- [ ] `POST /api/v1/control/resources/{id}/lines` - Add resource line → Use existing line creation service `task_id:control.resource.add_line`
- [ ] `PATCH /api/v1/control/resources/{id}/lines/{line_id}` - Update resource line → Use existing line update service `task_id:control.resource.update_line`
- [ ] `DELETE /api/v1/control/resources/{id}/lines/{line_id}` - Delete resource line → Use existing line deletion service `task_id:control.resource.delete_line`

---

## Campaign Management (Phase 4)

These endpoints allow creation, inspection, lifecycle control, and relaunching of campaigns. They mirror the Web UI capabilities, but return only machine-structured JSON.

Clients using `csadmin` or automated scripts must be able to create and manage campaigns via JSON payloads that follow the same schema used by the Web UI. Control API endpoints must support full campaign lifecycle management, including relaunching failed or modified attacks. Campaign metadata (e.g., name, visibility, active state) must be editable, but the server must reject any attempts to modify campaigns that are in a finalized state unless reactivation is explicitly requested. All validation logic (e.g., attached attacks, project membership, resource constraints) must match Web UI behavior to ensure parity.

### Implementation Tasks

**Reuse Existing Services**: All endpoints should leverage existing service layer functions from `app/core/services/campaign_service.py`:

- [ ] `GET /api/v1/control/campaigns` - List campaigns → Use `list_campaigns_service()` `task_id:control.campaign.list`
- [ ] `GET /api/v1/control/campaigns/{id}` - Campaign detail → Use `get_campaign_service()` `task_id:control.campaign.detail`
- [ ] `POST /api/v1/control/campaigns/` - Create campaign → Use `create_campaign_service()` `task_id:control.campaign.create`
- [ ] `PATCH /api/v1/control/campaigns/{id}` - Update campaign → Use `update_campaign_service()` `task_id:control.campaign.update`
- [ ] `POST /api/v1/control/campaigns/{id}/start` - Start campaign → Use `start_campaign_service()` `task_id:control.campaign.start`
- [ ] `POST /api/v1/control/campaigns/{id}/stop` - Stop campaign → Use `stop_campaign_service()` `task_id:control.campaign.stop`
- [ ] `POST /api/v1/control/campaigns/{id}/relaunch` - Relaunch campaign → Use `relaunch_campaign_service()` `task_id:control.campaign.relaunch`
- [ ] `DELETE /api/v1/control/campaigns/{id}` - Delete campaign → Use `delete_campaign_service()` `task_id:control.campaign.delete`
- [ ] `GET /api/v1/control/campaigns/{id}/progress` - Campaign progress → Use `get_campaign_progress_service()` `task_id:control.campaign.progress`
- [ ] `GET /api/v1/control/campaigns/{id}/metrics` - Campaign metrics → Use `get_campaign_metrics_service()` `task_id:control.campaign.metrics`
- [ ] `POST /api/v1/control/campaigns/{id}/reorder_attacks` - Reorder attacks → Use `reorder_attacks_service()` `task_id:control.campaign.reorder_attacks`

---

## Attack Management (Phase 4)

Attack management in the Control API mirrors the Web UI.

Clients (e.g., `csadmin`) must be able to create, inspect, and modify attacks using the same JSON template structure used by the Web UI. The API must prevent edits to attacks currently in `running` or `exhausted` state unless the client explicitly confirms that the attack should be reset and re-queued. All validation logic (e.g., for resource compatibility, hash mode constraints, or ephemeral inputs) must mirror the same rules enforced by the UI. This interface should also support attack preview or performance summary queries for tooling to make informed scheduling decisions. Endpoints support attack creation, validation, lifecycle management, performance review, and JSON export/import using the shared format.

### Implementation Tasks

**Reuse Existing Services**: All endpoints should leverage existing service layer functions from `app/core/services/attack_service.py`:

- [ ] `GET /api/v1/control/attacks` - List attacks → Use `get_attack_list_service()` `task_id:control.attack.list`
- [ ] `GET /api/v1/control/attacks/{id}` - Attack detail → Use `get_attack_service()` `task_id:control.attack.detail`
- [ ] `POST /api/v1/control/attacks/` - Create attack → Use `create_attack_service()` `task_id:control.attack.create`
- [ ] `PATCH /api/v1/control/attacks/{id}` - Update attack → Use `update_attack_service()` `task_id:control.attack.update`
- [ ] `DELETE /api/v1/control/attacks/{id}` - Delete attack → Use `delete_attack_service()` `task_id:control.attack.delete`
- [ ] `POST /api/v1/control/attacks/validate` - Validate attack → Use `estimate_attack_keyspace_and_complexity()` `task_id:control.attack.validate`
- [ ] `POST /api/v1/control/attacks/estimate` - Estimate attack → Use `estimate_attack_keyspace_and_complexity()` `task_id:control.attack.estimate`
- [ ] `GET /api/v1/control/attacks/{id}/performance` - Performance data → Use `get_attack_performance_summary_service()` `task_id:control.attack.performance`
- [ ] `POST /api/v1/control/attacks/{id}/move` - Move attack position → Use `move_attack_service()` `task_id:control.attack.move`
- [ ] `POST /api/v1/control/attacks/{id}/duplicate` - Duplicate attack → Use `duplicate_attack_service()` `task_id:control.attack.duplicate`
- [ ] `DELETE /api/v1/control/attacks/bulk` - Bulk delete attacks → Use `bulk_delete_attacks_service()` `task_id:control.attack.bulk_delete`

---

## Template Import Export (Phase 4)

- **Reuse Existing**: All export/import functionality must use the existing `CampaignTemplate` and `AttackTemplate` from `app/schemas/shared.py`
- No divergence is allowed between interfaces

### Existing Template Schemas

The Control API must reuse these existing schemas:

```python
from app.schemas.shared import CampaignTemplate, AttackTemplate

# Already implemented in shared.py:
# - CampaignTemplate: Complete campaign export/import structure
# - AttackTemplate: Attack configuration template with all modes
# - AttackTemplateRecordOut: Template record metadata
# - Schema version: "20250511" for compatibility tracking
```

### Reuse Existing Service Functions

Leverage existing template services:

```python
# Campaign export - reuse existing service
from app.core.services.campaign_service import export_campaign_template_service


async def control_export_campaign(
    campaign_id: int, db: AsyncSession
) -> CampaignTemplate:
    return await export_campaign_template_service(campaign_id, db)


# Attack export - reuse existing service
from app.core.services.attack_service import export_attack_template_service


async def control_export_attack(attack_id: int, db: AsyncSession) -> AttackTemplate:
    return await export_attack_template_service(attack_id, db)
```

### Implementation Tasks

- [ ] `POST /api/v1/control/campaigns/{id}/export` - Export template → Use `export_campaign_template_service()` `task_id:control.campaign.export`
- [ ] `POST /api/v1/control/campaigns/import` - Import campaign from `CampaignTemplate` `task_id:control.campaign.import`
- [ ] `POST /api/v1/control/attacks/{id}/export` - Export attack → Use `export_attack_template_service()` `task_id:control.attack.export`
- [ ] `POST /api/v1/control/attacks/import` - Import attack from `AttackTemplate` `task_id:control.attack.import`
- [ ] Verify Control API endpoints use existing template services `task_id:control.template.service_reuse`
- [ ] Add Control API template import functionality using existing schemas `task_id:control.template.import_functionality`

---

## Agent Management (Phase 5)

These endpoints provide structured read and write access to the full set of agents registered with Ouroboros. Agents are read-only to non-admin users, but visible to all project members. Admins can assign or restrict project access, adjust configuration, and retrieve real-time performance data.

### Implementation Tasks

**Reuse Existing Services**: All endpoints should leverage existing service layer functions from `app/core/services/agent_service.py`:

- [ ] `GET /api/v1/control/agents` - List agents → Use `list_agents_service()` `task_id:control.agent.list`
- [ ] `GET /api/v1/control/agents/{id}` - Agent detail → Use `get_agent_by_id_service()` `task_id:control.agent.detail`
- [ ] `POST /api/v1/control/agents/` - Register agent → Use `register_agent_service()` `task_id:control.agent.register`
- [ ] `PATCH /api/v1/control/agents/{id}` - Update agent → Use `update_agent_service()` or `toggle_agent_enabled_service()` `task_id:control.agent.update`
- [ ] `PATCH /api/v1/control/agents/{id}/config` - Update config → Use `update_agent_config_service()` or `update_agent_hardware_service()` `task_id:control.agent.config`
- [ ] `GET /api/v1/control/agents/{id}/performance` - Performance data → Use `get_agent_device_performance_timeseries()` `task_id:control.agent.performance`
- [ ] `GET /api/v1/control/agents/{id}/errors` - Error logs → Use `get_agent_error_log_service()` `task_id:control.agent.errors`
- [ ] `POST /api/v1/control/agents/{id}/benchmark` - Trigger benchmark → Use `trigger_agent_benchmark_service()` `task_id:control.agent.benchmark`
- [ ] `GET /api/v1/control/agents/{id}/benchmarks` - Benchmark summary → Use `get_agent_benchmark_summary_service()` `task_id:control.agent.benchmark_summary`
- [ ] `GET /api/v1/control/agents/{id}/hardware` - Hardware info → Use existing hardware service `task_id:control.agent.hardware`
- [ ] `PATCH /api/v1/control/agents/{id}/hardware` - Update hardware → Use existing hardware update service `task_id:control.agent.hardware_update`
- [ ] `GET /api/v1/control/agents/{id}/capabilities` - Agent capabilities → Use existing capabilities service `task_id:control.agent.capabilities`
- [ ] `POST /api/v1/control/agents/{id}/test_presigned` - Test presigned URL → Use existing presigned test service `task_id:control.agent.test_presigned`

---

## Task Management (Phase 5)

Task endpoints allow administrative-level inspection, state control, and lifecycle monitoring of individual cracking tasks. This includes agent-task assignments, requeue operations, error diagnostics, and performance tracking.

### 🧩 Implementation Tasks

**Reuse Existing Services**: All endpoints should leverage existing service layer functions from `app/core/services/task_service.py`:

- [ ] `GET /api/v1/control/tasks` - List tasks → Use existing task listing service (to be created) `task_id:control.task.list`
- [ ] `GET /api/v1/control/tasks/{id}` - Task detail → Use existing task detail service (to be created) `task_id:control.task.detail`
- [ ] `PATCH /api/v1/control/tasks/{id}/requeue` - Requeue task → Use existing task requeue service (to be created) `task_id:control.task.requeue`
- [ ] `POST /api/v1/control/tasks/{id}/cancel` - Cancel task → Use existing task cancellation service (to be created) `task_id:control.task.cancel`
- [ ] `GET /api/v1/control/tasks/{id}/logs` - Task logs → Create service for task log retrieval `task_id:control.task.logs`
- [ ] `GET /api/v1/control/tasks/{id}/performance` - Task performance → Create service for task performance metrics `task_id:control.task.performance`
- [ ] `GET /api/v1/control/tasks/{id}/status` - Task status → Create service for task status monitoring `task_id:control.task.status`

---

## Crackable Uploads (Phase 6)

These endpoints support the automated workflow for uploading files or hash text and converting them into hash lists and campaigns.

### 🧩 Implementation Tasks

**Reuse Existing Services**: All endpoints should leverage existing crackable upload services:

- [ ] `POST /api/v1/control/uploads/` - Upload file or hash text → Use existing upload service `task_id:control.upload.create`
- [ ] `GET /api/v1/control/uploads/{id}/status` - Upload status → Use existing status service `task_id:control.upload.status`
- [ ] `POST /api/v1/control/uploads/{id}/launch_campaign` - Launch campaign → Use existing launch service `task_id:control.upload.launch`
- [ ] `GET /api/v1/control/uploads/{id}/errors` - Upload errors → Use existing error service `task_id:control.upload.errors`
- [ ] `DELETE /api/v1/control/uploads/{id}` - Delete upload → Use existing deletion service `task_id:control.upload.delete`
- [ ] `GET /api/v1/control/uploads/{id}/preview` - Preview results → Use existing preview service `task_id:control.upload.preview`

---

## Live Monitoring (Phase 6)

These endpoints provide real-time monitoring capabilities for campaign progress, agent status, and system health.

### 🧩 Implementation Tasks

**Reuse Existing Services**: All endpoints should leverage existing event and monitoring services:

- [ ] `GET /api/v1/control/live/campaigns` - Campaign status stream → Use existing event service `task_id:control.live.campaigns`
- [ ] `GET /api/v1/control/live/agents` - Agent status stream → Use existing event service `task_id:control.live.agents`
- [ ] `GET /api/v1/control/live/tasks` - Task status stream → Use existing event service `task_id:control.live.tasks`
- [ ] `GET /api/v1/control/live/system` - System health stream → Use existing health service `task_id:control.live.system`

**Note**: These endpoints should provide JSON-formatted status updates rather than HTML-formatted SSE events used by the Web UI.

---

## State Management (Implementation Note)

Task and attack lifecycle transitions must follow the state rules defined in `core_algorithm_implementation_guide.md`.

### State Machine Implementation

Reference the state transition rules from `core_algorithm_implementation_guide.md`:

```python
# Task States: pending -> running -> (completed|failed|cancelled)
# Attack States: pending -> running -> (completed|failed|paused)
# Campaign States: draft -> active -> (completed|archived)


class StateValidator:
    """Validates state transitions for tasks, attacks, and campaigns."""

    def can_transition_task(
        self, current_state: TaskStatus, new_state: TaskStatus
    ) -> bool:
        """Check if task state transition is valid."""
        # Implement rules from core_algorithm_implementation_guide.md

    def can_transition_attack(
        self, current_state: AttackState, new_state: AttackState
    ) -> bool:
        """Check if attack state transition is valid."""
        # Implement rules from core_algorithm_implementation_guide.md

    def can_transition_campaign(
        self, current_state: CampaignState, new_state: CampaignState
    ) -> bool:
        """Check if campaign state transition is valid."""
        # Implement rules from core_algorithm_implementation_guide.md
```

### Progress Calculation

Implement keyspace-weighted progress from the core algorithm guide:

```python
def calculate_attack_progress(attack: Attack) -> float:
    """Calculate attack progress weighted by keyspace."""
    total_keyspace = sum(t.keyspace_total for t in attack.tasks)
    if total_keyspace == 0:
        return 0.0
    weighted_sum = sum(
        (t.progress_percent / 100.0) * t.keyspace_total for t in attack.tasks
    )
    return (weighted_sum / total_keyspace) * 100.0


def calculate_campaign_progress(campaign: Campaign) -> float:
    """Calculate campaign progress from weighted attack progress."""
    if not campaign.attacks:
        return 0.0
    return sum(calculate_attack_progress(a) for a in campaign.attacks) / len(
        campaign.attacks
    )
```

### Implementation Tasks

- [ ] Create state validation utilities based on core algorithm guide `task_id:control.state.validation_utils`
- [ ] Implement progress calculation functions `task_id:control.state.progress_calculation`
- [ ] Add state transition enforcement to all lifecycle endpoints `task_id:control.state.transition_enforcement`

---

---

### Documentation Updates

With the many changes to the API, we need to update the documentation to reflect the changes. Be sure to capture all the changes to the API in the documentation. The changes to be made are:

- [ ] Update the architecture documentation to reflect the changes. (found in `docs/architecture/*.md`)
- [ ] Update the API reference documentation to reflect the structure of the API and the endpoints that are available. (found in `docs/api/overview.md` and `docs/development/api-reference.md`)
- [ ] Update the user guide to reflect the changes. (found in `docs/user-guide/*.md`)
- [ ] Update the developer guide to reflect the changes. (found in `docs/development/*.md`)
- [ ] Update the getting started guide to reflect the changes. (found in `docs/getting-started/*.md`) - The primary audience for this guide is the administrator deploying the system and the end user trying to figure out how to use the system.
- [ ] Update the troubleshooting guide to reflect the changes. (found in `docs/user-guide/troubleshooting.md`) - The primary audience for this guide is the administrator configuring the system, and the end user trying to figure out why their campaign is behaving as expected. It is not for developers and each section should be a single topic with a clear title and a description of the problem and the solution.
- [ ] Update the FAQ to reflect the current state of the system. (found in `docs/user-guide/faq.md`)

---
