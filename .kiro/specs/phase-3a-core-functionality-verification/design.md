# Design Document

## Overview

This design document outlines the comprehensive technical approach for implementing Phase 3 Step 2: Core Functionality Verification & Completion. This phase encompasses not only verifying that existing Ouroboros features work correctly with the newly implemented authentication system, but also completing critical gaps in user management functionality, implementing comprehensive visual components based on UI design specifications, and migrating from legacy HTMX/Jinja templates to modern SvelteKit 5 components.

The design addresses eight major areas:

1. **Authentication Integration Verification** - Ensuring all existing features work with the new auth system
2. **User Management Implementation** - Completing missing user management workflows and interfaces
3. **Visual Component Implementation** - Building comprehensive UI components based on design specifications
4. **Template Migration** - Converting legacy HTMX/Jinja templates to SvelteKit 5 components
5. **Real-time Dashboard Implementation** - Creating live monitoring interfaces with SSE integration
6. **Workflow Implementation** - Building complete user workflows from authentication through advanced administration
7. **Development Environment Setup** - Establishing proper tooling, testing, and quality assurance
8. **Style System Implementation** - Applying consistent visual design using Catppuccin theme and Shadcn-Svelte components

## Architecture

### System Integration Approach

The design follows a comprehensive modernization approach that combines verification of existing functionality with complete UI modernization and template migration. The architecture is built on SvelteKit 5 with runes, Shadcn-Svelte components, and a robust real-time update system.

**Key Integration Points:**

- **SvelteKit 5 Architecture**: Full SSR with runes ($state, $derived, $effect) for reactive state management
- **Component System**: Shadcn-Svelte + Tailwind v4 with Catppuccin theme implementation
- **Form Handling**: Superforms v2 with Formsnap and Zod validation for all user inputs
- **Authentication**: Multi-layered auth with JWT tokens, session cookies, and role-based access control
- **Real-time Updates**: SSE integration with Svelte stores for live dashboard updates
- **Project Context**: Persistent project selection with scoped data visibility
- **Template Migration**: Complete conversion from HTMX/Jinja to SvelteKit components
- **Development Tooling**: Python 3.13 + uv, comprehensive testing with pytest/Playwright, quality assurance with ruff/mypy

### Authentication Integration Layer

**SSR Load Function Pattern:**

```typescript
// +page.server.ts pattern
export const load: PageServerLoad = async ({ cookies, params, url }) => {
  const session = await getSessionFromCookies(cookies);
  if (!session) {
    throw redirect(302, `/login?redirect=${url.pathname}`);
  }

  try {
    const data = await authenticatedApiCall(session.token, endpoint);
    return { data, user: session.user, project: session.project };
  } catch (error) {
    if (error.status === 401) {
      throw redirect(302, '/login');
    }
    throw error(500, 'Failed to load data');
  }
};
```

**Client-Side Authentication Context:**

- Use `$page.data.user` for role-based UI rendering
- Use `$page.data.project` for project context awareness
- Implement global project selector with context switching

## Components and Interfaces

### User Management Components

**User List Interface (`/users`):**

- DataTable component with role-based column visibility
- Search and filter functionality using Shadcn-Svelte components
- Action menus with permission-based item visibility
- Pagination with URL state management

**User Detail Interface (`/users/[id]`):**

- Profile display with inline editing capabilities
- Role management with permission validation
- Project association management
- Activity timeline with audit trail display

**User Deletion Interface (`/users/[id]/delete`):**

- Impact assessment display showing affected resources
- Multi-step confirmation workflow
- Cascade deletion options with clear warnings
- Typed confirmation input for destructive actions

**Settings Interface (`/settings`):**

- Profile editing with real-time validation
- Password change with security requirements
- API key management with secure display
- Theme and preference controls

### Project Management Components

**Project Selection Modal:**

- Auto-trigger on login for multi-project users
- Project list with membership indicators
- Last-selected project persistence in localStorage
- Smooth transition to selected project context

**Global Project Selector:**

- Header-mounted dropdown component
- Real-time project switching with data refresh
- Visual indication of current project context
- Permission-based project list filtering

### Form Architecture

**Superforms v2 Integration Pattern:**

```typescript
// Form schema using generated Zod objects
import { userCreateSchema } from '$lib/schemas/user';

// SvelteKit action
export const actions = {
  default: async ({ request, cookies }) => {
    return superValidate(request, userCreateSchema);
  }
};

// Component usage
const form = superForm(data.form, {
  validators: userCreateSchema,
  onUpdated: ({ form }) => {
    if (form.valid) {
      // Handle success
    }
  }
});
```

