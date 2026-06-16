# Development Setup

This guide covers setting up your development environment for Ouroboros

---

## Table of Contents

<!-- mdformat-toc start --slug=gitlab --no-anchors --maxlevel=2 --minlevel=1 -->

- [Development Setup](#development-setup)
  - [Table of Contents](#table-of-contents)
  - [Prerequisites](#prerequisites)
  - [Initial Setup](#initial-setup)
  - [Development Environment](#development-environment)
  - [Development Commands](#development-commands)
  - [Interface Development](#interface-development)
  - [Database Management](#database-management)
  - [Testing](#testing)
  - [Code Quality](#code-quality)
  - [Documentation](#documentation)
  - [Docker Development](#docker-development)
  - [Debugging](#debugging)
  - [CI/CD Pipeline](#cicd-pipeline)
  - [Best Practices](#best-practices)

<!-- mdformat-toc end -->

---

## Prerequisites

1. **System Requirements**

   - Python 3.13 or higher
   - Docker and Docker Compose
   - Git
   - uv package manager

2. **Development Tools**

   - Visual Studio Code (recommended)
   - Python extension for VS Code
   - Docker extension for VS Code
   - Git client

## Initial Setup

1. **Clone the Repository**

   ```bash
   git clone https://github.com/yourusername/ouroboros.git
   cd ouroboros
   ```

2. **Create Virtual Environment**

   ```bash
   python3.13 -m venv .venv
   source .venv/bin/activate  # Unix/macOS
   # or
   .venv\Scripts\activate     # Windows
   ```

3. **Install Dependencies**

   ```bash
   # Install uv
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Install dependencies
   uv pip install -e ".[dev]"
   ```

4. **Install Pre-commit Hooks**

   ```bash
   pre-commit install
   ```

## Development Environment

### VS Code Configuration

1. **Settings** Create `.vscode/settings.json`:

   ```json
   {
     "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
     "python.analysis.typeCheckingMode": "strict",
     "python.formatting.provider": "black",
     "python.linting.enabled": true,
     "python.linting.mypyEnabled": true,
     "python.linting.ruffEnabled": true,
     "[python]": {
       "editor.formatOnSave": true,
       "editor.codeActionsOnSave": {
         "source.organizeImports": true
       }
     }
   }
   ```

2. **Extensions** Install recommended extensions:

   ```json
   {
     "recommendations": [
       "ms-python.python",
       "ms-python.vscode-pylance",
       "ms-azuretools.vscode-docker",
       "tamasfe.even-better-toml",
       "charliermarsh.ruff"
     ]
   }
   ```

### Environment Variables

Create `.env` file:

```bash
# Development Settings
ENVIRONMENT=development
DEBUG=true

# Database
DATABASE_URL=postgresql+asyncpg://ouroboros:development@localhost:5432/cipherswarm_dev

# Redis
REDIS_URL=redis://localhost:6379/0

# MinIO
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin
MINIO_ENDPOINT=localhost:9000
MINIO_SECURE=false

# Security
SECRET_KEY=development_secret_key
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

## Development Commands

The project uses `just` for task automation:

```bash
# Start development services
just dev

# Run tests
just test

# Run linters
just lint

# Format code
just format

# Generate API documentation
just docs

# Clean development environment
just clean
```

## Interface Development

Ouroboros provides two web interface options for development:

### SvelteKit Frontend Development

For frontend-focused development with the SvelteKit interface:

```bash
# Install frontend dependencies
cd frontend
npm install

# Start frontend development server
npm run dev

# Build frontend for production
npm run build
```

The SvelteKit frontend runs on `http://localhost:5173` and proxies API calls to the FastAPI backend.

### NiceGUI Interface Development

For Python-native interface development with NiceGUI:

```bash
# Enable NiceGUI interface
export NICEGUI_ENABLED=true

# Start backend with NiceGUI interface
just dev

# Access NiceGUI interface at http://localhost:8000/ui/
```

**NiceGUI Development Benefits:**

- **Python-only development**: No JavaScript/TypeScript knowledge required
- **Integrated debugging**: Use Python debugger for both backend and UI
- **Rapid prototyping**: Quick UI changes without frontend build process
- **Simplified testing**: Test UI components using NiceGUI testing framework

**Development Structure:**

```
app/ui/
├── __init__.py              # NiceGUI app initialization
├── auth/                    # Authentication components
├── components/              # Reusable UI components
├── pages/                   # Page components
└── services/                # UI-specific services
```

**Hot Reload:**

NiceGUI supports hot reload for rapid development:

```python
# Enable hot reload in development
if settings.DEBUG:
    ui.run_with(app, mount_path="/ui", reload=True, debug=True)
```

## Database Management

### Migrations

```bash
# Create new migration
just db-revision "description"

# Apply migrations
just db-upgrade

# Rollback migration
just db-downgrade

# Show migration history
just db-history
```

### Development Database

```bash
# Reset development database
just db-reset

# Seed test data
just db-seed
```

## Testing

### Running Tests

```bash
# Run all tests
just test

# Run specific test file
just test tests/test_api.py

# Run with coverage
just test-cov
```

### Test Configuration

Create `tests/conftest.py`:

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
async def client() -> TestClient:
    """Create test client."""
    from app.main import app

    return TestClient(app)


@pytest.fixture
async def db_session() -> AsyncSession:
    """Create test database session."""
    from app.db.session import get_session

    async with get_session() as session:
        yield session
```

## Code Quality

### Linting

The project uses multiple linters:

1. **Ruff**

   ```bash
   # Run ruff
   just lint-ruff

   # Fix auto-fixable issues
   just lint-ruff-fix
   ```

2. **MyPy**

   ```bash
   # Run type checking
   just lint-mypy
   ```

3. **Black**

   ```bash
   # Format code
   just format
   ```

### Pre-commit Hooks

The project uses pre-commit hooks for code quality:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.2.1
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies:
          - types-all
```

## Documentation

### Building Documentation

```bash
# Serve documentation
just docs

# Build static site
just docs-build

# Test documentation
just docs-test
```

### Adding New Pages

1. Create markdown file in `docs/` directory
2. Update `mkdocs.yml` navigation
3. Add internal links using relative paths
4. Include code examples and diagrams

## Docker Development

### Local Development

```bash
# Start development stack
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# View logs
docker compose logs -f

# Stop services
docker compose down
```

### Testing with Docker

```bash
# Run tests in container
docker compose -f docker-compose.yml -f docker-compose.test.yml up --exit-code-from tests

# Clean test environment
docker compose -f docker-compose.yml -f docker-compose.test.yml down -v
```

## Debugging

### VS Code Configuration

Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "app.main:app",
        "--reload",
        "--port",
        "8000"
      ],
      "jinja": true,
      "justMyCode": false
    },
    {
      "name": "Python: Current File",
      "type": "python",
      "request": "launch",
      "program": "${file}",
      "console": "integratedTerminal",
      "justMyCode": false
    }
  ]
}
```

### Debug Tools

1. **FastAPI Debug Toolbar**

   ```python
   from fastapi.middleware.debug import DebugMiddleware

   app.add_middleware(DebugMiddleware)
   ```

2. **Python Debugger**

   ```python
   import pdb

   pdb.set_trace()
   ```

3. **Logging**

   ```python
   import logging

   logging.basicConfig(level=logging.DEBUG)
   ```

## CI/CD Pipeline

### GitHub Actions

The project uses GitHub Actions for CI/CD:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-python@v5
        with:
          python-version: '3.13'
      - name: Install dependencies
        run: |
          curl -LsSf https://astral.sh/uv/install.sh | sh
          uv pip install -e ".[dev]"
      - name: Run tests
        run: just test-cov
      - name: Upload coverage
        uses: codecov/codecov-action@v4

  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-python@v5
        with:
          python-version: '3.13'
      - name: Install dependencies
        run: |
          curl -LsSf https://astral.sh/uv/install.sh | sh
          uv pip install -e ".[dev]"
      - name: Run linters
        run: |
          just lint-ruff
          just lint-mypy
```

## Best Practices

1. **Code Style**

   - Follow PEP 8
   - Use type hints
   - Write docstrings
   - Keep functions small

2. **Testing**

   - Write unit tests
   - Use fixtures
   - Mock external services
   - Test edge cases

3. **Git Workflow**

   - Create feature branches
   - Write descriptive commits
   - Keep PRs focused
   - Review code changes

4. **Documentation**

   - Update docs with changes
   - Include examples
   - Document APIs
   - Add diagrams

For more information:

- [Contributing Guide](contributing.md)
- [Code Style Guide](style.md)
- [Testing Guide](testing.md)
- [API Documentation](../api/overview.md)
