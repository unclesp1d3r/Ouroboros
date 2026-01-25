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
    failures = await bus.publish("campaign.created", {"campaign_id": 123})
    if failures:
        logger.warning(f"{len(failures)} handler(s) failed")
"""

from collections import defaultdict
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from loguru import logger

# Type alias for event handlers
EventHandler = Callable[[dict[str, Any]], Awaitable[None]]


@dataclass
class HandlerFailure:
    """Represents a handler failure during event publishing."""

    handler_name: str
    exception: Exception
    event_type: str


class EventBus:
    """In-process event bus for synchronous cross-service communication.

    Provides topic-based publish/subscribe messaging within a single process.
    Handlers are called sequentially with exception isolation so one failing
    handler doesn't affect others.

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
        handlers = self._handlers.get(event_type, [])
        if handler in handlers:
            handlers.remove(handler)
            logger.debug(f"Unsubscribed handler from event: {event_type}")
        else:
            logger.warning(f"Handler not found for event type: {event_type}")

    def clear(self) -> None:
        """Clear all handlers. Intended for test cleanup."""
        self._handlers.clear()
        logger.debug("Cleared all event handlers")

    async def publish(
        self, event_type: str, payload: dict[str, Any]
    ) -> list[HandlerFailure]:
        """Publish an event to all subscribed handlers.

        Handlers are called sequentially. If any handler raises an exception,
        it is logged but does not prevent other handlers from executing.

        Args:
            event_type: The event type to publish.
            payload: Dictionary of event data passed to handlers.

        Returns:
            List of HandlerFailure objects for any handlers that raised exceptions.
            Empty list if all handlers succeeded.
        """
        handlers = self._handlers.get(event_type, [])
        if not handlers:
            logger.debug(f"No handlers for event: {event_type}")
            return []

        logger.debug(f"Publishing event {event_type} to {len(handlers)} handler(s)")

        failures: list[HandlerFailure] = []
        for handler in handlers:
            try:
                await handler(payload)
            except Exception as e:  # noqa: BLE001 - Intentional: isolate handler failures
                logger.exception(
                    f"Handler failed for event {event_type}: {handler.__name__}"
                )
                failures.append(
                    HandlerFailure(
                        handler_name=handler.__name__,
                        exception=e,
                        event_type=event_type,
                    )
                )

        if failures:
            logger.warning(
                f"Event {event_type}: {len(failures)}/{len(handlers)} handler(s) failed"
            )

        return failures


# Module-level singleton instance (created at import time for thread safety)
_event_bus = EventBus()


def get_event_bus() -> EventBus:
    """Get the global event bus instance.

    Returns:
        The singleton EventBus instance for application-wide event handling.
    """
    return _event_bus
