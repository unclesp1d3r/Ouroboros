# justfile - Ouroboros Developer Tasks
set shell := ["bash", "-cu"]
set windows-powershell := true
set dotenv-load := true
set ignore-comments := true

# Use mise to manage all dev tools (go, pre-commit, uv, etc.)
# See mise.toml for tool versions
mise_exec := "mise exec --"

default:
    @just --choose

alias h := help
alias test := test-backend

help:
    just --summary

# -----------------------------
# Setup & Installation
# -----------------------------

# Install dependencies and setup pre-commit hooks
[unix]
install:
    # Set up dev env & pre-commit hooks
    {{ mise_exec }} uv sync --dev --all-groups --all-packages
    {{ mise_exec }} uv run pre-commit install --hook-type commit-msg

[windows]
install:
    cd {{justfile_dir()}}
    # Set up dev env & pre-commit hooks
    {{ mise_exec }} uv sync --dev --all-groups --all-packages
    $env:PYTHONUTF8=1; {{ mise_exec }} uv run pre-commit install --hook-type commit-msg

# Update uv and bun dependencies
[unix]
update-deps:
    cd {{justfile_dir()}}
    mise upgrade --bump --local
    {{ mise_exec }} uv sync --dev --all-groups --all-packages -U
    cd frontend && {{ mise_exec }}  bun update
    {{ mise_exec }} uv run pre-commit autoupdate

[windows]
update-deps:
    cd {{justfile_dir()}}
    {{ mise_exec }} uv sync --dev --all-groups --all-packages -U
    cd frontend; {{ mise_exec }}  bun update
    $env:PYTHONUTF8=1; {{ mise_exec }} uv run pre-commit autoupdate


# -----------------------------
# Linting, Typing, Dep Check
# -----------------------------

pre-commit-run:
    {{ mise_exec }} uv lock --locked
    {{ mise_exec }} uv run pre-commit run -a

# Run all pre-commit checks
check: pre-commit-run based-pyright

based-pyright:
    {{ mise_exec }} uv run --group dev basedpyright -p pyproject.toml

# Format code using ruff, mdformat, and svelte check
format: frontend-format
    {{ mise_exec }} uv run --group dev ruff format .

# Check code formatting using ruff and mdformat
format-check:
    {{ mise_exec }} uv run --group dev ruff format --check

docs-format-check:
    {{ mise_exec }} uv run --group ci python -m mdformat --check *.md docs/**/*.md

docs-format:
    {{ mise_exec }} uv run --group ci python -m mdformat *.md docs/**/*.md

# Run all linting checks
lint: format-check docs-format-check check frontend-lint

# -----------------------------
# Testing & Coverage (Three-Tier Architecture)
# -----------------------------

# Run backend Python tests (Layer 1: Backend API/unit integration)
test-backend:
    cd {{justfile_dir()}}
    {{ mise_exec }} uv run pytest -n auto --cov --cov-config=pyproject.toml --cov-report=xml --tb=short -q

# Run frontend tests with mocked APIs (Layer 2: Frontend UI and logic validation)
[unix]
test-frontend:
    cd {{justfile_dir()}}/frontend && {{ mise_exec }} bunx vitest run && {{ mise_exec }} bunx playwright test

[windows]
test-frontend:
    cd {{justfile_dir()}}/frontend
    {{ mise_exec }} bunx vitest run
    {{ mise_exec }} bunx playwright test

# Run full-stack E2E tests against Docker backend (Layer 3: True user flows across real stack)
[unix]
test-e2e:
    cd {{justfile_dir()}}/frontend && {{ mise_exec }} bunx playwright test --config=playwright.config.e2e.ts

[windows]
test-e2e:
    cd {{justfile_dir()}}/frontend
    {{ mise_exec }} bunx playwright test --config=playwright.config.e2e.ts

# Run all python tests with maxfail=1 and disable warnings
test-fast:
    {{ mise_exec }} uv run pytest -n auto --maxfail=1 --disable-warnings -v tests/

# Run coverage report
coverage:
    {{ mise_exec }} uv run coverage report

# -----------------------------
# Build & Clean
# PHONY: build, clean-build
# -----------------------------

# Clean up .pyc files, __pycache__, and pytest cache
[unix]
clean:
    cd {{justfile_dir()}}
    @echo "Cleaning .pyc files, __pycache__, and .pytest_cache..."
    find . -type d -name "__pycache__" -exec rm -rf "{}" +
    find . -type f -name "*.pyc" -delete
    rm -rf .pytest_cache
    rm -rf dist build *.egg-info

# Build the backend project
build:
    {{ mise_exec }} uvx --from build pyproject-build --installer uv

# Clean up and build the project
clean-build: ci-check clean build

# Clean up .pyc files, __pycache__, and pytest cache before testing
clean-test: clean test-backend

# Generate CHANGELOG.md from commits (requires mise: git-cliff)
release:
    @echo "Generating changelog with git-cliff..."
    {{ mise_exec }} git cliff -o CHANGELOG.md --config cliff.toml
    @echo "Changelog updated! Commit and tag when ready."

