# Implementation Plan

## Overview

This implementation plan converts the SvelteKit Frontend Removal design into a series of systematic tasks for eliminating the separate SvelteKit frontend from Ouroboros. The tasks are organized to safely remove frontend code, dependencies, and configurations while preserving all functionality through the integrated NiceGUI interface.

The removal process must be executed after the NiceGUI web interface has been fully implemented, tested, and validated to provide equivalent functionality to the existing SvelteKit frontend.

## Prerequisites

Before executing these tasks, the following must be completed:

- NiceGUI web interface fully implemented and functional
- All SvelteKit features have equivalent NiceGUI implementations
- User workflows tested and validated in NiceGUI
- Stakeholder approval obtained for frontend removal

## Implementation Tasks

- [ ] 1. Create Backup and Safety Branch

  - Create a complete backup of the current project state
  - Create a new branch `remove-sveltekit-frontend` for the removal work
  - Document the current state and create rollback procedures
  - _Requirements: 12.1, 12.2, 12.3_

- [ ] 1.1 Validate NiceGUI Functionality

  - Test all major user workflows in NiceGUI interface
  - Verify authentication and authorization work correctly
  - Confirm real-time updates and notifications function properly
  - Validate performance is acceptable compared to SvelteKit
  - _Requirements: 11.1, 11.2, 11.3_

- [ ] 1.2 Document Current Frontend Features

  - Create comprehensive list of all SvelteKit features and pages
  - Map each feature to its NiceGUI equivalent
  - Identify any functionality gaps that need addressing
  - Get stakeholder sign-off on feature mapping
  - _Requirements: 11.4, 11.5_

- [ ] 2. Update Route Configuration

  - Add redirect middleware to FastAPI for legacy SvelteKit routes
  - Configure root path `/` to redirect to `/ui/dashboard`
  - Set up redirects for all major SvelteKit routes to NiceGUI equivalents
  - Test that all redirects work correctly
  - _Requirements: 7.1, 7.2, 7.3_

- [ ] 2.1 Remove Web UI API Routes

  - Delete all `/api/v1/web/*` endpoint files in `app/api/v1/endpoints/web/`
  - Remove web-specific schemas from `app/schemas/web/` or individual web schema files
  - Update FastAPI router configuration to exclude web API routes
  - Verify NiceGUI uses direct service calls instead of HTTP API calls
  - _Requirements: 2.1, 2.2, 2.3_

- [ ] 2.2 Clean Up Web API Tests

  - Remove all Web UI API integration tests from `tests/integration/web/`
  - Remove web API unit tests from `tests/unit/api/web/`
  - Update test configuration to exclude web API test directories
  - Verify remaining tests still pass
  - _Requirements: 2.4, 10.1, 10.2_

- [ ] 3. Update Docker Configuration

  - Remove `frontend` service from `docker-compose.yml`
  - Remove `frontend` service from `docker-compose.dev.yml`
  - Update nginx configuration to remove frontend proxy settings
  - Configure nginx to serve only FastAPI application with NiceGUI
  - _Requirements: 4.1, 4.2, 4.3_

- [ ] 3.1 Test Docker Configuration

  - Build and test updated Docker containers
  - Verify only backend services are required (app, db, redis, minio)
  - Test that NiceGUI interface is accessible through nginx
  - Confirm all API endpoints still work through proxy
  - _Requirements: 4.4, 4.5_

- [ ] 4. Remove Node.js Dependencies

  - Delete `package.json` from project root
  - Delete `package-lock.json` or `pnpm-lock.yaml` from project root
  - Remove `node_modules/` directory from project root
  - Verify no Node.js dependencies remain in project
  - _Requirements: 3.1, 3.2, 3.3_

- [ ] 4.1 Remove Frontend Configuration Files

  - Delete `svelte.config.js` - SvelteKit configuration
  - Delete `vite.config.ts` - Vite build configuration
  - Delete `tailwind.config.js` - TailwindCSS configuration
  - Delete `postcss.config.js` - PostCSS configuration
  - Delete `playwright.config.ts` - E2E test configuration
  - Delete `vitest.config.ts` - Frontend unit test configuration
  - _Requirements: 8.1, 8.2, 8.4_

- [ ] 4.2 Remove Frontend TypeScript Configuration

  - Delete frontend-specific `tsconfig.json` files
  - Remove frontend ESLint configuration files (`.eslintrc.*`)
  - Remove frontend Prettier configuration files (`.prettierrc`, `.prettierignore`)
  - Clean up any remaining frontend linting configurations
  - _Requirements: 8.2, 8.3_

- [ ] 5. Remove Frontend Directory and Files

  - Delete entire `frontend/` directory and all contents
  - Remove `.svelte-kit/` build cache directory
  - Remove `build/` frontend build output directory
  - Remove `test-results/` and `test-artifacts/` directories
  - Remove `playwright-report/` directory
  - _Requirements: 1.1, 1.2_

- [ ] 5.1 Update .gitignore File

  - Remove frontend-specific entries from `.gitignore`
  - Remove Node.js related ignore patterns (`node_modules/`, `.npm`, etc.)
  - Remove SvelteKit specific ignore patterns (`.svelte-kit/`, `build/`, etc.)
  - Remove frontend test artifact patterns
  - _Requirements: 8.1_

- [ ] 6. Update Build System and CI/CD

  - Remove frontend test steps from `.github/workflows/ci.yml`
  - Remove frontend linting and formatting from CI workflows
  - Remove Node.js setup steps from GitHub Actions
  - Remove frontend build and deployment steps
  - _Requirements: 6.1, 6.2_

- [ ] 6.1 Update Justfile Recipes

  - Remove frontend-related recipes from `justfile`
  - Remove `frontend-*` commands (test, lint, format, etc.)
  - Update `dev-fullstack` recipe to only start backend services
  - Remove any pnpm/npm related commands
  - _Requirements: 6.3_

