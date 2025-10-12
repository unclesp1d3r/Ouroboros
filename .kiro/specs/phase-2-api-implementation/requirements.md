# Requirements Document

## Introduction

The Phase 2 API Implementation represents the complete backend API architecture for Ouroboros, providing comprehensive REST interfaces for all system interactions. This phase encompasses three distinct API surfaces: the Agent API for distributed hashcat instances, the Web UI API for the SvelteKit frontend, and the Control API for CLI/automation tools. Together, these APIs enable secure, scalable, and efficient coordination of distributed password cracking operations across multiple machines and user interfaces.

Phase 2 builds upon the core infrastructure established in Phase 1, implementing the service layer architecture, authentication systems, and business logic required to support the full Ouroboros feature set. The implementation prioritizes backward compatibility with existing v1 agent integrations while introducing modern FastAPI patterns, comprehensive validation, and real-time capabilities.

## Requirements

### Requirement 1: Agent API Legacy Compatibility and Task Distribution

**User Story:** As a Ouroboros agent running legacy v1 software, I want seamless compatibility with the new FastAPI backend, so that I can continue operating without requiring immediate upgrades.

#### Acceptance Criteria

1. WHEN legacy v1 agents make requests to `/api/v1/client/*` endpoints THEN the system SHALL maintain exact compatibility with `contracts/v1_api_swagger.json` specification
2. WHEN agents register with the system THEN the system SHALL generate bearer tokens in format `csa_<agent_id>_<random_string>` and store agent capabilities
3. WHEN agents request task assignments THEN the system SHALL distribute keyspace chunks efficiently across available agents with appropriate load balancing
4. WHEN agents submit progress updates THEN the system SHALL track real-time task execution status and update campaign metrics
5. WHEN agents submit crack results THEN the system SHALL validate hash formats, prevent duplicates, and update hash list completion status
6. WHEN agents access attack resources THEN the system SHALL provide presigned S3 URLs with time-limited access and hash verification requirements
7. WHEN agents send heartbeats THEN the system SHALL update connectivity status and enforce rate limiting to prevent system overload

### Requirement 2: Web UI API Comprehensive Frontend Support

**User Story:** As a security analyst using the Ouroboros web interface, I want a rich, responsive API that supports all frontend functionality, so that I can efficiently manage campaigns, attacks, and resources through an intuitive interface.

#### Acceptance Criteria

1. WHEN users authenticate through the web interface THEN the system SHALL provide JWT-based authentication with project context switching and role-based access control
2. WHEN users manage campaigns THEN the system SHALL support complete CRUD operations with attack orchestration, lifecycle controls, and real-time progress monitoring
3. WHEN users configure attacks THEN the system SHALL provide sophisticated attack configuration with keyspace estimation, validation, and template support for all hashcat modes
4. WHEN users manage hash lists THEN the system SHALL support secure import/export with automatic hash type detection and project-level isolation
5. WHEN users monitor agents THEN the system SHALL provide comprehensive agent status, performance metrics, hardware configuration, and error reporting
6. WHEN users manage resources THEN the system SHALL support file upload/download with inline editing capabilities and metadata management
7. WHEN users need real-time updates THEN the system SHALL provide Server-Sent Events (SSE) for live campaign progress, agent status, and crack result notifications

### Requirement 3: Control API Programmatic Access and Automation

**User Story:** As a system administrator building automation tools, I want a comprehensive programmatic API with consistent responses and error handling, so that I can integrate Ouroboros into automated workflows and monitoring systems.

#### Acceptance Criteria

1. WHEN automation tools authenticate THEN the system SHALL use API key-based authentication with format `cst_<user_id>_<random_string>` and project scoping
2. WHEN API errors occur THEN the system SHALL return RFC9457-compliant Problem Details responses with structured error information
3. WHEN tools request data THEN the system SHALL provide offset-based pagination suitable for programmatic processing with consistent filtering and search capabilities
4. WHEN tools manage campaigns THEN the system SHALL support complete lifecycle management including creation, monitoring, control, and template import/export
5. WHEN tools manage agents THEN the system SHALL provide comprehensive agent configuration, monitoring, and benchmark capabilities
6. WHEN tools access system health THEN the system SHALL return detailed status information for all components including database, Redis, MinIO, and task queues
7. WHEN tools perform bulk operations THEN the system SHALL support efficient batch processing with appropriate performance optimization

