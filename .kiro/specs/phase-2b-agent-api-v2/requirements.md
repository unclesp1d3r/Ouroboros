# Requirements Document

## Introduction

The Agent API v2 is a modernized version of the Ouroboros agent communication interface that enables distributed password cracking agents to register, authenticate, receive task assignments, and report results. This API replaces the legacy v1 agent API with improved authentication, better state management, and enhanced task distribution capabilities while maintaining backward compatibility.

The Agent API v2 serves as the primary communication channel between Ouroboros agents (distributed hashcat instances) and the central server, enabling efficient coordination of password cracking operations across multiple machines in a network.

## Requirements

### Requirement 1

**User Story:** As a Ouroboros agent, I want to register with the server and receive authentication credentials, so that I can securely communicate with the server for task assignments.

#### Acceptance Criteria

1. WHEN an agent sends a registration request with client signature, hostname, and agent type THEN the system SHALL create a new agent record and return a bearer token in format `csa_<agent_id>_<token>`
2. WHEN an agent attempts to register with invalid or missing required fields THEN the system SHALL return a 422 validation error
3. WHEN an agent registration is successful THEN the system SHALL store the agent's capabilities and metadata in the database
4. WHEN an agent re-registers with the same client signature THEN the system SHALL update the existing record rather than create a duplicate

### Requirement 2

**User Story:** As a Ouroboros agent, I want to send periodic heartbeats to the server, so that the server knows I am online and available for task assignments.

#### Acceptance Criteria

1. WHEN an agent sends a heartbeat with valid authorization header THEN the system SHALL update the agent's `last_seen_at` timestamp and `last_ipaddress`
2. WHEN an agent sends heartbeats more frequently than once every 15 seconds THEN the system SHALL rate limit the requests and return a 429 error
3. WHEN an agent includes status updates in the heartbeat THEN the system SHALL validate the status is one of: `pending`, `active`, `error`, `offline`
4. WHEN an agent sends a heartbeat with invalid or expired token THEN the system SHALL return a 401 authentication error
5. WHEN an agent misses multiple consecutive heartbeats THEN the system SHALL mark the agent as disconnected

### Requirement 3

**User Story:** As a Ouroboros agent, I want to receive attack configurations from the server, so that I can execute password cracking tasks with the correct parameters.

#### Acceptance Criteria

1. WHEN an agent requests an attack configuration THEN the system SHALL return the full attack specification including masks, rules, and resource references
2. WHEN an agent requests an attack configuration THEN the system SHALL validate the agent's capability to handle the specified hash type before assignment
3. WHEN an agent lacks the capability for a hash type THEN the system SHALL not assign campaigns for that hash type to the agent
4. WHEN attack configuration includes resource references THEN the system SHALL provide forward-compatible fields for Phase 3 resource management
5. WHEN an agent requests attack configuration for a non-existent or unauthorized attack THEN the system SHALL return a 404 error

### Requirement 4

**User Story:** As a Ouroboros agent, I want to receive task assignments with specific keyspace chunks, so that I can work on a portion of the overall cracking operation in parallel with other agents.

#### Acceptance Criteria

1. WHEN an agent is available for work THEN the system SHALL assign at most one task per agent at any time
2. WHEN a task is assigned THEN the system SHALL include keyspace chunk information with skip and limit fields
3. WHEN a task is assigned THEN the system SHALL include hash file references and dictionary IDs (with Phase 3 compatibility)
4. WHEN no tasks are available for an agent THEN the system SHALL return an appropriate response indicating no work available
5. WHEN an agent already has an active task THEN the system SHALL not assign additional tasks until the current task is completed

### Requirement 5

**User Story:** As a Ouroboros agent, I want to report progress updates during task execution, so that the server can track the status of cracking operations.

#### Acceptance Criteria

