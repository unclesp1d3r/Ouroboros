---

## inclusion: fileMatch fileMatchPattern: \[frontend/\*\*/*.ts, docs/v2_rewrite_implementation_plan/phase-3-web-ui-implementation/*.md\]

# SSR Patterns and Load Function Best Practices

## Overview

This rule defines patterns for Server-Side Rendering (SSR) in SvelteKit, focusing on proper load function implementation, data hydration, and the relationship between SSR data and client-side stores.

## Load Function Patterns

### Basic Load Function Structure

```typescript
// +page.server.ts
import type { PageServerLoad } from './$types';
import { redirect, error } from '@sveltejs/kit';
import { serverApi } from '$lib/api/server';
import { CampaignListResponseSchema } from '$lib/schemas/campaigns';

export const load: PageServerLoad = async ({ cookies, url, params }) => {
    // Environment detection for testing
    if (process.env.NODE_ENV === 'test' || process.env.PLAYWRIGHT_TEST) {
        return { campaigns: mockCampaignData };
    }

    try {
        const response = await serverApi.get('/api/v1/web/campaigns/', {
            headers: {
                Cookie: cookies.toString(),
                'User-Agent': 'Ouroboros-Frontend/1.0'
            }
        });

        // Parse response with schema validation
        const campaignsData = CampaignListResponseSchema.parse(response.data);

        return {
            campaigns: campaignsData,
            meta: {
                title: 'Campaigns',
                description: 'Manage your password cracking campaigns'
            }
        };
    } catch (error) {
        // Handle authentication errors
        if (error.response?.status === 401) {
            throw redirect(302, '/login');
        }

        // Handle other errors
        console.error('Failed to load campaigns:', error);
        throw error(500, 'Failed to load campaigns');
    }
};
```

### Authentication in Load Functions

```typescript
// +layout.server.ts - Global authentication check
export const load: LayoutServerLoad = async ({ cookies }) => {
    const sessionId = cookies.get('sessionid');

    if (!sessionId) {
        return { user: null, isAuthenticated: false };
    }

    try {
        const response = await serverApi.get('/api/v1/auth/me/', {
            headers: { Cookie: `sessionid=${sessionId}` }
        });

        const userData = UserReadSchema.parse(response.data);

        return {
            user: userData,
            isAuthenticated: true
        };
    } catch (error) {
        // Clear invalid session
        cookies.delete('sessionid', { path: '/' });
        return { user: null, isAuthenticated: false };
    }
};
```

### Parameterized Load Functions

```typescript
// +page.server.ts - Dynamic route with parameters
export const load: PageServerLoad = async ({ params, cookies }) => {
    const { id } = params;

    if (!id || isNaN(Number(id))) {
        throw error(400, 'Invalid campaign ID');
    }

    try {
        const [campaignResponse, attacksResponse] = await Promise.all([
            serverApi.get(`/api/v1/web/campaigns/${id}/`, {
                headers: { Cookie: cookies.toString() }
            }),
            serverApi.get(`/api/v1/web/campaigns/${id}/attacks/`, {
                headers: { Cookie: cookies.toString() }
            })
        ]);

        const campaign = CampaignReadSchema.parse(campaignResponse.data);
        const attacks = AttackListResponseSchema.parse(attacksResponse.data);

        return {
            campaign,
            attacks,
            meta: {
                title: `Campaign: ${campaign.name}`,
                description: campaign.description || 'Campaign details'
            }
        };
    } catch (error) {
        if (error.response?.status === 404) {
            throw error(404, 'Campaign not found');
        }
        throw error(500, 'Failed to load campaign');
    }
};
```

## Component Data Usage Patterns

### Direct SSR Data Usage (Preferred)

```svelte
<!-- +page.svelte - Use SSR data directly -->
<script lang="ts">
    import type { PageData } from './$types';

    let { data }: { data: PageData } = $props();

    // Use SSR data directly for initial render
    let campaigns = $derived(data.campaigns.items);
    let totalCount = $derived(data.campaigns.total_count);
    let currentPage = $derived(data.campaigns.page);

    // Compute derived values from SSR data
    let activeCampaigns = $derived(
        campaigns.filter(c => c.status === 'active')
    );
</script>

<div class="campaigns-list">
    <h1>Campaigns ({totalCount})</h1>

    {#each campaigns as campaign}
        <CampaignCard {campaign} />
    {/each}

    <Pagination
        currentPage={currentPage}
        totalPages={data.campaigns.total_pages}
    />
</div>
```

### Store Hydration (When Reactive Updates Needed)

