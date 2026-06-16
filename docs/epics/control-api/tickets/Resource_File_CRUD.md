# Resource File CRUD

## Overview

Implement Control API endpoints for resource file management (list, get, update, delete). Resources include wordlists, rules, and masks used in attacks.

## Context

Resource files are essential for attack configuration. Users need to discover available resources, view details, update metadata, and delete unused resources. This ticket focuses on CRUD operations; upload workflow is handled separately.

**Spec References:**

- `spec:84e8066f-28f2-4489-aeb6-0aeceb19dcde/d3caa175-100a-4242-b8b4-0c8139a48034` (Core Flows - Flow 2: Resource Management, Steps 4-7)
- `spec:84e8066f-28f2-4489-aeb6-0aeceb19dcde/874b33d9-e442-4af3-98d3-e08cb71a007c` (Tech Plan - Data Model)

## Scope

**In Scope:**

- Resource list endpoint with filtering (type, project, search)
- Resource get endpoint with metadata and usage stats
- Resource update endpoint (metadata only)
- Resource delete endpoint with validation
- Resource content preview endpoint (first N lines)
- Integration with existing `file:app/core/services/resource_service.py`

**Out of Scope:**

- Resource upload (handled in presigned upload ticket)
- Resource content editing (metadata only)
- Resource versioning

## Implementation Guidance

**Endpoints:**

- `GET /api/v1/control/resources` - List resources
- `GET /api/v1/control/resources/{id}` - Get resource details
- `GET /api/v1/control/resources/{id}/preview` - Preview content
- `PATCH /api/v1/control/resources/{id}` - Update metadata
- `DELETE /api/v1/control/resources/{id}` - Delete resource

**Key Files:**

- Create `file:app/api/v1/endpoints/control/resources.py` - New router
- `file:app/core/services/resource_service.py` - Existing service layer
- `file:app/core/services/storage_service.py` - For content preview
- `file:app/models/attack_resource_file.py` - Resource model

**Response Format:**

```python
# List response includes rich metadata
{
    "items": [
        {
            "id": 456,
            "name": "rockyou.txt",
            "type": "wordlist",
            "file_size_bytes": 139921507,
            "line_count": 14344391,
            "project_id": 1,
            "is_uploaded": true,
            "usage_count": 5,  # Number of attacks using this resource
            "created_at": "2024-01-10T08:00:00Z",
        }
    ],
    "total": 128,
    "limit": 20,
    "offset": 0,
}
```

## Acceptance Criteria

- [ ] Users can list resources with filtering (type, project, search)
- [ ] List endpoint uses offset-based pagination
- [ ] Users can view resource details including usage statistics
- [ ] Users can preview resource content (first 100 lines)
- [ ] Users can update resource metadata (name, description, tags)
- [ ] Users can delete unused resources
- [ ] Delete validation prevents deletion if resource is used by attacks
- [ ] All operations respect project scoping (query parameter)
- [ ] Pending resources are visible but marked as `is_uploaded=false`
- [ ] All errors follow RFC9457 format

## Testing Strategy

**Backend Tests (Tier 1):**

- Test resource listing with filtering and pagination
- Test resource detail retrieval
- Test content preview (mock MinIO storage)
- Test metadata updates
- Test delete validation (prevent deletion of in-use resources)
- Test project scoping

**Test Command:** `just test-backend`

## Dependencies

None - can work in parallel with other resource layer tickets.

## Related Tickets

- Required by `ticket:84e8066f-28f2-4489-aeb6-0aeceb19dcde/T9` (Attack CRUD & Validation)
