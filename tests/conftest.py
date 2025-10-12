"""Test configuration and fixtures."""

import logging
from collections.abc import AsyncGenerator, Generator
from typing import Any

import bcrypt
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from minio import Minio
from pydantic import PostgresDsn
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from testcontainers.minio import MinioContainer  # type: ignore[import-untyped]
from testcontainers.postgres import PostgresContainer  # type: ignore[import-untyped]

from app.core.auth import create_access_token
from app.core.config import settings
from app.core.deps import get_db
from app.db.config import DatabaseSettings
from app.main import app
from app.models.agent import Agent
from app.models.base import Base
from app.models.project import Project
from app.models.user import User, UserRole
from tests.factories.agent_error_factory import AgentErrorFactory
from tests.factories.agent_factory import AgentFactory
from tests.factories.attack_factory import AttackFactory
from tests.factories.attack_resource_file_factory import AttackResourceFileFactory
from tests.factories.campaign_factory import CampaignFactory
from tests.factories.hash_item_factory import HashItemFactory
from tests.factories.hash_list_factory import HashListFactory
from tests.factories.hash_type_factory import HashTypeFactory
from tests.factories.hash_upload_task_factory import (
    HashUploadTaskFactory,
    UploadErrorEntryFactory,
)
from tests.factories.project_factory import ProjectFactory
from tests.factories.raw_hash_factory import RawHashFactory
from tests.factories.task_factory import TaskFactory
from tests.factories.upload_resource_file_factory import UploadResourceFileFactory
from tests.factories.user_factory import UserFactory


# --- Test DB provisioning ---
# Test DB provisioning
@pytest.fixture(scope="session")
def pg_container_url() -> Generator[str]:
    """Start a Postgres test container and yield a psycopg connection string."""
    with PostgresContainer("postgres:16", driver="psycopg") as postgres:
        url = postgres.get_connection_url()
        yield url


@pytest.fixture
def sync_db_url(pg_container_url: str) -> str:
    return pg_container_url


@pytest.fixture
def db_url(pg_container_url: str) -> str:
    return pg_container_url


