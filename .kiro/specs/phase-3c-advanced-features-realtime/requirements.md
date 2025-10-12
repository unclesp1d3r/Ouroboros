# Requirements Document

## Introduction

This specification defines the implementation of advanced features and real-time capabilities for Ouroboros's web interface. Building upon the core functionality verification, user management systems, Phase 2b Resource Management infrastructure, the completed crackable uploads pipeline, and the name-that-hash integration via HashGuessService, this feature set focuses on enhancing user experience through real-time updates via Server-Sent Events (SSE), advanced attack configuration options, comprehensive resource management workflows, and enhanced campaign operations.

The implementation emphasizes lightweight trigger notifications rather than full data streaming, project-scoped security, MinIO-based object storage with presigned URLs, plugin-based hash extraction architecture, intelligent hash type detection using the name-that-hash library, and comprehensive testing coverage with both mocked and full end-to-end tests. All resource management builds upon the existing StorageService and AttackResourceFile models established in Phase 2b, while crackable uploads utilize the HashUploadTask, UploadResourceFile, RawHash, and UploadErrorEntry models with background processing pipeline and HashGuessService for automatic hash type inference.

## Requirements

### Requirement 1: Real-Time Communication Infrastructure

**User Story:** As a Ouroboros operator, I want real-time updates on system status and campaign progress, so that I can monitor operations without manually refreshing pages.

#### Acceptance Criteria

1. WHEN the system has status updates THEN the backend SHALL provide Server-Sent Events (SSE) endpoints at `/api/v1/web/live/agents`, `/api/v1/web/live/campaigns`, and `/api/v1/web/live/toasts`
2. WHEN a user connects to SSE endpoints THEN the system SHALL filter events by project scope to prevent data leaks
3. WHEN SSE connections are established THEN the frontend SHALL implement automatic reconnection handling with exponential backoff
4. WHEN network interruptions occur THEN the system SHALL gracefully degrade to polling mode
5. WHEN SSE events are received THEN the system SHALL send lightweight trigger notifications rather than full data streaming
6. WHEN components need updates THEN they SHALL refetch data using existing API endpoints after receiving SSE triggers

### Requirement 2: Real-Time Dashboard Monitoring

**User Story:** As a security analyst, I want to see live updates of campaign progress, agent status, and task completion, so that I can respond quickly to operational changes.

#### Acceptance Criteria

1. WHEN campaigns are running THEN the dashboard SHALL display smooth progress bar animations with percentage displays and color coding (purple=running, green=completed)
2. WHEN agent status changes THEN the system SHALL update badge colors in real-time (🟢 Online → 🔴 Offline) without page refresh
3. WHEN tasks complete THEN the system SHALL show real-time updates to running/completed task counts with visual confirmation
4. WHEN system health changes THEN the dashboard SHALL display color-coded service status indicators for Redis, MinIO, and PostgreSQL
5. WHEN services fail THEN the system SHALL show alert banners with retry buttons for failed services
6. WHEN SSE connections fail THEN the system SHALL display connection status indicators and implement fallback polling

### Requirement 3: Toast Notification System

**User Story:** As a Ouroboros user, I want informative notifications about system events and crack discoveries, so that I can stay informed without constantly monitoring the interface.

#### Acceptance Criteria

1. WHEN hashes are cracked THEN the system SHALL display toast notifications with crack details (plaintext, attack used, timestamp, agent name)
2. WHEN agents connect or disconnect THEN the system SHALL show status change notifications with agent names and appropriate icons
3. WHEN campaigns complete or fail THEN the system SHALL display prominent completion notifications with campaign name, completion time, and crack count
4. WHEN system errors occur THEN the system SHALL show error notifications with actionable information and severity-appropriate styling
5. WHEN multiple rapid events occur THEN the system SHALL batch notifications to prevent spam (e.g., "5 new cracks" instead of 5 individual toasts)
6. WHEN toasts are displayed THEN they SHALL auto-dismiss for success notifications, remain persistent for errors, and support manual dismissal
7. WHEN multiple toasts are active THEN they SHALL stack vertically with proper spacing and queue management

