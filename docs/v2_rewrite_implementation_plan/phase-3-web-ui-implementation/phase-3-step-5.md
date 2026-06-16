# Phase 3 Step 5: System Monitoring & Administrative Features

\*\* System Administration Step\*\* - This step implements comprehensive system monitoring, audit logging, and administrative features for system health and governance.

---

## Table of Contents

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=2 --minlevel=1 -->

- [Phase 3 Step 5: System Monitoring & Administrative Features](#phase-3-step-5-system-monitoring--administrative-features)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [System Health Dashboard Implementation](#system-health-dashboard-implementation)
  - [Activity & Audit Logging Implementation](#activity--audit-logging-implementation)
  - [Advanced Administrative Features](#advanced-administrative-features)
  - [Enhanced Notification & Communication](#enhanced-notification--communication)
  - [System Monitoring & Administrative Testing](#system-monitoring--administrative-testing)
  - [Advanced Campaign Management Features](#advanced-campaign-management-features)
  - [Standalone Attack Management](#standalone-attack-management)
  - [Validation & Success Criteria](#validation--success-criteria)
  - [Implementation Notes](#implementation-notes)
  - [Completion Definition](#completion-definition)

<!-- mdformat-toc end -->

---

## Overview

With core functionality complete and integration tested, this step focuses on administrative and monitoring capabilities that enable effective system management, audit compliance, and operational oversight.

### Critical Context Notes

- **System Health Monitoring**: Redis queue metrics, PostgreSQL performance stats, MinIO storage usage, agent runtime statistics (admin-only)
- **Audit System**: Comprehensive logging of user actions, system events, and security events with filtering, search, and export capabilities
- **Administrative Features**: System configuration management, background job monitoring, bulk operations, maintenance mode controls
- **Resource Sensitivity**: Global vs project-scoped visibility, sensitive resource redaction for non-admins, access control validation
- **Fleet Management**: Agent configuration management, performance optimization, workload balancing, utilization analytics
- **Campaign Administration**: Advanced editing, deletion with impact assessment, ownership transfer, template library management
- **Notification System**: Administrative alerts, security events, resource quotas, system maintenance announcements
- **Performance Monitoring**: Real-time metrics visualization, trend analysis, bottleneck identification, capacity planning analytics
- **Testing Strategy**: All user-facing functionality must have both E2E tests (mocked and full E2E). Follow the [full testing architecture](../side_quests/full_testing_architecture.md) document and refer to `.cursor/rules/testing/e2e-docker-infrastructure.mdc` and `.cursor/rules/testing/testing-patterns.mdc` for detailed guidelines.
- **E2E Testing Structure**: `frontend/e2e/` contains mocked E2E tests (fast, no backend), `frontend/tests/e2e/` contains full E2E tests (slower, real backend). Configs: `playwright.config.ts` (mocked) vs `playwright.config.e2e.ts` (full backend)

## System Health Dashboard Implementation

### System Health Monitoring (Admin Only)

\*\* Technical Context\*\*: Admin-only dashboard displaying Redis queue metrics, PostgreSQL performance, MinIO storage usage, and agent runtime stats. Real-time charts with alert thresholds and notification management. Dashboard must use idiomatic Shadcn-Svelte components for charts, cards, and data visualization.

- [ ] **HEALTH-001**: System health dashboard implementation

  - [ ] Redis health and queue metrics (`MON-001a`)
    - **Health Cards**: Color-coded service status indicators (green=healthy, red=error, yellow=warning)
    - **Queue Metrics**: Real-time display of queue lengths, processing rates, failed jobs
    - **Connection Status**: Redis connection health with latency measurements
    - **Design Reference**: [Health Status Screen](../notes/ui_screens/health_status_screen.md)
  - [ ] PostgreSQL health and performance stats (`MON-001b`)
    - **Database Metrics**: Connection pool status, query performance, active connections
    - **Performance Charts**: Query execution time trends, connection usage over time
    - **Health Indicators**: Database responsiveness, WAL status, replication health
  - [ ] MinIO storage usage and latency (`MON-001c`)
    - **Storage Overview**: Used/available space with visual progress indicators
    - **Performance Metrics**: Upload/download speeds, request latency, error rates
    - **Bucket Health**: Individual bucket statistics and access patterns
  - [ ] Agent runtime statistics (`MON-001d`)
    - **Fleet Overview**: Total agents, online/offline counts, performance summaries
    - **Performance Trends**: System-wide hash rate trends, agent utilization charts
    - **Health Distribution**: Agent health status distribution with alerts
  - [ ] System performance trends and alerts (`MON-001e`)
    - **Trend Visualization**: Time-series charts for key performance indicators
    - **Alert Management**: Active alerts with severity levels and acknowledgment
    - **Performance Analytics**: Bottleneck identification and optimization recommendations

- [ ] **HEALTH-002**: System metrics visualization

  - [ ] Real-time system resource utilization charts
  - [ ] Database connection and query performance metrics
  - [ ] Storage usage and capacity planning indicators
  - [ ] Queue depth and processing rate monitoring
  - [ ] Alert thresholds and notification management

### System Administration Interface

- [ ] **ADMIN-001**: Administrative dashboard implementation

  - [ ] System configuration management interface
  - [ ] Service status overview and control panel
  - [ ] Background job management and monitoring
  - [ ] System maintenance mode controls
  - [ ] Emergency system shutdown and restart controls

- [ ] **ADMIN-002**: Administrative workflow enhancements

  - [ ] Bulk operations interface for data management
  - [ ] System backup and restore controls
  - [ ] Database maintenance and optimization tools
  - [ ] Log management and rotation controls
  - [ ] System update and version management

## Activity & Audit Logging Implementation

### Audit Log System

- [ ] **AUDIT-001**: Comprehensive audit logging implementation

  - [ ] Audit log page with filtering (`MON-002a`)
    - **Timeline Interface**: Chronological list of system and user activities
    - **Filter Controls**: Date range picker, user selector, action type filters
    - **Search Functionality**: Real-time search across log entries and metadata
    - **Pagination**: Efficient pagination for large audit log datasets
  - [ ] User action tracking (`MON-002b`)
    - **Action Details**: User, timestamp, action type, affected resources
    - **Context Information**: IP address, user agent, session details
    - **Visual Hierarchy**: Clear distinction between user and system actions
  - [ ] System event logging (`MON-002c`)
    - **Event Categories**: System startup/shutdown, service health changes, security events
    - **Severity Levels**: Color-coded severity indicators (info, warning, error, critical)
    - **Event Context**: Detailed information about system state changes
  - [ ] Audit detail view modal (`MON-002d`)
    - **Detailed View**: Expandable modal with full audit entry details
    - **JSON Viewer**: Formatted display of audit metadata and context
    - **Related Events**: Links to related audit entries for context
  - [ ] Audit log export functionality (`MON-002e`)
    - **Export Options**: CSV, JSON formats with configurable date ranges
    - **Filter Export**: Export only filtered/searched results
    - **Progress Feedback**: Progress indicators for large exports

- [ ] **AUDIT-002**: Advanced audit features

  - [ ] Audit log search and advanced filtering
  - [ ] Audit log retention policy management
  - [ ] Compliance reporting and automated exports
  - [ ] Audit trail integrity verification
  - [ ] Real-time audit event notifications

### Activity Tracking Enhancement

- [ ] **ACTIVITY-001**: User activity monitoring

  - [ ] User session tracking and analytics
  - [ ] Resource access pattern analysis
  - [ ] Campaign and attack operation logging
  - [ ] Agent interaction and command tracking
  - [ ] Performance impact analysis of user actions

- [ ] **ACTIVITY-002**: System activity monitoring

  - [ ] System-initiated operations logging
  - [ ] Automated task execution tracking
  - [ ] Background process monitoring and logging
  - [ ] Error pattern analysis and alerting
  - [ ] System health event correlation

## Advanced Administrative Features

### Resource Sensitivity & Permissions Enhancement

- [ ] **SENSITIVITY-001**: Complete sensitivity and permissions system
  - [ ] Global vs project-scoped resource visibility (`RES-004a`)
  - [ ] Sensitive resource redaction for non-admins (`RES-004b`)
  - [ ] Resource access control validation (`RES-404c`)
  - [ ] Resource sharing across projects (admin only) (`RES-004d`)
  - [ ] Resource permission inheritance (`RES-004e`)

### Campaign & Attack Administration

- [ ] **CAMPAIGN-ADMIN-001**: Advanced campaign administration

  - [ ] Campaign ownership transfer (admin only)
  - [ ] Bulk campaign operations and management
  - [ ] Campaign archive and cleanup management
  - [ ] Campaign template library management
  - [ ] Campaign performance optimization recommendations

- [ ] **ATTACK-ADMIN-001**: Attack administration features

  - [ ] Attack library and template management
  - [ ] Attack pattern analysis and optimization
  - [ ] Attack resource usage optimization
  - [ ] Attack failure pattern analysis
  - [ ] Attack performance benchmarking and comparison

### Agent Fleet Management

- [ ] **FLEET-001**: Advanced agent fleet management

  - [ ] Fleet-wide agent configuration management
  - [ ] Agent deployment and update management
  - [ ] Agent performance optimization recommendations
  - [ ] Agent health trending and predictive maintenance
  - [ ] Agent workload balancing and optimization

- [ ] **FLEET-002**: Agent analytics and insights

  - [ ] Agent utilization analytics and reporting
  - [ ] Agent cost-effectiveness analysis
  - [ ] Agent hardware lifecycle management
  - [ ] Agent benchmark trend analysis
  - [ ] Agent failure pattern identification

## Enhanced Notification & Communication

### Administrative Notifications

- [ ] **ADMIN-NOTIFY-001**: Administrative notification system

  - [ ] System health alert notifications
  - [ ] Security event notifications
  - [ ] Resource quota and limit notifications
  - [ ] System maintenance notifications
  - [ ] Critical error escalation notifications

- [ ] **ADMIN-NOTIFY-002**: Communication management

  - [ ] User announcement system
  - [ ] System status page management
  - [ ] Emergency communication protocols
  - [ ] Notification delivery verification
  - [ ] Communication audit and compliance

### Performance & Load Monitoring

- [ ] **PERFORMANCE-001**: Performance monitoring dashboard
  - [ ] Real-time performance metrics visualization
  - [ ] Performance trend analysis and alerting
  - [ ] Resource bottleneck identification
  - [ ] Performance optimization recommendations
  - [ ] Capacity planning analytics

## System Monitoring & Administrative Testing

### Testing Guidelines & Requirements

\*\* Critical Testing Context:\*\*

- **Test Structure**: All user-facing functionality must have both E2E tests (mocked and full E2E). Strictly follow existing test structure and naming conventions as described in the [full testing architecture](../side_quests/full_testing_architecture.md) document.
- **Test Execution**:
  - Run `just test-frontend` for mocked E2E tests (fast, no backend required)
  - Run `just test-e2e` for full E2E tests (requires Docker setup, slower but complete integration testing)
  - **Important**: Do not run full E2E tests directly - they require setup code and must run via the `just test-e2e` command
- **Test Utilities**: Use or reuse existing test utils and helpers in `frontend/tests/test-utils.ts` for consistency and maintainability
- **API Integration**: The OpenAPI spec for the current backend is in `contracts/current_api_openapi.json` and should be used for all backend API calls, with Zod objects generated from the spec in `frontend/src/lib/schemas/`
- **Test Notation**: When tasks include notations like (E2E) or (Mock), tests must be created or updated to cover that specific functionality and confirm it works as expected

### UI/UX Requirements & Standards

- **Responsive Design**: Ensure the interface is polished and follows project standards. While mobile support is not a priority, it should be functional and usable on modern desktop browsers and tablets from `1080x720` resolution on up. It is reasonable to develop for support of mobile resolutions.
- **Offline Capability**: Ability to operate entirely without internet connectivity is a priority. No functionality should depend on public CDNs or other internet-based services.
- **API Integration**: The OpenAPI spec for the current backend is in `contracts/current_api_openapi.json` and should be used for all backend API calls, with Zod objects having been generated from the spec in `frontend/src/lib/schemas/`.
- **Testing Coverage**: All forms must be validated using the OpenAPI spec and the Zod objects. All forms must be validated on both server side and client side.

### System Health Dashboard Testing

- [ ] **TEST-MON-001**: System Health Dashboard Tests (Admin Only)
  - [ ] **MON-001a**: Redis health and queue metrics (E2E + Mock)
  - [ ] **MON-001b**: PostgreSQL health and performance stats (E2E + Mock)
  - [ ] **MON-001c**: MinIO storage usage and latency (E2E + Mock)
  - [ ] **MON-001d**: Agent runtime statistics (E2E + Mock)
  - [ ] **MON-001e**: System performance trends and alerts (Mock)

### Activity & Audit Logging Testing

- [ ] **TEST-MON-002**: Activity & Audit Logging Tests
  - [ ] **MON-002a**: Audit log page with filtering (E2E + Mock)
  - [ ] **MON-002b**: User action tracking (E2E + Mock)
    - **Change Tracking**: Before/after values for data modifications
  - [ ] **MON-002c**: System event logging (E2E + Mock)
    - **Event Categories**: System startup, service failures, performance alerts
    - **Severity Levels**: Color-coded severity indicators (info, warning, error, critical)
    - **Event Context**: Detailed event metadata and system state information
  - [ ] **MON-002d**: Audit detail view modal (Mock)
    - **Detailed View**: Expandable modal with full audit entry details
    - **JSON Display**: Formatted display of audit entry metadata
    - **Related Events**: Links to related audit entries and system events
  - [ ] **MON-002e**: Audit log export functionality (E2E + Mock)
    - **Export Options**: CSV, JSON formats with date range selection
    - **Export Progress**: Progress indicator for large export operations
    - **Download Management**: Secure download links with expiration

### Resource Sensitivity Testing

- [ ] **TEST-RES-004**: Sensitivity & Permissions Tests
  - [ ] **RES-404a**: Global vs project-scoped resource visibility (E2E + Mock)
  - [ ] **RES-004b**: Sensitive resource redaction for non-admins (Mock)
  - [ ] **RES-404c**: Resource access control validation (E2E + Mock)
  - [ ] **RES-004d**: Resource sharing across projects (admin only) (E2E + Mock)
  - [ ] **RES-004e**: Resource permission inheritance (Mock)

### Administrative Feature Testing

- [ ] **TEST-ADMIN-001**: Administrative Dashboard Tests

  - [ ] System configuration management interface (E2E + Mock)
  - [ ] Service status overview and control panel (Mock)
  - [ ] Background job management and monitoring (E2E + Mock)
  - [ ] System maintenance mode controls (Mock)
  - [ ] Emergency system controls (Mock)

- [ ] **TEST-ADMIN-002**: Administrative Workflow Tests

  - [ ] Bulk operations interface for data management (E2E + Mock)
  - [ ] System backup and restore controls (Mock)
  - [ ] Database maintenance and optimization tools (Mock)
  - [ ] Log management and rotation controls (Mock)
  - [ ] System update and version management (Mock)

### Fleet Management Testing

- [ ] **TEST-FLEET-001**: Agent Fleet Management Tests

  - [ ] Fleet-wide agent configuration management (E2E + Mock)
  - [ ] Agent deployment and update management (Mock)
  - [ ] Agent performance optimization recommendations (Mock)
  - [ ] Agent health trending and predictive maintenance (Mock)
  - [ ] Agent workload balancing and optimization (Mock)

- [ ] **TEST-FLEET-002**: Agent Analytics Tests

  - [ ] Agent utilization analytics and reporting (Mock)
  - [ ] Agent cost-effectiveness analysis (Mock)
  - [ ] Agent hardware lifecycle management (Mock)
  - [ ] Agent benchmark trend analysis (Mock)
  - [ ] Agent failure pattern identification (Mock)

### Administrative Notification Testing

- [ ] **TEST-ADMIN-NOTIFY**: Administrative Notification Tests
  - [ ] System health alert notifications (E2E + Mock)
  - [ ] Security event notifications (Mock)
  - [ ] Resource quota and limit notifications (Mock)
  - [ ] System maintenance notifications (Mock)
  - [ ] Critical error escalation notifications (Mock)

## Advanced Campaign Management Features

### Campaign Edit & Modification Pages

- [ ] **CAMPAIGN-EDIT-001**: Complete campaign edit pages
  - [ ] Campaign edit page loads with current settings (`CAM-006a`)
  - [ ] Campaign metadata modification (name, description, notes) (`CAM-006b`)
  - [ ] Campaign settings updates (DAG mode, scheduling) (`CAM-006c`)
  - [ ] Attack reordering within existing campaigns (`CAM-006d`)
  - [ ] Campaign edit validation and error handling (`CAM-006e`)
  - [ ] Campaign edit permission enforcement (`CAM-006f`)

### Campaign Deletion Flow

- [ ] **CAMPAIGN-DELETE-001**: Complete campaign deletion flow
  - [ ] Campaign deletion page loads with impact assessment (`CAM-007a`)
  - [ ] Display of associated attacks, tasks, and resources (`CAM-007b`)
  - [ ] Warning messages for active/running campaigns (`CAM-007c`)
  - [ ] Confirmation workflow with typed verification (`CAM-007d`)
  - [ ] Cascade deletion warnings and options (`CAM-007e`)
  - [ ] Campaign deletion permission validation (`CAM-007f`)

### Campaign Edit & Deletion Testing

- [ ] **TEST-CAM-006**: Campaign Edit & Modification Tests

  - [ ] **CAM-006a**: Campaign edit page loads with current settings (E2E + Mock)
  - [ ] **CAM-006b**: Campaign metadata modification (E2E + Mock)
  - [ ] **CAM-006c**: Campaign settings updates (Mock)
  - [ ] **CAM-006d**: Attack reordering within existing campaigns (Mock)
  - [ ] **CAM-006e**: Campaign edit validation and error handling (Mock)
  - [ ] **CAM-006f**: Campaign edit permission enforcement (Mock)

- [ ] **TEST-CAM-007**: Campaign Deletion Flow Tests

  - [ ] **CAM-007a**: Campaign deletion page loads with impact assessment (E2E + Mock)
  - [ ] **CAM-007b**: Display of associated attacks, tasks, and resources (Mock)
  - [ ] **CAM-007c**: Warning messages for active/running campaigns (Mock)
  - [ ] **CAM-007d**: Confirmation workflow with typed verification (Mock)
  - [ ] **CAM-007e**: Cascade deletion warnings and options (Mock)
  - [ ] **CAM-007f**: Campaign deletion permission validation (Mock)

## Standalone Attack Management

### Standalone Attack Creation

- [ ] **ATTACK-STANDALONE-001**: Complete standalone attack features
  - [ ] Attack creation page loads independently from campaigns (`ATT-005a`)
  - [ ] Attack resource selection and validation (`ATT-005b`)
  - [ ] Standalone attack parameter configuration (`ATT-005c`)
  - [ ] Attack save and template creation (`ATT-005d`)
  - [ ] Attack preview and keyspace calculation (`ATT-005e`)
  - [ ] Attack export and sharing functionality (`ATT-005f`)

### Standalone Attack Testing

- [ ] **TEST-ATT-005**: Standalone Attack Creation Tests
  - [ ] **ATT-005a**: Attack creation page loads independently (E2E + Mock)
  - [ ] **ATT-005b**: Attack resource selection and validation (Mock)
  - [ ] **ATT-005c**: Standalone attack parameter configuration (Mock)
  - [ ] **ATT-005d**: Attack save and template creation (E2E + Mock)
  - [ ] **ATT-005e**: Attack preview and keyspace calculation (Mock)
  - [ ] **ATT-005f**: Attack export and sharing functionality (E2E + Mock)

## Validation & Success Criteria

### System Monitoring Validation

- [ ] **VALIDATE-001**: System monitoring provides comprehensive oversight
  - [ ] System health dashboard displays accurate real-time metrics
  - [ ] Performance monitoring identifies bottlenecks and issues
  - [ ] Alert system functions properly with appropriate thresholds
  - [ ] Resource usage tracking provides actionable insights
  - [ ] Trend analysis supports capacity planning decisions

### Audit & Compliance Validation

- [ ] **VALIDATE-002**: Audit logging meets compliance requirements
  - [ ] All user actions are properly logged with sufficient detail
  - [ ] Audit log search and filtering provide efficient access to information
  - [ ] Audit log export supports compliance reporting requirements
  - [ ] Audit trail integrity is maintained and verifiable
  - [ ] Retention policies are enforced automatically

### Administrative Features Validation

- [ ] **VALIDATE-003**: Administrative features provide effective system management
  - [ ] Administrative dashboard provides comprehensive system control
  - [ ] Bulk operations improve administrative efficiency
  - [ ] System maintenance controls work properly
  - [ ] Resource permission management enforces security policies
  - [ ] Fleet management provides effective agent oversight

### Campaign & Attack Administration Validation

- [ ] **VALIDATE-004**: Advanced campaign and attack features are complete
  - [ ] Campaign edit pages provide comprehensive modification capabilities
  - [ ] Campaign deletion flow prevents accidental data loss
  - [ ] Standalone attack creation supports template and reuse workflows
  - [ ] Impact assessment provides clear understanding of operation consequences
  - [ ] Permission enforcement prevents unauthorized operations

### Performance & Scalability Validation

- [ ] **VALIDATE-005**: System performs well under administrative load
  - [ ] Monitoring dashboards update efficiently with large datasets
  - [ ] Audit log queries perform acceptably with historical data
  - [ ] Bulk operations complete in reasonable time frames
  - [ ] Real-time monitoring doesn't impact system performance
  - [ ] Administrative interfaces remain responsive under normal load

## Implementation Notes

### Key Administrative System References

- **Component Architecture**: Use idiomatic Shadcn-Svelte components for administrative interfaces including dashboards, data tables, charts, and forms
- **SvelteKit Patterns**: Follow idiomatic SvelteKit 5 patterns for administrative data loading, bulk operations, and system monitoring
- **Audit Model**: User actions, system events, security events with filtering/search/export capabilities
- **Health Monitoring**: Redis metrics, PostgreSQL stats, MinIO usage, agent runtime data (admin-only access)
- **Resource Sensitivity**: Global vs project-scoped visibility, redaction for non-admins, access control validation
- **Fleet Management**: Agent configuration, performance optimization, utilization analytics, predictive maintenance
- **Campaign Administration**: Edit/deletion with impact assessment, ownership transfer, template library
- **Performance Requirements**: Real-time charts, trend analysis, capacity planning, non-intrusive monitoring

### System Monitoring Context

Comprehensive system monitoring enables effective operational management:

- Health dashboards provide real-time visibility into system status
- Performance monitoring enables proactive issue identification
- Alert systems ensure timely response to critical events
- Trend analysis supports capacity planning and optimization

### Audit & Compliance Strategy

Robust audit logging supports governance and compliance requirements:

- All user actions are tracked with sufficient detail for accountability
- System events are logged to support incident investigation
- Audit log retention and export support regulatory compliance
- Audit trail integrity ensures non-repudiation of logged events

### Administrative Feature Focus

Administrative features enhance system management efficiency:

- Centralized control panels reduce administrative overhead
- Bulk operations improve efficiency for large-scale management
- Permission management enforces security policies consistently
- Fleet management provides comprehensive agent oversight

### Campaign & Attack Administration

Advanced campaign and attack features improve operational workflows:

- Edit pages support comprehensive modification workflows
- Deletion flows prevent accidental data loss through impact assessment
- Standalone attack creation supports reusable template workflows
- Permission enforcement prevents unauthorized operations

## Completion Definition

This step is complete when:

1. System monitoring provides comprehensive real-time visibility into system health
2. Audit logging meets compliance requirements with search, export, and retention features
3. Administrative features enable efficient system management and control
4. Resource permission system enforces security policies consistently
5. Campaign and attack administration features support complete operational workflows
6. Performance monitoring and alerting enable proactive system management
7. All administrative and monitoring tests pass in both Mock and E2E environments
8. Administrative interfaces remain responsive and efficient under normal operational load
