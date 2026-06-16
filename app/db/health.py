"""Database health check module."""

from loguru import logger
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def check_database_health(session: AsyncSession) -> tuple[bool, str]:
    """Check database connectivity and basic operations.

    This function performs a basic health check by:
    1. Testing database connectivity
    2. Executing a simple query
    3. Verifying transaction functionality

    Args:
        session: The database session to use for health checks

    Returns:
        Tuple[bool, str]: A tuple containing:
            - bool: True if all checks pass, False otherwise
            - str: A message describing the health check result
    """
    try:
        # Test basic query execution
        logger.debug("Executing basic query")
        result = await session.execute(text("SELECT 1"))
        value = result.scalar_one()
        logger.debug(f"Basic query result: {value}")
        if value != 1:
            return False, "Database query returned unexpected value"

        # Test transaction functionality only if not already in a transaction
        logger.debug("Testing transaction functionality")
        if not session.in_transaction():
            async with session.begin():
                result = await session.execute(text("SELECT 1"))
                value = result.scalar_one()
                logger.debug(f"Transaction query result: {value}")
                if value != 1:
                    return False, "Database transaction query returned unexpected value"
        else:
            # If already in transaction, just execute the query
            result = await session.execute(text("SELECT 1"))
            value = result.scalar_one()
            logger.debug(f"Transaction query result: {value}")
            if value != 1:
                return False, "Database transaction query returned unexpected value"
    except Exception:  # noqa: BLE001 - Catch all DB errors for health check
        logger.exception("Health check failed")
        return False, "Database health check failed"
    else:
        return True, "Database is healthy"
