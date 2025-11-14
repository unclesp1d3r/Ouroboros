# Implementation Plan

## Overview

This implementation plan converts the NiceGUI Web Interface design into a series of coding tasks for implementing a Python-native web interface integrated directly into the Ouroboros FastAPI backend. The tasks are organized to build incrementally from core infrastructure to complete functionality, ensuring each step builds on previous work and results in a fully integrated system.

## UX Documentation References

The implementation should follow the detailed UX specifications and user flow documentation:

### Core UX Design Documents

- **[Dashboard UX Design](../../../docs/v2_rewrite_implementation_plan/notes/ui_screens/dashboard-ux.md)** - Complete dashboard layout, metrics cards, campaign overview, and real-time update specifications

- **[Campaign List View](../../../docs/v2_rewrite_implementation_plan/notes/ui_screens/campaign_list_view.md)** - Campaign table layout, attack display, and action menus

- **[User Flows Notes](../../../docs/v2_rewrite_implementation_plan/notes/user_flows_notes.md)** - Comprehensive user interaction flows and role-based access patterns

### Component-Specific Documentation

- **[Dictionary Attack Editor](../../../docs/v2_rewrite_implementation_plan/notes/ui_screens/new_dictionary_attack_editor.md)** - Attack configuration modal design and form patterns

- **[Agent Notes](../../../docs/v2_rewrite_implementation_plan/notes/agent_notes.md)** - Agent monitoring, configuration, and management interface specifications

- **[Campaign Notes](../../../docs/v2_rewrite_implementation_plan/notes/campaign_notes.md)** - Campaign behavior, attack ordering, and toolbar functionality

### Additional UX Screens

- **[Mask Attack Editor](../../../docs/v2_rewrite_implementation_plan/notes/ui_screens/new_mask_attack_editor.md)** - Mask attack configuration patterns

- **[Brute Force Attack Editor](../../../docs/v2_rewrite_implementation_plan/notes/ui_screens/brute_force_attack_editor.md)** - Brute force attack setup

- **[Health Status Screen](../../../docs/v2_rewrite_implementation_plan/notes/ui_screens/health_status_screen.md)** - System health monitoring interface

Each task references the relevant UX documentation to ensure the NiceGUI implementation matches the established design patterns and user experience requirements.

## Implementation Tasks

- [ ] 1. Create Basic NiceGUI Integration

  - Create `app/ui/__init__.py` with basic setup function
  - Implement minimal `ui.run_with()` integration with FastAPI
  - Test that NiceGUI routes are accessible at `/ui/` path
  - _Requirements: 1.1, 1.2, 1.3_

- [ ] 1.1 Set Up Directory Structure

  - Create `app/ui/` directory with subdirectories: `auth/`, `components/`, `pages/`, `services/`
  - Add `__init__.py` files to make directories proper Python packages
  - Create empty placeholder files for future components
  - _Requirements: 1.1, 1.4_

- [ ] 1.2 Create Hello World Page

  - Create `app/ui/pages/hello.py` with simple NiceGUI page
  - Add basic route at `/ui/hello` to test integration
  - Verify page loads and displays content correctly
  - _Requirements: 1.1, 1.5_

- [ ] 1.3 Configure Storage and Settings

  - Add storage secret configuration from application settings
  - Set up basic NiceGUI configuration options
  - Test configuration loading and application startup
  - _Requirements: 1.1, 1.3_

- [ ] 2. Create Basic Login Page

  - Create `app/ui/pages/login.py` with simple login form
  - Add username and password input fields
  - Implement basic form submission without authentication
  - _Requirements: 8.2, 8.3_

- [ ] 2.1 Add Authentication Logic

  - Integrate login form with existing `app.core.auth` system
  - Implement session cookie creation on successful login
  - Add error handling for invalid credentials
  - _Requirements: 8.1, 8.2, 8.5_