### Requirement 4: Advanced Attack Configuration

**User Story:** As a password cracking specialist, I want advanced attack configuration options including rule modificators, dynamic wordlists, hash type detection, and overlap detection, so that I can optimize cracking efficiency.

#### Acceptance Criteria

1. WHEN configuring dictionary attacks THEN the system SHALL provide user-friendly modifier buttons (+Change Case, +Substitute Characters) that abstract hashcat rule complexity
2. WHEN creating attacks THEN the system SHALL generate dynamic wordlists from project history and previous passwords
3. WHEN configuring multiple attacks THEN the system SHALL detect keyspace overlap and provide warnings about duplicate work
4. WHEN estimating attack performance THEN the system SHALL provide live keyspace calculation updates via `/api/v1/web/attacks/estimate`
5. WHEN creating ephemeral resources THEN the system SHALL store wordlists only on Attack objects without creating permanent resources
6. WHEN advanced users need control THEN the system SHALL allow direct rule file selection and custom rule creation
7. WHEN analyzing hash types THEN the system SHALL use `name-that-hash` library integration via `HashGuessService` for automatic hash type detection
8. WHEN displaying hash analysis THEN the system SHALL provide confidence-ranked suggestions with manual override capability
9. WHEN validating hash formats THEN the system SHALL handle common formats (shadow, NTLM, secretsdump output) with appropriate parsing

### Requirement 5: Campaign Lifecycle Management

**User Story:** As a campaign manager, I want comprehensive control over campaign operations including start/pause/resume/stop functionality and export/import capabilities, so that I can manage complex cracking operations effectively.

#### Acceptance Criteria

1. WHEN starting campaigns THEN the system SHALL generate tasks and validate all prerequisites before execution
2. WHEN pausing campaigns THEN the system SHALL require confirmation and safely halt operations without data loss
3. WHEN resuming campaigns THEN the system SHALL restore previous state and continue from the last checkpoint
4. WHEN stopping campaigns THEN the system SHALL provide impact assessment and confirmation dialogs
5. WHEN deleting campaigns THEN the system SHALL perform permission checks and cascade validation
6. WHEN managing attacks within campaigns THEN the system SHALL support drag-and-drop reordering with keyboard accessibility
7. WHEN bulk operations are needed THEN the system SHALL provide toolbar buttons for add attack, sort, bulk-select/delete, and start/stop toggle

### Requirement 6: Campaign Export and Import

**User Story:** As a security team lead, I want to export and import campaign configurations as templates, so that I can standardize attack strategies across different projects.

#### Acceptance Criteria

1. WHEN exporting campaigns THEN the system SHALL create JSON templates with GUID-based resource references
2. WHEN importing campaigns THEN the system SHALL validate schema versions and rehydrate ephemeral resources
3. WHEN importing templates THEN the system SHALL handle version compatibility and provide clear error messages for incompatible formats
4. WHEN cloning campaigns THEN the system SHALL create complete copies with new GUIDs while preserving configuration
5. WHEN exporting results THEN the system SHALL allow export of cracked hashes in various formats
6. WHEN validating imports THEN the system SHALL ensure data integrity and prevent malformed campaign creation

### Requirement 7: Comprehensive Resource Management

**User Story:** As a resource administrator, I want complete file upload, editing, and management capabilities using MinIO object storage with presigned URLs, so that I can efficiently manage wordlists, rules, masks, and charsets with proper deduplication and validation.

#### Acceptance Criteria

