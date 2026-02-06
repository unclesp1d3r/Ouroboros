# Attack Lifecycle & Reordering

## Overview

Implement Control API endpoints for attack lifecycle operations (start, stop, pause) and attack reordering within campaigns. Attack order determines execution priority.

## Context

Attacks within a campaign execute in priority order. Users need to control individual attack execution and reorder attacks to optimize campaign strategy. All state transitions must be validated.

**Spec References:**

- `spec:84e8066f-28f2-4489-aeb6-0aeceb19dcde/d3caa175-100a-4242-b8b4-0c8139a48034` (Core Flows - Flow 1: Campaign Lifecycle, Phase 3)
- `spec:84e8066f-28f2-4489-aeb6-0aeceb19dcde/874b33d9-e442-4af3-98d3-e08cb71a007c` (Tech Plan - State Machines)

## Scope

**In Scope:**

- Attack start/stop/pause endpoints
- Attack reordering within campaigns
- Attack performance metrics endpoint
- Integration with state machine from T2
- Integration with existing `file:app/core/services/attack_service.py`

**Out of Scope:**

- Attack CRUD (handled in T9)
- Task management (separate concern)
- Campaign-level lifecycle (handled in T8)

## Implementation Guidance

**Endpoints:**

- `POST /api/v1/control/attacks/{id}/start` - Start attack
- `POST /api/v1/control/attacks/{id}/stop` - Stop attack
- `POST /api/v1/control/attacks/{id}/pause` - Pause attack
- `POST /api/v1/control/campaigns/{campaign_id}/attacks/reorder` - Reorder attacks
- `GET /api/v1/control/attacks/{id}/metrics` - Get performance metrics

**Key Files:**

- `file:app/api/v1/endpoints/control/attacks.py` - Add lifecycle endpoints
- `file:app/core/services/attack_service.py` - Existing lifecycle services
- `file:app/core/state_machines.py` - State machine validation (from T2)
- `file:app/models/attack.py` - Attack model

**Reorder Request:**

```python
{
    "attack_order": [
        {"attack_id": 101, "priority": 1},
        {"attack_id": 102, "priority": 2},
        {"attack_id": 103, "priority": 3},
    ]
}
```

**Metrics Response:**

```python
{
    "attack_id": 101,
    "hash_rate": 1500000,  # hashes/second
    "progress_percent": 45.2,
    "estimated_completion": "2024-01-15T14:30:00Z",
    "cracks_found": 123,
    "tasks_completed": 5,
    "tasks_active": 2,
}
```

## Acceptance Criteria

- [ ] Users can start individual attacks
- [ ] Users can stop individual attacks
- [ ] Users can pause individual attacks
- [ ] All state transitions are validated by `AttackStateMachine`
- [ ] Invalid transitions return RFC9457 errors
- [ ] Users can reorder attacks within a campaign
- [ ] Reordering updates attack priority correctly
- [ ] Users can view attack performance metrics
- [ ] Metrics include hash rate, progress, ETA, crack count
- [ ] All operations respect project scoping

## Testing Strategy

**Backend Tests (Tier 1):**

- Test attack lifecycle actions with valid state transitions
- Test invalid state transitions (expect errors)
- Test attack reordering (various scenarios)
- Test performance metrics retrieval
- Test project scoping

**Test Command:** `just test-backend`

## Dependencies

- `ticket:84e8066f-28f2-4489-aeb6-0aeceb19dcde/T2` (State Machine Classes) - Required for validation
- `ticket:84e8066f-28f2-4489-aeb6-0aeceb19dcde/T9` (Attack CRUD) - Required for attack data

## Related Tickets

- Required by `ticket:84e8066f-28f2-4489-aeb6-0aeceb19dcde/T14` (Results & Batch Operations)
