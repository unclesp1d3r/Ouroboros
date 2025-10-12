# Requirements Document

## Introduction

This specification defines the requirements for completing agent management functionality and implementing comprehensive cross-component integration workflows in Ouroboros. This feature set represents the final integration step for Phase 3, ensuring all components work together seamlessly while providing complete agent administrative capabilities.

The system must provide comprehensive agent management including registration, monitoring, administration, and performance tracking, while ensuring all components integrate properly through end-to-end workflows. This includes robust error handling, security measures, and comprehensive testing coverage.

## Requirements

### Requirement 1: Complete Agent Registration Workflow

**User Story:** As a system administrator, I want to register new agents with proper configuration and security tokens, so that I can efficiently onboard computational resources into the Ouroboros network.

#### Acceptance Criteria

1. WHEN I access the agent registration interface THEN the system SHALL display a modal dialog with agent registration form using Shadcn-Svelte components
2. WHEN I fill out the registration form THEN the system SHALL require an agent label (custom_label) and project assignment toggles with at least one project selected
3. WHEN I submit a valid registration form THEN the system SHALL generate an agent token in format `csa_<agent_id>_<random_string>`
4. WHEN an agent token is generated THEN the system SHALL display it once with copy functionality and security warning that it won't be shown again
5. WHEN I assign projects to an agent THEN the system SHALL provide multi-toggle interface showing all available projects with clear permission context
6. WHEN I submit invalid registration data THEN the system SHALL provide real-time validation with clear error messaging
7. WHEN registration is successful THEN the system SHALL provide confirmation and guidance for agent configuration with the generated token
8. WHEN I use quick registration THEN the system SHALL provide streamlined workflow with sensible defaults for common configurations

### Requirement 2: Comprehensive Agent Details Modal

**User Story:** As a system administrator, I want to view and manage detailed agent information through a comprehensive interface, so that I can effectively monitor and control agent behavior and performance.

#### Acceptance Criteria

1. WHEN I open agent details THEN the system SHALL display a 5-tab modal (Settings, Hardware, Performance, Log, Capabilities) using Shadcn-Svelte tabs
2. WHEN I view agent display name THEN the system SHALL use `agent.custom_label or agent.host_name` fallback pattern throughout the interface
3. WHEN I access the Settings tab THEN the system SHALL provide editable controls for agent label, enabled toggle, update interval (defaulting to random 1-15 seconds), native hashcat toggle, additional hash types toggle, project assignments, and read-only system info (OS, IP, client signature, agent token)
4. WHEN I access the Hardware tab THEN the system SHALL display individual device toggles from `Agent.devices` list with backend device management, hardware acceleration settings, temperature abort thresholds, OpenCL device types, and backend toggles (CUDA, OpenCL, HIP, Metal)
5. WHEN I change hardware settings during active tasks THEN the system SHALL prompt with options: apply immediately, apply to next task, or cancel
6. WHEN I access the Performance tab THEN the system SHALL show 8-hour line charts of guess rates per device using `DeviceStatus.speed` and individual device cards with donut charts for utilization and temperature display
7. WHEN I access the Logs tab THEN the system SHALL display chronological `AgentError` entries with color-coded severity, rich context (message, error code, task links), expandable JSON details, and filtering by severity/time/task
8. WHEN I access the Capabilities tab THEN the system SHALL show benchmark table with columns for toggle/Hash ID/Name/Speed (in SI units)/Category, expandable rows for per-device breakdowns, search/filter functionality, last benchmark date caption, and rebenchmark trigger button
9. WHEN hardware info is unavailable THEN the system SHALL show graceful degradation with gray placeholders and clear messaging about pending hardware detection

### Requirement 3: Agent List Display and Monitoring

**User Story:** As a system user, I want to view all agents in a comprehensive list with real-time status information, so that I can monitor the health and activity of the computational network.

#### Acceptance Criteria

