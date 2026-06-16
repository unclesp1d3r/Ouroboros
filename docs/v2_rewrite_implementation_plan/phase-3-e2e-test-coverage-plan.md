# Phase 3: Complete E2E Test Coverage Plan

This document defines the comprehensive e2e test coverage required for Ouroboros Phase 3, derived from the user flows in `user_journey_flowchart.mmd` and `user_flows_notes.md`. These tests will validate the complete user experience from frontend through backend integration.

---

## Table of Contents

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=2 --minlevel=1 -->

- [Phase 3: Complete E2E Test Coverage Plan](#phase-3-complete-e2e-test-coverage-plan)
  - [Table of Contents](#table-of-contents)
  - [Testing Strategy](#testing-strategy)
  - [Missing Test Coverage Analysis](#missing-test-coverage-analysis)
  - [Authentication & Session Management Tests](#authentication--session-management-tests)
  - [Dashboard & Real-Time Monitoring Tests](#dashboard--real-time-monitoring-tests)
  - [Campaign Management Tests](#campaign-management-tests)
  - [Attack Configuration Tests](#attack-configuration-tests)
  - [Resource Management Tests](#resource-management-tests)
  - [Hash List Management Tests](#hash-list-management-tests)
  - [Agent Management Tests](#agent-management-tests)
  - [User & Project Management Tests](#user--project-management-tests)
  - [Access Control & Security Tests](#access-control--security-tests)
  - [Monitoring & System Health Tests](#monitoring--system-health-tests)
  - [Notification & Toast System Tests](#notification--toast-system-tests)
  - [UI/UX & Responsive Design Tests](#uiux--responsive-design-tests)
  - [Integration & Workflow Tests](#integration--workflow-tests)
  - [Performance & Load Tests](#performance--load-tests)
  - [Test Implementation Priority](#test-implementation-priority)
  - [Test Infrastructure Requirements](#test-infrastructure-requirements)
  - [Success Metrics](#success-metrics)
  - [Notes for Implementation](#notes-for-implementation)
  - [Current Test Coverage Analysis](#current-test-coverage-analysis)

<!-- mdformat-toc end -->

---

## Testing Strategy

### Three-Tier Architecture Integration

- **Layer 1**: Backend tests (Python + testcontainers) - [x] Complete
- **Layer 2**: Frontend mocked tests (Playwright + mocked APIs) - [x] Complete
- **Layer 3**: Full E2E tests (Playwright + real Docker backend) - Infrastructure complete, authentication pending

### Test Environment Requirements

- Docker-based backend stack with seeded test data
- SSR authentication implementation for authenticated flows
- Real database with predictable test data
- MinIO object storage for file uploads
- Session-based authentication flow

---

## Missing Test Coverage Analysis

Based on examination of the frontend source code in `/src`, the following UI elements and pages are **NOT** covered in the current e2e test plan:

### Missing Pages and Routes

1. **Resource Upload Page** (`/resources/upload/+page.svelte`)

   - File upload interface with drag-and-drop
   - Resource type detection and validation
   - Upload progress indicators
   - Metadata input forms

2. **Campaign Edit Page** (`/campaigns/[id]/edit/+page.svelte`)

   - Campaign modification workflows
   - Attack reordering within existing campaigns
   - Campaign settings updates

3. **User Detail Pages** (`/users/[id]/+page.svelte`)

   - Individual user profile viewing and editing
   - User-specific settings and permissions

4. **User Delete Page** (`/users/[id]/delete/+page.svelte`)

   - User deletion confirmation workflows
   - Impact assessment display

5. **Campaign Delete Page** (`/campaigns/[id]/delete/+page.svelte`)

   - Campaign deletion with impact assessment
   - Cascade deletion warnings

6. **Attack Creation/Edit Pages** (`/attacks/new/+page.svelte`, `/attacks/[id]/`)

   - Standalone attack creation outside of campaign context
   - Attack modification workflows

7. **Resource Detail Pages** (`/resources/[id]/+page.svelte`)

   - Individual resource viewing and editing
   - Content preview and metadata management

8. **Error Pages** (`/resources/+error.svelte`, `/campaigns/[id]/+error.svelte`)

   - Error state handling and user guidance
   - Error recovery workflows

### Missing UI Components and Features

1. **Project Selection Modal** (Used during login for multi-project users)

   - Project switching interface
   - Project context awareness

2. **Toast Notification System** (`Toast.svelte`)

   - Real-time notification display
   - Notification persistence and dismissal

3. **Night Mode Toggle** (`NightModeToggleButton.svelte`)

   - Dark/light theme switching
   - Theme persistence

4. **Advanced Search and Filtering**

   - Cross-page search functionality
   - Complex filter combinations
   - Saved search preferences

5. **File Upload Progress Tracking**

   - Large file upload handling
   - Upload cancellation
   - Resume functionality

6. **Resource Content Editing**

   - Inline editing for small files
   - Syntax highlighting for different resource types
   - Line-by-line editing capabilities

7. **Real-Time Progress Updates**

   - SSE connection management
   - Live dashboard updates
   - Connection recovery handling

---

## Authentication & Session Management Tests

### ASM-001: Login Flow

- [ ] **ASM-001a**: Successful login with valid credentials
- [ ] **ASM-001b**: Failed login with invalid credentials
- [ ] **ASM-001c**: Login form validation (empty fields, invalid email format)
- [ ] **ASM-001d**: Session persistence across page refreshes
- [ ] **ASM-001e**: Redirect to login page when accessing protected routes unauthenticated
- [ ] **ASM-001f**: "Remember me" checkbox functionality and persistence
- [ ] **ASM-001g**: Login loading states and error display

### ASM-002: Project Selection & Switching

- [ ] **ASM-002a**: Single project auto-selection on login
- [ ] **ASM-002b**: Multi-project selection modal on login
- [ ] **ASM-002c**: Project switching via global project selector
- [ ] **ASM-002d**: Project context persistence across navigation
- [ ] **ASM-002e**: Project-scoped data visibility validation
- [ ] **ASM-002f**: Project context awareness in all UI elements (verify all components respect current project)
- [ ] **ASM-002g**: Project-based resource filtering and access control validation

### ASM-003: Session Management

- [ ] **ASM-003a**: Session timeout handling with modal prompt
- [ ] **ASM-003b**: Token refresh on expired JWT
- [ ] **ASM-003c**: Logout functionality with session cleanup
- [ ] **ASM-003d**: Concurrent session handling
- [ ] **ASM-003e**: Session expiry redirect to login

---

## Dashboard & Real-Time Monitoring Tests

### DRM-001: Dashboard Data Loading

- [ ] **DRM-001a**: Dashboard loads with SSR data (agents, campaigns, stats)
- [ ] **DRM-001b**: Dashboard cards display correct real-time data
- [ ] **DRM-001c**: Error handling for failed dashboard API calls
- [ ] **DRM-001d**: Loading states during data fetch
- [ ] **DRM-001e**: Empty state handling (no campaigns, no agents)

### DRM-002: Real-Time Updates

- [ ] **DRM-002a**: Campaign progress updates via SSE (lightweight trigger notifications, not full data)
- [ ] **DRM-002b**: Agent status updates in real-time (verify EventSource reconnection handling)
- [ ] **DRM-002c**: Crack notifications via toast system (test batching logic for >5 events/sec)
- [ ] **DRM-002d**: Task completion notifications with targeted component refresh
- [ ] **DRM-002e**: System health status updates
- [ ] **DRM-002f**: SSE connection cleanup and timeout handling
- [ ] **DRM-002g**: Project-scoped event filtering (users only see events for their current project)

### DRM-003: Dashboard Navigation

- [ ] **DRM-003a**: Sidebar navigation between main sections
- [ ] **DRM-003b**: Dashboard card click-through to detail views
- [ ] **DRM-003c**: Breadcrumb navigation consistency
- [ ] **DRM-003d**: Deep linking to dashboard sections
- [ ] **DRM-003e**: Mobile responsive navigation

---

## Campaign Management Tests

### CAM-001: Campaign Creation Flow

- [ ] **CAM-001a**: New campaign wizard - basic campaign creation
- [ ] **CAM-001b**: Campaign creation with hashlist upload
- [ ] **CAM-001c**: Campaign creation with existing hashlist selection
- [ ] **CAM-001d**: Campaign metadata validation (name, description)
- [ ] **CAM-001e**: DAG mode toggle and configuration

### CAM-002: Campaign List & Navigation

- [ ] **CAM-002a**: Campaign list page loads with SSR data
- [ ] **CAM-002b**: Campaign pagination and search functionality
- [ ] **CAM-002c**: Campaign filtering by status (running, completed, paused)
- [ ] **CAM-002d**: Campaign sorting by various columns
- [ ] **CAM-002e**: Campaign detail view navigation

### CAM-003: Campaign Details & Management

- [ ] **CAM-003a**: Campaign detail page loads with attack list (verify attack positioning/ordering display)
- [ ] **CAM-003b**: Campaign progress tracking and metrics display (real-time updates every 5 seconds)
- [ ] **CAM-003c**: Attack reordering within campaign (drag-and-drop with keyboard support for accessibility)
- [ ] **CAM-003d**: Campaign toolbar actions (start, pause, export) with bulk operations support
- [ ] **CAM-003e**: Real-time campaign status updates (lifecycle state clarity with visual indicators)
- [ ] **CAM-003f**: Attack context menu actions (edit, duplicate, delete, move up/down/top/bottom)
- [ ] **CAM-003g**: Campaign attack summary display (type, config, keyspace, complexity, comment)

### CAM-004: Campaign Lifecycle Operations

- [ ] **CAM-004a**: Start campaign with task generation
- [ ] **CAM-004b**: Pause running campaign with confirmation
- [ ] **CAM-004c**: Resume paused campaign
- [ ] **CAM-004d**: Stop campaign with impact assessment
- [ ] **CAM-004e**: Campaign deletion with permission checks

### CAM-005: Campaign Export/Import

- [ ] **CAM-005a**: Export campaign as JSON template
- [ ] **CAM-005b**: Import campaign from JSON file
- [ ] **CAM-005c**: Campaign template validation on import
- [ ] **CAM-005d**: Campaign cloning functionality
- [ ] **CAM-005e**: Export cracked hashes from campaign

### CAM-006: Campaign Edit & Modification (NEW)

- [ ] **CAM-006a**: Campaign edit page loads with current settings
- [ ] **CAM-006b**: Campaign metadata modification (name, description, notes)
- [ ] **CAM-006c**: Campaign settings updates (DAG mode, scheduling)
- [ ] **CAM-006d**: Attack reordering within existing campaigns
- [ ] **CAM-006e**: Campaign edit validation and error handling
- [ ] **CAM-006f**: Campaign edit permission enforcement

### CAM-007: Campaign Deletion Flow (NEW)

- [ ] **CAM-007a**: Campaign deletion page loads with impact assessment
- [ ] **CAM-007b**: Display of associated attacks, tasks, and resources
- [ ] **CAM-007c**: Warning messages for active/running campaigns
- [ ] **CAM-007d**: Confirmation workflow with typed verification
- [ ] **CAM-007e**: Cascade deletion warnings and options
- [ ] **CAM-007f**: Campaign deletion permission validation

---

## Attack Configuration Tests

### ATT-001: Attack Creation Wizard

- [ ] **ATT-001a**: Dictionary attack creation with wordlist selection (smart defaults for hash type ranges)
- [ ] **ATT-001b**: Mask attack creation with mask patterns (inline editing with real-time validation)
- [ ] **ATT-001c**: Brute force attack configuration (checkbox charset selection with range slider)
- [ ] **ATT-001d**: Hybrid attack setup (dictionary + mask)
- [ ] **ATT-001e**: Previous passwords attack configuration (dynamic wordlist from project history)
- [ ] **ATT-001f**: Ephemeral wordlist creation ("Add Word" interface for small attack-specific lists)
- [ ] **ATT-001g**: Ephemeral mask list creation (inline mask lines with syntax validation)

### ATT-002: Attack Editor Modal

- [ ] **ATT-002a**: Attack type selection and switching (progressive disclosure of complex options)
- [ ] **ATT-002b**: Resource selection (searchable dropdowns sorted by last modified with entry counts)
- [ ] **ATT-002c**: Attack parameter validation (real-time feedback with structured error messages)
- [ ] **ATT-002d**: Keyspace estimation and complexity calculation (dynamic updates for unsaved changes)
- [ ] **ATT-002e**: Attack preview and summary
- [ ] **ATT-002f**: User-friendly modifiers for dictionary attacks (Change Case, Substitute Characters buttons)
- [ ] **ATT-002g**: Expert mode toggle for advanced rule list selection
- [ ] **ATT-002h**: Lifecycle awareness warnings (editing running/exhausted attacks requires confirmation)

### ATT-003: Attack Management

- [ ] **ATT-003a**: Edit existing attack with warning for running attacks
- [ ] **ATT-003b**: Duplicate attack configuration
- [ ] **ATT-003c**: Delete attack from campaign
- [ ] **ATT-003d**: Reorder attacks in DAG sequence
- [ ] **ATT-003e**: Attack dependency visualization

### ATT-004: Advanced Attack Features

- [ ] **ATT-004a**: Rule modificators and custom rules
- [ ] **ATT-004b**: Dynamic wordlist integration
- [ ] **ATT-004c**: Attack overlap detection and warnings
- [ ] **ATT-004d**: Ephemeral resource creation for attacks
- [ ] **ATT-004e**: Attack performance estimation

### ATT-005: Standalone Attack Creation (NEW)

- [ ] **ATT-005a**: Attack creation page loads independently from campaigns
- [ ] **ATT-005b**: Attack resource selection and validation
- [ ] **ATT-005c**: Standalone attack parameter configuration
- [ ] **ATT-005d**: Attack save and template creation
- [ ] **ATT-005e**: Attack preview and keyspace calculation
- [ ] **ATT-005f**: Attack export and sharing functionality

---

## Resource Management Tests

### RES-001: Resource List & Navigation

- [ ] **RES-001a**: Resource list page loads with SSR data
- [ ] **RES-001b**: Resource filtering by type (wordlists, rules, masks, charsets)
- [ ] **RES-001c**: Resource search functionality
- [ ] **RES-001d**: Resource pagination with large datasets
- [ ] **RES-001e**: Resource detail view navigation

### RES-002: Resource Upload Flow

- [ ] **RES-002a**: File upload via drag-and-drop zone
- [ ] **RES-002b**: File upload via file picker
- [ ] **RES-002c**: Resource metadata entry (name, description, sensitivity)
- [ ] **RES-002d**: Resource type auto-detection (automatic identification from content)
- [ ] **RES-002e**: Upload validation and error handling (multi-stage validation pipeline)
- [ ] **RES-002f**: Atomic upload operations (prevent database/storage inconsistencies)
- [ ] **RES-002g**: Comprehensive metadata capture during upload process

### RES-003: Resource Management

- [ ] **RES-003a**: Resource preview for supported file types (content preview without full editing commitment)
- [ ] **RES-003b**: Resource download functionality
- [ ] **RES-003c**: Resource deletion with permission checks
- [ ] **RES-003d**: Inline editing for small files (\<1MB) (size-based editing workflow)
- [ ] **RES-003e**: Resource usage tracking in attacks
- [ ] **RES-003f**: Type-aware editing interfaces (different modes for mask, rule, wordlist, charset)
- [ ] **RES-003g**: Line-oriented editing (add, edit, delete operations on specific lines)
- [ ] **RES-003h**: Real-time validation with detailed error messages

### RES-004: Sensitivity & Permissions

- [ ] **RES-004a**: Global vs project-scoped resource visibility
- [ ] **RES-004b**: Sensitive resource redaction for non-admins
- [ ] **RES-404c**: Resource access control validation
- [ ] **RES-004d**: Resource sharing across projects (admin only)
- [ ] **RES-004e**: Resource permission inheritance

### RES-005: Resource Upload Page (NEW)

- [ ] **RES-005a**: Resource upload page loads with file drop zone
- [ ] **RES-005b**: Drag-and-drop file upload interface
- [ ] **RES-005c**: File type validation and restrictions
- [ ] **RES-005d**: Upload progress indicators and cancellation
- [ ] **RES-005e**: Large file upload handling and chunking
- [ ] **RES-005f**: Resource metadata input form validation
- [ ] **RES-005g**: Upload completion confirmation and navigation

### RES-006: Resource Detail Pages (NEW)

- [ ] **RES-006a**: Resource detail page loads with full information
- [ ] **RES-006b**: Resource content preview for supported types
- [ ] **RES-006c**: Resource metadata editing and updates
- [ ] **RES-006d**: Resource usage history and tracking
- [ ] **RES-006e**: Resource content editing for small files
- [ ] **RES-006f**: Resource download and export options
- [ ] **RES-006g**: Resource deletion with usage validation

---

## Hash List Management Tests

### HSH-001: Hash List Operations

- [ ] **HSH-001a**: Hash list creation from file upload (dual input modes support)
- [ ] **HSH-001b**: Hash list creation from text paste (intelligent parsing from metadata)
- [ ] **HSH-001c**: Hash type auto-detection and validation (confidence scoring with override capability)
- [ ] **HSH-001d**: Hash list preview and statistics (confirmation screen with detected types)
- [ ] **HSH-001e**: Hash list deletion with cascade checks
- [ ] **HSH-001f**: Hash isolation from surrounding metadata (shadow files, NTLM pairs)
- [ ] **HSH-001g**: Multi-stage validation preventing malformed campaign creation

### HSH-002: Hash List Integration

- [ ] **HSH-002a**: Hash list selection in campaign creation
- [ ] **HSH-002b**: Hash list reuse across multiple campaigns
- [ ] **HSH-002c**: Crackable upload flow with hash detection (streamlined workflow design)
- [ ] **HSH-002d**: Hash list export in various formats
- [ ] **HSH-002e**: Auto-campaign creation from uploaded hashes (dynamic wordlist generation)
- [ ] **HSH-002f**: Progress visibility during upload and processing phases
- [ ] **HSH-002g**: Manual hash type override when auto-detection fails

---

## Agent Management Tests

### AGT-001: Agent List & Monitoring

- [ ] **AGT-001a**: Agent list page loads with real-time status (display name = agent.custom_label or agent.host_name)
- [ ] **AGT-001b**: Agent filtering by status (online, offline, error)
- [ ] **AGT-001c**: Agent search and sorting functionality
- [ ] **AGT-001d**: Agent performance metrics display (name+OS, status, temp, utilization, guess rate, current job)
- [ ] **AGT-001e**: Agent health monitoring and alerts
- [ ] **AGT-001f**: Information density optimization (compact view with essential data)
- [ ] **AGT-001g**: Role-based gear menu visibility (admin-only disable/details options)

### AGT-002: Agent Registration

- [ ] **AGT-002a**: New agent registration form (modal interface with label and project toggles)
- [ ] **AGT-002b**: Agent token generation and display (immediate token display, shown only once)
- [ ] **AGT-002c**: Agent project assignment (multi-toggle interface for project membership)
- [ ] **AGT-002d**: Agent configuration validation
- [ ] **AGT-002e**: Agent registration confirmation
- [ ] **AGT-002f**: Quick registration workflow (streamlined for immediate setup)

### AGT-003: Agent Details Modal

- [ ] **AGT-003a**: Agent settings tab (enable/disable, update interval, native hashcat, project assignment)
- [ ] **AGT-003b**: Agent hardware tab (individual device toggles, state-aware prompting, backend management)
- [ ] **AGT-003c**: Agent performance tab (8hr line charts, per-device donut charts, live SSE updates)
- [ ] **AGT-003d**: Agent logs tab (color-coded severity timeline, expandable details, filtering)
- [ ] **AGT-003e**: Agent capabilities tab (benchmark table with search/filter, expandable per-device rows)
- [ ] **AGT-003f**: Hardware graceful degradation (gray placeholders when device info unavailable)
- [ ] **AGT-003g**: Benchmark management (header button to trigger new benchmark runs)

### AGT-004: Agent Administration (Admin Only)

- [ ] **AGT-004a**: Agent restart command
- [ ] **AGT-004b**: Agent deactivation with confirmation
- [ ] **AGT-004c**: Device toggle (GPU enable/disable)
- [ ] **AGT-004d**: Agent benchmark trigger
- [ ] **AGT-004e**: Agent deletion with impact assessment

---

## User & Project Management Tests

### USR-001: User Management

- [ ] **USR-001a**: User list page with role-based visibility (Flowbite-inspired table with filtering/pagination)
- [ ] **USR-001b**: New user creation form
- [ ] **USR-001c**: User role assignment and validation (admin-controlled access restrictions)
- [ ] **USR-001d**: User project association management
- [ ] **USR-001e**: User deletion with cascade handling
- [ ] **USR-001f**: Clear permission boundaries (UI distinguishes self-service vs admin functions)
- [ ] **USR-001g**: Role-based UI element separation (admin-only functions visually separated)

### USR-002: Project Management

- [ ] **USR-002a**: Project list page with membership info
- [ ] **USR-002b**: Project creation form (admin only)
- [ ] **USR-002c**: Project user management
- [ ] **USR-002d**: Project settings and configuration
- [ ] **USR-002e**: Project deletion with impact assessment

### USR-003: Profile & Settings

- [ ] **USR-003a**: User profile editing (self-service name and email updates)
- [ ] **USR-003b**: Password change functionality (immediate confirmation feedback)
- [ ] **USR-003c**: User preferences and settings
- [ ] **USR-003d**: API key generation and management
- [ ] **USR-003e**: Activity history and audit logs
- [ ] **USR-003f**: Profile change validation and instant feedback
- [ ] **USR-003g**: Self-service vs admin-controlled function distinction

### USR-004: User Detail Pages (NEW)

- [ ] **USR-004a**: User detail page loads with complete profile information
- [ ] **USR-004b**: User profile editing and updates
- [ ] **USR-004c**: User role management and project associations
- [ ] **USR-004d**: User activity history and audit trails
- [ ] **USR-004e**: User permission validation and enforcement
- [ ] **USR-004f**: User profile form validation and error handling

### USR-005: User Deletion Flow (NEW)

- [ ] **USR-005a**: User deletion page loads with impact assessment
- [ ] **USR-005b**: Display of user's associated campaigns, attacks, and resources
- [ ] **USR-005c**: Warning messages for active user sessions
- [ ] **USR-005d**: Confirmation workflow with typed verification
- [ ] **USR-005e**: Cascade deletion options and warnings
- [ ] **USR-005f**: User deletion permission validation

---

## Access Control & Security Tests

### ACS-001: Role-Based Access Control

- [ ] **ACS-001a**: Admin-only functionality restrictions
- [ ] **ACS-001b**: Project admin scope limitations
- [ ] **ACS-001c**: Regular user permission enforcement
- [ ] **ACS-001d**: Cross-project access prevention
- [ ] **ACS-001e**: Sensitive resource access control

### ACS-002: Security Validations

- [ ] **ACS-002a**: CSRF protection on forms
- [ ] **ACS-002b**: Input validation and sanitization
- [ ] **ACS-002c**: File upload security checks
- [ ] **ACS-002d**: API endpoint authorization
- [ ] **ACS-002e**: Session security and timeout handling

---

## Monitoring & System Health Tests

### MON-001: System Health Dashboard (Admin Only)

- [ ] **MON-001a**: Redis health and queue metrics
- [ ] **MON-001b**: PostgreSQL health and performance stats
- [ ] **MON-001c**: MinIO storage usage and latency
- [ ] **MON-001d**: Agent runtime statistics
- [ ] **MON-001e**: System performance trends and alerts

### MON-002: Activity & Audit Logging

- [ ] **MON-002a**: Audit log page with filtering
- [ ] **MON-002b**: User action tracking
- [ ] **MON-002c**: System event logging
- [ ] **MON-002d**: Audit detail view modal
- [ ] **MON-002e**: Audit log export functionality

---

## Notification & Toast System Tests

### NOT-001: Toast Notifications

- [ ] **NOT-001a**: Success toast display and auto-dismiss (positive feedback for completed operations)
- [ ] **NOT-001b**: Error toast display with retry actions (specific, actionable error messages)
- [ ] **NOT-001c**: Info toast for system notifications (event categorization for different types)
- [ ] **NOT-001d**: Toast stacking and queue management
- [ ] **NOT-001e**: Manual toast dismissal (user control with appropriate persistence)
- [ ] **NOT-001f**: Visual hierarchy with color coding and iconography for quick recognition
- [ ] **NOT-001g**: Toast notification batching for rapid events (condensed summary notifications)

### NOT-002: Real-Time Event Notifications

- [ ] **NOT-002a**: Crack event notifications with details
- [ ] **NOT-002b**: Agent status change notifications
- [ ] **NOT-002c**: Campaign completion notifications
- [ ] **NOT-002d**: System error notifications
- [ ] **NOT-002e**: Batched notification handling

---

## UI/UX & Responsive Design Tests

### UIX-001: Layout & Navigation

- [ ] **UIX-001a**: Responsive sidebar behavior
- [ ] **UIX-001b**: Mobile navigation menu
- [ ] **UIX-001c**: Breadcrumb navigation accuracy
- [ ] **UIX-001d**: Modal overlay and z-index management
- [ ] **UIX-001e**: Dark mode toggle functionality

### UIX-002: Form Behavior

- [ ] **UIX-002a**: Form validation and error display (immediate validation with structured error reporting)
- [ ] **UIX-002b**: Progressive enhancement (JS disabled) (forms work without JavaScript enabled)
- [ ] **UIX-002c**: Form persistence during navigation (clean separation between form and app state)
- [ ] **UIX-002d**: Multi-step form navigation (SvelteKit Actions integration)
- [ ] **UIX-002e**: Form submission loading states (clear indication of processing)
- [ ] **UIX-002f**: Server-side validation with comprehensive error reporting
- [ ] **UIX-002g**: Superforms integration for consistent form handling patterns

### UIX-003: Data Display Components

- [ ] **UIX-003a**: Table sorting and pagination (consistent interaction models across features)
- [ ] **UIX-003b**: Progress bar accuracy and animation
- [ ] **UIX-003c**: Chart and metrics visualization (Catppuccin Macchiato theme integration)
- [ ] **UIX-003d**: Empty state handling
- [ ] **UIX-003e**: Error state display and recovery
- [ ] **UIX-003f**: Progressive disclosure (complex features revealed progressively)
- [ ] **UIX-003g**: Accessibility compliance (keyboard navigation, screen reader support, color contrast)
- [ ] **UIX-003h**: Responsive design with appropriate touch targets for mobile

### UIX-004: Theme and Appearance (NEW)

- [ ] **UIX-004a**: Dark mode toggle functionality and persistence
- [ ] **UIX-004b**: Theme switching without page refresh
- [ ] **UIX-004c**: Theme preference persistence across sessions
- [ ] **UIX-004d**: Catppuccin Macchiato theme consistency
- [ ] **UIX-004e**: Theme-aware component rendering
- [ ] **UIX-004f**: System theme detection and auto-switching

---

## Integration & Workflow Tests

### INT-001: End-to-End Campaign Workflows

- [ ] **INT-001a**: Complete campaign creation to execution flow
- [ ] **INT-001b**: Multi-attack campaign with DAG sequencing
- [ ] **INT-001c**: Campaign with resource upload and usage
- [ ] **INT-001d**: Campaign monitoring through completion
- [ ] **INT-001e**: Campaign results export and analysis

### INT-002: Cross-Component Integration

- [ ] **INT-002a**: Resource creation and immediate use in attack
- [ ] **INT-002b**: Agent registration and task assignment
- [ ] **INT-002c**: User creation and project assignment workflow
- [ ] **INT-002d**: Project switching with data context updates
- [ ] **INT-002e**: Multi-user collaboration scenarios

### INT-003: Error Recovery & Edge Cases

- [ ] **INT-003a**: Network failure recovery
- [ ] **INT-003b**: Large file upload handling
- [ ] **INT-003c**: Concurrent user modifications
- [ ] **INT-003d**: Browser refresh during operations
- [ ] **INT-003e**: Session expiry during long operations

### INT-004: Error Page Testing (NEW)

- [ ] **INT-004a**: Resource error page display and recovery options
- [ ] **INT-004b**: Campaign error page with helpful guidance
- [ ] **INT-004c**: Error page navigation and back functionality
- [ ] **INT-004d**: Error state persistence and refresh behavior
- [ ] **INT-004e**: Error reporting and feedback mechanisms

---

## Performance & Load Tests

### PRF-001: Page Load Performance

- [ ] **PRF-001a**: Dashboard load time with large datasets
- [ ] **PRF-001b**: Campaign list pagination performance
- [ ] **PRF-001c**: Resource list loading with many files
- [ ] **PRF-001d**: Agent list real-time update performance
- [ ] **PRF-001e**: SSR hydration speed

### PRF-002: User Interaction Performance

- [ ] **PRF-002a**: Modal open/close animation smoothness
- [ ] **PRF-002b**: Table sorting with large datasets
- [ ] **PRF-002c**: Real-time update frequency and smoothness
- [ ] **PRF-002d**: Form submission response times
- [ ] **PRF-002e**: File upload progress accuracy

### PRF-003: File Upload Performance (NEW)

- [ ] **PRF-003a**: Large file upload progress tracking
- [ ] **PRF-003b**: Upload cancellation and cleanup
- [ ] **PRF-003c**: Multiple concurrent upload handling
- [ ] **PRF-003d**: Upload resume functionality
- [ ] **PRF-003e**: Memory usage during large uploads

---

## Test Implementation Priority

### Phase 3A: Core Functionality (Critical Path)

1. **Authentication & Session** (ASM-001, ASM-002, ASM-003)
2. **Dashboard Loading** (DRM-001, DRM-003)
3. **Campaign Creation** (CAM-001, CAM-002)
4. **Basic Attack Configuration** (ATT-001, ATT-002)
5. **Resource Management** (RES-001, RES-002)

### Phase 3B: Advanced Features

1. **Agent Management** (AGT-001, AGT-002, AGT-003)
2. **Campaign Operations** (CAM-003, CAM-004)
3. **User/Project Management** (USR-001, USR-002)
4. **Access Control** (ACS-001, ACS-002)
5. **Advanced Attack Features** (ATT-003, ATT-004)

### Phase 3C: Integration & Polish

1. **Real-Time Features** (DRM-002, NOT-002)
2. **Monitoring & Health** (MON-001, MON-002)
3. **Integration Workflows** (INT-001, INT-002)
4. **Performance Validation** (PRF-001, PRF-002)
5. **UI/UX Polish** (UIX-001, UIX-002, UIX-003)

---

## Test Infrastructure Requirements

### Authentication Integration

- [ ] Implement SSR session-based authentication
- [ ] Create test user seeding with known credentials
- [ ] Develop authentication helpers for test setup
- [ ] Handle session persistence across test scenarios

### Docker Backend Integration

- [ ] Ensure Docker health checks work with authentication
- [ ] Implement test data seeding through service layer
- [ ] Create predictable test environment setup
- [ ] Handle test isolation and cleanup

### Test Data Management

- [ ] Standardized test user roles and permissions
- [ ] Predictable project/campaign/resource test data
- [ ] Consistent agent configurations for testing
- [ ] Mock vs real data switching mechanisms

### CI/CD Integration

- [ ] Three-tier test execution in CI pipeline
- [ ] Docker environment management in CI
- [ ] Test result reporting and coverage analysis
- [ ] Performance benchmark tracking

---

## Success Metrics

### Coverage Goals

- **Functional Coverage**: 100% of user-visible workflows
- **Role Coverage**: All user roles (admin, project admin, user)
- **Browser Coverage**: Chromium, Firefox, WebKit
- **Device Coverage**: Desktop, tablet, mobile viewports

### Quality Gates

- All critical path tests must pass before release
- No authentication-related test failures
- Performance benchmarks within acceptable ranges
- Zero accessibility violations in core workflows

### Maintenance Strategy

- Tests updated with feature development
- Regular test data refresh and validation
- Performance baseline updates with changes
- Documentation kept in sync with test coverage

---

## Notes for Implementation

1. **SSR Authentication**: Critical blocker for full E2E testing - must be implemented first
2. **Test Environment**: Docker-based backend with predictable seeded data
3. **Test Isolation**: Each test should be independent and not rely on previous test state
4. **Error Scenarios**: Include negative testing for all major workflows
5. **Performance**: Monitor test execution time and optimize slow tests
6. **Maintenance**: Keep test selectors and data synchronized with UI changes

### Design-Driven Testing Context

#### **Progressive Disclosure Testing**

- Verify complex options are hidden behind expert modes and revealed appropriately
- Test that UI complexity increases gradually as users need more advanced features
- Validate that default states show essential information without overwhelming users

#### **Real-Time Update Architecture Testing**

- Test SSE trigger-based updates (lightweight notifications, not full data streaming)
- Verify EventSource reconnection handling and graceful degradation
- Validate project-scoped event filtering ensures users only see relevant events
- Test batching logic for rapid events (>5 events/sec should be condensed)

#### **Accessibility & Responsive Design Testing**

- Keyboard navigation testing for all interactive elements (especially drag-and-drop alternatives)
- Screen reader compatibility for complex data displays and real-time updates
- Mobile touch target validation (minimum 44px touch targets)
- Color contrast validation for Catppuccin Macchiato theme

#### **Form Handling Philosophy Testing**

- Progressive enhancement validation (all forms must work without JavaScript)
- SvelteKit Actions integration testing (server-side validation with structured errors)
- Superforms integration testing (consistent form patterns across all features)
- Clean state separation testing (form state vs application state)

#### **Role-Based UX Testing**

- Admin-only function visibility testing (gear menus, management functions)
- Self-service vs admin-controlled function distinction validation
- Project context awareness testing (all UI elements respect current project)
- Permission boundary clarity testing (users understand what they can/cannot do)

#### **Information Density & Display Testing**

- Agent list compact view testing (essential data without clutter)
- Attack summary display testing (type, config, keyspace, complexity at a glance)
- Resource metadata visibility testing (line counts, sizes, usage info)
- Dashboard metrics card testing (real-time data without overwhelming detail)

---

## Current Test Coverage Analysis

### Existing E2E Tests (Implemented)

#### **Current Test Files in `/frontend/e2e/`**

01. **`agent-list-mock-fallback.e2e.test.ts`** - Agent Management

    - [x] Maps to: **AGT-001** (Agent list & monitoring), **AGT-003** (Agent details modal)
    - Coverage: Agent list rendering, details modal tabs, settings form validation

02. **`attacks-list.test.ts`** - Attack List Management

    - [x] Maps to: **ATT-003** (Attack management), **ATT-002** partial (Attack configuration display)
    - Coverage: Attack list display, filtering, search, action menus, delete confirmation

03. **`attacks_modals.test.ts`** - Attack Creation/Editing

    - [x] Maps to: **ATT-001** (Attack creation wizard), **ATT-002** (Attack editor modal)
    - Coverage: Attack wizard navigation, form validation, creation flow, edit flow

04. **`auth.test.ts`** - Authentication UI (Mock Only)

    - [x] Maps to: **ASM-001** partial (Login form UI only)
    - Coverage: Login form display, validation errors, form field interactions (NO real auth flow)

05. **`campaign-detail.test.ts`** + **`campaigns-detail.test.ts`** - Campaign Details

    - [x] Maps to: **CAM-003** (Campaign details & management)
    - Coverage: Campaign information display, attacks table, action buttons (duplicate files detected)

06. **`campaign-progress-metrics.test.ts`** - Campaign Monitoring

    - [x] Maps to: **CAM-003** (Campaign progress tracking), **DRM-002** partial (Real-time updates)
    - Coverage: Progress components, metrics display, auto-refresh functionality

07. **`campaigns-list.e2e.test.ts`** - Campaign List Management

    - [x] Maps to: **CAM-002** (Campaign list & navigation), **CAM-004** partial (Campaign operations)
    - Coverage: Campaign list display, accordion structure, action menus, empty states

08. **`dashboard.e2e.test.ts`** - Dashboard Overview

    - [x] Maps to: **DRM-001** (Dashboard data loading)
    - Coverage: Dashboard metrics cards, campaign overview, SSR data integration

09. **`layout.e2e.test.ts`** - Basic Layout

    - [x] Maps to: **UIX-001** partial (Layout & navigation)
    - Coverage: Sidebar rendering only (minimal test)

10. **`project-info.test.ts`** - Project Information Component

    - [x] Maps to: **USR-002** partial (Project information display)
    - Coverage: Project information display within projects page context

11. **`projects-list.test.ts`** - Project Management

    - [x] Maps to: **USR-002** (Project management)
    - Coverage: Project list, search, pagination, action menus, SSR integration

12. **`resource-detail-fragments.test.ts`** - Resource Details

    - [x] Maps to: **RES-003** (Resource management), **RES-002** partial (Resource preview)
    - Coverage: Resource detail tabs, preview, content editing, navigation

13. **`resources-list.test.ts`** - Resource List Management

    - [x] Maps to: **RES-001** (Resource list & navigation), **RES-002** partial (Resource display)
    - Coverage: Resource list, filtering by type, search, pagination, empty states

14. **`settings.test.ts`** - User Settings [FAIL] **EMPTY PLACEHOLDER**

    - Should map to: **USR-003** (Profile & settings)
    - Coverage: None (empty file)

15. **`users.test.ts`** - User Management [FAIL] **EMPTY PLACEHOLDER**

    - Should map to: **USR-001** (User management)
    - Coverage: None (empty file)

### Missing Test Coverage (In Plan But Not Implemented)

#### **Critical Authentication & Session Management**

- **ASM-001b-e**: Real login/logout flows, session persistence, authentication redirection
- **ASM-002**: Project selection & switching workflows
- **ASM-003**: Session timeout, token refresh, concurrent session handling

#### **Complete Campaign Workflows**

- **CAM-001**: Campaign creation wizard (only basic display tested)
- **CAM-004**: Campaign lifecycle operations (start, pause, resume, stop)
- **CAM-005**: Campaign export/import functionality

#### **Advanced Attack Features**

- **ATT-004**: Rule modificators, dynamic wordlists, attack dependencies
- **Attack performance estimation**: Keyspace calculation and complexity

#### **Hash List Management (Complete Category Missing)**

- **HSH-001**: Hash list creation, upload, type detection
- [ ] **HSH-002**: Hash list integration with campaigns

#### **User Management (Major Gap)**

- **USR-001**: User creation, role assignment, project association
- **USR-003**: Profile editing, password change, API key management

#### **Access Control & Security (Complete Category Missing)**

- **ACS-001**: Role-based access control validation
- **ACS-002**: Security validations (CSRF, input sanitization, file upload security)

#### **System Monitoring (Complete Category Missing)**

- **MON-001**: System health dashboard (admin-only features)
- **MON-002**: Activity & audit logging

#### **Real-Time Features (Major Gap)**

- **DRM-002**: Live SSE updates for agents, campaigns, notifications
- **NOT-001-002**: Toast notification system, real-time event notifications

#### **Integration & Workflow Testing (Complete Category Missing)**

- **INT-001**: End-to-end campaign workflows
- **INT-002**: Cross-component integration scenarios
- **INT-003**: Error recovery and edge cases

#### **Performance & Load Testing (Complete Category Missing)**

- **PRF-001-002**: Page load performance, user interaction performance

#### **Responsive Design & Accessibility (Major Gap)**

- **UIX-002-003**: Form behavior, data display components, mobile responsiveness

### Existing Tests Not in Plan (Unique Current Implementation)

#### **Component-Level Integration Tests**

- **Project Info Component**: Isolated component testing within page context
- **Layout Component**: Basic sidebar rendering test

#### **Test Implementation Patterns Not Planned**

- **Mock vs SSR Testing**: Current tests mix mock API responses with SSR data loading
- **Duplicate Test Files**: Two campaign detail test files with similar coverage
- **Component Fragment Testing**: Resource detail page tested as individual fragments

#### **Testing Architecture Differences**

- **Environment Detection**: Current tests use test scenarios via URL parameters
- **SSR vs SPA Patterns**: Current tests adapted for SSR architecture
- **Empty Placeholder Files**: Structured placeholders for future implementation

### Recommended Test Implementation Priority

#### **Phase 3A: Critical Gaps (Immediate)**

1. **Complete Authentication Testing** (ASM-001-003): Real login flows, session management
2. **User Management Implementation** (USR-001, USR-003): Fill empty placeholder files
3. **Hash List Management** (HSH-001-002): Complete missing category
4. **Access Control Validation** (ACS-001): Role-based permissions testing

#### **Phase 3B: Advanced Features (Medium Priority)**

1. **Campaign Lifecycle Operations** (CAM-004-005): Complete workflow testing
2. **Advanced Attack Features** (ATT-004): Dynamic resources, dependencies
3. **Real-Time Updates** (DRM-002, NOT-001-002): SSE and toast notifications
4. **System Monitoring** (MON-001-002): Admin dashboard and audit logs

#### **Phase 3C: Polish & Performance (Lower Priority)**

1. **Integration Workflows** (INT-001-003): End-to-end scenarios
2. **Performance Testing** (PRF-001-002): Load and interaction performance
3. **Responsive Design** (UIX-002-003): Mobile and accessibility testing
4. **Error Recovery** (INT-003): Edge cases and failure scenarios

### Test Coverage Summary

- **Implemented Categories**: 7 out of 15 (47%)
- **Complete Category Coverage**: 2 out of 15 (13%) - Dashboard, Resources
- **Critical Missing**: Authentication flows, Hash lists, Access control, Monitoring
- **Test File Count**: 15 files (2 empty placeholders, 2 duplicates)
- **Estimated Additional Tests Needed**: ~200 test scenarios

This comprehensive test plan ensures complete coverage of Ouroboros's user experience while maintaining the three-tier testing architecture established in Phase 3.
