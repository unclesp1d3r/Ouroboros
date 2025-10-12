import { execSync } from 'node:child_process';
import type { FullConfig } from '@playwright/test';

/**
 * Playwright Global Teardown for E2E Tests
 *
 * This teardown runs once after all E2E tests complete and:
 * 1. Stops and removes Docker containers
 * 2. Cleans up volumes and networks
 * 3. Ensures clean state for next test run
 */
async function globalTeardown(config: FullConfig) {
    console.log('🧹 Starting E2E global teardown...');

    try {
        // Stop and remove all containers, networks, and volumes
        console.log('📦 Stopping Docker compose stack...');
        execSync('docker compose -f ../docker-compose.e2e.yml down -v --remove-orphans', {
            stdio: 'inherit',
            cwd: process.cwd(),
        });

        // Additional cleanup: remove any dangling images from the E2E build
        console.log('🗑️  Cleaning up dangling Docker images...');
        try {
            execSync('docker image prune -f --filter label=project=ouroboros-e2e', {
                stdio: 'pipe',
            });
        } catch (error) {
            // Non-critical error, continue
            console.log('ℹ️  No dangling images to clean up');
        }

        console.log('✅ E2E global teardown completed successfully!');
    } catch (error) {
        console.error('❌ E2E global teardown failed:', error);

        // Try force cleanup as last resort
        console.log('🚨 Attempting force cleanup...');
        try {
            execSync(
                'docker compose -f ../docker-compose.e2e.yml down -v --remove-orphans --timeout 10',
                {
                    stdio: 'inherit',
                    cwd: process.cwd(),
                }
            );
            console.log('✅ Force cleanup completed');
        } catch (forceError) {
            console.error('❌ Force cleanup also failed:', forceError);
            console.log('⚠️  Manual cleanup may be required');
        }

        // Don't throw error to avoid masking test failures
    }
}

export default globalTeardown;