### Access Control Architecture

**Role-Based Component Rendering:**

```svelte
{#if $page.data.user.role === 'admin'}
  <AdminOnlyComponent />
{/if}

{#if canAccessProject($page.data.user, $page.data.project)}
  <ProjectScopedContent />
{/if}
```

**Permission Validation Utilities:**

- `canAccessProject(user, project)` - Project access validation
- `hasRole(user, role)` - Role-based permission checking
- `canManageUsers(user)` - Admin function access validation
- `canEditUser(currentUser, targetUser)` - User editing permissions

## Data Models

### User Management Data Flow

**User Entity Structure:**

```typescript
interface User {
  id: number;
  username: string;
  email: string;
  role: 'admin' | 'project_admin' | 'user';
  projects: ProjectMembership[];
  lastLogin: Date;
  isActive: boolean;
  createdAt: Date;
  updatedAt: Date;
}

interface ProjectMembership {
  projectId: number;
  projectName: string;
  role: string;
  joinedAt: Date;
}
```

**Project Context Structure:**

```typescript
interface ProjectContext {
  id: number;
  name: string;
  description: string;
  userRole: string;
  permissions: string[];
  isActive: boolean;
}
```

### Form Data Models

All forms use Zod schemas generated from the OpenAPI specification located at `contracts/current_api_openapi.json`. The generated schemas are stored in `frontend/src/lib/schemas/` and provide both client-side and server-side validation.

**Key Schema Categories:**

- User management: `userCreateSchema`, `userUpdateSchema`, `passwordChangeSchema`
- Project management: `projectCreateSchema`, `projectUpdateSchema`
- Settings: `profileUpdateSchema`, `preferencesSchema`
- Authentication: `loginSchema`, `registrationSchema`

## Error Handling

### Authentication Error Handling

**Error Response Patterns:**

- 401 Unauthorized → Redirect to login with return URL
- 403 Forbidden → Show access denied page with role information
- 404 Not Found → Show not found page with navigation options
- 500 Server Error → Log error and show generic error message

**Client-Side Error Boundaries:**

```svelte
{#await dataPromise}
  <LoadingSpinner />
{:then data}
  <DataDisplay {data} />
{:catch error}
  <ErrorDisplay {error} />
{/await}
```

### Form Error Handling

**Validation Error Display:**

- Field-level errors positioned near input elements
- Form-level errors displayed at top of form
- Real-time validation with debounced input
- Server-side validation with error mapping

**Error Recovery Patterns:**

- Auto-save draft data to localStorage
- Retry mechanisms for network failures
- Clear error state on successful operations
- Progressive enhancement for JavaScript failures

## Testing Strategy

### Test Architecture Overview

The testing strategy follows a dual approach with both mocked E2E tests and full E2E tests to ensure comprehensive coverage while maintaining fast feedback loops.

**Test Environment Structure:**

- `frontend/e2e/` - Mocked E2E tests (fast, no backend required)
- `frontend/tests/e2e/` - Full E2E tests (slower, real backend integration)
- `frontend/tests/test-utils.ts` - Shared test utilities and helpers

### Test Execution Patterns

**Mocked E2E Tests (`just test-frontend`):**

- Focus on UI behavior and validation
- Mock API responses using MSW (Mock Service Worker)
- Test form validation, error states, and user interactions
- Fast execution for development feedback

**Full E2E Tests (`just test-e2e`):**

- Test complete authentication flows
- Verify data persistence and API integration
- Test cross-browser compatibility
- Require Docker setup with real backend services

### Test Coverage Requirements

**User Management Testing:**

- User creation, editing, and deletion workflows
- Role-based access control validation
- Project association management
- Profile and settings functionality

**Authentication Integration Testing:**

- Login/logout flows with redirect handling
- Session persistence across navigation
- Token refresh and expiration handling
- Permission enforcement validation

**Form Behavior Testing:**

- Client-side and server-side validation
- Error display and recovery
- Progressive enhancement
- Multi-step form navigation

### Test Utilities and Helpers

**Common Test Patterns:**

