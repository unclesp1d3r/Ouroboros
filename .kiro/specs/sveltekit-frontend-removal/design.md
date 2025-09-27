# Design Document

## Overview

The SvelteKit Frontend Removal design outlines a systematic approach to eliminate the separate SvelteKit frontend from CipherSwarm while preserving all user functionality through the integrated NiceGUI interface. This design ensures a clean, safe, and complete transition to a single-application architecture.

The removal process is designed to be executed after the NiceGUI web interface has been fully implemented, tested, and validated to provide equivalent functionality to the existing SvelteKit frontend.

## Architecture

### Current State Architecture

```mermaid
graph TB
    subgraph "Current CipherSwarm Architecture"
        A[Client Browser] --> B[Nginx Reverse Proxy]
        B --> C[SvelteKit Frontend :5173]
        B --> D[FastAPI Backend :8000]

        C --> E[Frontend Build Process]
        C --> F[Node.js Dependencies]
        C --> G[SvelteKit Components]

        D --> H[NiceGUI Interface /ui/]
        D --> I[Agent API Routes /api/v1/client/]
        D --> J[Control API Routes /api/v1/control/]
        D --> K[Shared API Routes /api/v1/users, /api/v1/resources]
        D --> L[Database]
        D --> M[Redis Cache]
        D --> N[MinIO Storage]
    end

    subgraph "Development Tools"
        M[pnpm/npm]
        N[Vite Build]
        O[ESLint/Prettier]
        P[Playwright E2E]
    end

    E --> M
    E --> N
    F --> O
    G --> P
```

### Target State Architecture

```mermaid
graph TB
    subgraph "Target CipherSwarm Architecture"
        A[Client Browser] --> B[Nginx Reverse Proxy]
        B --> C[FastAPI Backend :8000]

        C --> D[NiceGUI Interface /ui/]
        C --> E[Agent API Routes /api/v1/client/]
        C --> F[Control API Routes /api/v1/control/]
        C --> G[Shared API Routes /api/v1/users, /api/v1/resources]
        C --> H[Database]
        C --> I[Redis Cache]
        C --> J[MinIO Storage]

        I[Root Redirect /] --> D
    end

    subgraph "Simplified Development"
        J[Python Only]
        K[FastAPI Testing]
        L[NiceGUI Components]
    end

    D --> J
    E --> K
    D --> L
```

## Components and Interfaces

### 1. Simplified Application Architecture

**Post-Removal System Components**

After the SvelteKit frontend removal, CipherSwarm will consist of these core components:

```
FastAPI Application
├── NiceGUI Web Interface (/ui/*)
├── Agent API (/api/v1/client/*)
├── Control API (/api/v1/control/*)
├── Shared Infrastructure (/api/v1/users, /api/v1/resources)
├── Backend Services (campaign_service, agent_service, etc.)
├── Database Layer (PostgreSQL + SQLAlchemy)
├── Caching Layer (Redis + Cashews)
└── Storage Layer (MinIO S3-compatible)
```

**Component Responsibilities:**
- **NiceGUI Interface**: Integrated web UI served directly from FastAPI
- **Agent API**: External agent communication (preserved unchanged)
- **Control API**: CLI/TUI interface (preserved unchanged)
- **Shared Infrastructure**: Cross-interface services (preserved unchanged)
- **Backend Services**: Business logic layer (enhanced for direct NiceGUI integration)

### 2. Route Migration and Redirect System

**URL Mapping Strategy**

