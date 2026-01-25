## 🐘 New Test Architecture (2025 Psycopg/Testcontainers Migration)

- All tests now expect Docker to be available and running on the host system.
- PostgreSQL is provided for tests by [`testcontainers.postgres.PostgresContainer`](mdc:https:/testcontainers-python.readthedocs.io/en/latest/modules/postgres.html).
- Database schema is bootstrapped for each test run using Alembic migrations (no hand-written SQL schemas).
- The preferred SQLAlchemy dialect is `postgresql+psycopg` (async driver).
- We have fully removed `asyncpg` and `psycopg2-binary` and they must not be used or referenced.
- Do not use SQLite or in-memory DBs for integration tests unless explicitly required.
- All test DB operations must use async SQLAlchemy sessions/engines compatible with `psycopg` v3.
- All test containers must be managed using `testcontainers-python` and properly cleaned up after tests.

### Testcontainers & Psycopg v3 Best Practices

- Use `testcontainers.postgres.PostgresContainer` to spin up a real PostgreSQL instance for each test session or module.
- Apply Alembic migrations to the test database after container startup and before running tests.
- Use async SQLAlchemy engines and sessions with the `postgresql+psycopg` driver for all DB operations.
- Provide a fixture (e.g., `async_session`) that yields an async SQLAlchemy session bound to the test DB.
- Ensure all test data is created and persisted using async session methods.
- Clean up containers and sessions after tests to avoid resource leaks.

## Principles

- Use `pytest` only, no unittest or nose.
- Prefer fixtures over mocks when integrating components.
- All test DB operations must use the `__async_session__` fixture to ensure compatibility with SQLAlchemy 2.0 async ORM.
- All new service logic must have corresponding tests in `tests/services/`.
- Avoid integration tests in unit test directories.

## Cursor Guidance

- Use descriptive function names (`test_assign_agent_to_session_succeeds()`).

- Group related tests into modules that mirror `app/` structure.

- Use `async def` with `pytest-asyncio`. Decorators are not needed unless switching to non-default modes.

- Only import `from app.services.X` or `from app.models.X` — don't use relative imports.

- Minimum required test coverage: **80%**

- Use `pytest --cov=app --cov-report=term-missing` in all coverage reports

- Report coverage deltas in CI (or log locally if airgapped)

- [x] Use `polyfactory` for generating test data in service, model, and route tests. See [Polyfactory Documentation](mdc:https:/polyfactory.litestar.dev/latest)

  - Use `polyfactory.create_async()` only. Do not use `.build()`, `SubFactory`, or `sync` methods. All test data must be persisted using an active async SQLAlchemy session.
  - Define all factories in `tests/factories/`.
  - Reuse shared factories across test files.
  - Avoid manually constructing ORM or Pydantic objects in tests unless necessary.
  - Keep factory defaults minimal — override fields in tests as needed.

- [x] Use `testcontainers-python` to run tests against isolated PostgreSQL instances.

  - Do not use SQLite or in-memory DBs unless explicitly required.
  - Define shared test schemas and data fixtures in `conftest.py`.
  - Use `PostgresContainer` to provide a real database for integration and service tests.
  - Apply Alembic migrations to the containerized DB before running tests.

- [x] Use `httpx.AsyncClient` for testing FastAPI endpoints.

  - Instantiate as: `httpx.AsyncClient(app=app, base_url="http://test")`
  - Do not use Starlette's test client or custom wrappers.
  - Place route integration tests under `tests/api/` grouped by functional area.

---

## 🧬 Pydantic v2 Compatibility

- All Pydantic schemas must use **v2 idioms**:
  - `model_dump()` replaces `.dict()`
  - `model_validate()` replaces `.parse_obj()`
- Avoid using deprecated v1-style config like `orm_mode = True` — instead, use the new `ConfigDict` syntax:

```python
class MySchema(BaseModel):
    ...
    model_config = ConfigDict(from_attributes=True)
```

- For tests:
  - Validate input using `model_validate()` to simulate deserialization
  - Validate output using `model_dump()` with `mode="json"` or `mode="python"` as needed
  - Ensure all schemas round-trip without loss (input → model → output)

## Note: If you're asserting schema output in tests, always use `model_dump(mode="json")` for consistency with API responses

## Test Directory Layout

