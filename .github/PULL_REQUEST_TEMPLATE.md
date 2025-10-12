## Pull Request Description

<!-- Provide a clear and concise description of the changes -->

## Type of Change

- [ ] **Feature** (new functionality)
- [ ] **Bug fix** (non-breaking change that fixes an issue)
- [ ] **Hotfix** (critical fix requiring immediate attention)
- [ ] **Performance** (code change that improves performance)
- [ ] **Refactor** (code restructuring without behavior changes)
- [ ] **Documentation** (documentation-only changes)
- [ ] **CI/Build** (changes to CI/build process)
- [ ] **Breaking change** (fix or feature that causes existing functionality to change)

## Test Strategy

<!-- Select the smallest tier that covers your changes per WARP.md guidance -->

- [ ] **Backend tests** (`just test-backend`) - API endpoints, services, models
- [ ] **Frontend tests** (`just test-frontend`) - UI components, client logic
- [ ] **E2E tests** (`just test-e2e`) - Complete user workflows
- [ ] **Full CI check** (`just ci-check`) - All tiers (PR-ready validation)
- [ ] **Documentation only** (no tests needed)

### Test Results

<!-- Confirm tests pass locally before opening PR -->

```bash
# Paste relevant test output here
```

## WARP.md Compliance Checklist

- [ ] **No PROTECTED areas modified** unless explicitly permitted
  - [ ] `contracts/v1_api_swagger.json` unchanged (Agent API v1 immutable)
  - [ ] `alembic/` migrations only via Alembic CLI
  - [ ] `.cursor/`, `.github/workflows/` changes have proper justification
- [ ] **Conventional Commit title** (will become squash commit message)
- [ ] **Rebased on target branch** (rebased on latest `main`)
- [ ] **Appropriate test tier selected** and ran locally
- [ ] **PR scope manageable** (under ~400 lines net change when feasible)

## Architecture Impact

<!-- Note impact on Service Layer, API surfaces, etc. -->

- [ ] **Service Layer** - Business logic changes in `app/core/services/`
- [ ] **Agent API v1** - Must maintain exact compatibility with `contracts/v1_api_swagger.json`
- [ ] **Web UI API** - FastAPI-native, can evolve with versioning
- [ ] **Control API** - Must use RFC9457 `application/problem+json` format
- [ ] **Database** - Uses SQLAlchemy 2.0 async patterns, Alembic migrations
- [ ] **Frontend** - SvelteKit 5 with Runes, SSR-first data loading
- [ ] **None** - No architectural impact

## Security Impact

- [ ] **None** - No security impact
- [ ] **Dependency updates** - Scanned with SAST/Dependabot
- [ ] **Data exposure risk** - Handles sensitive data
- [ ] **Authentication/Authorization** - Changes auth logic
- [ ] **Input validation** - New input handling

<!-- Describe any security-relevant changes -->

## Related Issues

<!-- Link to related issues using GitHub's syntax -->

Closes #
Related to #

## Milestone

<!-- Assign to appropriate milestone -->

- [ ] **v2.0.0-alpha.1** - Core services, agent compatibility smoke-tested
- [ ] **v2.0.0-beta.1** - Feature-complete, stabilization, UI polish
- [ ] **v2.0.0-rc.1** - Performance, security, migrations finalized
- [ ] **v2.0.0** - GA release
- [ ] **Maintenance** - Bug fixes and minor improvements

## Breaking Changes

<!-- Describe any backward-incompatible changes and required migration steps -->

## Additional Context

<!-- Add screenshots, logs, or other context -->

## Pre-merge Verification

- [ ] All required status checks pass
- [ ] Targets `main` branch (v2-primary workflow)
- [ ] Conventional Commit title follows format: `type(scope): description`
- [ ] Changes align with Ouroboros architecture patterns from WARP.md
- [ ] No direct database queries; uses SQLAlchemy ORM/async patterns
- [ ] Error handling uses appropriate exceptions (HTTPException vs RFC9457)
- [ ] No direct pushes to protected branches (PR-only workflow)

---

*This template ensures compliance with WARP.md golden rules and Ouroboros development standards.*
