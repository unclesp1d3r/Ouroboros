---

## inclusion: fileMatch fileMatchPattern: [docs/v2_rewrite_implementation_plan/phase-3-web-ui-implementation/\*.md]

# Phase 3 Task Verification Patterns

## Overview

This rule defines the verification patterns and completion criteria for Phase 3 Web UI implementation tasks, based on successful task execution workflows.

## Task Execution Process

### 1. Task Identification

- Read the entire Phase 3 step document before beginning
- Identify the next group of unchecked tasks in the checklist
- Select the **first unchecked task** in that group
- Focus only on that specific task

### 2. Verification Methods

#### Direct Observation (Preferred)

- Start development environment: `just docker-dev-up-watch`
- Use Playwright MCP tools to navigate to `http://localhost:5173`
- Verify functionality through direct interaction with the UI
- Test authentication flows and authenticated API calls
- Confirm UI components match design specifications

#### Code Review (When Needed)

- Review relevant source files for implementation completeness
- Check SSR load functions in `+page.server.ts` files
- Verify component usage of Shadcn-Svelte patterns
- Confirm SvelteKit 5 runes implementation

### 3. Task Completion Criteria

#### For Verification Tasks

- Functionality works as specified through direct observation
- No code changes required if implementation is correct
- Mark task complete in checklist
- Provide brief summary of what was verified

#### For Implementation Tasks

- Make necessary code changes using idiomatic patterns
- Run formatting: `just format`
- Add or update tests for correctness
- Run test suites: `just test` and `just frontend-test`
- Fix failing tests
- Run linters: `just check` and `just frontend-lint`
- Fix all linter issues
- Run final validation: `just ci-check`

### 4. Design Compliance

#### UI Component Requirements

- Use idiomatic Shadcn-Svelte components
- Follow SvelteKit 5 patterns with runes ($state, $derived, $effect)
- Implement proper SSR load functions with authenticated API calls
- Use Superforms v2 for all form handling
- Apply consistent responsive design patterns

#### Authentication Integration

- All pages must work with authenticated API calls
- Handle 401 redirects to login appropriately
- Show proper loading states during authentication
- Display user context and role-based permissions

### 5. Testing Requirements

#### Test Structure

- Mock E2E tests in `frontend/e2e/` (fast, no backend)
- Full E2E tests in `frontend/tests/e2e/` (slower, real backend)
- Use existing test utilities in `frontend/tests/test-utils.ts`

#### Test Execution

- Run `just frontend-test` for mocked E2E tests
- Run `just test-e2e` for full E2E tests (requires Docker setup)
- Environment detection for test scenarios

## Common Verification Patterns

### Dashboard Verification

```typescript
// Verify dashboard loads with authenticated API calls
- Login with test credentials
- Confirm dashboard displays status cards
- Verify data comes from authenticated API calls
- Check proper Shadcn-Svelte component usage
```

### Form Verification

```typescript
// Verify form functionality
- Test form validation (client and server-side)
- Confirm Superforms v2 integration
- Verify Zod schema validation
- Test success/error feedback
```

### Navigation Verification

```typescript
// Verify navigation functionality
- Test sidebar navigation between sections
- Confirm breadcrumb consistency
- Verify deep linking support
- Test responsive behavior
```

## Task Completion Workflow

### No Code Changes Required

1. Verify functionality through direct observation
2. Confirm implementation meets task requirements
3. Mark task complete in checklist
4. Provide verification summary
5. **Do not run `just ci-check`** (no changes made)

### Code Changes Required

1. Implement necessary changes
2. Run formatting and linting
3. Update/add tests as needed
4. Fix any failing tests
5. Run `just ci-check` for final validation
6. Mark task complete in checklist
7. Provide implementation summary

## File References

### Key Implementation Files

- Dashboard: [+page.svelte](mdc:Ouroboros/frontend/src/routes/+page.svelte)
- SSR Load Functions: [+page.server.ts](mdc:Ouroboros/frontend/src/routes/+page.server.ts)
- Component Library: [components/ui/](mdc:Ouroboros/frontend/src/lib/components/ui)
- Stores: [stores/](mdc:Ouroboros/frontend/src/lib/stores)
- Schemas: [schemas/](mdc:Ouroboros/frontend/src/lib/schemas)

### Testing Files

- Mock E2E Tests: [e2e/](mdc:Ouroboros/frontend/e2e)
- Full E2E Tests: [tests/e2e/](mdc:Ouroboros/frontend/tests/e2e)
- Test Utilities: [test-utils.ts](mdc:Ouroboros/frontend/tests/test-utils.ts)

### Configuration Files

- OpenAPI Contract: [current_api_openapi.json](mdc:Ouroboros/contracts/current_api_openapi.json)
- Playwright Config (Mock): [playwright.config.ts](mdc:Ouroboros/frontend/playwright.config.ts)
- Playwright Config (E2E): [playwright.config.e2e.ts](mdc:Ouroboros/frontend/playwright.config.e2e.ts)

## Best Practices

### Verification Focus

- Focus on the specific task requirements
- Don't over-verify functionality outside the task scope
- Use direct observation when possible
- Confirm design compliance with referenced specifications

### Implementation Standards

- Follow idiomatic SvelteKit 5 patterns
- Use proper Shadcn-Svelte components
- Implement comprehensive error handling
- Maintain consistent authentication integration

### Testing Strategy

- Implement both mock and full E2E tests where specified
- Use environment detection for test scenarios
- Maintain test coverage for critical workflows
- Fix failing tests before marking tasks complete

## Anti-Patterns to Avoid

- Running `just ci-check` when no code changes were made
- Implementing functionality outside the specific task scope
- Skipping direct observation verification
- Marking tasks complete without proper validation
- Making unnecessary code changes for verification tasks
