# Testing Guide

Ouroboros uses a comprehensive testing strategy with multiple layers of validation to ensure code quality, API compliance, and system reliability.

## Testing Architecture

### Test Organization

```
tests/
├── unit/                           # Unit tests (106 files)
│   ├── services/                   # Service layer tests
│   ├── plugins/                    # Plugin system tests
│   └── test_*.py                   # Individual component tests
├── integration/                    # Integration tests (36 files)
│   ├── agent/                      # Agent API tests
│   ├── web/                        # Web UI API tests
│   ├── control/                    # Control API tests
│   └── test_agent_api_v1_contract.py  # Contract compliance tests
├── factories/                      # Test data factories
│   ├── user_factory.py
│   ├── project_factory.py
│   └── campaign_factory.py
└── utils/                          # Test utilities and helpers
    ├── test_helpers.py
    └── hash_type_utils.py
```

### Test Types

1. **Unit Tests** - Test individual components in isolation
2. **Integration Tests** - Test API endpoints and service interactions
3. **Contract Tests** - Validate Agent API v1 compliance against OpenAPI spec
4. **End-to-End Tests** - Test complete workflows (planned)

## Running Tests

### Quick Commands

```bash
# Run all tests with coverage
just test

# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/

# Run specific test file
pytest tests/unit/test_campaign_service.py

# Run with verbose output
pytest -v tests/unit/test_campaign_service.py

# Run CI checks (formatting, linting, tests)
just ci-check
```

### Coverage Requirements

- **Target**: Minimum 80% coverage across all modules
- **Current Status**: 712 tests passing, comprehensive coverage
- **Reports**: Coverage XML generated at `coverage.xml`

## Test Categories

### Unit Tests (106 files)

Unit tests focus on testing individual components in isolation:

**Service Layer Tests:**

- `test_campaign_service.py` - Campaign business logic
- `test_attack_service.py` - Attack configuration and management
- `test_agent_service.py` - Agent lifecycle and management
- `test_hash_list_service.py` - Hash list operations
- `test_user_service.py` - User management
- `test_resource_service.py` - Resource file management
- `test_storage_service.py` - MinIO storage operations
- `test_template_service.py` - Attack template system
- `test_event_service.py` - Real-time event broadcasting

**Core Component Tests:**

- `test_authz.py` - Authorization and access control
- `test_hash_guess_service.py` - Hash type detection
- `test_attack_complexity_service.py` - Attack complexity scoring
- `test_task_assignment.py` - Task distribution algorithms
- `test_crackable_uploads_tasks.py` - File upload processing

**Plugin System Tests:**

- `test_base_plugin.py` - Plugin architecture
- `test_shadow_plugin.py` - Shadow file processing

### Integration Tests (36 files)

Integration tests validate API endpoints and cross-component interactions:

**Agent API Tests:**

- Agent registration and authentication
- Task assignment and distribution
- Result submission and validation
- Heartbeat and status management
- Resource access and downloads

**Web UI API Tests:**

- Campaign CRUD operations
- Attack configuration and management
- Real-time event streaming (SSE)
- Resource management and uploads
- User authentication and project context

**Control API Tests:**

- Programmatic campaign management
- RFC9457-compliant error responses
- API key authentication
- Batch operations

### Contract Testing

**Agent API v1 Compliance:**

- `test_agent_api_v1_contract.py` - Validates exact compliance with `contracts/v1_api_swagger.json`
- Schema validation for all request/response formats
- Error response format compliance
- Endpoint behavior verification

## Test Data Management

### Factories

Ouroboros uses Polyfactory for generating test data:

```python
# Example factory usage
user = await UserFactory.create_async()
project = await ProjectFactory.create_async()
campaign = await CampaignFactory.create_async(project_id=project.id, created_by=user.id)
```

**Available Factories:**

- `UserFactory` - User accounts with roles
- `ProjectFactory` - Project containers
- `CampaignFactory` - Campaign configurations
- `AttackFactory` - Attack definitions
- `HashListFactory` - Hash list containers
- `AgentFactory` - Agent registrations

### Database Fixtures

Tests use isolated database sessions:

```python
@pytest.mark.asyncio
async def test_campaign_creation(db_session):
    # Test uses isolated database session
    campaign = await create_campaign_service(db_session, campaign_data)
    assert campaign.name == "Test Campaign"
```

