---
inclusion: fileMatch
fileMatchPattern:

  - frontend/tests/e2e/\*\*/\*
  - frontend/e2e/\*\*/\*.test.ts
  - frontend/e2e/\*\*/\*.e2e.test.ts
  - frontend/playwright.config\*.ts
  - docker-compose.e2e.yml
  - scripts/seed_e2e_data.py
  - frontend/tests/global-setup.e2e.ts
  - frontend/tests/global-teardown.e2e.ts
---

# Ouroboros E2E Testing Patterns

## E2E Testing Infrastructure

### Playwright Configuration

- **Base URL**: `http://localhost:3005` (Docker frontend port)
- **Timeouts**: Extended for Docker startup and animated UI
- **Workers**: 1 (serial execution for database consistency)
- **Global Setup/Teardown**: Docker stack management

### E2E Test Patterns

```typescript
test("dashboard loads campaigns", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator('[data-testid="campaign-list"]')).toBeVisible();
    await expect(page.locator('[data-testid="campaign-count"]')).toContainText(
        /\d+/
    );
});
```

### Timeout Management for Animated UI

```typescript
export const TIMEOUTS = {
    MODAL_ANIMATION: 2000, // Modal open/close animations
    UI_ANIMATION: 1000, // Standard UI transitions
    FORM_SUBMISSION: 3000, // Form processing
    API_RESPONSE: 5000, // API calls in test environment
    PAGE_NAVIGATION: 15000, // Page navigation and SSR
};
```

## Docker Stack Management

### E2E-Specific Configuration

**File**: `frontend/playwright.config.e2e.ts`

**Key Settings**:

```typescript
export default defineConfig({
    testDir: "./tests/e2e",

    // Serial execution for database consistency
    workers: 1,

    // Test timeout
    timeout: 30_000, // 30 seconds per test

    // Expect timeout for assertions - increased for animated UI components
    expect: {
        timeout: 10_000, // 10 seconds for expect assertions
    },

    // Point to Docker frontend service
    use: {
        baseURL: "http://localhost:3005",

        // Action timeouts - increased for animated components
        actionTimeout: 10_000, // 10 seconds for actions (click, fill, etc.)
        navigationTimeout: 15_000, // 15 seconds for navigation

        video: {
            mode: "retain-on-failure",
            size: { width: 640, height: 480 },
        },
    },

    // Global lifecycle management
    globalSetup: "./tests/global-setup.e2e.ts",
    globalTeardown: "./tests/global-teardown.e2e.ts",

    // Comprehensive browser coverage
    projects: [
        { name: "chromium", use: devices["Desktop Chrome"] },
        { name: "firefox", use: devices["Desktop Firefox"] },
        { name: "webkit", use: devices["Desktop Safari"] },
    ],
});
```

### Global Setup Implementation

**File**: `frontend/tests/global-setup.e2e.ts`

**Key Functions**:

1. **Docker Stack Management**: Start compose stack with proper error handling
2. **Service Health Checks**: Wait for PostgreSQL and backend readiness
3. **Data Seeding**: Execute seeding script in backend container
4. **Frontend Validation**: Confirm frontend accessibility
5. **Cleanup on Failure**: Proper Docker cleanup if setup fails

**Implementation Pattern**:

```typescript
export default async function globalSetup() {
    try {
        // Start Docker stack (relative path fixed)
        execSync("docker compose -f ../docker-compose.e2e.yml up -d --build");

        // Wait for services
        await waitForServices();

        // Seed test data
        execSync(
            "docker compose -f ../docker-compose.e2e.yml exec -T backend python scripts/seed_e2e_data.py"
        );

        // Validate frontend
        await validateFrontend();
    } catch (error) {
        // Cleanup on failure
        execSync("docker compose -f ../docker-compose.e2e.yml down -v");
        throw error;
    }
}
```

### Global Teardown Implementation

