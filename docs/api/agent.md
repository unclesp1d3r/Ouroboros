# Agent API (v1)

## Overview

The Agent API (`/api/v1/client/*`) is used by distributed Ouroboros agents to communicate with the server. This API follows the legacy Ruby-on-Rails specification defined in `contracts/v1_api_swagger.json` and maintains strict backward compatibility.

Agents use this API to:

- Register and authenticate with the server
- Receive task assignments and attack configurations
- Submit progress updates and results
- Report errors and performance metrics
- Download attack resources and cracker binaries

## Authentication

All Agent API endpoints (except `/client/authenticate`) require Bearer token authentication:

```http
Authorization: Bearer csa_<agent_id>_<random_string>
```

Tokens are automatically generated during agent registration and are unique per agent.

## Base URL

All Agent API endpoints are prefixed with `/api/v1/client/` or `/api/v1/` (legacy compatibility).

## Endpoints

### Authentication & Configuration

#### `GET /api/v1/client/authenticate`

Verify agent authentication and retrieve agent ID.

**Response:** `AgentAuthenticateResponse`

- `authenticated: bool` - Authentication status
- `agent_id: int` - The authenticated agent's ID

#### `GET /api/v1/client/configuration`

Retrieve agent-specific configuration settings.

**Response:** `AgentConfigurationResponse`

- `config: AdvancedAgentConfiguration` - Agent configuration object
- `api_version: int` - API version number

### Agent Management

#### `GET /api/v1/client/agents/{id}`

Retrieve agent details by ID.

**Parameters:**

- `id: int` - Agent ID

**Response:** `AgentResponseV1`

#### `PUT /api/v1/client/agents/{id}`

Update agent information.

**Parameters:**

- `id: int` - Agent ID

**Request Body:** `AgentUpdateV1`

**Response:** `AgentResponseV1`

#### `POST /api/v1/client/agents/{id}/heartbeat`

Send agent heartbeat to update status and last seen timestamp.

**Parameters:**

- `id: int` - Agent ID

**Request Body:** `AgentHeartbeatRequest`

**Response:** `204 No Content`

#### `POST /api/v1/client/agents/{id}/submit_benchmark`

Submit agent benchmark results.

**Parameters:**

- `id: int` - Agent ID

**Request Body:** `AgentBenchmark`

**Response:** `204 No Content`

#### `POST /api/v1/client/agents/{id}/submit_error`

Report agent errors to the server.

**Parameters:**

- `id: int` - Agent ID

**Request Body:** `AgentErrorV1`

**Response:** `204 No Content`

#### `POST /api/v1/client/agents/{id}/shutdown`

Notify server of agent shutdown.

**Parameters:**

- `id: int` - Agent ID

**Response:** `204 No Content`

### Attack Management

#### `GET /api/v1/client/attacks/{id}`

Retrieve attack configuration by ID.

**Parameters:**

- `id: int` - Attack ID

**Response:** `AttackResponseV1`

#### `GET /api/v1/client/attacks/{id}/hashlist`

Download hash list for the specified attack.

**Parameters:**

- `id: int` - Attack ID

**Response:** Binary hash list file

### Task Management

#### `GET /api/v1/client/tasks/new`

Request a new task assignment.

**Response:** `TaskResponseV1` or `204 No Content` if no tasks available

#### `GET /api/v1/client/tasks/{id}`

Retrieve task details by ID.

**Parameters:**

- `id: int` - Task ID

**Response:** `TaskResponseV1`

#### `POST /api/v1/client/tasks/{id}/accept_task`

Accept an assigned task.

**Parameters:**

- `id: int` - Task ID

**Response:** `204 No Content`

#### `POST /api/v1/client/tasks/{id}/get_zap`

Request zap list (newly cracked hashes) for task.

**Parameters:**

- `id: int` - Task ID

**Response:** Binary zap list file or `204 No Content`

#### `POST /api/v1/client/tasks/{id}/submit_crack`

