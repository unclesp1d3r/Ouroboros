---

## inclusion: always

# Ouroboros Core Concepts

## Project Overview

Ouroboros is a distributed password cracking management system built with FastAPI and SvelteKit. It coordinates multiple agents running hashcat to efficiently distribute password cracking tasks across a network of machines.

## Critical Requirements

All code **must** follow the Python formatting standards defined in [python-style.mdc](mdc:Ouroboros/.cursor/rules/code/python-style.mdc)

### API Compatibility

1. **Agent API Versions**

Ouroboros supports two active versions of the Agent API:

- **v1: Legacy Compatibility (`/api/v1/client/*`)**

  - Mirrors the legacy Ruby-on-Rails version of Ouroboros (`https://github.com/unclesp1d3r/Ouroboros`).
  - Locked to `contracts/v1_api_swagger.json` (OpenAPI 3.0.1).
  - When working with integration tests of the Agent API v1, `contracts/v1_api_swagger.json` is **always** the authoritative source for correct behavior.
  - Must match every field, enum, and response exactly.
  - Breaking changes are prohibited.

- **v2: FastAPI-Native (`/api/v2/client/*`)**

  - NOT YET IMPLEMENTED. Will be created in the future.
  - Not constrained by the legacy spec.
  - Idiomatic FastAPI designs, updated schemas, and improved flows are allowed.
  - Breaking changes are allowed with proper versioning and documentation.
  - Cannot interfere in any way with the v1 Agent API.

Agents must declare their version or use version-specific routes. Future versions (v3, etc.) will follow the same model.

2. **Testing Requirements**
   - Automated tests must validate API responses against OpenAPI specification
   - Contract testing must ensure specification compliance
   - Integration tests must verify exact schema matches
   - CI/CD must include specification validation

## Architecture

### Backend Components

1. **FastAPI Application**

   - Core application server built with FastAPI
   - Asynchronous request handling
   - JWT-based authentication (api-users) for authentication and user management
   - OpenAPI 3.0.1 specification
   - SQLAlchemy ORM with PostgreSQL
   - Cachews for caching
   - Celery for task queues

2. **Database Models**\
   The backend defines a set of structured models to represent key operational and engagement data. These include:

   - `Project`: The top-level organizational and security boundary. Projects isolate agents, campaigns, hash lists, and users from one another. Access control is enforced at the project level, and no data is shared across projects without explicit export.
   - `Campaign`: A coordinated set of cracking attempts targeting a single hash list. Each campaign groups multiple attacks and serves as the operational unit for tracking progress and outcomes.
   - `Attack`: A specific cracking configuration (mode, rules, masks, charsets, etc.) used within a campaign. Multiple attacks may be chained or run in sequence under a campaign to exhaust various approaches.
   - `Task`: A discrete unit of work derived from an attack, assigned to a single agent. A task defines the keyspace slice, associated resources, and reporting path.
   - `HashList`: A set of hashes targeted by a campaign. Each campaign is linked to one hash list, but a hash list may be reused across multiple campaigns.
   - `HashItem`: An individual hash within a hash list. May include format-specific metadata such as salt or encoding. They may also contain user-defined metadata such as username and source, which should be stored as a JSONB.
   - `Agent`: A registered client capable of executing tasks. Agents report capability benchmarks, maintain a stateful heartbeat, and are tracked for version, platform, and operational health.
   - `CrackResult`: A record of a successfully cracked hash. Includes metadata about the agent, attack, and time of discovery.
   - `AgentError`: A fault or exception reported by an agent, optionally tied to a specific attack.
   - `Session`: Tracks the lifecycle of an active task execution, including live progress, last update time, and final disposition.
   - `Audit`: Historical log of user and system actions. Tracks changes to campaigns, attacks, task states, and user activity for accountability.
   - `User`: An authenticated entity authorized to access projects and perform actions. Permissions are scoped by role (`admin`, `user`, `power user`) and project membership.

   **Relationships**

- A Project has many Campaigns, but each Campaign belongs to exactly one Project.
- A User may belong to many Projects, and a Project may have many Users. (Many-to-many)
- A Campaign has many Attacks, but each Attack belongs to exactly one Campaign.
- An Attack has one or more Tasks, but each Task belongs to exactly one Attack.
- A Campaign is associated with a single HashList, but a HashList can be associated with many Campaigns. (Many-to-one from Campaign to HashList)
- A HashList has many HashItems, and a HashItem can belong to many HashLists. (Many-to-many)
- A CrackResult is associated with exactly one Attack, one HashItem, and one Agent.
- An AgentError always belongs to one Agent, and may optionally be associated with a single Attack.

Join tables such as `AgentsProjects` are used to enforce multi-tenancy boundaries or cross-link entities.

