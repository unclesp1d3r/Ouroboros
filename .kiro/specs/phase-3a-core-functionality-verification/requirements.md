# Requirements Document

## Introduction

This feature represents Phase 3 Step 2 of the Ouroboros web UI implementation, focusing on verifying that all existing implementations work correctly with the newly implemented authentication system and completing critical user management functionality that currently has empty placeholder files. This is a foundation verification step that ensures the authentication layer integrates properly with all existing features while filling gaps in user management workflows.

## Requirements

### Requirement 1: Existing Feature Verification with Authentication

**User Story:** As a user, I want all existing Ouroboros features to work seamlessly with the new authentication system, so that I can access and use all functionality without disruption.

#### Acceptance Criteria

1. WHEN a user accesses the dashboard THEN it SHALL load with authenticated API calls and display real-time data correctly
2. WHEN a user navigates between sections THEN the sidebar navigation SHALL work properly with authentication context
3. WHEN a user views campaign lists THEN they SHALL load with SSR data and support pagination, search, and filtering
4. WHEN a user accesses campaign details THEN attack lists SHALL display with proper authentication
5. WHEN a user manages resources THEN the resource list SHALL load with SSR data and support filtering by type
6. WHEN a user views agent status THEN the agent list SHALL display real-time status with authenticated API calls
7. WHEN authentication fails for any feature THEN the system SHALL redirect to login and return to the intended page after authentication

### Requirement 2: User Management Implementation

**User Story:** As an administrator, I want complete user management functionality including profile management and user administration, so that I can manage user accounts, roles, and permissions effectively.

#### Acceptance Criteria

1. WHEN an administrator accesses the user list THEN it SHALL display all users with role-based visibility and management options
2. WHEN an administrator creates a new user THEN the system SHALL provide a complete creation form with role assignment and project association
3. WHEN a user accesses their profile settings THEN they SHALL be able to edit their name, email, password, and preferences
4. WHEN an administrator deletes a user THEN the system SHALL show impact assessment and require confirmation with cascade handling
5. WHEN a user manages API keys THEN they SHALL be able to generate, view, and revoke keys securely
6. WHEN accessing user detail pages THEN they SHALL display complete profile information with editing capabilities
7. WHEN role-based access is enforced THEN users SHALL only see and access functions appropriate to their role

### Requirement 3: Project Management and Context Switching

**User Story:** As a user, I want to work within project contexts and switch between projects seamlessly, so that I can manage multiple projects efficiently while maintaining proper data isolation.

#### Acceptance Criteria

1. WHEN a user logs in with single project access THEN the system SHALL auto-select that project and store the selection
2. WHEN a user logs in with multiple project access THEN the system SHALL present a project selection modal
3. WHEN a user switches projects THEN the system SHALL update the global project selector and refresh all data contexts
4. WHEN a user navigates between pages THEN project context SHALL persist across all navigation
5. WHEN project-scoped data is displayed THEN it SHALL only show data relevant to the selected project
6. WHEN project-based access control is enforced THEN users SHALL only access resources within their authorized projects
7. WHEN an administrator manages projects THEN they SHALL be able to create, configure, and delete projects with impact assessment

### Requirement 4: Comprehensive Test Coverage Implementation

**User Story:** As a developer, I want comprehensive automated test coverage for all user-facing functionality, so that I can ensure reliability and catch regressions early.

#### Acceptance Criteria

1. WHEN user management functionality is tested THEN it SHALL have both mocked E2E tests and full E2E tests covering all workflows
2. WHEN dashboard functionality is tested THEN it SHALL verify data loading, navigation, and error handling scenarios
3. WHEN form behavior is tested THEN it SHALL validate client-side and server-side validation, error display, and submission flows
4. WHEN access control is tested THEN it SHALL verify role-based restrictions and permission enforcement
5. WHEN project management is tested THEN it SHALL cover project selection, switching, and context persistence
6. WHEN tests are executed THEN they SHALL run via `just test-frontend` for mocked tests and `just test-e2e` for full integration tests
7. WHEN test utilities are used THEN they SHALL follow existing patterns and maintain consistency across test suites

