---

## inclusion: always

# Test Organization and Standards

## Overview

This rule consolidates cross-cutting test organization standards for Ouroboros, covering directory structure, naming conventions, coverage requirements, CI integration, and test command patterns that apply across all testing layers.

## Directory Structure Standards

### Backend Test Organization

```
tests/
├── unit/                           # Unit tests mirroring app/ structure
│   ├── services/                   # Service layer tests
│   ├── models/                     # Model tests
│   ├── core/                       # Core functionality tests
│   └── plugins/                    # Plugin tests
├── integration/                    # Integration tests grouped by API interface
│   ├── agent/                      # Agent API tests (/api/v1/client/*)
│   ├── web/                        # Web UI API tests (/api/v1/web/*)
│   ├── control/                    # Control API tests (/api/v1/control/*)
│   └── services/                   # Service integration tests
├── factories/                      # Polyfactory test data factories
│   ├── user_factory.py
│   ├── project_factory.py
│   └── campaign_factory.py
└── utils/                          # Shared test utilities and helpers
    ├── test_helpers.py
    └── hash_type_utils.py
```

### Frontend Test Organization

```
frontend/
├── src/
│   ├── lib/
│   │   └── components/
│   │       └── **/*.test.ts       # Component unit tests co-located
│   └── routes/
│       └── **/*.test.ts           # Route component tests co-located
├── e2e/                           # Playwright E2E tests with mocks
│   ├── test-utils.ts              # E2E test utilities
│   ├── agents-list.test.ts
│   └── campaigns-list.test.ts
├── tests/
│   ├── e2e/                       # Full E2E tests against real backend
│   │   ├── login.e2e.test.ts
│   │   └── campaign-workflow.e2e.test.ts
│   ├── global-setup.e2e.ts        # E2E test setup
│   └── global-teardown.e2e.ts     # E2E test cleanup
└── test-artifacts/                # Test output and artifacts
```

### Test File Naming Conventions

#### Backend Tests

- **Unit tests**: `test_{module_name}.py` (e.g., `test_campaign_service.py`)
- **Integration tests**: `test_{resource}.py` (e.g., `test_campaigns.py`)
- **Factory files**: `{model_name}_factory.py` (e.g., `campaign_factory.py`)
- **Utility files**: `{purpose}_utils.py` or `test_helpers.py`

#### Frontend Tests

- **Component tests**: `{Component}.test.ts` (e.g., `CampaignCard.test.ts`)
- **Route tests**: `{route-name}.test.ts` (e.g., `campaigns-list.test.ts`)
- **E2E tests with mocks**: `{feature}.test.ts` (e.g., `agent-registration.test.ts`)
- **Full E2E tests**: `{workflow}.e2e.test.ts` (e.g., `login-workflow.e2e.test.ts`)

## Test Environment Detection

### Universal Environment Detection Pattern

```typescript
// ✅ CORRECT - Comprehensive test environment detection
function isTestEnvironment(): boolean {
    return process.env.NODE_ENV === 'test' ||
           process.env.PLAYWRIGHT_TEST === 'true' ||
           process.env.CI === 'true';
}

// Usage in load functions
export const load: PageServerLoad = async ({ cookies }) => {
    if (isTestEnvironment()) {
        return { mockData };
    }

    // Real API calls for production
    return await fetchRealData(cookies);
};
```

### Python Test Environment Detection

```python
# ✅ CORRECT - Python test environment detection
import os


def is_test_environment() -> bool:
    return (
        os.getenv("PYTEST_CURRENT_TEST") is not None
        or os.getenv("CI") == "true"
        or os.getenv("TESTING") == "true"
    )
```

## Coverage Requirements and Standards

### Coverage Targets

- **Backend**: Minimum 80% coverage for all modules
- **Frontend**: Minimum 80% coverage for critical components
- **E2E**: Coverage of all major user workflows

### Backend Coverage Reporting

