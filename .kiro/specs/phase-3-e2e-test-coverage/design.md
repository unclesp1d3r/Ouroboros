# Design Document

## Overview

This design document outlines the comprehensive technical approach for implementing missing End-to-End (E2E) test coverage for Ouroboros Phase 3. The design addresses critical gaps identified in the current testing infrastructure while establishing the authentication foundation required for comprehensive E2E testing.

The implementation follows Ouroboros's established three-tier testing architecture:

- **Layer 1**: Backend tests (Python + testcontainers) - ✅ Complete
- **Layer 2**: Frontend mocked tests (Playwright + mocked APIs) - 🔄 Partially complete
- **Layer 3**: Full E2E tests (Playwright + real Docker backend) - 🔄 Infrastructure complete, authentication pending

This design focuses on completing Layers 2 and 3 while implementing the SSR authentication foundation that enables comprehensive workflow testing.

## Architecture

### Test Architecture Overview

The design implements a dual-track testing approach that provides both fast feedback loops for development and comprehensive integration validation for releases.

**Test Environment Structure:**

```
frontend/
├── e2e/                    # Mocked E2E tests (fast, MSW mocked APIs)
├── tests/e2e/             # Full E2E tests (slower, real backend)
├── tests/test-utils.ts    # Shared utilities and helpers
└── playwright.config.ts   # Unified Playwright configuration
```

**Test Execution Commands:**

- `just test-frontend` - Runs mocked E2E tests for development feedback
- `just test-e2e` - Runs full E2E tests with Docker backend for integration validation
- `just ci-check` - Runs complete test suite including all tiers

### Authentication Integration Architecture

**SSR Session-Based Authentication:**

The design implements session-based authentication specifically for E2E testing, complementing the existing JWT-based API authentication.

```typescript
// Backend: Session authentication endpoint for E2E testing
// app/api/v1/endpoints/web/auth.py
@router.post("/session/login")
async def session_login(
    credentials: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db)
) -> LoginResponse:
    user = await authenticate_user_service(db, credentials.username, credentials.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Create session token
    session_token = create_session_token(user.id)

    # Set secure HTTP-only cookie
    response.set_cookie(
        key="sessionid",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=60 * 60 * 24 * 7  # 7 days
    )

    return LoginResponse(user=user, projects=user.projects)

// Frontend: SvelteKit load function with session authentication
// routes/+layout.server.ts
export const load: LayoutServerLoad = async ({ cookies, url }) => {
    const sessionId = cookies.get('sessionid');
    if (!sessionId) {
        if (url.pathname !== '/login') {
            throw redirect(302, `/login?redirect=${url.pathname}`);
        }
        return { user: null, project: null };
    }

    try {
        const session = await validateSession(sessionId);
        return {
            user: session.user,
            project: session.project,
            projects: session.availableProjects
        };
    } catch (error) {
        cookies.delete('sessionid');
        throw redirect(302, '/login');
    }
};
```

**Test Authentication Helpers:**

```typescript
// tests/test-utils.ts
export class AuthenticationHelper {
    constructor(private page: Page) {}

    async loginAs(role: 'admin' | 'project_admin' | 'user', projectId?: string) {
        const credentials = this.getTestCredentials(role);

        await this.page.goto('/login');
        await this.page.fill('[data-testid="username"]', credentials.username);
        await this.page.fill('[data-testid="password"]', credentials.password);
        await this.page.click('[data-testid="login-button"]');

        // Handle project selection if multiple projects
        if (projectId) {
            await this.selectProject(projectId);
        }

        await this.page.waitForURL('/dashboard');
        return credentials;
    }

    async selectProject(projectId: string) {
        // Handle project selection modal or dropdown
        const projectSelector = this.page.locator('[data-testid="project-selector"]');
        if (await projectSelector.isVisible()) {
            await projectSelector.click();
            await this.page.click(`[data-testid="project-option-${projectId}"]`);
        }
    }

    async logout() {
        await this.page.click('[data-testid="user-menu"]');
        await this.page.click('[data-testid="logout-button"]');
        await this.page.waitForURL('/login');
    }

    private getTestCredentials(role: string) {
        const credentials = {
            admin: { username: 'admin', password: 'admin123' },
            project_admin: { username: 'project_admin', password: 'project123' },
            user: { username: 'user', password: 'user123' }
        };
        return credentials[role];
    }
}
```

### Test Data Management Architecture

**Predictable Test Environment:**

