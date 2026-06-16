"""Seed data for E2E testing against Docker backend.

This script creates minimal, predictable test data for full-stack E2E tests.
Uses Polyfactory for data generation, Pydantic for validation, and service layer for persistence.

IMPORTANT: Ensure database migrations are up-to-date before running this script:
    - From host: `just docker-e2e-migrate`
    - From container: `alembic upgrade head`
"""

import asyncio
import os
import sys
import uuid
from pathlib import Path

# Add app to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.services.agent_service import register_agent_full_service
from app.core.services.campaign_service import create_campaign_service
from app.core.services.hash_list_service import create_hash_list_service
from app.core.services.project_service import create_project_service
from app.core.services.user_service import create_user_service
from app.models.agent import OperatingSystemEnum
from app.models.project import ProjectUserAssociation, ProjectUserRole
from app.models.user import User, UserRole
from app.schemas.campaign import CampaignCreate
from app.schemas.hash_list import HashListCreate
from app.schemas.project import ProjectCreate
from app.schemas.user import UserCreate
from tests.utils.hash_type_utils import get_or_create_hash_type


async def create_e2e_test_users(session: AsyncSession) -> dict[str, str]:
    """Create test users using service layer with known credentials."""
    logger.info("Creating E2E test users...")

    # Create admin user with known credentials
    admin_create = UserCreate(
        email="admin@e2e-test.example",
        name="E2E Admin User",
        password="admin-password-123",  # noqa: S106
    )

    # Create regular user with known credentials
    regular_user_create = UserCreate(
        email="user@e2e-test.example",
        name="E2E Regular User",
        password="user-password-123",  # noqa: S106
    )

    # Persist through service layer (handles validation, hashing, etc.)
    admin_user = await create_user_service(
        db=session,
        user_in=admin_create,
        role=UserRole.ADMIN,
        is_superuser=True,
        is_active=True,
    )
    regular_user = await create_user_service(
        db=session,
        user_in=regular_user_create,
        role=UserRole.ANALYST,
        is_superuser=False,
        is_active=True,
    )

    logger.info(f"Created admin user: {admin_user.id}")
    logger.info(f"Created regular user: {regular_user.id}")

    return {
        "admin_user_id": str(admin_user.id),
        "regular_user_id": str(regular_user.id),
    }


async def create_e2e_test_projects(
    session: AsyncSession, user_ids: dict[str, str]
) -> dict[str, int]:
    """Create test projects with known names and user associations."""
    logger.info("Creating E2E test projects...")

    # Generate factory data, convert to Pydantic, add known values
    project_create_1 = ProjectCreate(
        name="E2E Test Project Alpha",
        description="Primary test project for E2E testing",
        private=False,
    )

    project_create_2 = ProjectCreate(
        name="E2E Test Project Beta",
        description="Secondary test project for multi-project scenarios",
        private=False,
    )

    # Persist through service layer
    project_1 = await create_project_service(data=project_create_1, db=session)
    project_2 = await create_project_service(data=project_create_2, db=session)

    # Import the association model

    # Associate admin user with both projects
    admin_user_id = uuid.UUID(user_ids["admin_user_id"])
    regular_user_id = uuid.UUID(user_ids["regular_user_id"])

    # Admin user gets admin role in both projects
    admin_assoc_1 = ProjectUserAssociation(
        user_id=admin_user_id,
        project_id=project_1.id,
        role=ProjectUserRole.admin,
    )
    admin_assoc_2 = ProjectUserAssociation(
        user_id=admin_user_id,
        project_id=project_2.id,
        role=ProjectUserRole.admin,
    )

    # Regular user gets member role in project Alpha only
    user_assoc_1 = ProjectUserAssociation(
        user_id=regular_user_id,
        project_id=project_1.id,
        role=ProjectUserRole.member,
    )

    session.add_all([admin_assoc_1, admin_assoc_2, user_assoc_1])
    await session.commit()

    logger.info(f"Created project Alpha: {project_1.id}")
    logger.info(f"Created project Beta: {project_2.id}")
    logger.info("Associated admin user with both projects")
    logger.info("Associated regular user with project Alpha")

    return {"project_alpha_id": project_1.id, "project_beta_id": project_2.id}


