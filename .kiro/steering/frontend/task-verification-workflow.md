---

## inclusion: fileMatch fileMatchPattern: [docs/v2_rewrite_implementation_plan/phase-3-web-ui-implementation/\*]

# Task Verification Workflow Patterns

## Overview

This rule documents the systematic approach for verifying and completing Phase 3 Web UI implementation tasks, based on successful task execution patterns.

## Task Execution Process

### 1. Task Selection Strategy

```markdown
# [x] CORRECT - Systematic task selection
1. Read the entire Phase 3 step document before beginning
2. Identify the next group of unchecked tasks in the checklist
3. Select the **first unchecked task** in that group
4. Focus only on that specific task until completion
5. Mark task complete and move to next task

# [FAIL] WRONG - Random task selection
- Jumping between unrelated tasks
- Working on multiple tasks simultaneously
- Skipping prerequisite tasks
- Not following the documented order
```

### 2. Verification Methods

#### Direct Observation (Preferred Method)

```bash
# [x] CORRECT - Use development environment for verification
just docker-dev-up-watch  # Start development environment

# Then use Playwright MCP tools to navigate to http://localhost:5173
# Or manually browse to verify functionality
```

#### Component Testing

```typescript
// [x] CORRECT - Test specific functionality
test('dashboard loads with authenticated data', async ({ page }) => {
    await page.goto('/');
    await page.fill('[data-testid="email"]', 'admin@e2e-test.example');
    await page.fill('[data-testid="password"]', 'admin-password-123');
    await page.click('[data-testid="login-button"]');
    
    // Verify dashboard loads with real data
    await expect(page.locator('[data-testid="campaign-count"]')).toBeVisible();
    await expect(page.locator('[data-testid="agent-count"]')).toBeVisible();
});
```

### 3. Task Completion Criteria

#### For Verification Tasks (No Code Changes)

```markdown
[x] Verification Complete Checklist:
- [ ] Functionality works as specified through direct observation
- [ ] Authentication flows work correctly
- [ ] UI components match design specifications
- [ ] No errors in browser console
- [ ] Mark task complete in checklist
- [ ] Provide brief verification summary
- [ ] **Do NOT run `just ci-check`** (no changes made)
```

#### For Implementation Tasks (Code Changes Required)

```markdown
[x] Implementation Complete Checklist:
- [ ] Make necessary code changes using idiomatic patterns
- [ ] Run formatting: `just format`
- [ ] Add or update tests for correctness
- [ ] Run test suites: `just test` and `just frontend-test`
- [ ] Fix any failing tests
- [ ] Run linters: `just check` and `just frontend-lint`
- [ ] Fix all linter issues
- [ ] Run final validation: `just ci-check`
- [ ] Mark task complete in checklist
- [ ] Provide implementation summary
```

## Development Environment Management

### Docker Environment Control

```bash
# [x] CORRECT - Proper Docker management
just docker-dev-up-watch    # Start development environment
# Work with existing containers
just docker-dev-down        # Clean shutdown when done

# [FAIL] WRONG - Creating conflicting instances
pnpm run dev                # Don't start separate frontend instances
npm start                   # Don't create competing processes
```

### Service Monitoring

```bash
# [x] CORRECT - Monitor existing services
docker compose ps           # Check service status
docker compose logs backend --tail=20    # Check backend logs
docker compose logs frontend --tail=20   # Check frontend logs

# Restart specific services if needed
docker compose restart frontend
docker compose restart backend
```

## Authentication Testing Patterns

### Standard Test Credentials

```typescript
// [x] CORRECT - Use standard E2E test credentials
const TEST_CREDENTIALS = {
    email: 'admin@e2e-test.example',
    password: 'admin-password-123'
};

// Login workflow for verification
await page.fill('[data-testid="email"]', TEST_CREDENTIALS.email);
await page.fill('[data-testid="password"]', TEST_CREDENTIALS.password);
await page.click('[data-testid="login-button"]');
```

### Authentication State Verification

```typescript
// [x] CORRECT - Verify authentication state
// Check for user menu presence
await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();

// Check for project selector
await expect(page.locator('[data-testid="project-selector"]')).toBeVisible();

// Verify authenticated API calls work
await expect(page.locator('[data-testid="dashboard-data"]')).toBeVisible();
```

## Error Handling and Debugging

### Common Issues and Solutions

#### SSE Connection Issues

```typescript
// Problem: "Real-time updates disconnected"
// Solution: Check media type in backend SSE endpoints
// Ensure: media_type="text/event-stream" not "text/plain"

// Debugging steps:
1. Check browser console for SSE errors
2. Verify backend logs show successful connections
3. Check Vite proxy configuration for SSE endpoints
4. Confirm authentication cookies are being sent
```

#### Frontend Build Issues

```bash
# Problem: Vite/SvelteKit module resolution errors
# Solution: Restart frontend container
docker compose restart frontend

# Wait for healthy status
docker compose ps
```

#### Test Failures

```bash
# Problem: Tests failing after code changes
# Solution: Fix tests before marking task complete
just test-backend           # Fix backend tests
just frontend-test          # Fix frontend tests
just ci-check              # Final validation
```

