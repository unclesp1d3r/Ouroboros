# Template Import/Export

## Overview

Implement Control API endpoints for campaign template export and import. Templates enable reusable campaign configurations across projects and environments.

## Context

Users need to export successful campaign configurations as templates and import them into other environments. Templates are JSON-formatted with schema versioning for evolution. Partial import is supported when resources are missing.

**Spec References:**

- `spec:84e8066f-28f2-4489-aeb6-0aeceb19dcde/d3caa175-100a-4242-b8b4-0c8139a48034` (Core Flows - Flow 4: Template Reuse)
- `spec:84e8066f-28f2-4489-aeb6-0aeceb19dcde/874b33d9-e442-4af3-98d3-e08cb71a007c` (Tech Plan - Templates)

## Scope

**In Scope:**

- Campaign template export endpoint (JSON with schema version)
- Template validation endpoint (`validate_only=true`)
- Template import endpoint with partial import support
- Template schema versioning
- Integration with existing `file:app/core/services/template_service.py`

**Out of Scope:**

- Template versioning and migration (single schema version for now)
- Template marketplace or sharing
- Attack-only templates (campaign-level only)

## Implementation Guidance

**Endpoints:**

- `GET /api/v1/control/campaigns/{id}/export` - Export campaign as template
- `POST /api/v1/control/templates/validate` - Validate template
- `POST /api/v1/control/templates/import` - Import template

**Key Files:**

- Create `file:app/api/v1/endpoints/control/templates.py` - New router
- `file:app/core/services/template_service.py` - Existing service layer
- `file:app/schemas/shared.py` - CampaignTemplate schema

**Template Format:**

```python
{
    "schema_version": "1.0",
    "campaign": {
        "name": "Corporate Password Audit",
        "description": "Standard audit template",
        "attacks": [
            {
                "name": "Dictionary Attack",
                "attack_mode": 0,
                "wordlist_name": "rockyou.txt",  # Name, not ID
                "rule_list_name": "best64.rule",
            }
        ],
    },
}
```

**Import Response (Partial Import):**

```python
{
    "campaign_id": 789,
    "imported": {
        "campaign": true,
        "attacks": [{"name": "Dictionary Attack", "imported": true, "attack_id": 101}],
    },
    "skipped": {
        "attacks": [
            {
                "name": "Mask Attack",
                "reason": "missing_resource",
                "missing_resources": ["custom_masks.hcmask"],
            }
        ]
    },
}
```

## Acceptance Criteria

- [ ] Users can export campaign as JSON template with schema version
- [ ] Export includes all attacks and resource references (by name, not ID)
- [ ] Users can validate template before import (`validate_only=true`)
- [ ] Validation identifies missing resources and incompatibilities
- [ ] Users can import template with partial import support
- [ ] Import creates campaign and skips attacks with missing resources
- [ ] Import response clearly reports imported vs skipped items with reasons
- [ ] Templates are portable across environments (use resource names, not IDs)
- [ ] All operations respect project scoping
- [ ] All errors follow RFC9457 format

## Testing Strategy

**Backend Tests (Tier 1):**

- Test template export (various campaign configurations)
- Test template validation (valid and invalid templates)
- Test template import (full and partial import scenarios)
- Test missing resource handling
- Test schema version validation

**Test Command:** `just test-backend`

## Dependencies

- `ticket:84e8066f-28f2-4489-aeb6-0aeceb19dcde/T7` (Campaign CRUD) for campaign data
- `ticket:84e8066f-28f2-4489-aeb6-0aeceb19dcde/T9` (Attack CRUD) for attack data

## Related Tickets

- Complements `ticket:84e8066f-28f2-4489-aeb6-0aeceb19dcde/T14` (Results & Batch Operations)
