---
inclusion: fileMatch
fileMatchPattern:

  - tests/factories/\*\*/\*.py
  - scripts/seed\_\*.py
---

# Ouroboros Factory Testing Patterns

## Polyfactory Usage Patterns

### Factory Base Configuration

```python
from polyfactory import Use
from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory


class HashListFactory(SQLAlchemyFactory[HashList]):
    __model__ = HashList
    __set_relationships__ = False  # Prevents FK violations
    __async_session__ = None

    name = Use(lambda: "hashlist-factory")
    project_id = None  # Must be set explicitly
    hash_type_id = 0  # MD5 - pre-seeded data
```

**Critical Rules**:

- Use `create_async()` only, never `.build()` or sync methods
- Set `__set_relationships__ = False` to prevent FK violations
- Use pre-seeded data for stable foreign keys
- Explicitly set dynamic foreign keys in tests

### Factory Naming Conventions

- **Factory files**: `{model_name}_factory.py`
- **Factory classes**: `{ModelName}Factory`
- **Location**: `tests/factories/`
- **Import pattern**: `from tests.factories.{model}_factory import {Model}Factory`

## Async Factory Creation

### Standard Async Factory Pattern

```python
@pytest.mark.asyncio
async def test_create_hash_list_service(db_session):
    project = await ProjectFactory.create_async()
    data = HashListCreate(name="test", project_id=project.id)

    result = await create_hash_list_service(db_session, data)

    assert result.name == "test"
    # Verify persistence
    saved = await get_hash_list_service(db_session, result.id)
    assert saved.name == "test"
```

### Session Management

```python
# ✅ CORRECT - Set session before using factories
async def test_with_factories(db_session):
    # Set session for all factories
    UserFactory.__async_session__ = db_session
    ProjectFactory.__async_session__ = db_session

    user = await UserFactory.create_async()
    project = await ProjectFactory.create_async()
```

### Factory Method Extensions

```python
class HashListFactory(SQLAlchemyFactory[HashList]):
    # ... base configuration ...

    @classmethod
    async def create_async_with_hash_type(
        cls,
        hash_type_id: int = 0,
        **kwargs: Any,
    ) -> HashList:
        """Create a hash list ensuring the hash type exists."""
        from tests.utils.hash_type_utils import get_or_create_hash_type

        if cls.__async_session__ is None:
            raise ValueError("__async_session__ must be set")

        session = cls.__async_session__
        await get_or_create_hash_type(session, hash_type_id)

        kwargs["hash_type_id"] = hash_type_id
        return await cls.create_async(**kwargs)
```

## Foreign Key Handling

### Preventing FK Violations

```python
# ✅ CORRECT - Explicit FK management
class CampaignFactory(SQLAlchemyFactory[Campaign]):
    __model__ = Campaign
    __set_relationships__ = False  # Critical for FK safety

    # Required FKs must be set explicitly
    project_id = None  # Set in test
    hash_list_id = None  # Set in test
    created_by = None  # Set in test

    # Optional FKs can have safe defaults
    hash_type_id = 0  # MD5 - always exists
```

### FK Relationship Patterns

```python
@pytest.mark.asyncio
async def test_campaign_creation(db_session):
    # Arrange - Create test data with proper FK relationships
    user = await UserFactory.create_async()
    project = await ProjectFactory.create_async()
    hash_list = await HashListFactory.create_async(project_id=project.id)

    # Create required associations
    association = ProjectUserAssociation(
        user_id=user.id, project_id=project.id, role=ProjectUserRole.MEMBER
    )
    db_session.add(association)
    await db_session.commit()

    # Act - Create campaign with all required FKs
    campaign = await CampaignFactory.create_async(
        name="Test Campaign",
        project_id=project.id,
        hash_list_id=hash_list.id,
        created_by=user.id,
    )

    # Assert
    assert campaign.project_id == project.id
    assert campaign.hash_list_id == hash_list.id
    assert campaign.created_by == user.id
```

### Pre-seeded Data References

```python
# ✅ CORRECT - Use pre-seeded data for stable references
class HashListFactory(SQLAlchemyFactory[HashList]):
    hash_type_id = 0  # MD5 - always exists in pre-seeded data


class AttackFactory(SQLAlchemyFactory[Attack]):
    attack_mode = 0  # Dictionary attack - stable reference


# ❌ WRONG - Random FKs cause violations
class BadFactory(SQLAlchemyFactory[SomeModel]):
    foreign_key_id = Use(lambda: random.randint(1, 1000))  # Will fail
```

## Test Data Seeding

### E2E Data Seeding Pattern

```python
async def create_e2e_test_users(session: AsyncSession) -> dict[str, str]:
    """Create test users using service layer with known credentials."""
    logger.info("Creating E2E test users...")

    # Create admin user with known credentials
    admin_create = UserCreate(
        email="admin@e2e-test.example",
        name="E2E Admin User",
        password="admin-password-123",
    )

    admin_user = await create_user_service(session, admin_create)
    admin_user.role = UserRole.ADMIN
    admin_user.is_superuser = True
    await session.commit()

    return {"admin_id": str(admin_user.id)}
```

