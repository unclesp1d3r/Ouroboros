# Implementation Plan

- [ ] 1. Set up Agent API v2 foundation and routing structure

  - [x] 1.1 Create v2 API router infrastructure

    - Create `app/api/v2/router.py` to organize v2 endpoints
    - Create `app/api/v2/endpoints/agents.py` for agent-specific endpoints
    - Create `app/api/v2/endpoints/tasks.py` for task-specific endpoints
    - Create `app/api/v2/endpoints/attacks.py` for attack-specific endpoints
    - Create `app/api/v2/endpoints/resources.py` for resource-specific endpoints
    - _Requirements: 1.1, 8.1_

  - [ ] 1.2 Set up routing and authentication

    - Set up proper FastAPI routing with tags and documentation
    - Implement base authentication dependency for agent token validation
    - Create error handling middleware specific to agent API
    - Register v2 router in main.py application
    - _Requirements: 1.1, 8.1, 9.1_

- [ ] 2. Implement agent registration endpoint

  - [ ] 2.1 Create registration request/response schemas

    - Define `AgentRegisterRequestV2` Pydantic model with signature, hostname, agent_type, operating_system fields
    - Define `AgentRegisterResponseV2` model with agent_id and token fields
    - Add field validation and constraints for all input fields
    - Create schemas in `app/schemas/agent_v2.py` to separate from v1 schemas
    - _Requirements: 1.1, 1.2, 1.3_

  - [ ] 2.2 Implement registration service function

    - Create `register_agent_v2_service()` function in agent_service.py
    - Generate secure token with format `csa_<agent_id>_<random_token>`
    - Handle duplicate registration attempts and existing agent updates
    - Add proper error handling for database constraints
    - _Requirements: 1.1, 1.4, 9.2_

  - [ ] 2.3 Create registration API endpoint

    - Implement `POST /api/v2/client/agents/register` endpoint in `app/api/v2/endpoints/agents.py`
    - Add input validation and error response handling
    - Return 201 status code on successful registration
    - Handle validation errors (422) and conflicts (409)
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [ ] 3. Implement agent heartbeat system

  - [ ] 3.1 Create heartbeat schemas and validation

    - Define `AgentHeartbeatRequestV2` with state field and validation in `app/schemas/agent_v2.py`
    - Add rate limiting validation for 15-second minimum interval
    - Create response schemas for heartbeat acknowledgment
    - _Requirements: 2.1, 2.3, 10.1_

  - [ ] 3.2 Implement heartbeat service logic

    - Create `process_heartbeat_v2_service()` function in agent_service.py
    - Update agent `last_seen_at`, `last_ipaddress`, and state fields
    - Track missed heartbeats and connection status
    - Implement agent state validation and transitions
    - _Requirements: 2.1, 2.2, 2.5, 3.1, 3.2, 3.3_

  - [ ] 3.3 Create heartbeat API endpoint with rate limiting

    - Implement `POST /api/v2/client/agents/heartbeat` endpoint in agents.py
    - Add rate limiting middleware (max 1 request per 15 seconds)
    - Handle authentication and agent token validation
    - Return appropriate status codes (204, 401, 429)
    - _Requirements: 2.1, 2.2, 2.4, 10.1, 10.2_

- [ ] 4. Implement attack configuration system

  - [ ] 4.1 Create attack configuration schemas

    - Define `AttackConfigurationResponseV2` with attack specification fields in `app/schemas/agent_v2.py`
    - Include mask, rules, and resource reference fields
    - Add forward-compatibility fields for Phase 3 resource management
    - _Requirements: 3.1, 3.4_

  - [ ] 4.2 Implement attack configuration service

    - Create `get_attack_configuration_v2_service()` function in agent_service.py
    - Validate agent capability against hash type requirements
    - Fetch complete attack specification from database
    - Handle authorization and resource access validation
    - _Requirements: 3.1, 3.2, 3.5_

  - [ ] 4.3 Create attack configuration endpoint

    - Implement `GET /api/v2/client/agents/attacks/{attack_id}` endpoint in `app/api/v2/endpoints/attacks.py`
    - Add agent authentication and capability validation
    - Return 404 for non-existent or unauthorized attacks
    - Include proper error handling and status codes
    - _Requirements: 3.1, 3.2, 3.5_

