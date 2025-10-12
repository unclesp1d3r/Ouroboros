# Frontend Development Guide

This guide covers frontend development for Ouroboros's SvelteKit application, including the new configuration system, development patterns, and best practices.

## Table of Contents

1. [Frontend Architecture](#1-frontend-architecture)
2. [Configuration System](#2-configuration-system)
3. [Development Setup](#3-development-setup)
4. [Component Architecture](#4-component-architecture)
5. [Form Handling with Superforms](#5-form-handling-with-superforms)
6. [API Integration](#6-api-integration)
7. [Testing](#7-testing)
8. [Build and Deployment](#8-build-and-deployment)
9. [Best Practices](#9-best-practices)

---

## 1. Frontend Architecture

### Technology Stack

- **Framework**: SvelteKit with SSR (Server-Side Rendering)
- **Adapter**: `@sveltejs/adapter-node` for production deployment
- **UI Components**: Shadcn-Svelte + Flowbite
- **Forms**: Superforms v2 with Formsnap
- **Validation**: Zod schemas
- **Styling**: Tailwind CSS
- **Package Manager**: pnpm

### Project Structure

```text
frontend/
├── src/
│   ├── lib/
│   │   ├── components/          # Reusable UI components
│   │   │   ├── ui/             # Shadcn-Svelte components
│   │   │   ├── agents/         # Agent-specific components
│   │   │   ├── attacks/        # Attack-specific components
│   │   │   ├── campaigns/      # Campaign-specific components
│   │   │   └── layout/         # Layout components
│   │   ├── config/             # Configuration system
│   │   ├── stores/             # Svelte stores
│   │   ├── types/              # TypeScript type definitions
│   │   └── utils/              # Utility functions
│   ├── routes/                 # SvelteKit routes
│   │   ├── +layout.svelte      # Root layout
│   │   ├── +page.svelte        # Dashboard
│   │   ├── campaigns/          # Campaign routes
│   │   ├── attacks/            # Attack routes
│   │   └── agents/             # Agent routes
│   └── app.html                # HTML template
├── static/                     # Static assets
├── tests/                      # Test files
├── package.json                # Dependencies
├── vite.config.js              # Vite configuration
├── tailwind.config.js          # Tailwind configuration
└── svelte.config.js            # SvelteKit configuration
```

### Migration from SPA to SSR

Ouroboros is transitioning from a Static SPA to a full SSR application:

- **Before**: `adapter-static` with `fallback: 'index.html'`
- **After**: `adapter-node` with full SSR capabilities
- **Benefits**: Better SEO, faster initial page loads, working deep links, progressive enhancement

---

## 2. Configuration System

### Overview

The configuration system provides type-safe, environment-aware configuration for both server-side and client-side code. It handles the complexity of SvelteKit's dual environment (server/browser) and provides a clean API for accessing configuration values.

### Configuration Files

#### Environment Files

```bash
# frontend/.env.example (template)
VITE_API_BASE_URL=http://localhost:8000
PUBLIC_API_BASE_URL=http://localhost:8000
VITE_APP_NAME=Ouroboros
VITE_APP_VERSION=2.0.0
VITE_DEBUG=false
VITE_ENABLE_EXPERIMENTAL_FEATURES=false
VITE_TOKEN_EXPIRE_MINUTES=60

# Private environment variables (server-side only)
API_BASE_URL=http://app:8000
SESSION_SECRET=your-session-secret
```

```bash
# frontend/.env (local development)
VITE_API_BASE_URL=http://localhost:8000
PUBLIC_API_BASE_URL=http://localhost:8000
VITE_APP_NAME=Ouroboros
VITE_APP_VERSION=2.0.0
VITE_DEBUG=true
VITE_ENABLE_EXPERIMENTAL_FEATURES=true
VITE_TOKEN_EXPIRE_MINUTES=60

API_BASE_URL=http://localhost:8000
SESSION_SECRET=dev-session-secret
```

#### Configuration Schema

```typescript
// frontend/src/lib/config/index.ts
export interface AppConfig {
  /** Backend API base URL for server-side requests */
  apiBaseUrl: string;
  /** Public API base URL for client-side requests */
  publicApiBaseUrl: string;
  /** JWT token expiration time in minutes */
  tokenExpireMinutes: number;
  /** Enable debug mode */
  debug: boolean;
  /** Application name */
  appName: string;
  /** Application version */
  appVersion: string;
  /** Enable experimental features */
  enableExperimentalFeatures: boolean;
}
```

### Usage Examples

#### Basic Configuration Access

```typescript
import { config, getApiBaseUrl, isDevelopment, isExperimentalEnabled } from '$lib/config';

// Access configuration directly
console.log(config.appName); // "Ouroboros"
console.log(config.appVersion); // "2.0.0"

// Use utility functions
const apiUrl = getApiBaseUrl(); // "http://localhost:8000"
const isDev = isDevelopment(); // true in development
const hasExperimentalFeatures = isExperimentalEnabled(); // false by default
```

#### In SvelteKit Routes

```typescript
// +page.server.ts (server-side)
import { config } from '$lib/config';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async () => {
  // Use server-side API URL for server-to-server communication
  const response = await fetch(`${config.apiBaseUrl}/api/v1/web/campaigns`);

  return {
    campaigns: await response.json()
  };
};
```

```svelte
<!-- +page.svelte (client-side) -->
<script lang="ts">
  import { getApiUrl, isDevelopment } from '$lib/config';

  // Use public URL for client-side requests
  const apiUrl = getApiUrl('/api/v1/web/campaigns');

  // Conditional features based on environment
  const showDebugInfo = isDevelopment();
</script>

{#if showDebugInfo}
  <div class="debug-panel">
    API URL: {apiUrl}
  </div>
{/if}
```

### Environment Variable Conventions

#### Public Variables (VITE_prefix and PUBLIC\_ prefix)

Available in both server and browser environments:

- `VITE_API_BASE_URL`: Base URL for API calls (fallback for server-side)
- `PUBLIC_API_BASE_URL`: Public API base URL for client-side requests
- `VITE_APP_NAME`: Application name
- `VITE_APP_VERSION`: Application version
- `VITE_DEBUG`: Enable debug mode
- `VITE_ENABLE_EXPERIMENTAL_FEATURES`: Enable experimental features
- `VITE_TOKEN_EXPIRE_MINUTES`: JWT token expiration time in minutes

#### Private Variables (no prefix)

Available only on the server:

- `API_BASE_URL`: Internal API URL for server-to-server communication
- `SESSION_SECRET`: Secret for session encryption
- `DATABASE_URL`: Database connection string (if needed)

### Configuration Validation

The configuration system includes automatic runtime validation that runs when the module is imported:

```typescript
// Validation happens automatically on import
import { config } from '$lib/config'; // Will throw if configuration is invalid

// The system validates:
// - API URLs are valid URLs
// - Token expiration is positive
// - App name is not empty
// - All required fields are present
```

### Key Features

#### Dual Environment Support

The configuration system automatically detects whether it's running in a browser or server environment:

- **Server-side**: Uses private environment variables (`API_BASE_URL`) for internal communication
- **Client-side**: Uses public environment variables (`PUBLIC_API_BASE_URL`) for browser requests
- **Automatic fallback**: If `PUBLIC_API_BASE_URL` is not set, falls back to `VITE_API_BASE_URL`

#### Type Safety

All configuration values are strongly typed with TypeScript interfaces and include JSDoc documentation for better IDE support.

#### Environment Variable Precedence

The system follows a clear precedence order for environment variables:

1. Specific environment variables (e.g., `API_BASE_URL`)
2. Vite public variables (e.g., `VITE_API_BASE_URL`)
3. Default values defined in the configuration

#### Utility Functions

Pre-built utility functions handle common configuration needs:

- `getApiBaseUrl()`: Returns the correct API URL for the current environment
- `getApiUrl(endpoint)`: Builds full API URLs with proper base URL
- `isDevelopment()`: Detects development mode
- `isExperimentalEnabled()`: Checks if experimental features are enabled

### Testing Configuration

```typescript
// config.spec.ts
import { describe, it, expect, vi } from 'vitest';
import { config, getApiBaseUrl, isDevelopment } from '$lib/config';

describe('Configuration', () => {
  it('loads default configuration', () => {
    expect(config.appName).toBe('Ouroboros');
    expect(config.appVersion).toBe('2.0.0');
  });

  it('provides utility functions', () => {
    const apiUrl = getApiBaseUrl();
    expect(apiUrl).toBe('http://localhost:8000');

    const isDev = isDevelopment();
    expect(typeof isDev).toBe('boolean');
  });

  it('respects environment variables', () => {
    vi.stubEnv('VITE_API_BASE_URL', 'https://api.example.com');
    // Note: Configuration is loaded at module import time
    // For testing env changes, you may need to mock the entire module
  });
});
```

---

## 3. Development Setup

### Prerequisites

- Node.js 18+ and pnpm
- Backend API running on `http://localhost:8000`

### Initial Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
pnpm install

# Copy environment file
cp .env.example .env

# Start development server
pnpm dev
```

### Development Commands

```bash
# Development server with hot reload
pnpm dev

# Build for production
pnpm build

# Preview production build
pnpm preview

# Run tests
pnpm test

# Run tests with UI
pnpm test:ui

# Run E2E tests
pnpm test:e2e

# Type checking
pnpm check

# Linting
pnpm lint

# Format code
pnpm format
```

### VS Code Configuration

Create `.vscode/settings.json` in the frontend directory:

```json
{
  "typescript.preferences.importModuleSpecifier": "relative",
  "svelte.enable-ts-plugin": true,
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "[svelte]": {
    "editor.defaultFormatter": "svelte.svelte-vscode"
  },
  "tailwindCSS.includeLanguages": {
    "svelte": "html"
  }
}
```

---

## 4. Component Architecture

### Shadcn-Svelte Components

Ouroboros uses Shadcn-Svelte for consistent, accessible UI components:

```svelte
<!-- Example: Using Shadcn-Svelte components -->
<script lang="ts">
  import { Button } from '$lib/components/ui/button';
  import { Card, CardContent, CardHeader, CardTitle } from '$lib/components/ui/card';
  import { Badge } from '$lib/components/ui/badge';
</script>

<Card>
  <CardHeader>
    <CardTitle>Campaign Status</CardTitle>
  </CardHeader>
  <CardContent>
    <Badge variant="success">Active</Badge>
    <Button variant="outline" size="sm">View Details</Button>
  </CardContent>
</Card>
```

### Custom Component Structure

```svelte
<!-- lib/components/campaigns/CampaignCard.svelte -->
<script lang="ts">
  import type { Campaign } from '$lib/types';
  import { Card, CardContent, CardHeader, CardTitle } from '$lib/components/ui/card';
  import { Badge } from '$lib/components/ui/badge';

  export let campaign: Campaign;
  export let showActions = true;

  // Component logic here
</script>

<Card class="campaign-card">
  <CardHeader>
    <CardTitle>{campaign.name}</CardTitle>
  </CardHeader>
  <CardContent>
    <Badge variant={campaign.status === 'active' ? 'success' : 'secondary'}>
      {campaign.status}
    </Badge>

    {#if showActions}
      <div class="actions">
        <!-- Action buttons -->
      </div>
    {/if}
  </CardContent>
</Card>

<style>
  .campaign-card {
    /* Custom styles if needed */
  }
</style>
```

### Component Guidelines

1. **Props**: Use TypeScript interfaces for prop types
2. **Events**: Use `createEventDispatcher` for custom events
3. **Slots**: Provide slots for flexible content composition
4. **Accessibility**: Follow ARIA guidelines and semantic HTML
5. **Styling**: Use Tailwind classes, minimal custom CSS

---

## 5. Form Handling with Superforms

### Overview

Ouroboros uses Superforms v2 with Formsnap for type-safe, progressive enhancement forms that follow SvelteKit conventions.

### Basic Form Pattern

```typescript
// routes/campaigns/new/schema.ts
import { z } from 'zod';

export const campaignSchema = z.object({
  name: z.string().min(1, 'Name is required').max(100),
  description: z.string().optional(),
  hashListId: z.string().uuid('Invalid hash list'),
  priority: z.number().min(1).max(10).default(5)
});

export type CampaignFormData = z.infer<typeof campaignSchema>;
```

```typescript
// routes/campaigns/new/+page.server.ts
import { superValidate } from 'sveltekit-superforms';
import { zod } from 'sveltekit-superforms/adapters';
import { fail, redirect } from '@sveltejs/kit';
import { campaignSchema } from './schema';
import { serverApi } from '$lib/server/api';
import type { Actions, PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ cookies }) => {
  const form = await superValidate(zod(campaignSchema));
  return { form };
};

export const actions: Actions = {
  default: async ({ request, cookies }) => {
    const form = await superValidate(request, zod(campaignSchema));

    if (!form.valid) {
      return fail(400, { form });
    }

    try {
      // Convert form data to API format
      const apiPayload = {
        name: form.data.name,
        description: form.data.description,
        hash_list_id: form.data.hashListId,
        priority: form.data.priority
      };

      const campaign = await serverApi.post('/api/v1/web/campaigns/', apiPayload, {
        headers: { Cookie: cookies.get('sessionid') || '' }
      });

      return redirect(303, `/campaigns/${campaign.id}`);
    } catch (error) {
      return fail(500, { form, message: 'Failed to create campaign' });
    }
  }
};
```

```svelte
<!-- routes/campaigns/new/+page.svelte -->
<script lang="ts">
  import { superForm } from 'sveltekit-superforms';
  import { zodClient } from 'sveltekit-superforms/adapters';
  import { Field, Control, Label, FieldErrors } from 'formsnap';
  import { Button } from '$lib/components/ui/button';
  import { Input } from '$lib/components/ui/input';
  import { Textarea } from '$lib/components/ui/textarea';
  import { campaignSchema } from './schema';

  export let data;

  const { form, errors, enhance, submitting } = superForm(data.form, {
    validators: zodClient(campaignSchema),
    resetForm: true
  });
</script>

<form method="POST" use:enhance class="space-y-4">
  <Field name="name" form={form}>
    <Control let:attrs>
      <Label>Campaign Name</Label>
      <Input {...attrs} bind:value={$form.name} />
    </Control>
    <FieldErrors />
  </Field>

  <Field name="description" form={form}>
    <Control let:attrs>
      <Label>Description</Label>
      <Textarea {...attrs} bind:value={$form.description} />
    </Control>
    <FieldErrors />
  </Field>

  <Button type="submit" disabled={$submitting}>
    {$submitting ? 'Creating...' : 'Create Campaign'}
  </Button>
</form>
```

### Advanced Form Features

#### File Uploads

```svelte
<script lang="ts">
  import { enhance } from '$app/forms';
  import { FileInput } from '$lib/components/ui/file-input';

  let files: FileList;
  let uploading = false;
</script>

<form
  method="POST"
  enctype="multipart/form-data"
  use:enhance={() => {
    uploading = true;
    return async ({ result }) => {
      uploading = false;
      // Handle result
    };
  }}
>
  <FileInput bind:files accept=".txt,.zip" />
  <Button type="submit" disabled={uploading}>
    {uploading ? 'Uploading...' : 'Upload'}
  </Button>
</form>
```

#### Dynamic Forms

```svelte
<script lang="ts">
  import { superForm } from 'sveltekit-superforms';
  import { arrayProxy } from 'sveltekit-superforms';

  export let data;

  const { form, enhance } = superForm(data.form);
  const { values, errors } = arrayProxy(form, 'items');

  function addItem() {
    $values = [...$values, { name: '', value: '' }];
  }

  function removeItem(index: number) {
    $values = $values.filter((_, i) => i !== index);
  }
</script>

<form method="POST" use:enhance>
  {#each $values as item, i}
    <div class="flex gap-2">
      <Input bind:value={item.name} placeholder="Name" />
      <Input bind:value={item.value} placeholder="Value" />
      <Button type="button" on:click={() => removeItem(i)}>Remove</Button>
    </div>
  {/each}

  <Button type="button" on:click={addItem}>Add Item</Button>
  <Button type="submit">Save</Button>
</form>
```

---

## 6. API Integration

### Server-Side API Client

```typescript
// lib/server/api.ts
import { loadConfig } from '$lib/config';

class ServerApiClient {
  private baseUrl: string;

  constructor() {
    const config = loadConfig();
    this.baseUrl = config.api.internalUrl || config.api.baseUrl;
  }

  async get(endpoint: string, options: RequestInit = {}) {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      ...options
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }

    return response.json();
  }

  async post(endpoint: string, data: any, options: RequestInit = {}) {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      body: JSON.stringify(data),
      ...options
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }

    return response.json();
  }
}

export const serverApi = new ServerApiClient();
```

### Client-Side API Wrapper

```typescript
// lib/client/api.ts
import { getApiUrl } from '$lib/config';

export class ClientApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public response?: any
  ) {
    super(message);
  }
}

export async function apiCall(endpoint: string, options: RequestInit = {}) {
  const url = getApiUrl(endpoint);

  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers
    },
    ...options
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new ClientApiError(
      error.message || 'API request failed',
      response.status,
      error
    );
  }

  return response.json();
}

// Utility functions
export const api = {
  get: (endpoint: string, options?: RequestInit) =>
    apiCall(endpoint, { method: 'GET', ...options }),

  post: (endpoint: string, data?: any, options?: RequestInit) =>
    apiCall(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
      ...options
    }),

  put: (endpoint: string, data?: any, options?: RequestInit) =>
    apiCall(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
      ...options
    }),

  delete: (endpoint: string, options?: RequestInit) =>
    apiCall(endpoint, { method: 'DELETE', ...options })
};
```

### Data Loading Patterns

```typescript
// +page.server.ts - Server-side data loading
import { serverApi } from '$lib/server/api';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ cookies, params }) => {
  try {
    const [campaigns, agents] = await Promise.all([
      serverApi.get('/api/v1/web/campaigns/', {
        headers: { Cookie: cookies.get('sessionid') || '' }
      }),
      serverApi.get('/api/v1/web/agents/', {
        headers: { Cookie: cookies.get('sessionid') || '' }
      })
    ]);

    return {
      campaigns,
      agents
    };
  } catch (error) {
    throw error(500, 'Failed to load data');
  }
};
```

```svelte
<!-- +page.svelte - Client-side updates -->
<script lang="ts">
  import { api } from '$lib/client/api';
  import { invalidateAll } from '$app/navigation';

  export let data;

  async function refreshData() {
    try {
      await invalidateAll(); // Triggers server load function
    } catch (error) {
      console.error('Failed to refresh:', error);
    }
  }

  async function updateCampaign(id: string, updates: any) {
    try {
      await api.put(`/api/v1/web/campaigns/${id}`, updates);
      await refreshData();
    } catch (error) {
      console.error('Failed to update:', error);
    }
  }
