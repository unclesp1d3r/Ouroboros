# Implementation Plan

Convert the feature design into a series of prompts for a code-generation LLM that will implement each step in a test-driven manner. Prioritize best practices, incremental progress, and early testing, ensuring no big jumps in complexity at any stage. Make sure that each prompt builds on the previous prompts, and ends with wiring things together. There should be no hanging or orphaned code that isn't integrated into a previous step. Focus ONLY on tasks that involve writing, modifying, or testing code.

## Task List

- [x] 1. Server-Sent Events (SSE) Infrastructure Implementation

  - [x] 1.1 Create SSE event models and base infrastructure

    - [x] EventService class implemented in `app/core/services/event_service.py` with in-memory pub/sub
    - [x] EventMessage and EventListener classes with proper async handling
    - [x] Project-scoped event filtering and connection management
    - _Requirements: 1.1, 1.2, 1.6_

  - [x] 1.2 Implement SSE server endpoints

    - [x] `/api/v1/web/live/agents`, `/api/v1/web/live/campaigns`, and `/api/v1/web/live/toasts` endpoints implemented
    - [x] User authentication and connection cleanup with proper resource management
    - [x] Integration tests for SSE endpoints exist in `tests/integration/web/test_web_live_updates.py`
    - _Requirements: 1.1, 1.2, 1.6_

  - [x] 1.3 Create frontend SSE client service

    - [x] SSEService class implemented in `frontend/src/lib/services/sse.ts` with connection management
    - [x] Automatic reconnection handling with exponential backoff and auth recovery
    - [x] Connection status indicators and error handling for connection failures
    - _Requirements: 1.1, 1.2, 1.6_

  - [x] 1.4 Integrate SSE with existing components

    - [x] Dashboard components subscribe to SSE events for real-time updates
    - [x] Agent and campaign services broadcast SSE events on state changes
    - [x] Comprehensive integration tests for SSE triggers in `tests/integration/web/test_sse_campaign_triggers.py`
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

- [x] 2. Toast Notification System Implementation

  - [x] 2.1 Create backend notification service

    - [x] EventService handles notification broadcasting with batching logic
    - [x] Toast notifications triggered for crack discoveries in agent service
    - [x] Integration tests for toast notifications exist
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

  - [x] 2.2 Implement frontend toast management system

    - [x] Toast system using svelte-sonner with proper UI components
    - [x] Toast stacking and auto-dismiss functionality implemented
    - [x] Visual hierarchy with proper styling in layout
    - _Requirements: 3.6, 3.7, 3.8, 3.9, 3.10, 3.11, 3.12_

  - [x] 2.3 Integrate toast notifications with SSE events

    - [x] Toast system connected to SSE crack notification events
    - [x] Agent status change notifications and system alerts implemented
    - [x] E2E tests for toast notifications exist
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [ ] 3. Advanced Attack Configuration Features

  - [ ] 3.1 Implement rule modificator system

    - Create `RuleService` class in `app/core/services/rule_service.py` with rule generation and validation
    - Add rule modificator models and user-friendly modifier buttons that abstract hashcat complexity
    - Implement rule preview and testing capabilities with sample word transformations
    - Write unit tests for rule generation, validation, and preview functionality
    - _Requirements: 4.1, 4.6_

  - [ ] 3.2 Create dynamic wordlist generation service

    - Implement `AdvancedAttackService` class in `app/core/services/advanced_attack_service.py`
    - Add dynamic wordlist generation from project history and cracked hashes
    - Create ephemeral wordlist storage and management for attack-specific resources
    - Write unit tests for dynamic wordlist generation with mock data sources
    - _Requirements: 4.2, 4.5_

  - [ ] 3.3 Implement attack overlap detection and performance estimation

    - Add keyspace overlap analysis and duplicate work prevention alerts in `AdvancedAttackService`
    - Create `/api/v1/web/attacks/estimate` endpoint for live keyspace calculation updates
    - Implement performance impact estimation and time-to-completion predictions
    - Write unit tests for overlap detection and performance estimation algorithms
    - _Requirements: 4.3, 4.4_

  - [ ] 3.4 Integrate name-that-hash for hash type detection

    - Create `HashGuessService` class in `app/core/services/hash_guess_service.py` with name-that-hash integration
    - Add confidence-ranked hash type suggestions with manual override capability
    - Implement hash format validation and hashcat compatibility verification
    - Write integration tests for name-that-hash integration with various hash formats
    - _Requirements: 4.7, 4.8, 4.9_

  - [ ] 3.5 Enhance attack configuration UI components

    - Enhance existing `AttackEditorModal.svelte` with rule modificators and dynamic wordlist selection
    - Add attack overlap warnings and performance estimation displays to the modal
    - Implement hash type detection UI with confidence scoring and manual override
    - Write E2E tests for enhanced attack configuration workflows
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.7, 4.8, 4.9_

