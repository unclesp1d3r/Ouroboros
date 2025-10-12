# Requirements Document

## Introduction

The Control API v1 (`/api/v1/control/*`) provides programmatic access to all major Ouroboros backend operations for command-line tools, automation scripts, and third-party integrations. This API powers the `csadmin` command-line interface and enables machine-readable workflows for campaigns, attacks, agents, hash lists, tasks, and system statistics. Unlike the Web UI API which is designed for human interaction, the Control API is optimized for structured, automated workflows with consistent JSON responses and RFC9457-compliant error handling.

The Control API serves as a thin wrapper around existing service layer functions, maximizing code reuse while providing API key-based authentication, project scoping, and offset-based pagination suitable for programmatic access. All endpoints enforce the same business logic and security constraints as the Web UI API, ensuring consistent behavior across interfaces.

## Requirements

### Requirement 1: API Key Authentication and Authorization

**User Story:** As a system administrator, I want secure API key-based authentication for programmatic access, so that automated tools can access Ouroboros without interactive login sessions.

#### Acceptance Criteria

1. WHEN a user account is created THEN the system SHALL generate a unique API key with format `cst_<user_id>_<random_string>`
2. WHEN API requests are made THEN the system SHALL require `Authorization: Bearer <api_key>` header for all endpoints
3. WHEN API keys are validated THEN the system SHALL verify format, existence, and user active status
4. WHEN API key authentication fails THEN the system SHALL return RFC9457-compliant error responses with appropriate status codes
5. WHEN users request API key rotation THEN the system SHALL generate new keys and invalidate old ones immediately
6. WHEN API key information is requested THEN the system SHALL return key metadata without exposing the actual key value
7. WHEN project access is checked THEN the system SHALL enforce the same project scoping rules as the Web UI API

### Requirement 2: RFC9457-Compliant Error Handling

**User Story:** As a developer integrating with Ouroboros, I want standardized, machine-parseable error responses, so that I can programmatically handle different error conditions.

#### Acceptance Criteria

1. WHEN errors occur THEN the system SHALL return RFC9457 Problem Details format with type, title, status, detail, and instance fields
2. WHEN domain-specific errors occur THEN the system SHALL use custom error types like "campaign-not-found" or "invalid-attack-config"
3. WHEN validation errors occur THEN the system SHALL provide structured error details with field-specific guidance
4. WHEN authentication fails THEN the system SHALL return 401 status with appropriate problem type
5. WHEN authorization fails THEN the system SHALL return 403 status with project access denied details
6. WHEN resources are not found THEN the system SHALL return 404 status with resource-specific error types
7. WHEN server errors occur THEN the system SHALL return 500 status without exposing internal implementation details

### Requirement 3: Project Scoping and Multi-Tenant Access Control

**User Story:** As a system administrator, I want project-based access control for the Control API, so that users can only access resources from their assigned projects.

#### Acceptance Criteria

1. WHEN users access list endpoints THEN the system SHALL filter results to only include resources from accessible projects
2. WHEN users access detail endpoints THEN the system SHALL verify project access before returning resource data
3. WHEN project access is denied THEN the system SHALL return appropriate 403 error responses with project access denied details
4. WHEN users have multiple project assignments THEN the system SHALL include resources from all accessible projects in list responses
5. WHEN project filtering is applied THEN the system SHALL use the same access control logic as the Web UI API
6. WHEN admin users access resources THEN the system SHALL respect admin privileges while maintaining project scoping
7. WHEN project access utilities are used THEN the system SHALL cache project associations for performance optimization

### Requirement 4: Offset-Based Pagination and Filtering

**User Story:** As a developer building automation tools, I want consistent offset-based pagination, so that I can efficiently process large datasets programmatically.

#### Acceptance Criteria

