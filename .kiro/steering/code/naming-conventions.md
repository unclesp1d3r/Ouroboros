---
inclusion: fileMatch
fileMatchPattern: "**/*.py"
---

## Model + Schema Naming

- Models: `PascalCase` (e.g., `Agent`, `CrackSession`, `TaskResult`)
- Table names: snake_case (e.g., `crack_session`, `task_result`)
- Schemas: `PascalCase` + `Create`, `Update`, `Out` (e.g., `AgentCreate`, `TaskOut`)

## File + Function Naming

- Files: `snake_case.py`
- Functions/methods: `snake_case`
- CLI subcommands: match filename (e.g., `task.py` → `task()`)

## Cursor Enforcement

- Don't invent new naming styles.
- Match models and schema suffixes (`Create`, `Update`, etc.).
- Match filenames to the primary class or purpose.

### Additional Guidelines

- Schema classes must follow suffix conventions: `Create`, `Update`, `Out`, `InDB`.
- CLI command handlers must be named consistently with their files and entrypoints.