## Testing Best Practices

### Service Layer Testing

```python
@pytest.mark.asyncio
async def test_create_campaign_service_success(db_session):
    # Arrange
    user = await UserFactory.create_async()
    project = await ProjectFactory.create_async()
    campaign_data = CampaignCreate(name="Test Campaign", project_id=project.id)

    # Act
    result = await create_campaign_service(db_session, campaign_data, user.id)

    # Assert
    assert result.name == "Test Campaign"
    assert result.project_id == project.id
```

### API Endpoint Testing

```python
@pytest.mark.asyncio
async def test_create_campaign_endpoint(authenticated_client, db_session):
    # Test API endpoint with authentication
    response = await authenticated_client.post(
        "/api/v1/web/campaigns/", json={"name": "Test Campaign", "project_id": 1}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Campaign"
```

### Error Testing

```python
@pytest.mark.asyncio
async def test_campaign_not_found_error(db_session):
    with pytest.raises(CampaignNotFoundError):
        await get_campaign_service(db_session, 999)
```

## Mocking and Test Isolation

### External Dependencies

```python
@pytest.fixture
def mock_minio_client():
    with patch("app.core.storage.minio_client") as mock:
        yield mock


@pytest.mark.asyncio
async def test_file_upload(mock_minio_client, db_session):
    # Test with mocked MinIO client
    mock_minio_client.put_object.return_value = None
    result = await upload_file_service(db_session, file_data)
    assert result.status == "uploaded"
```

### Authentication Mocking

```python
@pytest.fixture
def authenticated_client():
    # Returns client with valid authentication headers
    return TestClient(app, headers={"Authorization": "Bearer test-token"})
```

## Continuous Integration

### GitHub Actions Integration

Tests run automatically on:

- Pull requests
- Pushes to main branch
- Scheduled runs (nightly)

### CI Pipeline

```yaml
  - name: Run Tests
    run: just ci-check
    env:
      DATABASE_URL: postgresql://test:test@localhost:5432/test_db
      TESTING: true
```

## Test Configuration

### Environment Variables

```bash
# Test database
DATABASE_URL=postgresql://test:test@localhost:5432/test_db
TESTING=true

# Disable external services in tests
MINIO_ENDPOINT=mock://localhost
REDIS_URL=memory://
```

### Pytest Configuration

```ini
# pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
addopts =
    --cov=app
    --cov-report=xml
    --cov-report=term-missing
    --strict-markers
```

## Current Status

### Phase 2 API Implementation Testing

✅ **Completed:**

- Unit test coverage for all service layers (106 test files)
- Integration tests for all API interfaces (36 test files)
- Agent API v1 contract compliance testing
- Comprehensive test data factories
- CI/CD integration with automated testing
- Coverage reporting and quality gates

### Test Metrics

- **Total Tests**: 712 passing, 1 xfailed
- **Test Files**: 142 total test files
- **Coverage**: Comprehensive coverage across all modules
- **Execution Time**: ~4.5 minutes for full suite
- **Contract Compliance**: Agent API v1 fully validated against OpenAPI spec

### Areas for Enhancement

While the testing infrastructure is comprehensive, some areas could be enhanced:

1. **End-to-End Testing**: Full workflow testing with real browser automation
2. **Performance Testing**: Load testing for high-throughput scenarios
3. **Security Testing**: Automated security vulnerability scanning
4. **Frontend Testing**: Component and integration tests for SvelteKit UI

## Troubleshooting

### Common Issues

**Database Connection Errors:**

```bash
# Reset test database
just db-reset
```

**Import Errors:**

```bash
# Ensure proper Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

**Async Test Issues:**

```python
# Use proper async test decorators
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result is not None
```

### Debug Mode

```bash
# Run tests with debug output
pytest -v -s tests/unit/test_campaign_service.py

# Run single test with pdb
pytest --pdb tests/unit/test_campaign_service.py::test_specific_function
```

## Contributing

When adding new features:

1. **Write tests first** (TDD approach)
2. **Maintain coverage** above 80%
3. **Update factories** for new models
4. **Add integration tests** for new endpoints
5. **Update contract tests** for Agent API changes
6. **Document test scenarios** in docstrings

For more information, see the [Developer Guide](developer_guide.md) and [Contributing Guidelines](../../CONTRIBUTING.md).