- [ ] 6.2 Update Pre-commit Hooks

  - Remove frontend-specific hooks from `.pre-commit-config.yaml`
  - Remove ESLint, Prettier, and other frontend linting hooks
  - Remove any Node.js or npm related hooks
  - Test that remaining pre-commit hooks work correctly
  - _Requirements: 6.4_

- [ ] 7. Update Documentation

  - Update `README.md` to remove frontend development sections
  - Remove "Frontend Development", "SvelteKit Setup", "Node.js Requirements" sections
  - Update "Quick Start" to remove frontend setup steps
  - Update "Development" section to backend-only workflow
  - Update "Testing" section to remove frontend test commands
  - Update "Deployment" section to single container approach
  - _Requirements: 5.1, 5.4_

- [ ] 7.1 Update Development Documentation

  - Update `docs/development/setup.md` to remove frontend sections
  - Remove "Frontend Development Environment" section
  - Remove "Node.js and pnpm Installation" section
  - Remove "SvelteKit Development Server" section
  - Update "Development Workflow" to backend + NiceGUI only
  - _Requirements: 5.2, 5.4_

- [ ] 7.2 Update Architecture Documentation

  - Update `docs/architecture/overview.md` to reflect new architecture
  - Update "System Architecture" to single FastAPI application
  - Replace "Frontend Architecture" section with NiceGUI section
  - Update "Deployment Architecture" to simplified container setup
  - Remove any references to separate frontend/backend services
  - _Requirements: 5.3, 5.4_

- [ ] 8. Remove Steering Documents

  - Delete `.kiro/steering/sveltekit5-runes.md`
  - Delete `.kiro/steering/shadcn-svelte-extras.md`
  - Delete `.kiro/steering/ux-guidelines.md`
  - Delete `.kiro/steering/task-verification-workflow.md`
  - Delete `.kiro/steering/phase-3-task-verification.md`
  - _Requirements: 5.2, 5.5_

- [ ] 8.1 Update Environment Configuration

  - Remove frontend-specific variables from `.env` and `env.example`
  - Remove frontend build and development settings
  - Update environment documentation to reflect backend-only requirements
  - Remove any frontend environment validation from application startup
  - _Requirements: 9.1, 9.2, 9.4_

- [ ] 9. Remove Frontend Tests

  - Delete all SvelteKit component tests
  - Delete frontend-specific Playwright E2E tests
  - Remove frontend test utilities and helpers
  - Update test commands to exclude frontend test execution
  - _Requirements: 10.1, 10.2, 10.3_

- [ ] 9.1 Update Test Configuration

  - Update test coverage configuration to exclude frontend code
  - Remove frontend test directories from coverage reports
  - Update CI test commands to only run backend and NiceGUI tests
  - Verify test suites run faster without frontend tests
  - _Requirements: 10.4, 10.5_

- [ ] 10. Validate Removal Success

  - Test that root path `/` redirects to `/ui/dashboard`
  - Verify all legacy SvelteKit routes redirect to NiceGUI equivalents
  - Confirm NiceGUI interface is fully accessible and functional
  - Test that Agent API and Control API endpoints still work
  - Verify no broken links or missing resources exist
  - _Requirements: 7.4, 7.5_

- [ ] 10.1 Test User Workflows

  - Test complete user login and dashboard access workflow
  - Test campaign creation and management in NiceGUI
  - Test agent monitoring and control functionality
  - Test attack configuration and execution
  - Test resource upload and management
  - Test user management and permissions (admin users)
  - _Requirements: 11.1, 11.2, 11.3_

- [ ] 10.2 Performance and Integration Testing

  - Verify application startup time improved (no frontend build)
  - Test that CI/CD pipeline runs faster without frontend steps
  - Confirm Docker container build is simpler and faster
  - Validate that only backend environment variables are required
  - Test backup and rollback procedures work if needed
  - _Requirements: 6.5, 9.5, 12.4_

- [ ] 11. Final Cleanup and Documentation

  - Update project README with simplified architecture description
  - Document the benefits achieved (single container, faster builds, etc.)
  - Create migration notes for any users affected by the change
  - Update any remaining references to SvelteKit in project files
  - _Requirements: 13.1, 13.3, 13.4_

- [ ] 11.1 Stakeholder Communication

  - Notify stakeholders of successful frontend removal
  - Provide updated documentation and setup instructions
  - Offer training on NiceGUI interface if needed
  - Document benefits and rationale for the change
  - _Requirements: 13.1, 13.2, 13.5_

- [ ] 11.2 Final Validation and Merge

  - Run complete test suite to ensure no regressions
  - Perform final review of all changes
  - Get approval from project maintainers
  - Merge removal branch to main branch
  - Tag release with frontend removal milestone
  - _Requirements: 12.3, 12.5_

## Post-Removal Benefits

Upon completion of these tasks, Ouroboros will achieve:

- **Simplified Architecture**: Single FastAPI application with integrated NiceGUI
- **Reduced Complexity**: No separate frontend/backend coordination required
- **Faster Development**: Python-only development workflow
- **Simpler Deployment**: Single container deployment
- **Faster CI/CD**: No frontend build, test, or linting steps
- **Reduced Maintenance**: Fewer dependencies and configurations to maintain
- **Better Integration**: NiceGUI directly integrated with backend services

## Rollback Procedures

If issues are discovered during removal:

1. **Immediate Rollback**: Switch back to backup branch
2. **Partial Rollback**: Restore specific components from backup
3. **Full Restoration**: Restore complete project state from backup
4. **Issue Resolution**: Address problems and retry removal process

The backup created in task 1 provides complete restoration capability throughout the removal process.
