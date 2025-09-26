---
inclusion: fileMatch
fileMatchPattern:
  - "frontend/src/**/*.test.ts"
  - "frontend/src/**/*.svelte"
  - "frontend/src/lib/stores/*.svelte.ts"
  - "frontend/vitest.config.ts"
---

# Ouroboros Frontend Testing Patterns

## SvelteKit 5 Testing Overview

Frontend testing in Ouroboros uses Vitest for unit testing and component testing with SvelteKit 5's runes system. This guide covers patterns specific to testing Svelte components, stores, and frontend logic.

## Vitest Configuration

Configure Vitest for SvelteKit 5 components with proper test environment setup:

```typescript
// vitest.config.ts
import { defineConfig } from "vitest/config";
import { sveltekit } from "@sveltejs/kit/vite";

export default defineConfig({
    plugins: [sveltekit()],
    test: {
        environment: "jsdom",
        setupFiles: ["./src/lib/test-setup.ts"],
        globals: true,
        coverage: {
            provider: "v8",
            reporter: ["text", "json", "html"],
            thresholds: {
                global: {
                    branches: 80,
                    functions: 80,
                    lines: 80,
                    statements: 80,
                },
            },
        },
    },
});
```

## SvelteKit 5 Store Testing with Runes

### Store Mocking Patterns

```typescript
// ✅ CORRECT - Mock .svelte.ts store files
vi.mock("$lib/stores/campaigns.svelte", () => ({
    campaignsStore: {
        get campaigns() {
            return [];
        },
        get loading() {
            return false;
        },
        get error() {
            return null;
        },
        hydrateCampaigns: vi.fn(),
        getCampaigns: vi.fn(),
    },
}));

// ❌ WRONG - Cannot test runes directly in .ts files
// Delete test files that try to test rune functionality directly
```

### Store Implementation Testing

```typescript
// ✅ CORRECT - Test store hydration methods with proper runes pattern
let campaignState = $state({
    campaigns: [],
    totalCount: 0,
    page: 1,
    loading: true,
});

export const campaignsStore = {
    // Hydration method for SSR data
    hydrateCampaigns(ssrData: CampaignListResponse) {
        campaignState.campaigns = ssrData.items;
        campaignState.totalCount = ssrData.total_count;
        campaignState.page = ssrData.page;
        campaignState.loading = false;
    },

    // Reactive getters
    get campaigns() {
        return campaignState.campaigns;
    },
    get loading() {
        return campaignState.loading;
    },
    get totalCount() {
        return campaignState.totalCount;
    },
};

// Test the hydration method
test("hydrateCampaigns updates store state correctly", () => {
    const mockData = {
        items: [{ id: 1, name: "Test Campaign" }],
        total_count: 1,
        page: 1,
        page_size: 10,
        total_pages: 1,
    };

    campaignsStore.hydrateCampaigns(mockData);

    expect(campaignsStore.campaigns).toEqual(mockData.items);
    expect(campaignsStore.totalCount).toBe(1);
    expect(campaignsStore.loading).toBe(false);
});
```

### Runtime Errors from Store Exports

```typescript
// ❌ PROBLEM - Direct $derived exports cause test failures
export const campaigns = $derived(campaignState.campaigns);

// ✅ SOLUTION - Use store object pattern or getter functions
export const campaignsStore = {
    get campaigns() {
        return campaignState.campaigns;
    },
};

// ✅ ALTERNATIVE - Use export function pattern
export function getCampaigns() {
    return campaignState.campaigns;
}
```

## Component Testing with SSR Data

### Mock Data Structure

```typescript
// ✅ CRITICAL - Mock data must match API structure exactly (snake_case, not camelCase)
import type { PageData } from "./$types";

const mockPageData: PageData = {
    campaigns: {
        items: [
            {
                id: 1,
                name: "Test Campaign",
                status: "active" as const, // Use exact enum values
                created_at: "2024-01-01T00:00:00Z",
                updated_at: "2024-01-01T00:00:00Z",
                description: "Test description",
            },
        ],
        total_count: 1, // Use snake_case as API returns
        page: 1,
        page_size: 10,
        total_pages: 1,
    },
};

render(CampaignsList, {
    props: { data: mockPageData },
});

// ❌ WRONG - Mismatched structure causes test failures
const mockCampaigns = {
    data: [...], // API doesn't return 'data' wrapper
    totalCount: 1 // API uses snake_case, not camelCase
};
```

