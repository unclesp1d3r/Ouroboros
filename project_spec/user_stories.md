# Ouroboros User Stories

**Version**: 2.0\
**Status**: Draft\
**Author(s)**: UncleSp1d3r\
**Date Created**: 2025-01-07\
**Last Modified**: 2025-01-07

---

## Table of Contents

[TOC]

---

## User Personas

### Red Team Operator (Primary User)

**Role**: Conducts password audits and penetration testing\
**Technical Level**: High\
**Primary Goals**: Efficient password cracking, comprehensive result analysis, operational security\
**Pain Points**: Time constraints, complex campaign management, resource coordination

### Blue Team Analyst

**Role**: Security professional analyzing password patterns\
**Technical Level**: Medium-High\
**Primary Goals**: Password complexity assessment, vulnerability identification, trend analysis\
**Pain Points**: Data interpretation, reporting complexity, limited time for analysis

### Infrastructure Administrator

**Role**: Manages distributed cracking infrastructure\
**Technical Level**: High\
**Primary Goals**: System reliability, performance optimization, resource management\
**Pain Points**: Agent coordination, hardware utilization, system maintenance

### Project Manager

**Role**: Oversees cracking operations and resource allocation\
**Technical Level**: Medium\
**Primary Goals**: Progress tracking, resource optimization, timeline management\
**Pain Points**: Visibility into operations, progress prediction, resource conflicts

---

## Authentication & Access Control

### Story: AC-001 - User Login and Session Management

**As a** Red Team Operator\
**I want to** log into Ouroboros with my username and password\
**So that** I can access my campaigns and maintain session persistence across browser reloads

**Acceptance Criteria:**

- [ ] User can log in with valid username/password combination
- [ ] Session persists across browser reloads and tab closures
- [ ] Invalid login attempts are handled gracefully with clear error messages
- [ ] Session timeout occurs after configurable period of inactivity
- [ ] User can log out explicitly, clearing all session data

**Priority:** High\
**Effort:** 2 points\
**Dependencies:** Backend authentication system

---

### Story: AC-002 - Project Context Selection

**As a** Project Manager\
**I want to** select which project I'm working on when I have access to multiple projects\
**So that** I see only relevant campaigns, resources, and agents for my current work context

**Acceptance Criteria:**

- [ ] User with multiple project access sees project selection interface
- [ ] Project selection filters all subsequent views and data
- [ ] Project context is maintained throughout the session
- [ ] User can switch between projects without logging out
- [ ] Sensitive campaigns are redacted appropriately based on project permissions

**Priority:** High\
**Effort:** 3 points\
**Dependencies:** Multi-project backend implementation

---

## Dashboard & Monitoring

### Story: DM-001 - Real-Time System Overview

**As a** Red Team Operator\
**I want to** see a real-time dashboard showing system status and active operations\
**So that** I can quickly assess current activity and identify any issues requiring attention

**Acceptance Criteria:**

- [ ] Dashboard displays active agents count with online/offline status
- [ ] Running tasks count updates in real-time without page refresh
- [ ] Recently cracked hashes are displayed with timestamps
- [ ] System hash rate shows 8-hour trend with performance indicators
- [ ] All metrics update automatically via Server-Sent Events (SSE)

**Priority:** High\
**Effort:** 5 points\
**Dependencies:** SSE implementation, agent heartbeat system

---

### Story: DM-002 - Campaign Progress Monitoring

**As a** Project Manager\
**I want to** monitor the progress of all active campaigns in a single view\
**So that** I can track completion status and identify campaigns needing attention

**Acceptance Criteria:**

- [ ] Campaign list shows progress bars with percentage completion
- [ ] State icons clearly indicate running, completed, error, and paused campaigns
- [ ] Attack summaries show type, keyspace, and estimated time remaining
- [ ] User can expand campaigns to view attack-level detail
- [ ] Progress updates occur in real-time without manual refresh

**Priority:** High\
**Effort:** 4 points\
**Dependencies:** Campaign state management, real-time updates

---

## Campaign Management

### Story: CM-001 - Campaign Creation Wizard

**As a** Red Team Operator\
**I want to** create a new campaign using a guided wizard interface\
**So that** I can efficiently configure hash lists, metadata, and initial attacks

**Acceptance Criteria:**

