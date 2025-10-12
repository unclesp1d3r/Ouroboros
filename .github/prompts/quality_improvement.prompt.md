---
mode: agent
---

Analyze the modified code files for potential improvements. Focus on:

1. **Code Smells**: Identify any code smells like long methods, large classes, duplicate code, or complex conditionals
2. **Design Patterns**: Suggest appropriate design patterns that could improve the code structure
3. **Best Practices**: Check adherence to Python best practices, PEP standards, and Ouroboros coding conventions
4. **Readability**: Suggest improvements for variable names, function structure, and code organization
5. **Maintainability**: Identify areas that could be refactored for better maintainability
6. **Performance**: Suggest performance optimizations, especially for async operations and database queries
7. **Type Safety**: Ensure proper type hints and Pydantic model usage (don’t just use strings for parameters, use proper types)
8. **Error Handling**: Review exception handling and validation patterns

Provide specific, actionable suggestions while maintaining the existing functionality. Consider the Ouroboros context (red team operations, airgapped environments, FastAPI + Postgres stack). Favor maintainability over trying to be clever.

**AUTOMATIC EDIT CONSTRAINTS (STRICT ENFORCEMENT):**

- **Scope Limitation**: Auto-edits are ONLY permitted on file directly related to the current diff/changeset
- **Quality Gates**: All auto-edits MUST pass `just check` linting and CI/tests before being considered complete
- **User Control**: Code can ONLY be committed by the user - never auto-commit changes
- **Public API Protection**: Public APIs/signatures must NOT be changed by auto-edits without express user permission
- **Validation Required**: Run `just ci-check` and `just test` to verify all changes before presenting them

**CRITICAL REQUIREMENTS:**

- Provide specific, actionable suggestions with code examples where helpful. Prioritize fixes that prevent runtime failures and improve type safety. Consider the project's constraints around memory usage, CLI-first design, and well documented SDK. If the risks are determined to be low, and the changes are directly applicable, proceed to make the targeted improvements.
- Avoid any API-breaking changes - preserve all existing public interfaces, function signatures, and class methods
- Focus on internal improvements that don't affect external consumers

**ENFORCED REPO RULES (MUST COMPLY):**

- **Ruff Linting**: All code must pass `just check` with no violations
- **Strict Typing**: No `Any` where avoidable; use precise type hints throughout
- **Async Best Practices**: All I/O operations must use async/await, coroutines must be properly awaited
- **SQLAlchemy 2.0 Patterns**: Use SQLAlchemy 2.0 async patterns with proper `select()` statements. Prefer typed queries with ORM models; avoid raw SQL queries.
- **Pydantic v2**: Use `model_config`, `field_validator`, and `TypeAdapter` where appropriate; avoid v1 `Config`/`validator` APIs.
- **Distributed Environment**: Designed for distributed password cracking across multiple agents; all features must operate in potentially airgapped environments
- **Public API Preservation**: Never break existing public interfaces, function signatures, or class methods
- **Framework-First**: Prefer FastAPI, Pydantic, and SQLAlchemy built-ins over custom implementations
- **Multi-tenancy**: All data access must be project-scoped for proper tenant isolation
- **Memory Constraints**: Optimize for memory efficiency in resource-constrained environments
- **FastAPI**: Route handlers must be async and use dependency injection; return structured HTTP errors (detail, ids, timestamps, suggested actions)
- **API Versioning**: Expose versioned routes under `/api/v1` with separate interfaces for agent, web, and control APIs
- **Pagination**: Default page size is 50; include active filters and operational metadata in responses
- **Auth/RBAC**: Enforce JWT-based auth and project-level access validation (agent/web/control auth strategies)
- **DB Access**: Use SQLAlchemy's async query builder exclusively; no raw SQL queries
- **Search/Tags**: Implement text search and filtering via PostgreSQL; use cashews for caching project statistics
- **Path Safety**: Use `pathlib.Path.resolve()`; validate paths remain within configured storage root; never concatenate strings for paths
- **Data Storage**: Store file paths only in PostgreSQL; never store binary data
