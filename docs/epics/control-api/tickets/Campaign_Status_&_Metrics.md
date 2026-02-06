# Campaign Status & Metrics

## Overview

Implement Control API endpoints for campaign status monitoring and metrics. Supports both individual campaign drill-down and bulk dashboard views optimized for TUI rendering.

## Context

Users need to monitor campaign progress through efficient polling. Individual status provides detailed drill-down, while bulk status enables dashboard views. Caching reduces database load for high-frequency polling.

**Spec References:**

- `spec:84e8066f-28f2-4489-aeb6-0aeceb19dcde/d3caa175-100a-4242-b8b4-0c8139a48034` (Core Flows - Flow 3: Real-Time Monitoring, Steps 1-3)
- `spec:84e8066f-28f2-4489-aeb6-0aeceb19dcde/874b33d9-e442-4af3-98d3-e08cb71a007c` (Tech Plan - Monitoring & Dashboard)

## Scope

**In Scope:**

- Individual campaign status endpoint (detailed progress)
- Bulk campaign status endpoint (dashboard view)
- Campaign metrics endpoint (hash rate, crack rate, trends)
- Caching implementation (5-10s TTL, project-scoped)
- Rich-but-shallow response format (campaign + 1-level attack rollup)
- Integration with existing `file:app/core/services/campaign_service.py`

**Out of Scope:**

- Real-time streaming (using polling only)
- Historical analytics (current state only)
- Agent-level monitoring (separate ticket)

## Implementation Guidance

**Endpoints:**

- `GET /api/v1/control/campaigns/{id}/status` - Individual campaign status
- `GET /api/v1/control/campaigns/status` - Bulk campaign status (dashboard)
- `GET /api/v1/control/campaigns/{id}/metrics` - Campaign metrics

**Key Files:**

- `file:app/api/v1/endpoints/control/campaigns.py` - Add monitoring endpoints
- `file:app/core/services/campaign_service.py` - Existing service layer
- `file:app/core/services/dashboard_service.py` - Dashboard aggregation
- Use `cashews` for caching (already imported in system.py)

**Bulk Status Response (Dashboard):**

```python
{
    "items": [
        {
            "id": 123,
            "name": "Corporate Audit",
            "state": "running",
            "progress_percent": 45.2,
            "eta_seconds": 3600,
            "crack_count": 1234,
            "active_tasks": 5,
            "current_attack": {
                "id": 456,
                "name": "Dictionary Attack",
                "state": "running",
                "progress_percent": 67.8,
            },
            "next_attack": {"id": 457, "name": "Mask Attack", "state": "pending"},
        }
    ],
    "total": 42,
    "limit": 20,
    "offset": 0,
}
```

**Caching Pattern:**

```python
from cashews import cache

@cache(ttl="10s", key="campaign_status:{project_id}:{filters}")
async def get_bulk_campaign_status(...):
    # Expensive query
    return results
```

## Acceptance Criteria

- [ ] Users can poll individual campaign status (progress, ETA, crack count)
- [ ] Individual status includes detailed attack breakdown
- [ ] Users can poll bulk campaign status with filtering and pagination
- [ ] Bulk status includes campaign rollup + current/next attack summary
- [ ] Bulk status is cached with 5-10s TTL, shared by project
- [ ] Cache key includes project_id and normalized filters
- [ ] Responses are optimized for TUI rendering (rich but not deeply nested)
- [ ] Campaign metrics include hash rate, crack rate, success percentage
- [ ] All operations respect project scoping
- [ ] All errors follow RFC9457 format

## Testing Strategy

**Backend Tests (Tier 1):**

- Test individual campaign status retrieval
- Test bulk campaign status with filtering
- Test caching behavior (verify cache hits/misses)
- Test metrics calculation
- Test project scoping

**Test Command:** `just test-backend`

## Dependencies

- `ticket:84e8066f-28f2-4489-aeb6-0aeceb19dcde/T7` (Campaign CRUD) for campaign data

## Related Tickets

- Complements `ticket:84e8066f-28f2-4489-aeb6-0aeceb19dcde/T12` (Agent & Task Monitoring)