- [ ] Wizard guides through hashlist selection (upload or existing)
- [ ] User enters campaign name, description, and sensitivity settings
- [ ] DAG support toggle explains phase-based execution behavior
- [ ] Automatic transition to attack configuration after campaign creation
- [ ] Success confirmation with toast notification

**Priority:** High\
**Effort:** 8 points\
**Dependencies:** File upload system, attack editor

---

### Story: CM-002 - Attack Configuration and Ordering

**As a** Red Team Operator\
**I want to** configure multiple attack strategies within a campaign\
**So that** I can implement comprehensive password cracking methodology

**Acceptance Criteria:**

- [ ] Attack editor supports Dictionary, Mask, and Brute Force attack types
- [ ] Resource dropdowns show available wordlists, rules, masks, and charsets
- [ ] Real-time keyspace estimation with complexity scoring (1-5 dots)
- [ ] Visual DAG ordering with drag-and-drop or up/down controls
- [ ] Attack validation prevents invalid configurations

**Priority:** High\
**Effort:** 10 points\
**Dependencies:** Resource management, keyspace calculation algorithms

---

### Story: CM-003 - Campaign Lifecycle Control

**As a** Red Team Operator\
**I want to** control campaign execution (launch, pause, resume, archive)\
**So that** I can manage resource utilization and respond to changing priorities

**Acceptance Criteria:**

- [ ] Launch button initiates task generation and agent distribution
- [ ] Pause functionality stops task assignment while preserving progress
- [ ] Resume capability restarts paused campaigns from previous state
- [ ] Archive option removes campaigns from active view with confirmation
- [ ] Delete option available only for never-launched campaigns

**Priority:** High\
**Effort:** 6 points\
**Dependencies:** Task scheduling system, state management

---

### Story: CM-004 - Template Import and Export

**As a** Blue Team Analyst\
**I want to** export successful campaign configurations as templates\
**So that** I can reuse proven attack strategies across different engagements

**Acceptance Criteria:**

- [ ] Export button generates JSON template with attack configurations
- [ ] Import functionality validates template format and resource availability
- [ ] Template import pre-fills campaign wizard with saved configuration
- [ ] Resource GUIDs are resolved or user is prompted for replacements
- [ ] Ephemeral resources (inline wordlists/masks) are embedded in templates

**Priority:** Medium\
**Effort:** 5 points\
**Dependencies:** Template schema validation, resource GUID system

---

## Agent Management

### Story: AM-001 - Agent Fleet Overview

**As an** Infrastructure Administrator\
**I want to** view all registered agents with their current status and performance\
**So that** I can monitor system health and identify agents needing attention

**Acceptance Criteria:**

- [ ] Agent list displays name, OS, status badge, temperature, utilization
- [ ] Current task assignment and guess rate are shown for active agents
- [ ] Last seen timestamp indicates connectivity health
- [ ] Status updates occur in real-time via SSE
- [ ] Offline agents are clearly distinguished from active ones

**Priority:** High\
**Effort:** 4 points\
**Dependencies:** Agent heartbeat system, performance metrics collection

---

### Story: AM-002 - Agent Registration and Configuration

**As an** Infrastructure Administrator\
**I want to** register new agents and configure their settings\
**So that** I can integrate new hardware into the distributed cracking system

**Acceptance Criteria:**

- [ ] Agent registration modal provides token and setup instructions
- [ ] Agent detail view shows comprehensive settings and hardware tabs
- [ ] Project assignment controls which campaigns agent can access
- [ ] Hardware configuration allows GPU device enable/disable
- [ ] Benchmark management with capability testing and performance tracking

**Priority:** High\
**Effort:** 7 points\
**Dependencies:** Agent authentication system, hardware detection

---

### Story: AM-003 - Agent Performance Monitoring

**As an** Infrastructure Administrator\
**I want to** monitor agent performance metrics and hardware utilization\
**So that** I can optimize system performance and identify hardware issues

**Acceptance Criteria:**

- [ ] Performance tab shows line charts of guess rates over 8-hour windows
- [ ] Device-specific donut charts display utilization percentages
- [ ] Temperature monitoring with threshold alerts
- [ ] Historical performance data for trend analysis
- [ ] Error log timeline with severity-coded messages