### Requirement 4: Hash Analysis and Type Detection Service

**User Story:** As a security analyst working with unknown hash formats, I want intelligent hash type detection and analysis, so that I can quickly identify hash types and configure appropriate attacks.

#### Acceptance Criteria

1. WHEN hash samples are submitted for analysis THEN the system SHALL use Name-That-Hash library to identify likely hash types with confidence scores
2. WHEN hash type detection is performed THEN the system SHALL return ranked suggestions compatible with hashcat mode numbers
3. WHEN multiline hash inputs are processed THEN the system SHALL handle common formats like `/etc/shadow`, `secretsdump` output, and Cisco IOS configurations
4. WHEN hash formatting is inconsistent THEN the system SHALL normalize formatting by stripping usernames, delimiters, and extraneous data
5. WHEN hash analysis results are returned THEN the system SHALL provide structured responses usable by both Web UI and Control API interfaces
6. WHEN hash validation is performed THEN the system SHALL verify format correctness for specific hash types and provide validation guidance
7. WHEN hash detection confidence is low THEN the system SHALL return multiple possibilities with relative confidence scores for manual selection

### Requirement 5: Shared Template System for Configuration Management

**User Story:** As a security analyst, I want to export and import attack configurations and campaign templates, so that I can reuse successful strategies and share configurations across environments.

#### Acceptance Criteria

1. WHEN attack configurations are exported THEN the system SHALL generate JSON templates with complete configuration data and resource references
2. WHEN campaign templates are exported THEN the system SHALL preserve attack ordering, comments, and ephemeral resource content for complete portability
3. WHEN templates are imported THEN the system SHALL validate schema correctness and resolve resource references by GUID with fallback options
4. WHEN resource references cannot be resolved THEN the system SHALL provide replacement options, skip capabilities, or abort with clear error messages
5. WHEN ephemeral resources are included THEN the system SHALL serialize inline content including custom masks and wordlists
6. WHEN template validation fails THEN the system SHALL return structured error messages with specific field guidance
7. WHEN templates are applied THEN the system SHALL support customization and validation before final campaign creation

### Requirement 6: Service Layer Architecture and Code Reuse

**User Story:** As a developer maintaining Ouroboros, I want consistent business logic across all API interfaces, so that behavior remains predictable and maintenance is simplified.

#### Acceptance Criteria

1. WHEN business operations are performed THEN the system SHALL implement all logic in service layer functions under `app/core/services/`
2. WHEN API endpoints are created THEN the system SHALL act as thin wrappers that delegate to service functions with consistent error handling
3. WHEN data validation is performed THEN the system SHALL use Pydantic models throughout the stack with comprehensive field validation
4. WHEN database operations are executed THEN the system SHALL use SQLAlchemy ORM with async patterns and proper session management
5. WHEN authentication is required THEN the system SHALL use consistent dependency injection patterns across all API interfaces
6. WHEN caching is needed THEN the system SHALL use Cashews exclusively with configurable TTL values and Redis/memory backend support
7. WHEN logging is performed THEN the system SHALL use Loguru exclusively with structured, contextual logging throughout the application

### Requirement 7: Real-Time Event System and Live Updates

**User Story:** As a security analyst monitoring active campaigns, I want real-time updates on campaign progress and system status, so that I can respond quickly to issues and track cracking progress without manual refreshing.

#### Acceptance Criteria

