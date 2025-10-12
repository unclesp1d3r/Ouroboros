# Requirements Document

## Introduction

This specification defines the core infrastructure requirements for Phase 1 of the Ouroboros v2 rewrite. The goal is to establish the foundational database models, authentication system, and basic API structure that will support the distributed password cracking management system. This phase focuses on creating a robust, scalable foundation using FastAPI, SQLAlchemy, and PostgreSQL.

## Requirements

### Requirement 1

**User Story:** As a system administrator, I want a robust database foundation with proper session management, so that the application can handle concurrent operations reliably.

#### Acceptance Criteria

1. WHEN the application starts THEN the system SHALL establish an async SQLAlchemy engine with connection pooling
2. WHEN database operations are performed THEN the system SHALL use dependency injection for session management
3. WHEN the health check endpoint is called THEN the system SHALL return database connectivity status
4. WHEN any model is created THEN the system SHALL automatically populate `id`, `created_at`, and `updated_at` fields

### Requirement 2

**User Story:** As a system administrator, I want comprehensive user management with authentication and authorization, so that access to the system can be properly controlled.

#### Acceptance Criteria

1. WHEN a user is created THEN the system SHALL store `name`, `email`, `role` (admin/analyst/operator), and authentication metadata
2. WHEN a user logs in THEN the system SHALL track `sign_in_count`, `current_sign_in_at`, `last_sign_in_at`, `current_sign_in_ip`, `last_sign_in_ip`
3. WHEN authentication fails THEN the system SHALL track `failed_attempts` and support account locking via `unlock_token`
4. WHEN password reset is requested THEN the system SHALL generate and store a `reset_password_token`
5. WHEN user data is queried THEN the system SHALL use unique indexes on `email`, `name`, and `reset_password_token`

### Requirement 3

**User Story:** As a project manager, I want to organize work into projects with proper access control, so that different teams can work on separate initiatives securely.

#### Acceptance Criteria

1. WHEN a project is created THEN the system SHALL store `name`, `description`, `private` flag, and optional `notes`
2. WHEN a project is archived THEN the system SHALL set `archived_at` timestamp
3. WHEN users are assigned to projects THEN the system SHALL maintain many-to-many relationships via association table
4. WHEN project names are queried THEN the system SHALL enforce uniqueness via database index

### Requirement 4

**User Story:** As a system administrator, I want to support multiple operating systems for agents, so that the system can work across different platforms.

#### Acceptance Criteria

1. WHEN an operating system is defined THEN the system SHALL store `name` (windows/linux/darwin) and `cracker_command`
2. WHEN operating system data is accessed THEN the system SHALL enforce enum values via Pydantic and database constraints
3. WHEN operating system names are queried THEN the system SHALL use unique index for performance

### Requirement 5

**User Story:** As an agent operator, I want comprehensive agent management with state tracking and device information, so that I can monitor and control distributed cracking resources.

#### Acceptance Criteria

1. WHEN an agent registers THEN the system SHALL store identity fields: `client_signature`, `host_name`, `custom_label`
2. WHEN an agent authenticates THEN the system SHALL store `token`, `last_seen_at`, `last_ipaddress`
3. WHEN agent state changes THEN the system SHALL track `state` (pending/active/error/offline/disabled) and `enabled` flag
4. WHEN agent configuration is updated THEN the system SHALL store `advanced_configuration` as JSON
5. WHEN agent devices are registered THEN the system SHALL store `devices` array with type, model, hash rate metadata
6. WHEN agents are assigned to projects THEN the system SHALL maintain many-to-many relationships
7. WHEN agent data is queried THEN the system SHALL use indexes on `token`, `state`, and `custom_label`

### Requirement 6

**User Story:** As a system administrator, I want comprehensive error tracking for agents and tasks, so that I can diagnose and resolve issues effectively.

#### Acceptance Criteria

1. WHEN an agent error occurs THEN the system SHALL store `message`, `severity`, `error_code`, and `metadata` as JSON
2. WHEN errors are created THEN the system SHALL automatically populate `created_at` and `updated_at` timestamps
3. WHEN errors are queried THEN the system SHALL use indexes on `agent_id` and `task_id` for performance
4. WHEN errors are associated THEN the system SHALL maintain relationships to `agent_id` and `task_id`

### Requirement 7

**User Story:** As a security analyst, I want to configure complex password cracking attacks with various modes and parameters, so that I can efficiently crack different types of hashes.

#### Acceptance Criteria

1. WHEN an attack is created THEN the system SHALL store `name`, `description`, `state`, and `hash_type` enum
2. WHEN attack mode is configured THEN the system SHALL store `attack_mode` enum value
3. WHEN mask attacks are configured THEN the system SHALL store `mask`, `increment_mode`, `increment_minimum`, `increment_maximum`
4. WHEN performance tuning is needed THEN the system SHALL store `optimized`, `workload_profile`, `slow_candidate_generators`
5. WHEN Markov chains are configured THEN the system SHALL store `disable_markov`, `classic_markov`, `markov_threshold`
6. WHEN rules are applied THEN the system SHALL store `left_rule`, `right_rule`
7. WHEN custom charsets are used THEN the system SHALL store `custom_charset_1`, `custom_charset_2`, `custom_charset_3`, `custom_charset_4`
8. WHEN attack scheduling is needed THEN the system SHALL store `priority`, `start_time`, `end_time`
9. WHEN attacks are queried THEN the system SHALL use indexes on `campaign_id` and `state`

### Requirement 8

**User Story:** As an agent operator, I want detailed task tracking with progress monitoring, so that I can monitor the execution of distributed cracking work.

#### Acceptance Criteria

1. WHEN a task is created THEN the system SHALL store `state` and `stale` flag
2. WHEN task execution begins THEN the system SHALL store `start_date` and track `end_date` when completed
3. WHEN task completes THEN the system SHALL set `completed_at` timestamp
4. WHEN task progress is updated THEN the system SHALL store `progress_percent` and `progress_keyspace`
5. WHEN task results are available THEN the system SHALL store `result_json` with structured output
6. WHEN tasks are queried THEN the system SHALL use indexes on `agent_id`, `state`, and `completed_at`
7. WHEN tasks are associated THEN the system SHALL maintain relationships to `agent_id` and `attack_id`

### Requirement 9

**User Story:** As a developer, I want all models to follow consistent patterns and validation rules, so that the codebase is maintainable and reliable.

#### Acceptance Criteria

1. WHEN any model is defined THEN the system SHALL use Pydantic v2 for schema validation
2. WHEN enum fields are used THEN the system SHALL enforce validation in both Pydantic schemas and SQL constraints
3. WHEN models are created THEN the system SHALL use SQLAlchemy async ORM with Alembic for migrations
4. WHEN database operations are performed THEN the system SHALL use async patterns consistently
5. WHEN model relationships are defined THEN the system SHALL use proper foreign key constraints and indexes
