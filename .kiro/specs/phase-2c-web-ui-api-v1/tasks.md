# Implementation Plan

## Overview

This implementation plan transforms the Web UI API v1 requirements and design into actionable coding tasks. The plan follows a test-driven development approach with incremental progress, building upon the existing Ouroboros infrastructure while adding comprehensive web interface capabilities.

The implementation is organized into logical phases that can be executed independently while maintaining system functionality. Each task includes specific requirements references and builds incrementally toward the complete Web UI API.

## Implementation Tasks

- [ ] Phase 1: Core Infrastructure and Authentication

- [ ] 1. Enhance authentication system for web UI requirements

  - Implement JWT-based authentication with refresh token support
  - Add project context switching functionality
  - Create user session management with project scoping
  - Implement Casbin-based authorization for role-based access control
  - Add authentication middleware for all web endpoints
  - _Requirements: 1.1, 1.2, 1.3, 1.6, 1.7, 11.1, 11.2, 11.3_

- [x] 1.1 Create authentication endpoints

  - Implement `POST /api/v1/web/auth/login` with JWT token generation
  - Implement `POST /api/v1/web/auth/logout` with token invalidation
  - Implement `POST /api/v1/web/auth/refresh` for token renewal
  - Implement `GET /api/v1/web/auth/me` for user profile retrieval
  - Implement `PATCH /api/v1/web/auth/me` for profile updates
  - Implement `POST /api/v1/web/auth/change_password` with validation
  - _Requirements: 1.1, 1.2_

- [x] 1.2 Implement project context management

  - Create `GET /api/v1/web/auth/context` endpoint for user context
  - Create `POST /api/v1/web/auth/context` endpoint for project switching
  - Add project scoping middleware for all web endpoints
  - Implement project access validation using Casbin policies
  - _Requirements: 1.6, 1.7, 11.2_

- [ ] 1.3 Create user and project management endpoints (admin only)

  - Implement `GET /api/v1/web/users/` with pagination and filtering
  - Implement `POST /api/v1/web/users/` for user creation
  - Implement `GET /api/v1/web/users/{id}` for user details
  - Implement `PATCH /api/v1/web/users/{id}` for user updates
  - Implement `DELETE /api/v1/web/users/{id}` for user deactivation
  - Implement project management endpoints with user assignment
  - _Requirements: 1.3, 1.4, 1.5_

- [ ] Phase 2: Campaign Management with Real-Time Updates

- [ ] 2. Implement comprehensive campaign management

  - Create campaign CRUD operations with state management
  - Add attack ordering and DAG phase support
  - Implement real-time progress tracking and metrics
  - Add campaign lifecycle controls (start/stop/pause/archive)
  - Create campaign template export/import functionality
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7_

- [x] 2.1 Create campaign CRUD endpoints

  - Implement `GET /api/v1/web/campaigns/` with pagination, filtering, and real-time updates
  - Implement `POST /api/v1/web/campaigns/` with validation and hash list assignment
  - Implement `GET /api/v1/web/campaigns/{id}` with comprehensive attack details
  - Implement `PATCH /api/v1/web/campaigns/{id}` with state transition validation
  - Implement `DELETE /api/v1/web/campaigns/{id}` with archive functionality
  - _Requirements: 2.1, 2.2_

- [x] 2.2 Add campaign progress and metrics endpoints

  - Implement `GET /api/v1/web/campaigns/{id}/progress` for real-time progress data
  - Implement `GET /api/v1/web/campaigns/{id}/metrics` for aggregate statistics
  - Create progress calculation service with keyspace weighting
  - Add crack rate and agent participation metrics
  - _Requirements: 2.5, 2.6_

- [x] 2.3 Implement campaign lifecycle controls

  - Create `POST /api/v1/web/campaigns/{id}/start` endpoint
  - Create `POST /api/v1/web/campaigns/{id}/stop` endpoint
  - Create `POST /api/v1/web/campaigns/{id}/relaunch` endpoint
  - Add state validation and confirmation requirements
  - Implement task reassignment logic for relaunched campaigns
  - _Requirements: 2.4, 2.7_