1. WHEN I view the agent list THEN the system SHALL display a table with columns for "Agent Name and OS", "Status", "Temperature in Celsius", "Utilization" (average of enabled devices from most recent `DeviceStatus`), "Current Attempts per Second", "Average Attempts per Second" (over last minute), and "Current Job" (Project/Campaign/Attack condensed)
2. WHEN I view agent status THEN the system SHALL use data from `DeviceStatus`, `TaskStatus`, and `HashcatGuess` objects from the Agent API v1 specification
3. WHEN I have admin privileges THEN the system SHALL show a gear icon menu with options to disable agent or view details
4. WHEN I am a non-admin user THEN the system SHALL show all agent information but hide administrative controls
5. WHEN I view current job information THEN the system SHALL display Project name, Campaign, and Attack name in condensed format for quick identification
6. WHEN agents report status updates THEN the system SHALL update the display in real-time without page refresh

### Requirement 4: Agent Administration Functions

**User Story:** As a system administrator, I want to perform administrative actions on agents, so that I can maintain proper agent lifecycle management and system health.

#### Acceptance Criteria

1. WHEN I have admin privileges THEN the system SHALL provide agent restart command functionality with confirmation
2. WHEN I deactivate an agent THEN the system SHALL require confirmation, show impact assessment, and prevent new task assignments while keeping agent alive
3. WHEN I toggle device settings THEN the system SHALL provide individual GPU/CPU enable/disable controls with task impact warnings and state-aware prompting
4. WHEN I trigger agent benchmarks THEN the system SHALL set agent state to `AgentState.pending`, provide progress feedback, and update results when completed
5. WHEN I delete an agent THEN the system SHALL require confirmation, display comprehensive impact assessment including active tasks and project assignments, and log the deletion
6. WHEN I perform admin actions THEN the system SHALL validate admin permissions, log all administrative activities, and provide clear feedback on action results

### Requirement 5: End-to-End Campaign Workflows

**User Story:** As a campaign manager, I want to create and execute complete campaigns from start to finish, so that I can efficiently manage password cracking operations across the entire system.

#### Acceptance Criteria

1. WHEN I create a campaign THEN the system SHALL support complete workflow from creation through execution to completion with real-time status updates
2. WHEN I create multi-attack campaigns THEN the system SHALL support DAG sequencing with dependency management and attack reordering capabilities
3. WHEN I manage attacks in campaigns THEN the system SHALL provide toolbar with add attack button, context menus with Remove/Move Up/Move Down/Move To Top/Move To Bottom/Duplicate/Edit options, and table view with Attack Type/Length/Settings/Passwords to Check/Complexity/Comments columns
4. WHEN I upload resources THEN the system SHALL integrate them immediately into attack editor dropdowns with searchable selection and usage tracking
5. WHEN I monitor campaigns THEN the system SHALL provide real-time progress tracking, agent assignment visibility, and task distribution monitoring through completion
6. WHEN campaigns complete THEN the system SHALL provide results export, analysis capabilities, and campaign template save/load functionality in JSON format
7. WHEN I start/stop campaigns THEN the system SHALL provide clear start/stop controls that make campaigns available for agent task assignment
8. WHEN I edit running attacks THEN the system SHALL warn about impact, require confirmation, and reset attack to pending state for restart

### Requirement 6: Cross-Component Integration

**User Story:** As a system user, I want all components to work together seamlessly, so that I can perform complex workflows without encountering integration issues.

#### Acceptance Criteria

1. WHEN I create resources THEN the system SHALL immediately populate them in attack editor dropdowns with searchable selection, entry counts, and last modified sorting
2. WHEN I register agents THEN the system SHALL automatically assign tasks based on benchmark capabilities and project permissions
3. WHEN I create users THEN the system SHALL support complete project assignment workflows with proper permission inheritance
4. WHEN I switch projects THEN the system SHALL maintain proper data context updates across all components while preserving sensitive campaign visibility rules
5. WHEN multiple users collaborate THEN the system SHALL handle permissions correctly across all workflows with proper access control validation
6. WHEN I perform resource operations THEN the system SHALL track usage across attacks, validate dependencies, and support both predefined and ephemeral resources
7. WHEN I use attack editor THEN the system SHALL provide dynamic keyspace estimation and complexity scoring for unsaved attacks
8. WHEN I work with campaign templates THEN the system SHALL support JSON-based save/load functionality for attacks and entire campaigns
9. WHEN agents execute tasks THEN the system SHALL display current job information showing Project/Campaign/Attack names in condensed format