### Requirement 5: Role-Based Access Control Implementation

**User Story:** As a system administrator, I want role-based access control enforced throughout the UI, so that users can only access functionality appropriate to their assigned roles.

#### Acceptance Criteria

1. WHEN admin-only functionality is accessed THEN it SHALL be restricted to users with admin roles
2. WHEN project admin functions are used THEN they SHALL be limited to the appropriate project scope
3. WHEN regular user permissions are enforced THEN users SHALL only access their authorized resources
4. WHEN cross-project access is attempted THEN the system SHALL prevent unauthorized access
5. WHEN role-based menus are displayed THEN they SHALL show only appropriate actions for the user's role
6. WHEN permission validation occurs THEN it SHALL be enforced both in the backend (Casbin) and frontend (SvelteKit load functions)
7. WHEN UI elements are rendered THEN they SHALL conditionally display based on user permissions

### Requirement 6: UI Polish and Responsive Design

**User Story:** As a user, I want a polished, responsive interface that works well across different screen sizes and provides a consistent visual experience, so that I can use Ouroboros effectively on various devices.

#### Acceptance Criteria

1. WHEN the interface is viewed on different screen sizes THEN it SHALL be responsive and functional from 1080x720 resolution and up
2. WHEN dark mode is toggled THEN the system SHALL switch themes without page refresh and persist the preference
3. WHEN modal overlays are used THEN they SHALL have proper z-index management and accessibility
4. WHEN mobile navigation is accessed THEN it SHALL provide a hamburger menu with drawer functionality
5. WHEN the Catppuccin theme is applied THEN it SHALL use Macchiato (dark) and Latte (light) variants consistently
6. WHEN system theme detection is enabled THEN it SHALL auto-switch themes based on system preferences
7. WHEN offline operation is required THEN the interface SHALL function without internet connectivity or external CDNs

### Requirement 9: Dashboard Visual Implementation

**User Story:** As a user, I want a comprehensive dashboard that provides real-time operational insights with clear visual indicators, so that I can quickly understand system status and take appropriate actions.

#### Acceptance Criteria

1. WHEN the dashboard loads THEN it SHALL display a top strip with four operational status cards (Active Agents, Running Tasks, Recently Cracked Hashes, Resource Usage)
2. WHEN status cards are displayed THEN they SHALL use Shadcn-Svelte Card components with uniform height, consistent padding, and 12-column responsive grid layout
3. WHEN the Active Agents card is clicked THEN it SHALL open an Agent Status Sheet sliding out from the right side
4. WHEN campaign overview is displayed THEN it SHALL show accordion-style rows with expandable campaign details sorted by Running campaigns first
5. WHEN campaign rows are expanded THEN they SHALL display attack lists with progress bars, ETAs, and gear icon menus
6. WHEN live toast notifications appear THEN they SHALL show cracked hashes with rate limiting and batch grouping
7. WHEN empty states occur THEN they SHALL display friendly guidance messages with clear call-to-action

### Requirement 10: Attack Configuration Visual Implementation

**User Story:** As a user, I want intuitive attack configuration interfaces with clear visual feedback, so that I can easily set up complex attacks with confidence in the parameters.

#### Acceptance Criteria

1. WHEN creating dictionary attacks THEN the interface SHALL provide a Flowbite modal with wordlist dropdown, length range inputs, and modifier buttons
2. WHEN creating mask attacks THEN the interface SHALL support inline mask entry, custom charset definition, and modificator selection
3. WHEN creating brute force attacks THEN the interface SHALL provide checkbox-driven charset selection with live preview of generated masks
4. WHEN attack parameters change THEN the system SHALL display live keyspace estimation and dot-based complexity meter (0-5 dots)
5. WHEN modifiers are selected THEN they SHALL show as toggleable buttons that map to backend rule files
6. WHEN attack forms are submitted THEN they SHALL validate parameters and provide clear error feedback
7. WHEN attack previews are shown THEN they SHALL display generated masks, charset strings, and estimated passwords to check

### Requirement 11: Campaign and Resource Visual Implementation

**User Story:** As a user, I want clear visual representations of campaigns, attacks, and resources with intuitive navigation, so that I can efficiently manage complex cracking operations.

