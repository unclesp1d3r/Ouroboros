# Psycopg Migration Task Plan

## [x] Migration Task Plan (Simplified for Skirmish Execution) - Completed

Follow these three tasks in order. Do not start the next task until all tests pass for the current one. Each task is self-contained and ends in a clear success state: **green tests.**

---

### Task 1: Update `test-guidelines.mdc` for the new test infrastructure

- [x] Context: Ouroboros is migrating from `pytest-postgresql` and `asyncpg` to `testcontainers-python` and `psycopg3`. These changes affect test strategy and tooling expectations. Your first step is to update our project's testing guidance to reflect this shift.

What to do:

- Open `.cursor/rules/code/test-guidelines.mdc`

- At the **top of the file**, insert a new section describing the **new test architecture**:

  - Tests now expect Docker to be available.
  - PostgreSQL is provided by [`testcontainers.postgres.PostgresContainer`](https://testcontainers-python.readthedocs.io/en/latest/modules/postgres.html)
  - Database migrations are applied using Alembic.
  - The preferred SQLAlchemy dialect is `postgresql+psycopg`.
  - We are gradually removing `asyncpg` and `psycopg2-binary`, but they must remain until the test container transition is complete (see note in Task 3).

\[x\] Success Criteria:

- `test-guidelines.mdc` is updated and committed
- The new section appears **above** any outdated notes about `asyncpg` or `pytest-postgresql`
- No code has changed yet
- Run all tests to confirm the test suite still passes (should be a no-op)

---

### 🐘 Task 2: Migrate from `asyncpg` to `psycopg` (Driver Swap Only)

- [x] Context: We are replacing `asyncpg` with `psycopg` as the async PostgreSQL driver. This is a drop-in driver replacement and should not involve containerization yet.

What to do:

- Update all SQLAlchemy engine creation to use `postgresql+psycopg://` instead of `postgresql+asyncpg://`

- Remove `asyncpg` from `pyproject.toml`

- Add:

  ```toml
  psycopg = { version = ">=3.1.18", extras = ["binary", "pool"] }
  ```

- Replace any usage of `asyncpg`-specific features if present (you likely aren't using any)

- Ensure `alembic.ini` and any overrides (e.g., in `env.py`) also use `postgresql+psycopg` URLs.

[WARN] Compatibility Note: Keep `psycopg2-binary` in your dependencies **for now**, because `pytest-postgresql` still depends on it. Do not remove it until Task 3 is complete.

\[x\] Success Criteria:

- All test fixtures (`async_engine`, `db_session`, etc.) run successfully with `psycopg`
- All tests pass with no connection errors
- No test container is used yet — this is purely a driver-level change
- Once tests are [x] green, commit your changes

---

### Task 3: Replace `pytest-postgresql` with `testcontainers[postgresql]`

- [x] Context: We are replacing `pytest-postgresql` with `testcontainers[postgresql]` for test DB provisioning. This enables containerized, isolated Postgres instances for all tests, and is a prerequisite for full async driver support and future DB scaling.

What to do:

- Remove `pytest-postgresql` from `pyproject.toml`

- Add:

  ```toml
  testcontainers = { version = ">=4.1.1", extras = ["postgresql"] }
  ```

- In `conftest.py`, replace:

  - `postgresql_proc` and `postgresql` fixtures
  - `db_url` and `sync_db_url` based on those fixtures

- Instead, define a `pg_container_url` fixture that:

  - Starts a `PostgresContainer`
  - Yields a connection string like `postgresql+psycopg://...`

- Ensure `async_engine` and `db_session` are updated to use this new container URL

- Apply Alembic migrations inside the container before tests run (see existing `env.py` for how)

🖐 Important: Once this step is complete, you may **safely remove `psycopg2-binary`** from `pyproject.toml`. Until then, keep it in place to avoid breaking `pytest-postgresql` or Alembic default behaviors.

\[x\] Success Criteria:

- All tests pass (run `just test` to confirm) using the new containerized Postgres instance
- No references to `pytest-postgresql` or `asyncpg` remain
- Docker must be running and usable for tests to pass
- Once tests are [x] green, commit your changes

---

Do not skip tasks or proceed without passing tests. Each phase is independent and should succeed before the next begins.
