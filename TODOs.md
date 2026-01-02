# Ouroboros TODO List

> **Last Updated**: 2025-12-30 **Purpose**: Tracks tasks not captured in `.kiro/specs/` but identified through codebase analysis, ADR next steps, and technical debt

## 🔥 Critical - Blocking Production

### 1. Attack Edit/Add Modals (Web UI)

**Impact**: Users cannot modify attacks after campaign creation

- [ ] Implement attack edit modal in campaign detail page (`frontend/src/routes/campaigns/[id]/+page.svelte:123`)
- [ ] Implement add attack modal in campaign detail page (`frontend/src/routes/campaigns/[id]/+page.svelte:188`)
- [ ] Duplicate modals exist in `frontend/src/routes/resources/campaigns/[id]/+page.svelte` - consolidate or remove
- [ ] Add campaign export/import actions (`frontend/src/routes/campaigns/[id]/+page.svelte:409`)

**References**:

- ADR 001 Next Steps: Week 1, Item 2
- Phase 3a Task 5.2 (marked incomplete)
- Frontend TODOs: 4 instances

### 2. Resource Upload Completion

**Impact**: Users cannot upload resources beyond basic functionality

- [ ] Complete resource upload functionality (`frontend/src/routes/resources/campaigns/+page.svelte:102`)
- [ ] Implement upload status page or refresh mechanism
- [ ] Upgrade background verification to Celery (`app/core/tasks/resource_tasks.py:20`)
- [ ] Upgrade resource verification to Celery (`app/api/v1/endpoints/web/resources.py:379`)

**References**:

- ADR 001 Next Steps: Week 1, Item 2
- Phase 3a Task 6.1 (marked incomplete)
- Backend TODOs: 3 instances

### 3. Form Validation Gaps

**Impact**: Missing client-side and server-side validation

- [ ] Move validation to Pydantic layer (`app/api/v1/endpoints/web/auth.py:260`)
- [ ] Move business logic to service layer (`app/api/v1/endpoints/web/auth.py:263`, `:268`)
- [ ] Add missing form validations throughout Web UI API
- [ ] Implement resource validation for mask/rule/charset (`app/core/services/resource_service.py:378`)

**References**:

- ADR 001 Next Steps: Week 1, Item 2
- Backend TODOs: 4 instances

## ⚠️ High Priority - Production Hardening

### 4. Security Audit (ADR 001: Week 2-3, Item 3)

- [ ] CSRF protection validation
- [ ] XSS prevention audit
- [ ] Input validation review
- [ ] Rate limiting implementation (currently referenced but not enforced)
- [ ] CSP headers configuration

### 5. Authentication & Authorization Gaps

- [ ] Add authentication to attack endpoints (`app/api/v1/endpoints/web/attacks.py:133`, `:152`, `:253`, `:339`)
- [ ] Implement Control API key authentication (`app/api/v1/endpoints/control/campaigns.py:51`)
- [ ] Add project scoping to SSE endpoints (`app/api/v1/endpoints/web/live.py:51`, `:81`, `:111`)

**Backend TODOs**: 7 instances

### 6. Agent Service Improvements

**Impact**: Agent lifecycle and task management edge cases

- [ ] Check for existing agent by signature/hostname during registration (`app/core/services/agent_service.py:66`)
- [ ] Define missed heartbeat behavior (`app/core/services/agent_service.py:115`)
- [ ] Implement benchmark aggregation strategy (`app/core/services/agent_service.py:196`, `:199`)
- [ ] Add agent shutdown state (`app/core/services/agent_service.py:268`)
- [ ] Free tasks on agent shutdown (`app/core/services/agent_service.py:269`)
- [ ] Require re-benchmarking after shutdown (`app/core/services/agent_service.py:270`)
- [ ] Fix untyped dict return types (`app/core/services/agent_service.py:429`)

**Backend TODOs**: 7 instances

### 7. Task Service Enhancements

- [ ] Add exhausted task status (`app/core/services/task_service.py:193`)
- [ ] Update activity_timestamp on status updates (`app/core/services/agent_service.py:820`)
- [ ] Encapsulate state transition logic in Task model (`app/core/services/agent_service.py:821`)
- [ ] Provide error details for failed state transitions (`app/core/services/agent_service.py:822`)
- [ ] Convert string literals to enums (`app/core/services/agent_service.py:957`, `:962`)

**Backend TODOs**: 5 instances

### 8. Performance Testing (ADR 001: Week 2-3, Item 3)

- [ ] Test with large datasets (campaigns with 1000+ attacks)
- [ ] Load testing for concurrent users
- [ ] SSE connection stress testing
- [ ] Database query optimization validation

## 📋 Medium Priority - Feature Completion

### 9. Attack Complexity Service Enhancements

- [ ] Support hybrid_mask mode (-a 7) (`app/core/services/attack_complexity_service.py:1`)
- [ ] Add overflow detection for absurd keyspace sizes (`:12`)
- [ ] Add complexity level scoring to estimation (`:21`)
- [ ] Consider rule-based scoring or rule impact estimation (`:32`)
- [ ] Add sanity warnings for long masks (`:38`)

**Backend TODOs**: 5 instances

