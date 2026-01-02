# pyright: reportGeneralTypeIssues=false
# type: ignore[assignment]

from faker import Faker
from polyfactory import Use
from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory

from app.models.agent_error import AgentError, Severity

fake = Faker()


class AgentErrorFactory(SQLAlchemyFactory[AgentError]):
    __model__ = AgentError
    __async_session__ = None
    __check_model__ = False
    __set_relationships__ = False
    __set_association_proxy__ = False

    message = Use(lambda: fake.sentence())
    severity = Severity.minor
    agent_id = None  # Must be set explicitly in tests
    task_id = None  # Must be set in test if needed
    # FK fields (agent_id, task_id) must be set explicitly in tests.


# Don't try to override build or create_async methods
