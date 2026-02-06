"""Ouroboros FastAPI Application."""

import asyncio
import contextlib
import logging
import time
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager

from cashews import cache
from cashews.contrib.fastapi import (
    CacheDeleteMiddleware,
    CacheEtagMiddleware,
    CacheRequestControlMiddleware,
)
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.endpoints.agent.v1_http_exception_handler import (
    v1_http_exception_handler,
)
from app.api.v1.router import api_router as api_v1_router
from app.core.config import settings
from app.core.control_rfc9457_middleware import ControlRFC9457Middleware
from app.core.exceptions import InvalidAgentTokenError
from app.core.logging import logger
from app.core.openapi_customization import setup_openapi_customization
from app.db.session import sessionmanager


# Redirect standard logging to loguru
class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = str(record.levelno)
        frame = logging.currentframe()
        depth = 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back  # type: ignore[assignment]
            depth += 1
        logger.opt(depth=depth, exception=record.exc_info).log(
            level,
            record.getMessage(),
        )


logging.basicConfig(handlers=[InterceptHandler()], level=0)
for name in logging.root.manager.loggerDict:
    logging.getLogger(name).handlers = [InterceptHandler()]


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
    """FastAPI lifespan events."""
    from app.core.tasks.resource_tasks import run_periodic_cleanup

    # Initialize database session manager with consolidated settings
    sessionmanager.init(settings)

    # Start periodic cleanup task
    cleanup_task = asyncio.create_task(run_periodic_cleanup())

    yield

    # Shutdown cleanup
    cleanup_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await cleanup_task
    await sessionmanager.close()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="""
Ouroboros is a distributed password cracking management system built with FastAPI and SvelteKit. It's a complete rewrite of CipherSwarm that coordinates multiple hashcat instances across different machines to efficiently crack password hashes using various attack strategies.

## API Interfaces

Ouroboros provides three distinct API interfaces:

### Agent API (`/api/v1/client/*`)
- **Purpose**: Legacy compatibility for existing hashcat agents
- **Authentication**: Bearer tokens (`csa_<agent_id>_<token>`)
- **Contract**: Strict adherence to OpenAPI 3.0.1 specification
- **Features**: Registration, heartbeat, task assignment, progress reporting, result submission

### Web UI API (`/api/v1/web/*`)
- **Purpose**: Rich interface for SvelteKit frontend
- **Authentication**: JWT tokens with HTTP-only cookies
- **Features**: Campaign management, attack configuration, agent monitoring, resource management, real-time SSE

### Control API (`/api/v1/control/*`)
- **Purpose**: Programmatic access for CLI tools and automation
- **Authentication**: API keys (`cst_<user_id>_<token>`)
- **Error Format**: RFC9457 Problem Details
- **Features**: Complete CRUD operations, batch processing, template management

## Authentication

All endpoints (except health checks and login) require authentication:

- **Agent API**: `Authorization: Bearer csa_<agent_id>_<token>`
- **Web UI API**: JWT tokens in HTTP-only cookies
- **Control API**: `Authorization: Bearer cst_<user_id>_<token>`

## Error Handling

Each API interface uses different error response formats:

- **Agent API**: `{"error": "message"}` (legacy compatibility)
- **Web UI API**: `{"detail": "message"}` (FastAPI standard)
- **Control API**: RFC9457 Problem Details format

## Rate Limiting

All APIs implement rate limiting to prevent abuse:
- Agent API: 100 requests/minute per agent
- Web UI API: 300 requests/minute per session
- Control API: 500 requests/minute per API key

## Real-Time Updates

The Web UI API provides Server-Sent Events (SSE) for real-time notifications:
- `/api/v1/web/live/campaigns` - Campaign, attack, and task state changes
- `/api/v1/web/live/agents` - Agent status and performance updates
- `/api/v1/web/live/toasts` - Crack results and system notifications

## Multi-Tenancy

Ouroboros implements project-based multi-tenancy where all resources are scoped to projects and users can be members of multiple projects.
""",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    contact={
        "name": "Ouroboros Project",
        "url": "https://github.com/unclesp1d3r/Ouroboros",
    },
    license_info={
        "name": "Mozilla Public License 2.0",
        "url": "https://mozilla.org/MPL/2.0/",
    },
    servers=[
        {
            "url": "http://localhost:8000",
            "description": "Development server",
        },
        {
            "url": "https://api.ouroboros.example.com",
            "description": "Production server",
        },
    ],
)

