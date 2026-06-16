---
inclusion: fileMatch
fileMatchPattern:
  - frontend/**/*.ts
  - frontend/**/*.svelte
  - frontend/**/*.js
---

# Ouroboros Frontend Development Guide

# Ouroboros Frontend Development Guide

## Technology Stack

- **Framework**: SvelteKit 2+ with TypeScript and SSR
- **UI Components**: Shadcn-Svelte, Bits UI, Flowbite Svelte
- **Styling**: TailwindCSS 4+
- **Validation**: Zod schemas with Superforms
- **HTTP Client**: Axios for API communication
- **Build Tool**: Vite 7+

## Schema Integration and Type Safety

### Schema Organization

```
src/lib/schemas/
├── index.ts        # Re-exports all schemas
├── auth.ts         # Authentication schemas
├── campaigns.ts    # Campaign-related schemas
├── projects.ts     # Project management schemas
├── users.ts        # User management schemas
└── base.ts         # Common types and enums
```

### OpenAPI Compliance

- **Reference**: `contracts/current_api_openapi.json` is the authoritative source
- **Schema Generation**: Generate Zod schemas that match OpenAPI exactly
- **Naming**: `EntityReadSchema` → `EntityRead` type, `EntityCreateSchema` → `EntityCreate` type

```typescript
// [x] CORRECT - Match OpenAPI specification exactly
export const CampaignReadSchema = z.object({
    id: z.number().int(),
    name: z.string(),
    status: z.enum(["pending", "running", "paused", "completed", "failed"]),
    created_at: z.string().datetime(),
    project_id: z.number().int(),
});

export type CampaignRead = z.infer<typeof CampaignReadSchema>;
```

### API Response Validation

```typescript
// [x] CORRECT - Always parse API responses with schemas
try {
    const response = await api.get("/api/v1/web/campaigns/");
    const data = CampaignListResponseSchema.parse(response.data);
    return data;
} catch (error) {
    if (error instanceof z.ZodError) {
        console.error("Schema validation failed:", error.errors);
    }
    throw error;
}
```

## SSR Authentication Patterns

### Server-Side Load Functions

```typescript
// +page.server.ts
export const load: PageServerLoad = async ({ cookies }) => {
    const sessionCookie = cookies.get("sessionid");

    if (!sessionCookie) {
        throw redirect(302, "/login");
    }

    try {
        const response = await serverApi.get("/api/v1/web/campaigns/", {
            headers: { Cookie: `sessionid=${sessionCookie}` },
        });
        return { campaigns: response.data };
    } catch (error) {
        if (error.response?.status === 401) {
            throw redirect(302, "/login");
        }
        throw error(500, "Failed to load data");
    }
};
```

### Session Management

```javascript
// hooks.server.js
export async function handle({
    event,
    resolve
}) {
    const sessionCookie = event.cookies.get("sessionid");

    if (sessionCookie) {
        event.locals.session = sessionCookie;
        event.locals.user = await validateSession(sessionCookie);
    }

    return resolve(event);
}
```

## Component Development

### Svelte 5 Patterns

```svelte
<script lang="ts">
    import type { CampaignRead } from '$lib/schemas/campaigns';

    // Use $props() for component props
    let { campaign }: { campaign: CampaignRead } = $props();

    // Use $state() for reactive state
    let isLoading = $state(false);

    // Use $derived() for computed values
    let statusColor = $derived(() => {
        switch (campaign.status) {
            case 'running': return 'bg-green-600';
            case 'completed': return 'bg-blue-600';
            case 'failed': return 'bg-red-600';
            default: return 'bg-gray-400';
        }
    });
</script>
```

### UI Component Usage

- **Primary**: Use Shadcn-Svelte components from `@ieedan/shadcn-svelte-extras`
- **Check jsrepo.json**: Use pinned versions when specified
- **Fallback**: Flowbite Svelte for additional components
- **Styling**: TailwindCSS for custom styling

## Server-Sent Events (SSE)

### Backend SSE Implementation

```python
# [x] CORRECT - Use proper SSE media type
@router.get("/live/campaigns")
async def get_campaign_events():
    return StreamingResponse(
        event_service.get_campaign_events(),
        media_type="text/event-stream",  # Critical: Must be text/event-stream
    )
```

### Frontend SSE Service

