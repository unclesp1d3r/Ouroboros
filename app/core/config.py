"""Core configuration module."""

from pydantic import AnyHttpUrl, Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings.

    Attributes:
        PROJECT_NAME: Name of the project
        VERSION: Project version
        API_V1_STR: API version 1 prefix
        BACKEND_CORS_ORIGINS: List of origins that can access the API
        SECRET_KEY: Secret key for JWT tokens
        ENVIRONMENT: Application environment (production, development, testing)
        POSTGRES_SERVER: PostgreSQL server hostname
        POSTGRES_USER: PostgreSQL username
        POSTGRES_PASSWORD: PostgreSQL password
        POSTGRES_DB: PostgreSQL database name
        sqlalchemy_database_uri: SQLAlchemy database URI
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
        DB_ECHO: bool = False
        MINIO_ENDPOINT: str = "minio:9000"
        MINIO_ACCESS_KEY: str = "minioadmin"
        MINIO_SECRET_KEY: str = "minioadmin"
        MINIO_BUCKET: str = "ouroboros-resources"
        MINIO_SECURE: bool = False
        MINIO_REGION: str | None = None
        JWT_SECRET_KEY: str = "a_very_secret_key"
        RESOURCE_UPLOAD_VERIFICATION_ENABLED: bool = True
        CACHE_URI: str = "mem://"
        UPLOAD_MAX_SIZE: int = 100 * 1024 * 1024  # 100MB
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