# Configure CORS for SvelteKit frontend cookie handling
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS]
    or [
        "http://localhost:5173",  # SvelteKit dev server
        "http://localhost:3000",  # Alternative dev port
        "http://localhost:3005",  # E2E testing port
    ],
    allow_credentials=True,  # Required for cookie-based authentication
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
        "Cookie",
        "Set-Cookie",
        "X-Requested-With",
        "X-Request-ID",
        "Access-Control-Allow-Credentials",
    ],
    expose_headers=[
        "Set-Cookie",
        "X-Request-ID",
    ],
)

# Add Cashews Middleware
app.add_middleware(CacheDeleteMiddleware)
app.add_middleware(CacheEtagMiddleware)
app.add_middleware(CacheRequestControlMiddleware)
cache.setup(settings.CACHE_CONNECT_STRING)

app.add_middleware(
    GZipMiddleware,
    minimum_size=1000,
)  # Compress responses larger than 1000 bytes


# Add RFC9457 middleware for Control API routes only
app.add_middleware(ControlRFC9457Middleware)

# Register v1 error envelope handler for HTTPException
app.add_exception_handler(HTTPException, v1_http_exception_handler)


# Logging middleware
@app.middleware("http")
async def log_requests(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    start_time = time.time()
    request_id = request.headers.get("x-request-id")
    try:
        response = await call_next(request)
    except Exception as e:
        logger.error(
            "Exception in request: {method} {url} | request_id={request_id} | error={error}",
            method=request.method,
            url=request.url.path,
            request_id=request_id,
            error=str(e),
        )
        raise
    process_time = (time.time() - start_time) * 1000
    logger.info(
        "{method} {url} - {status_code} - {process_time:.2f}ms | request_id={request_id}",
        method=request.method,
        url=request.url.path,
        status_code=response.status_code,
        process_time=process_time,
        request_id=request_id,
    )
    return response


# Middleware to set cookies from request.state.set_cookie (for FastHX endpoints)
@app.middleware("http")
async def set_cookie_from_state_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    response = await call_next(request)
    set_cookie = getattr(request.state, "set_cookie", None)
    if set_cookie:
        response.set_cookie(**set_cookie)
    hx_status_code = getattr(request.state, "hx_status_code", None)
    if hx_status_code:
        response.status_code = hx_status_code
    return response


# API router registration
app.include_router(api_v1_router, prefix="/api/v1")

# TODO: Enable v2 API when implementation is complete
# from app.api.v2.router import api_router as api_v2_router
# app.include_router(api_v2_router, prefix="/api/v2")


@app.get("/api-info")
async def api_info() -> dict[str, str]:
    """API information stub (moved from root)."""
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Simple health check endpoint for Docker health checks."""
    return {"status": "healthy"}


@app.exception_handler(InvalidAgentTokenError)
async def invalid_agent_token_handler(
    _request: Request,
    exc: InvalidAgentTokenError,
) -> JSONResponse:
    return JSONResponse(status_code=401, content={"detail": str(exc)})


# Register v1 error handler for all /api/v1/client/* and /api/v1/agent/* endpoints (contract compliance)
# The handler passes any non-Agent API endpoints to the default handler
app.add_exception_handler(HTTPException, v1_http_exception_handler)

# Setup custom OpenAPI documentation
setup_openapi_customization(app)