```python
class RouteMigration:
    """Handles migration from SvelteKit routes to NiceGUI equivalents"""

    ROUTE_MAPPINGS = {
        # Root and dashboard
        "/": "/ui/dashboard",
        "/dashboard": "/ui/dashboard",

        # Campaign management
        "/campaigns": "/ui/campaigns",
        "/campaigns/new": "/ui/campaigns/new",
        "/campaigns/{id}": "/ui/campaigns/{id}",
        "/campaigns/{id}/edit": "/ui/campaigns/{id}/edit",

        # Agent management
        "/agents": "/ui/agents",
        "/agents/{id}": "/ui/agents/{id}",

        # Attack configuration
        "/attacks": "/ui/attacks",
        "/attacks/new": "/ui/attacks/new",
        "/attacks/{id}": "/ui/attacks/{id}",

        # Resource management
        "/resources": "/ui/resources",
        "/resources/upload": "/ui/resources/upload",

        # User management
        "/users": "/ui/users",
        "/users/new": "/ui/users/new",
        "/users/{id}": "/ui/users/{id}",

        # Settings and profile
        "/settings": "/ui/settings",
        "/profile": "/ui/profile",

        # Authentication (if different)
        "/login": "/ui/login",
        "/logout": "/ui/logout"
    }

    @staticmethod
    def create_redirect_middleware():
        """Create FastAPI middleware for legacy route redirects"""

        @app.middleware("http")
        async def redirect_legacy_routes(request: Request, call_next):
            path = request.url.path

            # Check if this is a legacy frontend route
            if path in RouteMigration.ROUTE_MAPPINGS:
                redirect_url = RouteMigration.ROUTE_MAPPINGS[path]
                return RedirectResponse(url=redirect_url, status_code=301)

            # Handle parameterized routes
            for pattern, target in RouteMigration.ROUTE_MAPPINGS.items():
                if "{" in pattern:
                    # Convert to regex and check for match
                    regex_pattern = pattern.replace("{id}", r"(\d+)")
                    match = re.match(f"^{regex_pattern}$", path)
                    if match:
                        redirect_url = target.replace("{id}", match.group(1))
                        return RedirectResponse(url=redirect_url, status_code=301)

            response = await call_next(request)
            return response
```

### 3. File and Directory Removal Strategy

**Frontend Code and Dependencies**

The following SvelteKit-related files and directories will be completely removed:

**Directories:**
- `frontend/` - Entire SvelteKit application
- `node_modules/` - Node.js dependencies
- `.svelte-kit/` - SvelteKit build cache
- `build/` - Frontend build output
- `test-results/` - Playwright test results
- `test-artifacts/` - Frontend test artifacts
- `playwright-report/` - E2E test reports

**Configuration Files:**
- `package.json` - Node.js package configuration
- `package-lock.json` / `pnpm-lock.yaml` - Dependency lock files
- `svelte.config.js` - SvelteKit configuration
- `vite.config.ts` - Vite build configuration
- `tailwind.config.js` - TailwindCSS configuration
- `postcss.config.js` - PostCSS configuration
- `playwright.config.ts` - E2E test configuration
- `vitest.config.ts` - Frontend unit test configuration

**Steering Documents:**
- `.kiro/steering/sveltekit5-runes.md`
- `.kiro/steering/shadcn-svelte-extras.md`
- `.kiro/steering/ux-guidelines.md`
- `.kiro/steering/task-verification-workflow.md`
- `.kiro/steering/phase-3-task-verification.md`

**Files to Update (not remove):**
- `.gitignore` - Remove frontend-specific entries
- `README.md` - Update setup instructions
- `docker-compose.yml` - Remove frontend service
- `justfile` - Remove frontend recipes
- `.github/workflows/` - Update CI/CD workflows

### 4. Docker Configuration Updates

**Container Architecture Simplification**

```yaml
# Updated docker-compose.yml (frontend service removed)
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/cipherswarm
      - REDIS_URL=redis://redis:6379
      - MINIO_URL=http://minio:9000
    depends_on:
      - db
      - redis
      - minio
    volumes:
      - ./app:/app/app
    # NiceGUI interface now served directly from FastAPI

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - app
    # Updated to proxy all web traffic to FastAPI app

  db:
    image: postgres:16
    environment:
      - POSTGRES_DB=cipherswarm
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    environment:
      - MINIO_ROOT_USER=minioadmin
      - MINIO_ROOT_PASSWORD=minioadmin
    volumes:
      - minio_data:/data
    ports:
      - "9000:9000"
      - "9001:9001"

volumes:
  postgres_data:
  redis_data:
  minio_data:
```

**Updated Nginx Configuration**