### Seeding Script Structure

```python
async def seed_e2e_data():
    """Main seeding function with proper error handling."""
    try:
        # Database connection
        engine = create_async_engine(settings.database_url)
        async_session = async_sessionmaker(engine, expire_on_commit=False)

        async with async_session() as session:
            # Clear existing data
            await cleanup_test_data(session)

            # Create test data in dependency order
            users = await create_e2e_test_users(session)
            projects = await create_e2e_test_projects(session, users)
            campaigns = await create_e2e_test_campaigns(session, projects)

            logger.info("E2E test data seeded successfully")

    except Exception as e:
        logger.error(f"Seeding failed: {e}")
        await cleanup_test_data(session)
        raise
```

### Deterministic Test Data

```python
# ✅ CORRECT - Deterministic data for reliable tests
class UserFactory(SQLAlchemyFactory[User]):
    _name_counter = 0
    _email_counter = 0

    @classmethod
    def name(cls) -> str:
        cls._name_counter += 1
        return f"user-{cls.__faker__.uuid4()}-{cls._name_counter}"

    @classmethod
    def email(cls) -> str:
        cls._email_counter += 1
        return f"user{cls._email_counter}-{cls.__faker__.uuid4()}@example.com"

    # Always use consistent password hash
    hashed_password = bcrypt.hash("password")
```

## Cleanup Strategies

### Automatic Cleanup with Fixtures

```python
@pytest.fixture
async def db_session():
    """Provide clean database session for each test."""
    async with async_session() as session:
        # Set session for all factories
        UserFactory.__async_session__ = session
        ProjectFactory.__async_session__ = session
        HashListFactory.__async_session__ = session

        yield session

        # Cleanup handled by transaction rollback
        await session.rollback()
```

### Manual Cleanup for E2E Tests

```python
async def cleanup_test_data(session: AsyncSession):
    """Clean up test data in reverse dependency order."""
    try:
        # Delete in reverse dependency order
        await session.execute(text("DELETE FROM crack_results"))
        await session.execute(text("DELETE FROM tasks"))
        await session.execute(text("DELETE FROM attacks"))
        await session.execute(text("DELETE FROM campaigns"))
        await session.execute(text("DELETE FROM hash_items"))
        await session.execute(text("DELETE FROM hash_lists"))
        await session.execute(text("DELETE FROM project_user_associations"))
        await session.execute(text("DELETE FROM projects"))
        await session.execute(text("DELETE FROM users WHERE email LIKE '%e2e-test%'"))

        await session.commit()
        logger.info("Test data cleanup completed")

    except Exception as e:
        logger.warning(f"Cleanup failed: {e}")
        await session.rollback()
```

### Graceful Error Handling

```python
async def seed_with_cleanup():
    """Seed data with automatic cleanup on failure."""
    session = None
    try:
        session = await get_session()
        await create_test_data(session)

    except Exception as e:
        logger.error(f"Seeding failed: {e}")
        if session:
            await cleanup_test_data(session)
        raise
    finally:
        if session:
            await session.close()
```

## Factory Organization

### Factory File Structure

```
tests/factories/
├── __init__.py                    # Factory imports
├── user_factory.py               # User model factory
├── project_factory.py            # Project model factory
├── hash_list_factory.py          # Hash list factory
├── campaign_factory.py           # Campaign factory
├── attack_factory.py             # Attack factory
├── task_factory.py               # Task factory
└── agent_factory.py              # Agent factory
```

### Factory Import Patterns

```python
# tests/factories/__init__.py
from .user_factory import UserFactory
from .project_factory import ProjectFactory
from .hash_list_factory import HashListFactory
from .campaign_factory import CampaignFactory

__all__ = [
    "UserFactory",
    "ProjectFactory",
    "HashListFactory",
    "CampaignFactory",
]
```

### Shared Factory Utilities

```python
# tests/utils/factory_utils.py
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession


async def setup_factories(session: AsyncSession, *factory_classes: Any):
    """Set async session for multiple factory classes."""
    for factory_class in factory_classes:
        factory_class.__async_session__ = session


async def create_project_with_user(session: AsyncSession) -> tuple[Project, User]:
    """Create project with associated user - common pattern."""
    user = await UserFactory.create_async()
    project = await ProjectFactory.create_async()

    # Create association
    association = ProjectUserAssociation(
        user_id=user.id, project_id=project.id, role=ProjectUserRole.MEMBER
    )
    session.add(association)
    await session.commit()

    return project, user
```

## Common Anti-Patterns to Avoid

### FK Violation Anti-Patterns

