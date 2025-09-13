# 🧃 justfile — Ouroboros Developer Tasks
set shell := ["bash", "-cu"]
set windows-powershell := true
set dotenv-load := true
set ignore-comments := true

default:
    @just --choose

alias h := help

help:
    just --summary

# -----------------------------
# 🔧 Setup & Installation
# PHONY: install
# -----------------------------

# Install dependencies and setup pre-commit hooks
[unix]
install:
    cd {{justfile_dir()}}
    # 🚀 Set up dev env & pre-commit hooks
    uv sync --dev --all-groups --all-packages
    uv run pre-commit install --hook-type commit-msg

[windows]
install:
    cd {{justfile_dir()}}
    # 🚀 Set up dev env & pre-commit hooks
    uv sync --dev --all-groups --all-packages
    $env:PYTHONUTF8=1; uv run pre-commit install --hook-type commit-msg

# Update uv and pnpm dependencies
[unix]
update-deps:
    cd {{justfile_dir()}}
    uv sync --dev --all-groups --all-packages -U
    pnpm update --latest -r
    pre-commit autoupdate

[windows]
update-deps:
    cd {{justfile_dir()}}
    uv sync --dev --all-groups --all-packages -U
    pnpm update --latest -r
    $env:PYTHONUTF8=1; uv run pre-commit autoupdate


# -----------------------------
# 🧹 Linting, Typing, Dep Check
# PHONY: check, format, format-check, lint
# -----------------------------

# Run all pre-commit checks
[unix]
check:
    # 🚀 Full code + commit checks
    uv lock --locked
    uv run pre-commit run -a
    just based-pyright

[windows]
check:
    # 🚀 Full code + commit checks
    uv lock --locked
    $env:PYTHONUTF8=1; uv run pre-commit run -a
    just based-pyright

based-pyright:
    uv run --group dev basedpyright -p pyproject.toml

# Format code using ruff, mdformat, and svelte check
format:
    cd {{justfile_dir()}}
    just frontend-format
    uv run --group dev ruff format .
    uv run --group ci mdformat .

# Check code formatting using ruff and mdformat
format-check:
    uv run --group dev ruff format --check .
    uv run --group ci mdformat --check .

# Run all linting checks
lint: format-check check frontend-lint

# -----------------------------
# 🧪 Testing & Coverage (Three-Tier Architecture)
# PHONY: test-backend, test-frontend, test-e2e, test, coverage, clean-test
# -----------------------------

# Run backend Python tests (Layer 1: Backend API/unit integration)
test-backend:
    cd {{justfile_dir()}}
    uv run pytest -n auto --cov --cov-config=pyproject.toml --cov-report=xml --tb=short -q

# Run frontend tests with mocked APIs (Layer 2: Frontend UI and logic validation)
[unix]
test-frontend:
    cd {{justfile_dir()}}/frontend && pnpm exec vitest run && pnpm exec playwright test

[windows]
test-frontend:
    cd {{justfile_dir()}}/frontend
    pnpm exec vitest run
    pnpm exec playwright test

# Run full-stack E2E tests against Docker backend (Layer 3: True user flows across real stack)
[unix]
test-e2e:
    cd {{justfile_dir()}}/frontend && pnpm exec playwright test --config=playwright.config.e2e.ts

[windows]
test-e2e:
    cd {{justfile_dir()}}/frontend
    pnpm exec playwright test --config=playwright.config.e2e.ts

# Run all python tests with maxfail=1 and disable warnings
test-fast:
    uv run pytest -n auto --maxfail=1 --disable-warnings -v tests/

# Run coverage report
coverage:
    uv run coverage report

# -----------------------------
# 📦 Build & Clean
# PHONY: build, clean-build
# -----------------------------

# Clean up .pyc files, __pycache__, and pytest cache
clean:
    cd {{justfile_dir()}}
    @echo "🧹 Cleaning .pyc files, __pycache__, and .pytest_cache..."
    find . -type d -name "__pycache__" -exec rm -rf "{}" +
    find . -type f -name "*.pyc" -delete
    rm -rf .pytest_cache
    rm -rf dist build *.egg-info