```nginx
# Updated nginx.conf (no frontend proxy needed)
upstream backend {
    server app:8000;
}

server {
    listen 80;
    server_name localhost;

    # Redirect root to NiceGUI dashboard
    location = / {
        return 301 /ui/dashboard;
    }

    # Proxy all requests to FastAPI (includes NiceGUI at /ui/)
    location / {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support for NiceGUI real-time features
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # API routes (unchanged)
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 5. CI/CD Pipeline Updates

**Simplified GitHub Actions Workflow**

```yaml
# Updated .github/workflows/ci.yml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  backend-tests:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.13'

    - name: Install uv
      run: pip install uv

    - name: Install dependencies
      run: uv sync

    - name: Run linting
      run: |
        uv run ruff check .
        uv run ruff format --check .
        uv run mypy .

    - name: Run backend tests
      run: uv run pytest
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db

    - name: Run NiceGUI integration tests
      run: uv run pytest tests/integration/ui/

    # Frontend steps completely removed:
    # - No Node.js setup
    # - No pnpm installation
    # - No frontend linting
    # - No SvelteKit tests
    # - No Playwright E2E tests
    # - No frontend build

  docker-build:
    runs-on: ubuntu-latest
    needs: backend-tests

    steps:
    - uses: actions/checkout@v4

    - name: Build Docker image
      run: docker build -t cipherswarm:latest .

    - name: Test Docker container
      run: |
        docker run -d --name test-container cipherswarm:latest
        sleep 10
        docker exec test-container curl -f http://localhost:8000/health
        docker stop test-container
