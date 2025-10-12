import { test, expect } from '@playwright/test';

// Mock data for attacks
const mockAttacksResponse = {
    attacks: [
        {
            id: 1,
            name: 'Dictionary Attack 1',
            type: 'dictionary',
            language: 'English',
            length_min: 6,
            length_max: 12,
            settings_summary: 'Best64 rules with common passwords',
            keyspace: 1000000,
            complexity_score: 3,
            comment: 'Standard dictionary attack',
            state: 'running',
            created_at: '2023-01-01T10:00:00Z',
            updated_at: '2023-01-01T11:00:00Z',
            campaign_id: 1,
            campaign_name: 'Test Campaign 1',
        },
        {
            id: 2,
            name: 'Brute Force Attack',
            type: 'brute_force',
            language: null,
            length_min: 1,
            length_max: 4,
            settings_summary: 'Lowercase, Uppercase, Numbers, Symbols',
            keyspace: 78914410,
            complexity_score: 4,
            comment: null,
            state: 'completed',
            created_at: '2023-01-01T09:00:00Z',
            updated_at: '2023-01-01T12:00:00Z',
            campaign_id: 2,
            campaign_name: 'Test Campaign 2',
        },
        {
            id: 3,
            name: 'Mask Attack',
            type: 'mask',
            language: 'English',
            length_min: 8,
            length_max: 8,
            settings_summary: '?u?l?l?l?l?d?d?d?d',
            keyspace: 456976000,
            complexity_score: 5,
            comment: 'Corporate password pattern',
            state: 'draft',
            created_at: '2023-01-01T08:00:00Z',
            updated_at: '2023-01-01T08:30:00Z',
            campaign_id: null,
            campaign_name: null,
        },
    ],
    total: 3,
    page: 1,
    size: 10,
    total_pages: 1,
};

const emptyAttacksResponse = {
    attacks: [],
    total: 0,
    page: 1,
    size: 10,
    total_pages: 0,
};

const searchResponse = {
    attacks: [
        {
            id: 1,
            name: 'Dictionary Attack 1',
            type: 'dictionary',
            language: 'English',
            length_min: 6,
            length_max: 12,
            settings_summary: 'Best64 rules with common passwords',
            keyspace: 1000000,
            complexity_score: 3,
            comment: 'Standard dictionary attack',
            state: 'running',
            created_at: '2023-01-01T10:00:00Z',
            updated_at: '2023-01-01T11:00:00Z',
            campaign_id: 1,
            campaign_name: 'Test Campaign 1',
        },
    ],
    total: 1,
    page: 1,
    size: 10,
    total_pages: 1,
};

