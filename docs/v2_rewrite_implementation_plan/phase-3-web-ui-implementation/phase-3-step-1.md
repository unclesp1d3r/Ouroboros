# Phase 3 Step 1: SSR Authentication Foundation

---

## Table of Contents

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=2 --minlevel=1 -->

- [Phase 3 Step 1: SSR Authentication Foundation](#phase-3-step-1-ssr-authentication-foundation)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [Backend Authentication Tasks](#backend-authentication-tasks)
  - [Frontend SSR Authentication Tasks](#frontend-ssr-authentication-tasks)
  - [Test Implementation](#test-implementation)
  - [Docker Infrastructure Updates](#docker-infrastructure-updates)
  - [Validation & Success Criteria](#validation--success-criteria)
  - [Implementation Notes](#implementation-notes)
  - [Completion Definition](#completion-definition)

<!-- mdformat-toc end -->

---

\*\* Critical Foundation Step\*\* - This step implements the core authentication infrastructure required for all subsequent testing and functionality. Nothing else can be fully validated until this is complete.

## Overview

This step addresses the critical blocker preventing full E2E testing: implementing SSR-compatible authentication for SvelteKit with FastAPI backend integration. All load functions require authenticated API calls, and the current architecture lacks session management.

### Critical Context Notes

- **Architecture**: SvelteKit SSR frontend (port 5173) + FastAPI backend (port 8000) as separate services
- **Current State**: All SSR load functions (`+page.server.ts`) make API calls but fail with 401 due to missing session handling
- **Authentication Flow**: Adapts existing FastAPI JWT implementation for SSR - JWT tokens stored in HTTP-only cookies, forwarded from SvelteKit to FastAPI
- **Environment Detection**: Load functions check `PLAYWRIGHT_TEST` or `NODE_ENV=test` to return mock data during testing
- **Docker E2E**: Infrastructure complete but requires authentication to enable full backend integration testing
- **Testing Pattern**: Layer 2 (frontend mocked) works, Layer 3 (full E2E) blocked by authentication requirement

## Backend Authentication Tasks

### Backend Session Management Implementation

\*\* Technical Context\*\*: Adapt existing FastAPI JWT authentication for SSR compatibility. JWT tokens stored in HTTP-only cookies instead of localStorage, allowing server-side API calls.

- [x] **AUTH-BE-001**: Modify existing JWT authentication to support HTTP-only cookies

  - [x] Create `/api/v1/web/auth/login` endpoint that returns JWT in HTTP-only cookie
  - [x] Create `/api/v1/web/auth/logout` endpoint that clears JWT cookie
  - [x] Modify JWT middleware to accept tokens from cookies AND Authorization headers
    - [x] Update existing JWT validation to extract tokens from cookies
  - [x] Configure proper CORS settings for SvelteKit frontend cookie handling

- [x] **AUTH-BE-002**: JWT token refresh and validation

  - [x] Implement JWT token refresh mechanism
  - [x] Update existing JWT validation middleware for cookie extraction
  - [x] Implement proper token expiration handling
  - [x] Add token refresh capabilities for long-lived sessions

- [x] **AUTH-BE-003**: Health check endpoint updates

  - [x] Ensure `/api-info` endpoint remains unauthenticated for Docker health checks
  - [x] Create authenticated health endpoint for internal monitoring
  - [x] Update Docker health check configuration if needed

### Backend CORS and Security Configuration

- [x] **AUTH-BE-004**: CORS configuration for SvelteKit SSR
  - [x] Configure CORS to accept cookies from SvelteKit frontend
  - [x] Set appropriate `Access-Control-Allow-Credentials` headers
  - [x] Update allowed origins for development and production environments

## Frontend SSR Authentication Tasks

### SvelteKit Hooks Implementation

\*\* Technical Context\*\*: SvelteKit hooks extract JWT cookies from requests and set `event.locals.user` for use in load functions. Must handle JWT validation and automatic login redirect.

- [x] **AUTH-FE-001**: Create `hooks.server.js` for JWT cookie handling

  - [x] Implement JWT cookie extraction from requests
  - [x] Create user context setting for load functions (`event.locals.user`)
    - [x] Add JWT validation and refresh logic
      - [x] Implement automatic redirect to login for expired tokens

### Server-Side API Client

- [x] **AUTH-FE-002**: Create authenticated server-side API client
  - [x] Implement `ServerApiClient` class with JWT cookie authentication
  - [x] Add JWT cookie forwarding as Authorization headers for backend requests
  - [x] Implement proper error handling for 401/403 responses
  - [x] Create utility functions for common authenticated requests

### Login/Logout Route Implementation

- [x] **AUTH-FE-003**: Implement login page with idiomatic SvelteKit actions

  - [x] Create `/login/+page.svelte` using idiomatic Shadcn-Svelte login components
  - [x] Implement login form action in `/login/+page.server.ts` with Superforms integration
  - [x] Add JWT cookie setting from FastAPI response
  - [x] Implement redirect logic after successful login using SvelteKit patterns

- [x] **AUTH-FE-004**: Implement logout functionality

  - [x] Create logout action accessible from layout
  - [x] Implement JWT cookie cleanup and removal
  - [x] Add confirmation handling for logout process
  - [x] Ensure proper redirect after logout

### Load Function Authentication Updates

- [x] **AUTH-FE-005**: Update all `+page.server.ts` files for authentication
  - [x] Update dashboard load function (`/+page.server.ts`) - [x] Fixed flaky modal test timing issue
  - [x] Update campaigns load functions (`/campaigns/+page.server.ts`, `/campaigns/[id]/+page.server.ts`) - [x] Updated to use locals.session and locals.user pattern
  - [x] Update attacks load function (`/attacks/+page.server.ts`) - [x] Updated to use locals.session and locals.user pattern
  - [x] Update agents load function (`/agents/+page.server.ts`) - [x] Updated to use locals.session and locals.user pattern
  - [x] Update resources load functions (`/resources/+page.server.ts`, `/resources/[id]/+page.server.ts`)
  - [x] Update users load function (`/users/+page.server.ts`) - [x] Updated to use locals.session and locals.user pattern
  - [x] Update projects load function (`/projects/+page.server.ts`) - [x] Updated to use locals.session and locals.user pattern
  - [x] Update settings load function (`/settings/+page.server.ts`) - [x] Updated to use locals.session and locals.user pattern

### Environment Detection for Testing

- [x] **AUTH-FE-006**: Implement test environment authentication bypass
  - [x] Add environment detection in load functions (`PLAYWRIGHT_TEST`, `NODE_ENV=test`)
  - [x] Create mock data fallbacks for test scenarios
  - [x] Ensure test data matches production API response structure
  - [x] Implement clean switching between test and production modes

## Test Implementation

Create or update tests to cover the following functionality. All user-facing functionality must have E2E tests, both mocked and full E2E. If the the note below includes a notation like (E2E, referring to the full E2E tests) or (Mock, referring to the mocked E2E tests), then the test must be created or updated to cover the functionality and confirm that the functionality works as expected. Strictly follow the existing test structure and naming conventions, as as described in the [full testing architecture](../side_quests/full_testing_architecture.md) document. Refer to `.cursor/rules/testing/e2e-docker-infrastructure.mdc` and `.cursor/rules/testing/testing-patterns.mdc` for more details.

Be sure to use or reuse the existing test utils and helpers in `frontend/tests/test-utils.ts`. Run `just test-frontend` for the mocked tests and `just test-e2e` for the full E2E tests to verify that the tests are working as expected. Do not attempt to run the full E2E directly, since it requires setup code, it must run via the just command `just test-e2e`. The OpenAPI spec for the current backend is in `contracts/current_api_openapi.json` and should be used for all backend API calls, with Zod objects having been generated from the spec in `frontend/src/lib/schemas/`.

### Authentication Flow Tests (Critical)

- [x] **TEST-ASM-001**: Login Flow Testing

  - [x] **ASM-001a**: Successful login with valid credentials (E2E + Mock) - [x] Updated to use new test helpers and utils - verified for both mocked and full E2E tests
  - [x] **ASM-001b**: Failed login with invalid credentials (E2E + Mock) - [x] Implemented both mocked and full E2E tests for invalid credentials error handling
  - [x] **ASM-001c**: Login form validation errors (Mock) - [x] Implemented comprehensive client-side validation error tests including empty form, invalid email, empty password, and error clearing scenarios
  - [x] **ASM-001d**: JWT persistence across page refreshes (E2E) - [x] Implemented comprehensive JWT persistence test with proper login helper, page refresh, and session validation
  - [x] **ASM-001e**: Redirect to login when accessing protected routes unauthenticated (E2E)
  - [x] **ASM-001f**: Login loading states and error display (Mock) - [x] Implemented comprehensive tests for login loading states and error display in mocked environment

- [x] **TEST-ASM-003**: JWT Token Management Testing

  - [x] **ASM-003a**: JWT expiration handling with redirect (E2E)
  - [x] **ASM-003b**: Token refresh on API calls (E2E) - [x] Implemented comprehensive E2E test that validates automatic token refresh during SSR navigation across multiple protected routes
  - [x] **ASM-003c**: Logout functionality with JWT cleanup (E2E + Mock)
  - [x] **ASM-003d**: JWT expiry redirect to login (E2E) - [x] Comprehensive test implemented in `frontend/tests/e2e/auth.e2e.test.ts` that simulates token expiry, verifies login redirect, and tests re-authentication flow

### Load Function Authentication Tests

- [x] **TEST-AUTH-LOAD**: SSR Load Function Authentication
  - [x] Test authenticated data loading for dashboard (E2E) - [x] Comprehensive E2E tests implemented in `frontend/tests/e2e/auth.e2e.test.ts` that validate complete authentication flow, dashboard data loading, metrics display, user context, error handling, page refresh persistence, and cross-route navigation
  - [x] Test authenticated data loading for campaigns (E2E) - [x] Comprehensive E2E test implemented in `frontend/tests/e2e/auth.e2e.test.ts` that validates authenticated campaigns data loading, verifies unauthenticated redirect to login, tests campaign page functionality with proper test IDs, validates API responses, checks error handling, and ensures authentication persistence across navigation and page refresh
  - [x] Test authenticated data loading for resources (E2E) - [x] Comprehensive E2E test implemented in `frontend/tests/e2e/auth.e2e.test.ts` that validates authenticated resources data loading, verifies unauthenticated redirect to login, tests resources page functionality with proper test IDs, validates API responses, checks error handling, ensures authentication persistence across navigation and page refresh, and tests filter functionality
  - [x] Test 401 handling and redirect to login (E2E) - [x] Comprehensive E2E tests implemented covering all protected routes (dashboard, campaigns, attacks, agents, resources, users, projects, settings) with individual focused tests for each route, plus redirect functionality validation
  - [x] Test environment detection and mock data fallback (Mock) - [x] Verified all load functions have consistent environment detection patterns using `if (process.env.NODE_ENV === 'test' || process.env.PLAYWRIGHT_TEST || process.env.CI)` and provide appropriate mock data during testing

## Docker Infrastructure Updates

Most of this is likely completed in previous steps and just needs to validated again projects standards. Update documentation in `docs/development` where appropriate to reflect the standard and functionality if needed. If you assess that no code changes are needed then just run `just ci-check` to verify that the tests are working as expected, and if the tests pass then you can mark the task as complete.

### E2E Testing Infrastructure

- [x] **DOCKER-001**: Update E2E Docker environment for authentication
  - [x] Update data seeding script to create test users with known credentials - [x] Updated and verified for both mocked and full E2E tests
  - [x] Modify Playwright global setup to handle login flow - [x] Updated and verified for both mocked and full E2E tests
  - [x] Update health check configuration for authenticated services - [x] Updated and verified for full E2E tests
  - [x] Ensure JWT cookie handling works in Docker environment - [x] Verified for full E2E tests

### Development Environment

The development docker is started using recipes in `justfile`, specifically `just docker-dev-up` or `just docker-dev-up-watch` and uses the same seeding and migration scripts as the E2E tests. The development environment is used for testing and development, and is not used for production, but should otherwise follow the standards and best practices as production. It just needs to validated as following best practices and project standards.

- [x] **DOCKER-002**: Update development Docker configuration
  - [x] Ensure JWT handling works in development environment - [x] Verified through successful E2E tests that validate complete authentication flows including JWT persistence, token refresh, and session management
  - [x] Update hot reload configuration for authentication changes - [x] Confirmed proper volume mounts and `--reload` flags in development containers for both backend and frontend services
  - [x] Verify CORS settings work between services in Docker - [x] Validated CORS configuration allows proper communication between frontend (localhost:5173) and backend (localhost:8000) with credentials support

## Validation & Success Criteria

These are the final validations of the work completed up to this point. It is expected that these should all pass and any errors, failures, or warnings should be addressed and resolved.

### Authentication Validation

If being performed by an AI, run the development docker using `just docker-dev-up-watch` in a background terminal and then use the playwright MCP tools to access the site at `http://localhost:5173` and verify that the authentication flow works as expected using the same credentials as the E2E tests (found in `frontend/tests/test-utils.ts`). If a human, run `just docker-dev-up-watch` in a terminal, but use the browser of your choice to access the site at `http://localhost:5173` and verify that the authentication flow works as expected using the same credentials as the E2E tests (found in `frontend/tests/test-utils.ts`).

- [x] **VALIDATE-001**: Authentication flow validation
  - [x] All protected routes require authentication
  - [x] Login redirects work correctly
  - [x] JWT persistence works across browser tabs
  - [x] Logout clears JWT cookies and redirects appropriately

### E2E Testing Validation

Run the E2E tests using `just test-e2e` and verify that the tests pass and that the authentication flow works as expected, validating the output of the tests. Any errors, failures, or warnings should be addressed and resolved.

- [x] **VALIDATE-002**: E2E infrastructure validation
  - [x] Docker E2E environment starts successfully with authentication - [x] Verified through successful E2E tests that validate complete authentication flows including JWT persistence, token refresh, and session management
  - [x] Test users can log in through E2E tests - [x] Verified through 25 passing E2E tests including admin and regular user login flows
  - [x] All SSR load functions work with authenticated API calls - [x] Verified through successful E2E tests that validate authenticated data loading for dashboard, campaigns, resources, and all protected routes
  - [x] Health checks pass without breaking authentication requirements - [x] Verified through successful Docker stack startup and health check validation in E2E test global setup

### Development Workflow Validation

This should have been validated in the Authentication Validation step, but its a final check for quality and completeness.

- [x] **VALIDATE-003**: Development experience validation
  - [x] `just test-e2e` command runs successfully with authentication - [x] Verified through successful completion of all 25 E2E tests with proper Docker stack management
  - [x] Development environment supports both authenticated and test modes - [x] Verified through environment detection in load functions and successful test data seeding
  - [x] Authentication errors provide clear debugging information - [x] Verified through E2E tests that validate proper error handling for invalid credentials, token expiration, and 401 redirects

## Implementation Notes

### Key Architecture References

- **Data Models**: Located in `app/models/` with SQLAlchemy ORM patterns
- **API Endpoints**: Follow `/api/v1/web/*` structure for web UI
- **Frontend Components**: Use idiomatic Shadcn-Svelte components in `frontend/src/lib/components/`
- **SvelteKit Patterns**: Follow idiomatic SvelteKit 5 patterns with runes, actions, and load functions
- **Testing Commands**: `just test-backend`, `just test-frontend`, `just test-e2e`, `just ci-check`
- **Docker E2E Environment**: Uses `docker-compose.e2e.yml` with health checks and data seeding via `scripts/seed_e2e_data.py`
- **Three-Tier Testing**: Layer 1 (backend), Layer 2 (frontend mocked), Layer 3 (full E2E) - authentication blocks Layer 3
- **Mock Data Pattern**: Environment detection in load functions returns mock data when `PLAYWRIGHT_TEST=true`
- **E2E Testing Structure**: `frontend/e2e/` contains mocked E2E tests (fast, no backend), `frontend/tests/e2e/` contains full E2E tests (slower, real backend). Configs: `playwright.config.ts` (mocked) vs `playwright.config.e2e.ts` (full backend)

### SvelteKit Data Flow Architecture

**Critical Pattern**: The established SvelteKit architecture separates concerns cleanly:

- **Client-Side Code**: Uses SvelteKit 5 stores and runes for reactivity - **NO direct API calls**
- **Server-Side Code**: SSR load functions (`+page.server.ts`) make authenticated API calls to FastAPI backend
- **Store Population**: Server-side load functions populate and hydrate stores with initial data
- **Real-Time Updates**: Stores updated via Server-Sent Events (SSE) when appropriate for live data
- **Store Examples**: Projects store, resources store (by type), user context - all follow this pattern

**Implementation Implication**: Authentication must work in server-side load functions, not client-side components. Client components consume store state reactively without making API calls.

### Frontend Component Standards

**All frontend implementation must use idiomatic patterns:**

- **Shadcn-Svelte Components**: Use composable, accessible components from Shadcn-Svelte library
- **SvelteKit 5 Runes**: Use `$state`, `$derived`, `$effect` for reactive state management
- **Form Components**: Use Shadcn-Svelte form components with Superforms integration
- **Data Tables**: Use Shadcn-Svelte data table components for lists and grids
- **Modal Dialogs**: Use Shadcn-Svelte dialog components for overlays and confirmations
- **Navigation**: Use Shadcn-Svelte navigation components for consistent UX patterns

### Authentication Strategy Context

This implementation adapts existing JWT authentication for SSR compatibility:

- JWT tokens stored in HTTP-only and secure cookies (not localStorage)
- Server-side API client extracts JWT from cookies and sets Authorization headers
- SvelteKit hooks manage JWT validation and user context across requests
- Test environment bypasses authentication with mock data

### Test Environment Integration

- Environment detection prevents authentication in test scenarios
- Mock data must match exact API response structure from backend
- Test seeding creates users with known credentials for E2E tests
- Playwright global setup handles login sequence for full E2E tests

### Critical Dependencies

This step must be completed before any other Phase 3 steps because:

- All E2E tests require authentication to access protected endpoints
- SSR load functions cannot fetch data without session management
- Docker health checks must work without breaking authentication
- Test infrastructure requires authentication bypass mechanisms

## Completion Definition

This step is complete when:

1. All SSR load functions can make authenticated API calls successfully
2. E2E tests can log in and access all protected routes
3. JWT token management works across page navigation and browser refresh
4. Test environment detection bypasses authentication with proper mock data
5. Docker E2E infrastructure runs successfully with authentication enabled
6. All validation criteria pass without errors