```

### 6. Web UI API Routes Removal

**API Simplification Strategy**

With the transition to NiceGUI, the Web UI API routes (`/api/v1/web/*`) become obsolete since NiceGUI components will interact directly with backend services rather than making HTTP API calls.

```python
class WebUIAPIRemoval:
    """Handles removal of Web UI API routes"""

    # Web UI API routes to be removed
    WEB_API_ROUTES_TO_REMOVE = [
        "/api/v1/web/campaigns/",
        "/api/v1/web/campaigns/{id}",
        "/api/v1/web/campaigns/{id}/attacks",
        "/api/v1/web/attacks/",
        "/api/v1/web/attacks/{id}",
        "/api/v1/web/attacks/estimate",
        "/api/v1/web/agents/",
        "/api/v1/web/agents/{id}",
        "/api/v1/web/dashboard/summary",
        "/api/v1/web/dashboard/stats",
        "/api/v1/web/resources/",
        "/api/v1/web/resources/upload",
        "/api/v1/web/users/",
        "/api/v1/web/users/{id}"
    ]

    # Files containing Web UI API routes
    WEB_API_FILES_TO_REMOVE = [
        "app/api/v1/endpoints/web/campaigns.py",
        "app/api/v1/endpoints/web/attacks.py",
        "app/api/v1/endpoints/web/agents.py",
        "app/api/v1/endpoints/web/dashboard.py",
        "app/api/v1/endpoints/web/resources.py",
        "app/api/v1/endpoints/web/users.py",
        "app/api/v1/endpoints/web/__init__.py"
    ]

    # Schemas specific to Web UI API
    WEB_API_SCHEMAS_TO_REMOVE = [
        "app/schemas/web/",  # Entire web-specific schemas directory
        # Individual files if not in subdirectory:
        "app/schemas/dashboard.py",
        "app/schemas/web_campaign.py",
        "app/schemas/web_attack.py"
    ]

    # Tests for Web UI API routes
    WEB_API_TESTS_TO_REMOVE = [
        "tests/integration/web/",  # Entire web API test directory
        "tests/unit/api/web/"
    ]

class NiceGUIServiceIntegration:
    """Defines how NiceGUI will integrate with backend services"""

    # NiceGUI will use these service patterns instead of API calls
    SERVICE_INTEGRATION_PATTERNS = {
        "campaigns": {
            "old_api": "/api/v1/web/campaigns/",
            "new_pattern": "await campaign_service.list_campaigns(db, user_id)",
            "service_file": "app/core/services/campaign_service.py"
        },
        "agents": {
            "old_api": "/api/v1/web/agents/",
            "new_pattern": "await agent_service.list_agents(db, project_id)",
            "service_file": "app/core/services/agent_service.py"
        },
        "attacks": {
            "old_api": "/api/v1/web/attacks/",
            "new_pattern": "await attack_service.list_attacks(db, campaign_id)",
            "service_file": "app/core/services/attack_service.py"
        },
        "dashboard": {
            "old_api": "/api/v1/web/dashboard/summary",
            "new_pattern": "await dashboard_service.get_summary(db, user_id)",
            "service_file": "app/core/services/dashboard_service.py"
        }
    }

    @staticmethod
    def validate_service_availability() -> ServiceValidationResult:
        """Ensure all required backend services exist for NiceGUI integration"""

        required_services = [
            "campaign_service",
            "agent_service",
            "attack_service",
            "dashboard_service",
            "resource_service",
            "user_service"
        ]

        missing_services = []
        for service in required_services:
            service_path = f"app/core/services/{service}.py"
            if not os.path.exists(service_path):
                missing_services.append(service)

        return ServiceValidationResult(
            all_services_available=len(missing_services) == 0,
            missing_services=missing_services
        )
```

**API Architecture After Removal**

```mermaid
graph TB
    subgraph "Remaining API Structure"
        A[FastAPI Application]

        subgraph "Agent API (Preserved)"
            B[/api/v1/client/agents]
            C[/api/v1/client/tasks]
            D[/api/v1/client/attacks]
            E[/api/v1/client/crackers]
        end

        subgraph "Control API (Preserved)"
            F[/api/v1/control/campaigns]
            G[/api/v1/control/agents]
            H[/api/v1/control/stats]
        end

        subgraph "Shared Infrastructure (Preserved)"
            I[/api/v1/users]
            J[/api/v1/resources]
        end

        subgraph "NiceGUI Integration (New)"
            K[Direct Service Calls]
            L[No HTTP API Layer]
            M[Shared Backend Services]
        end

        A --> B
        A --> C
        A --> D
        A --> E
        A --> F
        A --> G
        A --> H
        A --> I
        A --> J
        A --> K
        K --> M
    end
```

### 7. Documentation Updates Strategy

**Documentation Updates Required**

The following documentation files need to be updated to remove SvelteKit references:

**README.md Updates:**
- Remove sections: "Frontend Development", "SvelteKit Setup", "Node.js Requirements", "Frontend Testing"
- Update sections: "Quick Start" (remove frontend setup), "Development" (backend-only workflow), "Testing" (remove frontend commands), "Deployment" (single container)

**docs/development/setup.md Updates:**
- Remove sections: "Frontend Development Environment", "Node.js and pnpm Installation", "SvelteKit Development Server"
- Update sections: "Development Workflow" (backend + NiceGUI only), "Hot Reload" (FastAPI + NiceGUI)

**docs/architecture/overview.md Updates:**
- Update sections: "System Architecture" (single FastAPI app), "Frontend Architecture" (replace with NiceGUI), "Deployment Architecture" (simplified containers)

**Steering Documents to Remove:**
- `.kiro/steering/sveltekit5-runes.md`
- `.kiro/steering/shadcn-svelte-extras.md`
- `.kiro/steering/ux-guidelines.md`
- `.kiro/steering/task-verification-workflow.md`
- `.kiro/steering/phase-3-task-verification.md`

## Validation Requirements

### Pre-Removal Validation

Before removing the SvelteKit frontend, the following validations must be completed:

**NiceGUI Functionality Validation:**
- All SvelteKit features have equivalent NiceGUI implementations
- User workflows work identically in NiceGUI interface
- Authentication and authorization function correctly
- Real-time updates and notifications work properly
- Performance is acceptable compared to SvelteKit

**System Integration Validation:**
- NiceGUI integrates properly with existing backend services
- All API endpoints remain functional (Agent API, Control API, shared routes)
- Database operations work correctly through service layer
- Caching and storage systems function properly

**User Experience Validation:**
- All user workflows can be completed in NiceGUI
- Interface is responsive and accessible
- No functionality gaps exist
- Stakeholder approval obtained

## Testing Strategy

### Pre-Removal Validation

Before removing the SvelteKit frontend, comprehensive testing must validate that NiceGUI provides equivalent functionality:

**User Workflow Testing:**
- User login and dashboard access
- Campaign creation and management
- Agent monitoring and control
- Attack configuration and execution
- Resource upload and management
- User management and permissions

**System Integration Testing:**
- Route redirects work correctly
- Authentication functions properly
- API endpoints remain functional
- Performance is acceptable
- No missing features identified

### Post-Removal Validation

After removal, the following must be verified:

**File System Validation:**
- All SvelteKit files and directories removed
- Node.js dependencies cleaned up
- Docker configurations updated
- Documentation updated

**Functional Testing:**
- Root path redirects to `/ui/dashboard`
- Legacy routes redirect to NiceGUI equivalents
- NiceGUI interface is accessible
- Agent API and Control API still functional
- No broken links or missing resources

**Integration Testing:**
- All user workflows work in NiceGUI
- Authentication and authorization functional
- Real-time updates working
- Performance maintained or improved