1. WHEN SSE connections are established THEN the system SHALL authenticate using JWT tokens and scope events to user's active project
2. WHEN campaign state changes occur THEN the system SHALL broadcast lightweight trigger events to subscribed clients for targeted UI updates
3. WHEN agent status updates occur THEN the system SHALL notify clients of performance changes, connectivity issues, and error conditions
4. WHEN crack results are submitted THEN the system SHALL trigger real-time notifications for successful hash cracks with appropriate context
5. WHEN SSE connections are lost THEN the system SHALL support automatic reconnection with proper authentication handling
6. WHEN multiple users monitor the same project THEN the system SHALL broadcast events to all authorized subscribers efficiently
7. WHEN event processing is performed THEN the system SHALL use efficient queuing mechanisms to prevent blocking of main application threads

### Requirement 8: Resource Management and S3 Integration

**User Story:** As a security analyst managing attack resources, I want comprehensive file management with secure storage and efficient access, so that I can organize wordlists, rules, and masks effectively.

#### Acceptance Criteria

1. WHEN resources are uploaded THEN the system SHALL store files in S3-compatible storage with UUID-based naming and metadata tracking
2. WHEN resources are accessed THEN the system SHALL generate presigned URLs with time-limited access and appropriate security constraints
3. WHEN resources are edited THEN the system SHALL support line-level editing for eligible resources under configurable size thresholds
4. WHEN resource validation is performed THEN the system SHALL verify content format based on resource type with structured error reporting
5. WHEN resources are deleted THEN the system SHALL check for active usage in campaigns and prevent deletion if resources are in use
6. WHEN ephemeral resources are created THEN the system SHALL support attack-local resources for custom wordlists and mask patterns
7. WHEN resource metadata is managed THEN the system SHALL support name, description, visibility, and project association changes

### Requirement 9: Performance Optimization and Scalability

**User Story:** As a system administrator managing large-scale cracking operations, I want the API to perform efficiently under high load, so that multiple users and agents can operate simultaneously without degradation.

#### Acceptance Criteria

1. WHEN database queries are executed THEN the system SHALL use appropriate indexes, pagination, and query optimization techniques
2. WHEN large datasets are processed THEN the system SHALL implement streaming responses and memory-efficient processing patterns
3. WHEN expensive operations are performed THEN the system SHALL use caching with configurable TTL values and intelligent cache invalidation
4. WHEN concurrent requests are made THEN the system SHALL handle them efficiently using async/await patterns throughout the stack
5. WHEN rate limiting is applied THEN the system SHALL protect against abuse while allowing normal operation for legitimate users and agents
6. WHEN background processing is needed THEN the system SHALL use appropriate task queues and avoid blocking main application threads
7. WHEN resource usage is monitored THEN the system SHALL provide performance metrics and optimization guidance for system administrators

### Requirement 10: Security and Access Control

**User Story:** As a system administrator, I want robust security controls and project-based access restrictions, so that sensitive data remains properly isolated and unauthorized access is prevented.

#### Acceptance Criteria

1. WHEN API requests are made THEN the system SHALL require authentication for all endpoints except public health checks and login
2. WHEN project-scoped data is accessed THEN the system SHALL enforce project context and prevent cross-project data leakage
3. WHEN admin operations are performed THEN the system SHALL validate admin role permissions using Casbin authorization framework
4. WHEN sensitive operations are requested THEN the system SHALL require explicit confirmation and maintain comprehensive audit trails
5. WHEN authentication fails THEN the system SHALL return appropriate error codes without exposing sensitive system information
6. WHEN data is transmitted THEN the system SHALL enforce HTTPS and implement standard security headers
7. WHEN tokens are managed THEN the system SHALL support rotation, revocation, and expiration with appropriate security practices

### Requirement 11: Comprehensive Testing and Validation

**User Story:** As a developer contributing to Ouroboros, I want comprehensive test coverage and validation, so that I can confidently make changes without breaking existing functionality.

#### Acceptance Criteria

1. WHEN service layer functions are implemented THEN the system SHALL include unit tests with mock dependencies and comprehensive coverage
2. WHEN API endpoints are created THEN the system SHALL include integration tests with real database and S3 storage using testcontainers
3. WHEN contract compliance is required THEN the system SHALL validate Agent API v1 responses against OpenAPI specification
4. WHEN validation logic is implemented THEN the system SHALL test both success and failure paths with appropriate error handling
5. WHEN business logic is complex THEN the system SHALL include scenario-based tests covering realistic usage patterns
6. WHEN performance is critical THEN the system SHALL include performance tests and benchmarks for key operations
7. WHEN test data is needed THEN the system SHALL use factory patterns for consistent, maintainable test data generation

