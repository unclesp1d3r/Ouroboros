# SSR Migration Patterns and Best Practices

## Overview

This rule documents proven patterns for migrating SvelteKit applications from SPA to SSR, based on the comprehensive migration outlined in [spa_to_ssr.md](mdc:Ouroboros/Ouroboros/docs/v2_rewrite_implementation_plan/side_quests/spa_to_ssr.md).

## Data Loading Patterns

### SSR Data vs Store Data

- **Pages should use SSR data directly** when possible
- **Only hydrate stores when components need reactive updates**
- **Avoid mixing SSR data and store data in the same component**

```svelte
<!-- ✅ CORRECT - Use SSR data directly -->
<script lang="ts">
    export let data: PageData;

    let campaigns = $derived(data.campaigns.items);
    let totalCount = $derived(data.campaigns.total_count);
</script>

<!-- ❌ WRONG - Don't mix SSR data with store calls -->
<script lang="ts">
    export let data: PageData;
    import { getCampaigns } from '$lib/stores/campaigns.svelte';

    let campaigns = $derived(getCampaigns()); // This creates confusion
</script>
```

### Load Function Patterns

```typescript
// ✅ CORRECT - Robust load function with error handling
export const load: PageServerLoad = async ({ cookies, url, params }) => {
    // Environment detection for tests
    if (process.env.NODE_ENV === 'test' || process.env.PLAYWRIGHT_TEST) {
        return { campaigns: mockCampaignData };
    }

    try {
        const response = await serverApi.get('/api/v1/web/campaigns/', {
            headers: { Cookie: cookies.get('sessionid') || '' }
        });

        return {
            campaigns: response.data,
            meta: {
                title: 'Campaigns',
                description: 'Manage your password cracking campaigns'
            }
        };
    } catch (error) {
        if (error.response?.status === 401) {
            throw redirect(302, '/login');
        }
        throw error(500, 'Failed to load campaigns');
    }
};
```

## Store Hydration Patterns

### When to Hydrate Stores

- **Components need reactive updates** after initial SSR load
- **Real-time data updates** (polling, WebSocket updates)
- **Cross-component state sharing** is required

```typescript
// ✅ CORRECT - Hydrate only when reactive updates needed
$effect(() => {
    // Only hydrate if components will update this data
    if (needsReactiveUpdates) {
        campaignsStore.hydrateCampaigns(data.campaigns);
    }
});
```

### Store Hydration Implementation

```typescript
export const campaignsStore = {
    // Hydration method for SSR data
    hydrateCampaigns(ssrData: CampaignListResponse) {
        campaignState.campaigns = ssrData.items;
        campaignState.totalCount = ssrData.total_count;
        campaignState.page = ssrData.page;
        campaignState.loading = false;
    },

    // Reactive getters
    get campaigns() { return campaignState.campaigns; },
    get loading() { return campaignState.loading; }
};
```

## Testing Patterns

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
            PLAYWRIGHT_TEST: 'true' // Enable test environment detection
        }
    }
});
```

### Mock Data Consistency

```typescript
// ✅ CORRECT - Mock data matches API structure exactly
const mockCampaigns = {
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
};
```

## Form Migration Patterns

### Modal to Route Conversion

```typescript
// ✅ CORRECT - Convert modals to dedicated routes with modal presentation
// Route: /campaigns/new
// Triggered by: Button in campaigns list
// Presentation: Modal overlay using dialog component
// Form handling: Standard SvelteKit form actions

export const actions: Actions = {
    default: async ({ request, cookies }) => {
        const form = await superValidate(request, zod(campaignSchema));

        if (!form.valid) {
            return fail(400, { form });
        }

        // Convert form data to API format
        const apiPayload = convertCampaignData(form.data);

        try {
            const campaign = await serverApi.post('/api/v1/web/campaigns/', apiPayload);
            return redirect(303, `/campaigns/${campaign.id}`);
        } catch (error) {
            return fail(500, { form, message: 'Failed to create campaign' });
        }
    }
};
```

### Superforms Integration

```svelte
<script lang="ts">
    import { superForm } from 'sveltekit-superforms';
    import { zodClient } from 'sveltekit-superforms/adapters';

    export let data;

    const { form, errors, enhance, submitting } = superForm(data.form, {
        validators: zodClient(campaignSchema)
    });
