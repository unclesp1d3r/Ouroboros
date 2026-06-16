---
inclusion: always
---

## Principals

- **NEVER** place DB logic in FastAPI route handlers. See [service-patterns.mdc](mdc:.cursor/rules/code/service-patterns.mdc)
- API endpoints **must** be covered by integration tests. See [test-guidelines.mdc](mdc:.cursor/rules/code/test-guidelines.mdc)

---

## [x] Endpoint Definitions

- All routes **must** use a return type, rather than define a `response_model=...` in the route decorator.
- Every route **must** include a `summary` and `description` argument to support OpenAPI documentation.
- Routes **must** return the appropriate HTTP status codes (`201`, `204`, `400`, `403`, `404`, etc). Use constants from `fastapi.status`, rather than the int constants (i.e. `fastapi.status.HTTP_404_NOT_FOUND` instead of `404`)
- Routes should be grouped by resource in `app/routes/`, e.g., `app/routes/agents.py`, `app/routes/projects.py`.
- The prefix and tags should be defined within the `APIRouter()`, not in `router.include_router`. For example: `router = APIRouter(prefix="/agents", tags=["Agents"])`
- Do not use `tags=[...]` in the route decorator to assign OpenAPI tags and organize docs, this should be used in the `APIRouter`
- No undocumented routes. Any route without `summary`, `description`, and `tags` will fail code review.
- All routes should use request and response models rather than dictionaries, unless absolutely necessary. If unavoidable, include a code comment with a justification.
- Cookies should be accessed via the FastAPI Cookie Parameters in an idiomatic manner

---

## Request/Response Schemas

- All request and response models **must** inherit from `pydantic.BaseModel`.
- Request and response models **must** be defined in `app/schemas/`, not inline in route files.
- Every field in a schema should include `example=...` in the `Field(...)` definition to improve OpenAPI docs.
- Use `Field(..., description=...)` to explain the purpose of non-obvious fields.
- Enum fields must always return `.value` when serialized. Avoid returning raw enum names.

---

# API Documentation Guidelines (Web UI)

All `/api/v1/web/*` endpoints must return JSON — not HTML fragments or templates.

Each endpoint must:

- Define a clear Pydantic response model.
- Include a `meta` section (pagination, status) if needed.
- Avoid leaking internal DB IDs; use UUIDs or public-safe keys.

Document all routes using FastAPI's OpenAPI schema. Use tags to group them by feature (e.g., Campaigns, Agents).

---

## Authentication & Authorization

- Protected routes **must** include an explicit dependency (e.g., `Depends(current_user)`).
- Authorization logic (e.g., role enforcement) **must** be declared using dependencies or decorators.
- Public vs. protected routes should be clearly documented.
- Return `403 Forbidden` for unauthorized users, not just `401 Unauthorized`.

---

## 🔁 API Versioning and Deprecation

- All public-facing routes **must** be prefixed with a version (e.g., `/api/v1/...`, `/api/v2/...`).
- Deprecated routes must:
  - Be annotated with a `deprecated=True` OpenAPI flag.
  - Include a docstring or OpenAPI description stating the replacement endpoint (if any).

---

## Validation and Payload Rules

- Use built-in Pydantic field types (`constr`, `conint`, `EmailStr`, etc.) instead of manual validation inside route functions.
- Required fields must be enforced with `Field(..., ...)`, not `Optional`.
- All request payloads must:
  - Match the defined Pydantic schema exactly.
  - Include ISO8601-formatted datetimes (`.isoformat()`).
  - Use proper enum `.value` strings, not integer keys or labels.
- Do not silently coerce bad data — raise `HTTPException` with status `422` and clear detail.

---

## 💣 Error Handling

- All exceptions raised in routes must use FastAPI's `HTTPException` with an appropriate status code and `detail=...` message.
- Use a consistent error envelope structure (e.g., `{ "detail": "Error message" }`).
- Do not expose internal exception tracebacks or raw database errors to the API consumer.
- Standardize known errors using shared error response models or FastAPI exception handlers (e.g., `EntityNotFoundError`, `UnauthorizedError`).
- See [error-handling.mdc](mdc:.cursor/rules/code/error-handling.mdc) for standards on error handling.

---

## Documentation & Tags

- Routes should be tagged using domain-specific nouns (e.g., `["Agents"]`, `["Tasks"]`, `["Projects"]`).
- Avoid generic tags like `["API"]`, `["General"]`, or tags with inconsistent capitalization.
- Group related endpoints under the same tag for easier OpenAPI navigation.

---

## Testing Requirements

- Every endpoint must have corresponding integration tests.
- Tests must cover:
  - Happy path
  - Invalid input (422)
  - Unauthorized access (401/403)
  - Not found (404)
- All test payloads must:
  - Use valid schema inputs with proper casing and types.
  - Include required fields and reflect the latest API changes.
- Use `status_code` assertions **before** accessing response bodies.
- For new resources, seed factories must support valid creation and relationship wiring.
- See [test-guidelines.mdc](mdc:.cursor/rules/code/test-guidelines.mdc) for standards on testing.

---

## [WARN] Logging (during testing)

- Avoid structured logging or Loguru calls in unit or integration test environments unless explicitly debugging.
- Use `print()` or `pprint()` for debug output in test runs if needed, and remove before commit.

---

## Performance & Misc

- Avoid performing expensive database queries in route-level logic. Prefer delegating to service-layer functions.
- Routes should never have database calls in the router. See [service-patterns.mdc](mdc:.cursor/rules/code/service-patterns.mdc)
- Don't duplicate business logic in multiple routes. Use shared service functions in `app/services/`.
- Avoid circular dependencies between `schemas`, `models`, and `services`.

---

## Summary

All endpoints must be well-structured, documented, and validated with clear input/output contracts. All tests must mirror real-world usage scenarios and ensure both correctness and resilience. Style violations in API design, schema usage, and route structure are treated as blocking issues in code review.
