---
inclusion: fileMatch
fileMatchPattern:
  - app/models/**/*
  - alembic/*
---

## Guidelines

- All SQLAlchemy models live in `app/models/`
- Fields must include types and constraints explicitly
- New models must be added to Alembic via `alembic revision --autogenerate` and reviewed manually.

## Cursor Rules

- DO NOT edit files under `alembic/versions/` directly.
- Add new models in separate files unless tightly coupled
- Use Alembic `op` methods to modify schema (`add_column`, `create_index`, etc.)
- Add comments describing migration purpose at the top of each revision

### Additional Guidelines

- All status/state fields must be defined using `sqlalchemy.Enum`, not raw strings.