- [ ] 2.2 Create Authentication Middleware

  - Create `app/ui/auth/middleware.py` with basic route protection
  - Implement session validation for protected routes
  - Add redirect logic for unauthenticated users
  - _Requirements: 8.1, 8.4, 8.6_

- [ ] 2.3 Add User Context Helpers

  - Create `app/ui/auth/context.py` with user session utilities
  - Implement user role checking functions
  - Add logout functionality with session cleanup
  - _Requirements: 8.3, 8.6, 8.7_

- [ ] 3. Create Basic Layout Component

  - Create `app/ui/components/layout.py` with simple header and main content area
  - Add basic CSS styling for layout structure
  - Test layout component with placeholder content
  - _Requirements: 10.1, 10.6_

- [ ] 3.1 Add Sidebar Navigation

  - Create sidebar component following [User Flows](../../../docs/v2_rewrite_implementation_plan/notes/user_flows_notes.md) navigation patterns
  - Add navigation links: Dashboard, Campaigns, Attacks, Agents, Resources, Users (admin only), Settings
  - Implement collapsible sidebar with logo and active item indicators
  - Add role-based menu item visibility (Users menu for admins only)
  - _Requirements: 10.2, 10.3_
  - _Reference: [User Flows - Authentication & Session](../../../docs/v2_rewrite_implementation_plan/notes/user_flows_notes.md#authentication--session)_

- [ ] 3.2 Create Header Component

  - Add application header with title and branding
  - Create user menu dropdown with logout option
  - Implement responsive header design
  - _Requirements: 10.2, 10.6_

- [ ] 3.3 Add Navigation State Management

  - Implement active page highlighting in navigation
  - Add role-based menu item visibility
  - Create navigation helpers for programmatic routing
  - _Requirements: 10.2, 10.3_

- [ ] 4. Create Dashboard Page

  - Create `app/ui/pages/dashboard.py` with basic dashboard layout following [Dashboard UX Design](../../../docs/v2_rewrite_implementation_plan/notes/ui_screens/dashboard-ux.md)
  - Implement sidebar + header layout with responsive, dark-mode-friendly design
  - Add placeholder content for metrics cards and campaign overview sections
  - Integrate with base layout component
  - _Requirements: 2.1, 2.6_
  - _Reference: [Dashboard UX Design](../../../docs/v2_rewrite_implementation_plan/notes/ui_screens/dashboard-ux.md)_

- [ ] 4.1 Create Metric Cards Component

  - Create `app/ui/components/cards.py` with metric card component following dashboard UX specifications
  - Implement four key cards: Active Agents (clickable to open Agent Sheet), Running Tasks, Recently Cracked Hashes (24h), Resource Usage (sparkline chart)
  - Use compact, visually scannable format with numeric highlights and optional icons
  - Display static data initially (no real-time updates yet)
  - _Requirements: 2.2, 2.3, 2.4_
  - _Reference: [Dashboard UX Design - Layout Overview](../../../docs/v2_rewrite_implementation_plan/notes/ui_screens/dashboard-ux.md#layout-overview)_

- [ ] 4.2 Integrate Dashboard Data Service

  - Connect dashboard to existing backend dashboard service
  - Fetch and display real dashboard metrics
  - Add error handling for data loading failures
  - _Requirements: 2.1, 2.7_

- [ ] 4.3 Add Campaign Overview Section

  - Create accordion-style campaign list component following [Campaign Overview Section](../../../docs/v2_rewrite_implementation_plan/notes/ui_screens/dashboard-ux.md#campaign-overview-section) design
  - Display campaigns sorted by Running first, then most recently updated
  - Show campaign name, progress bar (keyspace-weighted), state badges, and summary with compact state indicators
  - Implement expandable rows for attack details with progress bars and ETAs
  - Add navigation links to detailed campaign pages
  - _Requirements: 2.5, 2.6_
  - _Reference: [Dashboard UX - Campaign Overview](../../../docs/v2_rewrite_implementation_plan/notes/ui_screens/dashboard-ux.md#campaign-overview-section)_

- [ ] 4.4 Implement Real-time Updates

  - Create `app/ui/services/ui_events.py` for SSE integration following [Technical Notes](../../../docs/v2_rewrite_implementation_plan/notes/ui_screens/dashboard-ux.md#technical-notes)
  - Add real-time updates to dashboard metrics with stale data indicators (>30 seconds)
  - Implement connection status indicators and "Refresh Now" button for manual recovery
  - Add toast notifications for SSE disconnections and crack events
  - _Requirements: 2.8, 9.1, 9.2, 9.3_
  - _Reference: [Dashboard UX - Technical Notes](../../../docs/v2_rewrite_implementation_plan/notes/ui_screens/dashboard-ux.md#technical-notes)_

- [ ] 5. Create Campaign List Page

  - Create `app/ui/pages/campaigns.py` with campaign listing following [Campaign List View](../../../docs/v2_rewrite_implementation_plan/notes/ui_screens/campaign_list_view.md) design
  - Display campaigns in table format with six columns: Attack, Language, Length, Settings, Passwords to Check, Complexity
  - Add campaign information with human-readable labels and blue-linked settings summaries
  - Implement gear icon context menus for each campaign row
  - _Requirements: 3.1, 3.4_
  - _Reference: [Campaign List View](../../../docs/v2_rewrite_implementation_plan/notes/ui_screens/campaign_list_view.md)_

- [ ] 5.1 Add Campaign Search and Filtering

  - Implement search functionality for campaign names
  - Add status-based filtering (active, draft, archived)
  - Create filter controls and search input
  - _Requirements: 3.2, 3.3_

- [ ] 5.2 Create Campaign Data Table Component

  - Create `app/ui/components/tables.py` with reusable table component
  - Add sorting functionality for table columns
  - Implement pagination controls for large datasets
  - _Requirements: 3.1, 3.9_

- [ ] 5.3 Add Campaign Actions

  - Create gear icon context menus with actions: Edit, Duplicate, Move Up/Down, Remove following [Campaign Notes](../../../docs/v2_rewrite_implementation_plan/notes/campaign_notes.md#attack-row-actions-context-menu)
  - Add campaign status badges with color coding (Running=purple, Completed=green, Error=red, Paused=gray)
  - Implement campaign control actions (Start/Stop, Pause/Resume) with confirmation modals
  - Add bulk select controls with Check All and Bulk Delete functionality
  - _Requirements: 3.7, 3.8_
  - _Reference: [Campaign Notes - Attack Row Actions](../../../docs/v2_rewrite_implementation_plan/notes/campaign_notes.md#attack-row-actions-context-menu)_

- [ ] 5.4 Create Campaign Creation Form

  - Create simple campaign creation form
  - Add form validation and error handling
  - Implement form submission and success feedback
  - _Requirements: 3.6, 3.8_

- [ ] 5.5 Add Campaign Detail View

  - Create detailed campaign page with full information
  - Display campaign statistics and progress tracking
  - Add navigation from campaign list to detail view
  - _Requirements: 3.5, 3.7_

- [ ] 6. Create Agent List Page

  - Create `app/ui/pages/agents.py` with agent listing following [Agent Notes](../../../docs/v2_rewrite_implementation_plan/notes/agent_notes.md#agent-list-view-overview-table) specifications
  - Display agents in table with columns: Agent Name + OS, Status, Temperature (°C), Utilization, Current/Average Attempts/sec, Current Job
  - Show status indicators with color coding (🟢 Online, 🟡 Idle, 🔴 Offline)
  - Add gear icon menu for admin-only actions (Disable Agent, View Details)
  - _Requirements: 4.1, 4.2_
  - _Reference: [Agent Notes - Agent List View](../../../docs/v2_rewrite_implementation_plan/notes/agent_notes.md#agent-list-view-overview-table)_

- [ ] 6.1 Add Agent Status Monitoring

  - Implement real-time agent status updates
  - Add agent heartbeat monitoring and connection status
  - Create visual indicators for agent health
  - _Requirements: 4.2, 4.3, 4.6_

- [ ] 6.2 Create Agent Performance Display

  - Add agent performance metrics (hashrate, task completion)
  - Display agent capability information
  - Create simple performance charts or indicators
  - _Requirements: 4.3, 4.6_

- [ ] 6.3 Add Agent Management Actions

  - Create agent control interface following [Agent Detail View](../../../docs/v2_rewrite_implementation_plan/notes/agent_notes.md#agent-detail-view-tabbed-interface) with tabbed interface
  - Implement Settings tab (Agent Label, Enabled toggle, Update Interval, Project Assignment)
  - Add Hardware tab with device enable/disable toggles and hardware acceleration settings
  - Create Performance tab with line charts and device utilization cards
  - Add Log tab with colored severity indicators for agent errors
  - _Requirements: 4.4, 4.5, 4.7_
  - _Reference: [Agent Notes - Agent Detail View](../../../docs/v2_rewrite_implementation_plan/notes/agent_notes.md#agent-detail-view-tabbed-interface)_

- [ ] 7. Create Attack Configuration Page

  - Create `app/ui/pages/attacks.py` with basic attack listing
  - Display attacks with status and progress information
  - Add navigation to attack configuration forms
  - _Requirements: 5.5, 5.6_

- [ ] 7.1 Create Attack Mode Selection

  - Implement attack mode selection following [Dictionary Attack Editor](../../../docs/v2_rewrite_implementation_plan/notes/ui_screens/new_dictionary_attack_editor.md) design patterns
  - Create modal dialogs for each attack type with guided wizard steps (not tabs)
  - Add dictionary selection dropdown, length range inputs, and modifier buttons
  - Implement real-time keyspace estimation via `/api/v1/web/attacks/estimate` endpoint
  - Create form validation with complexity scoring (1-5 dots) and password count display
  - _Requirements: 5.1, 5.2_
  - _Reference: [Dictionary Attack Editor](../../../docs/v2_rewrite_implementation_plan/notes/ui_screens/new_dictionary_attack_editor.md)_

- [ ] 7.2 Add Resource Selection Interface

  - Create resource selection for wordlists and rules
  - Implement file browser for resource selection
  - Add resource validation and compatibility checking
  - _Requirements: 5.3, 5.4_

- [ ] 7.3 Implement Attack Progress Tracking

  - Add attack progress indicators and status display
  - Create attack control actions (start, pause, stop)
  - Display attack results and completion statistics
  - _Requirements: 5.5, 5.6, 5.7_

- [ ] 8. Create Resource List Page

  - Create `app/ui/pages/resources.py` with resource listing
  - Display resources with type, size, and upload date
  - Add basic resource information and metadata
  - _Requirements: 6.1, 6.4_

- [ ] 8.1 Add Resource Upload Interface

  - Create simple file upload form
  - Add file validation and type checking
  - Implement upload progress indicators
  - _Requirements: 6.2, 6.3_

- [ ] 8.2 Create Resource Management Features

  - Add resource search and filtering capabilities
  - Implement resource categorization (wordlists, rules, etc.)
  - Create resource details view with usage statistics
  - _Requirements: 6.1, 6.3, 6.4_

- [ ] 8.3 Add Resource Actions

  - Create download functionality for resources
  - Add resource deletion with confirmation
  - Implement resource sharing and access control
  - _Requirements: 6.5, 6.6_

- [ ] 9. Create User Management Page

  - Create `app/ui/pages/users.py` with user listing (admin only)
  - Display users with roles and status information
  - Add role-based access control for page visibility
  - _Requirements: 7.1, 7.2_

- [ ] 9.1 Add User Creation Form

  - Create user creation form with basic fields
  - Add role assignment dropdown
  - Implement form validation and submission
  - _Requirements: 7.2, 7.3_

- [ ] 9.2 Create User Editing Interface

  - Add user editing functionality
  - Implement user deactivation and status management
  - Create user profile management interface
  - _Requirements: 7.3, 7.5_

- [ ] 9.3 Add User Activity Display

  - Display user login history and activity
  - Add user session management information
  - Create basic user audit trail
  - _Requirements: 7.4, 7.6_

- [ ] 10. Add Basic Notification System

  - Create toast notification system following [Live Toast Notifications](../../../docs/v2_rewrite_implementation_plan/notes/ui_screens/dashboard-ux.md#live-toast-notifications) specifications
  - Implement crack event notifications with rate limiting and batch grouping
  - Add success/error message display with links to relevant views (hashlist, campaign)
  - Create notification preferences and suppression options
  - _Requirements: 9.3, 9.4_
  - _Reference: [Dashboard UX - Live Toast Notifications](../../../docs/v2_rewrite_implementation_plan/notes/ui_screens/dashboard-ux.md#live-toast-notifications)_

- [ ] 10.1 Enhance SSE Integration

  - Expand SSE integration to all relevant pages
  - Add connection status indicators across the interface
  - Implement automatic reconnection logic
  - _Requirements: 9.1, 9.2, 9.5_

- [ ] 10.2 Add Progress Tracking Components

  - Create progress bars for long-running operations
  - Add real-time progress updates for campaigns and attacks
  - Implement completion time estimates
  - _Requirements: 9.1, 9.2, 9.4_

- [ ] 11. Add Responsive Design

  - Make layouts responsive for mobile and tablet devices
  - Implement mobile-friendly navigation
  - Add responsive data tables with horizontal scrolling
  - _Requirements: 10.1, 10.6_

- [ ] 11.1 Implement Basic Accessibility

  - Add keyboard navigation support
  - Implement ARIA labels for screen readers
  - Create focus management for interactive elements
  - _Requirements: 10.7_

- [ ] 11.2 Enhance Error Handling

  - Improve error messages and user feedback
  - Add loading states for all async operations
  - Implement retry mechanisms for failed operations
  - _Requirements: 10.4, 10.5, 10.6_

- [ ] 12. Create Basic Component Tests

  - Set up NiceGUI testing framework
  - Create tests for basic UI components (cards, forms, tables)
  - Test component rendering and basic interactions
  - _Testing Strategy: Component Testing_

- [ ] 12.1 Add Page Structure Tests

  - Test page layouts and navigation
  - Verify authentication flows work correctly
  - Test form validation and error handling
  - _Testing Strategy: Component Testing_

- [ ] 12.2 Implement Basic E2E Tests

  - Set up Playwright testing framework
  - Create login workflow test
  - Test basic navigation between pages
  - _Testing Strategy: End-to-End Testing_

- [ ] 12.3 Add Comprehensive E2E Tests

  - Test complete user workflows (campaign creation, etc.)
  - Add cross-browser compatibility tests
  - Create performance and accessibility tests
  - _Testing Strategy: End-to-End Testing_

- [ ] 13. Finalize FastAPI Integration

  - Complete integration with existing FastAPI application
  - Test all NiceGUI routes work with existing authentication
  - Verify no conflicts with existing API endpoints
  - _Requirements: 1.1, 1.3_

- [ ] 13.1 Add Production Configuration

  - Configure security settings for production deployment
  - Set up proper static file serving
  - Add health checks for NiceGUI routes
  - _Requirements: 1.3_

- [ ] 13.2 Create Basic Documentation

  - Write user guide for the NiceGUI interface
  - Document installation and setup procedures
  - Create troubleshooting guide for common issues
  - _Documentation Requirements_