@pytest_asyncio.fixture(scope="function")
async def async_engine(db_url: str) -> AsyncGenerator[AsyncEngine]:
    engine = create_async_engine(db_url, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(async_engine: Any) -> AsyncGenerator[AsyncSession, Any]:
    async_session = async_sessionmaker(
        async_engine, expire_on_commit=False, class_=AsyncSession
    )
    async with async_session() as session:
        # Set Polyfactory async session for all factories
        from tests.factories.agent_error_factory import AgentErrorFactory
        from tests.factories.agent_factory import AgentFactory
        from tests.factories.attack_factory import AttackFactory
        from tests.factories.campaign_factory import CampaignFactory
        from tests.factories.hash_item_factory import HashItemFactory
        from tests.factories.hash_list_factory import HashListFactory
        from tests.factories.project_factory import ProjectFactory
        from tests.factories.task_factory import TaskFactory
        from tests.factories.upload_resource_file_factory import (
            UploadResourceFileFactory,
        )
        from tests.factories.user_factory import UserFactory

        AgentFactory.__async_session__ = session  # type: ignore[assignment, unused-ignore]
        AgentErrorFactory.__async_session__ = session  # type: ignore[assignment, unused-ignore]
        AttackFactory.__async_session__ = session  # type: ignore[assignment, unused-ignore]
        CampaignFactory.__async_session__ = session  # type: ignore[assignment, unused-ignore]
        ProjectFactory.__async_session__ = session  # type: ignore[assignment, unused-ignore]
        TaskFactory.__async_session__ = session  # type: ignore[assignment, unused-ignore]
        UserFactory.__async_session__ = session  # type: ignore[assignment, unused-ignore]
        ProjectFactory.__async_session__ = session  # type: ignore[assignment, unused-ignore]
        HashListFactory.__async_session__ = session  # type: ignore[assignment, unused-ignore]
        HashItemFactory.__async_session__ = session  # type: ignore[assignment, unused-ignore]
        AttackResourceFileFactory.__async_session__ = session  # type: ignore[assignment, unused-ignore]
        UploadResourceFileFactory.__async_session__ = session  # type: ignore[assignment, unused-ignore]
        HashUploadTaskFactory.__async_session__ = session  # type: ignore[assignment, unused-ignore]
        UploadErrorEntryFactory.__async_session__ = session  # type: ignore[assignment, unused-ignore]
        HashTypeFactory.__async_session__ = session  # type: ignore[assignment, unused-ignore]
        RawHashFactory.__async_session__ = session  # type: ignore[assignment, unused-ignore]

        yield session


@pytest_asyncio.fixture(autouse=True)
async def reset_db_and_seed_hash_types(db_session: AsyncSession) -> None:
    # Truncate all tables
    for table in reversed(Base.metadata.sorted_tables):
        await db_session.execute(table.delete())

    # Seed hash types from JSON file (limit to first 50 for test performance)
    from app.core.services.hash_type_service import HashTypeService

    await HashTypeService.seed_hash_types_from_json(db_session, limit=50)


@pytest.fixture
def db_settings(db_url: str) -> DatabaseSettings:
    """Fixture for DatabaseSettings using the test database URL."""
    return DatabaseSettings(url=PostgresDsn(db_url))


@pytest_asyncio.fixture
async def async_client(
    db_session: AsyncSession, db_settings: DatabaseSettings
) -> AsyncGenerator[AsyncClient]:
    # Initialize the database session manager for the test environment
    from app.db.session import sessionmanager

    sessionmanager.init(db_settings)

    async def override_get_db() -> AsyncGenerator[AsyncSession]:
        # Always yield the current db_session to ensure we see the latest data
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()
    await sessionmanager.close()


# --- Polyfactory setup ---
# Polyfactory setup
@pytest.fixture
def user_factory() -> UserFactory:
    return UserFactory()


@pytest.fixture
def agent_factory() -> AgentFactory:
    return AgentFactory()


@pytest.fixture
def agent_error_factory() -> AgentErrorFactory:
    return AgentErrorFactory()


@pytest.fixture
def attack_factory() -> AttackFactory:
    return AttackFactory()


@pytest.fixture
def task_factory() -> TaskFactory:
    return TaskFactory()


@pytest.fixture
def project_factory() -> ProjectFactory:
    return ProjectFactory()


@pytest.fixture
def campaign_factory() -> CampaignFactory:
    return CampaignFactory()


@pytest.fixture
def hash_list_factory() -> HashListFactory:
    return HashListFactory()


@pytest.fixture
def hash_item_factory() -> HashItemFactory:
    return HashItemFactory()


@pytest.fixture
def hash_type_factory() -> HashTypeFactory:
    return HashTypeFactory()


@pytest.fixture
def upload_resource_file_factory() -> UploadResourceFileFactory:
    return UploadResourceFileFactory()


@pytest.fixture
def hash_upload_task_factory() -> HashUploadTaskFactory:
    return HashUploadTaskFactory()


@pytest.fixture
def upload_error_entry_factory() -> UploadErrorEntryFactory:
    return UploadErrorEntryFactory()


@pytest.fixture
def raw_hash_factory() -> RawHashFactory:
    return RawHashFactory()


# --- Test data seeding ---
@pytest_asyncio.fixture
async def seed_minimal_project(
    db_session: AsyncSession, project_factory: ProjectFactory
) -> Project:
    project: Project = project_factory.build()
    db_session.add(project)
    await db_session.commit()
    return project


@pytest_asyncio.fixture
async def seed_minimal_agent(
    db_session: AsyncSession, agent_factory: AgentFactory
) -> Agent:
    agent: Agent = agent_factory.build()
    db_session.add(agent)
    await db_session.commit()
    return agent


@pytest.fixture
def attack_resource_file_factory() -> AttackResourceFileFactory:
    return AttackResourceFileFactory()


class PropagateHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        logging.getLogger(record.name).handle(record)


@pytest_asyncio.fixture
async def authenticated_async_client(
    async_client: AsyncClient, db_session: AsyncSession
) -> AsyncGenerator[AsyncClient]:
    """Yield an authenticated async_client with a valid user session for most tests."""
    user = await UserFactory.create_async()
    user.hashed_password = bcrypt.hashpw(b"password", bcrypt.gensalt()).decode()
    db_session.add(user)
    await db_session.commit()
    token = create_access_token(user.id)
    async_client.cookies.set("access_token", token)
    yield async_client


@pytest_asyncio.fixture
async def authenticated_user_client(
    async_client: AsyncClient, db_session: AsyncSession
) -> AsyncGenerator[tuple[AsyncClient, User]]:
    """Yield (async_client, user) for tests that need the user object for project membership, etc."""
    user = await UserFactory.create_async()
    user.hashed_password = bcrypt.hashpw(b"password", bcrypt.gensalt()).decode()
    db_session.add(user)
    await db_session.commit()
    token = create_access_token(user.id)
    async_client.cookies.set("access_token", token)
    yield async_client, user


@pytest_asyncio.fixture
async def authenticated_admin_client(
    async_client: AsyncClient, db_session: AsyncSession
) -> AsyncGenerator[AsyncClient]:
    """Yield an authenticated async_client with a valid admin user session for admin-only tests."""
    user = await UserFactory.create_async(role=UserRole.ADMIN, is_superuser=True)
    user.hashed_password = bcrypt.hashpw(b"password", bcrypt.gensalt()).decode()
    db_session.add(user)
    await db_session.commit()
    token = create_access_token(user.id)
    async_client.cookies.set("access_token", token)
    yield async_client


@pytest_asyncio.fixture
async def api_key_client(
    async_client: AsyncClient, db_session: AsyncSession
) -> AsyncGenerator[tuple[AsyncClient, User, str]]:
    """
    Create a user with API key and return (client, user, api_key).
    """
    from sqlalchemy import select

    from app.core.services.user_service import create_user_service
    from app.schemas.user import UserCreate

    # Create user using the service to ensure API key is generated
    user_data = UserCreate(
        email="apitest@example.com", name="API Test User", password="testpassword123"
    )

    user_read = await create_user_service(
        db=db_session, user_in=user_data, role=UserRole.ANALYST
    )

    # Fetch the actual user from database to get API key
    result = await db_session.execute(select(User).where(User.id == user_read.id))
    user = result.scalar_one()

    # Ensure API key is not None
    assert user.api_key is not None, "API key should be generated"

    yield async_client, user, user.api_key


# --- MinIO Testcontainer ---
@pytest.fixture(scope="session")
def minio_container() -> Generator[MinioContainer]:
    """Start a Minio test container and yield the container instance."""
    with MinioContainer("minio/minio:latest") as minio:
        config = minio.get_config()
        endpoint_url = config["endpoint"]
        access_key = config["access_key"]
        secret_key = config["secret_key"]
        from app.core import config as core_config

        # Patch settings for the test session
        core_config.settings.MINIO_ENDPOINT = endpoint_url
        core_config.settings.MINIO_ACCESS_KEY = access_key
        core_config.settings.MINIO_SECRET_KEY = secret_key
        # Use a test bucket name to avoid collisions
        core_config.settings.MINIO_BUCKET = "ouroboros-test-resources"

        client = minio.get_client()
        # Create all required buckets
        required_buckets = [
            core_config.settings.MINIO_BUCKET,
            "resources",
        ]
        for bucket in required_buckets:
            if not client.bucket_exists(bucket):
                client.make_bucket(bucket)
        yield minio


@pytest.fixture(scope="session")
def minio_client(minio_container: MinioContainer) -> Minio:
    return minio_container.get_client()  # type: ignore[no-any-return]


@pytest.fixture(autouse=True, scope="session")
def fast_resource_upload_timeout() -> None:
    settings.RESOURCE_UPLOAD_TIMEOUT_SECONDS = 2