- [ ] 4. Campaign Lifecycle Management Implementation

  - [ ] 4.1 Create campaign lifecycle service

    - Implement `CampaignLifecycleService` class in `app/core/services/campaign_lifecycle_service.py`
    - Add start, pause, resume, and stop operations with proper state validation
    - Implement task generation, impact assessment, and confirmation workflows
    - Write unit tests for all campaign lifecycle operations with mock dependencies
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

  - [ ] 4.2 Implement campaign export/import functionality

    - Create `CampaignTemplateService` class in `app/core/services/campaign_template_service.py`
    - Add JSON template export with GUID-based resource references and version management
    - Implement template import with schema validation, version compatibility, and resource rehydration
    - Write unit tests for export/import functionality with template validation
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8_

  - [ ] 4.3 Create advanced campaign management UI

    - Build campaign toolbar with add attack, sort, bulk-select/delete, and start/stop toggle buttons
    - Implement attack reordering with drag-and-drop and keyboard accessibility support
    - Add context menu per attack row with edit, duplicate, delete, and move operations
    - Write E2E tests for campaign management UI interactions and workflows
    - _Requirements: 5.6, 5.7_

  - [x] 4.4 Integrate campaign operations with real-time updates

    - [x] Campaign lifecycle operations connected to SSE event broadcasting
    - [x] Real-time status updates for campaign state changes implemented
    - [x] Comprehensive integration tests for campaign operations with SSE event verification exist
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ] 5. Enhanced Resource Management Implementation

  - [ ] 5.1 Create enhanced resource upload system

    - Implement `EnhancedResourceService` class in `app/core/services/enhanced_resource_service.py`
    - Add chunked upload support with resume capability and progress tracking
    - Create upload session management with presigned URLs and atomic operations
    - Write unit tests for enhanced resource service with MinIO testcontainer
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.8, 7.9, 7.10, 7.11, 7.12, 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7, 12.8, 12.9, 12.10_

  - [ ] 5.2 Implement resource content editor

    - Create `ResourceEditorService` class in `app/core/services/resource_editor_service.py`
    - Add line-oriented editing with add/remove functionality and real-time validation
    - Implement type-aware editing interfaces for different resource types (masks, rules, wordlists, charsets)
    - Write unit tests for resource editor with validation and error handling
    - _Requirements: 8.2, 8.6, 12.8, 12.9_

  - [ ] 5.3 Create comprehensive resource detail pages

    - Build resource detail UI with metadata editing, content preview, and usage tracking
    - Add resource download options with presigned URLs and export functionality
    - Implement resource deletion with usage validation and cascade checks
    - Write E2E tests for resource detail pages and content management workflows
    - _Requirements: 8.1, 8.3, 8.4, 8.5, 8.7, 8.8_

  - [ ] 5.4 Enhance existing resource upload UI

    - Enhance existing resource upload page with drag-over visual feedback and multi-file support
    - Implement progress indicators and cancellation controls for uploads
    - Add real-time validation and metadata input forms
    - Write E2E tests for enhanced resource upload workflows
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7_

