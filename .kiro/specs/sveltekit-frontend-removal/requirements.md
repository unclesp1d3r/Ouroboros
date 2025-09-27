# Requirements Document

## Introduction

This specification defines the requirements for removing the SvelteKit frontend from CipherSwarm once the NiceGUI web interface has been fully implemented and validated. This cleanup operation will eliminate the separate frontend application, its dependencies, tooling, and associated documentation to simplify the project architecture and reduce maintenance overhead.

The removal will ensure that CipherSwarm operates as a single FastAPI application with an integrated NiceGUI web interface, eliminating the complexity of managing separate frontend and backend services.

## Requirements

### Requirement 1: Frontend Code Removal

**User Story:** As a system administrator, I want the SvelteKit frontend code completely removed from the project, so that I only need to maintain and deploy a single FastAPI application.

#### Acceptance Criteria

1. WHEN the SvelteKit frontend is removed THEN the `frontend/` directory SHALL be completely deleted
2. WHEN the removal is complete THEN no SvelteKit source files SHALL remain in the project
3. WHEN accessing the root path `/` THEN the system SHALL redirect to the NiceGUI interface at `/ui/`
4. IF users access legacy frontend routes THEN the system SHALL redirect appropriately to NiceGUI equivalents
5. WHEN the frontend is removed THEN all SvelteKit-specific configuration files SHALL be deleted

### Requirement 2: Web UI API Routes Removal

**User Story:** As a developer, I want the Web UI API routes removed since NiceGUI integrates directly with backend services, so that the API surface is simplified and maintenance is reduced.

#### Acceptance Criteria

1. WHEN Web UI API routes are removed THEN all `/api/v1/web/*` endpoints SHALL be deleted
2. WHEN the API is simplified THEN NiceGUI SHALL use direct service calls instead of HTTP API calls
3. WHEN Web UI routes are removed THEN related schemas and tests SHALL also be deleted
4. WHEN the cleanup is complete THEN only Agent API, Control API, and shared infrastructure routes SHALL remain
5. WHEN NiceGUI operates THEN it SHALL integrate directly with backend services without HTTP overhead

### Requirement 3: Dependency and Tooling Cleanup

**User Story:** As a developer, I want all SvelteKit-related dependencies and tooling removed from the project, so that the build process is simplified and maintenance overhead is reduced.

#### Acceptance Criteria

1. WHEN dependencies are cleaned up THEN all Node.js dependencies SHALL be removed from the root project
2. WHEN tooling is removed THEN `package.json`, `pnpm-lock.yaml`, and `node_modules/` SHALL be deleted from the root
3. WHEN the cleanup is complete THEN no npm/pnpm scripts SHALL remain in project configuration
4. WHEN building the project THEN no frontend build steps SHALL be required
5. WHEN the removal is complete THEN all frontend-specific CI/CD steps SHALL be removed

### Requirement 4: Docker Configuration Updates

**User Story:** As a DevOps engineer, I want Docker configurations updated to remove frontend services, so that deployment is simplified to a single backend container.

#### Acceptance Criteria

1. WHEN Docker configs are updated THEN the `frontend` service SHALL be removed from all compose files
2. WHEN containers are started THEN only backend services SHALL be required (app, db, redis, minio)
3. WHEN the frontend service is removed THEN nginx configuration SHALL be updated to serve only the NiceGUI interface
4. IF nginx is used THEN it SHALL proxy `/ui/` to the FastAPI application
5. WHEN deployment occurs THEN no frontend build or serving SHALL be required

### Requirement 5: Documentation and Steering Updates

**User Story:** As a developer, I want all SvelteKit-related documentation and steering rules removed, so that project documentation accurately reflects the current architecture.

#### Acceptance Criteria

1. WHEN documentation is updated THEN all SvelteKit references SHALL be removed from README files
2. WHEN steering rules are cleaned up THEN frontend-specific steering documents SHALL be deleted
3. WHEN architecture docs are updated THEN they SHALL reflect the NiceGUI-only frontend approach
4. WHEN setup instructions are revised THEN they SHALL not include frontend development steps
5. WHEN the cleanup is complete THEN no references to SvelteKit SHALL remain in project documentation

### Requirement 6: Build System and CI/CD Updates

**User Story:** As a developer, I want build systems and CI/CD pipelines updated to remove frontend steps, so that builds are faster and simpler.

#### Acceptance Criteria

1. WHEN CI/CD is updated THEN frontend test steps SHALL be removed from all workflows
2. WHEN builds run THEN no frontend linting or formatting SHALL be executed
3. WHEN the justfile is updated THEN frontend-related recipes SHALL be removed
4. WHEN pre-commit hooks are updated THEN frontend-specific hooks SHALL be removed
5. WHEN the build completes THEN only backend artifacts SHALL be produced

