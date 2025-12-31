"""Agent API v2 Router Configuration.

This module organizes all v2 API endpoints for the modernized agent communication interface.
The v2 API provides improved authentication, better state management, and enhanced task
distribution capabilities while maintaining backward compatibility with v1.
"""

from fastapi import APIRouter

from app.api.v2.endpoints.agents import router as agents_router
from app.api.v2.endpoints.attacks import router as attacks_router
from app.api.v2.endpoints.resources import router as resources_router
from app.api.v2.endpoints.tasks import router as tasks_router

# Create the main v2 API router
api_router = APIRouter()

# Include all v2 endpoint routers
api_router.include_router(agents_router)
api_router.include_router(attacks_router)
api_router.include_router(tasks_router)
api_router.include_router(resources_router)
