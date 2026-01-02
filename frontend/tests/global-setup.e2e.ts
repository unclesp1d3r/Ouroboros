import { execFileSync } from 'node:child_process';
import { chromium, type FullConfig } from '@playwright/test';

/**
 * Playwright Global Setup for E2E Tests
 *
 * This setup runs once before all E2E tests and:
 * 1. Starts the Docker compose stack (backend + database)
 * 2. Waits for services to be healthy
 * 3. Seeds the database with predictable test data
 * 4. Validates that both frontend and backend are accessible
 */
async function globalSetup(config: FullConfig) {
    console.log('🐳 Starting E2E global setup...');

    try {
        // 1. Start Docker compose stack for E2E testing
        console.log('📦 Starting Docker compose stack...');
        execFileSync(
            'docker',
            ['compose', '-f', '../docker-compose.e2e.yml', 'up', '-d', '--build'],
            {
                stdio: 'inherit',
                cwd: process.cwd(),
            }
        );

        // 2. Wait for services to be healthy
        console.log('⏳ Waiting for services to be healthy...');
        await waitForServices();

        // 3. Run database migrations
        console.log('🔄 Running database migrations...');
        await runMigrations();

        // 4. Seed the database with test data
        console.log('🌱 Seeding E2E test data...');
        await seedTestData();

        // 5. Validate frontend accessibility
        console.log('🌐 Validating frontend accessibility...');
        await validateFrontend(config);

        console.log('✅ E2E global setup completed successfully!');
    } catch (error) {
        console.error('❌ E2E global setup failed:', error);

        // Cleanup on failure
        console.log('🧹 Cleaning up Docker containers...');
        try {
            execFileSync('docker', ['compose', '-f', '../docker-compose.e2e.yml', 'down', '-v'], {
                stdio: 'inherit',
                cwd: process.cwd(),
            });
        } catch (cleanupError) {
            console.error('Failed to cleanup:', cleanupError);
        }

        throw error;
    }
}

/**
 * Wait for Docker services to be healthy
 */
async function waitForServices(): Promise<void> {
    const maxWaitTime = 180_000; // 3 minutes to account for Docker build and health checks
    const checkInterval = 5_000; // 5 seconds
    const startTime = Date.now();

    while (Date.now() - startTime < maxWaitTime) {
        try {
            // Check if PostgreSQL is ready
            execFileSync(
                'docker',
                [
                    'compose',
                    '-f',
                    '../docker-compose.e2e.yml',
                    'exec',
                    '-T',
                    'postgres',
                    'pg_isready',
                    '-U',
                    'postgres',
                ],
                {
                    stdio: 'pipe',
                }
            );

            // Check if backend is responding (E2E uses port 8001)
            const backendResponse = await fetch('http://localhost:8001/health');

            // Check if frontend is responding (E2E uses port 3005)
            // Frontend returns 401 for unauthenticated users, which is expected
            const frontendResponse = await fetch('http://localhost:3005');

            console.log(
                `🔍 Service status - Backend: ${backendResponse.status}, Frontend: ${frontendResponse.status}`
            );

            if (backendResponse.ok && (frontendResponse.ok || frontendResponse.status === 401)) {
                console.log('✅ All services are healthy');
                return;
            }
        } catch (error) {
            // Services not ready yet, continue waiting
            const elapsed = Math.round((Date.now() - startTime) / 1000);
            console.log(
                `⏳ Services not ready after ${elapsed}s, waiting... (${error instanceof Error ? error.message : String(error)})`
            );
            await new Promise((resolve) => setTimeout(resolve, checkInterval));
        }
    }

    throw new Error('Services failed to become healthy within timeout period');
}

/**
 * Run database migrations in the backend container
 */
async function runMigrations(): Promise<void> {
    try {
        execFileSync(
            'docker',
            [
                'compose',
                '-f',
                '../docker-compose.e2e.yml',
                'exec',
                '-T',
                'backend',
                'uv',
                'run',
                'alembic',
                'upgrade',
                'head',
            ],
            {
                stdio: 'inherit',
                cwd: process.cwd(),
            }
        );

        console.log('✅ Database migrations completed successfully');
    } catch (error) {
        console.error('❌ Failed to run migrations:', error);
        throw error;
    }
}

/**
 * Seed the database with predictable test data
 */
async function seedTestData(): Promise<void> {
    try {
        // Run the seeding script in the backend container using uv
        // Set E2E_CONTAINER_MODE to indicate running from inside container
        execFileSync(
            'docker',
            [
                'compose',
                '-f',
                '../docker-compose.e2e.yml',
                'exec',
                '-T',
                '-e',
                'E2E_CONTAINER_MODE=true',
                'backend',
                'uv',
                'run',
                'python',
                'scripts/seed_e2e_data.py',
            ],
            {
                stdio: 'inherit',
                cwd: process.cwd(),
            }
        );

        console.log('✅ Test data seeded successfully');
    } catch (error) {
        console.error('❌ Failed to seed test data:', error);
        throw error;
    }
}

/**
 * Validate that the frontend is accessible and loads correctly
 */
async function validateFrontend(config: FullConfig): Promise<void> {
    const browser = await chromium.launch();
    const context = await browser.newContext();
    const page = await context.newPage();

    try {
        // Navigate to the frontend (E2E uses port 3005)
        await page.goto('http://localhost:3005', { waitUntil: 'networkidle' });

        // Check that the page loads and doesn't show error states
        await page.waitForSelector('body', { timeout: 10_000 });

        // Verify we can reach the login page or dashboard
        const title = await page.title();
        if (!title.includes('Ouroboros')) {
            throw new Error(`Unexpected page title: ${title}`);
        }

        console.log('✅ Frontend is accessible and functional');
    } catch (error) {
        console.error('❌ Frontend validation failed:', error);
        throw error;
    } finally {
        await browser.close();
    }
}

export default globalSetup;
