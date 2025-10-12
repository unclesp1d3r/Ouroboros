# Requirements Document

## Introduction

The Phase 5 Task Distribution System is a critical component of Ouroboros that manages the distribution of password cracking workloads across available agents in the network. This system transforms high-level campaigns and attacks into discrete, executable tasks that can be efficiently distributed to agents based on their capabilities and availability. The system ensures optimal resource utilization while maintaining campaign priorities and handling agent failures gracefully.

## Requirements

### Requirement 1

**User Story:** As a campaign manager, I want the system to automatically break down attacks into appropriately sized tasks so that work can be distributed efficiently across available agents.

#### Acceptance Criteria

1. WHEN an attack is ready for execution THEN the system SHALL calculate the total keyspace for the attack
2. WHEN the total keyspace is calculated THEN the system SHALL divide it into tasks based on agent benchmark data and availability
3. WHEN creating tasks THEN the system SHALL ensure each task represents a manageable workload for the target agent
4. WHEN an agent has higher benchmark scores THEN the system SHALL assign larger keyspace chunks to that agent
5. WHEN an agent has lower benchmark scores THEN the system SHALL assign smaller keyspace chunks to that agent
6. WHEN no agents are available THEN the system SHALL queue tasks for future assignment

### Requirement 2

**User Story:** As a system administrator, I want campaigns to be executed in priority order so that critical cracking operations are completed first.

#### Acceptance Criteria

1. WHEN multiple campaigns are ready for execution THEN the system SHALL sort them by priority level
2. WHEN campaigns have equal priority THEN the system SHALL sort attacks within campaigns by their defined order
3. WHEN a higher priority campaign becomes available THEN the system SHALL preempt lower priority tasks if resources are constrained
4. WHEN a campaign is paused THEN the system SHALL stop creating new tasks for that campaign
5. WHEN a campaign is resumed THEN the system SHALL continue task creation from where it left off

### Requirement 3

**User Story:** As an agent operator, I want agents to receive tasks automatically when they become available so that compute resources are utilized efficiently.

#### Acceptance Criteria

1. WHEN an agent sends a heartbeat THEN the system SHALL check for available tasks matching the agent's capabilities
2. WHEN suitable tasks are available THEN the system SHALL assign the highest priority task to the agent
3. WHEN an agent requests work THEN the system SHALL provide task payloads with all necessary execution parameters
4. WHEN an agent is assigned a task THEN the system SHALL mark the task as dispatched and track the assignment
5. WHEN an agent completes a task THEN the system SHALL update the task status and collect results

### Requirement 4

**User Story:** As a campaign manager, I want the system to handle agent failures gracefully so that work continues even when agents become unavailable.

#### Acceptance Criteria

1. WHEN an agent fails to send heartbeat within the timeout period THEN the system SHALL mark the agent as unavailable
2. WHEN an agent becomes unavailable THEN the system SHALL reassign its running tasks to other available agents
3. WHEN a task fails multiple times THEN the system SHALL mark it as failed and log the error details
4. WHEN an agent reconnects after failure THEN the system SHALL reassess its task assignments and capabilities
5. WHEN no agents are available for a task type THEN the system SHALL queue the task until suitable agents become available

### Requirement 5

**User Story:** As a campaign manager, I want to monitor task execution in real-time so that I can track progress and identify issues quickly.

#### Acceptance Criteria

1. WHEN tasks are created THEN the system SHALL track their lifecycle states (queued, dispatched, running, completed, failed)
2. WHEN task states change THEN the system SHALL update the database and notify relevant monitoring systems
3. WHEN agents report progress THEN the system SHALL update task completion percentages
4. WHEN tasks complete THEN the system SHALL collect and validate results before marking them as finished
5. WHEN tasks fail THEN the system SHALL log error details and determine if retry is appropriate

### Requirement 6

**User Story:** As a system administrator, I want to control campaign execution through the web interface so that I can manage operations effectively.

#### Acceptance Criteria

1. WHEN I pause a campaign THEN the system SHALL stop creating new tasks for that campaign
2. WHEN I resume a paused campaign THEN the system SHALL continue task creation and distribution
3. WHEN I stop a campaign THEN the system SHALL cancel all pending tasks and notify agents to stop running tasks
4. WHEN I view campaign status THEN the system SHALL display real-time task distribution and completion statistics
5. WHEN agents are working on stopped campaigns THEN the system SHALL notify them that their tasks are no longer needed

### Requirement 7

**User Story:** As an agent, I want to receive secure task payloads with all necessary information so that I can execute cracking operations correctly.

#### Acceptance Criteria

1. WHEN an agent requests a task THEN the system SHALL provide a complete task payload including attack parameters
2. WHEN providing task payloads THEN the system SHALL include keyspace boundaries, hash list data, and resource references
3. WHEN sending task data THEN the system SHALL ensure all communication is authenticated and encrypted
4. WHEN an agent receives a task THEN the system SHALL provide presigned URLs for downloading required resources
5. WHEN task parameters are invalid THEN the system SHALL reject the task and log the validation error

### Requirement 8

**User Story:** As a campaign manager, I want the system to optimize task distribution based on agent capabilities so that work is completed as efficiently as possible.

#### Acceptance Criteria

1. WHEN distributing tasks THEN the system SHALL consider agent benchmark data for the specific hash type
2. WHEN an agent has no benchmark data THEN the system SHALL assign a conservative default workload
3. WHEN multiple agents are available THEN the system SHALL distribute tasks to maximize overall throughput
4. WHEN an agent consistently underperforms THEN the system SHALL adjust future task sizes for that agent
5. WHEN new agents join THEN the system SHALL incorporate them into the distribution algorithm immediately

### Requirement 9

