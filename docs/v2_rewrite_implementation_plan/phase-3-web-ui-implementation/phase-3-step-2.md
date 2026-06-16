# Phase 3 Step 2: Core Functionality Verification & Completion

---

## Table of Contents

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=2 --minlevel=1 -->

- [Phase 3 Step 2: Core Functionality Verification & Completion](#phase-3-step-2-core-functionality-verification--completion)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [Verification Tasks (Existing Implementations)](#verification-tasks-existing-implementations)
  - [User Management Implementation (Critical Gap)](#user-management-implementation-critical-gap)
  - [Core Functionality Test Implementation](#core-functionality-test-implementation)
  - [Basic Access Control Implementation](#basic-access-control-implementation)
  - [UI Polish Tasks](#ui-polish-tasks)
  - [Validation & Success Criteria](#validation--success-criteria)
  - [Implementation Notes](#implementation-notes)
  - [Completion Definition](#completion-definition)

<!-- mdformat-toc end -->

---

\*\* Foundation Verification Step\*\* - This step verifies existing implementations work with authentication and completes core user management features that were identified as incomplete.

## Overview

With authentication implemented in [Step 1](./phase-3-step-1.md), this step focuses on verifying all existing implementations work correctly with authenticated APIs and completing the core user management functionality that currently has empty placeholder files.

### Critical Context Notes

- **Verification Focus**: All existing SvelteKit components and SSR load functions must work with authenticated API calls
- **User Management Gap**: Files `frontend/e2e/settings.test.ts` and `frontend/e2e/users.test.ts` are currently empty placeholders
- **Missing Routes**: User detail (`/users/[id]`) and deletion (`/users/[id]/delete`) pages need implementation
- **Project Context**: Project switching functionality affects all data visibility and requires proper context management
- **Role-Based Access**: UI must distinguish between admin-only and user functions with proper permission enforcement. Permissions must be enforced in the backend (using `casbin` in `app/core/authz.py`) and frontend (within the SvelteKit server load functions).
- **Testing Strategy**: Both Mock tests (UI behavior) and E2E tests (authentication flows) required for each feature; tests should be identical in functionality tested. Follow the [full testing architecture](../side_quests/full_testing_architecture.md) document and refer to `.cursor/rules/testing/e2e-docker-infrastructure.mdc` and `.cursor/rules/testing/testing-patterns.mdc` for detailed guidelines.
- **Component Architecture**: Uses Shadcn-Svelte components with Superforms for form handling and SvelteKit actions

## Verification Tasks (Existing Implementations)

Each of the following elements have been implemented in some capacity and with varying degrees of completeness. The goal of this step is to verify that the existing implementations work correctly with authentication and are consistent with the project's architecture and standards. Ensure idiomatic Shadcn-Svelte components are used for all UI elements. Ensure that SvelteKit 5 patterns are used for client-side and server-side code. Maximize code reuse and consistency across the application.

Verify the functionality through direct observation of the application and the output of the tests. Any errors, failures, or warnings should be addressed and resolved. If you are being performed by an AI, run the development docker using `just docker-dev-up-watch` in a background terminal and then use the playwright MCP tools to access the site at `http://localhost:5173` and verify that the functionality works as expected. If a human, run `just docker-dev-up-watch` in a terminal, but use the browser of your choice to access the site at `http://localhost:5173` and verify that the functionality works as expected.

### Dashboard & Layout Verification

- [x] **VERIFY-001**: Dashboard SSR functionality with authentication

  - [x] Verify dashboard loads with authenticated API calls (`DRM-001a`)
    - **UI Context**: Use Shadcn-Svelte `Card`, `CardHeader`, `CardTitle`, `CardContent` components for status cards
    - **Layout**: 12-column responsive grid with uniform card heights and consistent padding
    - **Top Strip Cards**: Active Agents, Running Tasks, Recently Cracked Hashes, Resource Usage with sparklines
    - **Design Reference**: [Dashboard UX Design](../notes/ui_screens/dashboard-ux.md)
  - [x] Verify dashboard cards display correct real-time data (`DRM-001b`)
    - **Live Updates**: Cards update via SSE without manual refresh
    - **Visual Elements**: Include numeric highlights, icons, and optional mini-charts for metrics
    - **Click Actions**: Active Agents card opens Agent Status Sheet (slide-out from right)
  - [x] Verify error handling for failed dashboard API calls (`DRM-001c`)
    - **Error States**: Show stale data indicators if last update >30 seconds
    - **Fallback**: Manual refresh option instead of automatic JSON polling (chosen implementation)
    - **Implementation Note**: Rather than implementing automatic JSON polling fallback, the current implementation provides a manual "Refresh Now" button when SSE connections fail. This gives users control over when to retry and reduces unnecessary background polling traffic.
  - [x] Verify loading states during data fetch (`DRM-001d`)
    - **Loading UI**: Use Shadcn-Svelte Progress components and skeleton loaders
    - **State Management**: Svelte stores for session + SSE management
  - [x] Verify empty state handling (no campaigns, no agents) (`DRM-001e`)
    - **Empty State**: Friendly guidance message ("No active campaigns yet. Join or create one to begin.")
    - **Visual Design**: Follow Shadcn design principles with clear call-to-action

- [x] **VERIFY-002**: Layout and navigation verification

  - [x] Verify sidebar navigation between main sections (`DRM-003a`)
    - **Sidebar Design**: Collapsible sidebar with logo, navigation links (Dashboard, Campaigns, Attacks, Agents, Resources, Users, Settings)
    - **Active States**: Clear active item indicators with visual hierarchy
    - **Navigation Flow**: Smooth transitions between main sections
  - [x] Verify dashboard card click-through to detail views (`DRM-003b`)
    - **Card Actions**: Clickable dashboard cards that navigate to relevant detail pages
    - **Visual Feedback**: Hover states and click feedback for interactive elements
  - [x] Verify breadcrumb navigation consistency (`DRM-003c`)
    - **Breadcrumb Design**: Clear navigation path showing current location in hierarchy
    - **Responsive Behavior**: Breadcrumbs adapt to different screen sizes
  - [x] Verify deep linking to dashboard sections (`DRM-003d`)
    - **URL Structure**: Clean URLs that support direct navigation to specific sections; should be able to go to `/` (dashboard), `/campaigns`, `/attacks`, `/agents`, `/resources`, `/users`, `/settings` and have the correct page load, or be directed to the login page if not authenticated and then redirected to the correct page after login.
    - **State Preservation**: Maintain navigation state across page refreshes
  - [x] Verify responsive sidebar behavior (`UIX-001a`) - Must be tested using the playwright MCP tools and the browser of your choice.
    - **Mobile Adaptation**: Sidebar collapses to hamburger menu on smaller screens
    - **Responsive Breakpoints**: Smooth transitions at 1080x720 and below

### Campaign Management Verification

- [x] **VERIFY-003**: Campaign list functionality with authentication

  - [x] Verify campaign list page loads with SSR data (`CAM-002a`)
    - **UI Layout**: Accordion-style rows with expandable campaign details
    - **Row Content**: Campaign name, progress bar (keyspace-weighted), state badges with color coding
    - **Status Colors**: Running=purple, Completed=green, Error=red, Paused=gray
    - **Sorting**: Default sort by Running campaigns first, then most recently updated
    - **Implementation Note**: The campaign list is now implemented as a table with a search input and a status filter. The campaign rows contain a disclosure triangle to expand a sub-table with the campaign's attacks.
  - [x] Verify campaign pagination and search functionality (`CAM-002b`)
    - **Components**: Use Shadcn-Svelte Table with built-in pagination
    - **Search**: Real-time filtering with search input component
    - **Status**: [x] Verified working - search filters campaigns by name and summary, pagination works with URL parameters, localStorage persistence for filters
  - [x] Verify campaign filtering by status (draft, active, archived, paused, completed, error) (`CAM-002c`)
    - **Filter UI**: Popover with a checkbox for each status. Only selected statuses are shown in the table. Filtering is done in the within the SvelteKit store.
    - **Visual Feedback**: Active filters clearly highlighted
    - **Current Status**: The popover is implemented, but filtering is not wired up to the store and some of the statuses are not being displayed.
  - [x] Verify campaign sorting by various columns (`CAM-002d`)
    - **Sort Options**: By status, progress, last updated, name
    - **UI Elements**: Column headers with sort indicators
    - **Current Status**: The sorting is not implemented in the data table or the store.
  - [x] Verify campaign detail view navigation (`CAM-002e`)
    - **Navigation**: Breadcrumb navigation and smooth transitions
    - **Deep Linking**: Support direct links to campaign details

- [x] **VERIFY-004**: Campaign details functionality

  - [x] Verify campaign detail page loads with attack list (`CAM-003a`)
    - **Page Layout**: Dynamic title showing campaign name, table-like attack grid
    - **Attack Table**: 6 columns (Attack, Language, Length, Settings, Passwords, Complexity)
    - **Visual Elements**: Blue-linked settings summary, dot-based complexity meter (0-5 dots)
    - **Design Reference**: [Campaign List View](../notes/ui_screens/campaign_list_view.md)
  - [ ] Verify campaign progress tracking and metrics display (`CAM-003b`)
    - **Progress Bars**: Keyspace-weighted with dynamic color by state
    - **Metrics**: Real-time ETA, completion percentage, active agent count
  - [ ] Verify real-time campaign status updates (`CAM-003e`)
    - **Live Updates**: Status changes via SSE, progress bar animations
    - **State Indicators**: Visual badges with appropriate icons (⚡ running, [x] completed)
  - [ ] Verify campaign attack summary display (`CAM-003g`)
    - **Summary Format**: "⚡ 3 attacks / 1 running / ETA 3h" with state-coded icons
    - **Action Menu**: Gear icon per row with context menu (Edit, Duplicate, Move, Remove)

### Attack Management Verification

- [ ] **VERIFY-005**: Attack configuration functionality
  - [ ] Verify attack type selection and switching (`ATT-002a`)
    - **Modal Design**: Flowbite modal with guided wizard steps (no tabs to reduce cognitive load)
    - **Type Selection**: Radio buttons for Dictionary/Mask/Brute/Hybrid attack types
    - **UI Flow**: Attack type selection → resource configuration → parameter setup
    - **Design Reference**: [Dictionary Attack Editor](../notes/ui_screens/new_dictionary_attack_editor.md)
  - [ ] Verify resource selection (searchable dropdowns) (`ATT-002b`)
    - **Dropdown UI**: Searchable select components showing resource names with metadata
    - **Resource Display**: Format as "filename.txt (N words/rules)" with file size info
    - **Organization**: Group by resource type (wordlists, rules, masks, charsets)
  - [ ] Verify attack parameter validation (`ATT-002c`)
    - **Form Validation**: Real-time client-side validation with server-side confirmation
    - **Error Display**: Clear error messages near relevant form fields
    - **Input Constraints**: Length ranges (min/max), pattern validation where applicable
  - [ ] Verify keyspace estimation and complexity calculation (`ATT-002d`)
    - **API Integration**: Live keyspace updates via `/api/v1/web/attacks/estimate` endpoint
    - **Complexity UI**: Dot-based visual meter (●●●○○) with tooltip descriptions
    - **Display Format**: "Passwords to check: N" with comma-separated thousands
  - [ ] Verify attack preview and summary (`ATT-002e`)
    - **Preview Panel**: Show attack configuration summary before saving
    - **Modifier Display**: Visual chips/tags for applied rules and transformations
    - **Save/Cancel**: Clear action buttons with appropriate styling

### Resource Management Verification

- [ ] **VERIFY-006**: Resource list and detail functionality
  - [ ] Verify resource list page loads with SSR data (`RES-001a`)
    - **Table Layout**: Resource name, type, size, upload date, usage count columns
    - **Resource Types**: Clear visual indicators for wordlists, rules, masks, charsets
    - **Metadata Display**: Show file size, line count, and last modified information
  - [ ] Verify resource filtering by type (`RES-001b`)
    - **Filter Controls**: Type-based filter buttons with count badges
    - **Visual Grouping**: Group resources by type with clear section headers
  - [ ] Verify resource search functionality (`RES-001c`)
    - **Search Interface**: Real-time search across resource names and descriptions
    - **Search Results**: Highlight matching terms in search results
  - [ ] Verify resource pagination with large datasets (`RES-001d`)
    - **Pagination UI**: Use Shadcn-Svelte pagination components
    - **Performance**: Efficient loading for large resource collections
  - [ ] Verify resource detail view navigation (`RES-001e`)
    - **Detail Pages**: Comprehensive resource information with usage history
    - **Navigation**: Smooth transitions from list to detail views
  - [ ] Verify resource preview for supported file types (`RES-003a`)
    - **Preview Interface**: Show file content preview for text-based resources
    - **Content Display**: Syntax highlighting for rules, plain text for wordlists

### Agent Management Verification

- [ ] **VERIFY-007**: Agent list and details functionality
  - [ ] Verify agent list page loads with real-time status (`AGT-001a`)
    - **Table Layout**: Agent Name+OS, Status, Temperature, Utilization, Current Rate, Average Rate, Current Job columns
    - **Status Indicators**: Color-coded badges ([GREEN] Online, [YELLOW] Idle, [RED] Offline)
    - **Real-time Updates**: Live data from DeviceStatus, TaskStatus, HashcatGuess via SSE
    - **Design Reference**: [Agent Notes](../notes/agent_notes.md)
  - [ ] Verify agent filtering by status (online, offline, error) (`AGT-001b`)
    - **Filter UI**: Status filter buttons with visual state indication
    - **Status Categories**: Online, Offline, Error, Idle with count badges
  - [ ] Verify agent search and sorting functionality (`AGT-001c`)
    - **Search**: Real-time text search across agent names and current jobs
    - **Sort Options**: By status, performance metrics, last seen, temperature
  - [ ] Verify agent performance metrics display (`AGT-001d`)
    - **Performance Cards**: Individual agent cards with donut charts for utilization
    - **Temperature Display**: Show actual °C or "Not Monitored" for -1 values
    - **Sparklines**: 8-hour trend lines for guess rate over time (SVG-based)
  - [ ] Verify agent health monitoring and alerts (`AGT-001e`)
    - **Health Status**: Visual health indicators with alert badges for issues
    - **Alert System**: Real-time notifications for agent errors or disconnections

## User Management Implementation (Critical Gap)

### Complete Empty Placeholder Files

\*\* Technical Context\*\*: These test files are completely empty and need full implementation. Settings involves self-service profile management (name, email, password), while users involves admin-controlled role assignment and project membership. All forms must use idiomatic Shadcn-Svelte components.

- [ ] **USER-001**: Implement `frontend/e2e/settings.test.ts` (currently empty)

  - [ ] User profile editing (self-service name and email updates) (`USR-003a`)
    - **Form Design**: Use Superforms v2 with Shadcn-Svelte form components
    - **Layout**: Clean profile form with editable name, email fields
    - **Validation**: Real-time validation with error display near fields
    - **Save Pattern**: Auto-save or explicit save with success feedback
  - [ ] Password change functionality with immediate confirmation (`USR-003b`)
    - **Security UX**: Current password → new password → confirm pattern
    - **Validation**: Password strength indicator, matching confirmation
    - **Feedback**: Immediate success/error toast notifications
  - [ ] User preferences and settings (`USR-003c`)
    - **Settings Groups**: Organize by categories (Account, Notifications, Appearance)
    - **Theme Toggle**: Dark mode switching with system detection
    - **Preferences**: Update intervals, notification settings
  - [ ] API key generation and management (`USR-003d`)
    - **Key Display**: Masked API keys with copy-to-clipboard functionality
    - **Generation UI**: "Generate New Key" button with secure display modal
    - **Management**: List of active keys with creation dates and revoke options
  - [ ] Activity history and audit logs (`USR-003e`)
    - **Timeline View**: Chronological list of user actions and login history
    - **Filtering**: Date range picker, action type filters
    - **Detail Display**: Show timestamp, action, IP address, user agent

- [ ] **USER-002**: Implement `frontend/e2e/users.test.ts` (admin-only) (currently empty)

  - [ ] User list page with role-based visibility (`USR-001a`)
    - **Table Design**: User name, email, role, project associations, last login, status columns
    - **Role Indicators**: Visual badges for Admin, Project Admin, User roles with color coding
    - **Status Display**: Active/Inactive status with clear visual differentiation
    - **Actions Column**: Gear icon menu for Edit, Change Role, Deactivate options
  - [ ] New user creation form (`USR-001b`)
    - **Modal Form**: Flowbite modal with user creation wizard
    - **Required Fields**: Username, email, initial password, role selection
    - **Role Selection**: Radio buttons or dropdown with role descriptions
    - **Project Assignment**: Multi-select for project memberships during creation
  - [ ] User role assignment and validation (`USR-001c`)
    - **Role Management**: Clear role hierarchy display (Admin > Project Admin > User)
    - **Permission Preview**: Show what permissions each role grants
    - **Validation**: Prevent role escalation beyond current user's permissions
  - [ ] User project association management (`USR-001d`)
    - **Project List**: Checkboxes or toggle switches for project membership
    - **Access Levels**: Different access levels per project if supported
    - **Visual Feedback**: Clear indication of current vs. proposed changes
  - [ ] User deletion with cascade handling (`USR-001e`)
    - **Warning Modal**: Impact assessment showing affected campaigns, attacks, resources
    - **Confirmation Pattern**: Type username to confirm deletion (destructive action)
    - **Cascade Options**: Choose what happens to user's created content

### User Detail and Deletion Pages Implementation

- [ ] **USER-003**: Create user detail pages (`/users/[id]/+page.svelte`)

  - [ ] User detail page loads with complete profile information (`USR-004a`)
    - **Page Layout**: Clean profile layout with user avatar, basic info, and tabbed sections
    - **Information Display**: User name, email, role, last login, account status
    - **Permission Context**: Show user's project memberships and access levels
  - [ ] User profile editing and updates (`USR-004b`)
    - **Edit Mode**: Inline editing or modal form for profile updates
    - **Form Design**: Use Superforms v2 with Shadcn-Svelte components
    - **Save Feedback**: Clear success/error feedback after updates
  - [ ] User role management and project associations (`USR-004c`)
    - **Role Interface**: Dropdown or radio selection for role changes (admin only)
    - **Project Assignment**: Multi-select interface for project memberships
    - **Permission Preview**: Show what permissions each role grants
  - [ ] User activity history and audit trails (`USR-004d`)
    - **Activity Timeline**: Chronological list of user actions and login history
    - **Event Details**: Show timestamp, action type, IP address, affected resources
    - **Filtering**: Date range and action type filters
  - [ ] User permission validation and enforcement (`USR-004e`)
    - **Access Control**: Hide/disable actions based on current user permissions
    - **Visual Indicators**: Clear distinction between viewable and editable elements
  - [ ] User profile form validation and error handling (`USR-004f`)
    - **Real-time Validation**: Immediate feedback on form field changes
    - **Error Display**: Clear error messages positioned near relevant fields

- [ ] **USER-004**: Create user deletion flow (admin-only) (`/users/[id]/delete/+page.svelte`)

  - [ ] User deletion page loads with impact assessment (`USR-005a`)
    - **Impact Display**: Show comprehensive impact of user deletion
    - **Warning Layout**: Prominent warning messages about irreversible action
    - **Data Summary**: List affected campaigns, attacks, resources, and dependencies
  - [ ] Display of user's associated campaigns, attacks, and resources (`USR-005b`)
    - **Association Lists**: Organized lists of user's created/owned content
    - **Impact Indicators**: Show what will be deleted vs. transferred vs. orphaned
    - **Resource Counts**: Clear counts of affected items by category
  - [ ] Warning messages for active user sessions (`USR-005c`)
    - **Session Alerts**: Prominent warnings if user has active sessions
    - **Active Work**: Show any running campaigns or ongoing tasks
    - **Timing Recommendations**: Suggest optimal deletion timing
  - [ ] Confirmation workflow with typed verification (`USR-005d`)
    - **Confirmation Pattern**: Require typing username to confirm deletion
    - **Multi-step Process**: Progressive confirmation with multiple checkpoints
    - **Cancel Options**: Clear escape routes at each step
  - [ ] Cascade deletion options and warnings (`USR-005e`)
    - **Cascade Choices**: Options for handling user's content (delete, transfer, orphan)
    - **Warning Messages**: Clear explanations of each cascade option's impact
    - **Dependency Mapping**: Show how deletion affects other users/content
  - [ ] User deletion permission validation (`USR-005f`)
    - **Permission Checks**: Verify admin permissions before allowing deletion
    - **Role Restrictions**: Prevent deletion of other admins by non-super-admins
    - **Audit Trail**: Log all deletion attempts and confirmations

### Project Management Completion

- [ ] **PROJECT-001**: Complete project management functionality (admin-only)
  - [ ] Project creation form (admin only) (`USR-002b`)
  - [ ] Project user management (`USR-002c`)
  - [ ] Project settings and configuration (`USR-002d`)
  - [ ] Project deletion with impact assessment (`USR-002e`)

### Project Selection & Switching Implementation

- [ ] **PROJECT-002**: Implement project selection and switching
  - [ ] Single project auto-selection on login (store last selected project in browser local storage, prompt if no project selected) (`ASM-002a`)
  - [ ] Multi-project selection modal on login (`ASM-002b`)
  - [ ] Project switching via global project selector (`ASM-002c`)
  - [ ] Project context persistence across navigation (`ASM-002d`)
  - [ ] Project-scoped data visibility validation (`ASM-002e`)
  - [ ] Project context awareness in all UI elements (`ASM-002f`)
  - [ ] Project-based resource filtering and access control (`ASM-002g`)

## Core Functionality Test Implementation

The items below represent task items that were either implemented or verified in the previous steps. Now we need to implement proper automated E2E tests to continue to verify that the functionality works as expected. Refer to the [full testing architecture](../side_quests/full_testing_architecture.md) document for more details on the testing architecture and the test structure and verification items above for the associated tasks being tested. In cases where the test is for full E2E (denoted by (E2E) in the test structure), there may be a similar mocked test that can copied and modified to create the full E2E test.

### Testing Guidelines & Requirements

\*\* Critical Testing Context:\*\*

- **Test Structure**: All user-facing functionality must have both E2E tests (mocked and full E2E). Strictly follow existing test structure and naming conventions as described in the [full testing architecture](../side_quests/full_testing_architecture.md) document.
- **Test Execution**:
  - Run `just test-frontend` for mocked E2E tests (fast, no backend required)
  - Run `just test-e2e` for full E2E tests (requires Docker setup, slower but complete integration testing)
  - **Important**: Do not run full E2E tests directly - they require setup code and must run via the `just test-e2e` command
- **Test Utilities**: Use or reuse existing test utils and helpers in `frontend/tests/test-utils.ts` for consistency and maintainability
- **API Integration**: The OpenAPI spec for the current backend is in `contracts/current_api_openapi.json` and should be used for all backend API calls, with Zod objects generated from the spec in `frontend/src/lib/schemas/`
- **Test Notation**: When tasks include notations like (E2E) or (Mock), tests must be created or updated to cover that specific functionality and confirm it works as expected

### User Management Testing

- [ ] **TEST-USR-001**: User Management Tests

  - [ ] **USR-001a**: User list page with role-based visibility (E2E + Mock)
  - [ ] **USR-001b**: New user creation form (E2E + Mock)
  - [ ] **USR-001c**: User role assignment and validation (E2E + Mock)
  - [ ] **USR-001d**: User project association management (E2E + Mock)
  - [ ] **USR-001e**: User deletion with cascade handling (E2E + Mock)
  - [ ] **USR-001f**: Clear permission boundaries in UI (Mock)
  - [ ] **USR-001g**: Role-based UI element separation (Mock)

- [ ] **TEST-USR-003**: Profile & Settings Tests

  - [ ] **USR-003a**: User profile editing (self-service updates) (E2E + Mock)
  - [ ] **USR-003b**: Password change functionality (E2E + Mock)
  - [ ] **USR-003c**: User preferences and settings (E2E + Mock)
  - [ ] **USR-003d**: API key generation and management (E2E + Mock)
  - [ ] **USR-003e**: Activity history and audit logs (E2E + Mock)
  - [ ] **USR-003f**: Profile change validation and feedback (Mock)
  - [ ] **USR-003g**: Self-service vs admin function distinction (Mock)

### Project Management Testing

- [ ] **TEST-USR-002**: Project Management Tests

  - [ ] **USR-002a**: Project list page with membership info (E2E + Mock)
  - [ ] **USR-002b**: Project creation form (admin only) (E2E + Mock)
  - [ ] **USR-002c**: Project user management (E2E + Mock)
  - [ ] **USR-002d**: Project settings and configuration (E2E + Mock)
  - [ ] **USR-002e**: Project deletion with impact assessment (E2E + Mock)

- [ ] **TEST-ASM-002**: Project Selection & Switching Tests

  - [ ] **ASM-002a**: Single project auto-selection on login (E2E)
  - [ ] **ASM-002b**: Multi-project selection modal on login (E2E)
  - [ ] **ASM-002c**: Project switching via global selector (E2E + Mock)
  - [ ] **ASM-002d**: Project context persistence across navigation (E2E)
  - [ ] **ASM-002e**: Project-scoped data visibility validation (E2E)
  - [ ] **ASM-002f**: Project context awareness in UI elements (Mock)
  - [ ] **ASM-002g**: Project-based resource filtering and access control (E2E)

### Dashboard and Navigation Testing

- [ ] **TEST-DRM-001**: Dashboard Data Loading Tests

  - [ ] **DRM-001a**: Dashboard loads with SSR data (E2E + Mock)
  - [ ] **DRM-001b**: Dashboard cards display correct real-time data (E2E + Mock)
  - [ ] **DRM-001c**: Error handling for failed dashboard API calls (Mock)
  - [ ] **DRM-001d**: Loading states during data fetch (Mock)
  - [ ] **DRM-001e**: Empty state handling (no campaigns, no agents) (Mock)

- [ ] **TEST-DRM-003**: Dashboard Navigation Tests

  - [ ] **DRM-003a**: Sidebar navigation between main sections (E2E + Mock)
  - [ ] **DRM-003b**: Dashboard card click-through to detail views (E2E + Mock)
  - [ ] **DRM-003c**: Breadcrumb navigation consistency (Mock)
  - [ ] **DRM-003d**: Deep linking to dashboard sections (E2E)
  - [ ] **DRM-003e**: Mobile responsive navigation (Mock)

### Form Behavior Testing

- [ ] **TEST-UIX-002**: Form Behavior Tests
  - [ ] **UIX-002a**: Form validation and error display (Mock)
  - [ ] **UIX-002b**: Progressive enhancement (JS disabled) (E2E)
  - [ ] **UIX-002c**: Form persistence during navigation (E2E)
  - [ ] **UIX-002d**: Multi-step form navigation (Mock)
  - [ ] **UIX-002e**: Form submission loading states (Mock)
  - [ ] **UIX-002f**: Server-side validation with error reporting (E2E)
  - [ ] **UIX-002g**: Superforms integration consistency (Mock)

## Basic Access Control Implementation

All functionality is to be developed using SvelteKit 5 patterns and idiomatic Shadcn-Svelte components. All forms must use Superforms v2 with SvelteKit actions, Zod validation, and Shadcn-Svelte form components. All forms must be validated on the server side and client side. All forms must be validated using the OpenAPI spec in `contracts/current_api_openapi.json` and the Zod objects in `frontend/src/lib/schemas/`. All forms must be validated using the OpenAPI spec in `contracts/current_api_openapi.json` and the Zod objects in `frontend/src/lib/schemas/`. All forms must be validated using the OpenAPI spec in `contracts/current_api_openapi.json` and the Zod objects in `frontend/src/lib/schemas/`.

Verify the functionality through direct observation of the application and the output of the tests. Any errors, failures, or warnings should be addressed and resolved. If you are being performed by an AI, run the development docker using `just docker-dev-up-watch` in a background terminal and then use the playwright MCP tools to access the site at `http://localhost:5173` and verify that the functionality works as expected. If a human, run `just docker-dev-up-watch` in a terminal, but use the browser of your choice to access the site at `http://localhost:5173` and verify that the functionality works as expected.

### Role-Based Access Control Foundation

- [ ] **ACCESS-001**: Implement basic RBAC UI patterns
  - [ ] Admin-only functionality restrictions (`ACS-001a`)
  - [ ] Project admin scope limitations (`ACS-001b`)
  - [ ] Regular user permission enforcement (`ACS-001c`)
  - [ ] Cross-project access prevention (`ACS-001d`)
  - [ ] Role-based menu and action visibility

### Access Control Testing

- [ ] **TEST-ACS-001**: Role-Based Access Control Tests
  - [ ] **ACS-001a**: Admin-only functionality restrictions (E2E + Mock)
  - [ ] **ACS-001b**: Project admin scope limitations (E2E + Mock)
  - [ ] **ACS-001c**: Regular user permission enforcement (E2E + Mock)
  - [ ] **ACS-001d**: Cross-project access prevention (E2E)

## UI Polish Tasks

### Layout and Responsive Design

- [ ] **POLISH-001**: Complete layout implementation
  - [ ] Modal overlay and z-index management (`UIX-001d`)
  - [ ] Mobile navigation menu (`UIX-001b`) - Suffice to have a hamburger menu that opens a drawer with the sidebar content
  - [ ] Responsive design validation across viewports

### Theme Implementation

**Style Guide**: Use the Catppuccin Macchiato theme (with DarkViolet as the accent color) in dark mode and the Catppuccin Latte theme in light mode. Refer to the [style guide](../development/style-guide.md) for more specifics.

- [ ] **POLISH-002**: Consistent styling
  - [ ] Dark mode toggle functionality (`UIX-001e`) - Use the NightModeToggleButton component with default dark mode - See [Shadcn Svelte Dark Mode](https://www.shadcn-svelte.com/docs/dark-mode/svelte) for more details.
  - [ ] Theme switching without page refresh (`UIX-004b`)
  - [ ] Theme preference persistence across sessions (`UIX-004c`)
  - [ ] Catppuccin theme consistency (`UIX-004d`)
  - [ ] System theme detection and auto-switching (`UIX-004f`) - use `mode-watcher` to detect system theme and auto-switch to the correct theme. See [Shadcn Svelte Dark Mode](https://www.shadcn-svelte.com/docs/dark-mode/svelte) for more details.

## Validation & Success Criteria

### Core Functionality Validation

- [ ] **VALIDATE-001**: All existing features work with authentication
  - [ ] Dashboard loads and displays data correctly
  - [ ] Campaign, attack, resource, and agent management functional
  - [ ] Forms submit successfully with proper validation
  - [ ] Navigation works across all sections

### User Management Validation

- [ ] **VALIDATE-002**: User management is fully functional
  - [ ] Empty test files are now implemented and passing
  - [ ] User creation, editing, and deletion workflows complete
  - [ ] Project selection and switching works properly
  - [ ] Role-based access control functions correctly

### Test Coverage Validation

- [ ] **VALIDATE-003**: Test coverage is comprehensive
  - [ ] All core functionality has both Mock and E2E tests where applicable
  - [ ] Test environment detection works properly
  - [ ] All tests pass in both Mock and E2E environments
  - [ ] Performance is acceptable for core workflows

## Implementation Notes

### Key Implementation Patterns

- **Component Architecture**: Use idiomatic Shadcn-Svelte components with proper composition and accessibility
- **SvelteKit Patterns**: Follow idiomatic SvelteKit 5 patterns with runes ($state, $derived, $effect), actions, and load functions
- **Form Handling**: All forms use Superforms v2 with SvelteKit actions, Zod validation, and Shadcn-Svelte form components
- **SSR Load Functions**: Located in `+page.server.ts` files, handle authenticated API calls and error states
- **Role-Based UI**: Use `$page.data.user.role` for conditional rendering of admin-only features
- **Project Context**: Access via `$page.data.project` and update with project switching functionality
- **Error Handling**: 401 redirects to login, 404 shows error page, 500 logs and shows generic error
- **Environment Detection**: Check `PLAYWRIGHT_TEST` or `NODE_ENV=test` for mock data fallbacks
- **E2E Testing Structure**: `frontend/e2e/` contains mocked E2E tests (fast, no backend), `frontend/tests/e2e/` contains full E2E tests (slower, real backend). Configs: `playwright.config.ts` (mocked) vs `playwright.config.e2e.ts` (full backend)

### UI/UX Requirements & Standards

- **Responsive Design**: Ensure the interface is polished and follows project standards. While mobile support is not a priority, it should be functional and usable on modern desktop browsers and tablets from `1080x720` resolution on up. It is reasonable to develop for support of mobile resolutions.
- **Offline Capability**: Ability to operate entirely without internet connectivity is a priority. No functionality should depend on public CDNs or other internet-based services.
- **API Integration**: The OpenAPI spec for the current backend is in `contracts/current_api_openapi.json` and should be used for all backend API calls, with Zod objects having been generated from the spec in `frontend/src/lib/schemas/`.
- **Testing Coverage**: All forms must be validated using the OpenAPI spec and the Zod objects. All forms must be validated on both server side and client side.

### Priority Focus

This step prioritizes:

1. Verifying existing implementations work with authentication
2. Completing the user management gap (empty test files)
3. Implementing basic access control patterns
4. Establishing solid test coverage for core features

### Test Implementation Strategy

- Mock tests focus on UI behavior and validation
- E2E tests focus on authentication flows and data persistence
- Both test types should be implemented for critical user workflows
- Environment detection ensures tests work in all scenarios

### User Management Context

User management was identified as a major gap with empty placeholder files. This step completes:

- Settings page functionality (`settings.test.ts`)
- User management workflows (`users.test.ts`)
- User detail and deletion pages
- Project selection and switching

## Completion Definition

This step is complete when:

1. All existing implementations verified to work with authentication
2. User management functionality fully implemented and tested
3. Basic access control patterns implemented across the application
4. Core functionality test coverage is comprehensive (Mock + E2E)
5. Theme system and responsive design are functional
6. All validation criteria pass without errors