### Requirement 12: Documentation and API Reference

**User Story:** As a developer integrating with Ouroboros APIs, I want comprehensive documentation and examples, so that I can understand and use the APIs effectively.

#### Acceptance Criteria

1. WHEN API endpoints are implemented THEN the system SHALL include comprehensive OpenAPI documentation with descriptions and examples
2. WHEN Pydantic schemas are defined THEN the system SHALL include field descriptions, constraints, and example values
3. WHEN error responses are returned THEN the system SHALL document all possible error conditions with appropriate status codes
4. WHEN authentication is required THEN the system SHALL document authentication methods and token formats clearly
5. WHEN complex operations are supported THEN the system SHALL provide usage examples and common workflow patterns
6. WHEN API changes are made THEN the system SHALL maintain version compatibility and document breaking changes
7. WHEN integration guidance is needed THEN the system SHALL provide clear examples for common use cases and integration patterns

### Requirement 13: Monitoring and Observability

**User Story:** As a system administrator, I want comprehensive monitoring and observability features, so that I can track system health, performance, and usage patterns effectively.

#### Acceptance Criteria

1. WHEN system health is checked THEN the system SHALL provide detailed status for all components including database, Redis, MinIO, and task queues
2. WHEN performance metrics are collected THEN the system SHALL track response times, error rates, and resource utilization
3. WHEN audit trails are needed THEN the system SHALL log all significant operations with appropriate context and user information
4. WHEN error conditions occur THEN the system SHALL provide structured error logging with severity levels and contextual information
5. WHEN system usage is analyzed THEN the system SHALL provide metrics on API usage patterns, user activity, and resource consumption
6. WHEN alerts are needed THEN the system SHALL support configurable alerting for critical system conditions
7. WHEN troubleshooting is required THEN the system SHALL provide detailed logging and diagnostic information for issue resolution

### Requirement 14: Migration and Backward Compatibility

**User Story:** As a system administrator upgrading from the Ruby-on-Rails version, I want seamless migration with backward compatibility, so that existing agents and workflows continue operating during the transition.

#### Acceptance Criteria

1. WHEN legacy agents connect THEN the system SHALL maintain exact API compatibility with existing v1 agent implementations
2. WHEN database migration is performed THEN the system SHALL preserve all existing data with appropriate schema transformations
3. WHEN configuration is migrated THEN the system SHALL support import of existing settings and resource files
4. WHEN both systems operate simultaneously THEN the system SHALL support gradual migration without service interruption
5. WHEN legacy features are deprecated THEN the system SHALL provide clear migration paths and timeline guidance
6. WHEN compatibility issues arise THEN the system SHALL provide detailed error messages and resolution guidance
7. WHEN migration is complete THEN the system SHALL provide validation tools to ensure data integrity and functionality

### Requirement 15: Extensibility and Plugin Architecture

**User Story:** As a developer extending Ouroboros functionality, I want a clean plugin architecture and extension points, so that I can add custom features without modifying core code.

#### Acceptance Criteria

1. WHEN custom hash types are needed THEN the system SHALL support plugin-based hash type detection and validation
2. WHEN custom attack modes are required THEN the system SHALL provide extension points for additional attack strategies
3. WHEN custom resource types are needed THEN the system SHALL support pluggable resource handlers and validators
4. WHEN custom authentication is required THEN the system SHALL provide hooks for alternative authentication mechanisms
5. WHEN custom notifications are needed THEN the system SHALL support pluggable notification systems and event handlers
6. WHEN custom storage is required THEN the system SHALL provide abstraction layers for alternative storage backends
7. WHEN plugin management is needed THEN the system SHALL provide discovery, loading, and configuration mechanisms for plugins