1. WHEN list endpoints are called THEN the system SHALL support `offset` and `limit` query parameters with sensible defaults
2. WHEN pagination is applied THEN the system SHALL return total count, current offset, and limit in response metadata
3. WHEN pagination conversion is needed THEN the system SHALL convert between offset-based and page-based pagination for service layer compatibility
4. WHEN large result sets are requested THEN the system SHALL enforce maximum limit constraints to prevent resource exhaustion
5. WHEN filtering is applied THEN the system SHALL support common filters like project_id, name, status, and date ranges
6. WHEN search functionality is needed THEN the system SHALL provide text-based search across relevant fields
7. WHEN pagination state is maintained THEN the system SHALL provide consistent ordering to prevent duplicate or missing results

### Requirement 5: System Health and Statistics Monitoring

**User Story:** As a system administrator, I want programmatic access to system health and statistics, so that I can monitor Ouroboros status and performance through automated tools.

#### Acceptance Criteria

1. WHEN system status is requested THEN the system SHALL return health status for database, Redis, MinIO, and core services
2. WHEN system version is requested THEN the system SHALL return API version, build information, and component versions
3. WHEN queue status is requested THEN the system SHALL return task queue depths, processing rates, and worker status
4. WHEN system statistics are requested THEN the system SHALL return dashboard summary data including campaign counts, agent status, and performance metrics
5. WHEN health checks are performed THEN the system SHALL include latency measurements and error rates
6. WHEN cached data is used THEN the system SHALL implement appropriate TTL values and cache invalidation strategies
7. WHEN monitoring data is requested THEN the system SHALL support time-series data for performance trending

### Requirement 6: User and Project Management

**User Story:** As a system administrator, I want comprehensive user and project management through the Control API, so that I can automate account provisioning and project assignments.

#### Acceptance Criteria

1. WHEN users are listed THEN the system SHALL return paginated user data with filtering and search capabilities
2. WHEN users are created THEN the system SHALL validate required fields, generate API keys, and return structured validation errors
3. WHEN users are updated THEN the system SHALL support profile changes, status updates, and role modifications
4. WHEN users are deleted THEN the system SHALL perform soft deletion and handle referential integrity
5. WHEN projects are managed THEN the system SHALL support creation, updates, user assignments, and deletion with validation
6. WHEN project users are listed THEN the system SHALL return user associations with role information
7. WHEN user-project assignments are modified THEN the system SHALL validate permissions and update associations atomically

### Requirement 7: Hash List and Hash Item Management

**User Story:** As a security analyst, I want programmatic hash list management with import/export capabilities, so that I can automate hash processing workflows.

#### Acceptance Criteria

1. WHEN hash lists are managed THEN the system SHALL support creation, updates, deletion, and listing with project scoping
2. WHEN hash lists are imported THEN the system SHALL support file uploads, format detection, and batch processing
3. WHEN hash lists are exported THEN the system SHALL support multiple formats including plaintext, potfile, and CSV
4. WHEN hash items are accessed THEN the system SHALL provide filtering by crack status, hash type, and metadata fields
5. WHEN hash validation is performed THEN the system SHALL verify format correctness and detect hash types
6. WHEN large hash lists are processed THEN the system SHALL implement streaming processing and progress tracking
7. WHEN hash metadata is managed THEN the system SHALL support structured metadata storage and retrieval

### Requirement 8: Hash Type Detection and Validation

**User Story:** As a security analyst, I want automated hash type detection and validation, so that I can programmatically identify and validate hash formats.

#### Acceptance Criteria

1. WHEN hash type detection is requested THEN the system SHALL analyze hash samples and return confidence scores
2. WHEN hash validation is performed THEN the system SHALL verify format correctness for specific hash types
3. WHEN supported hash types are listed THEN the system SHALL return comprehensive hash type information with capabilities
4. WHEN detection algorithms are used THEN the system SHALL leverage existing hash_guess_service functionality
5. WHEN multiple hash samples are provided THEN the system SHALL analyze patterns and provide consensus recommendations
6. WHEN hash type confidence is low THEN the system SHALL return multiple possibilities with relative confidence scores
7. WHEN validation errors occur THEN the system SHALL provide specific guidance on format requirements

### Requirement 9: Resource File Management

