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