**Priority:** Medium\
**Effort:** 6 points\
**Dependencies:** Performance metrics collection, charting library

---

### Story: AM-004 - Advanced Agent Control

**As an** Infrastructure Administrator\
**I want to** perform administrative actions on agents (restart, disable, configure)\
**So that** I can maintain system health and respond to operational issues

**Acceptance Criteria:**

- [ ] Restart agent functionality with task interruption warning
- [ ] Device disable/enable with immediate or deferred application
- [ ] Agent deactivation with confirmation and impact assessment
- [ ] Hardware configuration changes with task state considerations
- [ ] Bulk operations for multiple agent management

**Priority:** Medium\
**Effort:** 5 points\
**Dependencies:** Agent control API, confirmation workflows

---

## Resource Management

### Story: RM-001 - Resource Library Management

**As a** Blue Team Analyst\
**I want to** upload and organize wordlists, rules, masks, and charsets\
**So that** I can build a comprehensive library of cracking resources

**Acceptance Criteria:**

- [ ] File upload supports drag-and-drop with type detection
- [ ] Resource metadata includes label, description, and sensitivity flags
- [ ] Resource list with search, filtering, and pagination
- [ ] Preview functionality for small files with line counts
- [ ] Project-scoped resources with sharing controls

**Priority:** High\
**Effort:** 6 points\
**Dependencies:** MinIO integration, file type validation

---

### Story: RM-002 - Inline Resource Editing

**As a** Red Team Operator\
**I want to** edit small resource files directly in the web interface\
**So that** I can make quick modifications without downloading and re-uploading files

**Acceptance Criteria:**

- [ ] Edit functionality available for files under 1MB
- [ ] Text editor with syntax highlighting for rule files
- [ ] Real-time validation with error highlighting
- [ ] Save functionality updates file content atomically
- [ ] Larger files show download/re-upload workflow

**Priority:** Medium\
**Effort:** 4 points\
**Dependencies:** File size detection, text editing component

---

### Story: RM-003 - Automated Hash Type Detection

**As a** Red Team Operator\
**I want to** upload hash files and automatically detect the hash type\
**So that** I can quickly configure campaigns without manual hash analysis

**Acceptance Criteria:**

- [ ] Crackable upload interface supports both file upload and text paste
- [ ] name-that-hash integration provides confidence-ranked suggestions
- [ ] Hash type detection handles common formats (shadow, NTLM, etc.)
- [ ] User can override automatic detection if incorrect
- [ ] Preview shows detected hashes and proposed attack configurations

**Priority:** Medium\
**Effort:** 5 points\
**Dependencies:** name-that-hash integration, hash parsing logic

---

## Results and Analysis

### Story: RA-001 - Crack Result Notification and Viewing

**As a** Red Team Operator\
**I want to** receive immediate notifications when hashes are cracked\
**So that** I can quickly assess progress and adjust strategies if needed

**Acceptance Criteria:**

- [ ] Toast notifications appear when hashes are cracked
- [ ] Notification click opens filtered results view
- [ ] Results show plaintext, timestamp, hashlist source, and attack method
- [ ] Export functionality for reporting and documentation
- [ ] Batch notifications for high-volume cracking (>5/second)

**Priority:** High\
**Effort:** 4 points\
**Dependencies:** SSE implementation, results filtering system

---

### Story: RA-002 - Campaign Results Analysis

**As a** Blue Team Analyst\
**I want to** analyze cracking results to identify password patterns and weaknesses\
**So that** I can provide meaningful security recommendations

**Acceptance Criteria:**

- [ ] Results view shows statistics on password complexity and patterns
- [ ] Filtering by attack type, time range, and hash source
- [ ] Export capabilities in multiple formats (CSV, JSON)
- [ ] Pattern analysis showing common passwords and rule effectiveness
- [ ] Integration with learned.rules generation for future attacks

**Priority:** Medium\
**Effort:** 6 points\
**Dependencies:** Results aggregation, pattern analysis algorithms

---

## 🎛️ System Administration

### Story: SA-001 - User and Project Management

**As a** System Administrator\
**I want to** manage user accounts and project assignments\
**So that** I can control system access and maintain proper authorization

**Acceptance Criteria:**