```typescript
// Authentication test helper
export async function loginAsAdmin(page: Page) {
  await page.goto('/login');
  await page.fill('[data-testid="username"]', 'admin');
  await page.fill('[data-testid="password"]', 'password');
  await page.click('[data-testid="login-button"]');
  await page.waitForURL('/dashboard');
}

// Form validation test helper
export async function testFormValidation(page: Page, formSelector: string, validationRules: ValidationRule[]) {
  for (const rule of validationRules) {
    await page.fill(`${formSelector} [name="${rule.field}"]`, rule.invalidValue);
    await page.blur(`${formSelector} [name="${rule.field}"]`);
    await expect(page.locator(`[data-testid="${rule.field}-error"]`)).toContainText(rule.expectedError);
  }
}
```

## Visual Component Architecture

### Dashboard and Layout Components

**Layout System:**

```typescript
// +layout.svelte - Root layout with sidebar, header, and main content
interface LayoutProps {
  user: User;
  project: Project | null;
  projects: Project[];
}

// Sidebar.svelte - Navigation with role-based menu items
interface SidebarProps {
  collapsed: boolean;
  activeRoute: string;
  userRole: UserRole;
}

// Header.svelte - Project selector, user menu, live status indicators
interface HeaderProps {
  user: User;
  currentProject: Project | null;
  projects: Project[];
  sseConnected: boolean;
}
```

**Dashboard Components:**

```typescript
// DashboardCard.svelte - Reusable status card component
interface DashboardCardProps {
  title: string;
  value: number | string;
  subtitle?: string;
  icon?: string;
  trend?: 'up' | 'down' | 'stable';
  clickable?: boolean;
  onClick?: () => void;
}

// CampaignOverview.svelte - Accordion-style campaign list
interface CampaignOverviewProps {
  campaigns: Campaign[];
  onExpand: (campaignId: string) => void;
  onAction: (action: string, campaignId: string) => void;
}

// AgentStatusSheet.svelte - Slide-out agent monitoring panel
interface AgentStatusSheetProps {
  agents: Agent[];
  open: boolean;
  onClose: () => void;
  onAgentAction: (action: string, agentId: string) => void;
}
```

### Form and Modal Architecture

**Form Components:**

```typescript
// BaseForm.svelte - Wrapper for all forms using Superforms v2
interface BaseFormProps<T> {
  schema: ZodSchema<T>;
  initialData?: Partial<T>;
  onSubmit: (data: T) => Promise<void>;
  submitLabel?: string;
  cancelLabel?: string;
  onCancel?: () => void;
}

// FormField.svelte - Reusable form field with validation
interface FormFieldProps {
  name: string;
  label: string;
  type: 'text' | 'email' | 'password' | 'select' | 'textarea' | 'file';
  required?: boolean;
  options?: Array<{ value: string; label: string }>;
  placeholder?: string;
  description?: string;
}
```

**Modal System:**

```typescript
// BaseModal.svelte - Consistent modal wrapper
interface BaseModalProps {
  open: boolean;
  title: string;
  description?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  onClose: () => void;
  showCloseButton?: boolean;
}

// ConfirmationModal.svelte - Standardized confirmation dialogs
interface ConfirmationModalProps {
  open: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: 'default' | 'destructive';
  onConfirm: () => void;
  onCancel: () => void;
}
```

### Real-time Update Architecture

**SSE Integration:**

```typescript
// stores/sse.ts - Server-Sent Events management
interface SSEStore {
  connected: boolean;
  lastUpdate: Date | null;
  connectionAttempts: number;
  events: SSEEvent[];
}

interface SSEEvent {
  type: 'campaign_update' | 'agent_status' | 'crack_result' | 'system_health';
  data: any;
  timestamp: Date;
}

// SSE event handlers trigger targeted store updates
const campaignStore = writable<Campaign[]>([]);
const agentStore = writable<Agent[]>([]);
const toastStore = writable<Toast[]>([]);
```

**Live Data Components:**

```typescript
// LiveProgressBar.svelte - Real-time progress updates
interface LiveProgressBarProps {
  campaignId: string;
  initialProgress: number;
  showETA?: boolean;
  showRate?: boolean;
}

// LiveStatusBadge.svelte - Dynamic status indicators
interface LiveStatusBadgeProps {
  entityId: string;
  entityType: 'campaign' | 'agent' | 'task';
  initialStatus: string;
  showLastUpdate?: boolean;
}
```

## Template Migration Architecture

### Migration Strategy

**Component Mapping:**

