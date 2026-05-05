# type: ignore[assignment]

from faker import Faker
from polyfactory import Use
from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory

from app.models.project import Project

fake = Faker()


class ProjectFactory(SQLAlchemyFactory[Project]):
    __model__ = Project
    __async_session__ = None
    __check_model__ = False
    __set_relationships__ = False
    __set_association_proxy__ = False
    _name_counter = 0

    @classmethod
    def name(cls) -> str:
        cls._name_counter += 1
        return f"project-{cls.__faker__.uuid4()}-{cls._name_counter}"

    # name must be unique per test run
    description = Use(fake.unique.sentence)
    # No FKs; pure factory.
    # users can be set as a relation in tests
    # created_at, updated_at handled by DB
    # No build method needed; use create_async for persistence

    private = False
    archived_at = None  # Projects should not be archived by default
    id = None  # Must be set explicitly in tests if needed


# Don't try to override build or create_async methods
