---
inclusion: always
---

## Hands-Off Zones

Cursor must not generate or modify code in the following directories unless explicitly asked:

- `alembic`
- `.cursor/`
- `.github/`

You may **NEVER** modify the following file under any circumstances:

- `contracts/v1_api_swagger.json`

## Rationale

These areas are either user-authored documentation, manually managed config, or external-facing assets.

### Additional Guidelines

- If the user explicitly requests changes to a protected file, confirm the file and reason before making edits.
