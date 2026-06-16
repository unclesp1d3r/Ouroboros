# Ouroboros Phase 2 Endpoint Hygiene Sweep

Skirmish must complete this sweep after all `/api/v1/web/*` endpoints have been implemented and tested.

This pass is required to clean up minor violations of project-specific coding standards that may not be caught by `just ci-check` but are essential to long-term quality.

---

## Common Skipped Rules to Fix

### [FAIL] Skipped: Proper SvelteKit Integration

- [x] Replace all legacy server-rendered endpoints with SvelteKit JSON API endpoints and Svelte components
- [x] SvelteKit endpoints **must return a valid JSON API response**, not a server-rendered template
- [x] The response fields are unpacked automatically and available as top-level variables in the Svelte component

> See: `sveltekit-guidelines.mdc` — SvelteKit endpoints must always use JSON API.

---

### [FAIL] Skipped: Endpoint Purity

- [ ] Ensure **no database access** occurs in endpoint functions (move all DB access to services or `crud.py`)
- [ ] Use `Depends(get_db)` only inside service-layer helpers, not in the route body

> See: `service-patterns.mdc` — all persistence logic must be kept outside endpoints.

---

### [FAIL] Skipped: FastAPI Idiomatic Parameter Usage

- [ ] Remove all usage of `request: Request` for parameter parsing or user/project extraction
- [ ] Forms should never be parsed from the request body or the form data, each field should be a proper `Annotated[Form, ...]` parameter
- [ ] Replace with proper `Annotated[...]` dependencies:

```python
user: Annotated[User, Depends(current_user)]
project: Annotated[Project, Depends(get_current_project)]
```

> See: `fastapi-guidelines.mdc` — context should always use DI, never request-manual parsing.

---

### 🧼 Style Cleanups

#### `getattr` vs direct access

- [ ] Replace `getattr(foo, "bar")` with `foo.bar` unless:

  - Field is dynamic
  - There's a fallback value
  - Object may be missing the attribute and is guarded

#### Typing + Models

- [ ] Eliminate `dict[str, object]` returns
- [ ] Ensure all route input/output is typed with Pydantic v2 models

#### Imports

- [ ] Alphabetize imports within groups (`stdlib`, `third-party`, `local`)
- [ ] Remove any unused imports that snuck back in

> See: `python-style.mdc` — use direct access over reflection, and structure imports consistently.

---

## Final Checks

- [ ] Run full `just ci-check` again
- [ ] Launch `just dev` and download the `openapi.json` file to verify the generated schema is correct

---

## [x] Completion Criteria

All existing `/api/v1/web/*` endpoints must conform to:

- JSON API for any SvelteKit route
- Service-layer separation for DB logic
- Proper FastAPI DI for context
- Clean, direct attribute access
- Valid OpenAPI schema (Pydantic-typed, no JSON dict hacks)