01. WHEN uploading resources THEN the system SHALL provide a prominent drop zone with drag-over visual feedback and traditional file picker alternatives
02. WHEN files are dragged over THEN the system SHALL show visual highlights and support multiple file selection with preview
03. WHEN validating uploads THEN the system SHALL perform immediate client-side file type checking with clear error messages for supported types (wordlists, rule files, masks, charsets)
04. WHEN uploading large files THEN the system SHALL implement chunked upload with resume capability and accurate progress tracking
05. WHEN uploads complete THEN the system SHALL provide success confirmation with navigation options (view resource, upload more, return to list)
06. WHEN editing resources THEN the system SHALL support inline editing for small files (\<1MB and \<5,000 lines) with type-aware interfaces
07. WHEN managing metadata THEN the system SHALL provide comprehensive forms with real-time validation and batch operations
08. WHEN registering uploads THEN the system SHALL create database records with presigned PUT URLs that expire after 15 minutes
09. WHEN files are uploaded THEN the system SHALL use MD5 or SHA-256 hashing to detect duplicates and prevent multiple uploads of identical files
10. WHEN duplicate files are detected THEN the system SHALL allow users to link to existing resources rather than reuploading
11. WHEN upload verification occurs THEN the system SHALL compute hash, byte size, and line count in background threads
12. WHEN resources are not uploaded within timeout THEN the system SHALL automatically delete orphaned database records

### Requirement 8: Resource Detail and Content Management

**User Story:** As a resource user, I want detailed information about resources including content preview, usage tracking, and editing capabilities with proper access control, so that I can effectively utilize and maintain resource libraries.

#### Acceptance Criteria

1. WHEN viewing resource details THEN the system SHALL display comprehensive information including metadata, usage history, and content preview using presigned download URLs
2. WHEN editing resource content THEN the system SHALL provide line-oriented editing with add/remove functionality and real-time validation for files under size limits
3. WHEN previewing content THEN the system SHALL support different modes for mask, rule, wordlist, and charset files with first few lines preview
4. WHEN tracking usage THEN the system SHALL prevent deletion of resources that are actively referenced by campaigns or attacks
5. WHEN downloading resources THEN the system SHALL provide presigned download URLs that expire after 15 minutes
6. WHEN validating edits THEN the system SHALL provide real-time feedback from 422 error response models with detailed error messages
7. WHEN managing access THEN the system SHALL enforce role-based permissions (Admin: full access, Power User: project resources, User: non-sensitive only)
8. WHEN refreshing metadata THEN the system SHALL allow manual re-validation of size, checksum, and line count
9. WHEN auditing resources THEN the system SHALL detect orphaned MinIO objects without matching database records

### Requirement 9: Hash List Management System

**User Story:** As a hash analyst, I want comprehensive hash list management with intelligent detection using name-that-hash integration, dual input modes, and campaign integration, so that I can efficiently process and organize hash cracking targets.

#### Acceptance Criteria

1. WHEN creating hash lists THEN the system SHALL support both file upload and text paste input modes with intelligent hash type detection via `name-that-hash`
2. WHEN detecting hash types THEN the system SHALL provide confidence scoring with manual override capability for incorrect detections using `HashGuessService`
3. WHEN processing uploads THEN the system SHALL isolate hashes from surrounding metadata (shadow files, NTLM pairs) and provide preview with statistics
4. WHEN integrating with campaigns THEN the system SHALL support hash list reuse across multiple campaigns and streamlined crackable upload workflows
5. WHEN exporting hash lists THEN the system SHALL provide various format options and auto-campaign creation with dynamic wordlist generation
6. WHEN validating operations THEN the system SHALL implement multi-stage validation to prevent malformed campaign creation
7. WHEN deleting hash lists THEN the system SHALL perform cascade checks to prevent orphaned references
8. WHEN analyzing pasted hash text THEN the system SHALL use `name-that-hash` native Python API (not subprocess) for hash type inference
9. WHEN displaying hash analysis results THEN the system SHALL wrap `name-that-hash` responses in Ouroboros-style confidence-ranked outputs

### Requirement 10: Crackable Upload Processing

**User Story:** As a security analyst, I want automated hash extraction and campaign generation from various file formats using a plugin-based processing pipeline, so that I can quickly process complex files without manual hash extraction.

#### Acceptance Criteria