- [ ] 5. Implement task assignment system

  - [ ] 5.1 Create task assignment schemas

    - Define `TaskAssignmentResponseV2` with task details and keyspace chunk in `app/schemas/agent_v2.py`
    - Include hash file references and dictionary IDs (Phase 3 compatible)
    - Add skip and limit fields for keyspace distribution
    - _Requirements: 4.1, 4.2, 4.3_

  - [ ] 5.2 Implement task assignment service logic

    - Create `assign_next_task_v2_service()` function in agent_service.py
    - Enforce one task per agent constraint
    - Find suitable tasks based on agent capabilities
    - Calculate and assign keyspace chunks for parallel processing
    - _Requirements: 4.1, 4.2, 4.4, 4.5_

  - [ ] 5.3 Create task assignment endpoint

    - Implement `GET /api/v2/client/agents/tasks/next` endpoint in `app/api/v2/endpoints/tasks.py`
    - Handle cases where no tasks are available
    - Prevent multiple task assignments to same agent
    - Return appropriate responses for different scenarios
    - _Requirements: 4.1, 4.4, 4.5_

- [ ] 6. Implement progress tracking system

  - [ ] 6.1 Create progress update schemas

    - Define `TaskProgressUpdateV2` with progress_percent and keyspace_processed fields in `app/schemas/agent_v2.py`
    - Add validation for progress values (0-100% range)
    - Include optional estimated completion and current speed fields
    - _Requirements: 5.1, 5.3_

  - [ ] 6.2 Implement progress update service

    - Create `update_task_progress_v2_service()` function in agent_service.py
    - Validate task ownership and agent authorization
    - Update task progress tracking in real-time
    - Handle invalid progress data and edge cases
    - _Requirements: 5.1, 5.2, 5.4, 5.5_

  - [ ] 6.3 Create progress update endpoint

    - Implement `POST /api/v2/client/agents/tasks/{task_id}/progress` endpoint in tasks.py
    - Add task ID validation and agent ownership checks
    - Return appropriate status codes for different scenarios
    - Handle completed or non-existent tasks properly
    - _Requirements: 5.1, 5.2, 5.3, 5.5_

- [ ] 7. Implement result submission system

  - [ ] 7.1 Create result submission schemas

    - Define `TaskResultSubmissionV2` with cracked hashes and metadata structure in `app/schemas/agent_v2.py`
    - Add JSON validation for hash format and structure
    - Include error handling fields for failed tasks
    - _Requirements: 6.1, 6.2, 6.5_

  - [ ] 7.2 Implement result processing service

    - Create `submit_task_results_v2_service()` function in agent_service.py
    - Validate hash format and associate with correct hash list
    - Handle duplicate result detection and prevention
    - Update campaign statistics and progress automatically
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

  - [ ] 7.3 Create result submission endpoint

    - Implement `POST /api/v2/client/agents/tasks/{task_id}/results` endpoint in tasks.py
    - Add comprehensive input validation and error handling
    - Update task status and campaign progress
    - Broadcast success notifications for real-time updates
    - _Requirements: 6.1, 6.4, 6.5_

- [ ] 8. Implement resource management system

  - [ ] 8.1 Create presigned URL schemas

    - Define `ResourceUrlRequestV2` and `ResourceUrlResponseV2` models in `app/schemas/agent_v2.py`
    - Add resource type validation and access control fields
    - Include hash verification requirements in response
    - _Requirements: 7.1, 7.3_

  - [ ] 8.2 Implement presigned URL generation service

    - Create `generate_presigned_url_v2_service()` function in agent_service.py
    - Generate time-limited URLs for MinIO/S3 resources
    - Enforce hash verification requirements before task execution
    - Handle authorization and resource access validation
    - _Requirements: 7.1, 7.2, 7.4, 7.5_

  - [ ] 8.3 Create resource URL endpoint

    - Implement `GET /api/v2/client/agents/resources/{resource_id}/url` endpoint in `app/api/v2/endpoints/resources.py`
    - Add resource authorization and agent validation
    - Return 403 for unauthorized resource access
    - Handle expired or missing resources appropriately
    - _Requirements: 7.1, 7.3, 7.4, 7.5_