1. WHEN an agent sends a progress update THEN the system SHALL accept `progress_percent` and `keyspace_processed` fields
2. WHEN an agent sends progress updates THEN the system SHALL validate the task ID exists and belongs to the requesting agent
3. WHEN an agent sends invalid progress data THEN the system SHALL return a 422 validation error
4. WHEN progress updates are received THEN the system SHALL update the task's progress tracking in real-time
5. WHEN an agent sends progress for a completed or non-existent task THEN the system SHALL return an appropriate error

### Requirement 6

**User Story:** As a Ouroboros agent, I want to submit cracking results when I successfully crack hashes, so that the results can be stored and made available to users.

#### Acceptance Criteria

1. WHEN an agent submits results THEN the system SHALL accept a JSON structure containing cracked hashes and metadata
2. WHEN results are submitted THEN the system SHALL validate the hash format and associate results with the correct hash list
3. WHEN duplicate results are submitted THEN the system SHALL handle them appropriately without creating duplicates
4. WHEN results are successfully submitted THEN the system SHALL update campaign statistics and progress
5. WHEN invalid result data is submitted THEN the system SHALL return a 422 validation error with specific field information

### Requirement 7

**User Story:** As a Ouroboros agent, I want to access presigned URLs for downloading attack resources, so that I can obtain wordlists, rules, and other files needed for cracking operations.

#### Acceptance Criteria

1. WHEN an agent requests resource access THEN the system SHALL generate time-limited presigned URLs for authorized resources
2. WHEN presigned URLs are generated THEN the system SHALL enforce hash verification requirements before task execution
3. WHEN an agent attempts to access unauthorized resources THEN the system SHALL return a 403 forbidden error
4. WHEN presigned URLs expire THEN the system SHALL require agents to request new URLs
5. WHEN resource files are corrupted or missing THEN the system SHALL provide appropriate error responses

### Requirement 8

**User Story:** As a legacy Ouroboros agent using v1 API, I want my existing integration to continue working, so that I don't need to immediately upgrade to v2.

#### Acceptance Criteria

1. WHEN a v1 agent makes requests to legacy endpoints THEN the system SHALL maintain full backward compatibility
2. WHEN v1 agents access `GET /api/v1/agents/{id}` THEN the system SHALL return responses matching the existing swagger specification
3. WHEN v1 agents submit benchmarks via `POST /api/v1/agents/{id}/benchmark` THEN the system SHALL process them correctly
4. WHEN v1 agents report errors via `POST /api/v1/agents/{id}/error` THEN the system SHALL log and handle them appropriately
5. WHEN v1 agents shutdown via `POST /api/v1/agents/{id}/shutdown` THEN the system SHALL update agent status correctly
6. WHEN both v1 and v2 agents operate simultaneously THEN the system SHALL handle both without conflicts

### Requirement 9

**User Story:** As a system administrator, I want comprehensive authentication and authorization for agent communications, so that only authorized agents can access the system and perform operations.

#### Acceptance Criteria

1. WHEN agents authenticate THEN the system SHALL use bearer tokens with the format `csa_<agent_id>_<token>`
2. WHEN authentication tokens are generated THEN the system SHALL ensure they are cryptographically secure and unique
3. WHEN agents make authenticated requests THEN the system SHALL validate tokens and associate actions with the correct agent
4. WHEN authentication fails THEN the system SHALL return appropriate 401 errors without exposing sensitive information
5. WHEN tokens are compromised or expired THEN the system SHALL provide mechanisms for token revocation and renewal

### Requirement 10

**User Story:** As a system administrator, I want proper rate limiting and resource management for agent communications, so that the system remains stable under high load.

#### Acceptance Criteria

1. WHEN agents send heartbeats THEN the system SHALL enforce a minimum 15-second interval between requests
2. WHEN rate limits are exceeded THEN the system SHALL return 429 errors with appropriate retry-after headers
3. WHEN multiple agents connect simultaneously THEN the system SHALL handle concurrent connections efficiently
4. WHEN system resources are constrained THEN the system SHALL prioritize critical operations like result submission
5. WHEN agents disconnect unexpectedly THEN the system SHALL clean up resources and reassign tasks appropriately
