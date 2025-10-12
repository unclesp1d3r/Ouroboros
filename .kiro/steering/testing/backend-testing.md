---
inclusion: fileMatch
fileMatchPattern:

  - tests/unit/\*\*/\*.py
  - tests/integration/\*\*/\*.py
  - app/core/services/\*\*/\*.py
  - tests/conftest.py
---

# Ouroboros Backend Testing Patterns

## Backend Testing Architecture

### pytest + testcontainers + PostgreSQL

- Service layer and API endpoint testing
- Real database operations, no mocks
- Async/await patterns throughout

> [!NOTE]
> For core testing principles, architecture overview, and coverage requirements, see [testing-core.md](testing-core.md).

## Factory Usage Patterns

> [!NOTE]
> For comprehensive factory patterns, async creation, FK handling, and seeding strategies, see [testing-factories.md](testing-factories.md).

### Quick Factory Setup for Backend Tests

```python
# Set session for factories
UserFactory.__async_session__ = db_session
ProjectFactory.__async_session__ = db_session

# Create test data with explicit FKs
project = await ProjectFactory.create_async()
hash_list = await HashListFactory.create_async(project_id=project.id)
```

## Service Layer Testing

### Service Test Structure

```python
@pytest.mark.asyncio
async def test_create_hash_list_service(db_session):
    # Arrange
    project = await ProjectFactory.create_async()
    data = HashListCreate(name="test-hashlist", project_id=project.id, hash_type_id=0)

    # Act
    result = await create_hash_list_service(db_session, data)

    # Assert
    assert result.name == "test-hashlist"
    assert result.project_id == project.id

    # Verify persistence
    saved = await get_hash_list_service(db_session, result.id)
    assert saved.name == "test-hashlist"
```

### Service Error Testing

```python
@pytest.mark.asyncio
async def test_create_hash_list_service_duplicate_name_error(db_session):
    project = await ProjectFactory.create_async()

    # Create first hash list
    data = HashListCreate(name="duplicate", project_id=project.id, hash_type_id=0)
    await create_hash_list_service(db_session, data)

    # Attempt to create duplicate
    with pytest.raises(ValueError, match="already exists"):
        await create_hash_list_service(db_session, data)
```

### Service Validation Testing

```python
@pytest.mark.asyncio
async def test_update_campaign_service_validates_state_transition(db_session):
    project = await ProjectFactory.create_async()
    hash_list = await HashListFactory.create_async(project_id=project.id)
    campaign = await CampaignFactory.create_async(
        project_id=project.id, hash_list_id=hash_list.id, state=CampaignState.COMPLETED
    )

    # Cannot transition from COMPLETED to ACTIVE
    with pytest.raises(InvalidStateTransitionError):
        await start_campaign_service(db_session, campaign.id)
```

## API Endpoint Testing

### Basic API Test Pattern

```python
@pytest.mark.asyncio
async def test_create_hash_list_endpoint(authenticated_user_client):
    response = await authenticated_user_client.post(
        "/api/v1/web/hash-lists/",
        json={
            "name": "test-hashlist",
            "project_id": 1,
            "hash_type_id": 0,
            "description": "Test description",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "test-hashlist"
    assert data["project_id"] == 1
```

### API Error Response Testing

```python
@pytest.mark.asyncio
async def test_create_hash_list_validation_error(authenticated_user_client):
    response = await authenticated_user_client.post(
        "/api/v1/web/hash-lists/",
        json={"name": ""},  # Invalid empty name
    )

    assert response.status_code == 422
    error_data = response.json()
    assert "detail" in error_data
    assert any("name" in str(error) for error in error_data["detail"])
```

### API Pagination Testing

```python
@pytest.mark.asyncio
async def test_list_hash_lists_pagination(authenticated_user_client, db_session):
    project = await ProjectFactory.create_async()

    # Create multiple hash lists
    for i in range(25):
        await HashListFactory.create_async(name=f"hashlist-{i}", project_id=project.id)

    # Test first page
    response = await authenticated_user_client.get(
        "/api/v1/web/hash-lists/?page=1&size=10"
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 10
    assert data["total_count"] == 25
    assert data["page"] == 1
    assert data["total_pages"] == 3
```

### API Coverage Requirements

Test all endpoints for:

- **Success cases**: Valid input, expected output
- **Validation errors**: 422 status with field-specific errors
- **Authentication failures**: 401/403 status codes
- **Not found errors**: 404 status for missing resources
- **Pagination**: `page`, `size` parameters work correctly
- **Filtering**: Query parameters filter results correctly