#### Acceptance Criteria

1. WHEN viewing campaign details THEN the interface SHALL display a table-like attack grid with 6 columns (Attack, Language, Length, Settings, Passwords, Complexity)
2. WHEN attack settings are displayed THEN they SHALL show as blue-linked summaries with hover tooltips
3. WHEN complexity is shown THEN it SHALL use a dot-based visual meter with filled/unfilled circles
4. WHEN attack rows have actions THEN they SHALL display gear icons with context menus (Edit, Duplicate, Move, Remove)
5. WHEN progress is tracked THEN it SHALL use keyspace-weighted progress bars with dynamic color coding by state
6. WHEN campaign states are indicated THEN they SHALL use color-coded badges (Running=purple, Completed=green, Error=red, Paused=gray)
7. WHEN resource lists are displayed THEN they SHALL show file metadata, usage counts, and type-based filtering

### Requirement 12: Agent Management Visual Implementation

**User Story:** As a user, I want comprehensive agent monitoring with real-time performance data and clear status indicators, so that I can effectively manage distributed cracking resources.

#### Acceptance Criteria

1. WHEN agent lists are displayed THEN they SHALL show Agent Name+OS, Status, Temperature, Utilization, Current Rate, Average Rate, Current Job columns
2. WHEN agent status is indicated THEN it SHALL use color-coded badges (🟢 Online, 🟡 Idle, 🔴 Offline)
3. WHEN agent performance is shown THEN it SHALL include donut charts for utilization and sparklines for 8-hour trend data
4. WHEN agent details are accessed THEN they SHALL display in slide-out sheets with scrollable card layouts
5. WHEN agent hardware is managed THEN it SHALL provide device toggle interfaces and temperature monitoring
6. WHEN agent errors occur THEN they SHALL display in structured log streams with color coding and timestamps
7. WHEN agent benchmarks are shown THEN they SHALL include table and graph representations of performance data

### Requirement 13: System Health Visual Implementation

**User Story:** As an administrator, I want a comprehensive system health dashboard with real-time service monitoring, so that I can proactively identify and resolve infrastructure issues.

#### Acceptance Criteria

1. WHEN system health is displayed THEN it SHALL show service status cards for MinIO, Redis, PostgreSQL with color-coded indicators
2. WHEN service metrics are shown THEN they SHALL include latency, error counts, utilization, and connection status
3. WHEN services are unreachable THEN they SHALL display red badges with last-seen timestamps and error messages
4. WHEN admin access is available THEN additional diagnostic data SHALL be shown (keyspace breakdown, long-running queries, disk I/O)
5. WHEN real-time updates occur THEN they SHALL refresh every 5-10 seconds via SSE with stale data indicators
6. WHEN empty or error states occur THEN they SHALL show skeleton loaders and clear placeholder messages
7. WHEN agent health is monitored THEN it SHALL display collapsible sections with last-seen timestamps and current tasks

### Requirement 14: Visual Style and Design System Implementation

**User Story:** As a user, I want a consistent, polished visual design that follows established style guidelines and works offline, so that I have a professional and cohesive experience across all Ouroboros interfaces.

#### Acceptance Criteria

