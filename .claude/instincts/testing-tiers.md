# Instinct: Testing Tiers

**Confidence**: 100% **Source**: AGENTS.md, justfile **Category**: workflow

## Pattern

Use the smallest test tier that covers your changes.

### Tier Selection

| Tier     | Command                      | Use When                                       |
| -------- | ---------------------------- | ---------------------------------------------- |
| Backend  | `just test-backend`          | Backend logic, services, models, API endpoints |
| Frontend | `pnpm test` (from frontend/) | UI components, client logic, stores            |
| E2E      | `just test-e2e`              | Complete user workflows, integration           |
| CI Check | `just ci-check`              | PR-ready, touching multiple tiers              |

### Decision Tree

```
Did you change Python code?
├─ Yes → just test-backend
│   └─ Also changed frontend? → just ci-check
└─ No
    └─ Did you change frontend code?
        ├─ Yes → cd frontend && pnpm test
        └─ No (docs only, config) → skip tests
```

### Skip Testing When

- Verification-only tasks (reading code, answering questions)
- Documentation-only changes
- Configuration tweaks that don't affect behavior

### Run `just ci-check` When

- PR is ready for review
- Changes span backend AND frontend
- Unsure what's affected

## Anti-patterns

- Running `just ci-check` for every small backend change
- Skipping tests entirely for code changes
- Running E2E tests for unit-testable logic

## Trigger

Activate when:

- Completing code changes
- Preparing commits
- Before creating PRs
