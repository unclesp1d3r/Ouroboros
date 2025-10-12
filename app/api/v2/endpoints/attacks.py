"""Agent API v2 - Attack Configuration Endpoints.

This module provides endpoints for retrieving attack configurations and specifications
in the modernized v2 API. It includes enhanced capability validation, forward-compatible
resource management, and improved authorization compared to the legacy v1 API.

Endpoints:
- GET /api/v2/client/agents/attacks/{attack_id} - Attack configuration retrieval with validation
"""

from fastapi import APIRouter

# Create router with v2 client prefix and appropriate tags
router = APIRouter(
    prefix="/client/agents/attacks",
    tags=["Agent API v2 - Attacks"],
)

# TODO: Implement attack configuration endpoint (Task 4.3)
# GET /{attack_id} - Attack configuration retrieval with capability validation and authorization
