from pydantic import BaseModel, Field


class MinioHealth(BaseModel):
    status: str = Field(
        ..., description="MinIO service status: healthy, degraded, unreachable"
    )
    latency: float | None = Field(None, description="API response time in seconds")
    error: str | None = Field(None, description="Error message if any")
    bucket_count: int | None = Field(None, description="Number of buckets")


class MinioHealthDetailed(MinioHealth):
    """Extended MinIO health information for admin users"""

    object_count: int | None = Field(
        None, description="Total number of objects across all buckets"
    )
    storage_usage: int | None = Field(None, description="Total storage usage in bytes")
    metrics_error: str | None = Field(
        None, description="Error message if detailed metrics fetch failed"
    )


class RedisHealth(BaseModel):
    status: str = Field(
        ..., description="Redis service status: healthy, degraded, unreachable"
    )
    latency: float | None = Field(None, description="Command roundtrip time in seconds")
    error: str | None = Field(None, description="Error message if any")
    memory_usage: int | None = Field(None, description="Memory usage in bytes")
    active_connections: int | None = Field(
        None, description="Number of active connections"
    )


class RedisHealthDetailed(RedisHealth):
    """Extended Redis health information for admin users"""

    keyspace_keys: int | None = Field(
        None, description="Total number of keys in keyspace"
    )
    evicted_keys: int | None = Field(None, description="Number of evicted keys")
    expired_keys: int | None = Field(None, description="Number of expired keys")
    max_memory: int | None = Field(None, description="Maximum memory limit in bytes")
    metrics_error: str | None = Field(
        None, description="Error message if detailed metrics fetch failed"
    )


class PostgresHealth(BaseModel):
    status: str = Field(
        ..., description="PostgreSQL service status: healthy, degraded, unreachable"
    )
    latency: float | None = Field(None, description="Query roundtrip time in seconds")
    error: str | None = Field(None, description="Error message if any")


class PostgresHealthDetailed(PostgresHealth):
    """Extended PostgreSQL health information for admin users"""

    active_connections: int | None = Field(
        None, description="Number of active connections"
    )
    max_connections: int | None = Field(None, description="Maximum allowed connections")
    long_running_queries: int | None = Field(
        None, description="Number of long-running queries (>30s)"
    )
    database_size: int | None = Field(None, description="Database size in bytes")
    metrics_error: str | None = Field(
        None, description="Error message if detailed metrics fetch failed"
    )


class AgentHealthSummary(BaseModel):
    total_agents: int = Field(..., description="Total number of agents")
    online_agents: int = Field(
        ..., description="Number of agents online (last seen <2min)"
    )
    total_campaigns: int = Field(..., description="Total number of campaigns")
    total_tasks: int = Field(..., description="Total number of tasks")
    total_hashlists: int = Field(..., description="Total number of hash lists")


class SystemHealthOverview(BaseModel):
    minio: MinioHealth
    redis: RedisHealth
    postgres: PostgresHealth
    agents: AgentHealthSummary


class SystemHealthComponents(BaseModel):
    """Detailed system health information for components"""

    minio: MinioHealth | MinioHealthDetailed
    redis: RedisHealth | RedisHealthDetailed
    postgres: PostgresHealth | PostgresHealthDetailed
