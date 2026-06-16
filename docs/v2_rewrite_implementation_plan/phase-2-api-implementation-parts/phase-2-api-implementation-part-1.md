# Agent API (High Priority)

The agent API is used by the agent to register, heartbeat, and report results. It is also used by the distributed Ouroboros agents to obtain task assignments and submit results.

## Agent Authentication & Session Management

- [x] Registration endpoint (`POST /api/v2/client/agents/register`)

  - Accepts client signature, hostname, and agent type
  - Returns token in format: `csa_<agent_id>_<token>`

- [x] Heartbeat endpoint (`POST /api/v2/client/agents/heartbeat`)

  - Must include headers:

    - `Authorization: Bearer csa_<agent_id>_<token>`

  - Rate limited to once every 15 seconds

  - Tracks missed heartbeats and version drift

- [x] State Management

  - Accepts status updates (`pending`, `active`, `error`, `offline`)
  - Fails if state not in enum
  - Heartbeats update `last_seen_at`, `last_ipaddress`

## Attack Distribution

- [x] Attack Configuration Endpoint

  - Fetches full attack spec from server (mask, rules, etc.)
  - Validates agent capability before sending (upon startup an agent performs a hashcat benchmark and reports the results, which are stored in the database, and used to validate which hash types an agent can crack. Campaigns for hash lists that the agent cannot crack are not assigned to the agent.)
  - Note: Resource management fields (word_list_id, rule_list_id, mask_list_id, presigned URLs) will be fully supported in Phase 3. Endpoint and schema are forward-compatible.

- [x] Resource Management

  - Generates presigned URLs for agents
  - Enforces hash verification pre-task

- [x] Task Assignment

  - One task per agent (enforced)
  - Includes keyspace chunk (skip, limit fields now present)
  - Includes hash file, dictionary IDs (deferred to Phase 3 resource management)

- [x] Progress Tracking

  - Agents send updates to `POST /api/v1/client/tasks/{id}/progress`
  - Includes `progress_percent`, `keyspace_processed`

- [x] Result Collection

  - Payload includes JSON structure of cracked hashes, metadata

- [x] Legacy Agent API

  - Maintains compatibility with legacy agent API (v1); see [swagger.json](../../../swagger.json)
  - Handles `GET /api/v1/agents/{id}`
  - Handles `POST /api/v1/agents/{id}/benchmark`
  - Handles `POST /api/v1/agents/{id}/error`
  - Handles `POST /api/v1/agents/{id}/shutdown`

---
