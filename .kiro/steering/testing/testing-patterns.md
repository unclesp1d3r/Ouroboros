---
inclusion: fileMatch
fileMatchPattern:
  - frontend/**/*.test.ts
  - frontend/**/e2e/*.ts
---

# Frontend Testing Patterns and Best Practices

## Overview

This rule documents proven testing patterns for SvelteKit 5 applications with SSR, based on lessons learned from fixing test failures during the SPA to SSR migration.

## Test Environment Setup

### Environment Detection

```typescript
// ✅ CORRECT - Comprehensive test environment detection
if (process.env.NODE_ENV === 'test' ||
    process.env.PLAYWRIGHT_TEST ||
    process.env.CI) {
    return { mockData };
}
```

### Playwright Configuration

```typescript
// playwright.config.ts
export default defineConfig({
    webServer: {
        command: 'pnpm run build && pnpm run preview',
        port: 4173,
        env: {
            PLAYWRIGHT_TEST: 'true' // Critical for SSR test detection
        }
    },
    use: {
        baseURL: 'http://localhost:4173'
    }
});
```

## Unit Testing Patterns

### Store Testing with Runes

```typescript
// ✅ CORRECT - Mock .svelte.ts store files
vi.mock('$lib/stores/campaigns.svelte', () => ({
    campaignsStore: {
        getCampaigns: vi.fn(),
        loading: vi.fn(),
        error: vi.fn()
    }
}));

// ❌ WRONG - Cannot test runes directly in .ts files
// Delete test files that try to test rune functionality directly
```

### Component Testing with SSR Data

```typescript
// ✅ CORRECT - Test components with mock SSR data structure
const mockPageData = {
    campaigns: {
        items: [
            {
                id: 1,
                name: 'Test Campaign',
                status: 'active' as const, // Use exact enum values
                created_at: '2024-01-01T00:00:00Z'
            }
        ],
        total_count: 1,
        page: 1,
        page_size: 10,
        total_pages: 1
    }
};

render(CampaignsList, {
    props: { data: mockPageData }
});
```

### Mock Data Consistency

```typescript
// ✅ CRITICAL - Mock data must match API structure exactly
const mockCampaigns = {
    items: [...], // Exact API response structure
    total_count: 1, // Use snake_case as API returns
    page: 1,
    page_size: 10,
    total_pages: 1
};

// ❌ WRONG - Mismatched structure causes test failures
const mockCampaigns = {
    data: [...], // API doesn't return 'data' wrapper
    totalCount: 1 // API uses snake_case, not camelCase
};
```

## E2E Testing Patterns

### SSR vs SPA Test Expectations

```typescript
// ✅ CORRECT - Test actual SSR-rendered content
test('displays campaigns list', async ({ page }) => {
    await page.goto('/campaigns');

    // Test for actual rendered content, not loading states
    await expect(page.getByText('Test Campaign')).toBeVisible();

    // Don't test for loading spinners in SSR - data is pre-loaded
});

// ❌ WRONG - Testing SPA loading patterns in SSR
test('shows loading state', async ({ page }) => {
    await page.goto('/campaigns');

    // This won't work in SSR - no loading state on initial render
    await expect(page.getByText('Loading...')).toBeVisible();
});
```

### Test Data Management

```typescript
// ✅ CORRECT - Use environment detection for test data
export const load: PageServerLoad = async ({ cookies }) => {
    if (process.env.PLAYWRIGHT_TEST) {
        return {
            campaigns: {
                items: [
                    { id: 1, name: 'E2E Test Campaign', status: 'active' }
                ],
                total_count: 1,
                page: 1,
                page_size: 10,
                total_pages: 1
            }
        };
    }

    // Real API call for production
    return await fetchCampaigns(cookies);
};
```

### Skipped Test Management

```typescript
// ✅ CORRECT - Document why tests are skipped with clear reasoning
test.skip('handles 403 error correctly', async ({ page }) => {
    // Skip reason: In SSR, 403 errors are handled at server level
    // and result in error pages, not client-side error handling.
    // This test would need backend authentication setup to test properly.
});

// ✅ CORRECT - Fix skipped tests when possible
test('shows loading state during form submission', async ({ page }) => {
    // Previously skipped due to DOM update timing issues
    // Fixed by using proper waitFor patterns and async state handling

    await page.goto('/agents');
    await page.click('[data-testid="register-agent-button"]');

    const submitButton = page.getByText('Register Agent');
    await submitButton.click();

    // Use waitFor for async state updates
    await expect(submitButton).toBeDisabled();
    await expect(page.getByText('Registering...')).toBeVisible();
});
```

## Test Command Patterns

### Development Testing

```bash
# ✅ Fast iteration during development
pnpm exec vitest run                    # Unit tests only
pnpm exec playwright test --reporter=line --max-failures=1  # Quick E2E feedback

# ✅ Component-specific testing
pnpm exec vitest run src/lib/components/campaigns/
pnpm exec playwright test e2e/campaigns-list.test.ts
```

### Verification Testing

```bash
# ✅ Frontend-specific verification
just frontend-check        # Unit tests + E2E tests + linting
just frontend-test-e2e     # E2E tests only

# ✅ Full project verification (only at completion)
just ci-check              # Complete CI pipeline
```

## Common Testing Issues and Solutions

### Runtime Errors from Store Exports

```typescript
// ❌ PROBLEM - Direct $derived exports cause test failures
export const campaigns = $derived(campaignState.campaigns);

// ✅ SOLUTION - Use store object pattern
export const campaignsStore = {
    get campaigns() { return campaignState.campaigns; }
};
```

### Test Import Path Issues

```typescript
// ❌ PROBLEM - Importing from wrong path after migration
vi.mock('$lib/stores/campaigns', () => ({ ... }));

// ✅ SOLUTION - Update to .svelte.ts path
vi.mock('$lib/stores/campaigns.svelte', () => ({ ... }));
```

### SSR Page Loading Issues

```typescript
// ❌ PROBLEM - Page not loading due to store function calls
let campaigns = $derived(getCampaigns()); // Function calls in SSR

// ✅ SOLUTION - Use SSR data directly
let campaigns = $derived(data.campaigns.items); // Direct SSR data
```

### Test Timing Issues

```typescript
// ❌ PROBLEM - Tests fail due to async state updates
await fireEvent.click(submitButton);
expect(submitButton).toBeDisabled(); // Might fail due to timing

// ✅ SOLUTION - Use waitFor for async updates
await fireEvent.click(submitButton);
await waitFor(() => {
    expect(submitButton).toBeDisabled();
});
```

## Test Coverage Verification

### Functionality Coverage Checklist

When deleting test files, ensure functionality is tested elsewhere:

- [ ] **Store functionality** tested through component tests
- [ ] **Form submission** tested through E2E tests
- [ ] **Error handling** tested through integration tests
- [ ] **User interactions** tested through E2E user journeys

### Test File Organization

```
frontend/
├── src/lib/components/
│   ├── campaigns/
│   │   ├── CampaignProgress.svelte
│   │   ├── CampaignProgress.spec.ts     # Component unit tests
│   │   └── CampaignMetrics.spec.ts      # Component unit tests
├── e2e/
│   ├── campaigns-list.test.ts           # E2E user journeys
│   └── campaign-progress-metrics.test.ts # E2E integration tests
```

## Performance Testing Patterns

### Test Execution Speed

```typescript
// ✅ FAST - Unit tests with mocks
describe('CampaignProgress', () => {
    // Mock all external dependencies
    vi.mock('$lib/stores/campaigns.svelte');
    // Test component logic in isolation
});

// ✅ COMPREHENSIVE - E2E tests with real data
test('campaign creation workflow', async ({ page }) => {
    // Test complete user journey with SSR
    // Slower but validates full integration
});
```

### Test Environment Optimization

```typescript
// ✅ CORRECT - Separate test commands for different needs
{
  "scripts": {
    "test:unit": "vitest run",                    // Fast feedback
    "test:e2e": "playwright test",               // Full integration
    "test:component": "vitest run src/lib/components/", // Targeted testing
    "test:all": "pnpm test:unit && pnpm test:e2e"      // Complete verification
  }
}
```

## File References

- Test configuration: [playwright.config.ts](mdc:Ouroboros/Ouroboros/frontend/playwright.config.ts)
- Component tests: [CampaignProgress.spec.ts](mdc:Ouroboros/Ouroboros/frontend/src/lib/components/campaigns/CampaignProgress.spec.ts)
- E2E tests: [campaigns-list.test.ts](mdc:Ouroboros/Ouroboros/frontend/e2e/campaigns-list.test.ts)
- Store mocking: [campaigns.svelte.ts](mdc:Ouroboros/Ouroboros/frontend/src/lib/stores/campaigns.svelte.ts)
