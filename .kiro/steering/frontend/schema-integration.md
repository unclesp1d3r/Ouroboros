---
inclusion: fileMatch
fileMatchPattern:
  - frontend/**/*.ts
  - docs/v2_rewrite_implementation_plan/phase-3-web-ui-implementation/*.md
---

# Schema Integration and Type Safety Patterns

## Overview

This rule defines patterns for integrating Zod schemas with OpenAPI specifications, ensuring type safety across the frontend application while maintaining consistency with backend API contracts.

## Schema File Organization

### Directory Structure

```
src/lib/schemas/
├── index.ts                # Re-exports all schemas
├── auth.ts                 # Authentication schemas
├── campaigns.ts            # Campaign-related schemas
├── projects.ts             # Project management schemas
├── users.ts                # User management schemas
├── resources.ts            # Resource schemas
├── base.ts                 # Common types and enums
└── common.ts               # Shared utility schemas
```

### Schema Naming Conventions

- **Read schemas**: `EntityReadSchema` → `EntityRead` type
- **Create schemas**: `EntityCreateSchema` → `EntityCreate` type
- **Update schemas**: `EntityUpdateSchema` → `EntityUpdate` type
- **List responses**: `EntityListResponseSchema` → `EntityListResponse` type

## OpenAPI Compliance

### File Reference

The authoritative reference source for the schema files is the current backend OpenAPI contract specification documented in `contracts/current_api_openapi.json`.

### Schema Generation from OpenAPI

```typescript
// [x] CORRECT - Generate schemas that match OpenAPI exactly
import { z } from 'zod';

// Match OpenAPI specification exactly
export const CampaignReadSchema = z.object({
    id: z.number().int(),
    name: z.string(),
    description: z.string().nullable(),
    status: z.enum(['pending', 'running', 'paused', 'completed', 'failed']),
    priority: z.number().int().optional(), // Match OpenAPI optional fields
    created_at: z.string().datetime(),
    updated_at: z.string().datetime(),
    project_id: z.number().int(),
    hash_list_id: z.number().int().nullable(),
});

export type CampaignRead = z.infer<typeof CampaignReadSchema>;
```

### Pagination Schema Pattern

```typescript
// [x] CORRECT - Consistent pagination across all list responses
export const PaginationMetaSchema = z.object({
    total_count: z.number().int(),
    page: z.number().int(),
    page_size: z.number().int(),
    total_pages: z.number().int(),
});

export const CampaignListResponseSchema = z.object({
    items: z.array(CampaignReadSchema),
    ...PaginationMetaSchema.shape, // Spread pagination fields
});

export type CampaignListResponse = z.infer<typeof CampaignListResponseSchema>;
```

## Store Integration with Schemas

### API Response Parsing

```typescript
// [x] CORRECT - Parse all API responses with schemas
import { CampaignListResponseSchema } from '$lib/schemas/campaigns';

export const campaignsStore = {
    async loadCampaigns(page = 1) {
        try {
            const response = await api.get(`/api/v1/web/campaigns/?page=${page}`);

            // Always parse API responses
            const data = CampaignListResponseSchema.parse(response.data);
            this.hydrate(data);

        } catch (error) {
            if (error instanceof z.ZodError) {
                console.error('Schema validation failed:', error.errors);
                this.setError('Invalid data format received from server');
            } else {
                this.setError('Failed to load campaigns');
            }
        }
    }
};
```

### Form Data Validation

```typescript
// [x] CORRECT - Validate form data before API calls
import { CampaignCreateSchema } from '$lib/schemas/campaigns';

async createCampaign(formData: unknown) {
    try {
        // Validate form data against schema
        const validatedData = CampaignCreateSchema.parse(formData);

        const response = await api.post('/api/v1/web/campaigns/', validatedData);
        const newCampaign = CampaignReadSchema.parse(response.data);

        // Update store state
        campaignState.campaigns = [...campaignState.campaigns, newCampaign];
        return newCampaign;

    } catch (error) {
        if (error instanceof z.ZodError) {
            // Return validation errors for form display
            throw new ValidationError(error.errors);
        }
        throw error;
    }
}
```

## Type Adapter Patterns

### Creating UI-Specific Types

```typescript
// src/lib/types/campaign.ts
import type { CampaignRead } from '$lib/schemas/campaigns';

// [x] CORRECT - Extend schema types for UI needs
export interface CampaignItem extends CampaignRead {
    // Override optional fields to be required for UI consistency
    priority: number;           // Make required (was optional)
    is_unavailable: boolean;    // Make required (was optional)

    // Add UI-specific computed fields
    attacks: unknown[];
    progress: number;
    summary: string;
}

// [x] CORRECT - Transform function for schema to UI type
export function toCampaignItem(campaign: CampaignRead): CampaignItem {
    return {
        ...campaign,
        priority: campaign.priority ?? 0,
        is_unavailable: campaign.is_unavailable ?? false,
        attacks: [],
        progress: 0,
        summary: campaign.description || '',
    };
}
```

### Server-Side Type Transformations

```typescript
// +page.server.ts
import { CampaignListResponseSchema } from '$lib/schemas/campaigns';
import { toCampaignItem } from '$lib/types/campaign';

export const load: PageServerLoad = async ({ cookies }) => {
    const response = await serverApi.get('/api/v1/web/campaigns/');

    // Parse with schema first
    const campaignsData = CampaignListResponseSchema.parse(response.data);

    // Transform to UI types
    const transformedCampaigns = campaignsData.items.map(toCampaignItem);

    return {
        campaigns: {
            ...campaignsData,
            items: transformedCampaigns
        }
    };
};
```

## Enum and Constant Management

### Shared Enums

```typescript
// src/lib/schemas/base.ts
export const TaskStatusSchema = z.enum([
    'pending',
    'running',
    'paused',
    'completed',
    'failed',
    'abandoned'
]);

export type TaskStatus = z.infer<typeof TaskStatusSchema>;

// Export for use in components
export const TASK_STATUS_OPTIONS = TaskStatusSchema.options;
```

### Component Usage of Enums

```svelte
<script lang="ts">
    import { TASK_STATUS_OPTIONS, type TaskStatus } from '$lib/schemas/base';

    let { status }: { status: TaskStatus } = $props();

    function getStatusColor(status: TaskStatus) {
        switch (status) {
            case 'running': return 'bg-green-600';
            case 'completed': return 'bg-blue-600';
            case 'failed': return 'bg-red-600';
            case 'pending': return 'bg-yellow-500';
            default: return 'bg-gray-400';
        }
    }
</script>

<select bind:value={status}>
    {#each TASK_STATUS_OPTIONS as option}
        <option value={option}>{option}</option>
    {/each}
</select>
```

## Error Handling with Schemas

### Validation Error Processing

```typescript
// [x] CORRECT - Process Zod validation errors for UI display
export function processValidationErrors(error: z.ZodError): Record<string, string> {
    const fieldErrors: Record<string, string> = {};

    error.errors.forEach((err) => {
        const fieldPath = err.path.join('.');
        fieldErrors[fieldPath] = err.message;
    });

    return fieldErrors;
}

// Usage in form handling
try {
    const validatedData = CampaignCreateSchema.parse(formData);
    // ... proceed with API call
} catch (error) {
    if (error instanceof z.ZodError) {
        const fieldErrors = processValidationErrors(error);
        setFormErrors(fieldErrors);
    }
}
```

### Schema Evolution Handling

```typescript
// [x] CORRECT - Handle schema version compatibility
export const CampaignReadSchemaV1 = z.object({
    // Original schema fields
    id: z.number(),
    name: z.string(),
    // ... other fields
});

export const CampaignReadSchemaV2 = CampaignReadSchemaV1.extend({
    // New fields in v2
    tags: z.array(z.string()).optional(),
    metadata: z.record(z.unknown()).optional(),
});

// Use union for backward compatibility
export const CampaignReadSchema = z.union([
    CampaignReadSchemaV2,
    CampaignReadSchemaV1
]);
```

## Testing Schema Integration

### Mock Data with Schemas

```typescript
// [x] CORRECT - Generate mock data that validates against schemas
import { CampaignReadSchema } from '$lib/schemas/campaigns';

export function createMockCampaign(overrides: Partial<CampaignRead> = {}): CampaignRead {
    const mockData = {
        id: 1,
        name: 'Test Campaign',
        description: 'Test description',
        status: 'active' as const,
        priority: 1,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
        project_id: 1,
        hash_list_id: 1,
        ...overrides
    };

    // Validate mock data against schema
    return CampaignReadSchema.parse(mockData);
}
```

### Schema Validation Tests

```typescript
// [x] CORRECT - Test schema validation behavior
import { describe, it, expect } from 'vitest';
import { CampaignCreateSchema } from '$lib/schemas/campaigns';

describe('CampaignCreateSchema', () => {
    it('validates correct campaign data', () => {
        const validData = {
            name: 'Test Campaign',
            description: 'Test description',
            project_id: 1,
            hash_list_id: 1
        };

        expect(() => CampaignCreateSchema.parse(validData)).not.toThrow();
    });

    it('rejects invalid campaign data', () => {
        const invalidData = {
            name: '', // Empty name should fail
            project_id: 'invalid' // Wrong type
        };

        expect(() => CampaignCreateSchema.parse(invalidData)).toThrow();
    });
});
```

## Performance Considerations

### Schema Parsing Optimization

```typescript
// [x] CORRECT - Cache parsed schemas for repeated use
const schemaCache = new Map<string, unknown>();

export function cachedParse<T>(schema: z.ZodSchema<T>, data: unknown, key: string): T {
    if (schemaCache.has(key)) {
        return schemaCache.get(key) as T;
    }

    const parsed = schema.parse(data);
    schemaCache.set(key, parsed);
    return parsed;
}
```

### Selective Parsing

```typescript
// [x] CORRECT - Parse only necessary fields for performance
export const CampaignSummarySchema = CampaignReadSchema.pick({
    id: true,
    name: true,
    status: true,
    updated_at: true
});

// Use for list views where full data isn't needed
export type CampaignSummary = z.infer<typeof CampaignSummarySchema>;
```

## Best Practices Summary

1. **Always validate API responses** with Zod schemas
2. **Match OpenAPI specifications exactly** in schema definitions
3. **Use type adapters** to bridge schema types with UI requirements
4. **Handle validation errors gracefully** with user-friendly messages
5. **Create mock data** that validates against schemas
6. **Test schema validation behavior** explicitly
7. **Cache parsed results** for performance when appropriate
8. **Use selective parsing** for performance-critical operations

## Anti-Patterns to Avoid

### Direct Type Assertions

```typescript
// [FAIL] WRONG - Never use type assertions without validation
const campaign = response.data as CampaignRead;

// [x] CORRECT - Always validate with schemas
const campaign = CampaignReadSchema.parse(response.data);
```

### Schema Mutations

```typescript
// [FAIL] WRONG - Don't modify schemas after creation
CampaignReadSchema.shape.newField = z.string();

// [x] CORRECT - Extend or compose schemas
const ExtendedCampaignSchema = CampaignReadSchema.extend({
    newField: z.string()
});
```

### Inconsistent Error Handling

```typescript
// [FAIL] WRONG - Inconsistent error handling
try {
    const data = schema.parse(input);
} catch (e) {
    console.log('Error'); // Too generic
}

// [x] CORRECT - Specific error handling
try {
    const data = schema.parse(input);
} catch (error) {
    if (error instanceof z.ZodError) {
        handleValidationErrors(error);
    } else {
        handleUnknownError(error);
    }
}
```

## File References

- Schema definitions: [campaigns.ts](mdc:Ouroboros/Ouroboros/frontend/src/lib/schemas/campaigns.ts)
- Type adapters: [campaign.ts](mdc:Ouroboros/Ouroboros/frontend/src/lib/types/campaign.ts)
- Store integration: [campaigns.svelte.ts](mdc:Ouroboros/Ouroboros/frontend/src/lib/stores/campaigns.svelte.ts)
- OpenAPI contract: [current_api_openapi.json](mdc:Ouroboros/Ouroboros/contracts/current_api_openapi.json)