3. **API Interfaces**
   a. **Agent API** (`/api/v1/client/*`)

   - MUST follow OpenAPI 3.0.1 specification in `contracts/v1_api_swagger.json`
   - Used by distributed Ouroboros agents
   - Handles agent registration and heartbeat
   - Task distribution and result collection
   - Benchmark submission
   - Error reporting
   - Located under `app/api/v1/endpoints/agent` directory; wasn't previously located there, but should be moved.
   - Endpoints (as defined in specification):
     - `/api/v1/client/agents/*`: Agent lifecycle management
     - `/api/v1/client/attacks/*`: Attack configuration retrieval
     - `/api/v1/client/tasks/*`: Task management
     - `/api/v1/client/crackers/*`: Cracker binary updates

   **Router File Structure:**
   Each `/api/v1/client/<resource>` endpoint must be implemented in its own router file under `app/api/v1/endpoints/agent/<resource>.py`, except for root-level, non-resource endpoints, which are grouped in `general.py`.

   | Endpoint Path                  | Router File                              |
   | ------------------------------ | ---------------------------------------- |
   | `/api/v1/client/agents/*`      | `app/api/v1/endpoints/agent/agent.py`    |
   | `/api/v1/client/attacks/*`     | `app/api/v1/endpoints/agent/attacks.py`  |
   | `/api/v1/client/tasks/*`       | `app/api/v1/endpoints/agent/tasks.py`    |
   | `/api/v1/client/crackers/*`    | `app/api/v1/endpoints/agent/crackers.py` |
   | `/api/v1/client/configuration` | `app/api/v1/endpoints/agent/general.py`  |
   | `/api/v1/client/authenticate`  | `app/api/v1/endpoints/agent/general.py`  |

   > **Standard:** All root-level, non-resource endpoints for an API interface (e.g., Agent, Web, Control) should be grouped in a `general.py` file under the relevant endpoints directory.

   b. **Web UI API** (`/api/v1/web/*`)

   - Powers the web interface
   - Campaign and attack creation/management
   - Real-time monitoring and statistics
   - Agent fleet management
   - Results visualization
   - Located under `app/api/v1/endpoints/web` directory; wasn't previously located there, but should be moved.
   - Endpoints:
     - `/api/v1/web/campaigns/*`: Campaign management
     - `/api/v1/web/attacks/*`: Attack configuration
     - `/api/v1/web/agents/*`: Agent monitoring
     - `/api/v1/web/dashboard/*`: System statistics

   c. **Control API** (`/api/v1/control/*`)

   - Future Python TUI/CLI client interface
   - Command-line based management
   - Real-time monitoring
   - Batch operations
   - Scriptable interface
   - Located under `app/api/v1/endpoints/control` directory; wasn't previously located there, but should be moved.
   - Endpoints:
     - `/api/v1/control/campaigns/*`: Campaign operations
     - `/api/v1/control/attacks/*`: Attack management
     - `/api/v1/control/agents/*`: Agent control
     - `/api/v1/control/stats/*`: Performance metrics

   c. **Shared Infrastructure API**

   - Provides endpoints used by all major interfaces (Agent, Web UI, control)
   - Examples: `/api/v1/users`, `/api/v1/resources/{resource_id}/download`
   - Implemented in `app/api/v1/endpoints/users.py` and `resources.py`
   - Not specific to a single interface; provides common infrastructure (user management, resource access, etc.)
   - Standard for any future endpoints that must be accessible to multiple API clients

   > **Standard:** All endpoints that serve as shared infrastructure (e.g., user listing, resource download) should be grouped under this API and documented as such. These endpoints are versioned and maintained alongside the other API interfaces.

### Frontend Components

