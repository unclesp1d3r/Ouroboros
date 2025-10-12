### 📦 Task Note: MinIO Testcontainers Support (`task_id:testcontainers.minio_support`)

**Task Description:**

> Add `MinioContainer` from `testcontainers.minio` to enable integration tests for MinIO-based services.

**Context:**

- Ouroboros uses MinIO as its object storage backend for attack resources (wordlists, rules, masks, charsets).

- Existing integration tests use `PostgresContainer` from `testcontainers.postgresql` to spin up isolated environments.

- We need to provide similar test coverage for endpoints that interact with MinIO, particularly:

  - Upload flow (presign generation, DB row creation)
  - Download access and validation
  - Resource import/export logic
  - Crackable uploads (Phase 2b/3)

**Implementation Tasks:**

- [x] Add test dependency: `testcontainers[minio]`
- [x] Create a `minio_container` pytest fixture using `MinioContainer`
- [ ] Set up the MinIO endpoint (host/port/access keys) as overrideable config for test environment
- [ ] Auto-create buckets needed for tests (`wordlists`, `rules`, etc.)
- [ ] Ensure container fixture is used alongside `postgres_container` in affected integration test modules
- [ ] Validate that resource endpoints (upload, metadata, linking, ephemeral resource fetches) behave correctly
- [ ] Optionally seed a test wordlist or rule file for integration coverage
- [ ] Update `tests/integration/test_uploads.py` and related files

**Config Integration:**

- The `config.py` should support injecting `MINIO_ENDPOINT`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, and `MINIO_BUCKET_PREFIX` from environment or test fixture override.
- Consider a base test class or `conftest.py` helper to centralize test MinIO bootstrapping.

**CI Requirements:**

- [ ] Ensure the MinIO container fixture works in GitHub Actions or CI environment (expose ports, handle healthcheck)
- [ ] Include at least one upload + presign + fetch test in `just ci-check`

**References:**

- [Testcontainers MinIO Docs](https://testcontainers-python.readthedocs.io/en/latest/modules/minio/README.html)
- [`phase-2b-resource-management.md`](../phase-2b-resource-management.md)
- [Ouroboros Docker/MinIO Standards](.cursor/rules/architecture/core-concepts.mdc)
- [Ouroboros Docker Guidelines](.cursor/rules/architecture/docker-guidelines.mdc)
