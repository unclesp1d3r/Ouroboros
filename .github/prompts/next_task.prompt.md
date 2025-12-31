---
mode: agent
---

1. Read the entire tasks.md document before beginning. Do not skip this step.
2. Identify the next unchecked task in the checklist.

> ⚠️ Important: Some tasks may appear implemented but are still unchecked. You must verify that each task meets all project standards. "Complete" means the code is fully implemented, idiomatic, tested, lint-free, and aligned with all coding and architectural rules.

#### Task Execution Process

- Review the codebase to determine whether the task is already complete **according to project standards**.
- If the task is not fully compliant:
  - Make necessary code changes using idiomatic, maintainable approaches.
  - Run `just format` to apply formatting rules.
  - Add or update tests to ensure correctness.
  - Run the test suites:
    - `just test`
  - Fix any failing tests.
  - Run the linters:
    - `just check`
  - Fix all linter issues.
- Run `just ci-check` to confirm the full codebase passes final validation.

#### Completion Checklist

- [x] Code conforms to project rules and standards
- [x] Tests pass (`just test`)
- [x] Linting is clean (`just check`)
- [x] Task is marked complete in the checklist
- [x] A short summary of what was done is reported

> Update the @tasks.md task list with any items that are implemented and need test coverage, checking off items that have implemented tests. ❌ Do **not** commit or check in any code ⏸️ Do **not** begin another task ✅ Stop and wait for further instruction after completing this task
