# Phase 3 Step 3: Advanced Features & Real-Time Capabilities

**🎯 Advanced Features Step** - This step implements real-time capabilities, completes advanced attack features, and finishes resource management functionality.

---

## Table of Contents

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=2 --minlevel=1 -->

- [Phase 3 Step 3: Advanced Features & Real-Time Capabilities](#phase-3-step-3-advanced-features--real-time-capabilities)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [Real-Time Features Implementation](#real-time-features-implementation)
  - [Advanced Attack Features](#advanced-attack-features)
  - [Complete Resource Management](#complete-resource-management)
  - [Hash List Management Implementation](#hash-list-management-implementation)
  - [Advanced Features Testing](#advanced-features-testing)
  - [Validation & Success Criteria](#validation--success-criteria)
  - [Implementation Notes](#implementation-notes)
  - [Completion Definition](#completion-definition)

<!-- mdformat-toc end -->

---

## Overview

With core functionality verified and user management complete, this step focuses on advanced features that enhance the user experience: real-time updates via SSE, advanced attack configuration options, complete resource management workflows, and enhanced campaign operations.

### Critical Context Notes

- **SSE Architecture**: Server-Sent Events provide lightweight trigger notifications (not full data streaming) for real-time updates
- **Attack Editor Context**: Dictionary attacks support ephemeral wordlists, mask attacks create one-time mask lists, brute force is a UI wrapper for incremental masks
- **Resource Management**: Upload page supports file drop zones, inline editing for small files, and atomic operations to prevent orphaned data
- **Hash List Integration**: Crackable uploads support dual input modes (file upload + text paste) with intelligent hash type detection
- **Real-time Features**: Toast notifications batch rapid events, SSE connections handle reconnection, project-scoped filtering prevents data leaks
- **Campaign Operations**: Export/import uses JSON schema with GUID-based resource references, lifecycle operations include start/pause/resume/stop
- **Performance Requirements**: Live keyspace estimation via `/api/v1/web/attacks/estimate`, real-time progress tracking without performance impact
- **Testing Strategy**: All user-facing functionality must have both E2E tests (mocked and full E2E). Follow the [full testing architecture](../side_quests/full_testing_architecture.md) document and refer to `.cursor/rules/testing/e2e-docker-infrastructure.mdc` and `.cursor/rules/testing/testing-patterns.mdc` for detailed guidelines.
- **E2E Testing Structure**: `frontend/e2e/` contains mocked E2E tests (fast, no backend), `frontend/tests/e2e/` contains full E2E tests (slower, real backend). Configs: `playwright.config.ts` (mocked) vs `playwright.config.e2e.ts` (full backend)

## Real-Time Features Implementation

### Server-Sent Events (SSE) Infrastructure

**🔧 Technical Context**: SSE provides lightweight trigger notifications (not full data streaming). Events are project-scoped to prevent data leaks. Frontend uses EventSource with reconnection handling.

- [ ] **SSE-001**: Implement SSE endpoints in backend

  - [ ] Wire `/api/v1/web/live/agents` endpoint for agent status updates
  - [ ] Wire `/api/v1/web/live/campaigns` endpoint for campaign progress updates
  - [ ] Wire `/api/v1/web/live/toasts` endpoint for system notifications
  - [ ] Implement project-scoped event filtering (users see only their project events)
  - [ ] Add lightweight trigger notifications (not full data streaming)

- [ ] **SSE-002**: Frontend SSE listeners implementation

  - [ ] Create SSE service for managing EventSource connections
  - [ ] Implement automatic reconnection handling and graceful degradation
  - [ ] Add connection cleanup and timeout handling
  - [ ] Implement proper error handling for connection failures

### Real-Time Dashboard Updates

- [ ] **REALTIME-001**: Dashboard real-time capabilities
  - [ ] Campaign progress updates via SSE (`DRM-002a`)
    - **Progress UI**: Smooth progress bar animations with percentage displays
    - **Visual Feedback**: Progress bars change color based on campaign state (purple=running, green=completed)
    - **Live Updates**: Keyspace-weighted progress via SSE without page refresh
    - **Performance**: Throttled updates to prevent UI flooding
  - [ ] Agent status updates in real-time (`DRM-002b`)
    - **Status Indicators**: Real-time badge color changes (🟢 Online → 🔴 Offline)
    - **Agent Sheet**: Live updates in the slide-out Agent Status Sheet
    - **Table Updates**: Agent list table rows update status without full refresh
    - **Performance Metrics**: Live temperature, utilization, and hash rate displays
  - [ ] Task completion notifications with targeted component refresh (`DRM-002d`)
    - **Task Status**: Real-time updates to running/completed task counts
    - **Agent Assignment**: Show which agents receive new tasks
    - **Completion Feedback**: Visual confirmation when tasks finish
  - [ ] System health status updates (`DRM-002e`)
    - **Health Cards**: Color-coded service status indicators (Redis, MinIO, PostgreSQL)
    - **Alert Banners**: System-wide health issues displayed prominently
    - **Recovery Actions**: Retry buttons for failed services
  - [ ] SSE connection cleanup and timeout handling (`DRM-002f`)
    - **Connection Status**: Visual indicator of SSE connection state
    - **Reconnection Logic**: Automatic reconnection with exponential backoff
    - **Fallback Mode**: Switch to polling when SSE fails

### Toast Notification System Enhancement

- [ ] **TOAST-001**: Complete toast notification system

  - [ ] Crack event notifications with details (`NOT-002a`)
    - **Toast Design**: Shadcn-Svelte Toast with crack details (plaintext, attack used, timestamp)
    - **Content Display**: Show hash, plaintext, attack method, agent name
    - **Action Links**: Click toast to view full hashlist or suppress future toasts
  - [ ] Agent status change notifications (`NOT-002b`)
    - **Status Alerts**: Agent connection/disconnection notifications with agent name
    - **Visual Indicators**: Use appropriate icons and colors for status changes
  - [ ] Campaign completion notifications (`NOT-002c`)
    - **Completion Alerts**: Prominent notifications when campaigns complete or fail
    - **Summary Info**: Show campaign name, completion time, crack count
  - [ ] System error notifications (`NOT-002d`)
    - **Error Toasts**: System-level error notifications with actionable information
    - **Severity Levels**: Different styling for warnings vs critical errors
  - [ ] Batched notification handling (`NOT-002e`)
    - **Batching Logic**: Group multiple rapid cracks into batch notifications
    - **Rate Limiting**: Prevent notification spam during high crack rates

- [ ] **TOAST-002**: Toast UI behaviors

  - [ ] Success toast display and auto-dismiss (`NOT-001a`)
    - **Auto-dismiss**: Configurable timeout for success notifications
    - **Visual Design**: Green color scheme with checkmark icons
  - [ ] Error toast display with retry actions (`NOT-001b`)
    - **Persistent Errors**: Error toasts remain until manually dismissed
    - **Retry Actions**: Include retry buttons for recoverable errors
  - [ ] Info toast for system notifications (`NOT-001c`)
    - **Information Display**: Blue color scheme for informational messages
    - **System Updates**: Maintenance notices, feature announcements
  - [ ] Toast stacking and queue management (`NOT-001d`)
    - **Stack Behavior**: Multiple toasts stack vertically with proper spacing
    - **Queue Management**: Limit maximum concurrent toasts
  - [ ] Manual toast dismissal (`NOT-001e`)
    - **Close Controls**: X button on all toasts for manual dismissal
    - **Swipe Gestures**: Support swipe-to-dismiss on touch devices
  - [ ] Visual hierarchy with color coding and iconography (`NOT-001f`)
    - **Color System**: Success=green, Error=red, Warning=yellow, Info=blue
    - **Icon Usage**: Consistent iconography for different notification types
  - [ ] Toast notification batching for rapid events (`NOT-001g`)
    - **Batch Display**: Show "5 new cracks" instead of 5 individual toasts
    - **Expandable**: Click to see individual items in batch

## Advanced Attack Features

### Advanced Attack Configuration

**🔧 Technical Context**: Dictionary attacks support user-friendly modifier buttons (+Change Case, +Substitute Characters) that abstract hashcat rule complexity. Advanced users can select rule files directly. Ephemeral wordlists stored only on Attack object. All UI components must use idiomatic Shadcn-Svelte patterns.

- [ ] **ATTACK-ADV-001**: Rule modificators and custom rules

  - [ ] Rule explanation modal enhancement (`ATT-004a`)
  - [ ] Custom rule creation and validation
  - [ ] Rule preview and testing capabilities
  - [ ] Advanced rule combination patterns

- [ ] **ATTACK-ADV-002**: Dynamic wordlist integration

  - [ ] Dynamic wordlist generation from project history (`ATT-004b`)
  - [ ] Previous passwords automatic wordlist creation
  - [ ] User-specific wordlist generation from cracked hashes
  - [ ] Automatic wordlist update workflows

- [ ] **ATTACK-ADV-003**: Attack overlap detection and warnings

  - [ ] Attack overlap detection and warnings (`ATT-004c`)
  - [ ] Keyspace overlap analysis between attacks
  - [ ] Duplicate work prevention alerts
  - [ ] Optimization suggestions for attack ordering

- [ ] **ATTACK-ADV-004**: Attack performance estimation

  - [ ] Live update estimated keyspace and complexity via `/api/v1/web/attacks/estimate` (`ATT-004e`)
  - [ ] Real-time keyspace calculation updates
  - [ ] Performance impact estimation
  - [ ] Time-to-completion predictions

### Campaign Lifecycle Operations

- [ ] **CAMPAIGN-OPS-001**: Campaign lifecycle management

  - [ ] Start campaign with task generation (`CAM-004a`)
  - [ ] Pause running campaign with confirmation (`CAM-004b`)
  - [ ] Resume paused campaign (`CAM-004c`)
  - [ ] Stop campaign with impact assessment (`CAM-004d`)
  - [ ] Campaign deletion with permission checks (`CAM-004e`)

- [ ] **CAMPAIGN-OPS-002**: Advanced campaign features

  - [ ] Show warning + reset if editing running or exhausted attacks
  - [ ] Campaign toolbar with buttons: add attack, sort, bulk-select/delete, start/stop toggle (`CAM-003d`)
  - [ ] Context menu per attack row: edit, duplicate, delete, move up/down/top/bottom (`CAM-003f`)
  - [ ] Attack reordering within campaign (drag-and-drop with keyboard support) (`CAM-003c`)

### Campaign Export/Import

- [ ] **CAMPAIGN-IO-001**: Campaign export/import functionality

  - [ ] Export campaign as JSON template (`CAM-005a`)
  - [ ] Import campaign from JSON file (`CAM-005b`)
  - [ ] Campaign template validation on import (`CAM-005c`)
  - [ ] Campaign cloning functionality (`CAM-005d`)
  - [ ] Export cracked hashes from campaign (`CAM-005e`)

- [ ] **CAMPAIGN-IO-002**: JSON schema management

  - [ ] Allow JSON export/import of attack or campaign
  - [ ] Validate imported schema (versioned), rehydrate ephemeral lists, re-associate by GUID
  - [ ] Version compatibility handling for imports
  - [ ] Data integrity validation during import/export

## Complete Resource Management

### Resource Upload Enhancement

- [ ] **RESOURCE-UP-001**: Complete resource upload page implementation

  - [ ] Resource upload page loads with file drop zone (`RES-005a`)
    - **Drop Zone UI**: Large, prominent drop zone with drag-over visual feedback
    - **File Picker**: Alternative file picker button for traditional upload
    - **Visual Design**: Use Shadcn-Svelte styling with clear upload icons and instructions
  - [ ] Drag-and-drop file upload interface (`RES-005b`)
    - **Drop Feedback**: Visual highlight and border changes when files dragged over
    - **Multi-file**: Support multiple file selection and upload
    - **File Preview**: Show selected files with name, size, and type before upload
  - [ ] File type validation and restrictions (`RES-005c`)
    - **Client Validation**: Immediate file type checking with error messages
    - **Allowed Types**: Clearly display supported file types (wordlists, rules, masks, charsets)
    - **Size Limits**: Show file size limits and warn before upload attempt
  - [ ] Upload progress indicators and cancellation (`RES-005d`)
    - **Progress UI**: Individual progress bars per file with percentage
    - **Overall Progress**: Total upload progress indicator
    - **Cancel Controls**: Per-file and overall upload cancellation buttons
  - [ ] Large file upload handling and chunking (`RES-005e`)
    - **Chunked Upload**: Break large files into chunks with resume capability
    - **Progress Tracking**: Accurate progress display for chunked uploads
    - **Error Recovery**: Retry failed chunks without restarting entire upload
  - [ ] Resource metadata input form validation (`RES-005f`)
    - **Metadata Form**: Description, tags, category selection with validation
    - **Real-time Validation**: Immediate feedback on required fields
    - **Batch Metadata**: Apply metadata to multiple files at once
  - [ ] Upload completion confirmation and navigation (`RES-005g`)
    - **Success Feedback**: Clear confirmation of successful uploads
    - **Navigation Options**: Go to uploaded resource, upload more, or return to list
    - **Error Summary**: List any failed uploads with retry options

- [ ] **RESOURCE-UP-002**: Advanced upload features

  - [ ] Upload files via presigned URLs
  - [ ] Atomic upload operations (prevent database/storage inconsistencies) (`RES-002f`)
  - [ ] Comprehensive metadata capture during upload process (`RES-002g`)
  - [ ] Upload resume functionality for large files

### Resource Content Management

- [ ] **RESOURCE-CONTENT-001**: Resource line editor implementation

  - [ ] Resource line editor for masks/rules with inline validation
  - [ ] Add/remove rows functionality
  - [ ] Realtime feedback from 422 error response model
  - [ ] Line-oriented editing (add, edit, delete operations on specific lines) (`RES-003g`)
  - [ ] Real-time validation with detailed error messages (`RES-003h`)

- [ ] **RESOURCE-CONTENT-002**: Content editing workflows

  - [ ] Inline editing for small files (\<1MB) (`RES-003d`)
  - [ ] Type-aware editing interfaces (different modes for mask, rule, wordlist, charset) (`RES-003f`)
  - [ ] Content preview without full editing commitment (`RES-003a`)
  - [ ] Resource content editing for small files (implemented in detail pages)

### Resource Detail Pages

- [ ] **RESOURCE-DETAIL-001**: Complete resource detail pages
  - [ ] Resource detail page loads with full information (`RES-006a`)
  - [ ] Resource content preview for supported types (`RES-006b`)
  - [ ] Resource metadata editing and updates (`RES-006c`)
  - [ ] Resource usage history and tracking (`RES-006d`)
  - [ ] Resource content editing for small files (`RES-006e`)
  - [ ] Resource download and export options (`RES-006f`)
  - [ ] Resource deletion with usage validation (`RES-006g`)

## Hash List Management Implementation

### Hash List Operations

- [ ] **HASH-001**: Complete hash list management system
  - [ ] Hash list creation from file upload (dual input modes support) (`HSH-001a`)
  - [ ] Hash list creation from text paste (intelligent parsing from metadata) (`HSH-001b`)
  - [ ] Hash type auto-detection and validation (confidence scoring with override capability) (`HSH-001c`)
  - [ ] Hash list preview and statistics (confirmation screen with detected types) (`HSH-001d`)
  - [ ] Hash list deletion with cascade checks (`HSH-001e`)
  - [ ] Hash isolation from surrounding metadata (shadow files, NTLM pairs) (`HSH-001f`)
  - [ ] Multi-stage validation preventing malformed campaign creation (`HSH-001g`)

### Hash List Integration

- [ ] **HASH-002**: Hash list campaign integration
  - [ ] Hash list selection in campaign creation (`HSH-002a`)
  - [ ] Hash list reuse across multiple campaigns (`HSH-002b`)
  - [ ] Crackable upload flow with hash detection (streamlined workflow design) (`HSH-002c`)
  - [ ] Hash list export in various formats (`HSH-002d`)
  - [ ] Auto-campaign creation from uploaded hashes (dynamic wordlist generation) (`HSH-002e`)
  - [ ] Progress visibility during upload and processing phases (`HSH-002f`)
  - [ ] Manual hash type override when auto-detection fails (`HSH-002g`)

## Advanced Features Testing

### Testing Guidelines & Requirements

**🧪 Critical Testing Context:**

- **Test Structure**: All user-facing functionality must have both E2E tests (mocked and full E2E). Strictly follow existing test structure and naming conventions as described in the [full testing architecture](../side_quests/full_testing_architecture.md) document.
- **Test Execution**:
  - Run `just test-frontend` for mocked E2E tests (fast, no backend required)
  - Run `just test-e2e` for full E2E tests (requires Docker setup, slower but complete integration testing)
  - **Important**: Do not run full E2E tests directly - they require setup code and must run via the `just test-e2e` command
- **Test Utilities**: Use or reuse existing test utils and helpers in `frontend/tests/test-utils.ts` for consistency and maintainability
- **API Integration**: The OpenAPI spec for the current backend is in `contracts/current_api_openapi.json` and should be used for all backend API calls, with Zod objects generated from the spec in `frontend/src/lib/schemas/`
- **Test Notation**: When tasks include notations like (E2E) or (Mock), tests must be created or updated to cover that specific functionality and confirm it works as expected

### UI/UX Requirements & Standards

- **Responsive Design**: Ensure the interface is polished and follows project standards. While mobile support is not a priority, it should be functional and usable on modern desktop browsers and tablets from `1080x720` resolution on up. It is reasonable to develop for support of mobile resolutions.
- **Offline Capability**: Ability to operate entirely without internet connectivity is a priority. No functionality should depend on public CDNs or other internet-based services.
- **API Integration**: The OpenAPI spec for the current backend is in `contracts/current_api_openapi.json` and should be used for all backend API calls, with Zod objects having been generated from the spec in `frontend/src/lib/schemas/`.
- **Testing Coverage**: All forms must be validated using the OpenAPI spec and the Zod objects. All forms must be validated on both server side and client side.

### Real-Time Updates Testing

- [ ] **TEST-DRM-002**: Real-Time Monitoring Tests
  - [ ] **DRM-002a**: Campaign progress updates via SSE (E2E)
  - [ ] **DRM-002b**: Agent status updates in real-time (E2E)
  - [ ] **DRM-002c**: Crack notifications via toast system (E2E + Mock)
  - [ ] **DRM-002d**: Task completion notifications with refresh (E2E)
  - [ ] **DRM-002e**: System health status updates (E2E)
  - [ ] **DRM-002f**: SSE connection cleanup and timeout handling (Mock)
  - [ ] **DRM-002g**: Project-scoped event filtering (E2E)

### Toast Notification Testing

- [ ] **TEST-NOT-001**: Toast Notification Tests

  - [ ] **NOT-001a**: Success toast display and auto-dismiss (Mock)
  - [ ] **NOT-001b**: Error toast display with retry actions (Mock)
  - [ ] **NOT-001c**: Info toast for system notifications (Mock)
  - [ ] **NOT-001d**: Toast stacking and queue management (Mock)
  - [ ] **NOT-001e**: Manual toast dismissal (Mock)
  - [ ] **NOT-001f**: Visual hierarchy with color coding (Mock)
  - [ ] **NOT-001g**: Toast notification batching for rapid events (Mock)

- [ ] **TEST-NOT-002**: Real-Time Event Notification Tests

  - [ ] **NOT-002a**: Crack event notifications with details (E2E)
  - [ ] **NOT-002b**: Agent status change notifications (E2E)
  - [ ] **NOT-002c**: Campaign completion notifications (E2E)
  - [ ] **NOT-002d**: System error notifications (E2E)
  - [ ] **NOT-002e**: Batched notification handling (E2E)

### Advanced Attack Feature Testing

- [ ] **TEST-ATT-004**: Advanced Attack Feature Tests
  - [ ] **ATT-004a**: Rule modificators and custom rules (E2E + Mock)
  - [ ] **ATT-004b**: Dynamic wordlist integration (E2E + Mock)
  - [ ] **ATT-004c**: Attack overlap detection and warnings (Mock)
  - [ ] **ATT-004d**: Ephemeral resource creation for attacks (E2E + Mock)
  - [ ] **ATT-004e**: Attack performance estimation (Mock)

### Campaign Operations Testing

- [ ] **TEST-CAM-004**: Campaign Lifecycle Operation Tests

  - [ ] **CAM-004a**: Start campaign with task generation (E2E)
  - [ ] **CAM-004b**: Pause running campaign with confirmation (E2E + Mock)
  - [ ] **CAM-004c**: Resume paused campaign (E2E)
  - [ ] **CAM-004d**: Stop campaign with impact assessment (E2E + Mock)
  - [ ] **CAM-004e**: Campaign deletion with permission checks (E2E + Mock)

- [ ] **TEST-CAM-005**: Campaign Export/Import Tests

  - [ ] **CAM-005a**: Export campaign as JSON template (E2E + Mock)
  - [ ] **CAM-005b**: Import campaign from JSON file (E2E + Mock)
  - [ ] **CAM-005c**: Campaign template validation on import (Mock)
  - [ ] **CAM-005d**: Campaign cloning functionality (E2E + Mock)
  - [ ] **CAM-005e**: Export cracked hashes from campaign (E2E + Mock)

### Resource Management Testing

- [ ] **TEST-RES-005**: Resource Upload Page Tests

  - [ ] **RES-005a**: Resource upload page loads with file drop zone (E2E + Mock)
  - [ ] **RES-005b**: Drag-and-drop file upload interface (Mock)
  - [ ] **RES-005c**: File type validation and restrictions (Mock)
  - [ ] **RES-005d**: Upload progress indicators and cancellation (Mock)
  - [ ] **RES-005e**: Large file upload handling and chunking (E2E)
  - [ ] **RES-005f**: Resource metadata input form validation (Mock)
  - [ ] **RES-005g**: Upload completion confirmation and navigation (E2E + Mock)

- [ ] **TEST-RES-006**: Resource Detail Page Tests

  - [ ] **RES-006a**: Resource detail page loads with full information (E2E + Mock)
  - [ ] **RES-006b**: Resource content preview for supported types (Mock)
  - [ ] **RES-006c**: Resource metadata editing and updates (E2E + Mock)
  - [ ] **RES-006d**: Resource usage history and tracking (Mock)
  - [ ] **RES-006e**: Resource content editing for small files (Mock)
  - [ ] **RES-006f**: Resource download and export options (E2E + Mock)
  - [ ] **RES-006g**: Resource deletion with usage validation (E2E + Mock)

### Hash List Management Testing

- [ ] **TEST-HSH-001**: Hash List Operation Tests

  - [ ] **HSH-001a**: Hash list creation from file upload (E2E + Mock)
  - [ ] **HSH-001b**: Hash list creation from text paste (Mock)
  - [ ] **HSH-001c**: Hash type auto-detection and validation (Mock)
  - [ ] **HSH-001d**: Hash list preview and statistics (Mock)
  - [ ] **HSH-001e**: Hash list deletion with cascade checks (E2E + Mock)
  - [ ] **HSH-001f**: Hash isolation from surrounding metadata (Mock)
  - [ ] **HSH-001g**: Multi-stage validation preventing malformed campaigns (Mock)

- [ ] **TEST-HSH-002**: Hash List Integration Tests

  - [ ] **HSH-002a**: Hash list selection in campaign creation (E2E + Mock)
  - [ ] **HSH-002b**: Hash list reuse across multiple campaigns (E2E)
  - [ ] **HSH-002c**: Crackable upload flow with hash detection (E2E + Mock)
  - [ ] **HSH-002d**: Hash list export in various formats (E2E + Mock)
  - [ ] **HSH-002e**: Auto-campaign creation from uploaded hashes (E2E + Mock)
  - [ ] **HSH-002f**: Progress visibility during upload and processing (Mock)
  - [ ] **HSH-002g**: Manual hash type override when auto-detection fails (Mock)

## Validation & Success Criteria

### Real-Time Features Validation

- [ ] **VALIDATE-001**: Real-time capabilities are functional
  - [ ] SSE connections establish and maintain properly
  - [ ] Real-time updates work across all major components
  - [ ] Toast notifications display correctly with proper batching
  - [ ] Connection recovery works after network interruptions
  - [ ] Project-scoped filtering prevents data leaks

### Advanced Attack Features Validation

- [ ] **VALIDATE-002**: Advanced attack features are complete
  - [ ] Rule modificators and custom rules work properly
  - [ ] Dynamic wordlist generation functions correctly
  - [ ] Attack overlap detection provides useful warnings
  - [ ] Performance estimation provides accurate predictions
  - [ ] All advanced features integrate with existing attack workflows

### Resource Management Validation

- [ ] **VALIDATE-003**: Resource management is fully functional
  - [ ] File upload handles large files and provides progress feedback
  - [ ] Resource content editing works for all supported file types
  - [ ] Resource detail pages provide comprehensive information
  - [ ] Usage tracking and validation prevent orphaned references

### Hash List Management Validation

- [ ] **VALIDATE-004**: Hash list management is complete
  - [ ] Hash detection and validation work accurately
  - [ ] Campaign integration handles all hash list scenarios
  - [ ] Export/import functionality preserves data integrity
  - [ ] Error handling provides clear guidance for resolution

## Implementation Notes

### Key Technical Patterns

- **Component Architecture**: Use idiomatic Shadcn-Svelte components for all UI elements with proper accessibility and theming
- **SvelteKit Integration**: Follow idiomatic SvelteKit 5 patterns for real-time updates, form handling, and state management
- **SSE Implementation**: Use EventSource API with `/api/v1/web/live/*` endpoints for targeted component updates
- **Attack Editor Flow**: Dictionary → searchable dropdowns, Mask → ephemeral lists, Brute Force → UI wrapper for incremental masks
- **Resource Upload**: FileDropZone from Shadcn-Svelte-Extra, presigned URLs, atomic operations, progress tracking
- **Hash Detection**: Multi-stage validation, confidence scoring, manual override capability, shadow file parsing
- **Campaign Export**: JSON schema with GUID references, versioned imports, ephemeral resource rehydration
- **Performance Optimization**: Real-time keyspace calculation, live complexity estimation, minimal data transfer

### Real-Time Implementation Strategy

Real-time features use lightweight trigger notifications rather than full data streaming:

- SSE sends minimal event data to trigger component refreshes
- Components refetch data using existing API endpoints
- Project-scoped filtering prevents data leaks between projects
- Connection management handles reconnection and cleanup

### Advanced Attack Features Context

These features enhance the attack configuration experience:

- Rule modificators provide power users with advanced capabilities
- Dynamic wordlists improve attack efficiency using project history
- Overlap detection prevents wasted computational resources
- Performance estimation helps users plan attack sequences

### Resource Management Enhancement

Complete resource management addresses identified gaps:

- Upload page provides comprehensive file handling capabilities
- Content editing enables in-place modification of resources
- Detail pages centralize all resource-related information
- Usage tracking prevents accidental deletion of active resources

## Completion Definition

This step is complete when:

1. Real-time updates work correctly across all components via SSE
2. Toast notification system provides comprehensive user feedback
3. Advanced attack features enhance configuration capabilities
4. Resource management provides complete upload, edit, and detail workflows
5. Hash list management handles all upload and campaign integration scenarios
6. All advanced features have comprehensive test coverage (Mock + E2E)
7. Performance is acceptable for all real-time and advanced features