```typescript
// Legacy Template → SvelteKit Component mapping
const migrationMap = {
  'base.html.j2': '+layout.svelte + Sidebar.svelte + Header.svelte',
  'dashboard.html.j2': '+page.svelte (dashboard)',
  'agents/list.html.j2': 'routes/agents/+page.svelte',
  'campaigns/detail.html.j2': 'routes/campaigns/[id]/+page.svelte',
  'attacks/editor_modal.html.j2': 'lib/components/attacks/AttackEditorModal.svelte',
  // ... complete mapping for all templates
};
```

**Component Architecture:**

```
frontend/src/lib/components/
├── ui/                    # Shadcn-Svelte base components
├── layout/               # Layout components (Sidebar, Header, etc.)
├── dashboard/            # Dashboard-specific components
├── agents/               # Agent management components
├── campaigns/            # Campaign management components
├── attacks/              # Attack configuration components
├── resources/            # Resource management components
├── users/                # User management components
├── projects/             # Project management components
└── common/               # Shared utility components
```

### Legacy Feature Preservation

**HTMX to SvelteKit Patterns:**

```typescript
// HTMX: hx-get="/api/campaigns" hx-target="#campaign-list"
// SvelteKit: Reactive store updates with load functions
export const load: PageServerLoad = async ({ cookies }) => {
  const campaigns = await api.get('/api/v1/web/campaigns/', {
    headers: { Cookie: cookies.get('sessionid') || '' }
  });
  return { campaigns };
};

// HTMX: hx-post="/api/campaigns" hx-swap="outerHTML"
// SvelteKit: Form actions with progressive enhancement
export const actions: Actions = {
  create: async ({ request, cookies }) => {
    const form = await superValidate(request, campaignSchema);
    if (!form.valid) return fail(400, { form });

    const result = await api.post('/api/v1/web/campaigns/', form.data);
    return { form, success: true };
  }
};
```

**Alpine.js to Svelte Runes:**

```typescript
// Alpine.js: x-data="{ open: false }" x-show="open"
// Svelte: $state rune with reactive updates
<script lang="ts">
  let open = $state(false);

  function toggleOpen() {
    open = !open;
  }
</script>

{#if open}
  <div transition:slide>Content</div>
{/if}
```

## User Workflow Implementation

### Authentication and Project Management

**Login Flow Architecture:**

```typescript
// routes/login/+page.server.ts
export const actions: Actions = {
  default: async ({ request, cookies }) => {
    const form = await superValidate(request, loginSchema);
    if (!form.valid) return fail(400, { form });

    const { user, token, projects } = await authenticate(form.data);

    // Set secure session cookie
    cookies.set('sessionid', token, {
      httpOnly: true,
      secure: true,
      sameSite: 'strict',
      maxAge: 60 * 60 * 24 * 7 // 7 days
    });

    // Handle project selection
    if (projects.length === 1) {
      cookies.set('project_id', projects[0].id);
      throw redirect(303, '/dashboard');
    } else {
      throw redirect(303, '/projects/select');
    }
  }
};
```

**Project Context Management:**

```typescript
// stores/project.ts
interface ProjectContext {
  current: Project | null;
  available: Project[];
  switching: boolean;
}

export const projectStore = writable<ProjectContext>({
  current: null,
  available: [],
  switching: false
});

export async function switchProject(projectId: string) {
  projectStore.update(ctx => ({ ...ctx, switching: true }));

  await api.post('/api/v1/web/auth/context', { project_id: projectId });

  // Refresh all data after project switch
  await invalidateAll();

  projectStore.update(ctx => ({
    ...ctx,
    current: ctx.available.find(p => p.id === projectId) || null,
    switching: false
  }));
}
```

### Campaign and Attack Management Workflows

**Campaign Creation Wizard:**

```typescript
// lib/components/campaigns/CampaignWizard.svelte
interface WizardStep {
  id: string;
  title: string;
  component: ComponentType;
  valid: boolean;
  data: any;
}

const wizardSteps: WizardStep[] = [
  { id: 'hashlist', title: 'Select Hash List', component: HashlistStep, valid: false, data: {} },
  { id: 'metadata', title: 'Campaign Details', component: MetadataStep, valid: false, data: {} },
  { id: 'attacks', title: 'Configure Attacks', component: AttacksStep, valid: false, data: {} },
  { id: 'review', title: 'Review & Launch', component: ReviewStep, valid: false, data: {} }
];

let currentStep = $state(0);
let wizardData = $state({});

function nextStep() {
  if (currentStep < wizardSteps.length - 1) {
    currentStep++;
  }
}

function previousStep() {
  if (currentStep > 0) {
    currentStep--;
  }
}
```

**Attack Configuration System:**