### Requirement 7: Error Recovery and Edge Case Handling

**User Story:** As a system user, I want the system to handle errors gracefully and recover from edge cases, so that I can continue working even when problems occur.

#### Acceptance Criteria

1. WHEN network failures occur THEN the system SHALL provide graceful recovery with user feedback
2. WHEN I upload large files THEN the system SHALL handle interruptions with resume capability
3. WHEN concurrent modifications occur THEN the system SHALL resolve conflicts appropriately
4. WHEN I refresh the browser during operations THEN the system SHALL maintain operation state
5. WHEN sessions expire during long operations THEN the system SHALL handle expiry while maintaining user context
6. WHEN errors occur THEN the system SHALL display helpful error pages with recovery options

### Requirement 8: Advanced UI/UX Features

**User Story:** As a system user, I want consistent, accessible, and responsive interfaces, so that I can efficiently use the system regardless of my device or accessibility needs.

#### Acceptance Criteria

1. WHEN I interact with data tables THEN the system SHALL provide consistent sorting and pagination models
2. WHEN I view progress indicators THEN the system SHALL display accurate progress bars with smooth animations
3. WHEN I view charts and metrics THEN the system SHALL use consistent Catppuccin Macchiato theme visualization
4. WHEN I encounter empty states THEN the system SHALL provide helpful guidance and next steps
5. WHEN errors occur THEN the system SHALL display clear error states with recovery options
6. WHEN I use complex features THEN the system SHALL implement progressive disclosure to manage complexity
7. WHEN I navigate with keyboard or screen reader THEN the system SHALL provide full accessibility compliance
8. WHEN I use different devices THEN the system SHALL provide responsive design with appropriate touch targets

### Requirement 9: Theme System Implementation

**User Story:** As a system user, I want to customize the interface appearance and have my preferences persist, so that I can work in my preferred visual environment.

#### Acceptance Criteria

1. WHEN I toggle dark mode THEN the system SHALL switch themes without page refresh and persist the preference
2. WHEN I change themes THEN the system SHALL apply changes immediately across all components
3. WHEN I return to the system THEN the system SHALL remember my theme preference across sessions
4. WHEN I use the system THEN the system SHALL maintain consistent Catppuccin Macchiato theme throughout
5. WHEN components render THEN the system SHALL ensure all components are theme-aware
6. WHEN I have system theme preferences THEN the system SHALL detect and auto-switch based on system settings

### Requirement 10: Enhanced Security Measures

**User Story:** As a security-conscious administrator, I want comprehensive security protections throughout the system, so that I can ensure the system is protected against common threats.

#### Acceptance Criteria

1. WHEN I access sensitive resources THEN the system SHALL enforce proper access control
2. WHEN I submit forms THEN the system SHALL protect against CSRF attacks
3. WHEN I input data THEN the system SHALL validate and sanitize all input to prevent injection attacks
4. WHEN I upload files THEN the system SHALL perform security checks to prevent malicious file execution
5. WHEN I access API endpoints THEN the system SHALL properly validate authorization
6. WHEN I use the system THEN the system SHALL maintain secure session management while providing good user experience

### Requirement 11: Comprehensive Testing Coverage

**User Story:** As a developer, I want comprehensive test coverage for all functionality, so that I can ensure the system works correctly and regressions are caught early.

#### Acceptance Criteria