01. WHEN uploading crackable files THEN the system SHALL support `.shadow`, `.pdf`, `.zip`, `.7z`, `.docx` files with configurable size limits (default 100MB)
02. WHEN processing uploads THEN the system SHALL create `HashUploadTask` models with fields: `id`, `user_id`, `filename`, `status`, `started_at`, `finished_at`, `error_count`, `hash_list_id`, `campaign_id`
03. WHEN storing uploaded content THEN the system SHALL use `UploadResourceFile` models with presigned URLs for file storage or direct content storage for text blobs
04. WHEN extracting hashes THEN the system SHALL use plugin-based architecture with `extract_hashes(path: Path) -> list[RawHash]` interface
05. WHEN processing files THEN the system SHALL create `RawHash` models with fields: `id`, `hash`, `hash_type`, `username`, `metadata`, `line_number`, `upload_error_entry_id`
06. WHEN parsing fails THEN the system SHALL create `UploadErrorEntry` models with fields: `id`, `upload_id`, `line_number`, `raw_line`, `error_message`
07. WHEN creating campaigns THEN the system SHALL generate `HashList` and `Campaign` models with `is_unavailable = True` during processing
08. WHEN processing completes THEN the system SHALL parse `RawHash` objects into `HashItem` objects and set `is_unavailable = False`
09. WHEN hash type detection occurs THEN the system SHALL use `HashGuessService` with `name-that-hash` library integration and confidence thresholds before insertion
10. WHEN background processing runs THEN the system SHALL execute complete pipeline: download → extract → parse → create campaign → update status
11. WHEN errors occur THEN the system SHALL log failed lines, set appropriate status (`failed`, `partial_failure`, `completed`), and provide paginated error listings
12. WHEN campaigns are unavailable THEN the system SHALL exclude them from normal campaign and hash list endpoints until processing completes

### Requirement 11: Comprehensive Testing Coverage

**User Story:** As a quality assurance engineer, I want comprehensive test coverage for all advanced features using both mocked and full end-to-end testing approaches, so that I can ensure reliability and prevent regressions.

#### Acceptance Criteria

1. WHEN implementing features THEN all user-facing functionality SHALL have both mocked E2E tests (fast, no backend) and full E2E tests (complete integration)
2. WHEN running tests THEN mocked tests SHALL execute via `just test-frontend` and full E2E tests SHALL execute via `just test-e2e`
3. WHEN testing real-time features THEN tests SHALL verify SSE connections, toast notifications, and live updates across all components
4. WHEN testing advanced features THEN tests SHALL cover attack configuration, campaign operations, resource management, and hash list functionality
5. WHEN validating UI behavior THEN tests SHALL confirm responsive design, offline capability, and proper error handling
6. WHEN ensuring quality THEN all forms SHALL be validated using OpenAPI spec and Zod objects on both client and server sides
7. WHEN maintaining consistency THEN tests SHALL use existing test utilities and follow established naming conventions

### Requirement 12: Resource Lifecycle and Storage Integration

**User Story:** As a system architect, I want proper resource lifecycle management with MinIO integration and background processing, so that file uploads are reliable and storage remains consistent.

#### Acceptance Criteria

01. WHEN registering uploads THEN the system SHALL create database records with `status = pending` and return presigned PUT URLs with 15-minute expiration
02. WHEN clients upload files THEN they SHALL use presigned URLs to upload directly to MinIO with key format `resources/{resource_id}/{filename}`
03. WHEN upload verification occurs THEN the system SHALL trigger background tasks to compute hash, byte size, and line count using `asyncio.to_thread()`
04. WHEN files are successfully processed THEN the system SHALL update database records with `status = active` and `is_uploaded = true`
05. WHEN uploads fail or timeout THEN the system SHALL automatically delete orphaned database records after configurable timeout (default 15 minutes)
06. WHEN linking resources to attacks THEN the system SHALL use database ID references with GUID-based resource association
07. WHEN detecting duplicates THEN the system SHALL use MD5 or SHA-256 content hashing to prevent duplicate uploads and offer existing resource linking
08. WHEN auditing storage THEN the system SHALL detect and report orphaned MinIO objects without matching database records
09. WHEN managing resource types THEN the system SHALL support enum values: `[word_list, rule_list, mask_list, charset, dynamic_word_list]`
10. WHEN processing metadata THEN the system SHALL store comprehensive file information including `name`, `resource_type`, `guid`, `bucket`, `key`, `size_bytes`, `line_count`, `checksum`, `sensitivity`, `project_id`

