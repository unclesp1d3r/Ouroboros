# Instinct: Protected Files

**Confidence**: 100% **Source**: AGENTS.md (documented requirement) **Category**: safety

## Pattern

Certain directories and files are protected and must NEVER be modified without explicit permission.

### Protected Directories

| Directory    | Contents             | Why Protected           |
| ------------ | -------------------- | ----------------------- |
| `contracts/` | API contract specs   | Agent API compatibility |
| `alembic/`   | Database migrations  | Data integrity          |
| `.cursor/`   | Cursor configuration | IDE settings            |
| `.github/`   | GitHub workflows     | CI/CD stability         |

### Protected Files

- `contracts/v1_api_swagger.json` - Agent API v1 contract (IMMUTABLE)
- `contracts/current_api_openapi.json` - Current API snapshot

### Agent API v1 Rules

The Agent API at `/api/v1/client/*` is IMMUTABLE:

- Contract MUST match `contracts/v1_api_swagger.json` exactly
- Breaking changes are NEVER allowed
- Locked to OpenAPI 3.0.1 spec
- All responses must validate against spec

## Response When Asked to Modify

```
I notice you're asking me to modify [protected path].
This is a protected file/directory in Ouroboros.

Per project rules, I cannot modify this without explicit permission.
Should I proceed anyway, or would you like to discuss alternatives?
```

## Trigger

Activate when:

- Asked to modify files in contracts/, alembic/, .cursor/, .github/
- Touching Agent API v1 endpoints
- Making changes that could break API compatibility