### Requirement 7: Route and Proxy Configuration

**User Story:** As a user, I want seamless access to the web interface through familiar URLs, so that the transition from SvelteKit to NiceGUI is transparent.

#### Acceptance Criteria

1. WHEN accessing `/` THEN the system SHALL redirect to `/ui/dashboard`
2. WHEN legacy routes are accessed THEN appropriate redirects SHALL guide users to NiceGUI equivalents
3. WHEN the web interface loads THEN it SHALL be served from the integrated NiceGUI system
4. IF API routes are accessed THEN they SHALL continue to work unchanged at `/api/v1/client/` and `/api/v1/control/`
5. WHEN static assets are requested THEN they SHALL be served by the FastAPI application

### Requirement 8: Configuration File Cleanup

**User Story:** As a developer, I want all SvelteKit-specific configuration files removed, so that the project structure is clean and maintainable.

#### Acceptance Criteria

1. WHEN config cleanup occurs THEN `svelte.config.js`, `vite.config.ts`, and `tailwind.config.js` SHALL be deleted
2. WHEN TypeScript configs are cleaned THEN frontend-specific `tsconfig.json` files SHALL be removed
3. WHEN linting configs are updated THEN frontend ESLint and Prettier configs SHALL be deleted
4. WHEN Playwright configs are cleaned THEN frontend-specific test configurations SHALL be removed
5. WHEN the cleanup is complete THEN only backend configuration files SHALL remain

### Requirement 9: Environment and Settings Updates

**User Story:** As a system administrator, I want environment configurations updated to remove frontend-specific settings, so that deployment configuration is simplified.

#### Acceptance Criteria

1. WHEN environment files are updated THEN frontend-specific variables SHALL be removed
2. WHEN settings are cleaned THEN no frontend build or development settings SHALL remain
3. WHEN the application starts THEN no frontend environment validation SHALL occur
4. IF environment documentation exists THEN it SHALL reflect backend-only requirements
5. WHEN deployment occurs THEN only backend environment variables SHALL be required

### Requirement 10: Testing Infrastructure Updates

**User Story:** As a developer, I want testing infrastructure updated to remove frontend tests, so that test suites run faster and focus only on backend functionality.

#### Acceptance Criteria

1. WHEN test suites are updated THEN all SvelteKit component tests SHALL be removed
2. WHEN E2E tests are cleaned THEN frontend-specific Playwright tests SHALL be deleted
3. WHEN test commands are updated THEN no frontend test execution SHALL be included
4. WHEN coverage reports are generated THEN they SHALL include only backend code
5. WHEN tests run THEN only backend and NiceGUI integration tests SHALL execute

### Requirement 11: Migration and Validation

**User Story:** As a project maintainer, I want validation that the NiceGUI interface provides equivalent functionality to the removed SvelteKit frontend, so that no user capabilities are lost.

#### Acceptance Criteria

1. WHEN functionality is validated THEN all SvelteKit features SHALL have NiceGUI equivalents
2. WHEN user workflows are tested THEN they SHALL work identically in the NiceGUI interface
3. WHEN the migration is complete THEN user experience SHALL be maintained or improved
4. IF any functionality gaps exist THEN they SHALL be documented and addressed before removal
5. WHEN validation is complete THEN stakeholder approval SHALL be obtained before proceeding

### Requirement 12: Rollback and Safety Measures

**User Story:** As a project maintainer, I want safety measures in place during the removal process, so that the project can be restored if issues are discovered.

#### Acceptance Criteria

1. WHEN removal begins THEN a complete backup of the SvelteKit frontend SHALL be created
2. WHEN changes are made THEN they SHALL be implemented in a separate branch for testing
3. WHEN the removal is tested THEN comprehensive validation SHALL occur before merging
4. IF issues are discovered THEN the removal process SHALL be reversible
5. WHEN the removal is complete THEN the backup SHALL be retained for a defined period

### Requirement 13: Communication and Documentation

**User Story:** As a stakeholder, I want clear communication about the frontend removal process, so that I understand the impact and timeline.

#### Acceptance Criteria

1. WHEN the removal is planned THEN stakeholders SHALL be notified of the timeline
2. WHEN changes affect users THEN migration guides SHALL be provided if needed
3. WHEN the removal is complete THEN updated documentation SHALL be published
4. IF training is needed THEN it SHALL be provided for the NiceGUI interface
5. WHEN communication occurs THEN it SHALL include benefits and rationale for the change
