---

## inclusion: fileMatch fileMatchPattern: \[app/core/**/\*.py, app/api/**/*.py, app/api/v1/endpoints/\*\*/*.py\]

## Layered Architecture

Keep API endpoints thin. Business logic should be in service classes under `app/services`.

- Every `/api/v1/web/*` route must delegate to a service for:
  - Validation
  - Access control
  - Computation
  - DB writes/reads

Services should return Pydantic models. Endpoints should format them as JSONResponse with status codes.

\[x\] Test services independently from the API layer.

All business logic must live in services. These should:

- Contain reusable methods (e.g., `assign_agent_to_session()`)
- Take Pydantic data models, interact with SQLAlchemy models, and return data models (Pydantic)
- Be invoked by API routes or background jobs
- The methods should aspire to be reusable when possible
- Return strongly typed objects. DO NOT return `dict[str, Any]`

## Guidelines for Cursor

- NEVER place DB logic in FastAPI route handlers.
- Each route should call a `service/*` method with relevant input.
- Service methods should be unit-testable and accept explicit arguments.
- Service methods must return validated Pydantic `*Out` schemas, not raw DB models.
- Handle all task/agent/session mutations here — no side effects in route handlers.
