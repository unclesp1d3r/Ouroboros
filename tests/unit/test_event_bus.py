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
