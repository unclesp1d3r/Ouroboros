"""Event bus module for in-process service communication."""

from app.core.events.bus import EventBus, get_event_bus

__all__ = ["EventBus", "get_event_bus"]