```typescript
// Backend: Test data seeding service
// app/core/services/test_data_service.py
class TestDataService:
    async def seed_test_environment(self, db: AsyncSession) -> TestEnvironment:
        # Create test users with known credentials
        admin_user = await self.create_test_user(
            username="admin",
            password="admin123",
            role="admin",
            projects=["project1", "project2"]
        )

        project_admin = await self.create_test_user(
            username="project_admin",
            password="project123",
            role="project_admin",
            projects=["project1"]
        )

        regular_user = await self.create_test_user(
            username="user",
            password="user123",
            role="user",
            projects=["project1"]
        )

        # Create test projects with predictable data
        project1 = await self.create_test_project(
            name="Test Project 1",
            campaigns=3,
            resources=5,
            agents=2
        )

        return TestEnvironment(
            users=[admin_user, project_admin, regular_user],
            projects=[project1],
            campaigns=project1.campaigns,
            resources=project1.resources,
            agents=project1.agents
        )

// Frontend: Test environment utilities
// tests/fixtures/test-environment.ts
export interface TestEnvironment {
    users: TestUser[];
    projects: TestProject[];
    campaigns: TestCampaign[];
    resources: TestResource[];
    agents: TestAgent[];
}

export class TestEnvironmentManager {
    async setupEnvironment(): Promise<TestEnvironment> {
        // Seed backend with predictable test data
        const response = await fetch('/api/v1/test/seed-environment', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        return response.json();
    }

    async cleanupEnvironment(): Promise<void> {
        await fetch('/api/v1/test/cleanup-environment', { method: 'DELETE' });
    }
}
```

## Components and Interfaces

### Test Component Architecture

**Page Object Model Implementation:**

```typescript
// tests/page-objects/DashboardPage.ts
export class DashboardPage {
    constructor(private page: Page) {}

    // Locators
    get statusCards() { return this.page.locator('[data-testid="status-card"]'); }
    get campaignRows() { return this.page.locator('[data-testid="campaign-row"]'); }
    get agentStatusSheet() { return this.page.locator('[data-testid="agent-status-sheet"]'); }
    get toastNotifications() { return this.page.locator('[data-testid="toast"]'); }

    // Actions
    async waitForLoad() {
        await this.page.waitForLoadState('networkidle');
        await expect(this.statusCards.first()).toBeVisible();
    }

    async openAgentStatusSheet() {
        await this.statusCards.filter({ hasText: 'Active Agents' }).click();
        await expect(this.agentStatusSheet).toBeVisible();
    }

    async expandCampaignRow(campaignId: string) {
        const row = this.campaignRows.filter({ hasText: campaignId });
        await row.locator('[data-testid="expand-button"]').click();
        await expect(row.locator('[data-testid="attack-list"]')).toBeVisible();
    }

    // Assertions
    async assertStatusCardValue(cardName: string, expectedValue: string) {
        const card = this.statusCards.filter({ hasText: cardName });
        await expect(card.locator('[data-testid="card-value"]')).toContainText(expectedValue);
    }

    async assertToastNotification(message: string, type: 'success' | 'error' | 'info') {
        const toast = this.toastNotifications.filter({ hasText: message });
        await expect(toast).toHaveClass(new RegExp(`toast-${type}`));
    }
}

// tests/page-objects/CampaignWizardPage.ts
export class CampaignWizardPage {
    constructor(private page: Page) {}

    async createCampaign(config: CampaignConfig) {
        // Step 1: Select hashlist
        await this.selectHashlist(config.hashlistId);
        await this.clickNext();

        // Step 2: Campaign metadata
        await this.fillCampaignDetails(config.name, config.description);
        await this.clickNext();

        // Step 3: Configure attacks
        for (const attack of config.attacks) {
            await this.addAttack(attack);
        }
        await this.clickNext();

        // Step 4: Review and launch
        await this.reviewAndLaunch();
    }

    private async selectHashlist(hashlistId: string) {
        if (hashlistId === 'upload') {
            await this.uploadHashlist();
        } else {
            await this.page.selectOption('[data-testid="hashlist-select"]', hashlistId);
        }
    }

    private async addAttack(attack: AttackConfig) {
        await this.page.click('[data-testid="add-attack-button"]');

        const modal = this.page.locator('[data-testid="attack-editor-modal"]');
        await modal.selectOption('[data-testid="attack-type"]', attack.type);

        // Configure attack parameters based on type
        switch (attack.type) {
            case 'dictionary':
                await this.configureDictionaryAttack(modal, attack);
                break;
            case 'mask':
                await this.configureMaskAttack(modal, attack);
                break;
            case 'brute_force':
                await this.configureBruteForceAttack(modal, attack);
                break;
        }

        await modal.locator('[data-testid="save-attack"]').click();
        await expect(modal).not.toBeVisible();
    }
}
```

### Form Testing Architecture

**Form Validation Test Utilities:**