Submit cracked hash results.

**Parameters:**

- `id: int` - Task ID

**Request Body:** `CrackResultSubmissionV1`

**Response:** `204 No Content`

#### `POST /api/v1/client/tasks/{id}/submit_status`

Submit task status and progress updates.

**Parameters:**

- `id: int` - Task ID

**Request Body:** `TaskStatusUpdateV1`

**Response:** `204 No Content`

#### `POST /api/v1/client/tasks/{id}/abandon_task`

Abandon a task (mark as failed/incomplete).

**Parameters:**

- `id: int` - Task ID

**Response:** `204 No Content`

### Cracker Management

#### `GET /api/v1/client/crackers`

List available cracker binaries and versions.

**Response:** `CrackerListResponseV1`

#### `GET /api/v1/client/crackers/{id}`

Download cracker binary by ID.

**Parameters:**

- `id: int` - Cracker ID

**Response:** Binary cracker file

## Schema Objects

### Agent Schemas

::: app.schemas.agent.AdvancedAgentConfiguration options: show_root_heading: true show_source: false

::: app.schemas.agent.AgentBenchmark options: show_root_heading: true show_source: false

::: app.schemas.agent.AgentErrorV1 options: show_root_heading: true show_source: false

::: app.schemas.agent.AgentResponseV1 options: show_root_heading: true show_source: false

::: app.schemas.agent.AgentUpdateV1 options: show_root_heading: true show_source: false

::: app.schemas.agent.AgentHeartbeatRequest options: show_root_heading: true show_source: false

### Task Schemas

::: app.schemas.task.HashcatResult options: show_root_heading: true show_source: false

::: app.schemas.task.TaskOutV1 options: show_root_heading: true show_source: false

::: app.schemas.task.TaskProgressUpdate options: show_root_heading: true show_source: false

::: app.schemas.task.TaskStatusUpdate options: show_root_heading: true show_source: false

### Attack Schemas

::: app.schemas.attack.AttackOutV1 options: show_root_heading: true show_source: false

### Error Schemas

::: app.schemas.error.ErrorObject options: show_root_heading: true show_source: false

## Error Handling

The Agent API follows the legacy error format defined in `contracts/v1_api_swagger.json`. All errors return JSON with an `error` field:

```json
{
  "error": "Error message description"
}
```

### Common HTTP Status Codes

| Code  | Description           | Example Response                                                        |
| ----- | --------------------- | ----------------------------------------------------------------------- |
| `200` | Success               | `{"authenticated": true, "agent_id": 123}`                              |
| `204` | Success (No Content)  | _(empty response body)_                                                 |
| `401` | Unauthorized          | `{"error": "Invalid or missing authentication token"}`                  |
| `403` | Forbidden             | `{"error": "Agent not authorized for this resource"}`                   |
| `404` | Not Found             | `{"error": "Agent not found"}`                                          |
| `422` | Validation Error      | `{"error": "Invalid request data: missing required field 'hash_type'"}` |
| `429` | Too Many Requests     | `{"error": "Rate limit exceeded. Please retry after 60 seconds"}`       |
| `500` | Internal Server Error | `{"error": "Internal server error occurred"}`                           |

### Error Response Examples

**Authentication Failure:**

```json
{
  "error": "Bad credentials"
}
```

**Resource Not Found:**

```json
{
  "error": "Task with ID 12345 not found"
}
```

**Validation Error:**

```json
{
  "error": "Invalid benchmark data: hash_speed must be a positive number"
}
```

**Rate Limiting:**

```json
{
  "error": "Too many heartbeat requests. Maximum 1 request per 15 seconds"
}
```

## Rate Limiting

Agent API endpoints are subject to rate limiting to prevent abuse. Agents should implement exponential backoff when receiving `429 Too Many Requests` responses.

## Workflow Examples

### Complete Agent Lifecycle