## Authentication Testing

### Project Association Setup

Always create project associations for scoped endpoints:

```python
@pytest.fixture
async def user_with_project_access(db_session):
    user = await UserFactory.create_async()
    project = await ProjectFactory.create_async()

    # Create project association
    association = ProjectUserAssociation(
        user_id=user.id, project_id=project.id, role=ProjectUserRole.MEMBER
    )
    db_session.add(association)
    await db_session.commit()

    return user, project
```

### Authentication Test Patterns

```python
@pytest.mark.asyncio
async def test_endpoint_requires_authentication(client):
    response = await client.get("/api/v1/web/campaigns/")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_endpoint_requires_project_access(authenticated_user_client):
    # User without project access
    response = await authenticated_user_client.get("/api/v1/web/campaigns/")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_endpoint_with_valid_project_access(
    authenticated_user_client, db_session
):
    user = authenticated_user_client.user
    project = await ProjectFactory.create_async()

    # Grant access
    association = ProjectUserAssociation(
        user_id=user.id, project_id=project.id, role=ProjectUserRole.MEMBER
    )
    db_session.add(association)
    await db_session.commit()

    response = await authenticated_user_client.get(
        f"/api/v1/web/projects/{project.id}/campaigns/"
    )
    assert response.status_code == 200
```

### Role-Based Access Testing

```python
@pytest.mark.asyncio
async def test_admin_only_endpoint_access(db_session):
    # Test member access (should fail)
    member_client = await create_authenticated_client(role=ProjectUserRole.MEMBER)
    response = await member_client.delete("/api/v1/web/projects/1/")
    assert response.status_code == 403

    # Test admin access (should succeed)
    admin_client = await create_authenticated_client(role=ProjectUserRole.ADMIN)
    response = await admin_client.delete("/api/v1/web/projects/1/")
    assert response.status_code == 204
```

## Database Session Management

### Async Session Patterns

```python
@pytest.mark.asyncio
async def test_service_with_proper_session_handling(db_session):
    # Service functions accept AsyncSession as first parameter
    result = await create_resource_service(db_session, resource_data)

    # Session is managed by the test fixture
    # No need to commit/rollback in individual tests
    assert result.id is not None
```

### Transaction Testing

```python
@pytest.mark.asyncio
async def test_service_transaction_rollback_on_error(db_session):
    project = await ProjectFactory.create_async()

    # This should fail and rollback
    with pytest.raises(ValueError):
        await create_invalid_resource_service(db_session, invalid_data)

    # Verify rollback occurred
    count = await db_session.scalar(select(func.count(Resource.id)))
    assert count == 0  # No resources were created
```

## Pydantic v2 Testing Patterns

### Required Idioms

- `model_dump()` instead of `.dict()`
- `model_validate()` instead of `.parse_obj()`
- `ConfigDict(from_attributes=True)` instead of `orm_mode = True`

### Schema Validation Testing

```python
def test_schema_validation():
    # Input validation
    data = HashListCreate.model_validate(
        {"name": "test", "project_id": 1, "hash_type_id": 0}
    )

    # Output serialization
    output = data.model_dump(mode="json")

    # Round-trip testing
    assert HashListCreate.model_validate(output) == data


def test_schema_validation_error():
    with pytest.raises(ValidationError) as exc_info:
        HashListCreate.model_validate(
            {
                "name": "",  # Invalid empty name
                "project_id": "invalid",  # Invalid type
            }
        )

    errors = exc_info.value.errors()
    assert len(errors) == 2
    assert any(error["loc"] == ("name",) for error in errors)
    assert any(error["loc"] == ("project_id",) for error in errors)
```

### Model Serialization Testing

```python
@pytest.mark.asyncio
async def test_model_to_schema_conversion(db_session):
    hash_list = await HashListFactory.create_async()

    # Convert SQLAlchemy model to Pydantic schema
    schema = HashListOut.model_validate(hash_list)

    # Verify all fields are properly serialized
    assert schema.id == hash_list.id
    assert schema.name == hash_list.name
    assert schema.created_at is not None
```

## SQLAlchemy Testing Patterns

### Query Testing

