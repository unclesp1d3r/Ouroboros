# Agent & Task Monitoring

## Overview

Implement Control API endpoints for agent fleet monitoring and task tracking. Enables users to monitor agent availability, performance, and task execution status.

## Context

Users need visibility into agent fleet health and task execution for troubleshooting and capacity planning. The Control API provides read-only monitoring; agent registration is handled by the Agent API.

**Spec References:**

- `spec:84e8066f-28f2-4489-aeb6-0aeceb19dcde/d3caa175-100a-4242-b8b4-0c8139a48034` (Core Flows - Flow 3: Real-Time Monitoring, Steps 4-5)
- `spec:84e8066f-28f2-4489-aeb6-0aeceb19dcde/874b33d9-e442-4af3-98d3-e08cb71a007c` (Tech Plan - Data Model)

## Scope

**In Scope:**

- Agent fleet summary endpoint
- Agent list endpoint with filtering
- Agent detail endpoint (capabilities, performance, errors)
- Task list endpoint with filtering
- Task detail endpoint with logs
- Integration with existing `file:app/core/services/agent_service.py`
- Integration with existing `file:app/core/services/task_service.py`

**Out of Scope:**

- Agent registration (Agent API responsibility)
- Agent configuration updates (separate concern)
- Task creation (automatic via campaign execution)

## Implementation Guidance

**Endpoints:**

- `GET /api/v1/control/agents/summary` - Agent fleet summary
- `GET /api/v1/control/agents` - List agents
- `GET /api/v1/control/agents/{id}` - Get agent details
- `GET /api/v1/control/tasks` - List tasks
- `GET /api/v1/control/tasks/{id}` - Get task details

**Key Files:**

- Create `file:app/api/v1/endpoints/control/agents.py` - New router
- Create `file:app/api/v1/endpoints/control/tasks.py` - New router
- `file:app/core/services/agent_service.py` - Existing service layer
- `file:app/core/services/task_service.py` - Existing service layer

**Fleet Summary Response:**

```python
{
    "total_agents": 15,
    "active_agents": 12,
    "idle_agents": 3,
    "offline_agents": 0,
    "total_capacity": {"cpu_cores": 192, "gpu_count": 24, "memory_gb": 768},
    "current_utilization": {"active_tasks": 45, "utilization_percent": 75.0},
}
```

**Task List Response:**

```python
{
    "items": [
        {
            "id": 789,
            "campaign_id": 123,
            "attack_id": 456,
            "agent_id": 12,
            "state": "running",
            "progress_percent": 34.5,
            "started_at": "2024-01-15T10:00:00Z",
            "estimated_completion": "2024-01-15T11:30:00Z",
        }
    ],
    "total": 156,
    "limit": 20,
    "offset": 0,
}
```

## Acceptance Criteria

- [ ] Users can view agent fleet summary (total, active/idle, capabilities)
- [ ] Users can list agents with filtering (project, status, capabilities)
- [ ] Users can view agent details (hardware, performance, error logs)
- [ ] Users can list tasks with filtering (campaign, agent, status)
- [ ] Users can view task details with execution logs
- [ ] All operations respect project scoping
- [ ] List endpoints use offset-based pagination
- [ ] All errors follow RFC9457 format

## Testing Strategy

**Backend Tests (Tier 1):**

- Test agent fleet summary calculation
- Test agent listing with filtering
- Test agent detail retrieval
- Test task listing with filtering
- Test task detail retrieval
- Test project scoping

**Test Command:** `just test-backend`

## Dependencies

None - can work in parallel with other monitoring tickets.

## Related Tickets

- Complements `ticket:84e8066f-28f2-4489-aeb6-0aeceb19dcde/T11` (Campaign Status & Metrics)