### 10. Campaign Service Improvements

- [ ] Add permission check for priority raising (`app/core/services/campaign_service.py:390`)
- [ ] Implement resource-modified tracking logic (`app/core/services/campaign_service.py:800`)
- [ ] Return updated attack list context (`app/api/v1/endpoints/web/attacks.py:117`)

**Backend TODOs**: 3 instances

### 11. Frontend Mock Data Replacement

- [ ] Replace mock session/role data in NightModeToggleButton (`frontend/src/lib/components/layout/NightModeToggleButton.svelte:7`)
- [ ] Replace mock status in ProjectSelector (`frontend/src/lib/components/layout/ProjectSelector.svelte:33`)
- [ ] Implement actual modal in attacks-list test (`frontend/e2e/attacks-list.test.ts:352`)

**Frontend TODOs**: 3 instances

## 🔮 Future Work - Agent API v2

> [!NOTE]
> Entire Agent API v2 implementation is deferred (Phase 2b - 0% complete)

### 12. Agent API v2 Endpoints (Scaffolded but not implemented)

- [ ] Implement agent registration endpoint (`app/api/v2/endpoints/agents.py:20`)
- [ ] Implement agent heartbeat endpoint (`app/api/v2/endpoints/agents.py:23`)
- [ ] Implement attack configuration endpoint (`app/api/v2/endpoints/attacks.py:19`)
- [ ] Implement resource URL endpoint (`app/api/v2/endpoints/resources.py:19`)
- [ ] Implement task assignment endpoint (`app/api/v2/endpoints/tasks.py:21`)
- [ ] Implement progress update endpoint (`app/api/v2/endpoints/tasks.py:24`)
- [ ] Implement result submission endpoint (`app/api/v2/endpoints/tasks.py:27`)
- [ ] Enable v2 API in main.py (`app/main.py:254`)

**Backend TODOs**: 8 instances **References**: Phase 2b (entire phase at 0%)

## 📚 Documentation (ADR 001: Week 3-4)

### 13. User Documentation

- [ ] User guide for SvelteKit UI workflows
- [ ] Operator handbook with screenshots and tutorials
- [ ] Campaign creation workflow guide
- [ ] Resource management guide
- [ ] Agent deployment and configuration guide

### 14. Developer Documentation

- [ ] Frontend architecture guide
- [ ] Component library documentation
- [ ] API integration patterns
- [ ] Testing strategy and guidelines
- [ ] Contribution guidelines

### 15. Deployment Documentation

- [ ] Production deployment guide
- [ ] Environment configuration reference
- [ ] Security best practices
- [ ] Monitoring and logging setup
- [ ] Backup and disaster recovery procedures

## 🧹 Technical Debt

### 16. Infrastructure Upgrades

- [ ] Migrate to Argon2 for password hashing (`app/core/security.py:12`)
- [ ] Upgrade background tasks to Celery when Redis available (multiple files)
- [ ] Implement proper Celery task queue system

**Backend TODOs**: 3 instances

### 17. Code Quality

- [ ] Remove duplicate campaign routes (`/campaigns` and `/resources/campaigns`)
- [ ] Consolidate duplicate attack modals
- [ ] Fix untyped dict return types throughout codebase
- [ ] Convert remaining string literals to enums

## 📊 Testing Gaps (Not in Specs)

### 18. E2E Test Coverage

> [!NOTE]
> Phase 3 (E2E Test Coverage) is 35% complete, but these specific gaps aren't captured as individual tasks

- [ ] Full E2E tests for attack editing workflow
- [ ] Full E2E tests for resource upload with all file types
- [ ] Full E2E tests for campaign template import/export
- [ ] Full E2E tests for agent registration and configuration
- [ ] Full E2E tests for SSE reconnection and resilience

### 19. Integration Tests

- [ ] Integration tests for Celery task execution (when implemented)
- [ ] Integration tests for MinIO presigned URL validation
- [ ] Integration tests for agent shutdown cascade effects
- [ ] Integration tests for concurrent campaign operations

### 20. Performance Tests

- [ ] Load tests for 100+ concurrent SSE connections
- [ ] Stress tests for bulk attack operations
- [ ] Performance tests for large wordlist uploads (>1GB)
- [ ] Query performance tests for campaigns with 10,000+ attacks

---

## Summary Statistics

- **Total TODOs identified**: 52 in code + 80+ missing tasks = **132+ items**
- **Critical (blocking production)**: 3 categories, ~20 items
- **High priority (production hardening)**: 8 categories, ~40 items
- **Medium priority (feature completion)**: 4 categories, ~15 items
- **Future work (Agent API v2)**: 8 endpoints
- **Documentation**: 15+ guides/documents
- **Technical debt**: 10+ items
- **Testing gaps**: 20+ test scenarios

## Notes

1. **Tasks.md files are accurate**: All `.kiro/specs/**/tasks.md` completion statuses match codebase reality
2. **No false completions found**: Team has been disciplined about marking tasks complete
3. **This file complements specs**: These TODOs represent work discovered through code analysis, ADR next steps, and production readiness assessment
4. **Priority ordering**: Critical → High → Medium → Future reflects production readiness path
