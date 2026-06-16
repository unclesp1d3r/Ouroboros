"""Database session management module."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any

from loguru import logger
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

if TYPE_CHECKING:
    from app.core.config import Settings


class DatabaseSessionManager:
    """Manages database sessions and engine lifecycle.

    This class is responsible for:
    - Creating and managing the database engine
    - Providing session factories
    - Managing connection pools
    - Handling cleanup
    """

    def __init__(self) -> None:
        """Initialize the session manager."""
        self._engine: AsyncEngine | None = None
        self._sessionmaker: async_sessionmaker[AsyncSession] | None = None

    def init(self, settings: Settings) -> None:
        """Initialize the database engine and session maker.

        Args:
            settings: Application settings containing database configuration
        """
        db_url = str(settings.sqlalchemy_database_uri)

        # Base engine arguments
        engine_args: dict[str, Any] = {"echo": settings.DB_ECHO}

        # Only add pooling arguments for non-SQLite databases
        if not db_url.startswith("sqlite"):
            engine_args.update(
                {
                    "pool_size": settings.DB_POOL_SIZE,
                    "max_overflow": settings.DB_MAX_OVERFLOW,
                    "pool_timeout": settings.DB_POOL_TIMEOUT,
                    "pool_recycle": settings.DB_POOL_RECYCLE,
                }
            )

        self._engine = create_async_engine(db_url, **engine_args)
        self._sessionmaker = async_sessionmaker(
            autocommit=False, autoflush=False, expire_on_commit=False, bind=self._engine
        )

    async def close(self) -> None:
        """Close all connections in the pool."""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._sessionmaker = None

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession]:
        """Get a database session.

        Yields:
            AsyncSession: Database session

        Raises:
            RuntimeError: If session manager is not initialized
        """
        if not self._sessionmaker:
            raise RuntimeError("DatabaseSessionManager is not initialized")

        session = self._sessionmaker()
        try:
            yield session
            await session.commit()
        except Exception as e:
            logger.error(
                f"Database operation failed, rolling back: {type(e).__name__}: {e}"
            )
            await session.rollback()
            raise
        finally:
            await session.close()

    @property
    def engine(self) -> AsyncEngine:
        """Get the database engine.

        Returns:
            AsyncEngine: The database engine

        Raises:
            RuntimeError: If session manager is not initialized
        """
        if not self._engine:
            raise RuntimeError("DatabaseSessionManager is not initialized")
        return self._engine


# Global instance of the session manager
sessionmanager = DatabaseSessionManager()


async def get_session() -> AsyncGenerator[AsyncSession]:
    """FastAPI dependency for database sessions.

    Yields:
        AsyncSession: Database session
    """
    async with sessionmanager.session() as session:
        yield session


# Alias for FastAPI DB dependency
get_db = get_session