test.describe('Attacks List Page', () => {
    test.beforeEach(async ({ page }) => {
        // Set up basic mocks
        await page.route('**/api/v1/web/attacks*', async (route) => {
            const url = new URL(route.request().url());
            const searchQuery = url.searchParams.get('q');

            if (searchQuery === 'dictionary') {
                await route.fulfill({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify(searchResponse),
                });
            } else {
                await route.fulfill({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify(mockAttacksResponse),
                });
            }
        });
    });

    test('should display page title and header correctly', async ({ page }) => {
        await page.goto('/attacks');

        // Check page title
        await expect(page).toHaveTitle('Attacks - Ouroboros');

        // Check main heading
        await expect(page.getByRole('heading', { name: 'Attacks' })).toBeVisible();

        // Check description
        await expect(page.getByText('Manage and monitor attack configurations')).toBeVisible();

        // Check new attack button
        await expect(page.getByTestId('new-attack-button')).toBeVisible();
    });

    test('should load and display attacks correctly', async ({ page }) => {
        await page.goto('/attacks');

        // Wait for attacks table to be visible (loading will complete with mocked data)
        await expect(page.getByTestId('attacks-table')).toBeVisible();

        // Check that all attacks are displayed
        await expect(page.getByTestId('attack-row-1')).toBeVisible();
        await expect(page.getByTestId('attack-row-2')).toBeVisible();
        await expect(page.getByTestId('attack-row-3')).toBeVisible();

        // Check attack names
        await expect(page.getByText('Dictionary Attack 1')).toBeVisible();
        await expect(page.getByText('Brute Force Attack')).toBeVisible();
        await expect(page.getByText('Mask Attack')).toBeVisible();

        // Check attack types (using badge selector to avoid ambiguity)
        await expect(
            page.getByTestId('attack-row-1').locator('[data-slot="badge"]').getByText('Dictionary')
        ).toBeVisible();
        await expect(
            page.getByTestId('attack-row-2').locator('[data-slot="badge"]').getByText('Brute Force')
        ).toBeVisible();
        await expect(
            page.getByTestId('attack-row-3').locator('[data-slot="badge"]').getByText('Mask')
        ).toBeVisible();

        // Check attack states
        await expect(page.getByText('Running')).toBeVisible();
        await expect(page.getByText('Completed')).toBeVisible();
        await expect(page.getByText('Draft')).toBeVisible();

        // Check total count
        await expect(page.getByText('(3 total)')).toBeVisible();
    });

    test('should display attack details correctly', async ({ page }) => {
        await page.goto('/attacks');
        await expect(page.getByTestId('attacks-table')).toBeVisible();

        // Check language display
        await expect(page.locator('text=English').first()).toBeVisible();
        await expect(page.locator('text=—').first()).toBeVisible(); // For null language

        // Check length formatting
        await expect(page.getByText('6 → 12')).toBeVisible();
        await expect(page.getByText('1 → 4')).toBeVisible();
        await expect(page.getByTestId('attack-row-3').getByText('8')).toBeVisible(); // Same min/max

        // Check keyspace formatting
        await expect(page.getByText('1,000,000')).toBeVisible();
        await expect(page.getByText('78,914,410')).toBeVisible();
        await expect(page.getByText('456,976,000')).toBeVisible();

        // Check complexity dots
        await expect(page.getByTestId('complexity-1')).toBeVisible();
        await expect(page.getByTestId('complexity-2')).toBeVisible();
        await expect(page.getByTestId('complexity-3')).toBeVisible();

        // Check settings summary
        await expect(page.getByTestId('settings-summary-1')).toBeVisible();
        await expect(page.getByTestId('settings-summary-2')).toBeVisible();
        await expect(page.getByTestId('settings-summary-3')).toBeVisible();

        // Check campaign names
        await expect(page.getByText('Test Campaign 1')).toBeVisible();
        await expect(page.getByText('Test Campaign 2')).toBeVisible();

        // Check comments
        await expect(page.getByText('Standard dictionary attack')).toBeVisible();
        await expect(page.getByText('Corporate password pattern')).toBeVisible();
    });

    test('should handle search functionality', async ({ page }) => {
        await page.goto('/attacks');
        await expect(page.getByTestId('attacks-table')).toBeVisible();

        // Test search input
        const searchInput = page.getByTestId('search-input');
        await expect(searchInput).toBeVisible();
        await expect(searchInput).toHaveAttribute('placeholder', /Search attacks/);

        // Perform search
        await searchInput.fill('dictionary');

        // Wait for debounced search
        await page.waitForTimeout(500);

        // Should show only dictionary attack
        await expect(page.getByTestId('attack-row-1')).toBeVisible();
        await expect(page.getByTestId('attack-row-2')).not.toBeVisible();
        await expect(page.getByTestId('attack-row-3')).not.toBeVisible();

        // Check total count updated
        await expect(page.getByText('(1 total)')).toBeVisible();
    });

    test('should handle empty state correctly', async ({ page }) => {
        // Use URL parameter to trigger empty state in SSR
        await page.goto('/attacks?test_scenario=empty');

        // Check empty state message
        await expect(page.getByTestId('empty-state')).toBeVisible();
        await expect(page.getByText('No attacks configured yet.')).toBeVisible();

        // Check create first attack button
        await expect(page.getByText('Create your first attack')).toBeVisible();
    });

    test('should handle search empty state correctly', async ({ page }) => {
        // Start with normal attacks page
        await page.goto('/attacks');
        await expect(page.getByTestId('attacks-table')).toBeVisible();

        // Perform search with no results (this will trigger SSR reload with search parameter)
        await page.getByTestId('search-input').fill('nonexistent');

        // Wait for debounced search to trigger and navigation to complete
        await page.waitForTimeout(500);

        // Wait for URL to update with search parameter
        await page.waitForURL(/.*q=nonexistent.*/);

        // Check search empty state
        await expect(page.getByTestId('empty-state')).toBeVisible();
        await expect(page.getByText('No attacks found matching "nonexistent".')).toBeVisible();

        // Test clear search button
        await page.getByText('Clear search').click();

        // Should reload all attacks
        await expect(page.getByTestId('attacks-table')).toBeVisible();
        await expect(page.getByTestId('attack-row-1')).toBeVisible();
    });

    test('should handle error state correctly', async ({ page }) => {
        // Use URL parameter to trigger error state in SSR
        await page.goto('/attacks?test_scenario=error');

        // Check error alert
        await expect(page.getByTestId('error-alert')).toBeVisible();
        await expect(page.getByText('Failed to load attacks.')).toBeVisible();
    });

    test('should display and interact with attack action menus', async ({ page }) => {
        await page.goto('/attacks');
        await expect(page.getByTestId('attacks-table')).toBeVisible();

        // Click on first attack menu
        const menuButton = page.getByTestId('attack-menu-1');
        await expect(menuButton).toBeVisible();
        await menuButton.click();

        // Check menu items
        await expect(page.getByText('View Details')).toBeVisible();
        await expect(page.getByText('Edit')).toBeVisible();
        await expect(page.getByText('Duplicate')).toBeVisible();
        await expect(page.getByText('Delete')).toBeVisible();

        // Close menu by pressing Escape
        await page.keyboard.press('Escape');
    });

    test('should handle delete confirmation', async ({ page }) => {
        await page.goto('/attacks');
        await expect(page.getByTestId('attacks-table')).toBeVisible();

        // Set up confirm dialog handling
        let dialogShown = false;
        page.on('dialog', async (dialog) => {
            expect(dialog.message()).toContain('Are you sure you want to delete this attack?');
            dialogShown = true;
            await dialog.dismiss(); // Dismiss to avoid actual deletion
        });

        // Click menu and delete
        await page.getByTestId('attack-menu-1').click();
        await page.getByText('Delete').click();

        // Verify dialog was shown
        expect(dialogShown).toBe(true);
    });

    test('should handle pagination when multiple pages exist', async ({ page }) => {
        // Use URL parameter to trigger pagination test scenario
        await page.goto('/attacks?test_scenario=pagination');
        await expect(page.getByTestId('attacks-table')).toBeVisible();

        // Check pagination info
        await expect(page.getByText('Showing page 1 of 3 (25 total)')).toBeVisible();

        // Check pagination buttons
        await expect(page.getByTestId('prev-page')).toBeDisabled();
        await expect(page.getByTestId('next-page')).not.toBeDisabled();

        // Test next page
        await page.getByTestId('next-page').click();
        await expect(page.getByText('Showing page 2 of 3 (25 total)')).toBeVisible();
    });

    test('should handle new attack button click', async ({ page }) => {
        await page.goto('/attacks');

        // Mock console.log for new attack action
        let consoleMessage = '';
        page.on('console', (msg) => {
            if (msg.text().includes('Create new attack')) {
                consoleMessage = msg.text();
            }
        });

        // Click new attack button
        await page.getByTestId('new-attack-button').click();

        // For now, just verify the button is clickable
        // TODO: Implement actual modal when attack editor is created
        await expect(page.getByTestId('new-attack-button')).toBeVisible();
    });
});