```typescript
// lib/components/attacks/AttackEditor.svelte
interface AttackConfig {
  type: 'dictionary' | 'mask' | 'brute_force' | 'hybrid';
  parameters: Record<string, any>;
  resources: AttackResource[];
  keyspace?: number;
  complexity?: number;
}

// Real-time keyspace estimation
let attackConfig = $state<AttackConfig>({ type: 'dictionary', parameters: {}, resources: [] });
let keyspaceEstimate = $derived.by(async () => {
  if (!attackConfig.type || !attackConfig.parameters) return null;

  const response = await api.post('/api/v1/web/attacks/estimate', attackConfig);
  return response.keyspace;
});
```

### Resource and User Management

**Resource Management System:**

```typescript
// routes/resources/+page.svelte
interface ResourceFilter {
  type: string | null;
  search: string;
  sensitivity: 'all' | 'public' | 'sensitive';
  project: string | null;
}

let filters = $state<ResourceFilter>({
  type: null,
  search: '',
  sensitivity: 'all',
  project: null
});

let filteredResources = $derived(
  resources.filter(resource => {
    if (filters.type && resource.type !== filters.type) return false;
    if (filters.search && !resource.name.toLowerCase().includes(filters.search.toLowerCase())) return false;
    if (filters.sensitivity !== 'all' && resource.sensitive !== (filters.sensitivity === 'sensitive')) return false;
    return true;
  })
);
```

**User Management Interface:**

```typescript
// routes/users/+page.svelte (admin only)
interface UserManagementState {
  users: User[];
  selectedUser: User | null;
  showCreateModal: boolean;
  showDeleteModal: boolean;
  filters: UserFilter;
}

let state = $state<UserManagementState>({
  users: [],
  selectedUser: null,
  showCreateModal: false,
  showDeleteModal: false,
  filters: { role: 'all', project: 'all', status: 'active' }
});

// Role-based access control
let canManageUsers = $derived(
  $page.data.user?.role === 'admin' || $page.data.user?.role === 'project_admin'
);
```

## Development Environment Architecture

### Configuration Management

**Environment Configuration System:**

```typescript
// lib/config/index.ts
interface AppConfig {
  apiBaseUrl: string;
  publicApiBaseUrl: string;
  tokenExpireMinutes: number;
  debug: boolean;
  appName: string;
  appVersion: string;
  enableExperimentalFeatures: boolean;
}

// Dual environment support
export function getApiBaseUrl(): string {
  if (browser) {
    return env.PUBLIC_API_BASE_URL || env.VITE_API_BASE_URL;
  } else {
    return env.API_BASE_URL || env.VITE_API_BASE_URL;
  }
}

// Type-safe configuration validation
const configSchema = z.object({
  apiBaseUrl: z.string().url(),
  publicApiBaseUrl: z.string().url(),
  tokenExpireMinutes: z.number().positive(),
  debug: z.boolean(),
  appName: z.string().min(1),
  appVersion: z.string().min(1),
  enableExperimentalFeatures: z.boolean()
});

export const config = configSchema.parse({
  apiBaseUrl: getApiBaseUrl(),
  publicApiBaseUrl: env.PUBLIC_API_BASE_URL || env.VITE_API_BASE_URL,
  tokenExpireMinutes: parseInt(env.VITE_TOKEN_EXPIRE_MINUTES || '60'),
  debug: env.VITE_DEBUG === 'true',
  appName: env.VITE_APP_NAME || 'Ouroboros',
  appVersion: env.VITE_APP_VERSION || '2.0.0',
  enableExperimentalFeatures: env.VITE_ENABLE_EXPERIMENTAL_FEATURES === 'true'
});
```

### Testing Architecture

**Test Structure:**

```typescript
// Component unit tests (Vitest)
// components/Dashboard.spec.ts
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import Dashboard from './Dashboard.svelte';

describe('Dashboard', () => {
  it('renders status cards', () => {
    const mockData = {
      agents: { online: 5, total: 10 },
      tasks: { running: 3, total: 15 },
      cracks: { recent: 42 },
      hashRate: 1500000
    };

    render(Dashboard, { props: { data: mockData } });

    expect(screen.getByText('5 / 10')).toBeInTheDocument();
    expect(screen.getByText('3 running')).toBeInTheDocument();
  });
});

// E2E tests (Playwright)
// e2e/dashboard.test.ts
import { test, expect } from '@playwright/test';

test.describe('Dashboard', () => {
  test('displays real-time updates', async ({ page }) => {
    await page.goto('/dashboard');

    // Mock SSE events
    await page.route('/api/v1/web/live/campaigns', route => {
      route.fulfill({
        status: 200,
        headers: { 'Content-Type': 'text/event-stream' },
        body: 'data: {"type": "campaign_update", "data": {"id": "1", "progress": 75}}\n\n'
      });
    });

    await expect(page.locator('[data-testid="campaign-progress"]')).toContainText('75%');
  });
});
```