**File**: `frontend/tests/global-teardown.e2e.ts`

**Key Functions**:

1. **Complete Docker Cleanup**: Remove containers, networks, volumes
2. **Image Cleanup**: Remove dangling Docker images
3. **Graceful Error Handling**: Don't mask test failures with cleanup errors

## Universal Timeout Configuration for Animated UI

Create consistent timeout values in `e2e/test-utils.ts`:

```typescript
/**
 * Standard timeout values for animated UI components
 * These values account for CSS transitions and animations used in Shadcn-Svelte components
 */
export const TIMEOUTS = {
    // Modal and dialog animations
    MODAL_ANIMATION: 2000, // Time for modal to fully open/close

    // General UI animations
    UI_ANIMATION: 1000, // Standard UI transitions (buttons, form elements)

    // Form and input delays
    FORM_SUBMISSION: 3000, // Form submission processing
    INPUT_DEBOUNCE: 500, // Debounced input fields (search, etc.)

    // API and data loading
    API_RESPONSE: 5000, // API responses in test environment
    PAGE_NAVIGATION: 15000, // Page navigation and SSR loading

    // Tab and content switching
    TAB_SWITCH: 1500, // Tab content switching animations
    CONTENT_LOAD: 2000, // Dynamic content loading
};
```

### Helper Functions for Common UI Patterns

```typescript
import { expect, type Page, type Locator } from "@playwright/test";

/**
 * Wait for modal dialog to be fully rendered and interactive
 */
export async function waitForModal(page: Page, modalText: string) {
    await expect(page.getByRole("dialog")).toBeVisible({
        timeout: TIMEOUTS.MODAL_ANIMATION,
    });
    await expect(page.getByText(modalText)).toBeVisible({
        timeout: TIMEOUTS.UI_ANIMATION,
    });
}

/**
 * Wait for form submission states and feedback
 */
export async function waitForFormSubmission(page: Page, submitButton: Locator) {
    await expect(submitButton).toBeDisabled({ timeout: TIMEOUTS.UI_ANIMATION });
    await expect(
        submitButton.or(page.getByText(/submitting|loading/i))
    ).toBeVisible({ timeout: TIMEOUTS.FORM_SUBMISSION });
}

/**
 * Wait for tab to be selected and content to load
 */
export async function waitForTabToBeReady(page: Page, tabName: string) {
    const tab = page.getByRole("tab", { name: new RegExp(tabName, "i") });
    await expect(tab).toBeVisible({ timeout: TIMEOUTS.UI_ANIMATION });
    await expect(tab).toHaveAttribute("aria-selected", "true", {
        timeout: TIMEOUTS.TAB_SWITCH,
    });

    // Wait for tab panel content to be visible
    const tabPanel = page.getByRole("tabpanel");
    await expect(tabPanel).toBeVisible({ timeout: TIMEOUTS.CONTENT_LOAD });
}

/**
 * Wait for navigation to complete with URL validation
 */
export async function waitForNavigation(page: Page, urlPattern: RegExp) {
    await page.waitForURL(urlPattern, { timeout: TIMEOUTS.PAGE_NAVIGATION });
    await expect(page).toHaveURL(urlPattern);
}

/**
 * Create test helpers bound to a specific page
 */
export function createTestHelpers(page: Page) {
    return {
        waitForModal: (modalText: string) => waitForModal(page, modalText),
        waitForFormSubmission: (submitButton: Locator) =>
            waitForFormSubmission(page, submitButton),
        waitForTabToBeReady: (tabName: string) =>
            waitForTabToBeReady(page, tabName),
        waitForNavigation: (urlPattern: RegExp) =>
            waitForNavigation(page, urlPattern),
    };
}
```

## Fixing Flaky Tests with Timeout Patterns

### Navigation Timing Issues