</script>
```

---

## 7. Testing

### Unit Testing with Vitest

```typescript
// components/CampaignCard.spec.ts
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import CampaignCard from './CampaignCard.svelte';

describe('CampaignCard', () => {
  const mockCampaign = {
    id: '1',
    name: 'Test Campaign',
    status: 'active',
    description: 'Test description'
  };

  it('renders campaign information', () => {
    render(CampaignCard, { props: { campaign: mockCampaign } });

    expect(screen.getByText('Test Campaign')).toBeInTheDocument();
    expect(screen.getByText('active')).toBeInTheDocument();
  });

  it('shows actions when enabled', () => {
    render(CampaignCard, {
      props: { campaign: mockCampaign, showActions: true }
    });

    expect(screen.getByRole('button')).toBeInTheDocument();
  });
});
```

### Integration Testing

```typescript
// routes/campaigns/+page.spec.ts
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import Page from './+page.svelte';

// Mock the API
vi.mock('$lib/client/api', () => ({
  api: {
    get: vi.fn().mockResolvedValue([])
  }
}));

describe('Campaigns Page', () => {
  it('renders campaigns list', async () => {
    const mockData = {
      campaigns: [
        { id: '1', name: 'Campaign 1', status: 'active' }
      ]
    };

    render(Page, { props: { data: mockData } });

    expect(screen.getByText('Campaign 1')).toBeInTheDocument();
  });
});
```

### E2E Testing with Playwright

```typescript
// e2e/campaigns.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Campaign Management', () => {
  test('creates new campaign', async ({ page }) => {
    await page.goto('/campaigns');

    await page.click('text=New Campaign');
    await page.fill('[name="name"]', 'Test Campaign');
    await page.fill('[name="description"]', 'Test description');
    await page.click('button[type="submit"]');

    await expect(page).toHaveURL(/\/campaigns\/\w+/);
    await expect(page.locator('h1')).toContainText('Test Campaign');
  });
});
```

---

## 8. Build and Deployment

### Production Build

```bash
# Build the application
pnpm build

