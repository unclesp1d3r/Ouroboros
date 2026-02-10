# Results & Batch Operations

## Overview

Implement Control API endpoints for campaign results retrieval/export and batch operations. Results are available in multiple formats (JSON, CSV, hashcat potfile). Batch operations enable efficient multi-campaign control.

## Context

Users need to retrieve cracked hashes after campaign completion and perform bulk operations on multiple campaigns. Results are canonical at the hash list level but campaign-centric views provide convenience. Batch operations are single-project scoped for safety.

**Spec References:**

- `spec:84e8066f-28f2-4489-aeb6-0aeceb19dcde/d3caa175-100a-4242-b8b4-0c8139a48034` (Core Flows - Flow 5: Batch Operations, Flow 1 Exit)
- `spec:84e8066f-28f2-4489-aeb6-0aeceb19dcde/874b33d9-e442-4af3-98d3-e08cb71a007c` (Tech Plan - Results, Batch Operations)

## Scope

**In Scope:**

- Campaign results retrieval endpoint (summary)
- Results export endpoint (JSON, CSV, hashcat potfile)
- Batch campaign operations (start, stop, status) - single-project scoped
- Batch operation modes (atomic vs best-effort)
- Per-item success/failure reporting

**Out of Scope:**

- Cross-project batch operations
- Real-time result streaming
- Result filtering/search (use hash list endpoints)

## Implementation Guidance

**Endpoints:**

- `GET /api/v1/control/campaigns/{id}/results` - Get campaign results summary
- `GET /api/v1/control/campaigns/{id}/results/export` - Export results (format query param)
- `POST /api/v1/control/projects/{project_id}/campaigns/batch-start` - Batch start
- `POST /api/v1/control/projects/{project_id}/campaigns/batch-stop` - Batch stop
- `GET /api/v1/control/projects/{project_id}/campaigns/batch-status` - Batch status

**Key Files:**

- `file:app/api/v1/endpoints/control/campaigns.py` - Add results endpoints
- Create `file:app/api/v1/endpoints/control/batch.py` - New router for batch ops
- `file:app/core/services/campaign_service.py` - Existing service layer
- `file:app/models/crack_result.py` - Crack result model

**Results Export Formats:**

```python
# JSON
{
    "campaign_id": 123,
    "total_hashes": 5000,
    "cracked_hashes": 1234,
    "crack_rate": 24.68,
    "results": [
        {"hash": "5f4dcc3b5aa765d61d8327deb882cf99", "plaintext": "password"}
    ]
}

# CSV
hash,plaintext
5f4dcc3b5aa765d61d8327deb882cf99,password

# Hashcat potfile
5f4dcc3b5aa765d61d8327deb882cf99:password
```

**Batch Operation Request:**

```python
{
    "campaign_ids": [123, 124, 125],
    "mode": "best_effort",  # or "atomic"
}
```

**Batch Operation Response:**

```python
{
    "results": [
        {"id": 123, "success": true},
        {
            "id": 124,
            "success": false,
            "error": {
                "type": "invalid_state",
                "detail": "Campaign 124 is already running",
            },
        },
        {"id": 125, "success": true},
    ],
    "summary": {"total": 3, "succeeded": 2, "failed": 1},
}
```

## Acceptance Criteria

- [ ] Users can retrieve campaign results summary (total, cracked, crack rate)
- [ ] Results are canonical at hash list level (via hash_list_id reference)
- [ ] Users can export results in JSON, CSV, and hashcat potfile formats
- [ ] Export format is specified via query parameter
- [ ] Users can perform batch start on multiple campaigns (single project)
- [ ] Users can perform batch stop on multiple campaigns (single project)
- [ ] Users can perform batch status check on multiple campaigns
- [ ] Batch operations support atomic and best-effort modes (default: best-effort)
- [ ] Batch responses include per-item success/failure details
- [ ] Batch endpoints are path-scoped by project (`/projects/{id}/campaigns/batch-*`)
- [ ] All errors follow RFC9457 format

## Testing Strategy

**Backend Tests (Tier 1):**

- Test results retrieval and export (all formats)
- Test batch operations (start, stop, status)
- Test atomic vs best-effort modes
- Test per-item error reporting
- Test project scoping for batch operations

**Test Command:** `just test-backend`

## Dependencies

- `ticket:84e8066f-28f2-4489-aeb6-0aeceb19dcde/T8` (Campaign Lifecycle) for lifecycle operations
- `ticket:84e8066f-28f2-4489-aeb6-0aeceb19dcde/T10` (Attack Lifecycle) for attack operations

## Related Tickets

- Complements `ticket:84e8066f-28f2-4489-aeb6-0aeceb19dcde/T13` (Template Import/Export)
