# v2 Agent API Removal & v1 Decoupling Checklist - Completed

This checklist provides a step-by-step plan to fully decouple and remove the v2 Agent API implementation from Ouroboros, while ensuring the v1 Agent API remains fully functional and strictly compliant with the legacy OpenAPI specification (`contracts/v1_api_swagger.json`).

---

## Table of Contents

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=2 --minlevel=1 -->

- [v2 Agent API Removal & v1 Decoupling Checklist - Completed](#v2-agent-api-removal--v1-decoupling-checklist---completed)
  - [Table of Contents](#table-of-contents)
  - [Context](#context)
  - [Agent API Router File Structure](#agent-api-router-file-structure)
  - [Checklist](#checklist)
  - [Final Validation](#final-validation)
  - [Directives](#directives)

<!-- mdformat-toc end -->

---

## Context

- The v1 Agent API (endpoints under `/api/v1/client/*`) is a strict compatibility layer for legacy agents and must match `contracts/v1_api_swagger.json` exactly.
- The current v1 compatibility endpoints are thin wrappers around v2 endpoint logic and service functions.
- The v2 Agent API is not in use and is inconsistent with project direction.
- The goal is to:
  - Decouple v1 from v2 by duplicating or refactoring shared service logic. The priority should be given to preserving the v1 API and functionality.
  - Remove all v2 endpoints and v2-only service code.
  - Ensure v1 remains fully functional and compliant.

---

## Agent API Router File Structure

All v1 Agent API endpoints under `/api/v1/client/*` must be implemented in their own router files under `app/api/v1/endpoints/agent/`, with one file per resource. The mapping is as follows:

| Endpoint Path                  | Router File                              |
| ------------------------------ | ---------------------------------------- |
| `/api/v1/client/agents/*`      | `app/api/v1/endpoints/agent/agent.py`    |
| `/api/v1/client/attacks/*`     | `app/api/v1/endpoints/agent/attacks.py`  |
| `/api/v1/client/tasks/*`       | `app/api/v1/endpoints/agent/tasks.py`    |
| `/api/v1/client/crackers/*`    | `app/api/v1/endpoints/agent/crackers.py` |
| `/api/v1/client/configuration` | `app/api/v1/endpoints/agent/general.py`  |
| `/api/v1/client/authenticate`  | `app/api/v1/endpoints/agent/general.py`  |

> **Standard:** All root-level, non-resource endpoints for an API interface (e.g., Agent, Web, TUI) should be grouped in a `general.py` file under the relevant endpoints directory.

**Example:**

- The route `/api/v1/client/agents/{id}/shutdown` is implemented in `app/api/v1/endpoints/agent/agent.py`.
- The route `/api/v1/client/attacks/{id}` is implemented in `app/api/v1/endpoints/agent/attacks.py`.

---

## Checklist

### 1. Decouple v1 Compatibility Endpoints from v2 Logic

- [x] For each v1 compatibility endpoint in `app/api/v1/endpoints/client_compat.py`:
  - [x] Replace all direct calls to v2 endpoint functions (e.g., `v2_register_agent`, `v2_agent_heartbeat`, etc.) with direct calls to service-layer functions.
  - [x] If the service logic is not unique to v2 (i.e., it is version-agnostic), rename the function to remove the `_v2` suffix and update all references accordingly.
  - [x] If the service logic is v2-specific, duplicate and adapt it for v1, ensuring:
    - [x] All request/response schemas match `contracts/v1_api_swagger.json`.
    - [x] All business logic, error handling, and side effects are preserved.
  - [x] For endpoints with no suitable service function, implement new service logic as needed, matching v1 requirements.
- [x] Move all v1 Agent API endpoints to resource- and interface-specific subfolders under `app/api/v1/endpoints/` as described in the rules (e.g., `agent/`, `tasks/`, `attacks/`, `crackers/`).
  - [x] Each `/api/v1/client/<resource>` endpoint must be implemented in its own router file under `app/api/v1/endpoints/agent/<resource>.py`.
  - [x] See the table above for the required mapping.
- [x] Remove all imports of `app.api.v2.endpoints.client` from v1 code.
- [x] Update or add tests to cover the decoupled v1 endpoints.
- [x] Run all v1 endpoint tests and verify:
  - [x] All endpoints function as expected.
  - [x] All responses match `contracts/v1_api_swagger.json` (fields, types, status codes).
  - [x] **Patched submit_task_status_v1 to catch TaskNotFoundError from both agent_service and task_service; confirmed with passing test_task_v1_submit_status_not_found.**
- [x] Ensure all v1 agent API endpoints are in `app/api/v1/endpoints/agent`, and that `/api/v1/client/configuration` and `/api/v1/client/authenticate` are available at the correct paths.
  - [x] Fixed router registration; all tests now pass.

### 2. Remove v2 Agent API Endpoints

- [x] Delete `app/api/v2/router.py` and `app/api/v2/endpoints/client.py`.
- [x] Remove v2 API router registration from `app/main.py`.
- [x] Remove v2-specific endpoint tests (e.g., `tests/integration/v2/agent/`, etc.).
- [x] Ensure all shared service logic required by v1 remains intact.
- [x] Run all v1 endpoint tests and verify full functionality and compliance.

### 3. Remove v2-Only Service Functions

- [x] Identify all service functions in `app/core/services/client_service.py` and related modules that are used exclusively by v2 endpoints.
- [x] Remove these v2-only service functions and any associated helpers.
- [x] Remove v2-specific service tests.
- [x] Run all v1 endpoint tests and verify full functionality and compliance.

### 4. Remove v1 Type Adapters and Wrappers

- [x] Identify all v1-specific request/response types (e.g., TaskOutV1, AttackOutV1) that exist solely to ensure `contracts/v1_api_swagger.json` compliance.
- [x] Make these types the canonical v1 response/request types for all v1 agent API endpoints.
- [x] Remove any redundant wrappers or adapters that convert between v2 and v1 types.
- [x] Update all v1 endpoints to use the canonical v1 types directly.
- [x] Run all v1 endpoint tests and verify full functionality and compliance.

### 5. Cleanup Lingering Unused Code and Tests

- [x] Remove any unused types, endpoints, or test files that are no longer referenced after the refactor.
  - [x] Deleted obsolete agents.py and agents.cpython-313.pyc; confirmed all tests pass.
- [x] Rename and move any remaining v1 endpoints to resource- and interface-specific subfolders under `app/api/v1/endpoints/` as described in the rules (e.g., `agent/*` for Agent API endpoints, `webui/*` for WebUI API endpoints, `tui/*` for TUI API endpoints). See the rules for more details. For the purposes of this checklist, we will only be moving the agent endpoints.
  - [x] Each `/api/v1/client/<resource>` endpoint must be implemented in its own router file under `app/api/v1/endpoints/agent/<resource>.py`.
- [x] Run all v1 endpoint tests and verify no regressions or compliance issues.

---

## Final Validation

- [x] Run a full test suite (`just test` or equivalent) and ensure all tests pass.
- [x] Run contract/API schema validation against `contracts/v1_api_swagger.json` to confirm:
  - [x] All v1 Agent API endpoints match the OpenAPI spec exactly (fields, enums, status codes, error envelopes).
- [x] Review code for any lingering references to v2 endpoints, routers, or service logic.
- [x] Confirm that the v1 Agent API is fully functional, stable, and ready for production use.

<!--
2024-06-10: All v2 Agent API removal and v1 decoupling checklist items completed. All tests pass, linter errors resolved (except for non-blocking warnings), and v1 API is stable and compliant. -- Skirmish
-->

---

## Directives

- Each checklist item should be completed and validated before proceeding to the next.
- The highest priority is to maintain strict v1 compatibility and avoid regressions during the removal of v2 logic.
- As the items are completed, run `just test` to verify functionality and compliance. If all tests pass, the next item can be checked off. If any tests fail, fix the issue and verify the tests pass before checking off the item.
- Ensure all v1 endpoints are moved to resource- and interface-specific subfolders under `app/api/v1/endpoints/` as described in the rules (e.g., `agent/`, `tasks/`, `attacks/`, `crackers/`).
  - Each `/api/v1/client/<resource>` endpoint must be implemented in its own router file under `app/api/v1/endpoints/agent/<resource>.py`.
- Ensure all v1 endpoint follow the service interface pattern as described in the rules. (see `.cursor/rules/code/service_interface.mdc`)
- Attempt to address any linting or type checking errors or warnings.
- Despite requirements that were introduced into v2, there is NO requirement to verify the user-agent header in v1 and this should not be a blocker for implementing any v1 routes.
- Please add code comments for any meaningful changes to the codebase so we can remember why we made the changes.