- [ ] 2.4 Add attack management within campaigns

  - Implement `POST /api/v1/web/campaigns/{id}/add_attack` endpoint
  - Create `POST /api/v1/web/campaigns/{id}/reorder_attacks` for DAG management
  - Add attack position and comment field support
  - Implement complexity scoring for attack ordering
  - _Requirements: 2.3, 2.4_

- [ ] Phase 3: Advanced Attack Configuration

- [ ] 3. Create sophisticated attack configuration system

  - Implement attack CRUD with real-time validation
  - Add keyspace estimation and complexity scoring
  - Create type-specific attack editors (dictionary, mask, brute force)
  - Implement ephemeral resource support for inline editing
  - Add attack template export/import functionality
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

- [x] 3.1 Create attack CRUD endpoints

  - Implement `GET /api/v1/web/attacks/` with pagination and search
  - Implement `POST /api/v1/web/attacks/` with comprehensive validation
  - Implement `GET /api/v1/web/attacks/{id}` with configuration details
  - Implement `PATCH /api/v1/web/attacks/{id}` with lifecycle impact warnings
  - Implement `DELETE /api/v1/web/attacks/{id}` with dependency checking
  - _Requirements: 3.1, 3.2_

- [x] 3.2 Implement attack validation and estimation

  - Create `POST /api/v1/web/attacks/validate` endpoint for configuration validation
  - Implement `POST /api/v1/web/attacks/estimate` for real-time keyspace calculation
  - Add complexity scoring algorithm based on keyspace and resource requirements
  - Create validation service for attack mode compatibility
  - _Requirements: 3.2, 3.3_

- [x] 3.3 Add attack manipulation endpoints

  - Implement `POST /api/v1/web/attacks/{id}/move` for position changes
  - Implement `POST /api/v1/web/attacks/{id}/duplicate` for attack cloning
  - Implement `DELETE /api/v1/web/attacks/bulk` for batch operations
  - Add attack ordering service with DAG phase awareness
  - _Requirements: 3.4, 3.5_

- [ ] 3.4 Create ephemeral resource support

  - Implement inline wordlist creation and management
  - Add ephemeral mask list support for attack-specific masks
  - Create ephemeral resource cleanup on attack deletion
  - Implement validation for ephemeral resource content
  - _Requirements: 3.6, 3.7_

- [ ] 3.5 Add attack template system

  - Implement `GET /api/v1/web/attacks/{id}/export` for JSON export
  - Implement `POST /api/v1/web/attacks/import` for template loading
  - Create schema versioning and validation for templates
  - Add resource reference resolution by GUID
  - _Requirements: 3.7, 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7_

- [ ] Phase 4: Hash List Management and Processing

- [ ] 4. Implement comprehensive hash list management

  - Create hash list CRUD with import/export capabilities
  - Add hash item management with pagination and filtering
  - Implement crackable upload processing with automatic analysis
  - Add hash type detection and validation
  - Create export functionality for cracked results
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7_

- [x] 4.1 Create hash list CRUD endpoints

  - Implement `GET /api/v1/web/hash_lists/` with pagination and search
  - Implement `POST /api/v1/web/hash_lists/` with validation
  - Implement `GET /api/v1/web/hash_lists/{id}` with metadata
  - Implement `PATCH /api/v1/web/hash_lists/{id}` with integrity checking
  - Implement `DELETE /api/v1/web/hash_lists/{id}` with usage validation
  - _Requirements: 4.1, 4.2, 4.5_

- [x] 4.2 Add hash item management

  - Implement `GET /api/v1/web/hash_lists/{id}/items` with pagination
  - Add filtering by crack status (cracked/uncracked)
  - Implement search functionality for hash values and plaintexts
  - Add CSV/TSV export functionality for hash items
  - _Requirements: 4.3, 4.4_