### Component Test Structure

```typescript
// ✅ CORRECT - Comprehensive component test structure
import { render, screen } from "@testing-library/svelte";
import { expect, test, vi } from "vitest";
import CampaignCard from "./CampaignCard.svelte";

test("displays campaign information correctly", () => {
    const mockCampaign = {
        id: 1,
        name: "Test Campaign",
        status: "active" as const,
        progress: 75,
        created_at: "2024-01-01T00:00:00Z",
    };

    render(CampaignCard, { props: { campaign: mockCampaign } });

    expect(screen.getByText("Test Campaign")).toBeInTheDocument();
    expect(screen.getByText("Active")).toBeInTheDocument();
    expect(screen.getByText("75%")).toBeInTheDocument();
});
```

## SSR vs SPA Testing Patterns

### SSR Data Usage

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

### Load Function Testing

```typescript
// ✅ CORRECT - Robust load function with error handling
export const load: PageServerLoad = async ({ cookies, url, params }) => {
    // Environment detection for tests
    if (process.env.NODE_ENV === "test" || process.env.PLAYWRIGHT_TEST) {
        return { campaigns: mockCampaignData };
    }

    try {
        const response = await serverApi.get("/api/v1/web/campaigns/", {
            headers: { Cookie: cookies.get("sessionid") || "" },
        });

        return {
            campaigns: response.data,
            meta: {
                title: "Campaigns",
                description: "Manage your password cracking campaigns",
            },
        };
    } catch (error) {
        if (error.response?.status === 401) {
            throw redirect(302, "/login");
        }
        throw error(500, "Failed to load campaigns");
    }
};
```

### Store Hydration Testing

```typescript
// ✅ CORRECT - Test store hydration when reactive updates needed
$effect(() => {
    // Only hydrate if components will update this data
    if (needsReactiveUpdates) {
        campaignsStore.hydrateCampaigns(data.campaigns);
    }
});
```

## Form Testing with Superforms

### Superforms Mock Setup

```typescript
// ✅ CORRECT - Test form components with proper mock setup
import { superForm } from "sveltekit-superforms";
import { zodClient } from "sveltekit-superforms/adapters";

vi.mock("sveltekit-superforms", () => ({
    superForm: vi.fn(() => ({
        form: { subscribe: vi.fn() },
        errors: { subscribe: vi.fn() },
        enhance: vi.fn(),
        submitting: { subscribe: vi.fn() },
        delayed: { subscribe: vi.fn() },
        timeout: { subscribe: vi.fn() },
    })),
}));

test("form renders with correct fields", () => {
    const mockFormData = {
        name: "",
        description: "",
        project_id: null,
    };

    render(CampaignForm, { props: { data: { form: mockFormData } } });

    expect(screen.getByLabelText("Campaign Name")).toBeInTheDocument();
    expect(screen.getByLabelText("Description")).toBeInTheDocument();
});
```

### Form Validation Testing

```typescript
// ✅ CORRECT - Test form validation with Zod schemas
import { z } from "zod";

const campaignSchema = z.object({
    name: z.string().min(1, "Name is required"),
    description: z.string().optional(),
    project_id: z.number().positive("Project is required"),
});

test("form shows validation errors", async () => {
    render(CampaignForm, { props: { data: { form: {} } } });

    const submitButton = screen.getByText("Create Campaign");
    await fireEvent.click(submitButton);

    expect(screen.getByText("Name is required")).toBeInTheDocument();
    expect(screen.getByText("Project is required")).toBeInTheDocument();
});
```

## Event Handling Testing

### Component Events

```typescript
// ✅ CORRECT - Test component events and interactions
import { fireEvent } from "@testing-library/svelte";

test("emits delete event when delete button clicked", async () => {
    const component = render(CampaignCard, {
        props: { campaign: mockCampaign },
    });

    const deleteButton = screen.getByText("Delete");
    await fireEvent.click(deleteButton);

    // Test that the component emitted the expected event
    expect(component.component.$capture_state().onDelete).toHaveBeenCalledWith(
        1
    );
});
```

### User Interactions