**User Story:** As a security analyst, I want comprehensive resource file management through the Control API, so that I can automate wordlist, rule, and mask file operations.

#### Acceptance Criteria

1. WHEN resources are listed THEN the system SHALL return filterable results by type, project scope, and modification date
2. WHEN resources are uploaded THEN the system SHALL detect resource type, validate content, and store in S3-compatible storage
3. WHEN resource content is accessed THEN the system SHALL provide streaming access for large files
4. WHEN resource metadata is updated THEN the system SHALL support name, description, and visibility changes
5. WHEN resources are deleted THEN the system SHALL check for attack linkage and prevent deletion if in use
6. WHEN resource lines are managed THEN the system SHALL support line-level operations for eligible resource types
7. WHEN resource assignments are made THEN the system SHALL validate compatibility and update associations

### Requirement 10: Campaign Management and Lifecycle Control

**User Story:** As a security analyst, I want complete campaign management through the Control API, so that I can automate campaign creation, monitoring, and control workflows.

#### Acceptance Criteria

1. WHEN campaigns are listed THEN the system SHALL return paginated results with filtering, search, and progress metrics
2. WHEN campaigns are created THEN the system SHALL validate hash list assignment, attack configurations, and resource availability
3. WHEN campaign details are accessed THEN the system SHALL return comprehensive information including attacks, tasks, and metrics
4. WHEN campaign lifecycle is controlled THEN the system SHALL support start, stop, pause, and relaunch operations with state validation
5. WHEN campaign progress is requested THEN the system SHALL return real-time metrics including completion percentage and performance data
6. WHEN campaigns are updated THEN the system SHALL validate state transitions and enforce business rules
7. WHEN campaign templates are used THEN the system SHALL support export/import functionality with resource reference resolution

### Requirement 11: Attack Management and Configuration

**User Story:** As a security analyst, I want sophisticated attack configuration and management through the Control API, so that I can programmatically create and optimize cracking strategies.

#### Acceptance Criteria

1. WHEN attacks are created THEN the system SHALL support all hashcat attack modes with mode-specific validation
2. WHEN attack configurations are validated THEN the system SHALL return keyspace estimates, complexity scores, and validation errors
3. WHEN attacks are updated THEN the system SHALL validate state constraints and warn about lifecycle impacts
4. WHEN attack performance is requested THEN the system SHALL return detailed performance metrics and optimization suggestions
5. WHEN attacks are duplicated THEN the system SHALL create copies with appropriate modifications and validation
6. WHEN attack ordering is changed THEN the system SHALL support reordering within campaigns with validation
7. WHEN attack templates are used THEN the system SHALL support export/import with complete configuration preservation

### Requirement 12: Agent Management and Monitoring

**User Story:** As a system administrator, I want comprehensive agent management through the Control API, so that I can automate agent configuration and monitoring workflows.

#### Acceptance Criteria

1. WHEN agents are listed THEN the system SHALL return paginated data with status, performance metrics, and filtering capabilities
2. WHEN agent details are accessed THEN the system SHALL provide comprehensive information including hardware, performance, and capabilities
3. WHEN agent configuration is updated THEN the system SHALL support settings changes, project assignments, and hardware configuration
4. WHEN agent performance is monitored THEN the system SHALL provide time-series data and performance metrics
5. WHEN agent errors are accessed THEN the system SHALL return structured error logs with severity and context
6. WHEN agent benchmarks are triggered THEN the system SHALL initiate benchmark runs and return capability data
7. WHEN agent hardware is managed THEN the system SHALL support device configuration and temperature monitoring

### Requirement 13: Task Management and Monitoring

**User Story:** As a system administrator, I want detailed task management capabilities through the Control API, so that I can monitor and control individual cracking tasks programmatically.

#### Acceptance Criteria