```typescript
export class SSEService {
    private connections = new Map<string, EventSource>();

    connect(endpoint: string, onMessage: (event: any) => void): void {
        const eventSource = new EventSource(endpoint, {
            withCredentials: true, // Include cookies for authentication
        });

        eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.trigger !== "ping") {
                // Filter keepalive pings
                onMessage(data);
            }
        };

        this.connections.set(endpoint, eventSource);
    }
}
```

## Form Handling with Superforms

### Form Setup

```typescript
// +page.server.ts
export const actions: Actions = {
    default: async ({ request }) => {
        const form = await superValidate(request, zod(campaignCreateSchema));

        if (!form.valid) {
            return fail(400, { form });
        }

        try {
            const validatedData = CampaignCreateSchema.parse(form.data);
            // Process form data
            return { form };
        } catch (error) {
            return fail(500, { form, message: "Creation failed" });
        }
    },
};
```

### Form Component

```svelte
<script lang="ts">
    import { superForm } from 'sveltekit-superforms';
    import { zod } from 'sveltekit-superforms/adapters';

    let { data } = $props();

    const { form, errors, enhance } = superForm(data.form, {
        validators: zod(campaignCreateSchema)
    });
</script>

<form method="POST" use:enhance>
    <input bind:value={$form.name} />
    {#if $errors.name}<span class="error">{$errors.name}</span>{/if}
    <button type="submit">Create Campaign</button>
</form>
```

## Error Handling

### Validation Errors

```typescript
function processValidationErrors(error: z.ZodError): Record<string, string> {
    const fieldErrors: Record<string, string> = {};

    error.errors.forEach((err) => {
        const fieldPath = err.path.join(".");
        fieldErrors[fieldPath] = err.message;
    });

    return fieldErrors;
}
```

### API Error Handling

```typescript
try {
    const data = await api.post("/api/v1/web/campaigns/", payload);
    return CampaignReadSchema.parse(data);
} catch (error) {
    if (error instanceof z.ZodError) {
        throw new ValidationError(processValidationErrors(error));
    }
    if (error.response?.status === 401) {
        throw redirect(302, "/login");
    }
    throw error;
}
```

## Testing Patterns

### Component Testing

```typescript
import { render, screen } from "@testing-library/svelte";
import { createMockCampaign } from "$lib/test-utils";

test("renders campaign card", () => {
    const campaign = createMockCampaign();
    render(CampaignCard, { props: { campaign } });

    expect(screen.getByText(campaign.name)).toBeInTheDocument();
});
```

### Mock Data Generation

```typescript
export function createMockCampaign(
    overrides: Partial<CampaignRead> = {}
): CampaignRead {
    const mockData = {
        id: 1,
        name: "Test Campaign",
        status: "active" as const,
        created_at: "2024-01-01T00:00:00Z",
        project_id: 1,
        ...overrides,
    };

    return CampaignReadSchema.parse(mockData);
}
```

## Best Practices

### Code Organization

- **Routes**: Mirror API structure in `src/routes/`
- **Components**: Reusable components in `src/lib/components/`
- **Stores**: State management in `src/lib/stores/`
- **Services**: API clients in `src/lib/services/`
- **Types**: Generated types in `src/lib/types/`

### Performance

- **Lazy Loading**: Use dynamic imports for large components
- **Schema Caching**: Cache parsed schemas for repeated use
- **SSR Optimization**: Minimize client-side hydration

### Security

- **Input Validation**: Always validate with Zod schemas
- **Authentication**: Use session cookies for SSR
- **CSRF Protection**: Implement CSRF tokens for forms
- **XSS Prevention**: Sanitize user input

## Anti-Patterns to Avoid

- [FAIL] Using type assertions without schema validation
- [FAIL] Direct API calls without error handling
- [FAIL] Hardcoded API endpoints
- [FAIL] Missing authentication in SSR load functions
- [FAIL] Using `text/plain` instead of `text/event-stream` for SSE
- [FAIL] Not cleaning up EventSource connections
- [FAIL] Bypassing Zod validation for performance

## File References

- OpenAPI Contract: `contracts/current_api_openapi.json`
- Schema Definitions: `frontend/src/lib/schemas/`
- Component Library: `frontend/src/lib/components/`
- SSR Authentication: `frontend/src/hooks.server.js`