```typescript
// ❌ PROBLEM - Flaky tests due to navigation timing
test("search functionality", async ({ page }) => {
    await searchInput.press("Enter");
    await expect(page).toHaveURL(/.*search=test.*/); // May fail due to timing
});

// ✅ SOLUTION - Wait for navigation completion
test("search functionality", async ({ page }) => {
    const helpers = createTestHelpers(page);

    await searchInput.press("Enter");
    // Wait for navigation to complete before asserting URL
    await helpers.waitForNavigation(/.*search=test.*/);
});
```

### Modal Interaction Timing

```typescript
// ❌ PROBLEM - Modal not fully rendered when test proceeds
test("modal tabs are accessible", async ({ page }) => {
    await detailsBtn.click();
    await expect(page.getByRole("dialog")).toBeVisible(); // May fail
    await expect(page.getByRole("tab", { name: "General" })).toBeVisible(); // May fail
});

// ✅ SOLUTION - Use helper functions with proper waits
test("modal tabs are accessible", async ({ page }) => {
    const helpers = createTestHelpers(page);

    await detailsBtn.click();
    await helpers.waitForModal("Agent Details");
    await helpers.waitForTabToBeReady("General");

    // Modal is now guaranteed to be fully rendered and interactive
    await page.click('[data-testid="general-tab"]');
    await helpers.waitForTabToBeReady("Performance");
});
```

### Form Submission States

```typescript
// ❌ PROBLEM - Form state changes happen too fast to test reliably
test("form shows loading state", async ({ page }) => {
    await submitButton.click();
    await expect(submitButton).toBeDisabled(); // Might miss the state change
});

// ✅ SOLUTION - Use form submission helper
test("form shows loading state", async ({ page }) => {
    const helpers = createTestHelpers(page);

    await submitButton.click();
    await helpers.waitForFormSubmission(submitButton);

    // Form is now guaranteed to be in loading state
    await expect(page.getByText("Processing...")).toBeVisible();
});
```

## SSR vs SPA E2E Testing Patterns

### SSR Test Expectations

```typescript
// ✅ CORRECT - Test actual SSR-rendered content
test("displays campaigns list", async ({ page }) => {
    await page.goto("/campaigns");

    // Test for actual rendered content, not loading states
    await expect(page.getByText("Test Campaign")).toBeVisible();

    // Don't test for loading spinners in SSR - data is pre-loaded
});

// ❌ WRONG - Testing SPA loading patterns in SSR
test("shows loading state", async ({ page }) => {
    await page.goto("/campaigns");

    // This won't work in SSR - no loading state on initial render
    await expect(page.getByText("Loading...")).toBeVisible();
});
```

### Test Data Management

```typescript
// ✅ CORRECT - Use environment detection for test data
export const load: PageServerLoad = async ({ cookies }) => {
    if (process.env.PLAYWRIGHT_TEST) {
        return {
            campaigns: {
                items: [{ id: 1, name: "E2E Test Campaign", status: "active" }],
                total_count: 1,
                page: 1,
                page_size: 10,
                total_pages: 1,
            },
        };
    }

    // Real API call for production
    return await fetchCampaigns(cookies);
};
```

### Skipped Test Management

```typescript
// ✅ CORRECT - Document why tests are skipped with clear reasoning
test.skip("handles 403 error correctly", async ({ page }) => {
    // Skip reason: In SSR, 403 errors are handled at server level
    // and result in error pages, not client-side error handling.
    // This test would need backend authentication setup to test properly.
});

// ✅ CORRECT - Fix skipped tests when possible
test("shows loading state during form submission", async ({ page }) => {
    // Previously skipped due to DOM update timing issues
    // Fixed by using proper waitFor patterns and async state handling

    await page.goto("/agents");
    await page.click('[data-testid="register-agent-button"]');

    const submitButton = page.getByText("Register Agent");
    await submitButton.click();

    // Use waitFor for async state updates
    await expect(submitButton).toBeDisabled();
    await expect(page.getByText("Registering...")).toBeVisible();
});
```