### Quality Assurance

**Code Quality Pipeline:**

```typescript
// Development commands (justfile)
dev-frontend:
  cd frontend && pnpm dev

test-frontend:
  cd frontend && pnpm test

test-e2e:
  cd frontend && pnpm test:e2e

lint-frontend:
  cd frontend && pnpm lint

format-frontend:
  cd frontend && pnpm format

check-frontend:
  cd frontend && pnpm check

// CI integration
ci-check: lint-frontend test-frontend test-e2e check-frontend
```

## Performance Considerations

### Loading Performance

**SSR Optimization:**

- Parallel API calls in load functions where possible
- Proper error boundaries to prevent cascade failures
- Efficient data serialization for client hydration
- Minimal client-side JavaScript for initial render

**Client-Side Performance:**

- Lazy loading for non-critical components using dynamic imports
- Efficient state management with SvelteKit stores and runes
- Debounced search and filter operations (300ms delay)
- Optimistic UI updates for better perceived performance
- Component-level code splitting for large modals and complex interfaces

**Real-time Update Optimization:**

- SSE connection pooling and automatic reconnection
- Efficient event filtering to prevent unnecessary updates
- Batched DOM updates using Svelte's reactive system
- Smart caching of frequently accessed data

### Caching Strategy

**Browser Caching:**

- Static assets with long-term caching (1 year for immutable assets)
- API responses with appropriate cache headers (5-60 seconds for dynamic data)
- localStorage for user preferences and project selection
- SessionStorage for temporary form data and wizard state

**Server-Side Caching:**

- Redis caching for frequently accessed data (agent status, campaign summaries)
- Proper cache invalidation on data updates using cache tags
- Efficient database queries with appropriate indexes
- CDN caching for static resources when available

**Component-Level Caching:**

- Memoization of expensive computations using $derived
- Lazy loading of heavy components until needed
- Efficient list rendering with virtual scrolling for large datasets

## Security Considerations

### Authentication Security

**Token Management:**

- Secure HTTP-only cookies for session tokens
- Automatic token refresh before expiration
- Proper token revocation on logout
- CSRF protection for state-changing operations

**Access Control Security:**

- Server-side permission validation using Casbin
- Client-side permission checks for UI rendering
- Project-scoped data access validation
- Audit logging for administrative actions

### Input Validation Security

**Form Security:**

- Server-side validation for all form inputs
- XSS prevention through proper output encoding
- SQL injection prevention through parameterized queries
- File upload validation and sanitization

**API Security:**

- Request rate limiting to prevent abuse
- Input sanitization and validation
- Proper error handling without information disclosure
- Secure headers for all responses

## Style System Implementation

### Theme Architecture

**Catppuccin Theme Integration:**

```typescript
// tailwind.config.js
import { catppuccin } from '@catppuccin/tailwindcss';

export default {
  content: ['./src/**/*.{html,js,svelte,ts}'],
  theme: {
    extend: {
      colors: {
        accent: '#9400D3', // DarkViolet
        ...catppuccin('macchiato')
      }
    }
  },
  plugins: [catppuccin({ defaultFlavor: 'macchiato' })]
};
```

**Component Styling Standards:**

```typescript
// Button variants using Shadcn-Svelte patterns
const buttonVariants = cva(
  "inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors",
  {
    variants: {
      variant: {
        default: "bg-accent text-white hover:bg-accent/90",
        outline: "border border-accent text-accent hover:bg-accent hover:text-white",
        ghost: "hover:bg-accent/10 hover:text-accent"
      },
      size: {
        sm: "h-8 px-3 text-xs",
        md: "h-9 px-4",
        lg: "h-10 px-6"
      }
    },
    defaultVariants: {
      variant: "default",
      size: "md"
    }
  }
);
```

**Icon System:**