- [ ] 6. Hash List Management and Crackable Upload Enhancement

  - [ ] 6.1 Enhance hash list management service

    - Create `EnhancedHashListService` class in `app/core/services/enhanced_hash_list_service.py`
    - Integrate name-that-hash for intelligent hash type detection with confidence scoring
    - Add dual input modes (file upload + text paste) with hash isolation from metadata
    - Write unit tests for enhanced hash list service with name-that-hash integration
    - _Requirements: 9.1, 9.2, 9.3, 9.8, 9.9_

  - [ ] 6.2 Implement enhanced crackable upload processing

    - Create `EnhancedCrackableUploadService` class in `app/core/services/enhanced_crackable_upload_service.py`
    - Add plugin-based hash extraction with support for `.shadow`, `.pdf`, `.zip`, `.7z`, `.docx` files
    - Implement background processing pipeline with `HashUploadTask`, `RawHash`, and `UploadErrorEntry` models
    - Write integration tests for crackable upload processing with plugin architecture
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 10.8, 10.9, 10.10, 10.11, 10.12_

  - [ ] 6.3 Create hash list and upload management UI

    - Build hash list creation UI with dual input modes and intelligent type detection
    - Implement crackable upload interface with file support and progress tracking
    - Add hash list preview with statistics, confidence scoring, and manual override capability
    - Write E2E tests for hash list creation and crackable upload workflows
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 10.1, 10.2, 10.3, 10.4, 10.5, 10.6_

  - [ ] 6.4 Integrate hash management with campaign creation

    - Connect hash list selection to campaign creation workflows
    - Add auto-campaign creation from uploaded hashes with dynamic wordlist generation
    - Implement hash list reuse across multiple campaigns with proper validation
    - Write integration tests for hash list and campaign integration workflows
    - _Requirements: 9.4, 9.5, 9.6, 9.7, 10.7, 10.8, 10.9, 10.10, 10.11, 10.12_

- [ ] 7. Presigned URL Validation and Testing Infrastructure

  - [ ] 7.1 Implement presigned URL validation service

    - Create admin-only endpoint `POST /api/v1/web/agents/{id}/test_presigned` for URL validation
    - Add URL validation with HEAD requests, timeout handling, and security constraints
    - Implement proper error handling for 403/404 responses and network errors
    - Write unit tests for presigned URL validation with mock HTTP responses
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6, 13.7_

  - [ ] 7.2 Enhance testing infrastructure with MinIO testcontainers

    - Configure MinIO testcontainer integration for comprehensive storage testing
    - Add auto-creation of required buckets and test data seeding capabilities
    - Implement configurable MinIO endpoints and credentials for test environments
    - Write integration tests for all storage operations with MinIO testcontainer
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6, 14.7, 14.8_

- [ ] 8. Performance Optimization and Security Implementation

  - [x] 8.1 Implement performance optimizations

    - [x] Throttling for real-time updates implemented in SSE service to prevent UI flooding
    - [x] Connection limits and cleanup for SSE connections with proper timeout handling
    - [x] Performance considerations built into existing SSE implementation
    - _Requirements: 15.1, 15.2, 15.4, 15.5_

  - [x] 8.2 Enhance security measures

    - [x] Project-scoped event filtering implemented to prevent data leaks
    - [x] File type validation and security constraints in place
    - [x] Proper async handling patterns used throughout
    - _Requirements: 15.3, 15.6, 15.7, 15.8, 15.9, 15.10, 15.11_

- [ ] 9. Comprehensive Testing and Integration

  - [ ] 9.1 Expand unit test coverage for new services

    - Write unit tests for RuleService, AdvancedAttackService, and HashGuessService
    - Add tests for CampaignLifecycleService and CampaignTemplateService
    - Implement tests for EnhancedResourceService and ResourceEditorService
    - Ensure minimum 80% code coverage for all new components
    - _Requirements: 11.1, 11.2, 11.4, 11.6, 11.7_

  - [x] 9.2 Implement integration test coverage

    - [x] Integration tests for SSE functionality and event broadcasting exist
    - [x] Tests for real-time updates and campaign triggers implemented
    - [x] Toast notification integration tests in place
    - _Requirements: 11.1, 11.2, 11.4, 11.6, 11.7_

  - [ ] 9.3 Create end-to-end test suite for new features

    - Write E2E tests for advanced attack configuration workflows
    - Implement E2E tests for enhanced resource management features
    - Add tests for hash list management and crackable upload processing
    - Create tests for campaign lifecycle management operations
    - _Requirements: 11.1, 11.2, 11.3, 11.5, 11.6, 11.7_

  - [ ] 9.4 Final integration and validation

    - Integrate all new components and ensure proper wiring between frontend and backend
    - Validate all requirements are met with comprehensive testing
    - Perform final performance testing and optimization
    - Complete documentation and deployment preparation
    - _Requirements: All requirements validation_