```typescript
// tests/utilities/form-testing.ts
export interface ValidationRule {
    field: string;
    invalidValue: string;
    expectedError: string;
    validValue?: string;
}

export class FormTester {
    constructor(private page: Page) {}

    async testFormValidation(
        formSelector: string,
        validationRules: ValidationRule[]
    ) {
        for (const rule of validationRules) {
            // Test invalid value
            await this.page.fill(`${formSelector} [name="${rule.field}"]`, rule.invalidValue);
            await this.page.blur(`${formSelector} [name="${rule.field}"]`);

            const errorElement = this.page.locator(`[data-testid="${rule.field}-error"]`);
            await expect(errorElement).toContainText(rule.expectedError);

            // Test valid value if provided
            if (rule.validValue) {
                await this.page.fill(`${formSelector} [name="${rule.field}"]`, rule.validValue);
                await this.page.blur(`${formSelector} [name="${rule.field}"]`);
                await expect(errorElement).not.toBeVisible();
            }
        }
    }

    async testFormSubmission(
        formSelector: string,
        formData: Record<string, string>,
        expectedResult: 'success' | 'error',
        expectedMessage?: string
    ) {
        // Fill form
        for (const [field, value] of Object.entries(formData)) {
            await this.page.fill(`${formSelector} [name="${field}"]`, value);
        }

        // Submit form
        await this.page.click(`${formSelector} [type="submit"]`);

        // Verify result
        if (expectedResult === 'success') {
            await expect(this.page.locator('[data-testid="success-message"]')).toBeVisible();
            if (expectedMessage) {
                await expect(this.page.locator('[data-testid="success-message"]')).toContainText(expectedMessage);
            }
        } else {
            await expect(this.page.locator('[data-testid="error-message"]')).toBeVisible();
            if (expectedMessage) {
                await expect(this.page.locator('[data-testid="error-message"]')).toContainText(expectedMessage);
            }
        }
    }

    async testProgressiveEnhancement(formSelector: string, formData: Record<string, string>) {
        // Disable JavaScript
        await this.page.context().addInitScript(() => {
            Object.defineProperty(window, 'navigator', {
                value: { ...window.navigator, javaEnabled: () => false }
            });
        });

        // Test form still works
        await this.testFormSubmission(formSelector, formData, 'success');
    }
}
```

### Real-Time Testing Architecture

**SSE Testing Utilities:**

```typescript
// tests/utilities/sse-testing.ts
export class SSETester {
    private eventSource: EventSource | null = null;
    private receivedEvents: SSEEvent[] = [];

    constructor(private page: Page) {}

    async startListening(endpoint: string) {
        this.eventSource = await this.page.evaluateHandle((url) => {
            const es = new EventSource(url);
            (window as any).testEventSource = es;
            return es;
        }, endpoint);

        // Capture events
        await this.page.addInitScript(() => {
            (window as any).testEvents = [];
            if ((window as any).testEventSource) {
                (window as any).testEventSource.onmessage = (event: MessageEvent) => {
                    (window as any).testEvents.push({
                        type: event.type,
                        data: JSON.parse(event.data),
                        timestamp: new Date()
                    });
                };
            }
        });
    }

    async waitForEvent(eventType: string, timeout: number = 5000): Promise<SSEEvent> {
        return this.page.waitForFunction(
            (type) => {
                const events = (window as any).testEvents || [];
                return events.find((e: any) => e.data.type === type);
            },
            eventType,
            { timeout }
        );
    }

    async simulateEvent(eventType: string, eventData: any) {
        await this.page.evaluate(
            ({ type, data }) => {
                const event = new MessageEvent('message', {
                    data: JSON.stringify({ type, data })
                });
                if ((window as any).testEventSource) {
                    (window as any).testEventSource.dispatchEvent(event);
                }
            },
            { type: eventType, data: eventData }
        );
    }

    async stopListening() {
        if (this.eventSource) {
            await this.page.evaluate(() => {
                if ((window as any).testEventSource) {
                    (window as any).testEventSource.close();
                }
            });
        }
    }
}
```

## Data Models

### Test Data Models

**Test Environment Data Structures:**

