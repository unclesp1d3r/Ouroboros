import { test, expect } from '@playwright/test';

test.describe('Resources List Page', () => {
    test.beforeEach(async ({ page }) => {
        // Mock the API response for resources list
        await page.route('/api/v1/web/resources/*', async (route) => {
            const url = new URL(route.request().url());
            const searchParams = url.searchParams;

            // Parse query parameters
            const q = searchParams.get('q') || '';
            const resourceType = searchParams.get('resource_type') || '';
            const page_num = parseInt(searchParams.get('page') || '1');
            const page_size = parseInt(searchParams.get('page_size') || '25');

            // Mock data
            const mockResources = [
                {
                    id: '550e8400-e29b-41d4-a716-446655440001',
                    file_name: 'rockyou.txt',
                    file_label: 'RockYou Wordlist',
                    resource_type: 'word_list',
                    line_count: 14344391,
                    byte_size: 139921507,
                    updated_at: '2024-01-15T10:30:00Z',
                    project_id: null,
                    unrestricted: true,
                },
                {
                    id: '550e8400-e29b-41d4-a716-446655440002',
                    file_name: 'best64.rule',
                    file_label: 'Best64 Rules',
                    resource_type: 'rule_list',
                    line_count: 77,
                    byte_size: 1024,
                    updated_at: '2024-01-14T15:45:00Z',
                    project_id: 1,
                    unrestricted: false,
                },
                {
                    id: '550e8400-e29b-41d4-a716-446655440003',
                    file_name: 'common_masks.txt',
                    file_label: null,
                    resource_type: 'mask_list',
                    line_count: 25,
                    byte_size: 512,
                    updated_at: '2024-01-13T09:15:00Z',
                    project_id: null,
                    unrestricted: true,
                },
                {
                    id: '550e8400-e29b-41d4-a716-446655440004',
                    file_name: 'custom_charset.hcchr',
                    file_label: 'Custom Charset',
                    resource_type: 'charset',
                    line_count: 1,
                    byte_size: 64,
                    updated_at: '2024-01-12T14:20:00Z',
                    project_id: 1,
                    unrestricted: false,
                },
                {
                    id: '550e8400-e29b-41d4-a716-446655440005',
                    file_name: 'previous_passwords.txt',
                    file_label: 'Previous Passwords',
                    resource_type: 'dynamic_word_list',
                    line_count: 1250,
                    byte_size: 25600,
                    updated_at: '2024-01-11T11:00:00Z',
                    project_id: 1,
                    unrestricted: false,
                },
            ];

            // Filter by search query
            let filteredResources = mockResources;
            if (q) {
                filteredResources = mockResources.filter(
                    (r) =>
                        r.file_name.toLowerCase().includes(q.toLowerCase()) ||
                        (r.file_label && r.file_label.toLowerCase().includes(q.toLowerCase()))
                );
            }

            // Filter by resource type
            if (resourceType) {
                filteredResources = filteredResources.filter(
                    (r) => r.resource_type === resourceType
                );
            }

            // Pagination
            const total_count = filteredResources.length;
            const total_pages = Math.ceil(total_count / page_size);
            const start_index = (page_num - 1) * page_size;
            const end_index = start_index + page_size;
            const items = filteredResources.slice(start_index, end_index);

            await route.fulfill({
                json: {
                    items,
                    total_count,
                    page: page_num,
                    page_size,
                    total_pages,
                    resource_type: resourceType || null,
                },
            });
        });
    });

    test('should load and display resources list', async ({ page }) => {
        await page.goto('/resources');

        // Check page title and header
        await expect(page).toHaveTitle('Resources - Ouroboros');
        await expect(page.getByRole('heading', { name: 'Resources' })).toBeVisible();
        await expect(
            page.getByText('Manage wordlists, rule lists, masks, and charsets')
        ).toBeVisible();

        // Check upload button
        await expect(page.getByRole('button', { name: 'Upload Resource' })).toBeVisible();

        // Wait for resources to load
        await expect(page.getByText('rockyou.txt')).toBeVisible();
        await expect(page.getByText('best64.rule')).toBeVisible();
        await expect(page.getByText('common_masks.txt')).toBeVisible();

        // Check resource count badge
        await expect(page.getByTestId('resource-count')).toHaveText('5');

        // Wait for table to be visible
        await expect(page.getByRole('table')).toBeVisible();

        // Check table headers
        await expect(page.locator('th').filter({ hasText: 'Name' })).toBeVisible();
        await expect(page.locator('th').filter({ hasText: 'Type' })).toBeVisible();
        await expect(page.locator('th').filter({ hasText: 'Size' })).toBeVisible();
        await expect(page.locator('th').filter({ hasText: 'Lines' })).toBeVisible();
        await expect(page.locator('th').filter({ hasText: 'Last Updated' })).toBeVisible();
    });

    test('should display resource details correctly', async ({ page }) => {
        await page.goto('/resources');

        // Wait for resources to load
        await expect(page.getByText('rockyou.txt')).toBeVisible();

        // Check resource details
        const rockyouRow = page.locator('tr').filter({ hasText: 'rockyou.txt' });
        await expect(rockyouRow.getByText('RockYou Wordlist')).toBeVisible();
        await expect(rockyouRow.getByText('Word List')).toBeVisible();
        await expect(rockyouRow.getByText('136,642 KB')).toBeVisible();
        await expect(rockyouRow.getByText('14,344,391')).toBeVisible();

        // Check rule list
        const ruleRow = page.locator('tr').filter({ hasText: 'best64.rule' });
        await expect(ruleRow.getByText('Best64 Rules')).toBeVisible();
        await expect(ruleRow.getByText('Rule List')).toBeVisible();
        await expect(ruleRow.getByText('1 KB')).toBeVisible();
        await expect(ruleRow.getByText('77')).toBeVisible();

        // Check mask list
        const maskRow = page.locator('tr').filter({ hasText: 'common_masks.txt' });
        await expect(maskRow.getByText('Mask List')).toBeVisible();
        await expect(maskRow.getByText('1 KB')).toBeVisible();
        await expect(maskRow.getByText('25')).toBeVisible();
    });

    test('should filter resources by search query', async ({ page }) => {
        await page.goto('/resources');

        // Wait for initial load
        await expect(page.getByText('rockyou.txt')).toBeVisible();

        // Search for "rock"
        await page.getByPlaceholder('Search resources...').fill('rock');
        await page.getByRole('button', { name: 'Filter' }).click();

        // Should only show rockyou.txt
        await expect(page.getByText('rockyou.txt')).toBeVisible();
        await expect(page.getByText('best64.rule')).not.toBeVisible();
        await expect(page.getByText('common_masks.txt')).not.toBeVisible();

        // Check count badge updates
        await expect(page.getByTestId('resource-count')).toHaveText('1');

        // Clear filter
        await page.getByRole('button', { name: 'Clear' }).click();

        // Should show all resources again
        await expect(page.getByText('rockyou.txt')).toBeVisible();
        await expect(page.getByText('best64.rule')).toBeVisible();
        await expect(page.getByText('common_masks.txt')).toBeVisible();
        await expect(page.getByTestId('resource-count')).toHaveText('5');
    });

    test('should filter resources by type', async ({ page }) => {
        await page.goto('/resources');

        // Wait for initial load
        await expect(page.getByText('rockyou.txt')).toBeVisible();

        // Filter by rule_list
        await page.getByLabel('Resource Type').selectOption('rule_list');
        await page.getByRole('button', { name: 'Filter' }).click();

        // Should only show rule files
        await expect(page.getByText('best64.rule')).toBeVisible();
        await expect(page.getByText('rockyou.txt')).not.toBeVisible();
        await expect(page.getByText('common_masks.txt')).not.toBeVisible();

        // Check count badge updates
        await expect(page.getByTestId('resource-count')).toHaveText('1');
    });

    test('should handle search with Enter key', async ({ page }) => {
        await page.goto('/resources');

        // Wait for initial load
        await expect(page.getByText('rockyou.txt')).toBeVisible();

        // Search using Enter key
        const searchInput = page.getByPlaceholder('Search resources...');
        await searchInput.fill('best');
        await searchInput.press('Enter');

        // Should filter results
        await expect(page.getByText('best64.rule')).toBeVisible();
        await expect(page.getByText('rockyou.txt')).not.toBeVisible();
    });

    test('should show empty state when no resources found', async ({ page }) => {
        // Use the nonexistent search query to trigger empty state
        await page.goto('/resources?q=nonexistent');

        // Should show empty state
        await expect(page.getByText('No resources found.')).toBeVisible();
        await expect(page.getByTestId('resource-count')).toHaveText('0');
    });

    test('should show empty state with filter message', async ({ page }) => {
        await page.goto('/resources');

        // Wait for initial load
        await expect(page.getByText('rockyou.txt')).toBeVisible();

        // Search for something that doesn't exist
        await page.getByPlaceholder('Search resources...').fill('nonexistent');
        await page.getByRole('button', { name: 'Filter' }).click();

        // Should show empty state with filter message
        await expect(page.getByText('No resources found.')).toBeVisible();
        await expect(page.getByText('Try adjusting your filters.')).toBeVisible();
    });

    test('should handle API errors gracefully', async ({ page }) => {
        // Use test_error parameter to trigger server error
        await page.goto('/resources?test_error=500');

        // Should show error message
        await expect(
            page.getByText('Failed to load resources: 500 Internal Server Error')
        ).toBeVisible();
    });

    // Note: Loading state test removed - SSR doesn't have loading states since content is rendered on server

    test('should update URL parameters when filtering', async ({ page }) => {
        await page.goto('/resources');

        // Wait for initial load
        await expect(page.getByText('rockyou.txt')).toBeVisible();

        // Apply search filter
        await page.getByPlaceholder('Search resources...').fill('rock');
        await page.getByRole('button', { name: 'Filter' }).click();

        // Check URL contains search parameter
        await expect(page).toHaveURL(/.*q=rock.*/);

        // Apply type filter
        await page.getByLabel('Resource Type').selectOption('word_list');
        await page.getByRole('button', { name: 'Filter' }).click();

        // Check URL contains both parameters
        await expect(page).toHaveURL(/.*q=rock.*resource_type=word_list.*/);
    });

    test('should restore filters from URL parameters', async ({ page }) => {
        // Navigate with URL parameters
        await page.goto('/resources?q=best&resource_type=rule_list');

        // Should show filtered results
        await expect(page.getByText('best64.rule')).toBeVisible();
        await expect(page.getByText('rockyou.txt')).not.toBeVisible();

        // Should restore filter values
        await expect(page.getByPlaceholder('Search resources...')).toHaveValue('best');
        await expect(page.getByLabel('Resource Type')).toHaveValue('rule_list');
    });

    test('should have accessible resource links', async ({ page }) => {
        await page.goto('/resources');

        // Wait for resources to load
        await expect(page.getByText('rockyou.txt')).toBeVisible();

        // Check resource links
        const rockyouLink = page.getByRole('link', { name: 'rockyou.txt' });
        await expect(rockyouLink).toBeVisible();
        await expect(rockyouLink).toHaveAttribute(
            'href',
            '/resources/550e8400-e29b-41d4-a716-446655440001'
        );

        const ruleLink = page.getByRole('link', { name: 'best64.rule' });
        await expect(ruleLink).toBeVisible();
        await expect(ruleLink).toHaveAttribute(
            'href',
            '/resources/550e8400-e29b-41d4-a716-446655440002'
        );
    });
});