## Code Change Patterns

### SSR Load Function Implementation

```typescript
// [x] CORRECT - Authenticated SSR load function
export const load: PageServerLoad = async ({ cookies }) => {
    // Environment detection for testing
    if (process.env.NODE_ENV === 'test' || process.env.PLAYWRIGHT_TEST) {
        return { campaigns: mockCampaignData };
    }
    
    try {
        const response = await serverApi.get('/api/v1/web/campaigns/', {
            headers: { Cookie: cookies.toString() }
        });
        
        return { campaigns: response.data };
    } catch (error) {
        if (error.response?.status === 401) {
            throw redirect(302, '/login');
        }
        throw error(500, 'Failed to load campaigns');
    }
};
```

### Component Implementation

```svelte
<!-- [x] CORRECT - SvelteKit 5 with Shadcn-Svelte -->
<script lang="ts">
    import type { PageData } from './$types';
    import { Card, CardHeader, CardTitle, CardContent } from '$lib/components/ui/card';
    
    let { data }: { data: PageData } = $props();
    
    // Use SSR data directly for initial render
    let campaigns = $derived(data.campaigns.items);
    let totalCount = $derived(data.campaigns.total_count);
</script>

<div class="dashboard-grid">
    <Card>
        <CardHeader>
            <CardTitle>Active Campaigns</CardTitle>
        </CardHeader>
        <CardContent>
            <span class="metric">{totalCount}</span>
        </CardContent>
    </Card>
</div>
```

## Test Implementation Requirements

### Mock E2E Tests (Fast)

```typescript
// frontend/e2e/dashboard.test.ts
import { test, expect } from '@playwright/test';

test('dashboard displays campaign metrics', async ({ page }) => {
    // Mock API responses for fast testing
    await page.route('/api/v1/web/campaigns/', (route) => {
        route.fulfill({
            json: { items: mockCampaigns, total_count: 5 }
        });
    });
    
    await page.goto('/');
    await expect(page.locator('[data-testid="campaign-count"]')).toHaveText('5');
});
```

### Full E2E Tests (Comprehensive)

```typescript
// frontend/tests/e2e/dashboard.e2e.test.ts
import { test, expect } from '@playwright/test';

test('dashboard loads with real backend data', async ({ page }) => {
    // Use real backend - no mocking
    await page.goto('/');
    
    // Login with real credentials
    await page.fill('[data-testid="email"]', 'admin@e2e-test.example');
    await page.fill('[data-testid="password"]', 'admin-password-123');
    await page.click('[data-testid="login-button"]');
    
    // Verify real data loads
    await expect(page.locator('[data-testid="dashboard"]')).toBeVisible();
});
```

## Task Documentation Patterns

### Verification Summary Format

```markdown
## Task DRM-001b: Complete [x]

Successfully verified that dashboard cards display correct real-time data.

### Issues Found and Fixed:
1. **SSE Media Type Issue**: Fixed backend endpoints to use `text/event-stream`
2. **Connection Status Logic**: Improved frontend connection tracking
3. **Test Assertions**: Updated tests to expect correct media type

### Verification Results:
- [x] Dashboard loads with authenticated API calls
- [x] SSE connections establish successfully  
- [x] Real-time updates work correctly
- [x] All tests pass (596 backend, 149 frontend unit, 176 E2E)
```

### Implementation Summary Format

```markdown
## Task USR-001a: Complete [x]

Implemented user list page with role-based visibility.

### Key Changes:
1. **Created** `frontend/src/routes/users/+page.svelte`
2. **Added** SSR load function with authentication
3. **Implemented** role-based filtering and permissions
4. **Created** comprehensive test coverage

### Validation:
- [x] All linting passes (`just check`)
- [x] All tests pass (`just ci-check`) 
- [x] Authentication flows work correctly
- [x] Role-based access control functional
```

## Best Practices Summary

### Task Execution

1. **Follow systematic task selection** - work through checklist in order
2. **Use direct observation** for verification when possible
3. **Test with real authentication** using standard E2E credentials
4. **Clean up development environment** when switching contexts

### Code Changes

1. **Use idiomatic patterns** - SvelteKit 5, Shadcn-Svelte, Superforms
2. **Implement comprehensive testing** - both mock and full E2E
3. **Fix all issues before completion** - linting, tests, CI checks
4. **Document changes clearly** - what was done and why

### Environment Management

1. **Work with existing Docker containers** - don't create competing instances
2. **Monitor service health** - check logs and status regularly
3. **Restart services when needed** - frontend/backend as required
4. **Clean shutdown** - use `just docker-dev-down` when done

## Anti-Patterns to Avoid

### Task Management

- Working on multiple tasks simultaneously
- Skipping verification steps
- Not following the documented task order
- Running `just ci-check` when no code changes were made

### Development Environment

- Starting multiple frontend instances
- Ignoring Docker service health
- Not monitoring backend logs during development
- Creating conflicting development servers

### Testing and Validation

- Skipping authentication testing
- Not testing with real backend data
- Ignoring failing tests
- Not updating tests when code changes