- [x] 4.3 Create crackable upload system

  - Implement `POST /api/v1/web/uploads/` for file and text uploads
  - Create `GET /api/v1/web/uploads/{id}/status` for processing status
  - Implement `POST /api/v1/web/uploads/{id}/launch_campaign` for campaign generation
  - Add `GET /api/v1/web/uploads/{id}/errors` for error reporting
  - Implement `DELETE /api/v1/web/uploads/{id}` for cleanup
  - _Requirements: 4.6, 4.7_

- [ ] 4.4 Add hash analysis and detection

  - Implement hash type detection service using name-that-hash
  - Create hash validation and parsing functionality
  - Add confidence scoring for hash type detection
  - Implement preview generation for upload analysis
  - _Requirements: 4.6, 4.7_

- [ ] Phase 5: Agent Management and Monitoring

- [ ] 5. Create comprehensive agent management system

  - Implement agent listing with real-time status updates
  - Add detailed agent configuration and hardware management
  - Create performance monitoring with time-series data
  - Implement error logging and benchmark management
  - Add admin controls for agent lifecycle management
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7_

- [x] 5.1 Create agent listing and basic management

  - Implement `GET /api/v1/web/agents/` with pagination and filtering
  - Add real-time status updates via SSE integration
  - Implement `GET /api/v1/web/agents/{id}` for detailed agent information
  - Create `PATCH /api/v1/web/agents/{id}` for basic configuration updates
  - _Requirements: 5.1, 5.2_

- [x] 5.2 Add agent hardware and configuration management

  - Implement `GET /api/v1/web/agents/{id}/hardware` for device information
  - Create `PATCH /api/v1/web/agents/{id}/hardware` for hardware configuration
  - Add `PATCH /api/v1/web/agents/{id}/config` for advanced settings
  - Implement `PATCH /api/v1/web/agents/{id}/devices` for device toggles
  - _Requirements: 5.3, 5.4_

- [x] 5.3 Create performance monitoring system

  - Implement `GET /api/v1/web/agents/{id}/performance` for time-series data
  - Create agent device performance time-series storage
  - Add performance data collection service
  - Implement performance graph data endpoints
  - _Requirements: 5.5_

- [x] 5.4 Add error logging and benchmark management

  - Implement `GET /api/v1/web/agents/{id}/errors` for structured error logs
  - Create `GET /api/v1/web/agents/{id}/benchmarks` for capability data
  - Add `POST /api/v1/web/agents/{id}/benchmark` for benchmark triggering
  - Implement `GET /api/v1/web/agents/{id}/capabilities` for capability matrix
  - _Requirements: 5.6, 5.7_

- [ ] 5.5 Add admin controls and agent lifecycle management

  - Create `POST /api/v1/web/agents/` for agent registration
  - Implement `POST /api/v1/web/agents/{id}/test_presigned` for URL validation
  - Add agent creation with token generation
  - Implement admin-only agent control endpoints
  - _Requirements: 5.7_

- [ ] Phase 6: Resource Management and Line-Level Editing

- [ ] 6. Implement comprehensive resource management

  - Create resource CRUD with type detection and validation
  - Add line-level editing for small resources
  - Implement resource upload with S3 integration
  - Add metadata management and search functionality
  - Create resource linking and dependency tracking
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7_

- [x] 6.1 Create resource CRUD endpoints

  - Implement `GET /api/v1/web/resources/` with filtering by type
  - Implement `POST /api/v1/web/resources/` with upload and validation
  - Implement `GET /api/v1/web/resources/{id}` with metadata
  - Implement `PATCH /api/v1/web/resources/{id}` for metadata updates
  - Implement `DELETE /api/v1/web/resources/{id}` with dependency checking
  - _Requirements: 6.1, 6.2, 6.6_

- [x] 6.2 Add resource content management

  - Implement `GET /api/v1/web/resources/{id}/content` for editable content
  - Create `PATCH /api/v1/web/resources/{id}/content` for content updates
  - Add `GET /api/v1/web/resources/{id}/preview` for content preview
  - Implement size and line count validation for editing eligibility
  - _Requirements: 6.3, 6.4_