```typescript
// lib/components/ui/Icon.svelte
interface IconProps {
  name: keyof typeof iconMap;
  size?: 'sm' | 'md' | 'lg';
  class?: string;
}

const iconMap = {
  'book-open': BookOpenIcon,      // Dictionary attacks
  'command': CommandIcon,         // Mask attacks
  'hash': HashIcon,              // Brute force attacks
  'rotate-ccw': RotateCcwIcon,   // Previous passwords
  'merge': MergeIcon,            // Hybrid attacks
  'sliders-horizontal': SlidersHorizontalIcon, // Rule-based
  'puzzle': PuzzleIcon           // Modifiers
};
```

### Responsive Design System

**Breakpoint Strategy:**

```typescript
// Responsive utilities
const breakpoints = {
  sm: '640px',   // Mobile landscape
  md: '768px',   // Tablet portrait
  lg: '1024px',  // Tablet landscape / small desktop
  xl: '1280px',  // Desktop
  '2xl': '1536px' // Large desktop
};

// Component responsive patterns
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
  <!-- Responsive grid layout -->
</div>

<aside class="w-64 lg:block hidden"> <!-- Desktop sidebar -->
<button class="lg:hidden block"> <!-- Mobile menu toggle -->
```

**Mobile Navigation:**

```typescript
// lib/components/layout/MobileNav.svelte
let mobileMenuOpen = $state(false);

function toggleMobileMenu() {
  mobileMenuOpen = !mobileMenuOpen;
}

// Hamburger menu with slide-out drawer
{#if mobileMenuOpen}
  <div class="fixed inset-0 z-50 lg:hidden">
    <div class="fixed inset-0 bg-black/50" on:click={toggleMobileMenu}></div>
    <nav class="fixed left-0 top-0 h-full w-64 bg-surface0 p-4">
      <!-- Mobile navigation content -->
    </nav>
  </div>
{/if}
```

## Advanced Feature Implementation

### Health Monitoring System

**System Health Dashboard:**

```typescript
// routes/admin/health/+page.svelte (admin only)
interface SystemHealth {
  redis: ServiceHealth;
  minio: ServiceHealth;
  postgresql: ServiceHealth;
  agents: AgentHealth[];
}

interface ServiceHealth {
  status: 'healthy' | 'degraded' | 'unhealthy';
  latency: number;
  lastCheck: Date;
  metrics: Record<string, any>;
  errors: string[];
}

// Real-time health monitoring
let healthData = $state<SystemHealth | null>(null);
let healthSSE = $state<EventSource | null>(null);

onMount(() => {
  healthSSE = new EventSource('/api/v1/web/live/health');
  healthSSE.onmessage = (event) => {
    healthData = JSON.parse(event.data);
  };
});
```

**Service Status Cards:**

```typescript
// lib/components/health/ServiceStatusCard.svelte
interface ServiceStatusCardProps {
  service: ServiceHealth;
  name: string;
  icon: string;
  adminDetails?: boolean;
}

// Visual health indicators
function getStatusColor(status: string) {
  switch (status) {
    case 'healthy': return 'text-green-500';
    case 'degraded': return 'text-yellow-500';
    case 'unhealthy': return 'text-red-500';
    default: return 'text-gray-500';
  }
}
```

### Template Export/Import System

**Campaign Template Management:**

```typescript
// lib/utils/templates.ts
interface CampaignTemplate {
  name: string;
  description: string;
  version: string;
  attacks: AttackTemplate[];
  metadata: TemplateMetadata;
}

interface AttackTemplate {
  type: string;
  parameters: Record<string, any>;
  resources: ResourceReference[];
  position: number;
}

export async function exportCampaign(campaignId: string): Promise<CampaignTemplate> {
  const campaign = await api.get(`/api/v1/web/campaigns/${campaignId}`);
  const attacks = await api.get(`/api/v1/web/campaigns/${campaignId}/attacks`);

  return {
    name: campaign.name,
    description: campaign.description,
    version: '1.0',
    attacks: attacks.map(attack => ({
      type: attack.attack_mode,
      parameters: attack.parameters,
      resources: attack.resources,
      position: attack.position
    })),
    metadata: {
      exportedAt: new Date(),
      exportedBy: $page.data.user.username,
      cipherswarmVersion: config.appVersion
    }
  };
}

export async function importTemplate(template: CampaignTemplate): Promise<void> {
  // Validate template structure
  const validationResult = templateSchema.safeParse(template);
  if (!validationResult.success) {
    throw new Error('Invalid template format');
  }

  // Pre-fill campaign wizard with template data
  wizardStore.update(state => ({
    ...state,
    templateData: template,
    currentStep: 0
  }));
}
```