1. WHEN I run mocked E2E tests THEN the system SHALL execute fast tests without backend requirements
2. WHEN I run full E2E tests THEN the system SHALL execute complete integration tests with real backend
3. WHEN I test agent functionality THEN the system SHALL cover registration, details modal, and administration
4. WHEN I test integration workflows THEN the system SHALL cover end-to-end campaign and cross-component scenarios
5. WHEN I test error handling THEN the system SHALL cover network failures, file handling, and user interaction edge cases
6. WHEN I test UI/UX features THEN the system SHALL cover data display components and theme system functionality
7. WHEN I test security measures THEN the system SHALL validate CSRF protection, input validation, and authorization
8. WHEN tests execute THEN the system SHALL follow existing test structure and naming conventions

### Requirement 12: Agent Hardware Configuration Management

**User Story:** As a system administrator, I want to configure agent hardware settings and backend options, so that I can optimize performance and control which computational resources are used.

#### Acceptance Criteria

1. WHEN I configure backend devices THEN the system SHALL store device names as `Agent.devices` list and enabled devices as comma-separated integers in `backend_device` field
2. WHEN I set hardware limits THEN the system SHALL support temperature abort thresholds that translate to hashcat `--hwmon-temp-abort` parameter
3. WHEN I configure OpenCL settings THEN the system SHALL support OpenCL device type selection that maps to `--opencl-device-types` hashcat parameter
4. WHEN I toggle backend support THEN the system SHALL provide controls for CUDA, OpenCL, HIP, and Metal that map to respective `--backend-ignore-*` hashcat parameters
5. WHEN I modify hardware configuration THEN the system SHALL update the `AdvancedAgentConfiguration` object according to Agent API v1 specification
6. WHEN hardware info is not yet available THEN the system SHALL display placeholder text and gray out controls until agent reports `--backend-info` data

### Requirement 13: Agent Performance Monitoring and Visualization

**User Story:** As a system administrator, I want to monitor agent performance through detailed visualizations, so that I can identify performance issues and optimize resource utilization.

#### Acceptance Criteria

1. WHEN I view performance charts THEN the system SHALL display line charts showing `DeviceStatus.speed` over 8-hour windows with separate lines for each backend device
2. WHEN I view device utilization THEN the system SHALL show donut charts for each device displaying current utilization percentage and temperature from most recent `DeviceStatus`
3. WHEN temperature is unmonitored THEN the system SHALL display appropriate messaging for devices reporting temperature value of -1
4. WHEN I view performance data THEN the system SHALL update in real-time as new `TaskStatus` records are received from agents
5. WHEN I analyze performance trends THEN the system SHALL provide historical context and comparative analysis across devices and time periods
6. WHEN performance data is unavailable THEN the system SHALL show appropriate loading states and error messaging

### Requirement 14: Attack Editor Integration and Workflow

**User Story:** As a campaign manager, I want to create and edit attacks through an intuitive modal interface that integrates seamlessly with campaign management, so that I can efficiently configure complex attack sequences.

#### Acceptance Criteria

1. WHEN I open attack editor THEN the system SHALL display modal interface with dynamic keyspace estimation and complexity scoring that updates as I modify settings
2. WHEN I configure dictionary attacks THEN the system SHALL provide character length controls, searchable wordlist dropdown with entry counts and last modified sorting, modifier buttons for case/character order/substitution changes, rules list selection, "Previous Passwords" option, and ability to add custom words with "Add word" button
3. WHEN I configure mask attacks THEN the system SHALL provide mask input with "Add mask" button for multiple masks, validation for invalid characters, and X button to remove mask entries
4. WHEN I configure brute force attacks THEN the system SHALL provide character type checkboxes (Lowercase/Uppercase/Numbers/Symbols/Space) that generate appropriate masks and custom character sets
5. WHEN I edit running or exhausted attacks THEN the system SHALL warn about impact, require confirmation, and reset attack to pending state for restart
6. WHEN I save attack configurations THEN the system SHALL support JSON-based export for individual attacks and integration with campaign template system
7. WHEN I use resource selection THEN the system SHALL populate dropdowns from uploaded resources with immediate availability after resource creation
8. WHEN I estimate attack complexity THEN the system SHALL provide real-time keyspace calculation and complexity scoring for unsaved attacks through backend estimation endpoints

