---

## inclusion: fileMatch fileMatchPattern: \[frontend/src/lib/stores/\*\*/*, docs/v2_rewrite_implementation_plan/phase-3-web-ui-implementation/*.md\]

# SvelteKit 5 Store Implementation Patterns

## Overview

This rule defines idiomatic patterns for implementing stores in SvelteKit 5 using runes, based on successful implementations in the Ouroboros project. These patterns ensure type safety, proper SSR integration, and maintainable reactive state management.

## File Structure and Naming

### Store File Extensions

- **MUST use `.svelte.ts` extension** for all store files that use runes
- **CANNOT use regular `.ts` files** with runes - causes build errors
- Examples: `campaigns.svelte.ts`, `auth.svelte.ts`, `projects.svelte.ts`

### Store Organization

```
src/lib/stores/
├── auth.svelte.ts          # Authentication state
├── campaigns.svelte.ts     # Campaign management
├── projects.svelte.ts      # Project management
├── users.svelte.ts         # User management
└── resources.svelte.ts     # Resource management
```

## Core Store Pattern

### State Management with Runes

```typescript
// ✅ CORRECT - State object wrapper for complex state
const campaignState = $state({
    campaigns: [] as Campaign[],
    totalCount: 0,
    page: 1,
    pageSize: 10,
    loading: false,
    error: null as string | null
});

// ✅ CORRECT - Derived values for computed state
const filteredCampaigns = $derived(
    campaignState.campaigns.filter(c => c.status === 'active')
);
```

### Store Object Export Pattern

```typescript
// ✅ CORRECT - Export store object with getters and methods
export const campaignsStore = {
    // Reactive getters - DO NOT export $derived directly
    get campaigns() { return campaignState.campaigns; },
    get loading() { return campaignState.loading; },
    get error() { return campaignState.error; },
    get totalCount() { return campaignState.totalCount; },

    // Computed getters using derived values
    get filteredCampaigns() { return filteredCampaigns; },

    // State management methods
    setCampaigns(campaigns: Campaign[]) {
        campaignState.campaigns = campaigns;
        campaignState.loading = false;
    },

    setLoading(loading: boolean) {
        campaignState.loading = loading;
    },

    setError(error: string | null) {
        campaignState.error = error;
    },

    // SSR hydration method
    hydrate(data: CampaignListResponse) {
        this.setCampaigns(data.items);
        campaignState.totalCount = data.total_count;
        campaignState.page = data.page;
    },

    // API methods with proper error handling
    async loadCampaigns(page = 1) {
        this.setLoading(true);
        this.setError(null);

        try {
            const response = await api.get(`/api/v1/web/campaigns/?page=${page}`);
            const data = CampaignListResponseSchema.parse(response.data);
            this.hydrate(data);
        } catch (error) {
            this.setError('Failed to load campaigns');
            console.error('Campaign loading error:', error);
        }
    }
};
```

## Schema Integration

### Type-Safe API Calls

```typescript
import { CampaignListResponseSchema, CampaignCreateSchema } from '$lib/schemas/campaigns';

// ✅ CORRECT - Parse API responses with Zod schemas
async loadCampaigns() {
    try {
        const response = await api.get('/api/v1/web/campaigns/');
        const data = CampaignListResponseSchema.parse(response.data);
        this.hydrate(data);
    } catch (error) {
        if (error instanceof z.ZodError) {
            this.setError('Invalid data format received');
        } else {
            this.setError('Failed to load campaigns');
        }
    }
}
```

### Schema Validation in Store Methods

```typescript
// ✅ CORRECT - Validate input data before state updates
async createCampaign(campaignData: unknown) {
    try {
        const validatedData = CampaignCreateSchema.parse(campaignData);
        const response = await api.post('/api/v1/web/campaigns/', validatedData);
        const newCampaign = CampaignReadSchema.parse(response.data);

        campaignState.campaigns = [...campaignState.campaigns, newCampaign];
        return newCampaign;
    } catch (error) {
        if (error instanceof z.ZodError) {
            throw new Error('Invalid campaign data');
        }
        throw error;
    }
}
```

## SSR Integration Patterns

### Component Usage with SSR Data

```svelte
<!-- ✅ CORRECT - Use SSR data directly in pages -->
<script lang="ts">
    import type { PageData } from './$types';
    import { campaignsStore } from '$lib/stores/campaigns.svelte';

    let { data }: { data: PageData } = $props();

    // Use SSR data directly for initial render
    let campaigns = $derived(data.campaigns.items);
    let totalCount = $derived(data.campaigns.total_count);

    // Only hydrate store if components need reactive updates
    $effect(() => {
        if (needsReactiveUpdates) {
            campaignsStore.hydrate(data.campaigns);
        }
    });
</script>
```

### Load Function Integration

```typescript
// +page.server.ts
export const load: PageServerLoad = async ({ cookies }) => {
    try {
        const response = await serverApi.get('/api/v1/web/campaigns/', {
            headers: { Cookie: cookies.toString() }
        });

        return {
            campaigns: response.data,
            meta: {
                title: 'Campaigns',
                description: 'Manage your campaigns'
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

## Authentication Store Pattern

### JWT Token Management

```typescript
const authState = $state({
    user: null as User | null,
    token: null as string | null,
    isAuthenticated: false,
    loading: false
});