### Requirement 13: Presigned URL Validation and Testing

**User Story:** As a system administrator, I want to validate presigned URLs for diagnostic purposes, so that I can troubleshoot resource accessibility issues and ensure agent download reliability.

#### Acceptance Criteria

1. WHEN testing presigned URLs THEN the system SHALL provide an admin-only endpoint `POST /api/v1/web/agents/{id}/test_presigned` for URL validation
2. WHEN validating URLs THEN the system SHALL perform HEAD requests with 3-second timeout and return boolean success status
3. WHEN handling URL validation THEN the system SHALL only accept HTTP/HTTPS schemes and disallow file:// or other protocols
4. WHEN validation fails THEN the system SHALL treat 403/404 responses and network errors as invalid URLs
5. WHEN processing validation requests THEN the system SHALL not follow redirects for security
6. WHEN displaying results THEN the UI SHALL show green check or red ❌ indicators next to resource links
7. WHEN validating input THEN the system SHALL use Pydantic validation and return 422 for malformed URLs

### Requirement 14: Testing Infrastructure and Coverage

**User Story:** As a quality assurance engineer, I want comprehensive testing infrastructure including MinIO testcontainers, so that I can ensure reliable integration testing of all storage-related functionality.

#### Acceptance Criteria

1. WHEN running integration tests THEN the system SHALL use `MinioContainer` from `testcontainers.minio` for isolated test environments
2. WHEN setting up test fixtures THEN the system SHALL auto-create required buckets (`wordlists`, `rules`, `masks`, `charsets`)
3. WHEN configuring test environments THEN the system SHALL support overrideable MinIO endpoint, access keys, and bucket prefix configuration
4. WHEN running CI tests THEN the system SHALL ensure MinIO container fixtures work in GitHub Actions with proper port exposure and health checks
5. WHEN testing upload flows THEN the system SHALL validate presign generation, database row creation, and file accessibility
6. WHEN testing resource operations THEN the system SHALL cover upload, metadata refresh, linking, ephemeral resource scenarios, and crackable upload processing
7. WHEN seeding test data THEN the system SHALL optionally provide test wordlists or rule files for integration coverage
8. WHEN executing test suites THEN at least one complete upload + presign + fetch test SHALL be included in `just ci-check`

### Requirement 15: Performance and Security

**User Story:** As a system administrator, I want advanced features to maintain acceptable performance while ensuring security through project-scoped access and proper error handling, so that the system remains reliable under load.

#### Acceptance Criteria

01. WHEN providing real-time updates THEN the system SHALL throttle updates to prevent UI flooding and maintain responsive performance
02. WHEN handling SSE connections THEN the system SHALL implement proper cleanup, timeout handling, and connection limits
03. WHEN filtering events THEN the system SHALL ensure project-scoped filtering prevents data leaks between projects
04. WHEN processing large files THEN the system SHALL implement chunking, progress tracking, and resume capabilities without blocking the UI
05. WHEN performing keyspace calculations THEN the system SHALL provide live estimation without impacting overall system performance
06. WHEN handling errors THEN the system SHALL provide clear, actionable error messages without exposing sensitive system information
07. WHEN managing resources THEN the system SHALL implement atomic operations to prevent database/storage inconsistencies
08. WHEN using MinIO operations THEN the system SHALL execute all blocking operations using `asyncio.to_thread()` within FastAPI
09. WHEN managing presigned URLs THEN the system SHALL ensure all URLs expire after 15 minutes for security
10. WHEN validating file types THEN the system SHALL ensure uploaded files match declared resource_type to prevent malicious uploads
11. WHEN cleaning up failed uploads THEN the system SHALL automatically delete database records for files not uploaded within timeout period