### Requirement 15: Dashboard Integration and Real-Time Monitoring

**User Story:** As a system user, I want a comprehensive dashboard that shows real-time system status and agent activity, so that I can monitor the overall health and performance of the Ouroboros network.

#### Acceptance Criteria

1. WHEN I view the dashboard THEN the system SHALL display operational status cards for Active Agents, Running Tasks, Recently Cracked Hashes, and Resource Usage with real-time SSE updates
2. WHEN I view campaign overview THEN the system SHALL show all campaigns across the system with sensitive campaigns anonymized unless I have access, sorted by Running campaigns first then most recently updated
3. WHEN I view campaign rows THEN the system SHALL display campaign name, keyspace-weighted progress bar, state badge (Running=purple, Completed=green, Error=red, Paused=gray), summary with attack count/running/ETA, and expand functionality
4. WHEN I expand campaigns THEN the system SHALL show attack rows with type/config summary/progress bar/ETA and gear icon options, attached agent count and status
5. WHEN I click Active Agents card THEN the system SHALL open slide-out Sheet with agent cards showing label/status badge/last seen/current task/guess rate/sparkline trend
6. WHEN hashes are cracked THEN the system SHALL display live toast notifications with rate limiting and batch grouping, containing plaintext/attack/hashlist/timestamp
7. WHEN I have admin privileges THEN the system SHALL show agent expand buttons in the Sheet for detailed configuration access
8. WHEN SSE connections fail THEN the system SHALL show stale data indicators, manual refresh options, and clear error messaging with user-controlled recovery

### Requirement 16: System Health Monitoring (Admin Only)

**User Story:** As a system administrator, I want to monitor the health of all backend services and system components, so that I can proactively identify and resolve infrastructure issues.

#### Acceptance Criteria

1. WHEN I access system health THEN the system SHALL display status cards for MinIO, Redis, PostgreSQL, and Agents with color-coded health indicators (🟢 Healthy, 🟡 Degraded, 🔴 Unreachable)
2. WHEN I view MinIO status THEN the system SHALL show latency, errors, storage utilization using `/minio/health/live` endpoint and `minio-py` client
3. WHEN I view Redis status THEN the system SHALL show command latency, memory usage, active connections using `redis.asyncio.Redis` with `info()` commands
4. WHEN I view PostgreSQL status THEN the system SHALL show query latency, connection pool usage, replication lag using SQLAlchemy async sessions and system views
5. WHEN I view agent health THEN the system SHALL show online/offline status, last seen timestamps, current tasks, and guess rates
6. WHEN services are unreachable THEN the system SHALL display appropriate error states with skeleton loaders and clear messaging
7. WHEN I have admin privileges THEN the system SHALL show additional diagnostic data including detailed metrics, logs, and advanced system statistics
8. WHEN metrics update THEN the system SHALL use SSE for real-time updates every 5-10 seconds with server-side caching for expensive queries

### Requirement 17: Agent Benchmark Compatibility and Task Assignment

**User Story:** As a system administrator, I want agents to be automatically assigned tasks based on their benchmark capabilities, so that work is distributed efficiently to compatible hardware.

#### Acceptance Criteria

1. WHEN agents register THEN the system SHALL collect hashcat benchmark results for each supported hash type with speed measurements in hashes per second
2. WHEN I view agent capabilities THEN the system SHALL display benchmark results in table format with Hash ID, Name, Speed (in SI units), Category, and per-device breakdowns
3. WHEN tasks are assigned THEN the system SHALL use `can_handle_hash_type(agent, hash_type_id)` logic to verify agent compatibility based on benchmark data
4. WHEN agents request tasks THEN the system SHALL assign pending tasks only to agents with benchmark support for the task's hash type
5. WHEN agents lack benchmark data THEN the system SHALL flag them as ineligible for task assignment until benchmarks are completed
6. WHEN I trigger rebenchmarks THEN the system SHALL set agent state to `AgentState.pending` and update benchmark results when completed
7. WHEN benchmark data is stored THEN the system SHALL index by hash type for efficient compatibility checking
8. WHEN multiple agents are available THEN the system SHALL consider benchmark performance for intelligent load balancing

