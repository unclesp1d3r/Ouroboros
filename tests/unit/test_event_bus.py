"""Tests for the in-process event bus."""

import pytest

from app.core.events.bus import EventBus, HandlerFailure, get_event_bus


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
        failures = await bus.publish("no.subscribers", {"data": "test"})
        assert failures == []

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
    async def test_unsubscribe_nonexistent_handler(self, bus: EventBus) -> None:
        """Test that unsubscribing a non-registered handler logs warning but doesn't raise."""

        async def handler1(payload: dict) -> None:
            pass

        async def handler2(payload: dict) -> None:
            pass

        bus.subscribe("test.event", handler1)
        # Unsubscribe a different handler - should not raise
        bus.unsubscribe("test.event", handler2)

        # Original handler should still be subscribed
        received: list[str] = []

        async def check_handler(payload: dict) -> None:
            received.append("received")

        bus.subscribe("test.event", check_handler)
        await bus.publish("test.event", {})
        assert "received" in received

    @pytest.mark.asyncio
    async def test_unsubscribe_nonexistent_event_type(self, bus: EventBus) -> None:
        """Test that unsubscribing from non-existent event type is safe."""

        async def handler(payload: dict) -> None:
            pass

        # Should not raise
        bus.unsubscribe("nonexistent.event", handler)

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
        failures = await bus.publish("test.event", {})

        assert "success" in received
        assert len(failures) == 1
        assert failures[0].handler_name == "failing_handler"
        assert isinstance(failures[0].exception, ValueError)
        assert failures[0].event_type == "test.event"

    @pytest.mark.asyncio
    async def test_publish_returns_handler_failures(self, bus: EventBus) -> None:
        """Test that publish returns list of handler failures."""

        async def failing_handler1(payload: dict) -> None:
            raise ValueError("Error 1")

        async def failing_handler2(payload: dict) -> None:
            raise RuntimeError("Error 2")

        async def working_handler(payload: dict) -> None:
            pass

        bus.subscribe("test.event", failing_handler1)
        bus.subscribe("test.event", working_handler)
        bus.subscribe("test.event", failing_handler2)

        failures = await bus.publish("test.event", {})

        assert len(failures) == 2
        assert all(isinstance(f, HandlerFailure) for f in failures)
        handler_names = {f.handler_name for f in failures}
        assert handler_names == {"failing_handler1", "failing_handler2"}

    @pytest.mark.asyncio
    async def test_handlers_execute_in_subscription_order(self, bus: EventBus) -> None:
        """Test that handlers execute in the order they were subscribed."""
        order: list[int] = []

        async def handler1(payload: dict) -> None:
            order.append(1)

        async def handler2(payload: dict) -> None:
            order.append(2)

        async def handler3(payload: dict) -> None:
            order.append(3)

        bus.subscribe("test.event", handler1)
        bus.subscribe("test.event", handler2)
        bus.subscribe("test.event", handler3)

        await bus.publish("test.event", {})

        assert order == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_different_event_types_are_independent(self, bus: EventBus) -> None:
        """Test that handlers only receive events they subscribed to."""
        campaign_events: list[dict] = []
        attack_events: list[dict] = []

        async def campaign_handler(payload: dict) -> None:
            campaign_events.append(payload)

        async def attack_handler(payload: dict) -> None:
            attack_events.append(payload)

        bus.subscribe("campaign.created", campaign_handler)
        bus.subscribe("attack.created", attack_handler)

        await bus.publish("campaign.created", {"id": 1})
        await bus.publish("attack.created", {"id": 2})

        assert len(campaign_events) == 1
        assert len(attack_events) == 1
        assert campaign_events[0]["id"] == 1
        assert attack_events[0]["id"] == 2

    def test_clear_removes_all_handlers(self, bus: EventBus) -> None:
        """Test that clear() removes all handlers."""

        async def handler(payload: dict) -> None:
            pass

        bus.subscribe("event1", handler)
        bus.subscribe("event2", handler)

        bus.clear()

        # Verify handlers are cleared (internal check)
        assert len(bus._handlers) == 0


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