1. WHEN the color theme is applied THEN it SHALL use Catppuccin Macchiato palette with DarkViolet (#9400D3) as the accent color
2. WHEN typography is rendered THEN it SHALL use system font stack with consistent text sizing (text-xl for sections, text-lg for cards, text-base for body)
3. WHEN buttons are displayed THEN they SHALL use accent color for primary buttons and accent border for secondary buttons
4. WHEN badges are shown THEN they SHALL use semantic colors (green for success, yellow for warning, red for error, blue for info)
5. WHEN layout is structured THEN it SHALL follow Flowbite sidebar + navbar shell with responsive grid patterns
6. WHEN spacing is applied THEN it SHALL use consistent Tailwind spacing (p-4 for containers, appropriate grid gaps)
7. WHEN offline operation is required THEN all fonts, icons, and assets SHALL work without external dependencies

### Requirement 15: Component Consistency and Behavior Implementation

**User Story:** As a user, I want consistent component behavior and visual feedback across all interfaces, so that I can predict how interactions will work and receive clear status information.

#### Acceptance Criteria

1. WHEN tooltips are displayed THEN they SHALL use consistent styling (bg-surface0, text-subtext0, text-sm) with Flowbite tooltip behavior
2. WHEN form validation occurs THEN error states SHALL use red border and text with clear error messages below fields
3. WHEN toast notifications appear THEN they SHALL use semantic colors (red for errors, blue for info) with consistent positioning
4. WHEN modals are shown THEN they SHALL use Flowbite modal layout with max-w-2xl width and proper backdrop
5. WHEN tables are displayed THEN they SHALL use Flowbite table styling with alternating row colors and overflow handling
6. WHEN icons are used THEN they SHALL be Lucide icons stored locally with attack type mappings (book-open for dictionary, command for mask, hash for brute force)
7. WHEN responsive behavior is needed THEN it SHALL support minimum 768px width with collapsible sidebar below lg breakpoint

### Requirement 16: Interactive Behavior and SvelteKit Integration Implementation

**User Story:** As a developer, I want consistent interactive patterns using SvelteKit 5 with runes and actions for dynamic updates, so that the interface provides smooth user experiences with proper SSR and client-side reactivity.

#### Acceptance Criteria

1. WHEN dynamic updates are needed THEN they SHALL use SvelteKit 5 runes ($state, $derived, $effect) for reactive state management
2. WHEN live estimation is needed THEN it SHALL use reactive stores with debounced input for responsive feedback
3. WHEN forms are submitted THEN they SHALL use SvelteKit actions with Superforms v2 and return proper form states
4. WHEN SSE updates occur THEN they SHALL trigger targeted data refreshes using Svelte stores and reactive updates
5. WHEN form interactions happen THEN they SHALL provide immediate visual feedback using client-side validation with Zod schemas
6. WHEN data loading occurs THEN it SHALL show appropriate loading states using SvelteKit's loading mechanisms and skeleton loaders
7. WHEN errors occur THEN they SHALL display user-friendly messages using SvelteKit error handling without exposing internal details

### Requirement 17: Development Environment and Tooling Implementation

**User Story:** As a developer, I want a consistent development environment with proper tooling and configuration, so that I can efficiently develop, test, and maintain Ouroboros features.

#### Acceptance Criteria

1. WHEN the development environment is set up THEN it SHALL use Python 3.13 with uv package manager and proper virtual environment isolation
2. WHEN code quality tools are used THEN they SHALL include ruff for linting/formatting, mypy for type checking, and pre-commit hooks for automation
3. WHEN the frontend is developed THEN it SHALL use SvelteKit with SSR, pnpm package manager, and proper TypeScript configuration
4. WHEN Docker is used for development THEN it SHALL provide hot reload, health checks, and proper service orchestration
5. WHEN testing is performed THEN it SHALL include unit tests with pytest, integration tests with testcontainers, and E2E tests with Playwright
6. WHEN documentation is maintained THEN it SHALL use MkDocs with automatic generation and proper navigation structure
7. WHEN CI/CD is executed THEN it SHALL run all quality checks, tests, and security scans before deployment

### Requirement 18: Configuration and Environment Management Implementation

**User Story:** As a developer, I want type-safe configuration management that works across different environments, so that I can easily manage settings for development, testing, and production.

#### Acceptance Criteria

1. WHEN configuration is loaded THEN it SHALL use environment variables with proper validation and type safety
2. WHEN dual environments are supported THEN it SHALL handle both server-side (private) and client-side (public) configuration appropriately
3. WHEN API URLs are configured THEN they SHALL support internal server-to-server communication and public client-side requests
4. WHEN environment detection occurs THEN it SHALL properly distinguish between development, testing, and production modes
5. WHEN configuration validation happens THEN it SHALL validate URLs, required fields, and data types at startup
6. WHEN utility functions are provided THEN they SHALL include getApiBaseUrl(), isDevelopment(), and environment-specific helpers
7. WHEN configuration changes THEN they SHALL be reflected without requiring application restarts where possible

### Requirement 19: Code Architecture and Quality Standards Implementation

**User Story:** As a developer, I want consistent code architecture and quality standards enforced throughout the codebase, so that the application is maintainable, secure, and follows best practices.

#### Acceptance Criteria

1. WHEN service layer architecture is implemented THEN all business logic SHALL be in app/core/services/ with thin API route handlers
2. WHEN error handling is implemented THEN it SHALL use custom exceptions, proper HTTP status codes, and user-friendly messages
3. WHEN authentication is implemented THEN it SHALL support multiple token types (JWT, Bearer, API keys) with proper security measures
4. WHEN caching is implemented THEN it SHALL use Cashews exclusively with short TTLs and logical key prefixes
5. WHEN logging is implemented THEN it SHALL use loguru exclusively with structured, context-bound logging
6. WHEN type checking is enforced THEN it SHALL use mypy with strict configuration and type hints throughout
7. WHEN code style is enforced THEN it SHALL use ruff for formatting/linting with 119-character line limits and consistent patterns

### Requirement 20: Testing Architecture and Quality Assurance Implementation

**User Story:** As a developer, I want comprehensive testing coverage with multiple testing levels, so that I can ensure code quality, catch regressions, and maintain system reliability.

#### Acceptance Criteria

1. WHEN unit testing is performed THEN it SHALL use pytest with async support, proper fixtures, and minimum 80% coverage
2. WHEN integration testing is performed THEN it SHALL use testcontainers with real databases and API endpoint testing
3. WHEN E2E testing is performed THEN it SHALL use Playwright with both mocked and full-stack testing scenarios
4. WHEN test data is generated THEN it SHALL use polyfactory for consistent, realistic test data creation
5. WHEN test environments are managed THEN they SHALL provide proper isolation, cleanup, and reproducible results
6. WHEN CI testing is executed THEN it SHALL run all test levels, quality checks, and security scans automatically
7. WHEN test utilities are provided THEN they SHALL include authentication helpers, API mocking, and common test patterns

### Requirement 21: User Authentication and Project Management Workflow Implementation

**User Story:** As a user, I want seamless authentication and project selection workflows that maintain context across sessions, so that I can efficiently access my authorized projects and data.

#### Acceptance Criteria

1. WHEN a user logs in THEN they SHALL be authenticated with username/password and receive a session cookie with proper persistence
2. WHEN multiple projects are available THEN the system SHALL present a project selection interface with clear project information
3. WHEN a project is selected THEN it SHALL be stored in local session and persist across page reloads
4. WHEN project context is active THEN the dashboard SHALL show system-wide activity with sensitive campaigns redacted for unauthorized users
5. WHEN session management occurs THEN it SHALL handle token expiration, refresh, and logout gracefully
6. WHEN role-based access is enforced THEN users SHALL only see projects and functions appropriate to their assigned roles
7. WHEN project switching happens THEN it SHALL update the global context and refresh all relevant data displays

### Requirement 22: Real-Time Dashboard and Monitoring Workflow Implementation

**User Story:** As a user, I want a real-time dashboard that provides live updates on campaign progress, agent status, and system activity, so that I can monitor operations effectively.

#### Acceptance Criteria

1. WHEN the dashboard loads THEN it SHALL fetch and display campaigns, active agents, and task progress with proper loading states
2. WHEN SSE connections are established THEN they SHALL provide real-time updates for agent status, crack events, and campaign progress
3. WHEN dashboard cards are displayed THEN they SHALL show online agents, running tasks, recently cracked hashes, and system hash rate trends
4. WHEN campaign rows are shown THEN they SHALL display progress bars, state icons, attack summaries, and ETAs with expandable details
5. WHEN crack events occur THEN they SHALL trigger toast notifications and update relevant progress indicators
6. WHEN agent status changes THEN it SHALL update the agent sheet, dashboard cards, and any relevant displays
7. WHEN system events happen THEN they SHALL trigger appropriate UI updates in campaign rows, resource tables, and status indicators

### Requirement 23: Campaign Creation and Management Workflow Implementation

**User Story:** As a user, I want intuitive campaign creation and management workflows that guide me through configuration and provide clear feedback, so that I can efficiently set up and control cracking operations.

#### Acceptance Criteria

1. WHEN creating a new campaign THEN the system SHALL provide a guided wizard with hashlist selection, metadata entry, and attack configuration
2. WHEN selecting hashlists THEN users SHALL be able to upload new files or select from existing hashlists with proper validation
3. WHEN configuring attacks THEN the system SHALL provide attack type selection, resource dropdowns, and live keyspace estimation
4. WHEN DAG support is enabled THEN the system SHALL enforce phase-based execution ordering and prevent later phases from running until earlier phases complete
5. WHEN campaigns are launched THEN the system SHALL create tasks, schedule work, and provide confirmation feedback
6. WHEN campaign management actions are performed THEN users SHALL be able to pause, resume, archive, or delete campaigns with appropriate permissions and confirmations
7. WHEN campaign state changes THEN the system SHALL update all relevant displays and provide user feedback through toasts and status updates

### Requirement 24: Agent Management and Control Workflow Implementation

**User Story:** As a user, I want comprehensive agent management capabilities with real-time status monitoring and administrative controls, so that I can effectively manage distributed cracking resources.

#### Acceptance Criteria

1. WHEN viewing agent status THEN the system SHALL display agents in a slide-out sheet with status badges, last seen timestamps, current tasks, and performance metrics
2. WHEN agent details are accessed THEN they SHALL show guess rates, sparklines for performance trends, and current task assignments
3. WHEN administrative controls are used THEN admins SHALL be able to restart agents, deactivate agents, and toggle individual device usage
4. WHEN agent configuration changes are made THEN the system SHALL provide options for immediate application or deferred application to next task
5. WHEN agent heartbeats are received THEN they SHALL update agent status, performance metrics, and availability indicators
6. WHEN agent errors occur THEN they SHALL be logged, displayed in structured format, and trigger appropriate notifications
7. WHEN agent control actions are performed THEN they SHALL provide confirmation dialogs, execute backend commands, and update UI status

### Requirement 25: Resource Management and File Handling Workflow Implementation

**User Story:** As a user, I want efficient resource management workflows for uploading, editing, and organizing attack resources, so that I can maintain and utilize wordlists, rules, and other cracking assets.

#### Acceptance Criteria

1. WHEN uploading resources THEN users SHALL select file type, enter metadata (label, description, sensitivity), and upload via presigned URLs
2. WHEN resource sensitivity is configured THEN the system SHALL enforce proper visibility rules based on project scope and sensitivity flags
3. WHEN inline editing is available THEN users SHALL be able to edit small files (under 1MB) directly in the browser with validation
4. WHEN resource lists are displayed THEN they SHALL show metadata, usage information, and appropriate action buttons based on permissions
5. WHEN resource validation occurs THEN the system SHALL validate file formats, syntax, and content appropriately for each resource type
6. WHEN resource access is controlled THEN the system SHALL enforce project-based and sensitivity-based access restrictions
7. WHEN resource operations complete THEN the system SHALL update resource lists, provide feedback, and maintain proper audit trails

### Requirement 26: Advanced Workflow and Administrative Features Implementation

**User Story:** As an administrator, I want advanced workflow capabilities including health monitoring, template management, and system control, so that I can maintain system health and provide efficient operational tools.

#### Acceptance Criteria

1. WHEN health status is monitored THEN admins SHALL see Redis, MinIO, and PostgreSQL health with metrics, latency, and diagnostic information
2. WHEN campaign templates are used THEN users SHALL be able to export campaigns to JSON and import templates to pre-fill campaign wizards
3. WHEN DAG editing is performed THEN users SHALL be able to reorder attacks, assign phases, and visualize execution dependencies
4. WHEN rule editing with overlays is used THEN users SHALL see diff-style previews, merge options, and learned rules integration
5. WHEN manual task control is needed THEN admins SHALL be able to pause individual tasks and reassign them to different agents
6. WHEN system events require reactive updates THEN the UI SHALL update appropriate locations (toasts, progress bars, status indicators) based on event types
7. WHEN advanced administrative functions are accessed THEN they SHALL be properly restricted to authorized roles and provide appropriate confirmation workflows

### Requirement 27: Component Migration and Template Conversion Implementation

**User Story:** As a developer, I want to successfully migrate existing HTMX/Jinja templates to modern SvelteKit components, so that the UI maintains functionality while adopting modern patterns and improved maintainability.

#### Acceptance Criteria

1. WHEN templates are migrated THEN they SHALL be converted to SvelteKit 5 components using Shadcn-Svelte and Tailwind v4 with proper naming conventions
2. WHEN component architecture is implemented THEN it SHALL organize components in appropriate subdirectories (agents/, campaigns/, attacks/, resources/, users/, projects/)
3. WHEN legacy functionality is preserved THEN all original features SHALL be maintained while removing HTMX, Alpine.js, and Jinja dependencies
4. WHEN forms are implemented THEN they SHALL use Formsnap with Zod validation and SvelteKit actions instead of HTMX form handling
5. WHEN data loading is implemented THEN it SHALL use SvelteKit load functions and Svelte stores instead of server-side template rendering
6. WHEN interactivity is implemented THEN it SHALL use Svelte reactivity and stores instead of Alpine.js or inline JavaScript
7. WHEN component testing is implemented THEN each component SHALL have appropriate Vitest unit tests and Playwright E2E tests

### Requirement 28: Dashboard and Layout Component Implementation

**User Story:** As a user, I want a modern dashboard and layout system that provides intuitive navigation and real-time updates, so that I can efficiently monitor and manage Ouroboros operations.

#### Acceptance Criteria

1. WHEN the base layout is implemented THEN it SHALL provide SvelteKit layout with Sidebar, Header, and Toast components using Shadcn-Svelte
2. WHEN navigation is implemented THEN it SHALL be role-aware with proper access control and active state indicators
3. WHEN the dashboard is implemented THEN it SHALL display status cards (Active Agents, Running Tasks, Cracked Hashes, Resource Usage) with live SSE updates
4. WHEN campaign overview is displayed THEN it SHALL show accordion-style rows with expandable details and real-time progress updates
5. WHEN toast notifications are implemented THEN they SHALL use Shadcn-Svelte Toast components for crack events and system notifications
6. WHEN responsive design is applied THEN the layout SHALL work properly on different screen sizes with collapsible sidebar
7. WHEN empty and error states are handled THEN they SHALL provide appropriate user guidance and recovery options

### Requirement 29: Agent Management Component Implementation

**User Story:** As a user, I want comprehensive agent management interfaces that provide real-time monitoring and administrative controls, so that I can effectively manage distributed cracking resources.

#### Acceptance Criteria

1. WHEN agent lists are displayed THEN they SHALL use Svelte tables with filtering, search, and pagination capabilities
2. WHEN agent details are accessed THEN they SHALL display in Shadcn-Svelte modals with tabbed interfaces (Settings, Hardware, Performance, Log, Capabilities)
3. WHEN agent registration is performed THEN it SHALL use Shadcn-Svelte forms with proper validation and error handling
4. WHEN agent status is monitored THEN it SHALL show real-time updates via SSE with status badges and performance metrics
5. WHEN administrative controls are used THEN they SHALL provide confirmation dialogs and proper permission checking
6. WHEN agent performance is displayed THEN it SHALL include charts, sparklines, and benchmark information
7. WHEN agent errors are shown THEN they SHALL display in structured, color-coded log format with timestamps

### Requirement 30: Campaign and Attack Management Component Implementation

**User Story:** As a user, I want intuitive campaign and attack management interfaces that support complex configurations and provide clear feedback, so that I can efficiently set up and monitor cracking operations.

#### Acceptance Criteria

1. WHEN campaign lists are displayed THEN they SHALL use Svelte tables with accordion-style expandable rows and real-time progress updates
2. WHEN campaign details are accessed THEN they SHALL show attack tables with proper action menus and status indicators
3. WHEN campaign creation is performed THEN it SHALL use guided wizard modals with step-by-step configuration
4. WHEN attack configuration is performed THEN it SHALL provide type-specific editors (Dictionary, Mask, Brute Force) with live keyspace estimation
5. WHEN attack parameters are modified THEN they SHALL show real-time validation and complexity scoring with dot-based meters
6. WHEN campaign management actions are performed THEN they SHALL provide appropriate confirmation dialogs and state updates
7. WHEN DAG support is enabled THEN it SHALL provide visual phase ordering and dependency management

### Requirement 31: Resource and User Management Component Implementation

**User Story:** As a user, I want efficient resource and user management interfaces that support file operations and administrative functions, so that I can maintain system assets and user accounts effectively.

#### Acceptance Criteria

1. WHEN resource lists are displayed THEN they SHALL show file metadata, usage information, and type-based filtering with search capabilities
2. WHEN resource details are accessed THEN they SHALL provide preview, content editing, and line-by-line management for supported file types
3. WHEN resource uploads are performed THEN they SHALL use presigned URLs with progress indicators and validation feedback
4. WHEN user management is accessed THEN it SHALL provide admin-only interfaces with role-based access control and project associations
5. WHEN user details are managed THEN they SHALL use Shadcn-Svelte forms with proper validation and confirmation workflows
6. WHEN project management is performed THEN it SHALL provide project listing, creation, and configuration interfaces
7. WHEN sensitive resources are handled THEN they SHALL enforce proper visibility and access restrictions based on project scope

### Requirement 32: Form Handling and Data Management Implementation

**User Story:** As a developer, I want consistent form handling and data management patterns throughout the application, so that all user interactions are reliable, validated, and provide appropriate feedback.

#### Acceptance Criteria

1. WHEN forms are implemented THEN they SHALL use Formsnap with Zod validation schemas and SvelteKit actions for submission
2. WHEN form validation occurs THEN it SHALL provide real-time client-side validation with server-side confirmation
3. WHEN data loading is performed THEN it SHALL use SvelteKit load functions with proper error handling and loading states
4. WHEN API integration is implemented THEN it SHALL use consistent patterns for authentication, error handling, and response processing
5. WHEN state management is implemented THEN it SHALL use Svelte stores for reactive data with proper SSE integration
6. WHEN file operations are performed THEN they SHALL handle uploads, downloads, and inline editing with appropriate progress feedback
7. WHEN error handling is implemented THEN it SHALL provide user-friendly messages without exposing internal system details

### Requirement 7: Form Validation and Error Handling

**User Story:** As a user, I want all forms to provide clear validation feedback and handle errors gracefully, so that I can complete tasks efficiently with proper guidance when issues occur.

#### Acceptance Criteria

1. WHEN form validation occurs THEN it SHALL validate on both client-side and server-side using OpenAPI spec and Zod schemas
2. WHEN validation errors are displayed THEN they SHALL appear near relevant form fields with clear messaging
3. WHEN forms are submitted THEN they SHALL show loading states and provide success/error feedback
4. WHEN server-side validation fails THEN errors SHALL be reported clearly without exposing internal details
5. WHEN progressive enhancement is used THEN forms SHALL work with JavaScript disabled
6. WHEN form persistence is needed THEN data SHALL be maintained during navigation
7. WHEN Superforms v2 is used THEN it SHALL integrate consistently with SvelteKit actions and Shadcn-Svelte components

### Requirement 8: API Integration and Data Management

**User Story:** As a developer, I want all API interactions to follow consistent patterns and handle authentication properly, so that data flows reliably between frontend and backend systems.

#### Acceptance Criteria

1. WHEN API calls are made THEN they SHALL use the OpenAPI spec from `contracts/current_api_openapi.json`
2. WHEN Zod schemas are used THEN they SHALL be generated from the OpenAPI spec in `frontend/src/lib/schemas/`
3. WHEN authentication tokens are managed THEN they SHALL be handled securely with proper expiration and refresh
4. WHEN API errors occur THEN they SHALL be handled gracefully with appropriate user feedback
5. WHEN SSR load functions are used THEN they SHALL handle authenticated API calls and error states properly
6. WHEN real-time data is needed THEN it SHALL use SSE connections with fallback to manual refresh
7. WHEN environment detection is used THEN it SHALL properly distinguish between test and production environments