```bash
# Generate coverage reports
just test-backend                  # Includes coverage reporting
just coverage                      # Generate coverage reports

# Coverage thresholds in pyproject.toml
[tool.coverage.run]
source = ["app"]
omit = ["*/tests/*", "*/migrations/*"]

[tool.coverage.report]
fail_under = 80
show_missing = true
```

### Frontend Coverage Reporting

```bash
# Generate coverage reports
pnpm exec vitest run --coverage

# Coverage configuration in vitest.config.ts
export default defineConfig({
    test: {
        coverage: {
            provider: 'v8',
            reporter: ['text', 'json', 'html'],
            thresholds: {
                global: {
                    branches: 80,
                    functions: 80,
                    lines: 80,
                    statements: 80
                }
            }
        }
    }
});
```

### Coverage Expectations

- **All HTTP endpoints** must have corresponding integration tests
- **All business logic** (services, validators, helpers) must be covered with unit tests
- **Critical user workflows** must be covered with E2E tests
- **Error paths** and edge cases must be tested
- **Authentication and authorization** boundaries must be validated

## Test Command Patterns

### Development Commands

```bash
# Backend development testing
just test-fast                     # Quick backend tests
just test-backend                  # Full backend test suite
pytest tests/unit/services/        # Specific module tests

# Frontend development testing
just frontend-check                # Frontend tests + linting
just frontend-test-unit            # Frontend unit tests only
just frontend-test-e2e-ui          # Interactive E2E testing

# Combined development testing
just test                          # Legacy alias for test-backend
```

### Verification Commands

```bash
# Pre-commit verification
just check                         # Linting and formatting
just test-backend                  # Backend test suite
just frontend-check                # Frontend test suite

# CI verification
just ci-check                      # Complete CI pipeline
just test-e2e                      # Full E2E tests with Docker

# Coverage verification
just coverage                      # Generate coverage reports
```

### Debug and Troubleshooting Commands

```bash
# Backend debugging
pytest -v -s tests/unit/services/test_campaign_service.py::test_specific_function
pytest --pdb tests/integration/web/test_campaigns.py  # Drop into debugger

# Frontend debugging
cd frontend
pnpm exec vitest run src/lib/components/CampaignCard.test.ts --reporter=verbose
pnpm exec playwright test --debug e2e/campaigns-list.test.ts

# E2E debugging
just test-e2e                      # Full E2E tests with Docker
just docker-e2e-up                 # Start E2E environment
docker compose -f docker-compose.e2e.yml logs backend  # Service logs
```

## Mock Data Consistency Standards

### API Response Structure Consistency

```typescript
// ✅ CORRECT - Mock data must match API structure exactly
const mockCampaignListResponse = {
    items: [
        {
            id: 1,
            name: 'Test Campaign',
            status: 'active' as const,  // Use exact enum values
            created_at: '2024-01-01T00:00:00Z',  // ISO format
            hash_list: {
                id: 1,
                name: 'Test Hash List',
                hash_count: 100
            }
        }
    ],
    total_count: 1,      // snake_case as API returns
    page: 1,
    page_size: 10,
    total_pages: 1
};

// ❌ WRONG - Mismatched structure causes test failures
const mockCampaigns = {
    data: [...],         // API doesn't return 'data' wrapper
    totalCount: 1,       // API uses snake_case, not camelCase
    pageInfo: {...}      // Different pagination structure
};
```

### Cross-Layer Mock Consistency

- Frontend mocks must match backend API responses exactly
- Use the same data structures and field names across test layers
- Maintain consistency between test environments
- Update mocks when API contracts change
- Share common test data utilities where appropriate

## CI Integration Standards

### Test Execution Order

1. **Linting and formatting** (`just check`)
2. **Backend unit tests** (`just test-backend`)
3. **Frontend unit tests** (`just frontend-check`)
4. **Backend integration tests** (included in `just test-backend`)
5. **Frontend E2E tests with mocks** (included in `just frontend-check`)
6. **Full E2E tests** (`just test-e2e`) - optional for full CI

### CI Environment Configuration

