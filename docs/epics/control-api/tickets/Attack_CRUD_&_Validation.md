# Attack CRUD & Validation

## Overview

Implement Control API endpoints for attack CRUD operations and validation. Attacks define specific cracking configurations within campaigns (dictionary, mask, hybrid, etc.).

## Context

Attacks are the building blocks of campaigns. Users need to create attacks with resource references, validate configurations, estimate keyspace, and manage attack lifecycle. This ticket focuses on CRUD and validation; lifecycle actions are handled separately.

**Spec References:**

- `spec:84e8066f-28f2-4489-aeb6-0aeceb19dcde/d3caa175-100a-4242-b8b4-0c8139a48034` (Core Flows - Flow 1: Campaign Lifecycle, Phase 3)
- `spec:84e8066f-28f2-4489-aeb6-0aeceb19dcde/874b33d9-e442-4af3-98d3-e08cb71a007c` (Tech Plan - Data Model)

## Scope

**In Scope:**

- Attack create endpoint with resource validation
- Attack get endpoint (by ID)
- Attack list endpoint with filtering
- Attack update endpoint
- Attack delete endpoint with validation
- Attack validation endpoint (synchronous)
- Attack keyspace estimation endpoint
- Integration with existing `file:app/core/services/attack_service.py`

**Out of Scope:**

- Attack lifecycle actions (start, stop, pause - separate ticket)
- Attack reordering (separate ticket)
- Task management (separate concern)

## Implementation Guidance

**Endpoints:**

- `POST /api/v1/control/attacks` - Create attack
- `GET /api/v1/control/attacks` - List attacks
- `GET /api/v1/control/attacks/{id}` - Get attack details
- `PATCH /api/v1/control/attacks/{id}` - Update attack
- `DELETE /api/v1/control/attacks/{id}` - Delete attack
- `POST /api/v1/control/attacks/validate` - Validate attack config
- `POST /api/v1/control/attacks/estimate` - Estimate keyspace

**Key Files:**

- Create `file:app/api/v1/endpoints/control/attacks.py` - New router
- `file:app/core/services/attack_service.py` - Existing service layer
- `file:app/core/services/attack_complexity_service.py` - Keyspace estimation
- `file:app/models/attack.py` - Attack model

**Create Request:**

```python
{
    "campaign_id": 123,
    "name": "Dictionary Attack",
    "attack_mode": 0,  # Straight dictionary
    "wordlist_id": 456,
    "rule_list_id": 789,  # Optional
    "priority": 1,
}
```

**Validation Response:**

```python
{
    "valid": true,
    "warnings": [],
    "estimated_keyspace": 14344391,
    "estimated_time_seconds": 3600,
    "resource_availability": {
        "wordlist_456": "available",
        "rule_list_789": "available",
    },
}
```

## Acceptance Criteria

- [ ] Users can create attacks with resource references
- [ ] Attack creation validates resource availability
- [ ] Users can validate attack configurations before creation (synchronous)
- [ ] Users can estimate attack keyspace and time-to-completion
- [ ] Users can list attacks with filtering (campaign, type, status)
- [ ] Users can view attack details (config, resources, progress)
- [ ] Users can update attack configurations (when not running)
- [ ] Users can delete attacks (validation prevents deletion if running)
- [ ] All operations respect project scoping
- [ ] All errors follow RFC9457 format

## Testing Strategy

**Backend Tests (Tier 1):**

- Test attack creation with valid and invalid resource references
- Test attack validation (various configurations)
- Test keyspace estimation (mock complexity service)
- Test list endpoint with filtering
- Test update and delete operations
- Test delete validation (prevent deletion of running attacks)

**Test Command:** `just test-backend`

## Dependencies

- `ticket:84e8066f-28f2-4489-aeb6-0aeceb19dcde/T1` (RFC9457 Middleware) for error handling
- `ticket:84e8066f-28f2-4489-aeb6-0aeceb19dcde/T5` (Resource File CRUD) for resource references

## Related Tickets

- Required by `ticket:84e8066f-28f2-4489-aeb6-0aeceb19dcde/T10` (Attack Lifecycle & Reordering)
- Required by `ticket:84e8066f-28f2-4489-aeb6-0aeceb19dcde/T13` (Template Import/Export)