- [ ] 6.3 Create line-level editing system

  - Implement `GET /api/v1/web/resources/{id}/lines` with pagination
  - Create `POST /api/v1/web/resources/{id}/lines` for line addition
  - Add `PATCH /api/v1/web/resources/{id}/lines/{line_id}` for line updates
  - Implement `DELETE /api/v1/web/resources/{id}/lines/{line_id}` for line removal
  - Add real-time validation for resource-specific syntax
  - _Requirements: 6.4, 6.5_

- [ ] 6.4 Add resource metadata and management

  - Create resource type detection and validation
  - Implement GUID-based resource referencing for templates
  - Add resource usage tracking and dependency management
  - Create orphan resource cleanup functionality
  - _Requirements: 6.5, 6.6, 6.7_

- [ ] Phase 7: Real-Time Updates and Event System

- [ ] 7. Implement Server-Sent Events system for real-time updates

  - Create SSE infrastructure with authentication and project scoping
  - Add event broadcasting service for campaign, agent, and system updates
  - Implement lightweight notification system with client-driven updates
  - Add connection management and automatic reconnection
  - Create event filtering and subscription management
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7_

- [x] 7.1 Create SSE infrastructure

  - Implement `GET /api/v1/web/live/campaigns` for campaign event stream
  - Create `GET /api/v1/web/live/agents` for agent event stream
  - Add `GET /api/v1/web/live/toasts` for notification stream
  - Implement JWT authentication for SSE connections
  - _Requirements: 7.1, 7.2, 7.3_

- [x] 7.2 Add event broadcasting service

  - Create in-memory event broadcasting system
  - Implement topic-based event subscription management
  - Add project-scoped event filtering
  - Create event listener lifecycle management
  - _Requirements: 7.4, 7.5_

- [ ] 7.3 Integrate event triggers throughout system

  - Add campaign event triggers for state changes
  - Implement agent event triggers for status updates
  - Create toast event triggers for crack results
  - Add service-layer event broadcasting integration
  - _Requirements: 7.6, 7.7_

- [ ] Phase 8: Dashboard and System Monitoring

- [ ] 8. Create comprehensive dashboard and health monitoring

  - Implement dashboard summary with 4-card layout
  - Add system health monitoring for all components
  - Create performance metrics and time-series data
  - Implement caching for expensive operations
  - Add real-time updates for dashboard components
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7_

- [x] 8.1 Create dashboard summary endpoint

  - Implement `GET /api/v1/web/dashboard/summary` with aggregated metrics
  - Add active agents, running tasks, cracked hashes, and resource usage cards
  - Create sparkline data for hash rate trends
  - Implement project-scoped dashboard data
  - _Requirements: 8.1, 8.2_

- [x] 8.2 Add system health monitoring

  - Implement `GET /api/v1/web/health/overview` for operational status
  - Create `GET /api/v1/web/health/components` for detailed service health
  - Add health checks for PostgreSQL, Redis, and MinIO
  - Implement performance metrics collection
  - _Requirements: 8.3, 8.4_

- [ ] 8.3 Create caching infrastructure

  - Implement Cashews cache integration with memory and Redis backends
  - Add configurable TTL values for different data types
  - Create cache invalidation strategies for real-time updates
  - Implement cache warming for expensive operations
  - _Requirements: 8.5, 8.6, 8.7_

- [ ] Phase 9: UX Support and Utility Endpoints

- [ ] 9. Implement UX support features and utility endpoints

  - Create dropdown population endpoints for UI components
  - Add configuration suggestion and validation helpers
  - Implement rule explanation and syntax help
  - Create default configuration templates
  - Add intelligent UX features for attack configuration
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7_

- [x] 9.1 Create modal support endpoints

  - Implement `GET /api/v1/web/modals/agents` for agent dropdowns
  - Create `GET /api/v1/web/modals/resources` for resource selection
  - Add `GET /api/v1/web/modals/hash_types` with confidence scoring
  - Implement filtering and search for dropdown data
  - _Requirements: 9.1, 9.2_

- [x] 9.2 Add configuration assistance features

  - Create `GET /api/v1/web/modals/rule_explanation` for syntax help
  - Implement default configuration suggestions for attacks
  - Add intelligent charset and mask recommendations
  - Create rule modifier mapping for user-friendly options
  - _Requirements: 9.3, 9.4, 9.5_

