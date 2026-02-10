# Campaign CRUD & Validation

## Overview

Implement Control API endpoints for campaign CRUD operations and pre-flight validation. Campaigns coordinate password cracking attempts against hash lists.

## Context

Campaigns are the primary workflow entity in the Control API. Users need to create campaigns, configure them, validate before launch, and manage their lifecycle. This ticket focuses on CRUD and validation; lifecycle actions are handled separately.

**Spec References:**

- `spec:84e8066f-28f2-4489-aeb6-0aeceb19dcde/d3caa175-100a-4242-b8b4-0c8139a48034` (Core Flows - Flow 1: Campaign Lifecycle, Steps 2-5)
- `spec:84e8066f-28f2-4489-aeb6-0aeceb19dcde/874b33d9-e442-4af3-98d3-e08cb71a007c` (Tech Plan - Data Model)

## Scope

**In Scope:**

- Campaign create endpoint (with optional inline attacks)
- Campaign get endpoint (by ID)
- Campaign update endpoint (metadata)
- Campaign delete endpoint with validation
- Pre-flight validation endpoint
- Integration with existing `file:app/core/services/campaign_service.py`
- Extend existing `file:app/api/v1/endpoints/control/campaigns.py` (currently only has list)

**Out of Scope:**

- Campaign lifecycle actions (start, stop, pause - separate ticket)
- Campaign monitoring (separate ticket)
- Batch operations (separate ticket)

## Implementation Guidance

**Endpoints:**

- `POST /api/v1/control/campaigns` - Create campaign
- `GET /api/v1/control/campaigns/{id}` - Get campaign details
- `PATCH /api/v1/control/campaigns/{id}` - Update campaign
- `DELETE /api/v1/control/campaigns/{id}` - Delete campaign
- `POST /api/v1/control/campaigns/{id}/validate` - Pre-flight validation

**Key Files:**

- `file:app/api/v1/endpoints/control/campaigns.py` - Extend existing router
- `file:app/core/services/campaign_service.py` - Existing service layer
- `file:app/models/campaign.py` - Campaign model
- `file:app/schemas/campaign.py` - Request/response schemas

**Create Request (with inline attacks):**

```python
{
    "name": "Corporate Password Audit",
    "hash_list_id": 123,
    "project_id": 1,
    "attacks": [  # Optional inline attacks
        {"name": "Dictionary Attack", "attack_mode": 0, "wordlist_id": 456}
    ],
}
```

**Validation Response:**

```python
{
    "valid": false,
    "errors": [
        {
            "type": "missing_resource",
            "detail": "Wordlist 456 not found",
            "resource_id": 456,
        }
    ],
    "warnings": [
        {"type": "no_agents", "detail": "No active agents available for project 1"}
    ],
}
```

## Acceptance Criteria

- [ ] Users can create campaigns referencing hash lists
- [ ] Campaign creation supports inline attack definitions (optional)
- [ ] Campaign creation supports separate attack creation workflow
- [ ] Users can view campaign details (including nested attacks)
- [ ] Users can update campaign metadata (name, description)
- [ ] Users can delete campaigns in draft state
- [ ] Delete validation prevents deletion of running campaigns
- [ ] Pre-flight validation checks hash list, resources, agents availability
- [ ] Validation returns actionable error messages
- [ ] All operations respect project scoping (query parameter)
- [ ] All errors follow RFC9457 format

## Testing Strategy

**Backend Tests (Tier 1):**

- Test campaign creation with and without inline attacks
- Test campaign detail retrieval
- Test campaign updates
- Test delete validation (prevent deletion of running campaigns)
- Test pre-flight validation (various error scenarios)
- Test project scoping

**Test Command:** `just test-backend`

## Dependencies

- `ticket:84e8066f-28f2-4489-aeb6-0aeceb19dcde/T1` (RFC9457 Middleware) for error handling
- `ticket:84e8066f-28f2-4489-aeb6-0aeceb19dcde/T4` (Hash List CRUD) for hash list references

## Related Tickets

- Required by `ticket:84e8066f-28f2-4489-aeb6-0aeceb19dcde/T8` (Campaign Lifecycle Actions)
- Required by `ticket:84e8066f-28f2-4489-aeb6-0aeceb19dcde/T11` (Campaign Status & Metrics)