```typescript
// tests/types/test-data.ts
export interface TestUser {
    id: string;
    username: string;
    password: string;
    role: 'admin' | 'project_admin' | 'user';
    email: string;
    projects: string[];
    isActive: boolean;
}

export interface TestProject {
    id: string;
    name: string;
    description: string;
    userRole: string;
    campaigns: TestCampaign[];
    resources: TestResource[];
    agents: TestAgent[];
}

export interface TestCampaign {
    id: string;
    name: string;
    status: 'draft' | 'running' | 'paused' | 'completed';
    progress: number;
    attacks: TestAttack[];
    hashlistId: string;
    projectId: string;
}

export interface TestAttack {
    id: string;
    type: 'dictionary' | 'mask' | 'brute_force' | 'hybrid';
    name: string;
    parameters: Record<string, any>;
    resources: string[];
    keyspace: number;
    complexity: number;
    status: 'pending' | 'running' | 'completed' | 'failed';
}

export interface TestResource {
    id: string;
    name: string;
    type: 'wordlist' | 'rules' | 'masks' | 'charset';
    size: number;
    lineCount: number;
    sensitive: boolean;
    projectId: string;
    uploadedBy: string;
}

export interface TestAgent {
    id: string;
    name: string;
    hostname: string;
    status: 'online' | 'offline' | 'error';
    lastSeen: Date;
    currentTask?: string;
    performance: {
        hashRate: number;
        temperature: number;
        utilization: number;
    };
    devices: TestDevice[];
}

export interface TestDevice {
    id: string;
    name: string;
    type: 'cpu' | 'gpu';
    enabled: boolean;
    temperature: number;
    utilization: number;
}
```

**Test Configuration Models:**

```typescript
// tests/types/test-config.ts
export interface TestConfig {
    environment: 'mocked' | 'integration';
    baseUrl: string;
    timeout: number;
    retries: number;
    parallel: boolean;
    headless: boolean;
    browsers: ('chromium' | 'firefox' | 'webkit')[];
    viewports: ViewportConfig[];
    authentication: AuthConfig;
    testData: TestDataConfig;
}

export interface ViewportConfig {
    name: string;
    width: number;
    height: number;
    deviceScaleFactor?: number;
    isMobile?: boolean;
}

export interface AuthConfig {
    sessionTimeout: number;
    testUsers: TestUser[];
    defaultProject: string;
}

export interface TestDataConfig {
    seedOnStartup: boolean;
    cleanupOnTeardown: boolean;
    dataDirectory: string;
    fixtures: string[];
}
```

## Error Handling

### Test Error Handling Architecture

**Error Recovery Patterns:**

```typescript
// tests/utilities/error-handling.ts
export class TestErrorHandler {
    constructor(private page: Page) {}

    async handleAuthenticationError() {
        // Check if redirected to login
        if (this.page.url().includes('/login')) {
            console.log('Authentication expired, re-authenticating...');
            const auth = new AuthenticationHelper(this.page);
            await auth.loginAs('admin');
            return true;
        }
        return false;
    }

    async handleNetworkError(error: Error) {
        if (error.message.includes('net::ERR_CONNECTION_REFUSED')) {
            console.log('Backend connection failed, waiting for recovery...');
            await this.waitForBackendRecovery();
            return true;
        }
        return false;
    }

    async handleTimeoutError(operation: string) {
        console.log(`Operation ${operation} timed out, retrying...`);
        await this.page.reload();
        await this.page.waitForLoadState('networkidle');
        return true;
    }

    private async waitForBackendRecovery(maxWait: number = 30000) {
        const startTime = Date.now();
        while (Date.now() - startTime < maxWait) {
            try {
                const response = await fetch('/api/v1/health');
                if (response.ok) {
                    return;
                }
            } catch {
                // Continue waiting
            }
            await new Promise(resolve => setTimeout(resolve, 1000));
        }
        throw new Error('Backend failed to recover within timeout');
    }
}

// Test retry mechanism
export async function withRetry<T>(
    operation: () => Promise<T>,
    maxRetries: number = 3,
    delay: number = 1000
): Promise<T> {
    let lastError: Error;

    for (let attempt = 1; attempt <= maxRetries; attempt++) {
        try {
            return await operation();
        } catch (error) {
            lastError = error as Error;
            console.log(`Attempt ${attempt} failed: ${error.message}`);

            if (attempt < maxRetries) {
                await new Promise(resolve => setTimeout(resolve, delay * attempt));
            }
        }
    }

    throw lastError!;
}
```

**Test Isolation and Cleanup:**