```python
# ❌ WRONG - Random foreign keys cause FK violations
class BadFactory(SQLAlchemyFactory[Model]):
    foreign_key_id = Use(lambda: random.randint(1, 1000))


# ❌ WRONG - Auto-relationships create unpredictable data
class BadFactory(SQLAlchemyFactory[Model]):
    __set_relationships__ = True  # Causes FK violations


# ❌ WRONG - Using sync methods in async tests
def test_bad_pattern():
    model = BadFactory.build()  # Don't use build()
    model = BadFactory.create()  # Don't use sync create()
```

### Session Management Anti-Patterns

```python
# ❌ WRONG - Not setting async session
async def test_bad_session():
    # This will fail - no session set
    user = await UserFactory.create_async()


# ❌ WRONG - Mixing sync and async patterns
def test_mixed_patterns(db_session):
    user = UserFactory.create()  # Sync method in async test
    project = await ProjectFactory.create_async()  # Mixed patterns
```

### Test Data Anti-Patterns

```python
# ❌ WRONG - Hardcoded test data instead of factories
async def test_hardcoded_data(db_session):
    user = User(
        name="Test User",
        email="test@example.com",
        hashed_password="plaintext",  # Security issue
    )
    db_session.add(user)


# ❌ WRONG - Non-deterministic test data
class BadFactory(SQLAlchemyFactory[User]):
    name = Use(lambda: random.choice(["Alice", "Bob"]))  # Flaky tests
```

## Performance Considerations

### Factory Performance Tips

- Use `create_async()` only when persistence is needed
- Reuse factories across test files to reduce setup overhead
- Set up factory sessions once per test, not per factory call
- Use pre-seeded data references to avoid creating unnecessary records

### Batch Creation Patterns

```python
# ✅ CORRECT - Batch creation for performance
async def create_multiple_hash_lists(session: AsyncSession, count: int):
    """Create multiple hash lists efficiently."""
    project = await ProjectFactory.create_async()

    hash_lists = []
    for i in range(count):
        hash_list = await HashListFactory.create_async(
            name=f"Hash List {i}", project_id=project.id
        )
        hash_lists.append(hash_list)

    return hash_lists
```

## Testing Factory Implementations

### Factory Unit Tests

```python
@pytest.mark.asyncio
async def test_hash_list_factory_creates_valid_model(db_session):
    """Test that factory creates valid model instances."""
    HashListFactory.__async_session__ = db_session
    project = await ProjectFactory.create_async()

    hash_list = await HashListFactory.create_async(project_id=project.id)

    assert hash_list.id is not None
    assert hash_list.name == "hashlist-factory"
    assert hash_list.project_id == project.id
    assert hash_list.hash_type_id == 0


@pytest.mark.asyncio
async def test_factory_prevents_fk_violations(db_session):
    """Test that factory configuration prevents FK violations."""
    HashListFactory.__async_session__ = db_session

    # This should not create related models automatically
    hash_list = await HashListFactory.create_async(
        project_id=999999  # Non-existent project
    )

    # Should fail due to FK constraint
    with pytest.raises(IntegrityError):
        await db_session.commit()
```

## Integration with Service Layer

### Service Testing with Factories

```python
@pytest.mark.asyncio
async def test_create_campaign_service(db_session):
    """Test service layer with factory-generated data."""
    # Arrange
    user = await UserFactory.create_async()
    project = await ProjectFactory.create_async()
    hash_list = await HashListFactory.create_async(project_id=project.id)

    # Create project association
    association = ProjectUserAssociation(
        user_id=user.id, project_id=project.id, role=ProjectUserRole.MEMBER
    )
    db_session.add(association)
    await db_session.commit()

    # Act
    campaign_data = CampaignCreate(
        name="Test Campaign", description="Test description", hash_list_id=hash_list.id
    )

    result = await create_campaign_service(
        db_session, campaign_data, project.id, user.id
    )

    # Assert
    assert result.name == "Test Campaign"
    assert result.hash_list_id == hash_list.id
    assert result.created_by == user.id
```

## Documentation and Maintenance

### Factory Documentation

```python
class HashListFactory(SQLAlchemyFactory[HashList]):
    """Factory for creating HashList test instances.

    Usage:
        # Set session first
        HashListFactory.__async_session__ = db_session

        # Create with explicit project
        project = await ProjectFactory.create_async()
        hash_list = await HashListFactory.create_async(project_id=project.id)

    Notes:
        - Always set project_id explicitly
        - Uses MD5 (hash_type_id=0) by default
        - Prevents automatic relationship creation
    """
```

### Factory Maintenance Checklist

- [ ] Factory follows naming conventions
- [ ] `__set_relationships__ = False` is set
- [ ] Required FKs are set to `None` with comments
- [ ] Pre-seeded data is used for stable references
- [ ] Factory has proper docstring with usage examples
- [ ] Factory is tested with unit tests
- [ ] Factory is imported in `__init__.py`
- [ ] Factory handles async session correctly
