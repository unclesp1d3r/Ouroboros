---
inclusion: always
---

## Error Philosophy

- Prefer raising custom exceptions over returning raw dicts or booleans.
- Define custom exception types in `app/exceptions.py`.

## Cursor Instructions

- Use `fastapi.HTTPException` for API-specific errors.
- Wrap service-level logic in `try/except` only where needed.
- Avoid catching `Exception` unless absolutely required.

## Control API Error Handling (RFC9457)

- All Control API endpoints (`/api/v1/control/`) must implement error responses in compliance with [RFC9457](mdc:https:/datatracker.ietf.org/doc/html/rfc9457) (Problem Details for HTTP APIs).
- Errors must be returned as `application/problem+json` with the required fields: `type`, `title`, `status`, `detail`, `instance`, and any relevant extensions.
- See RFC9457 for field definitions and usage examples.

## Additional FastAPI Error Handling Best Practices

- Use FastAPI's `HTTPException` for all API-specific errors. Always provide a status code and a clear, actionable `detail` message. Favor FastAPI idiomatic conventions over custom implementations, except in Agent API v1.
- Define and raise custom exception classes for domain-specific errors in `app/core/exceptions.py`. Use these in service and business logic layers.
- Register global exception handlers using `@app.exception_handler` for custom exceptions and common error types (e.g., `ValidationError`, `IntegrityError`).
- Always return errors in a consistent JSON structure. For all APIs except Agent API v1, use a top-level `detail` field (FastAPI default). For Agent API v1, match the legacy schema (e.g., `{ "error": "..." }`).
- Log all exceptions with `loguru`, including stack traces for 5xx errors. Do not leak internal error details to clients—log them server-side only.
- For validation errors, rely on FastAPI's automatic 422 responses. Do not override unless required for compatibility.
- Use RFC9457 (Problem Details for HTTP APIs) for all Control API (`/api/v1/control/`) error responses. Return `application/problem+json` with required fields: `type`, `title`, `status`, `detail`, `instance`, and any relevant extensions.
- For all APIs except Agent API v1, prefer raising exceptions over returning error dicts or booleans. For Agent API v1, follow the legacy schema and field names exactly as defined in `contracts/v1_api_swagger.json`.
- Never use catch-all `except:` blocks. Always specify the exception type.
- Do not expose stack traces, database errors, or sensitive information in any client-facing error response.
- For 401/403 errors, always return a generic message (e.g., "Not authorized"), never the reason for failure.
- For 404 errors, return a clear, non-leaking message (e.g., "Record not found").
- For 5xx errors, return a generic message (e.g., "Internal server error"). Log the full traceback with `loguru`.
- For Agent API v1, all error responses must match the legacy schema and field names exactly as defined in `contracts/v1_api_swagger.json`. Exempt all other error handling rules that would break compatibility.

## Examples

```python
raise HTTPException(status_code=404, detail="Agent not found")
```