```typescript
// tests/fixtures/test-isolation.ts
export class TestIsolation {
    private testId: string;
    private createdResources: string[] = [];

    constructor() {
        this.testId = `test_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    async setup() {
        // Create isolated test environment
        await this.createTestNamespace();
        await this.seedTestData();
    }

    async cleanup() {
        // Clean up all created resources
        for (const resourceId of this.createdResources) {
            await this.deleteResource(resourceId);
        }

        // Clear browser state
        await this.clearBrowserState();
    }

    trackResource(resourceId: string) {
        this.createdResources.push(resourceId);
    }

    private async createTestNamespace() {
        // Create isolated project for this test
        const response = await fetch('/api/v1/test/create-namespace', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ testId: this.testId })
        });

        if (!response.ok) {
            throw new Error('Failed to create test namespace');
        }
    }

    private async clearBrowserState() {
        // Clear cookies, localStorage, sessionStorage
        await this.page.context().clearCookies();
        await this.page.evaluate(() => {
            localStorage.clear();
            sessionStorage.clear();
        });
    }
}
```

## Testing Strategy

### Test Execution Architecture

**Test Suite Organization:**

```typescript
// playwright.config.ts
export default defineConfig({
    testDir: './tests',
    fullyParallel: true,
    forbidOnly: !!process.env.CI,
    retries: process.env.CI ? 2 : 0,
    workers: process.env.CI ? 1 : undefined,
    reporter: [
        ['html'],
        ['junit', { outputFile: 'test-results/junit.xml' }],
        ['json', { outputFile: 'test-results/results.json' }]
    ],
    use: {
        baseURL: process.env.BASE_URL || 'http://localhost:5173',
        trace: 'on-first-retry',
        screenshot: 'only-on-failure',
        video: 'retain-on-failure'
    },
    projects: [
        // Mocked tests (fast feedback)
        {
            name: 'mocked-chromium',
            testDir: './e2e',
            use: { ...devices['Desktop Chrome'] },
            dependencies: ['setup-mocked']
        },

        // Full E2E tests (comprehensive validation)
        {
            name: 'e2e-chromium',
            testDir: './tests/e2e',
            use: { ...devices['Desktop Chrome'] },
            dependencies: ['setup-backend']
        },

        // Cross-browser testing
        {
            name: 'e2e-firefox',
            testDir: './tests/e2e',
            use: { ...devices['Desktop Firefox'] },
            dependencies: ['setup-backend']
        },

        // Mobile testing
        {
            name: 'mobile-chrome',
            testDir: './tests/e2e',
            use: { ...devices['Pixel 5'] },
            dependencies: ['setup-backend']
        }
    ]
});
```

**Test Categories and Prioritization:**

```typescript
// tests/categories/test-categories.ts
export const TestCategories = {
    CRITICAL: {
        priority: 1,
        timeout: 30000,
        retries: 3,
        tests: [
            'authentication-flows',
            'dashboard-loading',
            'campaign-creation',
            'resource-management'
        ]
    },

    ADVANCED: {
        priority: 2,
        timeout: 60000,
        retries: 2,
        tests: [
            'agent-management',
            'campaign-operations',
            'user-management',
            'access-control'
        ]
    },

    INTEGRATION: {
        priority: 3,
        timeout: 120000,
        retries: 1,
        tests: [
            'real-time-features',
            'workflow-integration',
            'performance-validation',
            'ui-polish'
        ]
    }
};

// Test execution based on category
export function getTestConfig(category: keyof typeof TestCategories) {
    const config = TestCategories[category];
    return {
        timeout: config.timeout,
        retries: config.retries,
        tag: `@${category.toLowerCase()}`
    };
}
```

### Mock Service Worker Integration

**API Mocking for Fast Tests:**

```typescript
// tests/mocks/api-handlers.ts
import { rest } from 'msw';

export const handlers = [
    // Authentication endpoints
    rest.post('/api/v1/web/auth/session/login', (req, res, ctx) => {
        const { username, password } = req.body as any;

        if (username === 'admin' && password === 'admin123') {
            return res(
                ctx.status(200),
                ctx.json({
                    user: { id: '1', username: 'admin', role: 'admin' },
                    projects: [
                        { id: '1', name: 'Test Project 1' },
                        { id: '2', name: 'Test Project 2' }
                    ]
                })
            );
        }

        return res(ctx.status(401), ctx.json({ detail: 'Invalid credentials' }));
    }),

    // Dashboard endpoints
    rest.get('/api/v1/web/dashboard/stats', (req, res, ctx) => {
        return res(
            ctx.status(200),
            ctx.json({
                agents: { online: 5, total: 10 },
                tasks: { running: 3, total: 15 },
                cracks: { recent: 42 },
                hashRate: 1500000
            })
        );
    }),

    // Campaign endpoints
    rest.get('/api/v1/web/campaigns/', (req, res, ctx) => {
        return res(
            ctx.status(200),
            ctx.json({
                items: [
                    {
                        id: '1',
                        name: 'Test Campaign 1',
                        status: 'running',
                        progress: 75,
                        attacks: 3
                    }
                ],
                total: 1
            })
        );
    }),

    // SSE endpoints
    rest.get('/api/v1/web/live/campaigns', (req, res, ctx) => {
        return res(
            ctx.status(200),
            ctx.set('Content-Type', 'text/event-stream'),
            ctx.body('data: {"type": "campaign_update", "data": {"id": "1", "progress": 80}}\n\n')
        );
    })
];

// MSW setup
import { setupWorker } from 'msw';

export const worker = setupWorker(...handlers);