1. WHEN tasks are listed THEN the system SHALL return paginated results with filtering by status, agent, campaign, and date ranges
2. WHEN task details are accessed THEN the system SHALL provide comprehensive task information including progress, performance, and logs
3. WHEN task lifecycle is controlled THEN the system SHALL support requeue, cancel, and restart operations with state validation
4. WHEN task performance is monitored THEN the system SHALL return real-time metrics including guess rates and progress
5. WHEN task logs are accessed THEN the system SHALL provide structured log data with filtering and search capabilities
6. WHEN task status is requested THEN the system SHALL return current state, agent assignment, and execution context
7. WHEN task errors occur THEN the system SHALL provide detailed error information and recovery suggestions

### Requirement 14: Template Import/Export and Configuration Management

**User Story:** As a security analyst, I want comprehensive template management through the Control API, so that I can automate configuration sharing and reuse workflows.

#### Acceptance Criteria

1. WHEN campaign templates are exported THEN the system SHALL generate complete JSON configurations with resource references
2. WHEN attack templates are exported THEN the system SHALL preserve all configuration data and ephemeral content
3. WHEN templates are imported THEN the system SHALL validate schema correctness and resolve resource references
4. WHEN resource references cannot be resolved THEN the system SHALL provide fallback options and error guidance
5. WHEN ephemeral resources are included THEN the system SHALL serialize inline content for complete portability
6. WHEN template validation fails THEN the system SHALL return structured error messages with specific field issues
7. WHEN templates are applied THEN the system SHALL support customization and validation before final creation

### Requirement 15: Live Monitoring and Real-Time Updates

**User Story:** As a developer building monitoring tools, I want access to real-time status updates through the Control API, so that I can build responsive monitoring dashboards.

#### Acceptance Criteria

1. WHEN live campaign status is requested THEN the system SHALL provide JSON-formatted status updates with progress and metrics
2. WHEN live agent status is requested THEN the system SHALL return real-time agent performance and connectivity data
3. WHEN live task status is requested THEN the system SHALL provide current task execution status and progress updates
4. WHEN live system status is requested THEN the system SHALL return system health metrics and component status
5. WHEN status updates are provided THEN the system SHALL use efficient polling mechanisms with appropriate update frequencies
6. WHEN monitoring data is cached THEN the system SHALL implement appropriate TTL values and cache invalidation
7. WHEN real-time data is requested THEN the system SHALL provide consistent formatting suitable for programmatic consumption

### Requirement 16: Performance and Scalability

**User Story:** As a system administrator, I want the Control API to perform efficiently under automated load, so that multiple tools and scripts can operate simultaneously without degradation.

#### Acceptance Criteria

1. WHEN database queries are executed THEN the system SHALL use appropriate indexes, pagination, and query optimization
2. WHEN large datasets are processed THEN the system SHALL implement streaming responses and memory-efficient processing
3. WHEN expensive operations are performed THEN the system SHALL use caching with configurable TTL values
4. WHEN concurrent requests are made THEN the system SHALL handle them efficiently using async patterns
5. WHEN rate limiting is applied THEN the system SHALL protect against abuse while allowing normal automated operation
6. WHEN background processing is needed THEN the system SHALL use appropriate task queues and avoid blocking operations
7. WHEN resource usage is monitored THEN the system SHALL provide performance metrics and optimization guidance

### Requirement 17: Service Layer Reuse and Consistency

**User Story:** As a developer maintaining Ouroboros, I want the Control API to maximize reuse of existing service layer functions, so that business logic remains consistent across all interfaces.

#### Acceptance Criteria

1. WHEN Control API endpoints are implemented THEN the system SHALL reuse existing service layer functions from Web UI API
2. WHEN business logic is executed THEN the system SHALL maintain consistency with Web UI API behavior and validation rules
3. WHEN data transformations are needed THEN the system SHALL use existing Pydantic schemas and conversion utilities
4. WHEN authentication is performed THEN the system SHALL leverage existing authentication patterns with API key adaptation
5. WHEN project scoping is applied THEN the system SHALL use the same access control utilities as other APIs
6. WHEN pagination is implemented THEN the system SHALL convert between offset-based and page-based pagination seamlessly
7. WHEN error handling is performed THEN the system SHALL translate service layer exceptions to appropriate RFC9457 responses
