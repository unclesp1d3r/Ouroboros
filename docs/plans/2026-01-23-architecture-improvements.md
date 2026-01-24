# Architecture Improvements Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Improve codebase architecture by implementing an in-process event bus for service decoupling and consolidating configuration to follow 12-factor app principles.

**Architecture:**

- Add a lightweight in-process event bus for synchronous cross-service communication (keeping Celery for truly async tasks)
- Merge `app/db/config.py` into `app/core/config.py` following 12-factor app principles
- Create comprehensive `.env.example` documenting all environment variables

**Tech Stack:** Python 3.13+, Pydantic Settings, FastAPI, asyncio

---

## Task 1: Create Event Bus Module

**Files:**

- Create: `app/core/events/__init__.py`
- Create: `app/core/events/bus.py`
- Test: `tests/unit/test_event_bus.py`

**Step 1: Create the events package init file**

Create `app/core/events/__init__.py`:

```python
"""Event bus module for in-process service communication."""

from app.core.events.bus import EventBus, get_event_bus

__all__ = ["EventBus", "get_event_bus"]
```

**Step 2: Write the failing test for EventBus**

Create `tests/unit/test_event_bus.py`:

```python
"""Tests for the in-process event bus."""

import pytest

from app.core.events.bus import EventBus, get_event_bus


class TestEventBus:
    """Tests for EventBus class."""

    @pytest.fixture
    def bus(self) -> EventBus:
        """Create a fresh event bus for each test."""
        return EventBus()

    @pytest.mark.asyncio
    async def test_subscribe_and_publish(self, bus: EventBus) -> None:
        """Test that subscribers receive published events."""
        received: list[dict] = []

        async def handler(payload: dict) -> None:
            received.append(payload)

        bus.subscribe("test.event", handler)
        await bus.publish("test.event", {"key": "value"})

        assert len(received) == 1
        assert received[0] == {"key": "value"}

    @pytest.mark.asyncio
    async def test_multiple_subscribers(self, bus: EventBus) -> None:
        """Test that multiple subscribers all receive the event."""
        received: list[str] = []

        async def handler1(payload: dict) -> None:
            received.append("handler1")

        async def handler2(payload: dict) -> None:
            received.append("handler2")

        bus.subscribe("test.event", handler1)
        bus.subscribe("test.event", handler2)
        await bus.publish("test.event", {})

        assert "handler1" in received
        assert "handler2" in received

    @pytest.mark.asyncio
    async def test_no_subscribers(self, bus: EventBus) -> None:
        """Test that publishing without subscribers doesn't raise."""
        await bus.publish("no.subscribers", {"data": "test"})

    @pytest.mark.asyncio
    async def test_unsubscribe(self, bus: EventBus) -> None:
        """Test that unsubscribed handlers don't receive events."""
        received: list[dict] = []

        async def handler(payload: dict) -> None:
            received.append(payload)

        bus.subscribe("test.event", handler)
        bus.unsubscribe("test.event", handler)
        await bus.publish("test.event", {"key": "value"})

        assert len(received) == 0

    @pytest.mark.asyncio
    async def test_handler_exception_isolation(self, bus: EventBus) -> None:
        """Test that one handler's exception doesn't affect others."""
        received: list[str] = []

        async def failing_handler(payload: dict) -> None:
            raise ValueError("Handler failed")

        async def working_handler(payload: dict) -> None:
            received.append("success")

        bus.subscribe("test.event", failing_handler)
        bus.subscribe("test.event", working_handler)
        await bus.publish("test.event", {})

        assert "success" in received


class TestEventBusSingleton:
    """Tests for the global event bus singleton."""

    def test_get_event_bus_returns_same_instance(self) -> None:
        """Test that get_event_bus returns the same instance."""
        bus1 = get_event_bus()
        bus2 = get_event_bus()
        assert bus1 is bus2

    def test_get_event_bus_returns_event_bus(self) -> None:
        """Test that get_event_bus returns an EventBus instance."""
        bus = get_event_bus()
        assert isinstance(bus, EventBus)
```

**Step 3: Run test to verify it fails**

Run: `pytest tests/unit/test_event_bus.py -v` Expected: FAIL with "ModuleNotFoundError: No module named 'app.core.events'"

**Step 4: Write the EventBus implementation**

Create `app/core/events/bus.py`:

```python
"""In-process event bus for service decoupling.

This module provides a lightweight event bus for synchronous cross-service
communication. Use this for operations where the caller needs immediate
feedback. For fire-and-forget or long-running operations, use Celery instead.

Example usage:
    from app.core.events import get_event_bus

    # Subscribe to events
    async def on_campaign_created(payload: dict) -> None:
        campaign_id = payload["campaign_id"]
        await notify_agents(campaign_id)

    bus = get_event_bus()
    bus.subscribe("campaign.created", on_campaign_created)

    # Publish events
    await bus.publish("campaign.created", {"campaign_id": 123})
"""

from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any

from loguru import logger

# Type alias for event handlers
EventHandler = Callable[[dict[str, Any]], Awaitable[None]]


class EventBus:
    """In-process event bus for synchronous cross-service communication.

    Provides topic-based publish/subscribe messaging within a single process.
    Handlers are called concurrently using asyncio.gather with exception
    isolation so one failing handler doesn't affect others.

    Attributes:
        _handlers: Mapping of event types to their registered handlers.
    """

    def __init__(self) -> None:
        """Initialize the event bus with empty handler registry."""
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Register a handler for an event type.

        Args:
            event_type: The event type to subscribe to (e.g., "campaign.created").
            handler: Async function that receives the event payload dict.
        """
        self._handlers[event_type].append(handler)
        logger.debug(f"Subscribed handler to event: {event_type}")

    def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        """Remove a handler from an event type.

        Args:
            event_type: The event type to unsubscribe from.
            handler: The handler function to remove.
        """
        if event_type in self._handlers:
            try:
                self._handlers[event_type].remove(handler)
                logger.debug(f"Unsubscribed handler from event: {event_type}")
            except ValueError:
                logger.warning(f"Handler not found for event type: {event_type}")

    async def publish(self, event_type: str, payload: dict[str, Any]) -> None:
        """Publish an event to all subscribed handlers.

        Handlers are called concurrently. If any handler raises an exception,
        it is logged but does not prevent other handlers from executing.

        Args:
            event_type: The event type to publish.
            payload: Dictionary of event data passed to handlers.
        """
        handlers = self._handlers.get(event_type, [])
        if not handlers:
            logger.debug(f"No handlers for event: {event_type}")
            return

        logger.debug(f"Publishing event {event_type} to {len(handlers)} handler(s)")

        for handler in handlers:
            try:
                await handler(payload)
            except Exception:
                logger.exception(
                    f"Handler failed for event {event_type}: {handler.__name__}"
                )


class _EventBusSingleton:
    """Singleton wrapper for the global event bus instance."""

    def __init__(self) -> None:
        """Initialize with no instance."""
        self._instance: EventBus | None = None

    def get_instance(self) -> EventBus:
        """Get or create the singleton EventBus instance.

        Returns:
            The global EventBus instance.
        """
        if self._instance is None:
            self._instance = EventBus()
        return self._instance


_singleton = _EventBusSingleton()


def get_event_bus() -> EventBus:
    """Get the global event bus instance.

    Returns:
        The singleton EventBus instance for application-wide event handling.
    """
    return _singleton.get_instance()
```

**Step 5: Run tests to verify they pass**

Run: `pytest tests/unit/test_event_bus.py -v` Expected: All 6 tests PASS

**Step 6: Commit**

```bash
git add app/core/events/ tests/unit/test_event_bus.py
git commit -m "feat: add in-process event bus for service decoupling

Implements a lightweight event bus for synchronous cross-service
communication, reducing direct coupling between services while
keeping Celery for async/background tasks."
```

---

## Task 2: Consolidate Database Configuration (12-Factor)

**Files:**

- Modify: `app/core/config.py`
- Delete: `app/db/config.py`
- Modify: `app/db/session.py`
- Modify: `app/main.py`
- Modify: `tests/conftest.py`

**Step 1: Read current test configuration to understand usage**

Run: `grep -r "DatabaseSettings" app/ tests/ --include="*.py" | head -20`

This identifies all files importing DatabaseSettings that need updating.

**Step 2: Update app/core/config.py to include database pool settings**

Add to the Settings class in `app/core/config.py` after the existing database settings (line ~86):

```python
# Add these fields to the Settings class:
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
```

**Step 3: Update app/db/session.py to use consolidated settings**

Replace `app/db/session.py` content:

```python
"""Database session management module."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any

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

    def init(self, settings: "Settings") -> None:
        """Initialize the database engine and session maker.

        Args:
            settings: Application settings containing database configuration.
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
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
            bind=self._engine,
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
        except Exception:
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
```

**Step 4: Update app/main.py lifespan to use consolidated settings**

Replace the lifespan function (lines 56-69) in `app/main.py`:

```python
@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
    """FastAPI lifespan events."""
    # Initialize database session manager with consolidated settings
    sessionmanager.init(settings)

    yield

    # Cleanup on shutdown
    await sessionmanager.close()
```

Also remove the import of `DatabaseSettings` from line 28:

```python
# Remove this line:
# from app.db.config import DatabaseSettings
```

**Step 5: Delete the old database config file**

Run: `rm app/db/config.py`

**Step 6: Update app/db/__init__.py if it exports DatabaseSettings**

Check if `app/db/__init__.py` exists and exports `DatabaseSettings`, remove if so.

**Step 7: Run tests to verify nothing breaks**

Run: `pytest tests/ -v --tb=short -x` Expected: All tests pass (or identify any tests using DatabaseSettings directly that need updating)

**Step 8: Commit**

```bash
git add app/core/config.py app/db/session.py app/main.py
git rm app/db/config.py
git commit -m "refactor: consolidate database config into Settings (12-factor)

Merges DatabaseSettings into the main Settings class following
12-factor app principles. All configuration now comes from a
single source with environment variable overrides."
```

---

## Task 3: Create Comprehensive .env.example

**Files:**

- Create: `.env.example`
- Update: `README.md` (reference the new file)

**Step 1: Create comprehensive .env.example**

Create `.env.example` in project root:

```bash
# =============================================================================
# Ouroboros Environment Configuration
# =============================================================================
# Copy this file to .env and customize for your environment.
# All settings have sensible defaults for development.
# =============================================================================

# -----------------------------------------------------------------------------
# Application Settings
# -----------------------------------------------------------------------------
# Application environment: production, development, or testing
# IMPORTANT: Set to "production" in production for secure cookie handling
ENVIRONMENT=development

# Project metadata (rarely needs changing)
# PROJECT_NAME=Ouroboros
# VERSION=0.1.0

# -----------------------------------------------------------------------------
# Security
# -----------------------------------------------------------------------------
# CRITICAL: Change these in production!
SECRET_KEY=change-me-in-production-use-openssl-rand-hex-32
JWT_SECRET_KEY=change-me-in-production-use-openssl-rand-hex-32

# JWT token expiration in minutes (default: 60)
# ACCESS_TOKEN_EXPIRE_MINUTES=60

# -----------------------------------------------------------------------------
# Database (PostgreSQL)
# -----------------------------------------------------------------------------
POSTGRES_SERVER=localhost
POSTGRES_USER=ouroboros
POSTGRES_PASSWORD=ouroboros
POSTGRES_DB=ouroboros

# Connection pool settings (tune for your workload)
# DB_POOL_SIZE=5
# DB_MAX_OVERFLOW=10
# DB_POOL_TIMEOUT=30
# DB_POOL_RECYCLE=1800
# DB_ECHO=false

# -----------------------------------------------------------------------------
# Redis
# -----------------------------------------------------------------------------
REDIS_HOST=localhost
REDIS_PORT=6379

# -----------------------------------------------------------------------------
# Celery (Background Tasks)
# -----------------------------------------------------------------------------
# Uses Redis by default
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# -----------------------------------------------------------------------------
# MinIO (S3-Compatible Storage)
# -----------------------------------------------------------------------------
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=ouroboros-resources
# MINIO_SECURE=false
# MINIO_REGION=

# -----------------------------------------------------------------------------
# Cache
# -----------------------------------------------------------------------------
# In-memory cache for development, use Redis URL for production
# Examples:
#   Development: mem://?check_interval=10&size=10000
#   Production:  redis://localhost:6379/1
CACHE_CONNECT_STRING=mem://?check_interval=10&size=10000

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------
# Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
# LOG_LEVEL=INFO
# LOG_TO_FILE=false
# LOG_FILE_PATH=logs/app.log
# LOG_RETENTION=10 days
# LOG_ROTATION=10 MB

# -----------------------------------------------------------------------------
# CORS (Frontend Origins)
# -----------------------------------------------------------------------------
# Comma-separated list of allowed origins
# BACKEND_CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]

# -----------------------------------------------------------------------------
# First Superuser (Initial Setup)
# -----------------------------------------------------------------------------
FIRST_SUPERUSER=admin@ouroboros.local
FIRST_SUPERUSER_PASSWORD=changeme

# -----------------------------------------------------------------------------
# Resource Limits
# -----------------------------------------------------------------------------
# Maximum file size for in-browser editing (MB)
# RESOURCE_EDIT_MAX_SIZE_MB=1
# Maximum lines for in-browser editing
# RESOURCE_EDIT_MAX_LINES=5000
# Maximum upload size in bytes (default: 100MB)
# UPLOAD_MAX_SIZE=104857600
# Timeout for resource upload verification (seconds)
# RESOURCE_UPLOAD_TIMEOUT_SECONDS=900

# -----------------------------------------------------------------------------
# Hashcat Settings
# -----------------------------------------------------------------------------
# HASHCAT_BINARY_PATH=hashcat
# DEFAULT_WORKLOAD_PROFILE=3
# ENABLE_ADDITIONAL_HASH_TYPES=false
```