// Start worker in browser
if (typeof window !== 'undefined') {
    worker.start();
}
```

## Performance Considerations

### Test Performance Optimization

**Parallel Test Execution:**

```typescript
// tests/utilities/parallel-execution.ts
export class ParallelTestManager {
    private workerPool: TestWorker[] = [];
    private testQueue: TestCase[] = [];

    constructor(private maxWorkers: number = 4) {}

    async executeTests(testCases: TestCase[]): Promise<TestResult[]> {
        this.testQueue = [...testCases];
        const results: TestResult[] = [];

        // Create worker pool
        for (let i = 0; i < this.maxWorkers; i++) {
            this.workerPool.push(new TestWorker(i));
        }

        // Execute tests in parallel
        const promises = this.workerPool.map(worker =>
            this.runWorker(worker, results)
        );

        await Promise.all(promises);
        return results;
    }

    private async runWorker(worker: TestWorker, results: TestResult[]) {
        while (this.testQueue.length > 0) {
            const testCase = this.testQueue.shift();
            if (!testCase) break;

            try {
                const result = await worker.executeTest(testCase);
                results.push(result);
            } catch (error) {
                results.push({
                    testCase,
                    status: 'failed',
                    error: error.message,
                    duration: 0
                });
            }
        }
    }
}
```

**Resource Management:**

```typescript
// tests/utilities/resource-management.ts
export class TestResourceManager {
    private browserContexts: Map<string, BrowserContext> = new Map();
    private pagePool: Page[] = [];

    async getBrowserContext(testId: string): Promise<BrowserContext> {
        if (!this.browserContexts.has(testId)) {
            const context = await browser.newContext({
                viewport: { width: 1280, height: 720 },
                ignoreHTTPSErrors: true,
                recordVideo: process.env.CI ? { dir: 'test-results/videos' } : undefined
            });

            this.browserContexts.set(testId, context);
        }

        return this.browserContexts.get(testId)!;
    }

    async getPage(testId: string): Promise<Page> {
        const context = await this.getBrowserContext(testId);
        const page = await context.newPage();

        // Set up error handling
        page.on('pageerror', error => {
            console.error(`Page error in test ${testId}:`, error);
        });

        page.on('requestfailed', request => {
            console.warn(`Request failed in test ${testId}:`, request.url());
        });

        return page;
    }

    async cleanup(testId: string) {
        const context = this.browserContexts.get(testId);
        if (context) {
            await context.close();
            this.browserContexts.delete(testId);
        }
    }

    async cleanupAll() {
        for (const [testId, context] of this.browserContexts) {
            await context.close();
        }
        this.browserContexts.clear();
    }
}
```

### Memory and Performance Monitoring

**Test Performance Metrics:**

```typescript
// tests/utilities/performance-monitoring.ts
export class PerformanceMonitor {
    private metrics: PerformanceMetric[] = [];

    async measurePageLoad(page: Page, url: string): Promise<PageLoadMetrics> {
        const startTime = Date.now();

        await page.goto(url);
        await page.waitForLoadState('networkidle');

        const endTime = Date.now();
        const loadTime = endTime - startTime;

        // Get performance metrics from browser
        const performanceMetrics = await page.evaluate(() => {
            const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
            return {
                domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
                loadComplete: navigation.loadEventEnd - navigation.loadEventStart,
                firstPaint: performance.getEntriesByName('first-paint')[0]?.startTime || 0,
                firstContentfulPaint: performance.getEntriesByName('first-contentful-paint')[0]?.startTime || 0
            };
        });

        const metrics: PageLoadMetrics = {
            url,
            totalLoadTime: loadTime,
            ...performanceMetrics,
            timestamp: new Date()
        };

        this.metrics.push(metrics);
        return metrics;
    }

    async measureMemoryUsage(page: Page): Promise<MemoryMetrics> {
        const memoryInfo = await page.evaluate(() => {
            return (performance as any).memory ? {
                usedJSHeapSize: (performance as any).memory.usedJSHeapSize,
                totalJSHeapSize: (performance as any).memory.totalJSHeapSize,
                jsHeapSizeLimit: (performance as any).memory.jsHeapSizeLimit
            } : null;
        });

        return {
            ...memoryInfo,
            timestamp: new Date()
        };
    }

    generateReport(): PerformanceReport {
        return {
            totalTests: this.metrics.length,
            averageLoadTime: this.calculateAverage('totalLoadTime'),
            slowestPages: this.getSlowestPages(5),
            performanceTrends: this.calculateTrends(),
            recommendations: this.generateRecommendations()
        };
    }

    private calculateAverage(metric: keyof PageLoadMetrics): number {
        const values = this.metrics.map(m => m[metric] as number).filter(v => v > 0);
        return values.reduce((sum, val) => sum + val, 0) / values.length;
    }

