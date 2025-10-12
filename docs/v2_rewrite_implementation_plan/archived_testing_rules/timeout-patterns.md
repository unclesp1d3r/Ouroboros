# Universal Timeout Patterns for Animated UI Testing

## Overview

This rule documents universal timeout configuration and helper patterns for E2E testing of animated UI components, specifically for SvelteKit applications using Shadcn-Svelte components with CSS transitions and animations.

## Universal Timeout Configuration

### Playwright Configuration

Configure universal timeouts in `playwright.config.ts` to handle animated UI components consistently:

```typescript
// ✅ CORRECT - Universal timeout configuration for animated UIs
import { defineConfig } from '@playwright/test';

export default defineConfig({
    // Test timeout
    timeout: 30_000, // 30 seconds per test

    // Expect timeout for assertions - increased for animated UI components
    expect: {
        timeout: 10_000 // 10 seconds for expect assertions
    },

    use: {
        // Action timeouts - increased for animated components
        actionTimeout: 10_000, // 10 seconds for actions (click, fill, etc.)
        navigationTimeout: 15_000, // 15 seconds for navigation

        video: {
            mode: 'retain-on-failure',
            size: { width: 640, height: 480 }
        }
    },

    webServer: {
        command: 'pnpm run build && pnpm run preview',
        port: 4173,
        env: {
            PLAYWRIGHT_TEST: 'true' // Critical for SSR test detection
        }
    }
});
```

## Test Utilities and Helper Functions

### Standardized Timeout Constants

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
    CONTENT_LOAD: 2000 // Dynamic content loading
};
```

### Helper Functions for Common UI Patterns

```typescript
import { expect, type Page, type Locator } from '@playwright/test';

/**
 * Wait for modal dialog to be fully rendered and interactive
 */
export async function waitForModal(page: Page, modalText: string) {
    await expect(page.getByRole('dialog')).toBeVisible({ timeout: TIMEOUTS.MODAL_ANIMATION });
    await expect(page.getByText(modalText)).toBeVisible({ timeout: TIMEOUTS.UI_ANIMATION });
}

/**
 * Wait for form submission states and feedback
 */
export async function waitForFormSubmission(page: Page, submitButton: Locator) {
    await expect(submitButton).toBeDisabled({ timeout: TIMEOUTS.UI_ANIMATION });
    await expect(submitButton.or(page.getByText(/submitting|loading/i)))
        .toBeVisible({ timeout: TIMEOUTS.FORM_SUBMISSION });
}

/**
 * Wait for tab to be selected and content to load
 */
export async function waitForTabToBeReady(page: Page, tabName: string) {
    const tab = page.getByRole('tab', { name: new RegExp(tabName, 'i') });
    await expect(tab).toBeVisible({ timeout: TIMEOUTS.UI_ANIMATION });
    await expect(tab).toHaveAttribute('aria-selected', 'true', { timeout: TIMEOUTS.TAB_SWITCH });

    // Wait for tab panel content to be visible
    const tabPanel = page.getByRole('tabpanel');
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
        waitForFormSubmission: (submitButton: Locator) => waitForFormSubmission(page, submitButton),
        waitForTabToBeReady: (tabName: string) => waitForTabToBeReady(page, tabName),
        waitForNavigation: (urlPattern: RegExp) => waitForNavigation(page, urlPattern)
    };
}
```

## Fixing Flaky Tests with Timeout Patterns

### Navigation Timing Issues

```typescript
// ❌ PROBLEM - Flaky tests due to navigation timing
test('search functionality', async ({ page }) => {
    await searchInput.press('Enter');
    await expect(page).toHaveURL(/.*search=test.*/); // May fail due to timing
});

// ✅ SOLUTION - Wait for navigation completion
test('search functionality', async ({ page }) => {
    const helpers = createTestHelpers(page);

    await searchInput.press('Enter');
    // Wait for navigation to complete before asserting URL
    await helpers.waitForNavigation(/.*search=test.*/);
});
```

### Modal Interaction Timing

```typescript
// ❌ PROBLEM - Modal not fully rendered when test proceeds
test('modal tabs are accessible', async ({ page }) => {
    await detailsBtn.click();
    await expect(page.getByRole('dialog')).toBeVisible(); // May fail
    await expect(page.getByRole('tab', { name: 'General' })).toBeVisible(); // May fail
});

// ✅ SOLUTION - Use helper functions with proper waits
test('modal tabs are accessible', async ({ page }) => {
    const helpers = createTestHelpers(page);

    await detailsBtn.click();
    await helpers.waitForModal('Agent Details');
    await helpers.waitForTabToBeReady('General');

    // Modal is now guaranteed to be fully rendered and interactive
    await page.click('[data-testid="general-tab"]');
    await helpers.waitForTabToBeReady('Performance');
});
```

### Form Submission States

```typescript
// ❌ PROBLEM - Form state changes happen too fast to test reliably
test('form shows loading state', async ({ page }) => {
    await submitButton.click();
    await expect(submitButton).toBeDisabled(); // Might miss the state change
});

// ✅ SOLUTION - Use form submission helper
test('form shows loading state', async ({ page }) => {
    const helpers = createTestHelpers(page);

    await submitButton.click();
    await helpers.waitForFormSubmission(submitButton);

    // Form is now guaranteed to be in loading state
    await expect(page.getByText('Processing...')).toBeVisible();
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
        reducedMotion: process.env.CI ? 'reduce' : 'no-preference'
    }
});
```

### Debug Mode with Extended Timeouts

```typescript
// For debugging, extend timeouts when running with --debug flag
const isDebugMode = process.argv.includes('--debug');
const debugMultiplier = isDebugMode ? 3 : 1;

export const TIMEOUTS = {
    MODAL_ANIMATION: 2000 * debugMultiplier,
    UI_ANIMATION: 1000 * debugMultiplier,
    // ... other timeouts
};
```

## Benefits of Universal Timeout Approach

- **Consistency**: All tests use the same timeout values for similar operations
- **Maintainability**: Single place to update timeout values if animation durations change
- **Reliability**: Tests are more robust against timing issues with animated UIs
- **Documentation**: Clear timeout constants make test code more readable and self-documenting
- **Reusability**: Helper functions can be used across all E2E tests without duplication
- **Reduced Flakiness**: Proper wait conditions prevent intermittent test failures in CI/CD
- **Developer Experience**: Clearer error messages when timeouts occur with meaningful context

## Best Practices

1. **Use helper functions** instead of inline timeouts for common patterns
2. **Document timeout reasons** when using custom timeout values
3. **Test timeout values** in CI environment to ensure they work under load
4. **Monitor test execution times** to balance reliability with speed
5. **Update timeout values together** when UI animation speeds change
6. **Use meaningful names** for timeout constants that explain their purpose

## File References

- Configuration: [playwright.config.ts](mdc:Ouroboros/Ouroboros/Ouroboros/frontend/playwright.config.ts)
- Test utilities: [test-utils.ts](mdc:Ouroboros/Ouroboros/Ouroboros/frontend/e2e/test-utils.ts)
- Example usage: [agent-list-mock-fallback.e2e.test.ts](mdc:Ouroboros/Ouroboros/Ouroboros/frontend/e2e/agent-list-mock-fallback.e2e.test.ts)
