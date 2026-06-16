# ADR 001: Remove NiceGUI Integration, Use SvelteKit Frontend Only

## Status

**Accepted** - 2025-12-30

## Context

Ouroboros originally planned a dual-frontend strategy:

1. **SvelteKit** - Modern TypeScript-based SPA frontend
2. **NiceGUI** - Python-native web interface integrated into FastAPI

The original intent (documented in `.kiro/specs/`) was to:

- Build NiceGUI as a complete replacement for SvelteKit
- Simplify deployment to a single Python-only application
- Eliminate Node.js dependency and frontend tooling complexity
- Reduce maintenance overhead by having a single codebase

However, development resources were primarily invested in the SvelteKit frontend, while NiceGUI implementation stalled early.

## Decision

**We will remove NiceGUI entirely and standardize on SvelteKit as the sole frontend.**

### Rationale

#### Completeness Analysis

**SvelteKit Frontend:**

- **85% complete** with production-ready features
- 30 routes implemented (dashboard, campaigns, attacks, agents, resources, users, settings)
- 300+ UI components with consistent design
- 40+ test files (unit, component, E2E with Playwright)
- Comprehensive features: CRUD operations, pagination, filtering, sorting, SSE real-time updates
- Professional UI/UX with Tailwind CSS and shadcn-svelte
- TypeScript strict mode for type safety
- Modern Svelte 5 with runes for reactive state management

**NiceGUI Interface:**

- **14% complete** - only authentication implemented
- 1 functional page (login only)
- 0 test files
- No dashboard, campaign management, agent monitoring, or any core features
- Estimated 6-8 weeks of full-time work to reach feature parity

#### Maintenance Burden

Maintaining two parallel UIs would require:

- Implementing every feature twice
- Writing tests for both UIs
- Fixing bugs in two codebases
- Keeping feature parity synchronized
- Documenting two different user experiences

This represents an unsustainable maintenance burden for marginal benefit.

#### Deployment "Simplification" is Theoretical

The promised benefits of NiceGUI were:

- ✗ **Single-language stack** - But project already has Node.js working well
- ✗ **Simplified deployment** - But Docker already handles multi-container setup
- ✗ **Lower complexity** - But SvelteKit is already mature and stable
- ✗ **Easier for backend devs** - But frontend is feature-complete, not under active UI development

In practice:

- SvelteKit deployment is already containerized and working
- Docker Compose handles orchestration cleanly
- Node.js dependency is negligible (already present, tested, working)
- The complexity of managing two UIs far exceeds the complexity of deploying SvelteKit

#### Technical Superiority of SvelteKit

For complex password cracking management UIs, SvelteKit offers:

- Better performance for data-heavy tables and charts
- Superior developer experience with TypeScript
- Larger ecosystem and community support
- Better testing frameworks (Vitest + Playwright)
- More mature component libraries
- Better accessibility features

### Implementation Status

**Completed 2025-12-30:**

- [x] Removed `app/ui/` directory (NiceGUI code)
- [x] Removed NiceGUI imports and setup from `app/main.py`
- [x] Removed `nicegui` dependency from `pyproject.toml`
- [x] Removed `server` entrypoint script from `pyproject.toml`
- [x] Reverted Dockerfile to use `uvicorn app.main:app` directly
- [x] Reverted Dockerfile.dev to use `uvicorn app.main:app --reload`
- [x] Reverted docker-compose.dev.yml commands
- [x] Reverted justfile `dev-backend` recipe
- [x] Removed `.kiro/specs/nicegui-web-interface/`
- [x] Removed `.kiro/specs/sveltekit-frontend-removal/`
- [x] Verified README.md correctly shows SvelteKit as frontend

## Consequences

### Positive

- **Clear direction**: Single frontend to maintain and improve
- **Faster development**: Focus resources on completing SvelteKit TODOs
- **Better user experience**: Professional, polished UI instead of incomplete alternative
- **Reduced technical debt**: No dual-UI synchronization burden
- **Clearer documentation**: Single user guide, no confusion about which UI to use
- **Better testing**: Focus test resources on one comprehensive suite

### Negative

- **Node.js dependency remains**: Can't deploy Python-only (acceptable tradeoff)
- **Two-container deployment**: Backend + Frontend (already working, minimal overhead)
- **Backend devs need frontend knowledge**: For UI contributions (but UI is 85% done)

### Neutral

- **Docker setup unchanged**: SvelteKit was already in docker-compose.yml
- **API design unaffected**: Agent API and Control API remain unchanged
- **Backend services unchanged**: Service layer, database, auth all unchanged

## Next Steps

### Immediate (Week 1)

1. [x] Remove all NiceGUI code and references
2. Complete remaining SvelteKit TODOs:
   - Implement attack edit/add modals
   - Complete resource upload functionality
   - Add any missing form validations

### Short-term (Week 2-3)

3. Production hardening:
   - Security audit (CSRF, XSS, input validation)
   - Performance testing with large datasets
   - Add rate limiting
   - Configure CSP headers
4. Testing enhancement:
   - Add E2E tests for incomplete features
   - Integration test for SSE connections
   - Load testing

### Documentation (Week 3-4)

5. Update user documentation:
   - User guide for SvelteKit UI workflows
   - Operator handbook
   - Screenshots and tutorials
6. Update developer documentation:
   - Frontend architecture guide
   - Component library documentation
   - Contribution guidelines

## References

- `.kiro/specs/nicegui-web-interface/` (removed)
- `.kiro/specs/sveltekit-frontend-removal/` (removed)
- Codebase analysis showing 85% vs 14% completion
- Original architectural vision documents

## Notes

This decision prioritizes **pragmatism over idealism**. While the vision of a Python-only stack had merit, the execution reality shows that:

1. SvelteKit reached production quality
2. NiceGUI implementation never progressed beyond scaffolding
3. Maintaining both UIs is unsustainable

The right decision is to cut losses, acknowledge what works (SvelteKit), and focus resources on completing and polishing the production-ready solution rather than pursuing an incomplete alternative.

---

**Reviewed by**: Original Developer **Date**: 2025-12-30 **Status**: Implemented
