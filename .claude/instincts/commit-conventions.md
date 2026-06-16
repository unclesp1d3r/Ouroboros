# Instinct: Commit Conventions

**Confidence**: 95% **Source**: Git history analysis (100+ commits) **Category**: workflow

## Pattern

When creating commits in the Ouroboros project:

1. Use conventional commit format: `<type>(<scope>): <description>`
2. Most common types: `chore`, `fix`, `feat`, `docs`, `test`, `ci`
3. Common scopes: `api`, `deps`, `docs`, `auth`, `security`, `state-machines`
4. Keep descriptions lowercase and concise
5. No period at end of subject line

## Examples

```
fix(api): improve error handling and add get_valid_actions method
test(state-machines): add tests for get_valid_actions method
chore(deps): bump docker/login-action from 3.6.0 to 3.7.0
docs: link CLAUDE.md to AGENTS.md for reference
feat(api): implement Agent API v2 with enhanced features
```

## Anti-patterns

- `Fixed bug` (missing type/scope)
- `feat(api): Added new feature.` (capitalized, has period)
- Long multi-line commit messages for simple changes
