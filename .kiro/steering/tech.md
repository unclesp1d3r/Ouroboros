# Ouroboros Technology Stack

## Backend Stack

- **Framework**: FastAPI (Python 3.13+)
- **Database**: PostgreSQL 16+ with SQLAlchemy ORM
- **Authentication**: Bearer Token with JWT
- **Caching**: Redis 7
- **Object Storage**: MinIO
- **Task Queue**: Celery with Redis broker
- **Migrations**: Alembic
- **Validation**: Pydantic v2
- **Security**: Passlib with bcrypt, python-jose with cryptography

## Frontend Stack

- **Framework**: SvelteKit 2+ with TypeScript
- **UI Components**: Shadcn Svelte, Bits UI, Flowbite Svelte, DaisyUI
- **Styling**: TailwindCSS 4+
- **Charts**: LayerChart with D3
- **Forms**: Superforms with Zod validation
- **HTTP Client**: Axios
- **Build Tool**: Vite 7+

## Development Tools

- **Package Manager**: uv (Python), pnpm (Node.js)
- **Task Runner**: just (justfile)
- **Code Quality**: Ruff (formatting/linting), MyPy (type checking)
- **Testing**: pytest (backend), Vitest + Playwright (frontend)
- **Pre-commit**: Automated code quality checks
- **Documentation**: MkDocs with Material theme

## Infrastructure

- **Containerization**: Docker with multi-stage builds
- **Orchestration**: Docker Compose
- **Reverse Proxy**: Built-in FastAPI/Uvicorn
- **Monitoring**: Health checks for all services

## Common Commands

### Development Setup

```bash
# Install all dependencies and setup pre-commit hooks
just install

# Start backend development server with hot reload
just dev-backend

# Start frontend development server
just dev-frontend

# Start full-stack development environment
just dev-fullstack
```

### Code Quality

```bash
# Run all pre-commit checks
just check

# Format code (Python + Svelte)
just format

# Run all linting checks
just lint
```

### Testing

```bash
# Run backend tests with coverage
just test-backend

# Run frontend unit and E2E tests
just test-frontend

# Run full-stack E2E tests
just test-e2e

# Run all tests (CI equivalent)
just ci-check
```

### Database Management

```bash
# Reset test database (drop, recreate, migrate)
just db-reset

# Run migrations
alembic upgrade head

# Seed E2E test data
just seed-e2e-data
```

### Docker Operations

```bash
# Build and start development environment
just docker-dev-up-watch

# Build and start production environment
just docker-prod-up

# Stop and clean up development environment
just docker-dev-down
```

### Documentation

```bash
# Serve docs locally
just docs

# Build docs for testing
just docs-test
```

## Configuration

- **Environment**: `.env` file for local development
- **Python**: `pyproject.toml` for dependencies and tool configuration
- **Frontend**: `package.json` and `svelte.config.js`
- **Docker**: Multi-environment compose files
- **Database**: Alembic migrations in `alembic/versions/`