</script>

<form method="POST" use:enhance>
    <!-- Form fields using Formsnap components -->
</form>
```

## Error Handling Patterns

### Load Function Error Handling

```typescript
export const load: PageServerLoad = async ({ cookies }) => {
    try {
        const response = await serverApi.get('/api/v1/web/campaigns/');
        return { campaigns: response.data };
    } catch (error) {
        // Handle specific error cases
        if (error.response?.status === 401) {
            throw redirect(302, '/login');
        }
        if (error.response?.status === 403) {
            throw error(403, 'Access denied');
        }

        // Log error and provide fallback
        console.error('Failed to load campaigns:', error);
        throw error(500, 'Failed to load campaigns');
    }
};
```

### Component Error Boundaries

```svelte
<script lang="ts">
    export let data: PageData;

    // Handle potential data issues gracefully
    let campaigns = $derived(data.campaigns?.items || []);
    let hasError = $derived(!data.campaigns);
</script>

{#if hasError}
    <div class="error-state">
        <p>Failed to load campaigns. Please try again.</p>
    </div>
{:else}
    <!-- Normal content -->
{/if}
```

## Performance Patterns

### Selective Store Usage

```svelte
<!-- ✅ CORRECT - Use SSR data for initial render, store for updates -->
<script lang="ts">
    export let data: PageData;
    import { campaignsStore } from '$lib/stores/campaigns.svelte';

    // Use SSR data for initial render
    let initialCampaigns = data.campaigns.items;

    // Use store data for reactive updates (if needed)
    let liveCampaigns = $derived(campaignsStore.campaigns);

    // Choose data source based on context
    let displayCampaigns = $derived(
        liveCampaigns.length > 0 ? liveCampaigns : initialCampaigns
    );
</script>
```

### Lazy Store Hydration

```typescript
// Only hydrate stores when actually needed
$effect(() => {
    if (needsRealTimeUpdates && !campaignsStore.isHydrated) {
        campaignsStore.hydrateCampaigns(data.campaigns);
    }
});
```

## Established Patterns

### 1. SSR Load Function Pattern

**File Pattern**: `+page.server.ts` for every route requiring data

```typescript
import type { PageServerLoad } from './$types';
import { serverApi } from '$lib/server/api';
import { error } from '@sveltejs/kit';

export const load: PageServerLoad = async ({ cookies, params }) => {
    // Test environment detection
    if (process.env.NODE_ENV === 'test' || process.env.PLAYWRIGHT_TEST || process.env.CI) {
        return { campaigns: mockCampaignData };
    }

    try {
        const response = await serverApi.get(`/api/v1/web/campaigns/`, {
            headers: {
                'Cookie': cookies.get('sessionid') || '',
                'X-Requested-With': 'XMLHttpRequest'
            }
        });

        return { campaigns: response.data };
    } catch (err) {
        if (err.response?.status === 401) {
            throw redirect(302, '/login');
        }
        throw error(500, 'Failed to load campaigns');
    }
};
```

### 2. SvelteKit 5 Runes Store Pattern

**Reference**: @campaigns store

```typescript
import { writable } from 'svelte/store';

export function createCampaignsStore() {
    const campaigns = $state<Campaign[]>([]);
    const loading = $state(false);

    // Derived computed values
    const activeCampaigns = $derived(
        campaigns.filter(c => c.status === 'active')
    );

    // Hydrate from SSR data
    function hydrate(data: Campaign[]) {
        campaigns.splice(0, campaigns.length, ...data);
    }

    // Update after form actions
    function updateCampaign(updated: Campaign) {
        const index = campaigns.findIndex(c => c.id === updated.id);
        if (index >= 0) {
            campaigns[index] = updated;
        }
    }

    return {
        get campaigns() { return campaigns; },
        get activeCampaigns() { return activeCampaigns; },
        get loading() { return loading; },
        hydrate,
        updateCampaign
    };
}
```

### 3. Proper Formsnap Integration Pattern

**Critical Implementation** (see @attack wizard):

```svelte
<script lang="ts">
import { Field, Control, Label, FieldErrors } from 'formsnap';
import { superForm } from 'sveltekit-superforms';
import { zodClient } from 'sveltekit-superforms/adapters';

export let data;

const { form, errors, enhance, submitting } = superForm(data.form, {
    validators: zodClient(attackSchema)
});
</script>

<!-- CORRECT Formsnap pattern with Svelte 5 snippets -->
<form method="POST" use:enhance>
    <Field {form} name="name">
        <Control>
            {#snippet children({ props })}
                <Label>Attack Name</Label>
                <Input {...props} bind:value={$form.name} />
            {/snippet}
        </Control>
        <FieldErrors />
    </Field>
</form>
```

**Key Requirements**:

- ✅ Use `{#snippet children({ props })}` (Svelte 5 syntax)
- ✅ Destructure `props` from snippet parameter
- ✅ Import from `'formsnap'` directly
- ❌ Never use basic HTML forms as shortcuts

### 4. Modal-to-Route Migration Pattern

**Pattern**: Convert modals to dedicated routes with modal presentation

**Example**: Campaign editor modal → `/campaigns/new` route

```svelte
<!-- +page.svelte -->
<script lang="ts">
import { goto } from '$app/navigation';
import { Modal } from '$lib/components/ui/modal';

export let data;

function handleClose() {
    goto('/campaigns', { invalidateAll: true });
}
</script>

<Modal open={true} onOpenChange={handleClose}>
    <form method="POST" use:enhance>
        <!-- Form content -->
    </form>
</Modal>
```

**Navigation Pattern**:

```svelte
<!-- In campaigns list -->
<Button href="/campaigns/new">New Campaign</Button>
<Button href="/campaigns/{campaign.id}/edit">Edit</Button>
```

### 5. Multi-Step Form Wizard Pattern

**Example**: @Attack creation wizard

```svelte
<script lang="ts">
let currentStep = $state(0);
const steps = ['Basic Configuration', 'Attack Settings', 'Resources', 'Review'];

// Show fields based on current step and attack type
const showField = (field: string) => {
    const stepFields = {
        0: ['name', 'attack_mode', 'hash_type'],
        1: ['mask', 'increment_mode', 'increment_min'],
        2: ['wordlist_id', 'rule_list_id'],
        3: [] // Review step
    };
    return stepFields[currentStep]?.includes(field) ?? false;
};
</script>

<div class="wizard-container">
    {#each steps as step, index}
        <div class="step" class:active={index === currentStep}>
            {step}
        </div>
    {/each}
</div>

<!-- Conditional field rendering -->
{#if showField('name')}
    <Field {form} name="name">
        <!-- Field implementation -->
    </Field>
{/if}
```

## Critical Lessons Learned

### 1. Formsnap Implementation

**Issue**: Abandoning Formsnap for basic HTML when encountering integration issues **Solution**: Always use proper Formsnap pattern with Svelte 5 snippets **Rule**: Never shortcut to basic HTML - fix Formsnap integration instead

### 2. Environment Detection Strategy

**Pattern**: Consistent test environment detection

```typescript
if (process.env.NODE_ENV === 'test' || process.env.PLAYWRIGHT_TEST || process.env.CI) {
    return { mockData };
}
```

**Playwright Config**:

```typescript
webServer: {
    env: { PLAYWRIGHT_TEST: 'true' }
}
```

### 3. Docker Configuration Reuse

**Lesson**: Don't create new Docker setups - reuse existing working configurations **Example**: Use `Dockerfile.dev` for E2E testing instead of modifying production Dockerfile **Rule**: Check existing Docker files before creating new ones

### 4. Task Completion Discipline

**Critical Rule**: Complete one task fully before moving to next **Anti-pattern**: Partial implementations across multiple routes **Verification**: Run `just ci-check` only after completing logical groups

### 5. Component Data Flow Changes

**Before (SPA)**:

```svelte
<script>
import { onMount } from 'svelte';
let campaigns = [];

onMount(async () => {
    const response = await api.get('/campaigns');
    campaigns = response.data;
});
</script>
```

**After (SSR)**:

```svelte
<script>
export let data; // From +page.server.ts
$: campaigns = data.campaigns;
</script>
```

### 6. Store Hydration Pattern

**Example**: @Projects store hydration

```typescript
// In +layout.server.ts or +page.server.ts
export const load = async () => {
    const projects = await getProjects();
    return { projects };
};

// In component
<script>
import { projectsStore } from '$lib/stores/projects';
export let data;

// Hydrate store from SSR data
$effect(() => {
    if (data.projects) {
        projectsStore.hydrate(data.projects);
    }
});
</script>
```

## Component Integration Patterns

### 1. Namespace Imports for Multi-Component Libraries

```typescript
// ✅ Correct pattern
import * as Accordion from '$lib/components/ui/accordion/index.js';
// Usage: <Accordion.Root><Accordion.Item>

// ❌ Avoid individual imports that may not exist
import { AccordionRoot } from '$lib/components/ui/accordion/root.js';
```

### 2. FileDropZone Integration

**Reference**: @Resource upload implementation

```svelte
<script lang="ts">
import { FileDropZone } from '@ieedan/shadcn-svelte-extras';

function handleFilesSelected(files: File[]) {
    // Process uploaded files
}

function handleFileRejected({ reason, file }: { reason: string; file: File }) {
    // Handle rejection
}
</script>

<FileDropZone
    onUpload={handleFilesSelected}
    onFileRejected={handleFileRejected}
    accept=".txt,.csv,.json"
    maxSize={10 * 1024 * 1024}
/>
```

### 3. JSRepo Component Integration

**Pattern**: Use JSRepo for Shadcn-Svelte-Extras components

```bash
# Check available components
just jsrepo-list

# Get specific component
just jsrepo-get @ieedan/shadcn-svelte-extras/ts/file-drop-zone
```

## SSR Error Handling Patterns

### 1. SSR Load Function Errors

```typescript
export const load: PageServerLoad = async ({ cookies }) => {
    try {
        const response = await serverApi.get('/api/v1/web/campaigns/');
        return { campaigns: response.data };
    } catch (err) {
        if (err.response?.status === 401) {
            throw redirect(302, '/login');
        }
        if (err.response?.status === 403) {
            throw error(403, 'Access denied');
        }
        throw error(500, 'Failed to load data');
    }
};
```

### 2. Form Action Error Handling

```typescript
export const actions: Actions = {
    default: async ({ request, cookies }) => {
        const form = await superValidate(request, zod(schema));

        if (!form.valid) {
            return fail(400, { form });
        }

        try {
            await serverApi.post('/api/v1/web/campaigns/', form.data);
            return redirect(303, '/campaigns');
        } catch (err) {
            return fail(500, {
                form,
                message: 'Creation failed'
            });
        }
    }
};
```

## Migration Verification

### Checklist for Route Migration

- [ ] `+page.server.ts` created with proper load function
- [ ] Environment detection implemented for tests
- [ ] Error handling covers auth, permissions, and server errors
- [ ] Component uses SSR data directly (not store calls)
- [ ] Store hydration only when reactive updates needed
- [ ] Tests updated to match SSR behavior
- [ ] Mock data matches API structure exactly

### Common Migration Issues

1. **Runtime errors from direct `$derived` exports** - Use store object pattern
2. **Test failures from SSR expectations** - Update test assertions
3. **Build errors from runes in `.ts` files** - Use `.svelte.ts` extensions
4. **Hydration mismatches** - Ensure SSR and client data consistency

## File References

- Migration plan: [spa_to_ssr.md](mdc:Ouroboros/Ouroboros/docs/v2_rewrite_implementation_plan/side_quests/spa_to_ssr.md)
- Store examples: [campaigns.svelte.ts](mdc:Ouroboros/Ouroboros/frontend/src/lib/stores/campaigns.svelte.ts)
- SSR load functions: [+page.server.ts](mdc:Ouroboros/Ouroboros/frontend/src/routes/campaigns/+page.server.ts)
- Component patterns: [+page.svelte](mdc:Ouroboros/Ouroboros/frontend/src/routes/campaigns/+page.svelte)