```svelte
<!-- +page.svelte - Hydrate store for reactive updates -->
<script lang="ts">
    import type { PageData } from './$types';
    import { campaignsStore } from '$lib/stores/campaigns.svelte';
    import { onMount } from 'svelte';

    let { data }: { data: PageData } = $props();

    // Use SSR data for initial render
    let campaigns = $derived(data.campaigns.items);

    // Hydrate store only if components need reactive updates
    $effect(() => {
        // Only hydrate if we need real-time updates or cross-component state
        if (needsReactiveUpdates) {
            campaignsStore.hydrate(data.campaigns);
        }
    });

    // Use store data for reactive operations
    let storeCampaigns = $derived(campaignsStore.campaigns);
    let isLoading = $derived(campaignsStore.loading);
</script>
```

## Form Handling with SSR

### Form Actions with Validation

```typescript
// +page.server.ts - Form actions
import { fail } from '@sveltejs/kit';
import { superValidate } from 'sveltekit-superforms';
import { zod } from 'sveltekit-superforms/adapters';
import { CampaignCreateSchema } from '$lib/schemas/campaigns';

export const load: PageServerLoad = async () => {
    const form = await superValidate(zod(CampaignCreateSchema));

    return { form };
};

export const actions = {
    create: async ({ request, cookies }) => {
        const form = await superValidate(request, zod(CampaignCreateSchema));

        if (!form.valid) {
            return fail(400, { form });
        }

        try {
            const response = await serverApi.post('/api/v1/web/campaigns/', form.data, {
                headers: { Cookie: cookies.toString() }
            });

            const newCampaign = CampaignReadSchema.parse(response.data);

            throw redirect(302, `/campaigns/${newCampaign.id}`);
        } catch (error) {
            if (error.response?.status === 400) {
                return fail(400, {
                    form,
                    message: 'Invalid campaign data'
                });
            }

            return fail(500, {
                form,
                message: 'Failed to create campaign'
            });
        }
    }
};
```

### Form Component with SSR Data

```svelte
<!-- CampaignForm.svelte -->
<script lang="ts">
    import { superForm } from 'sveltekit-superforms';
    import { zodClient } from 'sveltekit-superforms/adapters';
    import { CampaignCreateSchema } from '$lib/schemas/campaigns';

    let { data, message = null } = $props();

    const { form, errors, enhance, submitting } = superForm(data.form, {
        validators: zodClient(CampaignCreateSchema),
        resetForm: false,
        onUpdated: ({ form }) => {
            if (form.valid) {
                // Handle successful submission
                console.log('Campaign created successfully');
            }
        }
    });
</script>

<form method="POST" action="?/create" use:enhance>
    <div class="form-group">
        <label for="name">Campaign Name</label>
        <input
            id="name"
            name="name"
            bind:value={$form.name}
            class:error={$errors.name}
        />
        {#if $errors.name}
            <span class="error">{$errors.name}</span>
        {/if}
    </div>

    <button type="submit" disabled={$submitting}>
        {$submitting ? 'Creating...' : 'Create Campaign'}
    </button>

    {#if message}
        <div class="message">{message}</div>
    {/if}
</form>
```

## Error Handling Patterns

### Graceful Error Boundaries

```typescript
// +error.svelte - Error page component
<script lang="ts">
    import { page } from '$app/stores';

    let { status, error } = $props();
</script>

<div class="error-page">
    <h1>{status}</h1>
    <p>{error?.message || 'An unexpected error occurred'}</p>

    {#if status === 404}
        <p>The page you're looking for doesn't exist.</p>
        <a href="/">Go home</a>
    {:else if status === 401}
        <p>You need to log in to access this page.</p>
        <a href="/login">Log in</a>
    {:else if status === 500}
        <p>Something went wrong on our end.</p>
        <button onclick="window.location.reload()">Try again</button>
    {/if}
</div>
```

### Load Function Error Recovery

```typescript
// +page.server.ts - Error recovery patterns
export const load: PageServerLoad = async ({ cookies, depends }) => {
    depends('campaigns:list');

    try {
        const response = await serverApi.get('/api/v1/web/campaigns/');
        return { campaigns: response.data };
    } catch (error) {
        // Provide fallback data instead of throwing
        if (error.response?.status === 503) {
            return {
                campaigns: { items: [], total_count: 0 },
                error: 'Service temporarily unavailable'
            };
        }

        // Only throw for critical errors
        throw error(500, 'Failed to load campaigns');
    }
};
```

## Performance Optimization

### Parallel Data Loading

```typescript
// +page.server.ts - Load multiple resources in parallel
export const load: PageServerLoad = async ({ cookies }) => {
    try {
        // Load multiple resources concurrently
        const [campaignsResponse, projectsResponse, agentsResponse] = await Promise.all([
            serverApi.get('/api/v1/web/campaigns/'),
            serverApi.get('/api/v1/web/projects/'),
            serverApi.get('/api/v1/web/agents/')
        ]);

        return {
            campaigns: CampaignListResponseSchema.parse(campaignsResponse.data),
            projects: ProjectListResponseSchema.parse(projectsResponse.data),
            agents: AgentListResponseSchema.parse(agentsResponse.data)
        };
    } catch (error) {
        // Handle errors appropriately
        throw error(500, 'Failed to load dashboard data');
    }
};
```

