# Implementation Plan

- [ ] 1. Create core task distribution database models

  - Create TaskPlan model with attack_id, total_keyspace, estimated_duration, and status fields
  - Create WorkSlice model with task_plan_id, start_offset, length, status, assigned_agent_id, and lease tracking
  - Create KeyspacePhase model for incremental attacks with phase_order, mask_pattern, and keyspace boundaries
  - Create AgentReliability model to track success/failure/timeout counts per agent and hash type
  - Add database migrations for all new models with proper indexes and relationships
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 2.1, 2.2, 2.3, 2.4, 2.5_

- [ ] 2. Implement TaskPlanner service for keyspace calculation and slice generation

  - Create TaskPlanner service with create_task_plan() and calculate_keyspace() methods
  - Implement hashcat --keyspace integration for accurate keyspace estimation
  - Add generate_work_slices() method using skip/limit parameters for precise control
  - Create handle_incremental_phases() for multi-phase incremental attacks
  - Add hybrid attack keyspace calculation (dictionary × mask combinations)
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 13.1, 13.2, 13.3_

- [ ] 3. Build AgentScorer service for intelligent task assignment

  - Create AgentScorer service with score_agent() method using benchmark data and reliability
  - Implement update_reliability() method to track agent success/failure patterns
  - Add apply_thermal_penalty() method to reduce scores for overheating agents
  - Create agent health monitoring with failure pattern detection
  - Add reliability score calculation using rolling success/failure ratios
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 8.1, 8.2, 8.3, 8.4, 12.1, 12.2, 12.3, 12.4, 12.5_

- [ ] 4. Implement WorkSlice Manager for slice lifecycle management

  - Create WorkSlice Manager service with assign_slice(), update_progress(), and complete_slice() methods
  - Add slice status tracking (queued, assigned, running, completed, failed)
  - Implement slice reassignment logic for failed or abandoned slices
  - Create reclaim_expired_slices() method for automatic cleanup
  - Add slice splitting capability for failed large slices
  - _Requirements: 1.4, 1.5, 1.6, 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ] 5. Build Redis-based lease management system

  - Create Lease Manager service with create_lease(), extend_lease(), and reclaim_expired_leases() methods
  - Implement TTL-based slice tracking in Redis with task:lease:{agent_id}:{slice_id} keys
  - Add agent health caching with agent:health:{agent_id} keys
  - Create background worker for expired lease detection and reclamation
  - Implement automatic slice reassignment when leases expire
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ] 6. Create Agent API v2 endpoints for advanced task distribution

  - Create /api/v2/client/tasks/request endpoint returning WorkSlice with lease management
  - Implement /api/v2/client/status endpoint for structured telemetry from --status-json
  - Add /api/v2/client/tasks/{task_id}/progress endpoint for real-time progress updates
  - Create /api/v2/client/tasks/{task_id}/complete endpoint with result submission
  - Implement /api/v2/client/heartbeat endpoint with backoff signal support
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 9.1, 9.2, 9.3, 9.4, 10.1, 10.2_

- [ ] 7. Implement real-time agent status streaming and processing

  - Create AgentStatusUpdate model for structured telemetry data
  - Implement status processing pipeline to parse hashcat --status-json output
  - Add real-time progress tracking and WorkSlice status updates
  - Create WebSocket connections for live dashboard updates
  - Implement device temperature and performance monitoring
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [ ] 8. Build intelligent backoff and load smoothing system

  - Implement backoff signal generation based on agent health and system load
  - Add randomized sync intervals to prevent heartbeat synchronization spikes
  - Create load detection and automatic backoff trigger mechanisms
  - Update agent heartbeat endpoints to return backoff_seconds when needed
  - Add agent-side backoff handling with appropriate jitter
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

- [ ] 9. Create learned rules system with debug output parsing

  - Create SubmittedDebugArtifact, RuleUsageLog, and LearnedRule database models
  - Implement agent debug artifact upload endpoint to MinIO with compression
  - Create Celery task parse_and_score_debug_rules() for asynchronous processing
  - Add rule promotion logic based on success criteria and effectiveness scoring
  - Create generate_learned_rules_file() method for project-specific rule generation
  - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5_