- [ ] User creation with role assignment (admin, project admin, user)
- [ ] Project management with user membership controls
- [ ] Role-based UI elements show only permitted actions
- [ ] Audit logging for user management actions
- [ ] Bulk user operations for efficiency

**Priority:** Medium\
**Effort:** 5 points\
**Dependencies:** Role-based access control system

---

### Story: SA-002 - System Health Monitoring

**As a** System Administrator\
**I want to** monitor the health of all system components\
**So that** I can proactively identify and resolve infrastructure issues

**Acceptance Criteria:**

- [ ] Health dashboard shows PostgreSQL, MinIO, and Redis status
- [ ] Service latency and performance metrics
- [ ] Agent connectivity and heartbeat monitoring
- [ ] Alert configuration for critical system events
- [ ] Diagnostic information for troubleshooting

**Priority:** Medium\
**Effort:** 4 points\
**Dependencies:** Health check endpoints, monitoring infrastructure

---

## Advanced Features

### Story: AF-001 - DAG-Based Attack Execution

**As a** Red Team Operator\
**I want to** configure attack execution phases with dependencies\
**So that** I can implement sophisticated attack strategies that build upon each other

**Acceptance Criteria:**

- [ ] Visual DAG editor with phase groupings
- [ ] Attack ordering with drag-and-drop reordering
- [ ] Phase-based execution prevents later attacks until earlier complete
- [ ] Warning prompts when modifying running campaign DAG
- [ ] Clear visual indication of execution order and dependencies

**Priority:** Low\
**Effort:** 7 points\
**Dependencies:** Task scheduling enhancements, DAG visualization

---

### Story: AF-002 - Learned Rules Integration

**As a** Blue Team Analyst\
**I want to** incorporate learned rules from successful cracks into future attacks\
**So that** I can improve attack efficiency based on previous successes

**Acceptance Criteria:**

- [ ] Automatic learned.rules generation from crack results
- [ ] Rule editor with overlay functionality showing learned patterns
- [ ] Diff-style preview of rule modifications
- [ ] Option to append, replace, or cancel rule overlays
- [ ] Integration with attack configuration for rule application

**Priority:** Low\
**Effort:** 6 points\
**Dependencies:** Rule analysis algorithms, diff visualization

---

## 📱 User Experience

### Story: UX-001 - Responsive Design and Accessibility

**As a** user with disabilities\
**I want to** use Ouroboros with assistive technologies\
**So that** I can participate in password cracking operations regardless of my physical capabilities

**Acceptance Criteria:**

- [ ] WCAG 2.1 AA compliance for all interface elements
- [ ] Keyboard navigation support for all functionality
- [ ] Screen reader compatibility with proper ARIA labels
- [ ] High contrast mode support
- [ ] Mobile-responsive layouts for monitoring on tablets/phones

**Priority:** Medium\
**Effort:** 4 points\
**Dependencies:** Accessibility testing framework

---

### Story: UX-002 - Progressive Enhancement and Offline Capability

**As a** Red Team Operator in an airgapped environment\
**I want to** use Ouroboros without external dependencies\
**So that** I can operate in secure, disconnected networks

**Acceptance Criteria:**

- [ ] All functionality works without JavaScript (progressive enhancement)
- [ ] No external CDN or internet dependencies
- [ ] Local resource caching for improved performance
- [ ] Offline-first design principles throughout application
- [ ] Clear indication when real-time features are unavailable

**Priority:** High\
**Effort:** 3 points\
**Dependencies:** SSR implementation, caching strategy

---

## Integration and Migration

### Story: IM-001 - Agent Compatibility Maintenance

**As an** Infrastructure Administrator with existing agents\
**I want to** migrate to Ouroboros v2 without reconfiguring my agent fleet\
**So that** I can benefit from new features while maintaining operational continuity

**Acceptance Criteria:**

- [ ] All v1 agents connect and operate without modification
- [ ] API compatibility maintained for all agent endpoints
- [ ] Agent authentication and heartbeat systems work identically
- [ ] Task distribution maintains performance characteristics
- [ ] Migration path documentation with rollback procedures

**Priority:** High\
**Effort:** 2 points (already implemented)\
**Dependencies:** V1 API compatibility layer

---

### Story: IM-002 - Data Migration from v1 System

