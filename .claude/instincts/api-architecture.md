# Instinct: Three-API Architecture

**Confidence**: 100% **Source**: AGENTS.md, codebase structure **Category**: architecture

## Pattern

Ouroboros uses three distinct APIs with different purposes and authentication:

### Agent API (`/api/v1/client/*`)

- **Purpose**: Communication with CipherSwarmAgent (Go hashcat runners)
- **Auth**: Bearer token (`csa_<agent_id>_<random>`)
- **Contract**: IMMUTABLE - locked to `contracts/v1_api_swagger.json`
- **Breaking changes**: NEVER allowed

### Web UI API (`/api/v1/web/*`)

- **Purpose**: SvelteKit frontend interactions
- **Auth**: OAuth2 + refresh tokens (session cookies)
- **Responses**: Optimized for UI consumption

### Control API (`/api/v1/control/*`)

- **Purpose**: CLI tool (csadmin), automation, integrations
- **Auth**: API key bearer (`cst_<user_id>_<random>`)
- **Errors**: RFC9457 `application/problem+json` format
- **Pagination**: Offset-based for programmatic consumption

## Service Layer Reuse

All three APIs delegate to shared service functions:

```
Web UI API  ──┐
Control API ──┼──> app/core/services/* ──> SQLAlchemy ORM
Agent API   ──┘
```

## Trigger

Activate when:

- Creating new endpoints
- Modifying existing API behavior
- Discussing authentication
- Planning API changes
