import asyncio
import os
from logging.config import fileConfig
from typing import Any

from sqlalchemy import engine_from_config, pool
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context  # type: ignore[attr-defined]
from app.models.base import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_url() -> str:
    """Get database URL from environment variable or alembic config."""
    # Check for DATABASE_URL environment variable first (for E2E tests and containers)
    database_url = os.getenv("DATABASE_URL")
    if database_url is not None:
        return database_url

    # Fall back to alembic.ini config
    url = config.get_main_option("sqlalchemy.url")
    if url is None:
        raise ValueError(
            "Database URL not configured. "
            "Set DATABASE_URL environment variable or sqlalchemy.url in alembic.ini"
        )
    return url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    url = get_url()
    if url.startswith("postgresql+psycopg"):
        # Use async engine for async driver
        async def do_run_migrations() -> None:
            connectable = create_async_engine(url, poolclass=pool.NullPool)
            async with connectable.connect() as connection:

                def sync_configure(sync_conn: Any) -> None:  # noqa: ANN401
                    context.configure(
                        connection=sync_conn, target_metadata=target_metadata
                    )

                await connection.run_sync(sync_configure)
                async with connection.begin():
                    await connection.run_sync(lambda _: context.run_migrations())  # type: ignore[reportUnknownLambdaType]
            await connectable.dispose()

        asyncio.run(do_run_migrations())
    else:
        connectable = engine_from_config(
            config.get_section(config.config_ini_section, {}),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )
        with connectable.connect() as connection:
            context.configure(connection=connection, target_metadata=target_metadata)
            with context.begin_transaction():
                context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