# Build the backend project
build:
    uvx --from build pyproject-build --installer uv

# Clean up and build the project
clean-build:
    just ci-check
    just clean
    just build

# Clean up .pyc files, __pycache__, and pytest cache before testing
clean-test: clean
    @echo "✅ Cleaned. Running tests..."
    just test-backend

# Generate CHANGELOG.md from commits
release: install-git-cliff
    # 📝 Generate CHANGELOG.md from commits
    @echo "🚀 Generating changelog with git-cliff..."
    git cliff -o CHANGELOG.md --config cliff.toml
    @echo "✅ Changelog updated! Commit and tag when ready."

# Preview changelog without writing
release-preview: install-git-cliff
    # 🔍 Preview changelog without writing
    git cliff --config cliff.toml


[unix]
install-git-cliff:
    #!/usr/bin/env bash
    if ! command -v git-cliff &> /dev/null; then
        cargo install git-cliff --locked || echo "Make sure git-cliff is installed manually"
    fi

[windows]
install-git-cliff:
    if (-not (Get-Command git-cliff -ErrorAction SilentlyContinue)) {
    cargo install git-cliff --locked
    if ($LASTEXITCODE -ne 0) {
    Write-Host "Make sure git-cliff is installed manually"
        exit $LASTEXITCODE
    }

# -----------------------------
# 📚 Documentation
# PHONY: docs, docs-test, docs-export
# -----------------------------

# Serve documentation locally with mkdocs
docs:
    uv run mkdocs serve --dev-addr 0.0.0.0:9090

# Test documentation build
docs-test:
    uv run mkdocs build -s

# Export documentation to a single combined PDF
docs-export:
    # 🧾 Export a single combined PDF via mkdocs-exporter
    uv run mkdocs build

# -----------------------------
# 📦 Docker Tasks
# PHONY: docker-build, docker-down, docker-up
# -----------------------------

# Check the Dockerfiles syntax for errors
docker-file-check:
    cd {{justfile_dir()}}
    docker build --check .
    cd {{justfile_dir()}}/frontend
    docker build --check .

# Build the Docker image
docker-build:
    cd {{justfile_dir()}}
    docker compose build

# Build E2E test environment Docker images
docker-build-e2e:
    cd {{justfile_dir()}}
    docker compose -f docker-compose.e2e.yml build

# Up the Docker services
docker-prod-up:
    cd {{justfile_dir()}}
    docker compose -f docker-compose.yml up -d

# Up the Docker services for development with hot reload
docker-dev-up:
    cd {{justfile_dir()}}
    docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --remove-orphans --build

# Up the Docker services for development with hot reload and do not detach from the logs
docker-dev-up-watch:
    just docker-dev-up
    @echo "🔄 Running database migrations..."
    just docker-dev-migrate
    @echo "🌱 Seeding E2E test data..."
    just docker-dev-seed
    @echo "📋 Following logs..."
    docker compose -f docker-compose.yml -f docker-compose.dev.yml logs -f

# Up the Docker services for E2E testing
docker-e2e-up:
    cd {{justfile_dir()}}
    docker compose -f docker-compose.e2e.yml up -d --wait

# Run database migrations in development environment
docker-dev-migrate:
    cd {{justfile_dir()}}
    docker compose -f docker-compose.yml -f docker-compose.dev.yml exec -T backend /app/.venv/bin/python -c "import sys; sys.path.insert(0, '/app/.venv/lib/python3.13/site-packages'); from alembic.config import main; sys.argv = ['alembic', 'upgrade', 'head']; main()"

# Seed E2E test data in development environment
docker-dev-seed:
    cd {{justfile_dir()}}
    docker compose -f docker-compose.yml -f docker-compose.dev.yml exec -T backend uv run python scripts/seed_e2e_data.py

# Down the Docker services for production
docker-prod-down:
    cd {{justfile_dir()}}
    docker compose -f docker-compose.yml down

# Down the Docker services for development
docker-dev-down:
    cd {{justfile_dir()}}
    docker compose -f docker-compose.yml -f docker-compose.dev.yml down -v --remove-orphans

# Down the Docker services for e3e
docker-e2e-down:
    cd {{justfile_dir()}}
    docker compose -f docker-compose.e2e.yml down -v --remove-orphans

# -----------------------------
# 🤖 CI Workflow (Three-Tier Architecture)
# PHONY: ci-check
# Note: Runs all checks and tests across all three tiers.
# -----------------------------

# Setup CI checks and dependencies for CI workflow
[unix]
ci-setup:
    cd {{justfile_dir()}}
    uv sync --dev --group ci || @echo "Make sure uv is installed manually"
    uv run pre-commit install --hook-type commit-msg || @echo "Make sure pre-commit is installed manually"
    pnpm install --save-dev commitlint @commitlint/config-conventional || @echo "Make sure pnpm is installed manually"

[windows]
ci-setup:
    cd {{justfile_dir()}}
    uv sync --dev --group ci || @echo "Make sure uv is installed manually"
    $env:PYTHONUTF8=1; uv run pre-commit install --hook-type commit-msg || @echo "Make sure pre-commit is installed manually"
    pnpm install --save-dev commitlint @commitlint/config-conventional || @echo "Make sure pnpm is installed manually"

# Run all checks and tests for the entire project (three-tier architecture)
ci-check:
    cd {{justfile_dir()}}
    just format-check
    just check
    just test-backend
    just test-frontend
    just test-e2e

# Run CI workflow locally with act
github-actions-test:
    cd {{justfile_dir()}}
    just ci-setup
    @echo "Running CI workflow"
    act push --workflows .github/workflows/CI.yml --container-architecture linux/amd64
    @echo "Running Code Quality workflow"
    act push --workflows .github/workflows/ci-check.yml --container-architecture linux/amd64

# Run all checks and tests for the backend only
backend-check:
    cd {{justfile_dir()}}
    just format-check
    just check
    just test-backend

# -----------------------------
# 🗄️ Database Tasks
# PHONY: db-drop-test, db-migrate-test, db-reset, check-schema, seed-e2e-data
# Note: Requires $TEST_DATABASE_URL to be set in your environment.
# -----------------------------

# Drop the test database schema and recreate it
db-drop-test:
    @echo "Dropping test database..."
    @psql "$TEST_DATABASE_URL" -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;" || true

# Run Alembic migrations against the test database
db-migrate-test:
    @echo "Running Alembic migrations on test database..."
    @TEST_DATABASE_URL="$TEST_DATABASE_URL" alembic upgrade head

# Full reset: drop, recreate, migrate for the test database
db-reset: db-drop-test db-migrate-test
    @echo "Test database reset and migrated successfully!"

# Seed E2E test data for full-stack testing
seed-e2e-data:
    cd {{justfile_dir()}}
    uv run python scripts/seed_e2e_data.py

# Check the schema types against the database
check-schema:
    uv run python scripts/dev/check_schema_types.py

# -----------------------------
# 🚀 Development Environment (Decoupled)
# PHONY: dev, dev-backend, dev-frontend, dev-fullstack
# -----------------------------

# Development: Run migrations and start the backend dev server only
dev-backend:
    cd {{justfile_dir()}}
    alembic upgrade head
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-seed-db:
    cd {{justfile_dir()}}
    uv run --script scripts/seed_e2e_data.py

# Development: Start the frontend dev server only (requires backend running separately)
[unix]
dev-frontend:
    cd {{justfile_dir()}}/frontend && pnpm dev --host 0.0.0.0 --port 5173

[windows]
dev-frontend:
    cd {{justfile_dir()}}/frontend; pnpm dev --host 0.0.0.0 --port 5173

# Development: Start both backend and frontend in Docker with hot reload
dev-fullstack:
    cd {{justfile_dir()}}
    just docker-dev-up-watch

# Legacy development command (runs backend only)
dev:
    just dev-backend

# -----------------------------
# Frontend Tasks
# -----------------------------

# Start the frontend dev server
[unix]
frontend-dev:
    cd {{justfile_dir()}}/frontend && pnpm dev

[windows]
frontend-dev:
    cd {{justfile_dir()}}/frontend; pnpm dev

# Build the frontend for static deploy
[unix]
frontend-build:
    cd {{justfile_dir()}}/frontend && pnpm install && pnpm build

[windows]
frontend-build:
    cd {{justfile_dir()}}/frontend; pnpm install; pnpm build

# Run unit + e2e frontend tests (legacy - use test-frontend instead)
frontend-test:
    just frontend-test-unit
    just frontend-test-e2e

# Run only frontend unit tests
[unix]
frontend-test-unit:
    cd {{justfile_dir()}}/frontend && pnpm exec vitest run

[windows]
frontend-test-unit:
    cd {{justfile_dir()}}/frontend; pnpm exec vitest run

# Run only frontend E2E tests (mocked APIs)
[unix]
frontend-test-e2e:
    cd {{justfile_dir()}}/frontend && pnpm exec playwright test

[windows]
frontend-test-e2e:
    cd {{justfile_dir()}}/frontend; pnpm exec playwright test

# Run only frontend E2E tests with full backend
[unix]
frontend-test-e2e-full:
    cd {{justfile_dir()}}/frontend && pnpm exec playwright test --config=playwright.config.e2e.ts

[windows]
frontend-test-e2e-full:
    cd {{justfile_dir()}}/frontend; pnpm exec playwright test --config=playwright.config.e2e.ts

# Lint frontend code using eslint and svelte check
[unix]
frontend-lint:
    cd {{justfile_dir()}}/frontend && pnpm lint

[windows]
frontend-lint:
    cd {{justfile_dir()}}/frontend; pnpm lint

# Format frontend code using pnpm format
[unix]
frontend-format:
    cd {{justfile_dir()}}/frontend && pnpm format

[windows]
frontend-format:
    cd {{justfile_dir()}}/frontend; pnpm format

# Run all frontend checks including linting, testing, and building
frontend-check:
    just frontend-lint
    just frontend-test
    just frontend-build

# Run only frontend E2E tests with UI for interactive testing
[unix]
frontend-test-e2e-ui:
    cd {{justfile_dir()}}/frontend && pnpm exec playwright test --ui

[windows]
frontend-test-e2e-ui:
    cd {{justfile_dir()}}/frontend; pnpm exec playwright test --ui

# Run only frontend E2E tests with UI for interactive testing
[unix]
frontend-test-e2e-full-ui:
    cd {{justfile_dir()}}/frontend && pnpm exec playwright test --ui --config=playwright.config.e2e.ts

[windows]
frontend-test-e2e-full-ui:
    cd {{justfile_dir()}}/frontend; pnpm exec playwright test --ui --config=playwright.config.e2e.ts

# -----------------------------
# 🚢 Production Build & Deployment
# PHONY: build-prod, deploy-prod, build-frontend-prod
# -----------------------------

# Build frontend for SSR production deployment
[unix]
build-frontend-prod:
    cd {{justfile_dir()}}/frontend && pnpm install --frozen-lockfile && pnpm build

[windows]
build-frontend-prod:
    cd {{justfile_dir()}}/frontend; pnpm install --frozen-lockfile; pnpm build

# Build all production assets (backend + frontend)
build-prod:
    just build
    just build-frontend-prod

# Deploy production environment (Docker Compose)
deploy-prod:
    cd {{justfile_dir()}}
    just docker-build
    just docker-prod-up
    @echo "✅ Production deployment started. Check docker compose logs for status."

# Stop production deployment
deploy-prod-stop:
    just docker-prod-down
    @echo "✅ Production deployment stopped."