- [ ] 9. Implement authentication and authorization system

  - [ ] 9.1 Create agent token validation service

    - Implement `validate_agent_token_v2()` dependency function in `app/core/deps.py`
    - Parse and validate `csa_<agent_id>_<token>` format
    - Add token expiration and revocation support
    - Handle malformed or invalid tokens with proper errors
    - _Requirements: 9.1, 9.2, 9.4, 9.5_

  - [ ] 9.2 Implement token management services

    - Create token generation with cryptographic security in agent_service.py
    - Add token revocation and renewal capabilities
    - Implement usage tracking and monitoring
    - Add automatic cleanup of expired tokens
    - _Requirements: 9.2, 9.3, 9.5_

  - [ ] 9.3 Add comprehensive authorization checks

    - Implement resource-level authorization for agents in agent_service.py
    - Add project-scoped access control where applicable
    - Validate agent permissions for specific operations
    - Handle disabled or suspended agent accounts
    - _Requirements: 9.1, 9.3, 9.4_

- [ ] 10. Implement rate limiting and resource management

  - [ ] 10.1 Create rate limiting middleware

    - Implement per-agent rate limiting for heartbeats (15-second minimum) in `app/core/middleware/rate_limiting.py`
    - Add global system rate limits for API endpoints
    - Create exponential backoff for rate limit violations
    - Return 429 status codes with retry-after headers
    - _Requirements: 10.1, 10.2, 10.4_

  - [ ] 10.2 Implement resource cleanup and management

    - Add automatic cleanup of disconnected agents in agent_service.py
    - Implement task reassignment for failed agents
    - Handle resource constraints and prioritization
    - Add monitoring for system resource usage
    - _Requirements: 10.3, 10.5_

- [x] 11. Maintain backward compatibility with v1 API

  - [x] 11.1 Ensure v1 endpoint compatibility

    - Verify all existing v1 endpoints continue to work unchanged
    - Test `GET /api/v1/client/agents/{id}` endpoint functionality
    - Validate `POST /api/v1/client/agents/{id}/benchmark` compatibility
    - Ensure error and shutdown endpoints work correctly
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_

  - [x] 11.2 Implement dual API support infrastructure

    - Create shared service layer for common operations between v1 and v2
    - Ensure database operations work for both API versions
    - Add version detection and routing logic
    - Handle concurrent v1 and v2 agent operations
    - _Requirements: 8.6_

- [ ] 12. Add comprehensive testing suite

  - [ ] 12.1 Create unit tests for service functions

    - Test agent registration service with various input scenarios in `tests/unit/test_agent_v2_service.py`
    - Test heartbeat processing with state transitions and edge cases
    - Test task assignment logic with capability validation
    - Test result processing with duplicate detection and validation
    - _Requirements: All requirements - validation through testing_

  - [ ] 12.2 Create integration tests for API endpoints

    - Test complete registration flow with database persistence in `tests/integration/v2/test_agent_endpoints.py`
    - Test heartbeat endpoint with rate limiting and authentication
    - Test task assignment and progress tracking workflows
    - Test result submission with real database operations
    - _Requirements: All requirements - end-to-end validation_

  - [ ] 12.3 Create contract tests for API compatibility

    - Validate v2 API responses against OpenAPI specification in `tests/integration/v2/test_agent_contracts.py`
    - Test backward compatibility with v1 API contracts
    - Verify error response formats match specifications
    - Test rate limiting behavior and response codes
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_

- [ ] 13. Add monitoring, logging, and observability

  - [ ] 13.1 Implement comprehensive logging

    - Add structured logging for all agent operations using loguru
    - Log authentication events and security-related activities
    - Include performance metrics and timing information
    - Add error tracking with appropriate log levels
    - _Requirements: 9.1, 9.3, 10.4_

  - [ ] 13.2 Add metrics collection and monitoring

    - Track agent registration and heartbeat rates using existing event service
    - Monitor task assignment latency and success rates
    - Collect result submission metrics and error rates
    - Add system resource usage monitoring
    - _Requirements: 10.3, 10.4, 10.5_

- [ ] 14. Create documentation and deployment configuration

  - [ ] 14.1 Generate OpenAPI documentation

    - Create comprehensive API documentation for all v2 endpoints using FastAPI automatic documentation
    - Include request/response examples and error codes in endpoint docstrings
    - Document authentication requirements and token formats
    - Add migration guide from v1 to v2 API in `docs/api/agent-api-v2-migration.md`
    - _Requirements: All requirements - documentation_

  - [ ] 14.2 Add deployment and configuration management

    - Create environment variable configuration for API settings in `app/core/config.py`
    - Add Docker configuration for containerized deployment (already exists)
    - Include monitoring and alerting configuration
    - Document scaling and performance considerations
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_