async def create_e2e_test_hash_lists(
    session: AsyncSession, project_ids: dict[str, int]
) -> dict[str, int]:
    """Create test hash lists with known values."""
    logger.info("Creating E2E test hash lists...")

    # First ensure we have a hash type (MD5)

    hash_type = await get_or_create_hash_type(session, 0, "MD5")

    # Create a test user for the service call
    test_user_data = UserCreate(
        email="hashlist@e2e-test.example",
        name="E2E HashList User",
        password="test-password-123",  # noqa: S106
    )
    test_user = await create_user_service(
        db=session,
        user_in=test_user_data,
        role=UserRole.ANALYST,
        is_superuser=False,
        is_active=True,
    )

    hashlist_create = HashListCreate(
        name="E2E Test Hash List",
        description="Test hash list for E2E testing",
        project_id=project_ids["project_alpha_id"],
        hash_type_id=hash_type.id,
    )

    # Import User model to cast to proper type

    # Cast the UserRead to User (they have compatible attributes)
    test_user_model = User(**test_user.model_dump())
    hashlist = await create_hash_list_service(hashlist_create, session, test_user_model)

    logger.info(f"Created hash list: {hashlist.id}")

    return {"hashlist_alpha_id": hashlist.id}


async def create_e2e_test_campaigns(
    session: AsyncSession, project_ids: dict[str, int], hashlist_ids: dict[str, int]
) -> dict[str, int]:
    """Create test campaigns with known names."""
    logger.info("Creating E2E test campaigns...")

    campaign_create = CampaignCreate(
        name="E2E Test Campaign",
        description="Primary test campaign for E2E testing",
        project_id=project_ids["project_alpha_id"],
        hash_list_id=hashlist_ids["hashlist_alpha_id"],
    )

    campaign = await create_campaign_service(campaign_create, session)

    logger.info(f"Created campaign: {campaign.id}")

    return {"campaign_alpha_id": campaign.id}


async def create_e2e_test_agents(session: AsyncSession) -> dict[str, int]:
    """Create test agents with known configurations."""
    logger.info("Creating E2E test agents...")

    # Use the register_agent_full_service which is the proper way to create agents
    agent, token = await register_agent_full_service(
        host_name="e2e-test-agent",
        operating_system=OperatingSystemEnum.linux,
        client_signature="e2e-test-signature",
        custom_label="E2E Test Agent",
        devices="CPU",
        agent_update_interval=30,
        use_native_hashcat=False,
        db=session,
    )

    logger.info(f"Created agent: {agent.id} with token: {token[:20]}...")

    return {"agent_alpha_id": agent.id}


async def clear_existing_data(session: AsyncSession) -> None:
    """Clear existing data in dependency order."""
    logger.info("Clearing existing E2E test data...")

    # Clear in reverse dependency order using raw SQL for speed
    table_names = [
        "tasks",
        "attacks",
        "campaigns",
        "hash_list_items",
        "hash_items",
        "hash_lists",
        "agent_errors",
        "hashcat_benchmarks",
        "project_agents",
        "agents",
        "project_user_associations",
        "projects",
        "users",
    ]

    for table_name in table_names:
        try:
            await session.execute(
                text(f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE")
            )
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Could not truncate {table_name}: {e}")

    await session.commit()
    logger.info("Cleared existing data successfully")


async def seed_e2e_data() -> None:
    """Main seeding function - easily extensible for additional data."""
    logger.info("🌱 Starting E2E data seeding...")

    # Connect to database using E2E configuration
    if os.getenv("E2E_CONTAINER_MODE") == "true":
        # Running inside Docker container - use container networking
        db_url = "postgresql+psycopg://postgres:postgres@postgres:5432/ouroboros_e2e"
    elif os.getenv("TESTING") == "true":
        # Running from host - use external port
        db_url = "postgresql+psycopg://postgres:postgres@localhost:5433/ouroboros_e2e"
    else:
        # Use default settings
        db_url = str(settings.sqlalchemy_database_uri)

    logger.info(f"Connecting to database: {db_url}")

    engine = create_async_engine(db_url)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    try:
        async with async_session() as session:
            # Clear existing data
            await clear_existing_data(session)

            # Create test data in dependency order
            user_ids = await create_e2e_test_users(session)
            project_ids = await create_e2e_test_projects(session, user_ids)
            hashlist_ids = await create_e2e_test_hash_lists(session, project_ids)
            campaign_ids = await create_e2e_test_campaigns(
                session, project_ids, hashlist_ids
            )
            agent_ids = await create_e2e_test_agents(session)

            await session.commit()
            logger.info("✅ E2E data seeding completed successfully!")

            # Log summary of created data
            logger.info(f"Created users: {len(user_ids)}")
            logger.info(f"Created projects: {len(project_ids)}")
            logger.info(f"Created hash lists: {len(hashlist_ids)}")
            logger.info(f"Created campaigns: {len(campaign_ids)}")
            logger.info(f"Created agents: {len(agent_ids)}")

    except Exception as e:
        logger.error(f"❌ Failed to seed E2E data: {e}")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_e2e_data())