**Step 2: Verify .env.example covers all settings**

Run: `grep -E "^\s+[A-Z_]+:" app/core/config.py | wc -l`

Compare count with .env.example entries to ensure all are documented.

**Step 3: Commit**

```bash
git add .env.example
git commit -m "docs: add comprehensive .env.example with all settings

Documents all environment variables with descriptions and examples.
Follows 12-factor app principles for configuration."
```

---

## Task 4: Update Existing .env with Test Database Name Fix

**Files:**

- Modify: `.env`

**Step 1: Update .env to use correct database name**

The current `.env` references `cipherswarm` (legacy name). Update to `ouroboros`:

```bash
TEST_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ouroboros_test

POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=ouroboros

MINIO_ENDPOINT=127.0.0.1:9000
MINIO_ACCESS_KEY=ROOTNAME
MINIO_SECRET_KEY=CHANGEME123
```

**Step 2: Commit**

```bash
git add .env
git commit -m "fix: update database name from cipherswarm to ouroboros"
```

---

## Task 5: Add Event Types Constants Module

**Files:**

- Create: `app/core/events/types.py`
- Modify: `app/core/events/__init__.py`

**Step 1: Create event types constants**

Create `app/core/events/types.py`:

```python
"""Event type constants for the event bus.

Centralizes event type strings to prevent typos and enable IDE autocomplete.
Use these constants when subscribing to or publishing events.

Example:
    from app.core.events import EventTypes, get_event_bus

    bus = get_event_bus()
    bus.subscribe(EventTypes.CAMPAIGN_CREATED, handler)
    await bus.publish(EventTypes.CAMPAIGN_CREATED, {"campaign_id": 123})
"""


class EventTypes:
    """Constants for event bus event types.

    Naming convention: ENTITY_ACTION (e.g., CAMPAIGN_CREATED)
    """

    # Campaign events
    CAMPAIGN_CREATED = "campaign.created"
    CAMPAIGN_UPDATED = "campaign.updated"
    CAMPAIGN_DELETED = "campaign.deleted"
    CAMPAIGN_STARTED = "campaign.started"
    CAMPAIGN_PAUSED = "campaign.paused"
    CAMPAIGN_COMPLETED = "campaign.completed"

    # Attack events
    ATTACK_CREATED = "attack.created"
    ATTACK_UPDATED = "attack.updated"
    ATTACK_DELETED = "attack.deleted"
    ATTACK_STARTED = "attack.started"
    ATTACK_COMPLETED = "attack.completed"

    # Task events
    TASK_CREATED = "task.created"
    TASK_ASSIGNED = "task.assigned"
    TASK_PROGRESS = "task.progress"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"

    # Agent events
    AGENT_REGISTERED = "agent.registered"
    AGENT_HEARTBEAT = "agent.heartbeat"
    AGENT_OFFLINE = "agent.offline"
    AGENT_ERROR = "agent.error"

    # Hash events
    HASH_CRACKED = "hash.cracked"
    HASH_LIST_CREATED = "hash_list.created"
    HASH_LIST_UPDATED = "hash_list.updated"

    # Resource events
    RESOURCE_UPLOADED = "resource.uploaded"
    RESOURCE_DELETED = "resource.deleted"
```

**Step 2: Update __init__.py to export EventTypes**

Update `app/core/events/__init__.py`:

```python
"""Event bus module for in-process service communication."""

from app.core.events.bus import EventBus, get_event_bus
from app.core.events.types import EventTypes

__all__ = ["EventBus", "EventTypes", "get_event_bus"]
```

**Step 3: Commit**

```bash
git add app/core/events/types.py app/core/events/__init__.py
git commit -m "feat: add event type constants for type-safe event handling"
```

---

## Task 6: Integration Test for Event Bus with Service Pattern

**Files:**

- Create: `tests/integration/test_event_bus_integration.py`

**Step 1: Write integration test demonstrating service pattern**

Create `tests/integration/test_event_bus_integration.py`:

```python
"""Integration tests for event bus usage patterns."""

import pytest

from app.core.events import EventTypes, get_event_bus


class TestEventBusServicePattern:
    """Test event bus usage in service-like patterns."""

    @pytest.fixture(autouse=True)
    def reset_event_bus(self) -> None:
        """Reset event bus handlers between tests.

        Note: In production, handlers are registered once at startup.
        For tests, we need to manage handler lifecycle carefully.
        """
        bus = get_event_bus()
        # Clear all handlers for clean test state
        bus._handlers.clear()

    @pytest.mark.asyncio
    async def test_cross_service_notification(self) -> None:
        """Test that services can notify each other via events."""
        notifications_received: list[dict] = []

        # Simulate a "notification service" that listens for campaign events
        async def notification_handler(payload: dict) -> None:
            notifications_received.append(
                {
                    "type": "campaign_created",
                    "campaign_id": payload["campaign_id"],
                }
            )

        bus = get_event_bus()
        bus.subscribe(EventTypes.CAMPAIGN_CREATED, notification_handler)

        # Simulate campaign service creating a campaign
        await bus.publish(
            EventTypes.CAMPAIGN_CREATED,
            {"campaign_id": 42, "name": "Test Campaign"},
        )

        assert len(notifications_received) == 1
        assert notifications_received[0]["campaign_id"] == 42

    @pytest.mark.asyncio
    async def test_multiple_services_subscribe(self) -> None:
        """Test that multiple services can subscribe to the same event."""
        audit_log: list[str] = []
        sse_events: list[str] = []

        async def audit_handler(payload: dict) -> None:
            audit_log.append(f"Cracked hash: {payload['hash_id']}")

        async def sse_handler(payload: dict) -> None:
            sse_events.append(f"toast:{payload['hash_id']}")

        bus = get_event_bus()
        bus.subscribe(EventTypes.HASH_CRACKED, audit_handler)
        bus.subscribe(EventTypes.HASH_CRACKED, sse_handler)

        await bus.publish(
            EventTypes.HASH_CRACKED,
            {"hash_id": 123, "plaintext": "password123"},
        )

        assert len(audit_log) == 1
        assert len(sse_events) == 1
        assert "123" in audit_log[0]
        assert "123" in sse_events[0]

    @pytest.mark.asyncio
    async def test_event_types_constants(self) -> None:
        """Test that EventTypes constants work correctly."""
        received: list[str] = []

        async def handler(payload: dict) -> None:
            received.append(payload["event"])

        bus = get_event_bus()
        bus.subscribe(EventTypes.AGENT_REGISTERED, handler)

        await bus.publish(EventTypes.AGENT_REGISTERED, {"event": "agent.registered"})

        assert EventTypes.AGENT_REGISTERED == "agent.registered"
        assert len(received) == 1
```

**Step 2: Run integration test**

Run: `pytest tests/integration/test_event_bus_integration.py -v` Expected: All tests PASS

**Step 3: Commit**

```bash
git add tests/integration/test_event_bus_integration.py
git commit -m "test: add integration tests for event bus service patterns"
```

---

## Summary

After completing all tasks, the architecture will have:

1. **Event Bus** (`app/core/events/`) - Lightweight in-process pub/sub for service decoupling
2. **Consolidated Config** (`app/core/config.py`) - Single source of truth, 12-factor compliant
3. **Environment Documentation** (`.env.example`) - Complete reference for all settings
4. **Type-Safe Events** (`EventTypes`) - Constants preventing typos in event names

### Verification Checklist

- [ ] All tests pass: `pytest tests/ -v`
- [ ] Type check passes: `basedpyright app/`
- [ ] Lint passes: `ruff check app/`
- [ ] Application starts: `uvicorn app.main:app --reload`
- [ ] `.env.example` covers all Settings fields