# Preview changelog without writing (requires mise: git-cliff)
release-preview:
    {{ mise_exec }} git cliff --config cliff.toml

# -----------------------------
# Documentation
# PHONY: docs, docs-test, docs-export
# -----------------------------

# Serve documentation locally with mkdocs
docs:
    {{ mise_exec }} uv run mkdocs serve --dev-addr 0.0.0.0:9090

# Test documentation build
docs-test:
    {{ mise_exec }} uv run mkdocs build -s

# Export documentation to a single combined PDF
docs-export:
    # Export a single combined PDF via mkdocs-exporter
    {{ mise_exec }} uv run mkdocs build

# -----------------------------
# Docker Tasks
# PHONY: docker-build, docker-down, docker-up
# -----------------------------

# Check the Dockerfiles syntax for errors
docker-file-check:
    cd {{justfile_dir()}}
    {{ mise_exec }} docker build --check .
    cd {{justfile_dir()}}/frontend
    {{ mise_exec }} docker build --check .

# Build the Docker image
docker-build:
    cd {{justfile_dir()}}
    {{ mise_exec }} docker compose build

# Build E2E test environment Docker images
docker-build-e2e:
    cd {{justfile_dir()}}
    {{ mise_exec }} docker compose -f docker-compose.e2e.yml build

# Up the Docker services
docker-prod-up:
    cd {{justfile_dir()}}
    {{ mise_exec }} docker compose -f docker-compose.yml up -d

# Up the Docker services for development with hot reload
docker-dev-up:
    cd {{justfile_dir()}}
    {{ mise_exec }} docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --remove-orphans --build

# Up the Docker services for development with hot reload and do not detach from the logs
docker-dev-up-watch: docker-dev-up docker-dev-migrate docker-dev-seed
    @echo "Following logs..."
    {{ mise_exec }} docker compose -f docker-compose.yml -f docker-compose.dev.yml logs -f

# Up the Docker services for E2E testing
docker-e2e-up:
    cd {{justfile_dir()}}
    {{ mise_exec }} docker compose -f docker-compose.e2e.yml up -d --wait

# Run database migrations in development environment
docker-dev-migrate:
    cd {{justfile_dir()}}
    {{ mise_exec }} docker compose -f docker-compose.yml -f docker-compose.dev.yml exec -T backend uv run alembic upgrade head

# Seed E2E test data in development environment
docker-dev-seed:
    cd {{justfile_dir()}}
    {{ mise_exec }} docker compose -f docker-compose.yml -f docker-compose.dev.yml exec -T backend uv run --script scripts/seed_e2e_data.py

# Down the Docker services for production
docker-prod-down:
    cd {{justfile_dir()}}
    {{ mise_exec }} docker compose -f docker-compose.yml down

# Down the Docker services for development
docker-dev-down:
    cd {{justfile_dir()}}
    {{ mise_exec }} docker compose -f docker-compose.yml -f docker-compose.dev.yml down -v --remove-orphans

# Down the Docker services for e3e
docker-e2e-down:
    cd {{justfile_dir()}}
    {{ mise_exec }} docker compose -f docker-compose.e2e.yml down -v --remove-orphans

# -----------------------------
# CI Workflow (Three-Tier Architecture)
# PHONY: ci-check
# Note: Runs all checks and tests across all three tiers.
# -----------------------------

# Setup CI checks and dependencies (requires mise: uv, bun, pre-commit)
[unix]
ci-setup:
    cd {{justfile_dir()}}
    {{ mise_exec }} uv sync --dev --group ci
    {{ mise_exec }} uv run pre-commit install --hook-type commit-msg
    cd frontend && {{ mise_exec }} bun add -d commitlint @commitlint/config-conventional

[windows]
ci-setup:
    cd {{justfile_dir()}}
    {{ mise_exec }} uv sync --dev --group ci
    $env:PYTHONUTF8=1; {{ mise_exec }} uv run pre-commit install --hook-type commit-msg
    cd frontend; {{ mise_exec }} bun add -d commitlint @commitlint/config-conventional

# Run all checks and tests for the entire project (three-tier architecture)
ci-check: lint test-backend test-frontend test-e2e

# Reduced CI check for GitHub Actions
github-ci-check: lint test-fast test-frontend

# Run CI workflow locally with act
github-actions-test: ci-setup
    @echo "Running CI workflow"
    {{ mise_exec }} act push --workflows .github/workflows/CI.yml --container-architecture linux/amd64
    @echo "Running Code Quality workflow"
    {{ mise_exec }} act push --workflows .github/workflows/ci-check.yml --container-architecture linux/amd64

# Run all checks and tests for the backend only
backend-check: format-check check test-backend

# -----------------------------
# Database Tasks
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
    {{ mise_exec }} uv run alembic upgrade head