```typescript
// ✅ CORRECT - Test user interactions with proper async handling
test("search input filters campaigns", async () => {
    render(CampaignsList, { props: { data: mockPageData } });

    const searchInput = screen.getByPlaceholderText("Search campaigns...");
    await fireEvent.input(searchInput, { target: { value: "test" } });

    // Wait for debounced search
    await vi.waitFor(() => {
        expect(screen.getByText("Test Campaign")).toBeInTheDocument();
    });
});
```

## Environment Detection

### Test Environment Setup

```typescript
// ✅ CORRECT - Comprehensive test environment detection
if (
    process.env.NODE_ENV === "test" ||
    process.env.PLAYWRIGHT_TEST ||
    process.env.CI
) {
    return { mockData };
}
```

### Mock API Responses

```typescript
// ✅ CORRECT - Mock API responses for frontend tests
vi.mock("$lib/api", () => ({
    api: {
        get: vi.fn().mockResolvedValue({
            data: {
                items: [mockCampaign],
                total_count: 1,
                page: 1,
                page_size: 10,
                total_pages: 1,
            },
        }),
        post: vi.fn().mockResolvedValue({ data: mockCampaign }),
        put: vi.fn().mockResolvedValue({ data: mockCampaign }),
        delete: vi.fn().mockResolvedValue({}),
    },
}));
```

## Frontend-Specific Anti-Patterns to Avoid

> [!NOTE]
> For general testing anti-patterns, see [testing-core.md](testing-core.md).

### Frontend Testing Anti-Patterns

```typescript
// ❌ WRONG - Testing runes directly in .ts files
test("campaigns rune updates correctly", () => {
    // This will fail - runes can't be tested outside component context
});

// ❌ WRONG - Using camelCase in mock data when API uses snake_case
const mockData = {
    totalCount: 1, // Should be total_count
    createdAt: "2024-01-01", // Should be created_at
};

// ❌ WRONG - Not mocking store dependencies
import { campaignsStore } from "$lib/stores/campaigns.svelte";
// This will cause runtime errors in tests

// ❌ WRONG - Testing implementation details instead of behavior
test("component has correct class names", () => {
    // Focus on user-visible behavior, not implementation
});
```

### Best Practices

```typescript
// ✅ CORRECT - Test user-visible behavior
test("displays loading state while fetching data", () => {
    render(CampaignsList, { props: { data: { campaigns: { items: [] } } } });
    expect(screen.getByText("Loading campaigns...")).toBeInTheDocument();
});

// ✅ CORRECT - Test component props and events
test("passes correct props to child components", () => {
    const mockCampaign = { id: 1, name: "Test" };
    render(CampaignCard, { props: { campaign: mockCampaign } });
    expect(screen.getByText("Test")).toBeInTheDocument();
});

// ✅ CORRECT - Test accessibility
test("form is accessible", () => {
    render(CampaignForm);
    expect(screen.getByLabelText("Campaign Name")).toBeInTheDocument();
    expect(
        screen.getByRole("button", { name: "Create Campaign" })
    ).toBeInTheDocument();
});
```

## Test Execution Commands

> [!NOTE]
> For complete test execution commands and development workflow, see [testing-core.md](testing-core.md).

### Frontend-Specific Commands

```bash
# Frontend unit tests only
just test-frontend

# Watch mode for development (from frontend/ directory)
pnpm test --watch

# Coverage report
pnpm test --coverage

# Specific test file
pnpm test src/lib/components/CampaignCard.test.ts
```

## Performance Considerations

### Test Performance

- Keep unit tests fast (< 100ms each)
- Mock external dependencies and API calls
- Use `vi.clearAllMocks()` in test setup
- Avoid testing implementation details

### Memory Management

```typescript
// ✅ CORRECT - Clean up after tests
afterEach(() => {
    vi.clearAllMocks();
    cleanup(); // From @testing-library/svelte
});
```

## Debugging Frontend Tests

### Common Issues

1. **Store runtime errors**: Always mock store dependencies
2. **SSR data mismatches**: Ensure mock data matches API structure exactly
3. **Async timing issues**: Use `vi.waitFor()` for async operations
4. **Component not rendering**: Check that all required props are provided

### Debug Strategies

```typescript
// ✅ CORRECT - Debug component state
test("debug component rendering", () => {
    const { debug } = render(CampaignCard, {
        props: { campaign: mockCampaign },
    });
    debug(); // Prints current DOM state

    // Or use screen.debug() for specific elements
    screen.debug(screen.getByText("Test Campaign"));
});
```