- [ ] 9.3 Implement hash type detection and validation

  - Create hash guessing service integration
  - Add confidence scoring for hash type detection
  - Implement hash type override functionality
  - Create validation for hash format compatibility
  - _Requirements: 9.6, 9.7_

- [ ] Phase 10: Security, Performance, and Production Readiness

- [ ] 10. Implement security controls and performance optimization

  - Add comprehensive input validation and sanitization
  - Implement rate limiting and abuse prevention
  - Create audit logging for sensitive operations
  - Add performance monitoring and optimization
  - Implement production deployment considerations
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7, 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7_

- [ ] 10.1 Add security controls

  - Implement comprehensive input validation using Pydantic
  - Add SQL injection prevention through parameterized queries
  - Create XSS prevention through output encoding
  - Implement CSRF protection for state-changing operations
  - _Requirements: 11.4, 11.5_

- [ ] 10.2 Create performance optimization

  - Add database query optimization with appropriate indexes
  - Implement cursor-based pagination for large datasets
  - Create connection pooling optimization
  - Add background task processing for expensive operations
  - _Requirements: 12.1, 12.2, 12.5_

- [ ] 10.3 Add monitoring and observability

  - Implement structured logging with correlation IDs
  - Create performance metrics collection
  - Add error rate monitoring and alerting
  - Implement health check endpoints for deployment
  - _Requirements: 12.3, 12.4, 12.6, 12.7_

- [ ] Phase 11: Testing and Documentation

- [ ] 11. Create comprehensive test coverage and documentation

  - Implement unit tests for all service layer functions
  - Add integration tests for API endpoints
  - Create end-to-end tests for critical workflows
  - Add performance and load testing
  - Update documentation for new API capabilities
  - _Requirements: All requirements need test coverage_

- [ ] 11.1 Create service layer tests

  - Write unit tests for all business logic functions
  - Add tests for error handling and edge cases
  - Create mock objects for external dependencies
  - Implement test data factories for consistent test data
  - _Requirements: All service layer functions_

- [ ] 11.2 Add API endpoint tests

  - Create integration tests for all endpoints
  - Add authentication and authorization tests
  - Test pagination, filtering, and search functionality
  - Validate error responses and status codes
  - _Requirements: All API endpoints_

- [ ] 11.3 Create end-to-end workflow tests

  - Test complete user workflows from login to campaign completion
  - Add tests for real-time update functionality
  - Create tests for file upload and processing workflows
  - Test agent management and monitoring workflows
  - _Requirements: Complete user workflows_

- [ ] 11.4 Add performance and load tests

  - Create performance benchmarks for critical endpoints
  - Add load testing for concurrent user scenarios
  - Test SSE connection handling under load
  - Validate database performance under stress
  - _Requirements: Performance requirements_

- [ ] 11.5 Update documentation

  - Update API reference documentation
  - Create user guide updates for new functionality
  - Add troubleshooting guides for common issues
  - Update architecture documentation
  - _Requirements: Documentation requirements_

## Implementation Notes

### Development Approach

- Follow test-driven development (TDD) principles
- Implement service layer functions before API endpoints
- Use existing Ouroboros patterns and conventions
- Maintain backward compatibility with existing Agent APIs

### Quality Standards

- Minimum 80% test coverage for all new code
- All endpoints must include comprehensive error handling
- Real-time features must gracefully degrade when SSE is unavailable
- All user input must be validated using Pydantic schemas

### Dependencies and Integration

- Build upon existing SQLAlchemy models and database schema
- Integrate with existing authentication and authorization systems
- Use established patterns from existing service layer implementations
- Maintain compatibility with existing Agent API contracts

### Performance Considerations

- Implement caching for expensive operations
- Use appropriate database indexes for query optimization
- Design for horizontal scaling through stateless architecture
- Consider background task processing for long-running operations

This implementation plan provides a structured approach to building the comprehensive Web UI API v1 while maintaining system reliability and following established development practices.