```yaml
# GitHub Actions example
  - name: Run backend tests
    run: just test-backend
    env:
      DATABASE_URL: postgresql://test:test@localhost:5432/test_db
      TESTING: true

  - name: Run frontend tests
    run: just frontend-check
    env:
      NODE_ENV: test
      CI: true

  - name: Run E2E tests
    run: just test-e2e
    env:
      PLAYWRIGHT_TEST: true
      CI: true
```

### Test Isolation and Cleanup

- Each test should be independent and not rely on test execution order
- Use proper setup/teardown for test data
- Clean state between tests (handled by fixtures)
- Avoid shared mutable state between tests
- Use containerized databases for isolation

## Test Data Management

### Factory Usage Standards

- **Always use factories** for creating test data in backend tests
- **Provide required foreign keys explicitly** in test code
- **Use pre-seeded data references** when possible (e.g., `hash_type_id = 0` for MD5)
- **Set dynamic foreign keys to None** in factory defaults and require explicit setting
- **Reuse shared factories** across test files

### Test Data Lifecycle

```python
# ✅ CORRECT - Proper test data lifecycle
@pytest.mark.asyncio
async def test_campaign_creation(db_session):
    # Arrange - Create test data
    user = await UserFactory.create_async()
    project = await ProjectFactory.create_async()

    # Create required associations
    association = ProjectUserAssociation(
        user_id=user.id, project_id=project.id, role=ProjectUserRole.MEMBER
    )
    db_session.add(association)
    await db_session.commit()

    # Act - Perform the test action
    campaign = await CampaignFactory.create_async(
        project_id=project.id, created_by=user.id
    )

    # Assert - Verify the results
    assert campaign.project_id == project.id
    assert campaign.created_by == user.id
```

## Documentation and Test Quality

### Test Documentation Standards

- **Use descriptive test names** that explain the scenario being tested
- **Include docstrings** for complex test setups or business logic
- **Document test data requirements** and relationships
- **Explain non-obvious assertions** with comments
- **Note any special requirements** or constraints

### Test Quality Checklist

- [ ] Test name clearly describes the scenario
- [ ] Test follows Arrange-Act-Assert pattern
- [ ] Test data is created using factories
- [ ] Required foreign key relationships are established
- [ ] Both success and failure cases are tested
- [ ] Error messages are meaningful and actionable
- [ ] Test is independent and doesn't rely on other tests
- [ ] Cleanup is handled automatically by fixtures

## Common Anti-Patterns to Avoid

### Backend Anti-Patterns

- ❌ **Random foreign keys** in factories (causes violations)
- ❌ **Missing project associations** for project-scoped tests
- ❌ **Manual SQL** instead of ORM operations
- ❌ **Hardcoded test data** instead of factories
- ❌ **Mixing unit and integration tests** in same files

### Frontend Anti-Patterns

- ❌ **Testing implementation details** instead of behavior
- ❌ **Mismatched mock data** structures vs API responses
- ❌ **Testing SPA patterns** in SSR environment
- ❌ **Direct rune testing** in .ts files (not possible)
- ❌ **Mixing SSR data and store data** in same component

### General Anti-Patterns

- ❌ **Flaky tests** due to timing issues or race conditions
- ❌ **Tests that depend on external services** or network
- ❌ **Overly complex test setup** that obscures the test intent
- ❌ **Tests that test the framework** instead of application logic
- ❌ **Catch-all exception handling** that masks real issues

## Migration and Maintenance

### When to Update Tests

- **API contract changes**: Update integration tests and mocks
- **Schema changes**: Update factory definitions and test data
- **UI component changes**: Update component tests and E2E selectors
- **Business logic changes**: Update service tests and validation tests
- **Infrastructure changes**: Update CI configuration and Docker setup

### Test Maintenance Best Practices

- **Run tests frequently** during development
- **Fix failing tests immediately** - don't let them accumulate
- **Update tests with code changes** in the same commit
- **Refactor tests** when they become hard to understand or maintain
- **Remove obsolete tests** when features are removed
- **Keep test utilities up to date** with current patterns