## Test Environment Specific Considerations

### Animation Handling in CI/CD

```typescript
// For CI environments, consider reducing animation durations
// This can be configured in the test setup or via CSS overrides

// playwright.config.ts - CI-specific configuration
export default defineConfig({
    use: {
        // Reduce motion for faster tests in CI
        reducedMotion: process.env.CI ? "reduce" : "no-preference",
    },
});
```

### Debug Mode with Extended Timeouts

```typescript
// For debugging, extend timeouts when running with --debug flag
const isDebugMode = process.argv.includes("--debug");
const debugMultiplier = isDebugMode ? 3 : 1;

export const TIMEOUTS = {
    MODAL_ANIMATION: 2000 * debugMultiplier,
    UI_ANIMATION: 1000 * debugMultiplier,
    // ... other timeouts
};
```

## E2E-Specific Anti-Patterns to Avoid

> [!NOTE]
> For general testing anti-patterns, see [testing-core.md](testing-core.md).

### E2E Testing Anti-Patterns

- Not checking Docker service health before tests
- Testing SPA loading patterns in SSR applications
- Using hardcoded timeouts instead of wait conditions
- Not handling animated UI components properly
- Running E2E tests in parallel (causes database conflicts)
- Not cleaning up Docker resources after test failures

## Test Command Patterns

> [!NOTE]
> For complete test execution commands, see [testing-core.md](testing-core.md).

### Development Testing

```bash
# ✅ Fast iteration during development
pnpm exec playwright test --reporter=line --max-failures=1  # Quick E2E feedback

# ✅ Component-specific testing
pnpm exec playwright test e2e/campaigns-list.test.ts
```

### Verification Testing

```bash
# ✅ E2E-specific verification
just test-e2e              # Full E2E tests with Docker stack

# ✅ Full project verification (only at completion)
just ci-check              # Complete CI pipeline
```

## E2E Test Data Seeding

> [!NOTE]
> For comprehensive test data seeding patterns, factory usage, and cleanup strategies, see [testing-factories.md](testing-factories.md).

### Test Data Creation

**Test Data Created**:

- **Users**: Admin and regular user with known credentials
- **Projects**: "E2E Test Project Alpha" and "E2E Test Project Beta"
- **Campaigns**: Sample campaign with hash list
- **Agents**: Test agent configurations

```text
project_service.create_project(
    ProjectCreate(name="E2E Test Project Alpha"),
    created_by=admin_user.id
)

except Exception as e:
    logger.error(f"Seeding failed: {e}")
    # Graceful cleanup
    await cleanup_test_data()
    raise
```

## Benefits and Best Practices

### Benefits of Universal Timeout Approach

- **Consistency**: All tests use the same timeout values for similar operations
- **Maintainability**: Single place to update timeout values if animation durations change
- **Reliability**: Tests are more robust against timing issues with animated UIs
- **Documentation**: Clear timeout constants make test code more readable and self-documenting
- **Reusability**: Helper functions can be used across all E2E tests without duplication
- **Reduced Flakiness**: Proper wait conditions prevent intermittent test failures in CI/CD
- **Developer Experience**: Clearer error messages when timeouts occur with meaningful context

### Best Practices

1. **Use helper functions** instead of inline timeouts for common patterns
2. **Document timeout reasons** when using custom timeout values
3. **Test timeout values** in CI environment to ensure they work under load
4. **Monitor test execution times** to balance reliability with speed
5. **Update timeout values together** when UI animation speeds change
6. **Use meaningful names** for timeout constants that explain their purpose

## File References

- Configuration: `frontend/playwright.config.e2e.ts`
- Docker compose: `docker-compose.e2e.yml`
- Test utilities: `frontend/e2e/test-utils.ts`
- Global setup: `frontend/tests/global-setup.e2e.ts`
- Data seeding: `scripts/seed_e2e_data.py`
