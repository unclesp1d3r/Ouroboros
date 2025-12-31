import asyncio
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

import redis.asyncio as aioredis
from cashews import cache
from loguru import logger
from minio.error import S3Error
from sqlalchemy import func, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.services.storage_service import StorageService, get_storage_service
from app.db.health import check_database_health
from app.models.agent import Agent
from app.models.campaign import Campaign
from app.models.hash_list import HashList
from app.models.task import Task
from app.models.user import User
from app.schemas.health import (
    AgentHealthSummary,
    MinioHealth,
    MinioHealthDetailed,
    PostgresHealth,
    PostgresHealthDetailed,
    RedisHealth,
    RedisHealthDetailed,
    SystemHealthComponents,
    SystemHealthOverview,
)


def _is_admin(user: User) -> bool:
    """Check if user has admin privileges"""
    return (
        getattr(user, "is_superuser", False) or getattr(user, "role", None) == "admin"
    )


async def _get_detailed_minio_health(
    get_storage_service_fn: Callable[[], StorageService],
    basic_health: MinioHealth,
) -> MinioHealthDetailed:
    """Get detailed MinIO health information for admin users"""
    object_count = None
    storage_usage = None

    if basic_health.status == "healthy":
        try:
            storage = get_storage_service_fn()

            # Count objects and calculate storage usage across all buckets
            total_objects = 0
            total_size = 0

            buckets = await asyncio.to_thread(storage.client.list_buckets)
            for bucket in buckets:
                objects = await asyncio.to_thread(
                    storage.client.list_objects, bucket.name, recursive=True
                )
                for obj in objects:
                    total_objects += 1
                    total_size += obj.size or 0

            object_count = total_objects
            storage_usage = total_size

        except (RuntimeError, ConnectionError, S3Error) as e:
            logger.warning(f"Failed to get detailed MinIO metrics: {e}")

    return MinioHealthDetailed(
        status=basic_health.status,
        latency=basic_health.latency,
        error=basic_health.error,
        bucket_count=basic_health.bucket_count,
        object_count=object_count,
        storage_usage=storage_usage,
    )


async def _get_detailed_redis_health(basic_health: RedisHealth) -> RedisHealthDetailed:
    """Get detailed Redis health information for admin users"""
    keyspace_keys = None
    evicted_keys = None
    expired_keys = None
    max_memory = None

    if basic_health.status == "healthy":
        try:
            redis = aioredis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                decode_responses=True,
            )

            # Get detailed info
            info = await redis.info()
            keyspace_info = await redis.info("keyspace")

            # Calculate total keys across all databases
            total_keys = 0
            for key, value in keyspace_info.items():
                if key.startswith("db"):
                    # Redis keyspace info returns a dict with keys like 'keys', 'expires', 'avg_ttl'
                    if isinstance(value, dict) and "keys" in value:
                        total_keys += int(value["keys"])
                    elif isinstance(value, str):
                        # Fallback for string format "keys=X,expires=Y,avg_ttl=Z"
                        keys_part = value.split(",")[0]
                        if "=" in keys_part:
                            total_keys += int(keys_part.split("=")[1])

            keyspace_keys = total_keys
            evicted_keys = info.get("evicted_keys")
            expired_keys = info.get("expired_keys")
            max_memory = info.get("maxmemory")

            await redis.aclose()

        except (RuntimeError, ConnectionError, aioredis.RedisError) as e:
            logger.warning(f"Failed to get detailed Redis metrics: {e}")

    return RedisHealthDetailed(
        status=basic_health.status,
        latency=basic_health.latency,
        error=basic_health.error,
        memory_usage=basic_health.memory_usage,
        active_connections=basic_health.active_connections,
        keyspace_keys=keyspace_keys,
        evicted_keys=evicted_keys,
        expired_keys=expired_keys,
        max_memory=max_memory,
    )


async def _get_detailed_postgres_health(
    db: AsyncSession, basic_health: PostgresHealth
) -> PostgresHealthDetailed:
    """Get detailed PostgreSQL health information for admin users"""
    active_connections = None
    max_connections = None
    long_running_queries = None
    database_size = None

    if basic_health.status == "healthy":
        try:
            # Get connection stats
            result = await db.execute(
                text("SELECT count(*) FROM pg_stat_activity WHERE state = 'active'")
            )
            active_connections = result.scalar()

            # Get max connections setting
            result = await db.execute(text("SHOW max_connections"))
            max_conn_value = result.scalar()
            max_connections = (
                int(max_conn_value) if max_conn_value is not None else None
            )

            # Count long-running queries (>30 seconds)
            result = await db.execute(
                text("""
                    SELECT count(*)
                    FROM pg_stat_activity
                    WHERE state = 'active'
                    AND now() - query_start > interval '30 seconds'
                """)
            )
            long_running_queries = result.scalar()

            # Get database size
            result = await db.execute(
                text("SELECT pg_database_size(current_database())")
            )
            database_size = result.scalar()

        except (RuntimeError, ConnectionError, SQLAlchemyError) as e:
            logger.warning(f"Failed to get detailed PostgreSQL metrics: {e}")

    return PostgresHealthDetailed(
        status=basic_health.status,
        latency=basic_health.latency,
        error=basic_health.error,
        active_connections=active_connections,
        max_connections=max_connections,
        long_running_queries=long_running_queries,
        database_size=database_size,
    )


