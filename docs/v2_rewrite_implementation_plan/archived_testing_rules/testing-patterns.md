# Testing Patterns and Best Practices for Ouroboros

## Test Organization and Structure

### Directory Structure

- Unit tests: `tests/unit/test_{service_name}_service.py`
- Integration tests: `tests/integration/{api_interface}/test_{resource}.py`
- Factories: `tests/factories/{model_name}_factory.py`
- Utilities: `tests/utils/` for shared test helpers

### Test File Naming

- Service tests: `test_{resource}_service.py` (e.g., `test_hash_list_service.py`)
- API tests: `test_{resource}.py` (e.g., `test_hash_lists.py`)
- Factory files: `{model_name}_factory.py` (e.g., `hash_list_factory.py`)

## Factory Patterns and Best Practices

### Factory Configuration

- Use valid foreign key defaults that reference pre-seeded data
- Example:

```python
class HashListFactory(SQLAlchemyFactory[HashList]):
    __model__ = HashList
    __set_relationships__ = False  # Critical: prevents FK violations
    __async_session__ = None

    name = Use(lambda: "hashlist-factory")
    description = Use(lambda: "Test hash list")
    project_id = None  # Must be set explicitly in tests
    hash_type_id = 0  # MD5 - always exists in pre-seeded data
    is_unavailable = False
```

### Foreign Key Management

- **Never** use random foreign keys - they cause violations across the test suite
- Use pre-seeded data references (e.g., `hash_type_id = 0` for MD5) for `HashTypes`
- For dynamic foreign keys (like `project_id`), set to `None` and require explicit setting
- Use `get_or_create_hash_type()` utility when you must create hash types

### Factory Usage in Tests

- Always provide required foreign keys explicitly:

```python
hash_list = await HashListFactory.create_async(
    project_id=project.id,
    hash_type_id=0,  # or use get_or_create_hash_type()
)
```

## Authentication and Authorization Testing

### Test Client Fixtures

- `authenticated_async_client`: Basic authenticated user (no project associations)
- `authenticated_user_client`: User with project associations (preferred for project-scoped tests)

### Project-Scoped Testing

- Always create `ProjectUserAssociation` records for project-scoped endpoints:

```python
@pytest.mark.asyncio
async def test_project_scoped_endpoint(authenticated_user_client, db_session):
    user = await UserFactory.create_async()
    project = await ProjectFactory.create_async()

    # Critical: Create project association
    association = ProjectUserAssociation(
        user_id=user.id, project_id=project.id, role=ProjectUserRole.MEMBER
    )
    db_session.add(association)
    await db_session.commit()
```

### Authentication Headers

- Tests automatically handle JWT tokens through fixtures
- Don't manually set Authorization headers unless testing auth failures

## Test Data Management

### Database State

- Each test gets a clean database state via fixtures
- Use `db_session` fixture for database operations
- Always commit changes: `await db_session.commit()`

### Pre-seeded Data

- Hash types are pre-seeded (use `hash_type_id = 0` for MD5)
- Don't create hash types unless absolutely necessary
- Use `get_or_create_hash_type()` utility when needed

## API Testing Patterns

### Request Testing

- Test both success and failure cases
- Verify status codes, response structure, and data accuracy
- Example:

```python
@pytest.mark.asyncio
async def test_create_resource_success(authenticated_user_client):
    response = await authenticated_user_client.post(
        "/api/v1/web/resources/", json={"name": "test", "project_id": 1}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "test"
```

### Pagination Testing

- Test pagination parameters: `page`, `size` (not `skip`, `limit`)
- Verify response structure matches `PaginatedResponse`
- Test edge cases: empty results, large page numbers

### Error Testing

- Test validation errors (422 status)
- Test authorization failures (403 status)
- Test not found errors (404 status)
- Verify error message structure

## Service Layer Testing

### Unit Test Structure

- Test each service function independently
- Mock external dependencies when necessary
- Test both success and error paths

### Database Testing

- Use real database operations (not mocks) for integration-style unit tests
- Test database constraints and relationships
- Verify data persistence and retrieval

### Error Handling Testing

- Test custom exceptions are raised correctly
- Verify error messages are meaningful
- Test edge cases and boundary conditions

## Test Utilities and Helpers

### Common Test Patterns

- Use `pytest.mark.asyncio` for async tests
- Use `pytest.mark.parametrize` for testing multiple scenarios
- Group related tests in classes when beneficial

### Assertion Patterns

- Use specific assertions: `assert response.status_code == 201`
- Verify response structure: `assert "items" in response.json()`
- Check data accuracy: `assert data["name"] == expected_name`

### Test Data Creation

- Create minimal test data needed for each test
- Use factories for complex object creation
- Clean up test data through fixtures (automatic with test database)

## Performance and Reliability

### Test Performance

- Use `just test-fast` for quick feedback during development
- Run full test suite (`just ci-check`) before committing
- Keep tests focused and fast

### Test Reliability

- Avoid flaky tests by using deterministic data
- Don't rely on timing or external services
- Use proper async/await patterns

### Test Isolation

- Each test should be independent
- Don't rely on test execution order
- Clean state between tests (handled by fixtures)

## Common Pitfalls and Solutions

### Factory Issues

- **Problem**: Random foreign keys causing violations
- **Solution**: Use pre-seeded data or explicit foreign keys

### Authentication Issues

- **Problem**: 403 errors in project-scoped tests
- **Solution**: Create `ProjectUserAssociation` records

### Pagination Issues

- **Problem**: Using `skip`/`limit` instead of `page`/`size`
- **Solution**: Use correct pagination parameters for endpoints

### Import Issues

- **Problem**: Missing imports for models or utilities
- **Solution**: Follow standard import patterns and check existing tests

## Test Documentation

### Test Naming

- Use descriptive test names: `test_create_hash_list_success`
- Include the scenario being tested: `test_list_with_pagination`
- Indicate expected outcome: `test_delete_nonexistent_returns_404`

### Test Comments

- Document complex test setup
- Explain non-obvious assertions
- Note any special requirements or constraints