1. **SvelteKit-Based UI**

   - Located in `frontend/` directory tree
   - The frontend code has a different `package.json` than the backend code, so any pnpm/npm commands must be run from within `frontend` if it relates to the frontend code.
   - Built with SvelteKit (SPA pre-build)
   - Communicates with backend via JSON API (RESTful endpoints)
   - [Shadcn-Svelte](mdc:Ouroboros/https:/www.shadcn-svelte.com/docs) for component library and styling
   - Client-side routing and state management
   - Client-side validation using [Zod](mdc:Ouroboros/https:/zod.dev)
   - Modal-based forms using [Superforms](mdc:Ouroboros/https:/superforms.rocks)
   - Responsive, accessible, and modern UX
   - When writing Svelte components, aspire to use idiomatic Svelte (<https://svelte.dev/llms-small.txt>)

2. **Component Library**

   - Use Shadcn-Svelte and Flowbite as the primary UI libraries
   - Hundreds of pre-built, accessible Svelte components
   - Enterprise-ready dashboard components
   - Consistent design language across the application
   - Built-in dark mode support
   - Accessibility compliant
   - Key components used:
     - Data tables for task management
     - Progress indicators for cracking status
     - Alert components for notifications
     - Modal dialogs for configuration
     - Form components for attack setup
     - Cards for agent and task display
     - Navigation components for dashboard layout
     - Stats components for metrics display

3. **Key Features**

   - Agent management dashboard
   - Attack configuration interface
   - Real-time task monitoring
   - Results visualization

4. **Python control** (Planned)

   - Command-line interface
   - Real-time monitoring
   - Batch operations
   - Scriptable workflows

## Core Concepts

### Agent Management

1. **Agent States**

   - `pending`: Initial registration state
   - `active`: Ready for tasks
   - `stopped`: Manually paused
   - `error`: Encountered issues

2. **Agent Configuration**

   - Update intervals
   - Device selection (CPU/GPU)
   - Hashcat configuration
   - Benchmark management

### Attack System

1. **Attack Modes**

   - Dictionary attacks
   - Mask attacks
   - Hybrid dictionary attacks
   - Hybrid mask attacks

2. **Attack Resources**

   - Word lists
   - Rule lists
   - Mask patterns
   - Custom charsets

3. **Resource Storage**

   - All static attack resources stored in MinIO S3-compatible storage
   - Resources include:
     - Word lists for dictionary attacks
     - Rule lists for rule-based attacks
     - Mask pattern lists for mask attacks
     - Custom charset files
   - Each resource file has:
     - Unique identifier
     - MD5 checksum for verification
     - Metadata including size, upload date, and description
     - S3 presigned URLs for secure agent downloads
   - Web UI requirements:
     - Direct file uploads to MinIO buckets
     - Progress tracking for large files
     - Checksum verification
     - Resource management interface
     - File preview capabilities
     - Resource tagging and categorization
   - MinIO Configuration:
     - Bucket Structure:
       - `wordlists/`: Dictionary attack word lists
       - `rules/`: Hashcat rule files
       - `masks/`: Mask pattern files
       - `charsets/`: Custom charset definitions
       - `temp/`: Temporary storage for uploads
     - File Organization:
       - Files stored with UUID-based names
       - Original filenames stored in metadata
       - Version control through metadata tags
     - Backup Configuration:
       - Automatic daily snapshots
       - Version retention policies
       - Cross-region replication (optional)
   - Security Implementation:
     - Access Control:
       - Bucket policies for strict access control
       - Temporary presigned URLs for agent downloads
       - Role-based access for web UI users
       - IP-based restrictions for agent access
     - Data Protection:
       - Server-side encryption at rest
       - TLS for all transfers
       - Automatic virus scanning for uploads
       - File type verification
     - Monitoring:
       - Access logging
       - Usage metrics
       - Error tracking
       - Quota management

### Task Distribution

1. **Task Lifecycle**

   - Creation and assignment
   - Progress monitoring
   - Result collection
   - Completion/abandonment

2. **Task Features**

   - Keyspace distribution
   - Progress tracking
   - Real-time status updates
   - Error handling

## Project Structure

### Docker Configuration

1. **Service Containers**

   - FastAPI Application:
     - Python 3.13 base image
     - uv package manager
     - Development and production configurations
     - Health checks
     - Graceful shutdown handling
   - PostgreSQL Database:
     - Version 16 or later
     - Persistent volume mounts
     - Automated backups
     - Replication support (optional)
   - Redis Cache (Optional):
     - Latest stable version
     - Production caching backend (Cashews)
     - Celery task queue backend
     - Development uses in-memory caching
   - MinIO Object Storage:
     - Latest stable version
     - Configured buckets for attack resources
     - TLS/SSL support
     - Access key management
   - Nginx Reverse Proxy:
     - Latest stable version
     - SSL termination
     - Rate limiting
     - Static file serving
   - Monitoring Stack (Optional):
     - Prometheus
     - Grafana
     - Node exporter
     - Cadvisor

2. **Development Setup**

- See [docker-guidelines.mdc](mdc:Ouroboros/.cursor/rules/architecture/docker-guidelines.mdc) for docker deployment guidance.

04. **Container Security**

    - Non-root users in all containers
    - Read-only root filesystem where possible
    - Limited container capabilities
    - Resource limits and quotas
    - Regular security scanning
    - Secrets management via environment files

05. **Deployment Requirements**

    - Single command deployment: `docker compose up -d`
    - Automated database migrations
    - Health check monitoring
    - Backup and restore procedures
    - Log aggregation
    - Monitoring and alerting
    - Zero-downtime updates
    - Rollback capabilities

06. **Development Workflow**

    - Hot reload for development
    - Shared volume mounts for code changes
    - Development-specific overrides
    - Test environment configuration
    - Debug capabilities
    - Local resource access

07. **CI/CD Integration**

    - Automated builds
    - Container testing
    - Security scanning
    - Registry pushes
    - Deployment automation
    - Environment promotion

08. **Backup Strategy**

    - Database dumps
    - MinIO bucket backups
    - Configuration backups
    - Automated scheduling
    - Retention policies
    - Restore testing

09. **Monitoring Setup**

    - Container metrics
    - Application me - Resource usage
    - Alert configuration
    - Log management
    - Performance tracking

10. **Scaling Configuration**

    - Service replication
    - Load balancing
    - Database clustering
    - Cache distribution
    - Storage expansion
    - Backup scaling

## Development Guidelines

### Logging

All application logging MUST use the @`loguru` logging library. Standard Python `logging` is not permitted.

- Logs should be structured, timestamped, and consistently leveled (`debug`, `info`, `warning`, `error`, `critical`)
- Prefer `logger.bind()` for attaching context (e.g., task ID, agent ID) to log messages
- Ensure logs emit to stdout by default for compatibility with containerized environments
- Avoid manual formatting — use `loguru`'s built-in formatting tools

### Code Organization

1. **API Versioning**

   - Agent API versioning controlled by `contracts/v1_api_swagger.json` specification
   - Agent, Web UI, and Control APIs versioned independently
   - Version-specific modules in `api/v1/`
   - Backward compatibility maintenance

2. **Database Practices**

   - Alembic migrations for schema changes
   - SQLAlchemy for database operations
   - Type hints and validation with Pydantic

3. **Security Considerations**

   - JWT token authentication
   - Agent verification
   - Secure resource downloads
   - Air-gapped network support

### Authentication Strategies

1. **Web UI Authentication**

   - OAuth2 with Password flow and refresh tokens
   - Session-based with secure HTTP-only cookies
   - CSRF protection for forms
   - Rate limiting on login attempts
   - Password requirements:
     - Minimum length and complexity
     - Password hashing with Argon2
     - Regular password rotation policies
   - Remember-me functionality with secure tokens

2. **Agent API Authentication**

   - Bearer token authentication

   - Tokens automatically generated on agent registration

   - One token per agent, bound to agent ID

   - Token rotation on security events

   - Token format: `csa_<agent_id>_<random_string>`

   - Automatic token invalidation on agent removal

   - Rate limiting per agent token

   - Required headers:

     - See @core-concepts-appendix.mdc for authentic\*TUI API Authentication\*\*

   - API key-based authentication using bearer tokens

   - Keys generated through web interface

   - Associated with specific user accounts

   - Configurable permissions and scopes

   - Token format: `cst_<user_id>_<random_string>`

   - Multiple active keys per user supported

   - Key management features:

     - Key creation with expiration
     - Scope configuration
     - Usage monitoring
     - Emergency revocation

   - Required headers:

     - See @core-concepts-appendix.mdc for authentication example

3. **Common Security Features**

   - All tokens transmitted over HTTPS only
   - Automatic token expiration
   - Token revocation capabilities
   - Audit logging of authentication events
   - Failed attempt monitoring
   - IP-based rate limiting
   - Security event notifications

### 🔁 Caching

Ouroboros uses Cashews as the primary caching library f-compatible TTL caching across internal services and web UI endpoints.

- All caching must use Cashews decorators or `cache.get()` / `cache.set()` API.
- In-memory caching (`mem://`) is used by default in development.
- Production deployments may optionally switch to Redis by configuring `redis://...` during `cache.setup()`.

#### 🔒 Usage Constraints

- Do **not** use other cache mechanisms (e.g., `functools.lru_cache`, FastAPI internal cache) for any persistent/shared value.
- TTLs should be short (≤ 60s) unless a strong reason exists.
- All cache keys should be prefixed logically, e.g. `campaign_stats:`, `agent_health:`, etc.
- Avoid caching large serialized objects unless explicitly required.
- Tagging and `.invalidate()` should be used for cache busting when data dependencies change.
- Prefer decorator usage when possible.

#### 🧠 Examples

- Cashews caching code examples are now in @core-concepts-appendix.mdc

Note: cache.setup() should run once at app startup (startup_event or ASGI lifespan).

### Best Practices

1. **API Design**

   - RESTful endpoint structure
   - Comprehensive error handling
   - Status code consistency
   - Clear response schemas

2. **Frontend Development**

   - SvelteKit for SPA app
   - JSON API for all data interactions
   - Shadcn-Svelte for UI components and styling
   - Responsive design
   - Accessibility compliance

3. **Performance**

   - Asynchronous operations
   - Efficient task distribution
   - Resource monitoring
   - Caching strategies

## Testing and Validation

1. **Testing Levels**

   - Unit tests for core logic
   - Integration tests for API endpoints
   - End-to-end testing for workflows
   - Performance benchmarking

2. **Quality Assurance**

   - Type checking
   - Code linting
   - Documentation coverage
   - Security scanning