**As a** System Administrator\
**I want to** migrate existing campaigns, resources, and user data from v1 to v2\
**So that** I can preserve historical data and continue existing operations

**Acceptance Criteria:**

- [ ] Migration tools for users, projects, and role assignments
- [ ] Campaign and attack configuration preservation
- [ ] Resource file migration with metadata retention
- [ ] Historical results and audit log preservation
- [ ] Validation tools to verify migration completeness

**Priority:** Medium\
**Effort:** 8 points\
**Dependencies:** Migration tooling development

---

## Story Mapping and Prioritization

### Epic Priority Matrix

| Epic                            | Priority | User Value | Technical Complexity | Dependencies                         |
| ------------------------------- | -------- | ---------- | -------------------- | ------------------------------------ |
| Authentication & Access Control | High     | High       | Medium               | Backend auth system                  |
| Campaign Management             | High     | Very High  | High                 | Resource management, task scheduling |
| Dashboard & Monitoring          | High     | High       | Medium               | SSE, real-time updates               |
| Agent Management                | High     | High       | Medium               | Agent communication protocols        |
| Resource Management             | High     | High       | Medium               | MinIO integration                    |
| Results and Analysis            | Medium   | High       | Low                  | Results aggregation                  |
| System Administration           | Medium   | Medium     | Low                  | RBAC implementation                  |
| Advanced Features               | Low      | Medium     | High                 | DAG visualization, AI integration    |
| User Experience                 | Medium   | Medium     | Medium               | Accessibility framework              |
| Integration and Migration       | High     | High       | Low                  | V1 compatibility (already done)      |

### Release Planning

#### MVP Release (Phases 1-3 Complete)

- Authentication & Access Control (AC-001, AC-002)
- Campaign Management (CM-001, CM-002, CM-003)
- Dashboard & Monitoring (DM-001, DM-002)
- Agent Management (AM-001, AM-002)
- Resource Management (RM-001)
- Results and Analysis (RA-001)

#### Release 1.1 (Phase 4-5)

- Advanced Agent Management (AM-003, AM-004)
- Enhanced Resource Management (RM-002, RM-003)
- Campaign Templates (CM-004)
- System Administration (SA-001, SA-002)

#### Release 2.0 (Phase 6+)

- Advanced Features (AF-001, AF-002)
- Enhanced Analysis (RA-002)
- Full Accessibility (UX-001)
- Migration Tooling (IM-002)

---

## Story Writing Guidelines

### Definition of Ready

- [ ] User persona and role clearly identified
- [ ] Business value and user need articulated
- [ ] Acceptance criteria specific and testable
- [ ] Dependencies identified and documented
- [ ] Effort estimation completed
- [ ] Priority level assigned

### Definition of Done

- [ ] All acceptance criteria met
- [ ] Unit tests written and passing
- [ ] Integration tests covering user workflow
- [ ] Code review completed
- [ ] Documentation updated
- [ ] User acceptance testing completed

---

## Story Lifecycle

```mermaid
graph LR
    Backlog --> Ready
    Ready --> InProgress[In Progress]
    InProgress --> Review
    Review --> Testing
    Testing --> Done
    Review --> InProgress
    Testing --> Review
```

---

## 📈 Metrics and Success Criteria

### User Experience Metrics

- **Task Completion Rate**: >95% of user workflows completed successfully
- **Time to Campaign Launch**: \<5 minutes for standard campaign setup
- **Error Recovery**: \<30 seconds average time to recover from user errors
- **Accessibility Compliance**: 100% WCAG 2.1 AA compliance

### System Performance Metrics

- **Agent Scalability**: Support for 100+ concurrent agents
- **Real-time Update Latency**: \<1 second for SSE event delivery
- **API Response Time**: \<200ms for standard operations
- **Uptime**: 99.9% availability target

### Business Value Metrics

- **Migration Success**: 100% v1 agent compatibility maintained
- **Feature Adoption**: 80% of users utilizing new v2 features within 30 days
- **User Satisfaction**: >90% positive feedback on user experience improvements
- **Operational Efficiency**: 25% reduction in campaign setup time

---

**Note**: These user stories are derived from the comprehensive user flows documented in `docs/v2_rewrite_implementation_plan/notes/user_flows_notes.md` and reflect the current implementation status of the Ouroboros v2 rewrite project.
