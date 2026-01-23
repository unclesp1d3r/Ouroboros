# Contributing to Ouroboros

Thank you for your interest in contributing to Ouroboros! We appreciate your efforts and value your time. This guide will help you understand how to contribute effectively to the project.

⚡ **Quick Start**: See [WARP.md](WARP.md) for comprehensive development rules and setup commands.

---

## Table of Contents

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=3 --minlevel=1 -->

- [Contributing to Ouroboros](#contributing-to-ouroboros)
  - [Table of Contents](#table-of-contents)
  - [Getting Started](#getting-started)
    - [1. Setup Your Environment](#1-setup-your-environment)
    - [2. Verify Setup](#2-verify-setup)
  - [Git Workflow - V2-Primary Development](#git-workflow---v2-primary-development)
    - [Branch Structure](#branch-structure)
    - [Development Workflow](#development-workflow)
  - [Conventional Commits](#conventional-commits)
    - [Format](#format)
    - [Types](#types)
    - [Scopes (Examples)](#scopes-examples)
    - [Examples](#examples)
  - [Testing Strategy](#testing-strategy)
    - [Tier 1: Backend Tests](#tier-1-backend-tests)
    - [Tier 2: Frontend Tests](#tier-2-frontend-tests)
    - [Tier 3: E2E Tests](#tier-3-e2e-tests)
    - [Full CI Check](#full-ci-check)
  - [Protected Areas](#protected-areas)
  - [Code Review Process](#code-review-process)
    - [Automated Reviews](#automated-reviews)
    - [Review Focus Areas](#review-focus-areas)
    - [Single Maintainer Workflow](#single-maintainer-workflow)
  - [Submitting Contributions](#submitting-contributions)
    - [Before Opening PR](#before-opening-pr)
    - [Opening the PR](#opening-the-pr)
    - [PR Requirements](#pr-requirements)
  - [Code of Conduct](#code-of-conduct)

<!-- mdformat-toc end -->

---

## Getting Started

To get started contributing to Ouroboros:

### 1. Setup Your Environment

1. Fork the repository from [Ouroboros](https://github.com/unclesp1d3r/Ouroboros)

2. Clone your fork locally:

   ```bash
   git clone https://github.com/your-username/Ouroboros.git
   cd Ouroboros
   ```

3. Install dependencies and setup:

   ```bash
   just install  # Sets up Python/JS deps, pre-commit hooks
   ```

4. Start development environment:

   ```bash
   just docker-dev-up-watch  # Full stack with hot reload
   # OR
   just dev  # Backend only
   ```

### 2. Verify Setup

- [http://localhost:8000/docs](http://localhost:8000/docs) (Swagger UI)
- [http://localhost:5173](http://localhost:5173) (SvelteKit Frontend)
- [http://localhost:8000/redoc](http://localhost:8000/redoc) (ReDoc)

## Git Workflow - V2-Primary Development

Ouroboros uses a **streamlined workflow** focused on v2 development with v1 archived for reference:

### Branch Structure

```mermaid
gitGraph
  commit id: "v1 archived"
  branch v1-archive
  commit id: "v1 stable"
  checkout main
  commit id: "v2 promoted"
  branch feature/api/new-endpoint
  commit id: "feat"
  commit id: "tests"
  checkout main
  merge feature/api/new-endpoint
  commit id: "merge feature"
  branch release/v2.1
  commit id: "stabilize"
  commit id: "v2.1.0"
  checkout main
  merge release/v2.1
  commit id: "release"
  branch hotfix/security-patch
  commit id: "security fix"
  checkout main
  merge hotfix/security-patch
  commit id: "hotfix deployed"
```

#### Long-lived Branches

- **`main`**: Primary development branch (v2 codebase)
- **`v1-archive`**: Archived v1 stable (maintenance-only, rarely updated)

#### Short-lived Branches

- **`feature/<area>/<desc>`**: New features off `main`
- **`hotfix/<desc>`**: Emergency fixes off `main`
- **`release/<version>`**: Release preparation off `main`

### Development Workflow

#### Standard Development

```bash
# Start from main
git checkout main
git pull origin main
git checkout -b feature/api/new-feature

# Development
just dev  # or just docker-dev-up-watch
# Make changes...
just test-backend  # Run smallest tier covering changes

# Commit with Conventional Commits
git add .
git commit -m "feat(api): add project quotas"

# Stay synced with main
git fetch origin
git rebase origin/main

# Open PR targeting main
gh pr create --base main --title "feat(api): add project quotas"
```

#### Hotfixes

```bash
# Start from main
git checkout main
git pull origin main
git checkout -b hotfix/critical-security-fix

# Fix the issue...
just test-backend
git commit -m "fix(auth): patch security vulnerability"

# Open PR targeting main
gh pr create --base main --title "fix(auth): patch security vulnerability"
```

#### Releases

```bash
# Start from main
git checkout main
git pull origin main
git checkout -b release/v2.1.0

# Stabilization work...
just ci-check  # full validation
git commit -m "chore(release): prepare v2.1.0"

# Open PR targeting main
gh pr create --base main --title "chore(release): prepare v2.1.0"
```

## Conventional Commits

All commit messages **must** follow the [Conventional Commits](https://conventionalcommits.org) specification:

### Format

```text
type(scope): description

[optional body]

[optional footer(s)]
```

### Types

- **`feat`**: New feature for users
- **`fix`**: Bug fix for users
- **`docs`**: Documentation changes
- **`style`**: Code formatting (no logic changes)
- **`refactor`**: Code restructuring (no behavior changes)
- **`perf`**: Performance improvements
- **`test`**: Test additions or corrections
- **`ci`**: CI/CD configuration changes
- **`chore`**: Maintenance tasks
- **`deps`**: Dependency updates

### Scopes (Examples)

- `api`, `auth`, `models`, `services`, `frontend`, `agents`, `infra`

### Examples

```bash
feat(api): add RFC9457 error handler
fix(frontend): correct SSR auth redirect
docs(readme): update installation instructions
feat(api)!: remove deprecated endpoints  # Breaking change
```

## Testing Strategy

Ouroboros uses a **three-tier testing architecture**. Choose the **smallest tier** that covers your changes:

### Tier 1: Backend Tests

```bash
just test-backend
```

- **Scope**: API endpoints, services, models with real PostgreSQL/MongoDB
- **Technology**: pytest + testcontainers + polyfactory
- **Speed**: Fast (seconds)

### Tier 2: Frontend Tests

```bash
just test-frontend
```

- **Scope**: UI components, user interactions, client-side logic
- **Technology**: Vitest + Playwright with mocked APIs
- **Speed**: Fast (seconds)

### Tier 3: E2E Tests

```bash
just test-e2e
```

- **Scope**: Complete user workflows across real backend
- **Technology**: Playwright against full Docker stack
- **Speed**: Slow (minutes)

### Full CI Check

```bash
just ci-check  # Only when PR-ready
```

- **Use**: Complete validation before opening PR
- **Includes**: All tiers + format + lint + security checks

## Protected Areas

[WARN] **These areas require explicit permission before modification:**

- **`contracts/`** — API specifications (Agent API v1 is **IMMUTABLE**)
- **`alembic/`** — Database migrations (use Alembic CLI only)
- **`.cursor/`** — AI assistant configuration
- **`.github/workflows/`** — CI workflows (require `ci-approved` label)

**Golden Rule**: Never break Agent API v1 contract in `contracts/v1_api_swagger.json`

## Code Review Process

### Automated Reviews

- **CodeRabbit AI**: Primary review tool (configured in `.coderabbit.yml`)
- **GitHub Copilot**: Disabled per user preference

### Review Focus Areas

1. **WARP.md compliance**: Service layer patterns, architecture alignment
2. **Agent API v1 compatibility**: No breaking changes allowed
3. **Test coverage**: Appropriate tier selected and passing
4. **Security**: No hardcoded secrets, proper input validation
5. **Performance**: Async patterns, proper database usage

### Single Maintainer Workflow

- Rely on automated checks + template compliance
- Optional self-review with summary comment
- Merge after all required status checks pass

## Submitting Contributions

### Before Opening PR

1. **Run tests locally**:

   ```bash
   just test-backend  # or appropriate tier
   ```

2. **Format code**:

   ```bash
   just format
   ```

3. **Rebase on target branch**:

   ```bash
   git fetch origin
   git rebase origin/main  # all development targets main
   ```

### Opening the PR

1. **Push to your fork**:

   ```bash
   git push origin feature/api/new-feature
   ```

2. **Create PR with correct base**:

   ```bash
   gh pr create --base main --title "feat(api): add project quotas"
   ```

3. **Fill out PR template** completely

4. **Assign to milestone** (v2.0.0-alpha.1, etc.)

5. **Add appropriate labels** (type:feat, area:api, etc.)

### PR Requirements

- [x] Conventional Commit title
- [x] WARP.md compliance checklist completed
- [x] Test tier selected and passing locally
- [x] No PROTECTED areas modified without justification
- [x] PR scope under ~400 lines when feasible

## Code of Conduct

Please note that we have a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

Thank you for contributing to Ouroboros! We look forward to your pull requests.
