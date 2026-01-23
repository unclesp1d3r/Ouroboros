import { defineConfig } from '@playwright/test';

export default defineConfig({
    // Test timeout
    timeout: 30_000, // 30 seconds per test

    // Expect timeout for assertions - increased for animated UI components
    expect: {
        timeout: 10_000, // 10 seconds for expect assertions (matches E2E config)
    },

    use: {
        // Action timeouts - increased for animated components
        actionTimeout: 10_000, // 10 seconds for actions (click, fill, etc.)
        navigationTimeout: 15_000, // 15 seconds for navigation

        video: {
            mode: 'retain-on-failure',
            size: { width: 640, height: 480 },
        },
    },
    webServer: {
        command: 'bun run build && bun run preview',
        port: 4173,
        reuseExistingServer: true,
        env: {
            PLAYWRIGHT_TEST: 'true',
            NODE_ENV: 'test',
        },
    },
    testDir: 'e2e',
    workers: 2,
});