- Unit tests go under `tests/`, mirroring the `app/` structure.
  - e.g., `tests/services/`, `tests/models/`, `tests/core/`
- Integration tests go under `tests/integration/`
  - Group by API type and then by feature
  - e.g., `tests/integration/web/test_web_resources.py`, `tests/integration/agent/test_agent_general_endpoints.py`

**Do not mix unit and integration tests.**

---

## Coverage Expectations

- All HTTP endpoints must have corresponding integration tests using `httpx.AsyncClient`.
- All business logic — especially services, validators, and helpers — must be covered with unit tests.
- Include tests for:
  - Non-happy paths (e.g., validation failures, auth failures)
  - State transitions (e.g., cracking lifecycle)
  - Expected side effects (e.g., DB writes, notifications)
- Tests should validate real-world workflows where possible, not just inputs/outputs.

Avoid over-mocking. Prioritize realistic, layered testing grounded in the real stack.

---

## Advanced Coverage Considerations

- 🌀 **Asynchronous Side Effects**: If a route or service spawns background tasks (e.g., via `asyncio.create_task` or Celery), write tests to confirm those tasks are queued, invoked, or cause expected state changes.

- ⚔️ **Concurrency & Race Conditions**: Simulate concurrent execution of relevant endpoints (e.g., task acquisition, job tracking) using `pytest-asyncio` with `asyncio.gather()` or `trio`. Verify consistent outcomes.

- **Schema Drift & API Contracts**: Where endpoints return structured responses (e.g., JSON), add explicit schema validation using Pydantic models or response matchers to catch unintentional output changes.

- **RBAC & Permission Boundaries**: For protected routes or admin-only actions, include both authorized and unauthorized test cases. Validate HTTP 403 behavior and prevent privilege escalation.

- 🔁 **Startup/Shutdown Events**: If your application registers services, event handlers, or startup hooks, write integration tests that validate those hooks fire and function as expected.

- **Migration Coverage**: Include at least one test that validates all Alembic migrations apply cleanly (alembic upgrade head) in CI against a fresh DB.

---

## Linter & Static Analysis Guidelines (for /tests)

You should attempt to satisfy all linter and static analysis rules in the `/tests` directory. However:

- Do **not** waste time chasing every false-positive caused by test-specific code structures (e.g., dynamically generated test IDs, parametrization, context-dependent mocks).
- If a linter rule fails for a **legitimate test use case**:
  - [x] First, try to restructure the code to avoid the warning.
  - [x] If that's not possible, **ask permission** before adding a `# noqa` or updating `pyproject.toml` to silence the warning globally or selectively.
  - [FAIL] Never disable test directory linting wholesale.

Linter errors in tests should be treated as **soft failures** unless they indicate real issues (e.g., unimported fixtures, unreachable code, broken decorators). Prioritize clarity and functionality over silence.

---

## Unit Testing Guidelines

- All algorithmic logic and helper services must be covered by unit tests in `tests/unit/`
- Factories must use Polyfactory and support `create_async()`
- Avoid mocking the database unless absolutely necessary
- Do not use `print()` or `pdb` in committed tests
- Disable logging assertions unless specifically testing logging behavior

## Integration Testing Guidelines

- API endpoints must be covered by integration tests in `tests/integration/`
- Use `httpx.AsyncClient` and `testcontainers-python` (PostgresContainer)
- Validate endpoint contracts for `/api/v1/client/*` against `contracts/v1_api_swagger.json`
- Use `pytest` and `httpx.AsyncClient` to test all `/api/v1/web/` endpoints.
- Use actual project/user association logic in test setup
- Do not skip authentication or RBAC in integration tests

## CI Enforcement

- `just ci-check` must run all tests, linting, and formatting checks
- Integration tests should use a throwaway database with schema bootstrapped from Alembic
- Cache invalidation must be validated where applicable

# Test Guidelines - SvelteKit + JSON API

## Backend

- Use `pytest` and `httpx.AsyncClient` to test all `/api/v1/web/` endpoints.
- Validate JSON schema, status codes, permission scopes.
- No HTML responses should be returned.

## Frontend

- Unit tests: use **Vitest** for all Svelte components.
- E2E tests: use **Playwright** for form flows, nav, and SSE updates.
- Coverage threshold: 80%+ for all critical user flows.

CI runs both backend and frontend test suites before packaging.