```bash
# 1. Agent authenticates and gets configuration
curl -H "Authorization: Bearer csa_123_abc..." \
    "https://api.example.com/api/v1/client/authenticate"

curl -H "Authorization: Bearer csa_123_abc..." \
    "https://api.example.com/api/v1/client/configuration"

# 2. Agent sends initial heartbeat
curl -X POST \
    -H "Authorization: Bearer csa_123_abc..." \
    -H "Content-Type: application/json" \
    -d '{"status": "idle", "current_task_id": null, "devices_status": {"GPU0": "ready"}}' \
    "https://api.example.com/api/v1/client/agents/123/heartbeat"

# 3. Agent submits benchmark results
curl -X POST \
    -H "Authorization: Bearer csa_123_abc..." \
    -H "Content-Type: application/json" \
    -d '{"hash_type": 0, "runtime": 1000, "hash_speed": 1000000.0, "device": 0}' \
    "https://api.example.com/api/v1/client/agents/123/submit_benchmark"

# 4. Agent requests new task
curl -H "Authorization: Bearer csa_123_abc..." \
    "https://api.example.com/api/v1/client/tasks/new"

# 5. Agent accepts assigned task
curl -X POST \
    -H "Authorization: Bearer csa_123_abc..." \
    "https://api.example.com/api/v1/client/tasks/456/accept_task"

# 6. Agent gets attack configuration
curl -H "Authorization: Bearer csa_123_abc..." \
    "https://api.example.com/api/v1/client/attacks/789"

# 7. Agent downloads hash list
curl -H "Authorization: Bearer csa_123_abc..." \
    "https://api.example.com/api/v1/client/attacks/789/hashlist" \
    -o hashlist.txt

# 8. Agent submits progress updates
curl -X POST \
    -H "Authorization: Bearer csa_123_abc..." \
    -H "Content-Type: application/json" \
    -d '{"status": "running", "progress": 25.5, "estimated_completion": "2024-01-01T15:30:00Z"}' \
    "https://api.example.com/api/v1/client/tasks/456/submit_status"

# 9. Agent submits crack results
curl -X POST \
    -H "Authorization: Bearer csa_123_abc..." \
    -H "Content-Type: application/json" \
    -d '{"hash": "5d41402abc4b2a76b9719d911017c592", "plain_text": "hello"}' \
    "https://api.example.com/api/v1/client/tasks/456/submit_crack"

# 10. Agent completes task
curl -X POST \
    -H "Authorization: Bearer csa_123_abc..." \
    "https://api.example.com/api/v1/client/tasks/456/exhausted"

# 11. Agent shuts down
curl -X POST \
    -H "Authorization: Bearer csa_123_abc..." \
    "https://api.example.com/api/v1/client/agents/123/shutdown"
```

### Error Reporting Workflow

```bash
# Report general agent error
curl -X POST \
    -H "Authorization: Bearer csa_123_abc..." \
    -H "Content-Type: application/json" \
    -d '{
        "message": "GPU temperature exceeded safe limits",
        "severity": "warning",
        "attack_id": null
    }' \
    "https://api.example.com/api/v1/client/agents/123/submit_error"

# Report attack-specific error
curl -X POST \
    -H "Authorization: Bearer csa_123_abc..." \
    -H "Content-Type: application/json" \
    -d '{
        "message": "Hashcat process crashed during mask attack",
        "severity": "error",
        "attack_id": 789
    }' \
    "https://api.example.com/api/v1/client/agents/123/submit_error"
```

### Task Abandonment Workflow

```bash
# Agent encounters issue and abandons task
curl -X POST \
    -H "Authorization: Bearer csa_123_abc..." \
    "https://api.example.com/api/v1/client/tasks/456/abandon_task"

# Agent reports the reason for abandonment
curl -X POST \
    -H "Authorization: Bearer csa_123_abc..." \
    -H "Content-Type: application/json" \
    -d '{
        "message": "Task abandoned due to hardware failure",
        "severity": "error",
        "attack_id": 789
    }' \
    "https://api.example.com/api/v1/client/agents/123/submit_error"
```

