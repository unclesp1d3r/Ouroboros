# Ouroboros Agent & Authentication API Reference

This document provides a comprehensive reference for all Ouroboros API endpoints that are NOT part of the `/api/v1/web/*` or `/api/v1/control/*` interfaces. These endpoints are primarily used by Ouroboros agents and authentication systems.

---

## Table of Contents

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=2 --minlevel=1 -->

- [Ouroboros Agent & Authentication API Reference](#ouroboros-agent--authentication-api-reference)
  - [Table of Contents](#table-of-contents)
  - [Authentication](#authentication)
  - [General Authentication Endpoints](#general-authentication-endpoints)
  - [Agent Configuration](#agent-configuration)
  - [Agent Authentication](#agent-authentication)
  - [Agent Management](#agent-management)
  - [Task Management](#task-management)
  - [Attack Management](#attack-management)
  - [Cracker Management](#cracker-management)
  - [Error Handling](#error-handling)
  - [API Patterns](#api-patterns)
  - [API Version Compatibility](#api-version-compatibility)
  - [Security Considerations](#security-considerations)
  - [Performance Notes](#performance-notes)

<!-- mdformat-toc end -->

---

## Authentication

All agent API endpoints require authentication via the `Authorization` header:

```http
Authorization: Bearer <agent_token>
```

Agent tokens follow the format: `csa_<agent_id>_<random_string>`

## General Authentication Endpoints

### POST `/api/v1/auth/login`

**Summary:** User login with email and password

**Parameters:**

- `email` (query, required): User email address
- `password` (query, required): User password

**Responses:**

- `200`: Successful login - Returns authentication token
- `422`: Validation error

**Example:**

```http
POST /api/v1/auth/login?email=user@example.com&password=secret123
```

### POST `/api/v1/auth/jwt/login`

**Summary:** JWT-based login

**Request Body:** `application/x-www-form-urlencoded`

- Username/password form data

**Responses:**

- `200`: Successful login - Returns JWT token
- `422`: Validation error

## Agent Configuration

### GET `/api/v1/client/configuration`

**Summary:** Get agent configuration

**Description:** Returns the configuration for the agent that has been set by the administrator on the server. The configuration is stored in the database and can be updated by the administrator on the server and is global, but specific to the individual agent. Client should cache the configuration and only request a new configuration if the agent is restarted or if the configuration has changed.

**Parameters:**

- `Authorization` (header, required): Bearer token

**Responses:**

- `200`: Successful - Returns `AgentConfigurationResponse`
- `401`: Unauthorized
- `404`: Agent not found
- `422`: Validation error

### GET `/api/v1/configuration`

**Summary:** Get agent configuration (legacy v1 endpoint)

**Description:** Legacy endpoint for agent configuration retrieval. Same functionality as `/api/v1/client/configuration`.

**Parameters:**

- `Authorization` (header, required): Bearer token

**Responses:**

- `200`: Successful - Returns `AgentConfigurationResponse`
- `401`: Unauthorized
- `404`: Agent not found
- `422`: Validation error

## Agent Authentication

### GET `/api/v1/client/authenticate`

**Summary:** Authenticate client

**Description:** Authenticates the client. This is used to verify that the client is able to connect to the server.

**Parameters:**

- `Authorization` (header, required): Bearer token

**Responses:**

- `200`: Successful - Returns `AgentAuthenticateResponse` with `authenticated: true` and `agent_id`
- `401`: Unauthorized - Returns `ErrorObject` with "Bad credentials" message
- `422`: Validation error

**Example Response:**

```json
{
  "authenticated": true,
  "agent_id": 2624
}
```

### GET `/api/v1/authenticate`

**Summary:** Authenticate client (legacy v1 endpoint)

**Description:** Legacy endpoint for client authentication. Same functionality as `/api/v1/client/authenticate`.

**Parameters:**

- `Authorization` (header, required): Bearer token

**Responses:**

- `200`: Successful - Returns `AgentAuthenticateResponse`
- `401`: Unauthorized - Returns `ErrorObject`
- `422`: Validation error

## Agent Management

### GET `/api/v1/client/agents/{id}`

**Summary:** Get agent by ID

**Description:** Get agent details by ID. Requires agent authentication.

**Parameters:**

- `id` (path, required): Agent ID
- `Authorization` (header, required): Bearer token

**Responses:**

- `200`: Successful - Returns `AgentResponseV1`
- `422`: Validation error

### PUT `/api/v1/client/agents/{id}`

**Summary:** Update agent

**Description:** Update agent information. Requires agent authentication.

**Parameters:**

- `id` (path, required): Agent ID

**Request Body:** `AgentUpdateV1` schema

**Responses:**

- `200`: Successful - Returns `AgentResponseV1`
- `422`: Validation error

### POST `/api/v1/client/agents/{id}/submit_benchmark`

**Summary:** Submit agent benchmark results

**Description:** Submit agent benchmark results. Requires agent authentication.

**Parameters:**

- `id` (path, required): Agent ID
- `Authorization` (header, required): Bearer token

**Request Body:** `AgentBenchmark` schema

**Responses:**

- `204`: Successful - No content
- `422`: Validation error

### POST `/api/v1/client/agents/{id}/submit_error`

**Summary:** Submit agent error

**Description:** Submit agent error. Requires agent authentication.

**Parameters:**

- `id` (path, required): Agent ID
- `Authorization` (header, required): Bearer token

**Request Body:** `AgentErrorV1` schema

**Responses:**

- `204`: Successful - No content
- `422`: Validation error

### POST `/api/v1/client/agents/{id}/shutdown`

**Summary:** Shutdown agent

**Description:** Shutdown agent. Requires agent authentication.

**Parameters:**

- `id` (path, required): Agent ID
- `Authorization` (header, required): Bearer token

**Responses:**

- `204`: Successful - No content
- `422`: Validation error

### POST `/api/v1/client/agents/{id}/heartbeat`

**Summary:** Agent heartbeat

**Description:** Agent sends a heartbeat to update its status and last seen timestamp. Contract-compliant endpoint.

**Parameters:**

- `id` (path, required): Agent ID
- `Authorization` (header, required): Bearer token

**Request Body:** `AgentHeartbeatRequest` schema

**Responses:**

- `204`: Successful - No content
- `422`: Validation error

## Task Management

### GET `/api/v1/client/tasks/new`

**Summary:** Request a new task from server

**Description:** Request a new task from the server, if available. Compatibility layer for v1 API.

**Parameters:**

- `Authorization` (header, required): Bearer token

**Responses:**

- `200`: Successful - Returns task data
- `422`: Validation error

### GET `/api/v1/client/tasks/{id}`

**Summary:** Request task information

**Description:** Request the task information from the server. Requires agent authentication and assignment.

**Parameters:**

- `id` (path, required): Task ID
- `Authorization` (header, required): Bearer token

**Responses:**

- `200`: Successful - Returns `TaskOutV1`
- `404`: Task not found
- `401`: Unauthorized
- `403`: Forbidden
- `422`: Validation error

### POST `/api/v1/client/tasks/{id}/accept_task`

**Summary:** Accept task

**Description:** Accept an offered task from the server. Sets the task status to running and assigns it to the agent.

**Parameters:**

- `id` (path, required): Task ID
- `Authorization` (header, required): Bearer token

**Responses:**

- `204`: Task accepted successfully
- `422`: Task already completed
- `404`: Task not found for agent
- `401`: Unauthorized
- `403`: Forbidden

### POST `/api/v1/client/tasks/{id}/submit_status`

**Summary:** Submit task status update

**Description:** Submit a status update for a running task. This is the main status heartbeat endpoint for agents.

**Parameters:**

- `id` (path, required): Task ID
- `Authorization` (header, required): Bearer token

**Request Body:** `TaskStatusUpdate` schema

**Responses:**

- `204`: Status received successfully
- `202`: Status received successfully, but stale
- `410`: Status received successfully, but task paused
- `422`: Malformed status data
- `404`: Task not found
- `401`: Unauthorized
- `403`: Forbidden
- `409`: Task not running

### POST `/api/v1/client/tasks/{id}/progress`

**Summary:** Update task progress

**Description:** Agents send progress updates for a task. Compatibility layer for v1 API.

**Parameters:**

- `id` (path, required): Task ID
- `Authorization` (header, required): Bearer token

**Request Body:** `TaskProgressUpdate` schema

**Responses:**

- `204`: Successful - No content
- `422`: Validation error

### POST `/api/v1/client/tasks/{id}/submit_crack`

**Summary:** Submit cracked hash result

**Description:** Submit a cracked hash result for a task. Compatibility layer for v1 API.

**Parameters:**

- `id` (path, required): Task ID
- `Authorization` (header, required): Bearer token

**Request Body:** `HashcatResult` schema

**Responses:**

- `200`: Successful - Returns confirmation
- `422`: Validation error

### POST `/api/v1/client/tasks/{id}/exhausted`

**Summary:** Notify of exhausted task

**Description:** Notify the server that the task is exhausted. This will mark the task as completed.

**Parameters:**

- `id` (path, required): Task ID
- `Authorization` (header, required): Bearer token

**Responses:**

- `204`: Successful - No content
- `404`: Task not found
- `401`: Unauthorized
- `403`: Forbidden
- `422`: Task already completed or exhausted

### POST `/api/v1/client/tasks/{id}/abandon`

**Summary:** Abandon task

**Description:** Abandon a task. This will mark the task as abandoned. Usually used when the client is unable to complete the task.

**Parameters:**

- `id` (path, required): Task ID
- `Authorization` (header, required): Bearer token

**Responses:**

- `204`: Successful - No content
- `422`: Already completed
- `404`: Task not found
- `401`: Unauthorized
- `403`: Forbidden

### GET `/api/v1/client/tasks/{id}/get_zaps`

**Summary:** Get completed hashes

**Description:** Gets the completed hashes for a task. This is a text file that should be added to the monitored directory to remove the hashes from the list during runtime.

**Parameters:**

- `id` (path, required): Task ID
- `Authorization` (header, optional): Bearer token

**Responses:**

- `200`: Successful - Returns text/plain content
- `422`: Already completed
- `404`: Task not found
- `401`: Unauthorized
- `403`: Forbidden

## Attack Management

### GET `/api/v1/client/attacks/{id}`

**Summary:** Get attack by ID

**Description:** Returns an attack by id. This is used to get the details of an attack.

**Parameters:**

- `id` (path, required): Attack ID
- `Authorization` (header, required): Bearer token

**Responses:**

- `200`: Successful - Returns `AttackOutV1`
- `422`: Validation error

### GET `/api/v1/client/attacks/{id}/hash_list`

**Summary:** Get hash list for attack

**Description:** Returns the hash list for an attack as a text file. Each line is a hash value. Requires agent authentication.

**Parameters:**

- `id` (path, required): Attack ID
- `Authorization` (header, required): Bearer token

**Responses:**

- `200`: Successful - Returns text/plain content
- `404`: Record not found
- `401`: Unauthorized
- `403`: Forbidden
- `422`: Validation error

## Cracker Management

### GET `/api/v1/client/crackers/check_for_cracker_update`

**Summary:** Check for cracker update

**Description:** Checks for an update to the cracker and returns update info if available.

**Parameters:**

- `version` (query, required): Current cracker version (semver)
- `operating_system` (query, required): Operating system (windows, linux, darwin)

**Responses:**

- `200`: Successful - Returns `CrackerUpdateResponse`
- `400`: Bad request - Returns `ErrorObject`
- `401`: Unauthorized - Returns `ErrorObject`
- `422`: Validation error

**Example:**

```http
GET /api/v1/client/crackers/check_for_cracker_update?version=6.2.6&operating_system=linux
```

## Error Handling

### Common Error Responses

**401 Unauthorized:**

```json
{
  "error": "Bad credentials"
}
```

**422 Validation Error:**

```json
{
  "detail": [
    {
      "loc": [
        "body",
        "field"
      ],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**404 Not Found:**

```json
{
  "detail": "Record not found"
}
```

### Error Codes by Endpoint

- **Authentication endpoints**: 401 (unauthorized), 422 (validation)
- **Agent endpoints**: 401 (unauthorized), 403 (forbidden), 404 (not found), 422 (validation)
- **Task endpoints**: 401 (unauthorized), 403 (forbidden), 404 (not found), 409 (conflict), 410 (gone), 422 (validation)
- **Attack endpoints**: 401 (unauthorized), 403 (forbidden), 404 (not found), 422 (validation)

## API Patterns

### Agent Lifecycle

1. **Authentication**: `GET /api/v1/client/authenticate`
2. **Configuration**: `GET /api/v1/client/configuration`
3. **Heartbeat**: `POST /api/v1/client/agents/{id}/heartbeat`
4. **Task Request**: `GET /api/v1/client/tasks/new`
5. **Task Accept**: `POST /api/v1/client/tasks/{id}/accept_task`
6. **Status Updates**: `POST /api/v1/client/tasks/{id}/submit_status`
7. **Submit Results**: `POST /api/v1/client/tasks/{id}/submit_crack`
8. **Task Completion**: `POST /api/v1/client/tasks/{id}/exhausted`
9. **Shutdown**: `POST /api/v1/client/agents/{id}/shutdown`

### Task States

- **New**: Task is available for assignment
- **Running**: Task is being executed by an agent
- **Paused**: Task execution is temporarily stopped
- **Completed**: Task has finished successfully
- **Exhausted**: Task keyspace has been fully explored
- **Abandoned**: Task was abandoned by the agent

### Authentication Flow

1. Agent obtains token during registration
2. All API calls include `Authorization: Bearer <token>`
3. Server validates token and returns appropriate response
4. 401 responses indicate invalid/expired tokens

### Status Updates

Agents should send periodic status updates while executing tasks:

- **Frequency**: Every 10-30 seconds during active execution
- **Content**: Progress information, hash rate, temperature, etc.
- **Response Codes**:
  - 204: Continue execution
  - 202: Status accepted but stale
  - 410: Task paused, stop execution

### Error Reporting

Agents should report errors using the dedicated error endpoint:

- **Endpoint**: `POST /api/v1/client/agents/{id}/submit_error`
- **Content**: Structured error information
- **Timing**: Immediately when errors occur

### Resource Management

- **Hash Lists**: Downloaded via `GET /api/v1/client/attacks/{id}/hash_list`
- **Completed Hashes**: Retrieved via `GET /api/v1/client/tasks/{id}/get_zaps`
- **Updates**: Checked via `GET /api/v1/client/crackers/check_for_cracker_update`

## API Version Compatibility

These endpoints represent the v1 Agent API, which is locked to the contract defined in `contracts/v1_api_swagger.json`. All endpoints must maintain exact compatibility with the legacy Ruby-on-Rails version of Ouroboros.

Key compatibility requirements:

- Field names and types must match exactly
- Response schemas are immutable
- Breaking changes are prohibited
- New functionality should be added to v2 API when available

## Security Considerations

- All agent communications require valid bearer tokens
- Tokens are bound to specific agents and cannot be shared
- Failed authentication attempts should be logged
- Rate limiting may be applied to prevent abuse
- All communications should use HTTPS in production

## Performance Notes

- Configuration should be cached locally by agents
- Heartbeat frequency should be configurable
- Status updates should be batched when possible
- Large hash lists may require streaming or chunked downloads
- Error reporting should be throttled to prevent spam
