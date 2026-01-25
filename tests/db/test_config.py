"""Tests for consolidated database configuration in Settings."""

import os
from collections.abc import Generator

import pytest
from pydantic import ValidationError

from app.core.config import Settings

# Constants for default config values
DEFAULT_POOL_SIZE = 5
DEFAULT_MAX_OVERFLOW = 10
DEFAULT_POOL_TIMEOUT = 30
DEFAULT_POOL_RECYCLE = 1800


@pytest.fixture(autouse=True)
def clean_env() -> Generator[None]:
    """Clean environment variables before each test."""
    old_environ = dict(os.environ)
    os.environ.clear()
    yield
    os.environ.clear()
    os.environ.update(old_environ)


def test_settings_database_uri_construction() -> None:
    """Test that sqlalchemy_database_uri is properly constructed."""
    settings = Settings(
        POSTGRES_SERVER="localhost",
        POSTGRES_USER="testuser",
        POSTGRES_PASSWORD="testpass",
        POSTGRES_DB="testdb",
    )
    uri = str(settings.sqlalchemy_database_uri)
    assert "postgresql+psycopg://" in uri
    assert "testuser" in uri
    assert "testpass" in uri
    assert "localhost" in uri
    assert "testdb" in uri


def test_settings_pool_size_validation() -> None:
    """Test pool size validation."""
    # Valid pool size
    settings = Settings(DB_POOL_SIZE=5)
    assert settings.DB_POOL_SIZE == DEFAULT_POOL_SIZE

    # Invalid: less than minimum (1)
    with pytest.raises(ValidationError):
        Settings(DB_POOL_SIZE=0)

    # Invalid: more than maximum (20)
    with pytest.raises(ValidationError):
        Settings(DB_POOL_SIZE=21)


def test_settings_max_overflow_validation() -> None:
    """Test max overflow validation."""
    # Valid max overflow
    settings = Settings(DB_MAX_OVERFLOW=10)
    assert settings.DB_MAX_OVERFLOW == DEFAULT_MAX_OVERFLOW

    # Invalid: negative value
    with pytest.raises(ValidationError):
        Settings(DB_MAX_OVERFLOW=-1)


def test_settings_pool_timeout_validation() -> None:
    """Test pool timeout validation."""
    # Valid pool timeout
    settings = Settings(DB_POOL_TIMEOUT=30)
    assert settings.DB_POOL_TIMEOUT == DEFAULT_POOL_TIMEOUT

    # Invalid: negative value
    with pytest.raises(ValidationError):
        Settings(DB_POOL_TIMEOUT=-1)


def test_settings_pool_recycle_validation() -> None:
    """Test pool recycle validation."""
    # Valid pool recycle
    settings = Settings(DB_POOL_RECYCLE=1800)
    assert settings.DB_POOL_RECYCLE == DEFAULT_POOL_RECYCLE

    # Valid: -1 to disable recycling
    settings = Settings(DB_POOL_RECYCLE=-1)
    assert settings.DB_POOL_RECYCLE == -1

    # Invalid: less than -1
    with pytest.raises(ValidationError):
        Settings(DB_POOL_RECYCLE=-2)


def test_settings_db_defaults() -> None:
    """Test default values for database pool settings."""
    settings = Settings()
    assert settings.DB_POOL_SIZE == DEFAULT_POOL_SIZE
    assert settings.DB_MAX_OVERFLOW == DEFAULT_MAX_OVERFLOW
    assert settings.DB_POOL_TIMEOUT == DEFAULT_POOL_TIMEOUT
    assert settings.DB_POOL_RECYCLE == DEFAULT_POOL_RECYCLE
    assert settings.DB_ECHO is False


def test_settings_db_echo() -> None:
    """Test DB_ECHO setting."""
    settings = Settings(DB_ECHO=True)
    assert settings.DB_ECHO is True

    settings = Settings(DB_ECHO=False)
    assert settings.DB_ECHO is False


def test_settings_from_environment() -> None:
    """Test that settings can be loaded from environment variables."""
    os.environ["DB_POOL_SIZE"] = "10"
    os.environ["DB_MAX_OVERFLOW"] = "20"
    os.environ["DB_POOL_TIMEOUT"] = "60"
    os.environ["DB_POOL_RECYCLE"] = "3600"
    os.environ["DB_ECHO"] = "true"

    settings = Settings()
    assert settings.DB_POOL_SIZE == 10
    assert settings.DB_MAX_OVERFLOW == 20
    assert settings.DB_POOL_TIMEOUT == 60
    assert settings.DB_POOL_RECYCLE == 3600
    assert settings.DB_ECHO is True
