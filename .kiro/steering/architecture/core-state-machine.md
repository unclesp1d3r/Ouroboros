---
inclusion: fileMatch
fileMatchPattern:
  - app/**/*.py
---

## State Machine Philosophy

Ouroboros uses finite state machines (FSMs) to manage the lifecycle of distributed cracking operations.

Each entity has well-defined transitions:

### Agent

- `registered` → `active` → `disconnected` → `reconnecting` → `retired`

### Session

- `initialized` → `primed` → `executing` → `completed` → `archived`

### Task

- `pending` → `dispatched` → `running` → `complete` → `validated`

### Guidelines for Cursor

- NEVER create new states not in this spec without justification.
- Prefer enums + transitions over booleans or status strings.
- Use clearly named service methods for transitions (e.g., `advance_session()`, `expire_task()`).
- Tests must validate illegal transitions are blocked.

### Additional Guidelines for Cursor

- All state transitions must be validated via explicit service methods.
- DO NOT allow direct writes to `.state` or `.status` outside of the service layer.