    private getSlowestPages(count: number): PageLoadMetrics[] {
        return this.metrics
            .sort((a, b) => b.totalLoadTime - a.totalLoadTime)
            .slice(0, count);
    }
}
```

## Security Considerations

### Test Security Architecture

**Secure Test Environment:**

```typescript
// tests/security/test-security.ts
export class TestSecurityManager {
    async validateTestEnvironment(): Promise<SecurityValidation> {
        const checks = [
            this.validateTestCredentials(),
            this.validateNetworkIsolation(),
            this.validateDataSanitization(),
            this.validateAccessControls()
        ];

        const results = await Promise.all(checks);

        return {
            passed: results.every(r => r.passed),
            checks: results,
            recommendations: this.generateSecurityRecommendations(results)
        };
    }

    private async validateTestCredentials(): Promise<SecurityCheck> {
        // Ensure test credentials are not production credentials
        const testUsers = ['admin', 'project_admin', 'user'];
        const productionIndicators = ['prod', 'production', 'live'];

        const hasProductionCredentials = testUsers.some(user =>
            productionIndicators.some(indicator =>
                user.toLowerCase().includes(indicator)
            )
        );

        return {
            name: 'Test Credentials Validation',
            passed: !hasProductionCredentials,
            message: hasProductionCredentials
                ? 'Test environment uses production-like credentials'
                : 'Test credentials are properly isolated'
        };
    }

    private async validateNetworkIsolation(): Promise<SecurityCheck> {
        // Ensure test environment doesn't access production services
        try {
            const response = await fetch('https://production-api.example.com/health');
            return {
                name: 'Network Isolation',
                passed: false,
                message: 'Test environment can access production services'
            };
        } catch {
            return {
                name: 'Network Isolation',
                passed: true,
                message: 'Test environment is properly isolated'
            };
        }
    }

    private async validateAccessControls(): Promise<SecurityCheck> {
        // Test that access controls are properly enforced
        const testCases = [
            { role: 'user', endpoint: '/api/v1/admin/users', shouldFail: true },
            { role: 'project_admin', endpoint: '/api/v1/admin/system', shouldFail: true },
            { role: 'admin', endpoint: '/api/v1/admin/users', shouldFail: false }
        ];

        const results = await Promise.all(
            testCases.map(async testCase => {
                try {
                    const response = await this.makeAuthenticatedRequest(
                        testCase.role,
                        testCase.endpoint
                    );

                    const actuallyFailed = response.status === 403;
                    return actuallyFailed === testCase.shouldFail;
                } catch {
                    return testCase.shouldFail;
                }
            })
        );

        const allPassed = results.every(r => r);

        return {
            name: 'Access Control Validation',
            passed: allPassed,
            message: allPassed
                ? 'Access controls are properly enforced'
                : 'Some access control violations detected'
        };
    }
}
```

**Test Data Security:**

```typescript
// tests/security/data-security.ts
export class TestDataSecurity {
    async sanitizeTestData(data: any): Promise<any> {
        // Remove sensitive information from test data
        const sensitiveFields = [
            'password', 'token', 'secret', 'key', 'hash',
            'ssn', 'credit_card', 'phone', 'email'
        ];

        return this.recursiveSanitize(data, sensitiveFields);
    }

    private recursiveSanitize(obj: any, sensitiveFields: string[]): any {
        if (typeof obj !== 'object' || obj === null) {
            return obj;
        }

        if (Array.isArray(obj)) {
            return obj.map(item => this.recursiveSanitize(item, sensitiveFields));
        }

        const sanitized: any = {};
        for (const [key, value] of Object.entries(obj)) {
            if (sensitiveFields.some(field => key.toLowerCase().includes(field))) {
                sanitized[key] = '[REDACTED]';
            } else {
                sanitized[key] = this.recursiveSanitize(value, sensitiveFields);
            }
        }

        return sanitized;
    }

