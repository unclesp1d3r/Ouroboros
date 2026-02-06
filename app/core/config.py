"""Core configuration module."""

from pydantic import AnyHttpUrl, Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings.

    All configuration is loaded from environment variables following 12-factor app principles.
    Database pool settings are consolidated here for a single source of truth.

    Attributes:
        PROJECT_NAME: Name of the project
        VERSION: Project version
        BACKEND_CORS_ORIGINS: List of origins that can access the API
        SECRET_KEY: Secret key for JWT tokens
        ENVIRONMENT: Application environment (production, development, testing)
        POSTGRES_SERVER: PostgreSQL server hostname
        POSTGRES_USER: PostgreSQL username
        POSTGRES_PASSWORD: PostgreSQL password
        POSTGRES_DB: PostgreSQL database name
        DB_POOL_SIZE: Size of the database connection pool
        DB_MAX_OVERFLOW: Maximum overflow connections beyond pool_size
        DB_POOL_TIMEOUT: Seconds to wait for a connection from the pool
        DB_POOL_RECYCLE: Seconds after which connections are recycled
        DB_ECHO: Echo SQL statements to stdout (development only)
        sqlalchemy_database_uri: SQLAlchemy database URI (computed property)
        FIRST_SUPERUSER: First superuser email
        FIRST_SUPERUSER_PASSWORD: First superuser password
        REDIS_HOST: Redis server hostname
        REDIS_PORT: Redis server port
        CELERY_BROKER_URL: Celery broker URL
        CELERY_RESULT_BACKEND: Celery result backend URL
        HASHCAT_BINARY_PATH: Path to hashcat binary
        DEFAULT_WORKLOAD_PROFILE: Default hashcat workload profile
        ENABLE_ADDITIONAL_HASH_TYPES: Enable additional hash types
        ACCESS_TOKEN_EXPIRE_MINUTES: JWT access token expiration time in minutes
        RESOURCE_EDIT_MAX_SIZE_MB: Maximum size (in MB) for in-browser resource editing
        RESOURCE_EDIT_MAX_LINES: Maximum number of lines for in-browser resource editing
        MINIO_ENDPOINT: MinIO S3-compatible storage endpoint
        MINIO_ACCESS_KEY: MinIO access key
        MINIO_SECRET_KEY: MinIO secret key
        MINIO_BUCKET: MinIO bucket name
        MINIO_SECURE: Whether MinIO uses HTTPS
        MINIO_REGION: Optional MinIO region
        JWT_SECRET_KEY: JWT secret key
        CACHE_CONNECT_STRING: Cache connection string for cashews
        UPLOAD_MAX_SIZE: Maximum upload size in bytes
    """

    PROJECT_NAME: str = "Ouroboros"
    VERSION: str = "0.1.0"
    BACKEND_CORS_ORIGINS: list[AnyHttpUrl] = Field(
        default_factory=list,
        description="List of origins that can access the API",
    )

    # Environment
    ENVIRONMENT: str = Field(
        default="production",
        description="Application environment (production, development, testing). Defaults to production for security.",
    )

    # Security
    SECRET_KEY: str = Field(
        default="k5moVLqLGy82D4FE54VvkkqAyxe6XF6k",
        description="Secret key for JWT tokens",
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=60,
        description="JWT access token expiration time in minutes",
    )

    # Database
    POSTGRES_SERVER: str = Field(
        default="localhost",
        description="PostgreSQL server hostname",
    )
    POSTGRES_USER: str = Field(
        default="ouroboros",
        description="PostgreSQL username",
    )
    POSTGRES_PASSWORD: str = Field(
        default="ouroboros",
        description="PostgreSQL password",
    )
    POSTGRES_DB: str = Field(
        default="ouroboros",
        description="PostgreSQL database name",
    )

    # Database Connection Pool Settings
    DB_POOL_SIZE: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Size of the database connection pool",
    )
    DB_MAX_OVERFLOW: int = Field(
        default=10,
        ge=0,
        description="Maximum overflow connections beyond pool_size",
    )
    DB_POOL_TIMEOUT: int = Field(
        default=30,
        ge=0,
        description="Seconds to wait for a connection from the pool",
    )
    DB_POOL_RECYCLE: int = Field(
        default=1800,
        ge=-1,
        description="Seconds after which connections are recycled (-1 to disable)",
    )
    DB_ECHO: bool = Field(
        default=False,
        description="Echo SQL statements to stdout (development only)",
    )

    # Users
    FIRST_SUPERUSER: str = Field(
        default="admin@ouroboros.local",
        description="First superuser email",
    )
    FIRST_SUPERUSER_PASSWORD: str = Field(
        default="ouroboros",
        description="First superuser password",
    )

    # Redis
    REDIS_HOST: str = Field(
        default="localhost",
        description="Redis server hostname",
    )
    REDIS_PORT: int = Field(
        default=6379,
        description="Redis server port",
    )

    # Celery
    CELERY_BROKER_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Celery broker URL",
    )
    CELERY_RESULT_BACKEND: str = Field(
        default="redis://localhost:6379/0",
        description="Celery result backend URL",
    )

    # Hashcat Settings
    HASHCAT_BINARY_PATH: str = Field(
        default="hashcat",
        description="Path to hashcat binary",
    )
    DEFAULT_WORKLOAD_PROFILE: int = Field(
        default=3,
        description="Default hashcat workload profile",
    )
    ENABLE_ADDITIONAL_HASH_TYPES: bool = Field(
        default=False,
        description="Enable additional hash types",
    )

    # Logging
    log_level: str = Field(default="INFO", description="Log level for loguru")
    log_to_file: bool = Field(default=False, description="Enable file logging")
    log_file_path: str = Field(default="logs/app.log", description="Path to log file")
    log_retention: str = Field(
        default="10 days",
        description="Log file retention policy",
    )
    log_rotation: str = Field(default="10 MB", description="Log file rotation policy")

    # Resource Editing Limits
    RESOURCE_EDIT_MAX_SIZE_MB: int = Field(
        default=1,
        description="Maximum size (in MB) for in-browser resource editing. Larger files must be downloaded and edited offline.",
    )
    RESOURCE_EDIT_MAX_LINES: int = Field(
        default=5000,
        description="Maximum number of lines for in-browser resource editing. Larger files must be downloaded and edited offline.",
    )

    # Crackable Upload Limits
    UPLOAD_MAX_SIZE: int = Field(
        default=100 * 1024 * 1024,  # 100MB
        description="Maximum allowed upload size for crackable uploads in bytes (default 100MB)",
    )

    # Resource Upload Verification
    RESOURCE_UPLOAD_TIMEOUT_SECONDS: int = Field(
        default=900,
        description="Timeout in seconds for background verification of resource uploads. If the file is not uploaded within this time, the resource is deleted. Tests should override this to a low value.",
    )

    # Resource Cleanup Job
    RESOURCE_CLEANUP_INTERVAL_HOURS: int = Field(
        default=1,
        description="Interval in hours for periodic resource cleanup job",
    )
    RESOURCE_CLEANUP_AGE_HOURS: int = Field(
        default=24,
        description="Age in hours after which pending resources are cleaned up",
    )

    # MinIO S3-Compatible Storage
    MINIO_ENDPOINT: str = Field(
        default="minio:9000",
        description="MinIO endpoint",
    )
    MINIO_ACCESS_KEY: str = Field(
        default="minioadmin",
        description="MinIO access key",
    )
    MINIO_SECRET_KEY: str = Field(
        default="minioadmin",
        description="MinIO secret key",
    )
    MINIO_BUCKET: str = Field(
        default="ouroboros-resources",
        description="MinIO bucket name",
    )
    MINIO_SECURE: bool = Field(
        default=False,
        description="Set to True if MinIO uses HTTPS",
    )
    MINIO_REGION: str | None = Field(
        default=None,
        description="Optional: e.g., 'us-east-1'",
    )

    # JWT settings
    JWT_SECRET_KEY: str = Field(
        default="a_very_secret_key",
        description="JWT secret key",
    )

    # Cache
    CACHE_CONNECT_STRING: str = Field(
        default="mem://?check_interval=10&size=10000",
        description="Cache connection string for cashews",
    )

    @property
    def sqlalchemy_database_uri(self) -> PostgresDsn:
        """Get the SQLAlchemy database URI.

        Returns:
            PostgresDsn: Database URI
        """
        return PostgresDsn.build(
            scheme="postgresql+psycopg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            path=self.POSTGRES_DB,
        )

    @property
    def cookies_secure(self) -> bool:
        """Determine if cookies should be secure based on environment.

        Returns:
            bool: True if cookies should be secure (HTTPS only), False otherwise
        """
        return self.ENVIRONMENT.lower() == "production"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