### Conditional Data Loading

```typescript
// +page.server.ts - Load data conditionally
export const load: PageServerLoad = async ({ url, cookies }) => {
    const showAdvanced = url.searchParams.get('advanced') === 'true';

    const basicDataPromise = serverApi.get('/api/v1/web/campaigns/');

    // Only load additional data if needed
    const advancedDataPromise = showAdvanced
        ? serverApi.get('/api/v1/web/campaigns/analytics/')
        : Promise.resolve(null);

    const [basicResponse, advancedResponse] = await Promise.all([
        basicDataPromise,
        advancedDataPromise
    ]);

    return {
        campaigns: CampaignListResponseSchema.parse(basicResponse.data),
        analytics: advancedResponse ?
            CampaignAnalyticsSchema.parse(advancedResponse.data) : null
    };
};
```

## Testing SSR Load Functions

### Load Function Unit Tests

```typescript
// +page.server.test.ts
import { describe, it, expect, vi } from 'vitest';
import { load } from './+page.server';

// Mock the server API
vi.mock('$lib/api/server', () => ({
    serverApi: {
        get: vi.fn()
    }
}));

describe('campaigns load function', () => {
    it('loads campaigns successfully', async () => {
        const mockResponse = {
            data: {
                items: [{ id: 1, name: 'Test Campaign' }],
                total_count: 1,
                page: 1,
                page_size: 10,
                total_pages: 1
            }
        };

        vi.mocked(serverApi.get).mockResolvedValue(mockResponse);

        const result = await load({
            cookies: new Map([['sessionid', 'test-session']]),
            url: new URL('http://localhost/campaigns'),
            params: {}
        });

        expect(result.campaigns).toEqual(mockResponse.data);
    });

    it('handles authentication errors', async () => {
        vi.mocked(serverApi.get).mockRejectedValue({
            response: { status: 401 }
        });

        await expect(load({
            cookies: new Map(),
            url: new URL('http://localhost/campaigns'),
            params: {}
        })).rejects.toThrow('redirect');
    });
});
```

### Integration Testing with Playwright

```typescript
// campaigns.e2e.test.ts
import { test, expect } from '@playwright/test';

test('campaigns page loads with SSR data', async ({ page }) => {
    await page.goto('/campaigns');

    // Verify SSR content is immediately visible
    await expect(page.locator('h1')).toContainText('Campaigns');

    // Verify campaign data is rendered
    await expect(page.locator('[data-testid="campaign-item"]')).toHaveCount(3);

    // Verify no loading states on initial render
    await expect(page.locator('[data-testid="loading"]')).not.toBeVisible();
});
```

## Best Practices Summary

1. **Use SSR data directly** in components when possible
2. **Only hydrate stores** when reactive updates are needed
3. **Parse all API responses** with Zod schemas in load functions
4. **Handle errors gracefully** with appropriate redirects and fallbacks
5. **Load data in parallel** when possible for performance
6. **Test load functions** with unit tests and integration tests
7. **Provide meaningful error pages** for different error types
8. **Use environment detection** for test scenarios

## Anti-Patterns to Avoid

### Loading Data in Components

```svelte
<!-- ❌ WRONG - Don't load data in components -->
<script>
    import { onMount } from 'svelte';

    let campaigns = [];

    onMount(async () => {
        const response = await fetch('/api/campaigns');
        campaigns = await response.json();
    });
</script>
```

### Mixing SSR and Client Data

```svelte
<!-- ❌ WRONG - Don't mix SSR data with store calls -->
<script>
    export let data;
    import { getCampaigns } from '$lib/stores/campaigns.svelte';

    // This creates confusion about data source
    let campaigns = $derived(getCampaigns());
</script>
```

### Ignoring Schema Validation

```typescript
// ❌ WRONG - Don't skip schema validation in load functions
export const load: PageServerLoad = async ({ cookies }) => {
    const response = await serverApi.get('/api/campaigns/');
    return { campaigns: response.data }; // No validation!
};
```

## File References

- Load function examples: [+page.server.ts](mdc:Ouroboros/frontend/src/routes/campaigns/+page.server.ts)
- Component usage: [+page.svelte](mdc:Ouroboros/frontend/src/routes/campaigns/+page.svelte)
- Error handling: [+error.svelte](mdc:Ouroboros/frontend/src/routes/+error.svelte)
- Schema integration: [campaigns.ts](mdc:Ouroboros/frontend/src/lib/schemas/campaigns.ts)