    async validateDataLeakage(testResults: TestResult[]): Promise<DataLeakageReport> {
        const leaks: DataLeak[] = [];

        for (const result of testResults) {
            // Check for sensitive data in test output
            const sensitivePatterns = [
                /password["\s]*[:=]["\s]*[^"\s]+/gi,
                /token["\s]*[:=]["\s]*[^"\s]+/gi,
                /secret["\s]*[:=]["\s]*[^"\s]+/gi,
                /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/gi
            ];

            for (const pattern of sensitivePatterns) {
                const matches = result.output?.match(pattern);
                if (matches) {
                    leaks.push({
                        testId: result.testId,
                        pattern: pattern.source,
                        matches: matches.length,
                        severity: 'high'
                    });
                }
            }
        }

        return {
            totalLeaks: leaks.length,
            leaks,
            recommendations: this.generateDataLeakageRecommendations(leaks)
        };
    }
}
```

## Implementation Strategy

### Phase-Based Implementation Plan

**Phase 3A: Critical Foundation (Week 1-2)**

```typescript
// Implementation priority: Authentication and core workflows
const Phase3A = {
    authentication: [
        'SSR session-based authentication implementation',
        'Test user seeding with known credentials',
        'Authentication helper utilities',
        'Session persistence and cleanup'
    ],

    dashboard: [
        'Dashboard loading with SSR data',
        'Status card display and interaction',
        'Basic navigation testing',
        'Error state handling'
    ],

    campaigns: [
        'Campaign list loading and display',
        'Basic campaign creation workflow',
        'Campaign detail page navigation',
        'Campaign status updates'
    ],

    resources: [
        'Resource list display and filtering',
        'Basic resource upload workflow',
        'Resource detail view navigation',
        'Resource management operations'
    ]
};
```

**Phase 3B: Advanced Features (Week 3-4)**

```typescript
const Phase3B = {
    agents: [
        'Agent list display and status monitoring',
        'Agent registration workflow',
        'Agent detail modal functionality',
        'Agent management operations'
    ],

    attacks: [
        'Attack configuration wizard',
        'Attack parameter validation',
        'Keyspace estimation testing',
        'Attack management operations'
    ],

    users: [
        'User management interface implementation',
        'User creation and editing workflows',
        'Role-based access control validation',
        'User deletion with impact assessment'
    ],

    projects: [
        'Project selection and switching',
        'Project context persistence',
        'Project-scoped data validation',
        'Project management operations'
    ]
};
```

**Phase 3C: Integration and Polish (Week 5-6)**

```typescript
const Phase3C = {
    realTime: [
        'SSE connection management',
        'Live dashboard updates',
        'Toast notification system',
        'Real-time status indicators'
    ],

    integration: [
        'End-to-end workflow testing',
        'Cross-component integration',
        'Error recovery scenarios',
        'Performance validation'
    ],

    polish: [
        'Responsive design testing',
        'Accessibility compliance',
        'Theme switching functionality',
        'Mobile navigation testing'
    ],

    quality: [
        'Test coverage analysis',
        'Performance benchmarking',
        'Security validation',
        'Documentation completion'
    ]
};
```

### Test Infrastructure Setup

**Docker Integration for E2E Testing:**

```yaml
# docker-compose.e2e.yml
version: '3.8'
services:
  app:
    build:
      context: .
      dockerfile: Dockerfile.dev
    environment:
      - DATABASE_URL=postgresql://test:test@db:5432/cipherswarm_test
      - REDIS_URL=redis://redis:6379/1
      - MINIO_URL=http://minio:9000
      - TEST_MODE=true
    depends_on:
      - db
      - redis
      - minio
    ports:
      - 8000:8000
    healthcheck:
      test: [CMD, curl, -f, http://localhost:8000/api/v1/health]
      interval: 10s
      timeout: 5s
      retries: 5

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    environment:
      - VITE_API_BASE_URL=http://app:8000
      - VITE_TEST_MODE=true
    ports:
      - 5173:5173
    depends_on:
      - app

  db:
    image: postgres:16
    environment:
      - POSTGRES_DB=cipherswarm_test
      - POSTGRES_USER=test
      - POSTGRES_PASSWORD=test
    volumes:
      - test_db_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes

  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      - MINIO_ROOT_USER=testuser
      - MINIO_ROOT_PASSWORD=testpass123
    volumes:
      - test_minio_data:/data

volumes:
  test_db_data:
  test_minio_data:
```

**Test Execution Scripts:**

```bash
#!/bin/bash
# scripts/run-e2e-tests.sh

set -e

echo "Starting E2E test environment..."

# Start Docker services
docker-compose -f docker-compose.e2e.yml up -d

# Wait for services to be healthy
echo "Waiting for services to be ready..."
timeout 60 bash -c 'until curl -f http://localhost:8000/api/v1/health; do sleep 2; done'
timeout 60 bash -c 'until curl -f http://localhost:5173; do sleep 2; done'

# Seed test data
echo "Seeding test data..."
curl -X POST http://localhost:8000/api/v1/test/seed-environment

# Run tests
echo "Running E2E tests..."
cd frontend
pnpm test:e2e

# Cleanup
echo "Cleaning up..."
docker-compose -f docker-compose.e2e.yml down -v

echo "E2E tests completed!"
```

This comprehensive design provides the foundation for implementing complete E2E test coverage while maintaining the established three-tier testing architecture and ensuring proper authentication integration for comprehensive workflow validation.
