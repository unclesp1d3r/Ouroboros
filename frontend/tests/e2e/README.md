# E2E Testing Documentation

## Overview

This directory contains full-stack End-to-End (E2E) tests for
Ouroboros. These tests run against a real Docker backend stack and
validate complete user workflows from frontend to database.

## Architecture

### Three-Tier Testing Structure

1. **Layer 1 (Backend)**: Python unit/integration tests with
   testcontainers - `just test-backend`
2. **Layer 2 (Frontend Mocked)**: Vitest + Playwright with API mocks -
   `just test-frontend`
3. **Layer 3 (Full E2E)**: Playwright E2E against real Docker backend -
   `just test-e2e`

### E2E Infrastructure

- **Docker Stack**: PostgreSQL, MinIO, Redis, FastAPI backend, SvelteKit
  frontend
- **Data Seeding**: Predictable test data created via
  `scripts/seed_e2e_data.py`
- **Global Setup/Teardown**: Automatic Docker lifecycle management
- **Isolated Environment**: Tests run against separate E2E database and
  storage

## Running E2E Tests

### Quick Start

```bash
# Run all E2E tests
just test-e2e

# Run specific test file
cd frontend && pnpm exec playwright test --config=playwright.config.e2e.ts auth.e2e.test.ts

# Run with UI (headed mode)
cd frontend && pnpm exec playwright test --config=playwright.config.e2e.ts --headed

# Run with debug mode
cd frontend && pnpm exec playwright test --config=playwright.config.e2e.ts --debug
```

### Manual Setup (if needed)

```bash
# Start E2E Docker stack manually
just docker-e2e-up

# Seed E2E test data manually
uv run python scripts/seed_e2e_data.py

# Stop E2E Docker stack
just docker-e2e-down
```

## Test Data

### Seeded Users

- **Admin**: `admin@e2e-test.example` / `admin-password-123`
- **Regular User**: `user@e2e-test.example` / `user-password-123`

### Seeded Projects

- **E2E Test Project Alpha**: Primary test project with campaigns
- **E2E Test Project Beta**: Secondary project for multi-project
  scenarios

### Seeded Campaigns

- **E2E Test Campaign**: Campaign in Project Alpha with hash list

### Seeded Agents

- **E2E Test Agent**: Test agent for task execution testing

## Test Files

### `auth.e2e.test.ts`

- User authentication workflows
- Session management and persistence
- Access control and redirection
- Error handling for invalid credentials
- Multi-user concurrent sessions

### `projects.e2e.test.ts`

- Project listing and navigation
- Campaign creation and management
- Project switching and context
- Data visibility and access control

## Configuration

### Playwright Configuration (`playwright.config.e2e.ts`)

- **Execution**: Serial (workers: 1) to avoid database conflicts
- **Browsers**: Chrome, Firefox, Safari, Mobile Chrome/Safari
- **Timeouts**: 30s test timeout, 60s global timeout
- **Base URL**: `http://localhost:3005` (E2E frontend)
- **Global Setup**: `tests/global-setup.e2e.ts`
- **Global Teardown**: `tests/global-teardown.e2e.ts`

### Docker Configuration (`docker-compose.e2e.yml`)

- **PostgreSQL**: Port 5444, database `cipherswarm_e2e`
- **MinIO**: Port 9002, admin console 9003
- **Redis**: Port 6381
- **Backend**: Port 8001
- **Frontend**: Port 3005

## Best Practices

### Test Design

- Use seeded data whenever possible for consistency
- Include proper cleanup between tests
- Test complete user workflows, not just UI interactions
- Validate both success and error scenarios
- Use descriptive test names and good documentation

### Data-testid Usage

```typescript
// Use data-testid for reliable element selection
await page.click('[data-testid="projects-nav"]');
await expect(page.locator('[data-testid="project-card"]')).toHaveCount(2);
```

### Error Handling

```typescript
// Always include proper error context
await expect(page.locator('[data-testid="error-message"]')).toContainText('Expected error message');
```

### Async/Await Patterns

```typescript
// Proper waiting for network requests and navigation
await page.click('button[type="submit"]');
await expect(page).toHaveURL(/\/dashboard/);
```

## Debugging

### Common Issues

1. **Docker stack not starting**

   ```bash
   # Check service health
   docker compose -f docker-compose.e2e.yml ps

   # Check logs
   docker compose -f docker-compose.e2e.yml logs
   ```

2. **Database connection issues**

   ```bash
   # Verify PostgreSQL is ready
   docker compose -f docker-compose.e2e.yml exec postgres pg_isready
   ```

3. **Seeding fails**

   ```bash
   # Run seeding manually to see errors
   E2E_DATABASE_URL="postgresql://ouroboros:ouroboros@localhost:5444/cipherswarm_e2e" \
       uv run python scripts/seed_e2e_data.py
   ```

### Debug Tools

```bash
# Visual debugging
cd frontend && pnpm exec playwright test --config=playwright.config.e2e.ts --debug --headed

# Generate test report
cd frontend && pnpm exec playwright show-report

# Record test execution
cd frontend && pnpm exec playwright test --config=playwright.config.e2e.ts --record-video=on
```

## Adding New Tests

### 1. Create Test File

```typescript
// tests/e2e/feature.e2e.test.ts
import { test, expect, type Page } from '@playwright/test';

// Use seeded test data
const TEST_DATA = {
    // Reference data from scripts/seed_e2e_data.py
};

test.describe('Feature Name', () => {
    test.beforeEach(async ({ page }) => {
        // Setup: login, navigate, etc.
    });

    test('should perform user workflow', async ({ page }) => {
        // Test implementation using data-testid selectors
    });
});
```

### 2. Update Seeding Script (if needed)

```python
# scripts/seed_e2e_data.py
# Add new test data following existing patterns
```

### 3. Document Test Coverage

- Update this README with new test descriptions
- Include any new seeded data in documentation
- Add debugging notes for new features

## Integration with CI/CD

The E2E tests are integrated into the CI pipeline:

- **Local**: `just ci-check` runs all three test layers
- **GitHub Actions**: E2E tests run on PRs and main branch
- **Docker**: Uses same infrastructure as production
- **Reporting**: Test results and artifacts uploaded to CI

## Performance Considerations

- **Serial Execution**: Tests run one at a time to avoid database
  conflicts
- **Docker Overhead**: E2E tests are slower than unit/integration tests
- **Resource Usage**: Requires sufficient Docker resources (4GB+ RAM
  recommended)
- **Cleanup**: Automatic cleanup prevents resource leaks between runs

## Future Enhancements

- **Parallel Execution**: Database isolation for parallel test execution
- **Visual Regression**: Screenshot comparison for UI consistency
- **Performance Testing**: Load testing integration with E2E
  infrastructure
- **Cross-Browser**: Extended browser coverage for compatibility testing