```python
@pytest.mark.asyncio
async def test_complex_query_service(db_session):
    project = await ProjectFactory.create_async()

    # Create test data
    active_campaigns = []
    for i in range(3):
        campaign = await CampaignFactory.create_async(
            project_id=project.id, state=CampaignState.ACTIVE
        )
        active_campaigns.append(campaign)

    # Create inactive campaign
    await CampaignFactory.create_async(
        project_id=project.id, state=CampaignState.COMPLETED
    )

    # Test the query
    result = await get_active_campaigns_service(db_session, project.id)

    assert len(result) == 3
    assert all(c.state == CampaignState.ACTIVE for c in result)
```

### Relationship Testing

```python
@pytest.mark.asyncio
async def test_model_relationships(db_session):
    project = await ProjectFactory.create_async()
    hash_list = await HashListFactory.create_async(project_id=project.id)
    campaign = await CampaignFactory.create_async(
        project_id=project.id, hash_list_id=hash_list.id
    )

    # Test relationship loading
    loaded_campaign = await db_session.get(
        Campaign,
        campaign.id,
        options=[selectinload(Campaign.hash_list), selectinload(Campaign.project)],
    )

    assert loaded_campaign.hash_list.id == hash_list.id
    assert loaded_campaign.project.id == project.id
```

## Performance Testing

### Query Performance

```python
@pytest.mark.asyncio
async def test_query_performance_with_large_dataset(db_session):
    project = await ProjectFactory.create_async()

    # Create large dataset
    campaigns = []
    for i in range(1000):
        campaign = await CampaignFactory.create_async(project_id=project.id)
        campaigns.append(campaign)

    # Test pagination performance
    start_time = time.time()
    result = await list_campaigns_service(db_session, skip=0, limit=20)
    execution_time = time.time() - start_time

    assert len(result[0]) == 20  # items
    assert result[1] == 1000  # total count
    assert execution_time < 1.0  # Should be fast
```

## Common Anti-Patterns to Avoid

### Factory Anti-Patterns

> [!NOTE]
> For comprehensive factory anti-patterns and best practices, see [testing-factories.md](testing-factories.md).

Key points for backend tests:

- Always use `await FactoryClass.create_async()`
- Set explicit foreign keys: `project_id=project.id`
- Never use random FK values

### Testing Anti-Patterns

```python
# ❌ WRONG - Not testing error paths
async def test_create_campaign_success_only():
    # Only tests happy path
    pass


# ✅ CORRECT - Testing both success and error paths
async def test_create_campaign_success():
    # Test success case
    pass


async def test_create_campaign_validation_error():
    # Test validation errors
    pass


async def test_create_campaign_not_found_error():
    # Test not found errors
    pass
```

### Session Management Anti-Patterns

```python
# ❌ WRONG - Managing sessions in tests
async def test_bad_session_management():
    async with AsyncSession() as session:
        # Don't create sessions in tests
        pass


# ✅ CORRECT - Using fixture-provided sessions
async def test_good_session_management(db_session):
    # Use the provided session
    result = await service_function(db_session, data)
```

## Test Organization

> [!NOTE]
> For complete test organization structure and naming conventions, see [testing-core.md](testing-core.md).

### Backend-Specific Organization

Focus on:

- **Service tests**: Business logic validation
- **API tests**: Endpoint behavior and error handling
- **Authentication tests**: Project access and role validation

## Backend-Specific Anti-Patterns to Avoid

> [!NOTE]
> For general testing anti-patterns, see [testing-core.md](testing-core.md).

### Backend Testing Anti-Patterns

- Using random foreign keys in factories (causes FK violations)
- Mixing unit and integration tests in same files
- Not checking Docker service health before E2E tests
- Managing database sessions manually in tests
- Using sync methods with async sessions
- Not testing authentication and authorization paths
- Hardcoding user IDs or project IDs in tests

## Debugging Backend Tests

### Common Issues and Solutions

**Foreign Key Violations**:

```python
# Problem: Random FK values in factories
# Solution: Set __set_relationships__ = False and explicit FKs

# Problem: Missing pre-seeded data
# Solution: Use hash_type_id = 0 (MD5) which is pre-seeded
```

**Async Session Issues**:

```python
# Problem: Using sync methods with async sessions
# Solution: Always use async/await patterns

# Problem: Session not committed
# Solution: Let fixtures handle session lifecycle
```

**Test Data Isolation**:

```python
# Problem: Tests affecting each other
# Solution: Use unique names with UUID or timestamps

# Problem: Leftover data from previous tests
# Solution: Proper test database reset in fixtures
```