# Preview production build locally
pnpm preview
```

### Docker Deployment

```dockerfile
# frontend/Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package.json pnpm-lock.yaml ./
RUN npm install -g pnpm && pnpm install --frozen-lockfile

COPY . .
RUN pnpm build

FROM node:18-alpine AS runner

WORKDIR /app
COPY --from=builder /app/build ./build
COPY --from=builder /app/package.json ./
COPY --from=builder /app/node_modules ./node_modules

EXPOSE 3000
CMD ["node", "build"]
```

### Environment Configuration

```bash
# Production environment variables
VITE_API_BASE_URL=https://api.ouroboros.com
VITE_APP_NAME=Ouroboros
VITE_ENVIRONMENT=production
VITE_EXPERIMENTAL_FEATURES=false

API_INTERNAL_URL=http://app:8000
SESSION_SECRET=production-secret-key
```

---

## 9. Best Practices

### Code Organization

1. **File Naming**: Use kebab-case for files, PascalCase for components
2. **Import Order**: External libraries, internal modules, relative imports
3. **Component Size**: Keep components under 200 lines, extract logic to utilities
4. **Type Safety**: Use TypeScript interfaces for all data structures

### Performance

1. **Code Splitting**: Use dynamic imports for large components
2. **Image Optimization**: Use SvelteKit's image optimization features
3. **Bundle Analysis**: Regularly check bundle size with `pnpm build --analyze`
4. **Lazy Loading**: Implement lazy loading for data-heavy components

### Accessibility

1. **Semantic HTML**: Use proper HTML elements and ARIA attributes
2. **Keyboard Navigation**: Ensure all interactive elements are keyboard accessible
3. **Screen Readers**: Test with screen reader software
4. **Color Contrast**: Maintain WCAG AA compliance

### Security

1. **Input Validation**: Validate all user inputs with Zod schemas
2. **XSS Prevention**: Use SvelteKit's built-in XSS protection
3. **CSRF Protection**: Implement CSRF tokens for forms
4. **Content Security Policy**: Configure CSP headers

### Error Handling

```svelte
<script lang="ts">
  import { page } from '$app/stores';
  import { api, ClientApiError } from '$lib/client/api';

  let error: string | null = null;
  let loading = false;

  async function handleAction() {
    try {
      loading = true;
      error = null;
      await api.post('/api/v1/web/campaigns/', data);
    } catch (err) {
      if (err instanceof ClientApiError) {
        error = err.message;
      } else {
        error = 'An unexpected error occurred';
      }
    } finally {
      loading = false;
    }
  }
</script>

{#if error}
  <Alert variant="destructive">
    <AlertDescription>{error}</AlertDescription>
  </Alert>
{/if}
```

### Development Workflow

1. **Feature Branches**: Create feature branches for new development
2. **Code Review**: All changes require code review
3. **Testing**: Write tests for new features and bug fixes
4. **Documentation**: Update documentation for API changes
5. **Linting**: Run linters before committing code

### Debugging

```typescript
// Enable debug mode in development
import { dev } from '$app/environment';

if (dev) {
  console.log('Debug info:', data);
}

// Use SvelteKit's built-in debugging
import { browser } from '$app/environment';

if (browser && dev) {
  // Client-side debugging
  window.debugData = data;
}
```

This guide provides a comprehensive foundation for frontend development in Ouroboros. For specific implementation details, refer to the existing codebase and component documentation.