- [ ] 10. Build Markov model auto-generation system

  - Create ProjectMarkovModel database model with version tracking and metadata
  - Implement internal markov_statsgen() engine for .hcstat2 file generation
  - Add automatic model updates triggered by crack count thresholds and staleness
  - Create background job update_markov_model() for incremental model building
  - Add UI integration for Markov-enhanced brute force attacks
  - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5_

- [ ] 11. Implement agent self-governance and fault recovery

  - Add agent thermal monitoring and automatic workload adjustment
  - Implement agent checkpoint writing for mid-task recovery
  - Create checkpoint upload endpoint and slice recovery assessment logic
  - Add agent self-throttling based on environmental conditions
  - Create thermal event handling with automatic backoff and recovery
  - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5_

- [ ] 12. Create DAG-based campaign planning system

  - Create DAGCampaign, DAGPhase, and DAGTemplate database models
  - Implement DAG execution engine with phase dependency management
  - Add success criteria evaluation and automatic phase triggering
  - Create DAG progress visualization and phase status tracking
  - Implement phase-aware attack strategy selection
  - _Requirements: 16.1, 16.2, 16.3, 16.4, 16.5_

- [ ] 13. Build comprehensive monitoring and analytics dashboard

  - Create real-time dashboard with slice distribution and completion statistics
  - Implement campaign progress tracking with keyspace-weighted progress bars
  - Add agent performance analytics and thermal status monitoring
  - Create rule effectiveness visualization and Markov model analytics
  - Implement slice assignment monitoring and agent fleet management interface
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ] 14. Add campaign control and management features

  - Implement campaign pause/resume functionality with task state management
  - Add campaign stop functionality with agent notification and task cancellation
  - Create campaign priority management and preemption logic
  - Implement background task prioritization for low-priority campaigns
  - Add campaign scheduling and automated execution features
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

- [ ] 15. Create secure task payload delivery system

  - Implement secure task payload generation with complete attack parameters
  - Add presigned URL generation for resource downloads
  - Create task parameter validation and error handling
  - Implement encrypted communication for all agent-server interactions
  - Add JWT-based authentication for all agent communications
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ] 16. Build performance optimization and caching layer

  - Implement Redis caching for agent scoring results and TaskPlan metadata
  - Add database query optimization with proper indexing for slice operations
  - Create efficient JSON serialization for status streaming
  - Implement batch operations for bulk slice updates and status processing
  - Add connection pooling and query optimization for high-throughput scenarios
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ] 17. Add comprehensive testing and validation

  - Create unit tests for TaskPlanner, AgentScorer, and WorkSlice Manager services
  - Implement integration tests for end-to-end slice distribution workflows
  - Add performance tests for slice assignment throughput and status streaming
  - Create contract tests for Agent API v2 compatibility and lease management
  - Add load testing for concurrent agent coordination and slice processing
  - _Requirements: All requirements validation_

- [ ] 18. Implement security and access control enhancements

  - Add project-scoped permissions for slice assignments and task access
  - Create rate limiting for agent endpoints and status streaming
  - Add audit logging for all administrative actions and slice operations
  - Implement IP-based restrictions and agent authentication validation
  - Create security monitoring for suspicious agent behavior patterns
  - _Requirements: Security considerations across all requirements_

- [ ] 19. Create administrative interfaces and tooling

  - Build admin dashboard for slice assignment monitoring and agent fleet management
  - Implement campaign management interface with DAG visualization
  - Add rule effectiveness explorer and Markov model management tools
  - Create debugging tools for slice replay and performance analysis
  - Implement system health monitoring and alerting interfaces
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 6.4_

- [ ] 20. Integrate and deploy complete system

  - Integrate all components with existing Ouroboros infrastructure
  - Create deployment scripts and configuration management
  - Implement monitoring and alerting for production deployment
  - Create documentation and user guides for new task distribution features
  - Add migration scripts for existing campaigns and tasks to new system
  - _Requirements: All requirements integration and deployment_