**User Story:** As a system administrator, I want the system to implement advanced task scheduling with WorkSlice distribution so that keyspace can be divided efficiently across agents.

#### Acceptance Criteria

1. WHEN an attack is submitted THEN the system SHALL create a TaskPlan with precomputed WorkSlice divisions
2. WHEN calculating WorkSlices THEN the system SHALL use hashcat's --skip and --limit parameters for precise keyspace control
3. WHEN distributing WorkSlices THEN the system SHALL assign slices based on agent scoring that considers hashrate benchmarks and reliability
4. WHEN an agent requests work THEN the system SHALL provide the best-matched WorkSlice with appropriate lease duration
5. WHEN a WorkSlice lease expires THEN the system SHALL automatically reclaim and reassign the work to another agent
6. WHEN agents report thermal throttling THEN the system SHALL reduce their slice assignments and scoring priority

### Requirement 10

**User Story:** As an agent operator, I want agents to provide real-time status streaming so that the server can monitor progress and make informed scheduling decisions.

#### Acceptance Criteria

1. WHEN an agent is executing a task THEN it SHALL parse hashcat's --status-json output and stream structured telemetry
2. WHEN streaming status THEN the agent SHALL include slice progress, crack results, device temperatures, and guessrate data
3. WHEN the server receives status updates THEN it SHALL update real-time dashboards and progress tracking
4. WHEN an agent reports overheating or throttling THEN the system SHALL adjust future task assignments accordingly
5. WHEN status streaming detects performance degradation THEN the system SHALL consider slice reassignment

### Requirement 11

**User Story:** As a system administrator, I want the system to implement intelligent backoff and load smoothing so that agent coordination is efficient and doesn't overload the server.

#### Acceptance Criteria

1. WHEN an agent is overloading the system THEN the server SHALL respond with backoff_seconds to instruct the agent to wait
2. WHEN agents initialize THEN they SHALL use randomized sync intervals to prevent heartbeat synchronization spikes
3. WHEN the server detects high load THEN it SHALL implement backoff signals to reduce agent request frequency
4. WHEN agents receive backoff signals THEN they SHALL respect the delay with appropriate jitter to avoid herding effects
5. WHEN system load normalizes THEN the server SHALL reduce or eliminate backoff requirements

### Requirement 12

**User Story:** As a campaign manager, I want the system to track agent reliability and failure patterns so that unreliable agents don't impact campaign success.

#### Acceptance Criteria

1. WHEN agents complete or fail tasks THEN the system SHALL track success_count, fail_count, and timeout_count per agent
2. WHEN calculating agent reliability THEN the system SHALL derive a rolling reliability score from historical performance
3. WHEN assigning tasks THEN the system SHALL use reliability scores to prioritize stable agents over flaky ones
4. WHEN an agent shows consistent failure patterns THEN the system SHALL reduce its task assignment priority
5. WHEN displaying agent status THEN the system SHALL show reliability indicators (Stable, Intermittent, Flaky)

### Requirement 13

**User Story:** As a campaign manager, I want the system to support incremental and hybrid attack modes so that complex attack strategies can be executed efficiently.

#### Acceptance Criteria

1. WHEN an incremental attack is configured THEN the system SHALL create KeyspacePhase objects for each mask length
2. WHEN executing incremental attacks THEN the system SHALL complete phases in order and track progress per phase
3. WHEN a hybrid attack is configured THEN the system SHALL calculate the multiplicative keyspace (dictionary × mask)
4. WHEN distributing hybrid attack tasks THEN the system SHALL use --skip and --limit parameters normally across the combined keyspace
5. WHEN displaying progress THEN the system SHALL show per-phase progress bars for incremental attacks

### Requirement 14

**User Story:** As a campaign manager, I want the system to implement intelligent attack strategies and feedback loops so that cracking effectiveness improves over time.

#### Acceptance Criteria

1. WHEN passwords are cracked THEN the system SHALL analyze them to derive new rules, masks, and dictionary candidates
2. WHEN generating attack plans THEN the system SHALL use historical crack data to prioritize high-success strategies
3. WHEN attacks complete THEN the system SHALL update project-specific Markov models and learned rules
4. WHEN configuring new campaigns THEN the system SHALL suggest attack strategies based on similar historical campaigns
5. WHEN slice performance varies significantly THEN the system SHALL adapt future slice sizing and distribution

### Requirement 15

**User Story:** As an agent, I want to implement self-governance and fault recovery so that I can operate autonomously and recover from failures gracefully.

#### Acceptance Criteria

1. WHEN executing tasks THEN the agent SHALL monitor device temperatures and adjust workload profiles automatically
2. WHEN the agent detects overheating THEN it SHALL self-throttle by reducing hashcat workload parameters
3. WHEN the agent crashes during task execution THEN it SHALL write checkpoint data to enable recovery
4. WHEN the agent restarts THEN it SHALL upload checkpoint data to the server for slice recovery assessment
5. WHEN environmental conditions degrade THEN the agent SHALL report status and request appropriate task adjustments

### Requirement 16

**User Story:** As a campaign manager, I want the system to support DAG-based campaign planning so that complex multi-phase attack strategies can be automated.

#### Acceptance Criteria

1. WHEN creating campaigns THEN the system SHALL support defining attack flows as directed acyclic graphs (DAGs)
2. WHEN executing DAG campaigns THEN the system SHALL progress through phases based on success criteria and dependencies
3. WHEN a DAG phase succeeds THEN the system SHALL automatically trigger dependent phases and promote successful results
4. WHEN DAG phases fail consistently THEN the system SHALL skip or modify subsequent phases based on configured rules
5. WHEN displaying DAG campaigns THEN the system SHALL show phase progress, dependencies, and success attribution