### DAG Visualization and Management

**DAG Editor Component:**

```typescript
// lib/components/attacks/DAGEditor.svelte
interface DAGNode {
  id: string;
  attack: Attack;
  phase: number;
  position: { x: number; y: number };
  dependencies: string[];
}

let dagNodes = $state<DAGNode[]>([]);
let selectedNode = $state<string | null>(null);
let draggedNode = $state<string | null>(null);

function moveAttackToPhase(attackId: string, newPhase: number) {
  const attack = dagNodes.find(node => node.id === attackId);
  if (attack) {
    attack.phase = newPhase;
    // Update backend
    api.patch(`/api/v1/web/attacks/${attackId}`, { phase: newPhase });
  }
}

// Visual DAG representation
function renderDAG() {
  const phases = groupBy(dagNodes, 'phase');
  return Object.entries(phases).map(([phase, nodes]) => ({
    phase: parseInt(phase),
    nodes,
    canExecute: phase === '1' || allPreviousPhasesComplete(parseInt(phase) - 1)
  }));
}
```

### Rule Editor with Learned Rules

**Advanced Rule Editor:**

```typescript
// lib/components/resources/RuleEditor.svelte
interface RuleEditorState {
  content: string;
  learnedRules: string[];
  showOverlay: boolean;
  diffMode: boolean;
  hasChanges: boolean;
}

let editorState = $state<RuleEditorState>({
  content: '',
  learnedRules: [],
  showOverlay: false,
  diffMode: false,
  hasChanges: false
});

// Diff visualization
let diffResult = $derived(() => {
  if (!editorState.showOverlay) return null;

  return generateDiff(editorState.content, editorState.learnedRules.join('\n'));
});

function applyLearnedRules(mode: 'append' | 'replace' | 'merge') {
  switch (mode) {
    case 'append':
      editorState.content += '\n' + editorState.learnedRules.join('\n');
      break;
    case 'replace':
      editorState.content = editorState.learnedRules.join('\n');
      break;
    case 'merge':
      editorState.content = mergeRules(editorState.content, editorState.learnedRules);
      break;
  }
  editorState.hasChanges = true;
}
```

## Deployment Considerations

### Environment Configuration

**Development Environment:**

- Hot reload for rapid development feedback using Vite HMR
- Mock data for testing without backend dependencies
- Debug logging and error reporting with source maps
- Development-specific feature flags and experimental features
- Docker Compose setup with service health checks

**Production Environment:**

- Optimized builds with code splitting and tree shaking
- Production logging configuration with structured JSON logs
- Error monitoring and alerting using Sentry or similar
- Performance monitoring and metrics collection
- CDN integration for static asset delivery

**Docker Configuration:**

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

### Monitoring and Observability

**Application Monitoring:**

- User authentication success/failure rates with detailed error tracking
- Page load performance metrics including Core Web Vitals
- API response times and error rates with endpoint-specific breakdowns
- User interaction tracking for UX optimization and conversion funnels
- Real-time SSE connection health and reconnection patterns

**Error Tracking:**

- Client-side error reporting with stack traces and user context
- Server-side error logging with request correlation IDs
- User session replay for debugging complex interaction issues
- Performance bottleneck identification with flame graphs
- Automated alerting for critical error thresholds

**Performance Metrics:**

```typescript
// lib/utils/analytics.ts
interface PerformanceMetrics {
  pageLoadTime: number;
  firstContentfulPaint: number;
  largestContentfulPaint: number;
  cumulativeLayoutShift: number;
  firstInputDelay: number;
  apiResponseTimes: Record<string, number>;
  sseConnectionHealth: {
    connected: boolean;
    reconnectCount: number;
    lastDisconnect: Date | null;
  };
}

export function trackPerformance(metrics: PerformanceMetrics) {
  // Send to monitoring service
  if (config.debug) {
    console.log('Performance metrics:', metrics);
  }
}

// Automatic performance tracking
onMount(() => {
  const observer = new PerformanceObserver((list) => {
    for (const entry of list.getEntries()) {
      trackPerformance({
        pageLoadTime: entry.duration,
        // ... other metrics
      });
    }
  });

  observer.observe({ entryTypes: ['navigation', 'paint', 'largest-contentful-paint'] });
});
```

This comprehensive design document now covers all aspects of the core functionality verification and completion phase, providing detailed technical specifications for implementing the complete modernization of Ouroboros's frontend while maintaining all existing functionality and adding comprehensive new features.