async def get_system_health_components_service(
    db: AsyncSession,
    current_user: User,
    get_storage_service_fn: Callable[[], StorageService] = get_storage_service,
) -> SystemHealthComponents:
    """Get detailed system health components information"""
    is_admin = _is_admin(current_user)

    # Get basic health information first (this is cached)
    overview = await get_system_health_overview_service(
        db, current_user, get_storage_service_fn
    )

    # For admin users, enhance with detailed information (not cached)
    if is_admin:
        minio_health: (
            MinioHealth | MinioHealthDetailed
        ) = await _get_detailed_minio_health(get_storage_service_fn, overview.minio)
        redis_health: (
            RedisHealth | RedisHealthDetailed
        ) = await _get_detailed_redis_health(overview.redis)
        postgres_health: (
            PostgresHealth | PostgresHealthDetailed
        ) = await _get_detailed_postgres_health(db, overview.postgres)
    else:
        # For non-admin users, return basic health information
        minio_health = overview.minio
        redis_health = overview.redis
        postgres_health = overview.postgres

    return SystemHealthComponents(
        minio=minio_health,
        redis=redis_health,
        postgres=postgres_health,
    )


@cache(ttl="60s", key="system_health_overview")
async def get_system_health_overview_service(
    db: AsyncSession,
    _current_user: User,
    get_storage_service_fn: Callable[[], StorageService] = get_storage_service,
) -> SystemHealthOverview:
    # MinIO health
    minio_status = "unreachable"
    minio_latency = None
    minio_error = None
    minio_bucket_count = None
    try:
        storage = get_storage_service_fn()
        start = datetime.now(UTC)
        buckets = await asyncio.to_thread(storage.client.list_buckets)
        minio_latency = (datetime.now(UTC) - start).total_seconds()
        minio_status = "healthy"
        minio_bucket_count = len(buckets)
    except (RuntimeError, ConnectionError, S3Error) as e:
        minio_error = str(e)
        logger.error(f"MinIO health check failed: {e}")
        minio_status = "unreachable"
    minio = MinioHealth(
        status=minio_status,
        latency=minio_latency,
        error=minio_error,
        bucket_count=minio_bucket_count,
    )
    # Redis health
    redis_status = "unreachable"
    redis_latency = None
    redis_error = None
    redis_memory = None
    redis_connections = None
    try:
        redis = aioredis.Redis(
            host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True
        )
        start = datetime.now(UTC)
        await redis.ping()  # type: ignore[reportGeneralTypeIssues]
        redis_latency = (datetime.now(UTC) - start).total_seconds()
        redis_status = "healthy"
        info = await redis.info()
        redis_memory = info.get("used_memory")
        redis_connections = info.get("connected_clients")
        await redis.aclose()
    except (RuntimeError, ConnectionError, aioredis.RedisError) as e:
        redis_error = str(e)
        logger.error(f"Redis health check failed: {e}")
        redis_status = "unreachable"
    redis_health = RedisHealth(
        status=redis_status,
        latency=redis_latency,
        error=redis_error,
        memory_usage=redis_memory,
        active_connections=redis_connections,
    )
    # Postgres health
    pg_status = "unreachable"
    pg_latency = None
    pg_error = None
    try:
        start = datetime.now(UTC)
        healthy, msg = await check_database_health(db)
        pg_latency = (datetime.now(UTC) - start).total_seconds()
        if healthy:
            pg_status = "healthy"
        else:
            pg_status = "unreachable"
            pg_error = msg
    except (RuntimeError, ConnectionError) as e:
        pg_error = str(e)
        logger.error(f"Postgres health check failed: {e}")
        pg_status = "unreachable"
    postgres = PostgresHealth(
        status=pg_status,
        latency=pg_latency,
        error=pg_error,
    )
    # Agent/campaign/task/hashlist summary
    online_cutoff = datetime.now(UTC) - timedelta(minutes=2)
    total_agents = await db.scalar(select(func.count()).select_from(Agent))
    online_agents = await db.scalar(
        select(func.count())
        .select_from(Agent)
        .where(Agent.last_seen_at >= online_cutoff, Agent.enabled)
    )
    total_campaigns = await db.scalar(select(func.count()).select_from(Campaign))
    total_tasks = await db.scalar(select(func.count()).select_from(Task))
    total_hashlists = await db.scalar(select(func.count()).select_from(HashList))
    agent_summary = AgentHealthSummary(
        total_agents=total_agents or 0,
        online_agents=online_agents or 0,
        total_campaigns=total_campaigns or 0,
        total_tasks=total_tasks or 0,
        total_hashlists=total_hashlists or 0,
    )
    return SystemHealthOverview(
        minio=minio,
        redis=redis_health,
        postgres=postgres,
        agents=agent_summary,
    )