export const authStore = {
    get user() { return authState.user; },
    get isAuthenticated() { return authState.isAuthenticated; },
    get isAdmin() { return authState.user?.role === 'admin'; },
    get loading() { return authState.loading; },

    async login(credentials: LoginCredentials) {
        authState.loading = true;
        try {
            const response = await api.post('/api/v1/auth/login/', credentials);
            const data = LoginResponseSchema.parse(response.data);

            authState.user = data.user;
            authState.token = data.access_token;
            authState.isAuthenticated = true;

            // Store in secure cookie
            document.cookie = `access_token=${data.access_token}; secure; samesite=strict`;
        } finally {
            authState.loading = false;
        }
    },

    logout() {
        authState.user = null;
        authState.token = null;
        authState.isAuthenticated = false;
        document.cookie = 'access_token=; expires=Thu, 01 Jan 1970 00:00:00 GMT';
    }
};
```

## Error Handling Patterns

### Consistent Error Management

```typescript
// ✅ CORRECT - Consistent error handling across stores
const handleApiError = (error: unknown, context: string) => {
    if (error instanceof z.ZodError) {
        return `Invalid data format in ${context}`;
    }
    if (error?.response?.status === 401) {
        authStore.logout();
        return 'Authentication required';
    }
    if (error?.response?.status === 403) {
        return 'Access denied';
    }
    return `Failed to ${context}`;
};

// Usage in store methods
async loadCampaigns() {
    try {
        // ... API call
    } catch (error) {
        const errorMessage = handleApiError(error, 'load campaigns');
        this.setError(errorMessage);
    }
}
```

## Testing Patterns

### Store Testing with Mocks

```typescript
// ✅ CORRECT - Mock .svelte.ts store files in tests
vi.mock('$lib/stores/campaigns.svelte', () => ({
    campaignsStore: {
        get campaigns() { return []; },
        get loading() { return false; },
        get error() { return null; },
        hydrate: vi.fn(),
        loadCampaigns: vi.fn()
    }
}));
```

### Component Testing with Store Integration

```typescript
test('component uses store data correctly', () => {
    const mockStore = {
        campaigns: [{ id: 1, name: 'Test Campaign' }],
        loading: false,
        error: null
    };

    vi.mocked(campaignsStore).campaigns = mockStore.campaigns;

    render(CampaignsList);
    expect(screen.getByText('Test Campaign')).toBeInTheDocument();
});
```

## Anti-Patterns to Avoid

### Direct Rune Exports

```typescript
// ❌ WRONG - Never export $derived directly
export const campaigns = $derived(campaignState.campaigns);

// ❌ WRONG - Never export $state directly
export const campaignState = $state({ campaigns: [] });
```

### Mixing Store and SSR Data

```svelte
<!-- ❌ WRONG - Don't mix SSR data with store calls -->
<script>
    export let data: PageData;
    import { getCampaigns } from '$lib/stores/campaigns.svelte';

    // This creates confusion about data source
    let campaigns = $derived(getCampaigns());
</script>
```

### Improper File Extensions

```typescript
// ❌ WRONG - Using .ts extension with runes
// campaigns.ts
const state = $state({}); // This will cause build errors
```

## Migration Guidelines

### From Svelte 4 Stores

1. **Rename files** from `.ts` to `.svelte.ts`
2. **Replace writable/readable** with `$state`
3. **Replace derived** with `$derived`
4. **Update exports** to use store object pattern
5. **Update all imports** to use new file paths
6. **Update tests** to mock new store structure

### Component Updates

1. **Remove store subscriptions** (`$store` syntax)
2. **Use direct store access** (`store.property`)
3. **Update reactive statements** to use `$derived`
4. **Fix import paths** for renamed store files

## Performance Considerations

### Efficient State Updates

```typescript
// ✅ CORRECT - Batch related state updates
updateCampaignData(campaigns: Campaign[], totalCount: number) {
    // Single reactive update
    Object.assign(campaignState, {
        campaigns,
        totalCount,
        loading: false,
        error: null
    });
}
```

### Selective Reactivity

```typescript
// ✅ CORRECT - Use derived for expensive computations
const expensiveComputation = $derived(() => {
    return campaignState.campaigns
        .filter(c => c.status === 'active')
        .map(c => ({ ...c, computed: heavyCalculation(c) }));
});
```

## Best Practices Summary

1. **Always use `.svelte.ts` extension** for rune-based stores
2. **Export store objects with getters**, never direct rune values
3. **Use SSR data directly in pages** when possible
4. **Hydrate stores only when reactive updates are needed**
5. **Parse all API responses with Zod schemas**
6. **Handle errors consistently across all stores**
7. **Test stores through component integration**
8. **Update all import paths when migrating files**

## File References

- Store implementations: [campaigns.svelte.ts](mdc:Ouroboros/Ouroboros/frontend/src/lib/stores/campaigns.svelte.ts)
- Authentication store: [auth.svelte.ts](mdc:Ouroboros/Ouroboros/frontend/src/lib/stores/auth.svelte.ts)
- Schema integration: [campaigns.ts](mdc:Ouroboros/Ouroboros/frontend/src/lib/schemas/campaigns.ts)
- Component usage: [CampaignProgress.svelte](mdc:Ouroboros/Ouroboros/frontend/src/lib/components/campaigns/CampaignProgress.svelte)
