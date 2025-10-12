"""
🧭 JSON API Refactor - Ouroboros Web UI

Follow these rules for all endpoints in this file:
1. Must return Pydantic models as JSON (no TemplateResponse or render()).
2. Must use FastAPI parameter types: Query, Path, Body, Depends, etc.
3. Must not parse inputs manually — let FastAPI validate and raise 422s.
4. Must use dependency-injected context for auth/user/project state.
5. Must not include database logic — delegate to a service layer (e.g. campaign_service).
6. Must not contain HTMX, Jinja, or fragment-rendering logic.
7. Must annotate live-update triggers with: # SSE_TRIGGER: <event description>
8. Must update test files to expect JSON (not HTML) and preserve test coverage.

📘 See canonical task list and instructions in:
docs/v2_rewrite_implementation_plan/phase-2-api-implementation-part-2.md

Live Event Feeds (Server-Sent Events)
=====================================

These endpoints provide Server-Sent Events (SSE) streams for real-time notifications
to the frontend. They use in-memory event broadcasting without external dependencies.
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from loguru import logger

from app.core.deps import get_current_user
from app.core.services.event_service import get_event_service
from app.models.user import User

router = APIRouter(prefix="/live")


@router.get("/campaigns")
async def campaign_events_feed(
    current_user: Annotated[User, Depends(get_current_user)],
) -> StreamingResponse:
    """
    Server-Sent Events feed for campaign/attack/task state changes.

    Clients should listen for 'refresh' events and then fetch updated data
    from the appropriate campaign endpoints.
    """
    event_service = get_event_service()

    listener = await event_service.create_listener(
        topics={"campaigns"},
        project_id=None,  # TODO: Add project scoping when project context is available
    )

    logger.info(f"User {current_user.id} connected to campaign events feed")

    return StreamingResponse(
        listener.get_events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


@router.get("/agents")
async def agent_events_feed(
    current_user: Annotated[User, Depends(get_current_user)],
) -> StreamingResponse:
    """
    Server-Sent Events feed for agent status, performance, and error updates.

    Clients should listen for 'refresh' events and then fetch updated data
    from the appropriate agent endpoints.
    """
    event_service = get_event_service()

    listener = await event_service.create_listener(
        topics={"agents"},
        project_id=None,  # TODO: Add project scoping when project context is available
    )

    logger.info(f"User {current_user.id} connected to agent events feed")

    return StreamingResponse(
        listener.get_events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


@router.get("/toasts")
async def toast_events_feed(
    current_user: Annotated[User, Depends(get_current_user)],
) -> StreamingResponse:
    """
    Server-Sent Events feed for toast notifications (new crack results, system alerts).

    Clients should listen for events and display toast notifications in the UI.
    The 'trigger' field contains the message to display.
    """
    event_service = get_event_service()

    listener = await event_service.create_listener(
        topics={"toasts"},
        project_id=None,  # TODO: Add project scoping when project context is available
    )

    logger.info(f"User {current_user.id} connected to toast events feed")

    return StreamingResponse(
        listener.get_events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


# Broadcast helper functions for use by other services
async def broadcast_campaign_update(
    campaign_id: int, project_id: int | None = None
) -> None:
    """Broadcast a campaign update event."""
    event_service = get_event_service()
    await event_service.broadcast_campaign_update(campaign_id, project_id)


async def broadcast_agent_update(agent_id: int, project_id: int | None = None) -> None:
    """Broadcast an agent update event."""
    event_service = get_event_service()
    await event_service.broadcast_agent_update(agent_id, project_id)


async def broadcast_toast(message: str, project_id: int | None = None) -> None:
    """Broadcast a toast notification event."""
    event_service = get_event_service()
    await event_service.broadcast_toast_notification(message, project_id)