## Integration Guidelines

### Authentication Best Practices

1. **Token Storage**: Store agent tokens securely and never log them
2. **Token Validation**: Verify token format before making requests
3. **Error Handling**: Implement proper retry logic for authentication failures
4. **Token Rotation**: Handle token rotation events gracefully

### Request Headers

Always include these headers in your requests:

```http
Authorization: Bearer csa_<agent_id>_<token>
User-Agent: YourAgent/1.0.0
Content-Type: application/json
Accept: application/json
```

### Rate Limiting Handling

Implement exponential backoff when receiving `429` responses:

```python
import time
import random


def make_request_with_backoff(url, headers, data=None, max_retries=3):
    for attempt in range(max_retries):
        response = requests.post(url, headers=headers, json=data)

        if response.status_code != 429:
            return response

        # Exponential backoff with jitter
        delay = (2**attempt) + random.uniform(0, 1)
        time.sleep(delay)

    return response  # Return last response after max retries
```

### Heartbeat Implementation

Agents should send heartbeats every 15-60 seconds:

```python
import threading
import time


class HeartbeatManager:
    def __init__(self, agent_id, token, interval=30):
        self.agent_id = agent_id
        self.token = token
        self.interval = interval
        self.running = False
        self.current_task_id = None
        self.devices_status = {}

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._heartbeat_loop)
        self.thread.start()

    def stop(self):
        self.running = False
        if hasattr(self, "thread"):
            self.thread.join()

    def _heartbeat_loop(self):
        while self.running:
            try:
                self._send_heartbeat()
            except Exception as e:
                print(f"Heartbeat failed: {e}")

            time.sleep(self.interval)

    def _send_heartbeat(self):
        data = {
            "status": "running" if self.current_task_id else "idle",
            "current_task_id": self.current_task_id,
            "devices_status": self.devices_status,
        }

        response = requests.post(
            f"https://api.example.com/api/v1/client/agents/{self.agent_id}/heartbeat",
            headers={"Authorization": f"Bearer {self.token}"},
            json=data,
        )

        if response.status_code not in [200, 204]:
            raise Exception(f"Heartbeat failed: {response.status_code}")
```

### Progress Reporting

Report task progress regularly during execution:

```python
class TaskProgressReporter:
    def __init__(self, task_id, token):
        self.task_id = task_id
        self.token = token
        self.last_progress = 0
        self.last_report_time = 0

    def report_progress(self, progress, force=False):
        current_time = time.time()

        # Report every 5% progress or every 30 seconds
        if (
            progress - self.last_progress >= 5.0
            or current_time - self.last_report_time >= 30
            or force
        ):
            data = {
                "status": "running",
                "progress": progress,
                "estimated_completion": self._calculate_eta(progress),
            }

            response = requests.post(
                f"https://api.example.com/api/v1/client/tasks/{self.task_id}/submit_status",
                headers={"Authorization": f"Bearer {self.token}"},
                json=data,
            )

            if response.status_code in [200, 204]:
                self.last_progress = progress
                self.last_report_time = current_time

    def _calculate_eta(self, progress):
        if progress <= 0:
            return None

        elapsed = time.time() - self.start_time
        remaining = (elapsed / progress) * (100 - progress)
        eta = datetime.now() + timedelta(seconds=remaining)

        return eta.isoformat()
```

## Compatibility

This API maintains strict backward compatibility with the legacy Ruby-on-Rails Ouroboros implementation. Breaking changes are prohibited. All new features requiring API changes will be implemented in Agent API v2 (planned for future release).

### Version Compatibility Matrix

| Agent Version | API Version | Compatibility         |
| ------------- | ----------- | --------------------- |
| 1.0.x - 1.2.x | v1.0        | ✅ Full               |
| 1.3.x - 1.5.x | v1.1        | ✅ Full               |
| 2.0.x+        | v1.3        | ✅ Full               |
| Future        | v2.0        | 🔄 Migration Required |