# Full reset: drop, recreate, migrate for the test database
db-reset: db-drop-test db-migrate-test
    @echo "Test database reset and migrated successfully!"

# Seed E2E test data for full-stack testing
seed-e2e-data:
    cd {{justfile_dir()}}
    {{ mise_exec }} uv run --script scripts/seed_e2e_data.py

# Check the schema types against the database
check-schema:
    {{ mise_exec }} uv run --script scripts/dev/check_schema_types.py

# -----------------------------
# Development Environment (Decoupled)
# PHONY: dev, dev-backend, dev-frontend, dev-fullstack
# -----------------------------

# Development: Run migrations and start the backend dev server only
dev-backend:
    cd {{justfile_dir()}}
    {{ mise_exec }} uv run alembic upgrade head
    {{ mise_exec }} uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-seed-db:
    cd {{justfile_dir()}}
    {{ mise_exec }} uv run --script scripts/seed_e2e_data.py

# Development: Start the frontend dev server only (requires backend running separately)
[unix]
dev-frontend:
    cd {{justfile_dir()}}/frontend && {{ mise_exec }} bun run dev --host 0.0.0.0 --port 5173

[windows]
dev-frontend:
    cd {{justfile_dir()}}/frontend; {{ mise_exec }} bun run dev --host 0.0.0.0 --port 5173

# Development: Start both backend and frontend in Docker with hot reload
dev-fullstack: docker-dev-up-watch

# Legacy development command (runs backend only)
dev: dev-backend

# -----------------------------
# Frontend Tasks
# -----------------------------

# Start the frontend dev server
[unix]
frontend-dev:
    cd {{justfile_dir()}}/frontend && {{ mise_exec }} bun run dev

[windows]
frontend-dev:
    cd {{justfile_dir()}}/frontend; {{ mise_exec }} bun run dev

# Build the frontend for static deploy
[unix]
frontend-build:
    cd {{justfile_dir()}}/frontend && {{ mise_exec }} bun install && {{ mise_exec }} bun run build

[windows]
frontend-build:
    cd {{justfile_dir()}}/frontend; {{ mise_exec }} bun install; {{ mise_exec }} bun run build

# Run only frontend unit tests
[unix]
frontend-test-unit:
    cd {{justfile_dir()}}/frontend && {{ mise_exec }} bunx vitest run

[windows]
frontend-test-unit:
    cd {{justfile_dir()}}/frontend; {{ mise_exec }} bunx vitest run

# Run only frontend E2E tests (mocked APIs)
[unix]
frontend-test-e2e:
    cd {{justfile_dir()}}/frontend && {{ mise_exec }} bunx playwright test

[windows]
frontend-test-e2e:
    cd {{justfile_dir()}}/frontend; {{ mise_exec }} bunx playwright test

# Lint frontend code using eslint and svelte check
[unix]
frontend-lint:
    cd {{justfile_dir()}}/frontend && {{ mise_exec }} bun run lint

[windows]
frontend-lint:
    cd {{justfile_dir()}}/frontend; {{ mise_exec }} bun run lint

# Format frontend code using bun format
[unix]
frontend-format:
    cd {{justfile_dir()}}/frontend && {{ mise_exec }} bun run format

[windows]
frontend-format:
    cd {{justfile_dir()}}/frontend; {{ mise_exec }} bun run format

# Run all frontend checks including linting, testing, and building
frontend-check: frontend-lint test-frontend frontend-build

# Run only frontend E2E tests with UI for interactive testing
[unix]
frontend-test-e2e-ui:
    cd {{justfile_dir()}}/frontend && {{ mise_exec }} bunx playwright test --ui

[windows]
frontend-test-e2e-ui:
    cd {{justfile_dir()}}/frontend; {{ mise_exec }} bunx playwright test --ui

# Run only frontend E2E tests with UI for interactive testing
[unix]
frontend-test-e2e-full-ui:
    cd {{justfile_dir()}}/frontend && {{ mise_exec }} bunx playwright test --ui --config=playwright.config.e2e.ts

[windows]
frontend-test-e2e-full-ui:
    cd {{justfile_dir()}}/frontend; {{ mise_exec }} bunx playwright test --ui --config=playwright.config.e2e.ts

# -----------------------------
# Production Build & Deployment
# PHONY: build-prod, deploy-prod, build-frontend-prod
# -----------------------------

# Build frontend for SSR production deployment
[unix]
build-frontend-prod:
    cd {{justfile_dir()}}/frontend && {{ mise_exec }} bun install --frozen-lockfile && {{ mise_exec }} bun run build

[windows]
build-frontend-prod:
    cd {{justfile_dir()}}/frontend; {{ mise_exec }} bun install --frozen-lockfile; {{ mise_exec }} bun run build

# Build all production assets (backend + frontend)
build-prod: build build-frontend-prod

# Deploy production environment (Docker Compose)
deploy-prod: docker-build docker-prod-up

# Stop production deployment
deploy-prod-stop: docker-prod-down
    @echo "Production deployment stopped."
