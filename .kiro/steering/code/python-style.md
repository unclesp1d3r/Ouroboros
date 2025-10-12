---
inclusion: fileMatch
fileMatchPattern: '**/*.py'
---

# Python Style Guidelines

## Description

Rules and guidelines for maintaining consistent Python code style across the project.

## Formatting Rules

- Use `ruff format` for all Python files
- Line length: 119 characters
- Indentation: 4 spaces
- Use double quotes (`"`) for strings
- 2 lines between top-level function/class definitions
- Group imports: stdlib, third-party, local

## Type Hints

- Always use type hints for function parameters and return values

- Use `| None` instead of `Optional[]` for union types

- Use `-> None` for functions that return nothing

- Use `@dataclass` for data-only classes

- Do not use `getattr` unless unavoidable, prefer direct attribute access

- It is **NEVER** acceptable to return `dict[str, object]` from a method.

- Use `Annotated` for field definitions with additional metadata:

  ```python
  # ✅ Good
  from typing import Annotated
  from pydantic import Field

  name: Annotated[str, Field(min_length=1, description="User's full name")]

  # ❌ Avoid
  name: str = Field(..., min_length=1, description="User's full name")
  ```

- Use `Annotated` for complex type hints with constraints:

  ```python
  # ✅ Good
  from typing import Annotated
  from pydantic import Field

  age: Annotated[int, Field(ge=0, le=120)]

  # ❌ Avoid
  age: int = Field(..., ge=0, le=120)
  ```

## Naming Conventions

- Modules/files: `snake_case.py`
- Variables: `snake_case`
- Constants: `ALL_CAPS`
- Classes: `CamelCase`
- Functions: `snake_case()`
- Async functions: `async def snake_case()`

## Best Practices

- Use `pathlib.Path` instead of `os.path`
- Use `logging` instead of `print()`
- Use f-strings instead of `%` or `.format()`
- Use context managers (`with` statements)
- Use specific exceptions, not catch-all `except:`
- Prefer direct attribute access (`obj.attr`) over `getattr()` unless the attribute name is dynamic or requires a fallback.
- Do not use `getattr()` to bypass static analysis or typing; if the attribute is known, access it explicitly.
- Avoid global mutable state
- Use dependency injection for testability
- When using Pydantic objects, always use v2 conventions
- Always use timezone-aware alternatives (e.g., `datetime.now(datetime.UTC)`) instead of `datetime.utcnow()` to prevent DTZ003 lint errors and ensure correct, portable time handling throughout the codebase.

## Testing

- Use `pytest` for all tests
- Use `pytest-cov` for coverage
- Use `mypy` for static type checking
- User `just` for all DevOps task running; see [justfile](mdc:justfile)
- Avoid hard-coded paths/secrets in tests

## Anti-Patterns to Avoid

**Avoid**:

- Catch-all exceptions
- Mixing tabs and spaces
- Global mutable state
- Using `print()` in production code, except in tests.
- Manual JSON serialization
- Hungarian notation (e.g., `strName`, `iCount`)
- Using `__all__`; it's unnecessary unless explicitly curating a public API for from module `import *`, which we don't do.
