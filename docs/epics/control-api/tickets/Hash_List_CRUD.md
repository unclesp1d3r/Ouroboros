# Hash List CRUD

## Overview

Implement Control API endpoints for hash list management (create, read, update, delete). Hash lists are the foundation of campaigns, containing the hashes to be cracked.

## Context

Hash lists are central to the Control API workflow. Users need to create hash lists before creating campaigns. The Control API must provide full CRUD operations with validation and project scoping.

**Spec References:**

- `spec:84e8066f-28f2-4489-aeb6-0aeceb19dcde/d3caa175-100a-4242-b8b4-0c8139a48034` (Core Flows - Flow 1: Campaign Lifecycle, Step 1)
- `spec:84e8066f-28f2-4489-aeb6-0aeceb19dcde/874b33d9-e442-4af3-98d3-e08cb71a007c` (Tech Plan - Data Model)

## Scope

**In Scope:**

- Hash list create endpoint with validation
- Hash list get endpoint (by ID)
- Hash list list endpoint with filtering and pagination
- Hash list update endpoint (metadata only)
- Hash list delete endpoint with validation
- Project scoping and access control
- Integration with existing `file:app/core/services/hash_list_service.py`

**Out of Scope:**

- Hash cracking logic (Agent API responsibility)
- Campaign association (handled in campaign tickets)
- Hash type detection (use existing hash guess service)

## Implementation Guidance

**Endpoints:**

- `POST /api/v1/control/hash-lists` - Create hash list
- `GET /api/v1/control/hash-lists` - List hash lists
- `GET /api/v1/control/hash-lists/{id}` - Get hash list details
- `PATCH /api/v1/control/hash-lists/{id}` - Update hash list metadata
- `DELETE /api/v1/control/hash-lists/{id}` - Delete hash list

**Key Files:**

- Create `file:app/api/v1/endpoints/control/hash_lists.py` - New router
- `file:app/core/services/hash_list_service.py` - Existing service layer
- `file:app/models/hash_list.py` - Hash list model
- `file:app/schemas/hash_list.py` - Request/response schemas

**Response Format:**

```python
# List response includes rich metadata
{
    "items": [
        {
            "id": 123,
            "name": "Corporate Hashes",
            "hash_count": 5000,
            "detected_types": ["NTLM", "bcrypt"],
            "validation_status": "valid",
            "project_id": 1,
            "created_at": "2024-01-15T10:30:00Z",
        }
    ],
    "total": 42,
    "limit": 20,
    "offset": 0,
}
```

## Acceptance Criteria

- [ ] Users can create hash lists with hash data and metadata
- [ ] Hash validation detects invalid formats and returns clear errors
- [ ] Users can list hash lists with filtering (project, search, hash type)
- [ ] List endpoint uses offset-based pagination
- [ ] Users can view hash list details (count, types, validation status)
- [ ] Users can update hash list metadata (name, description)
- [ ] Users can delete unused hash lists
- [ ] Delete validation prevents deletion if hash list is used by campaigns
- [ ] All operations respect project scoping (query parameter)
- [ ] All errors follow RFC9457 format

## Testing Strategy

**Backend Tests (Tier 1):**

- Test hash list creation with valid and invalid data
- Test hash validation (various hash formats)
- Test list endpoint with filtering and pagination
- Test update and delete operations
- Test project scoping (users can only access their projects)
- Test delete validation (prevent deletion of in-use hash lists)

**Test Command:** `just test-backend`

## Dependencies

None - can work in parallel with other resource layer tickets.

## Related Tickets

- Required by `ticket:84e8066f-28f2-4489-aeb6-0aeceb19dcde/T7` (Campaign CRUD & Validation)