### Requirement 18: Progress Calculation and State Management

**User Story:** As a campaign manager, I want accurate progress tracking across campaigns, attacks, and tasks, so that I can monitor completion status and estimate remaining time.

#### Acceptance Criteria

1. WHEN I view task progress THEN the system SHALL calculate completion based on `progress_percent == 100` or `result_submitted` status
2. WHEN I view attack progress THEN the system SHALL calculate completion when all tasks are complete using keyspace-weighted averaging
3. WHEN I view campaign progress THEN the system SHALL calculate completion when all attacks are complete using keyspace-weighted aggregation
4. WHEN progress is calculated THEN the system SHALL use keyspace weighting formula: `weighted_sum = sum((task.progress_percent / 100.0) * task.keyspace_total)` divided by total keyspace
5. WHEN state transitions occur THEN the system SHALL automatically update parent object states based on child completion status
6. WHEN I view progress bars THEN the system SHALL display keyspace-weighted progress that accurately reflects work remaining rather than simple task averaging
7. WHEN tasks have zero keyspace THEN the system SHALL log and exclude them from progress calculations
8. WHEN progress updates occur THEN the system SHALL propagate changes up the hierarchy from task to attack to campaign

### Requirement 19: Keyspace Estimation and Attack Complexity

**User Story:** As a campaign manager, I want accurate keyspace estimation for all attack types, so that I can understand attack complexity and predict completion times.

#### Acceptance Criteria

01. WHEN I configure dictionary attacks THEN the system SHALL estimate keyspace as `wordlist_size * rule_count`
02. WHEN I configure mask attacks THEN the system SHALL estimate keyspace as product of charset lengths per position
03. WHEN I configure incremental mask attacks THEN the system SHALL estimate keyspace as sum of products across length range
04. WHEN I configure combinator attacks THEN the system SHALL estimate keyspace as `left_wordlist_size * right_wordlist_size`
05. WHEN I configure hybrid attacks THEN the system SHALL estimate keyspace as `wordlist_size * mask_keyspace` (mode 6) or `mask_keyspace * wordlist_size` (mode 7)
06. WHEN rules are applied THEN the system SHALL multiply base keyspace by rule count
07. WHEN I view attack complexity THEN the system SHALL display estimated keyspace, complexity score (1-5), and ETA calculations
08. WHEN keyspace is estimated THEN the system SHALL match hashcat's actual candidate space within ±1% accuracy
09. WHEN attacks are created THEN the system SHALL precompute and store `attack.keyspace_total` for use in task distribution and progress reporting
10. WHEN invalid configurations are provided THEN the system SHALL return zero keyspace or raise validation errors

### Requirement 20: Hash Crack Result Aggregation and Tracking

**User Story:** As a system user, I want comprehensive tracking of cracked hashes across campaigns and hash lists, so that I can monitor success rates and export results.

#### Acceptance Criteria

1. WHEN hashes are cracked THEN the system SHALL aggregate counts at hash list level with `hash_items.filter(cracked=True).count()`
2. WHEN I view campaign results THEN the system SHALL display total cracked hashes as sum across all associated hash lists
3. WHEN duplicate crack results are submitted THEN the system SHALL deduplicate to prevent double counting
4. WHEN I view hash list statistics THEN the system SHALL show total hash count and cracked count with percentage
5. WHEN crack results are stored THEN the system SHALL use indexes on `HashItem.cracked` for performance
6. WHEN I export results THEN the system SHALL provide comprehensive crack data with plaintext, attack method, and timestamps
7. WHEN real-time updates occur THEN the system SHALL update crack counts immediately via SSE for live dashboard display
8. WHEN I view historical data THEN the system SHALL track crack timestamps for trend analysis and reporting
