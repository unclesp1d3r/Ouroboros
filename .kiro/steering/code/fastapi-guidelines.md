---
inclusion: fileMatch
fileMatchPattern:
  - '**/api/**/*.py'
  - '**/routes/**/*.py'
  - '**/endpoints/**/*.py'
  - '**/schemas/**/*.py'
  - '**/models/**/*.py'
---

# FastAPI Development Guidelines

## Description

Standards and best practices for FastAPI development in the Ouroboros project.

## File Glob Patterns

- `**/api/**/*.py`
- `**/routes/**/*.py`
- `**/endpoints/**/*.py`
- `**/schemas/**/*.py`
- `**/models/**/*.py`

## Always Apply

true

## Key Principles

- Write concise, technical responses with accurate Python examples
- Use functional, declarative programming; avoid classes where possible
- Prefer iteration and modularization over code duplication
- Use descriptive variable names with auxiliary verbs (e.g., is_active, has_permission)
- Use lowercase with underscores for directories and files (e.g., routers/user_routes.py)
- Favor named exports for routes and utility functions
- Use the Receive an Object, Return an Object (RORO) pattern
- **All application logging must use `loguru`. Do not use standard Python `logging`.**
- **All caching must use Cashews (`cashews` library) exclusively. Do not use functools, FastAPI internal cache, or any other mechanism.**
- **All public API routes must be versioned (e.g., `/api/v1/...`).**

## Code Organization

### Route Structure

```python
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/resource", tags=["Resource"])


class ResourceCreate(BaseModel):
    name: str
    description: str | None = None


@router.post("/", response_model=ResourceResponse)
async def create_resource(
    data: ResourceCreate, current_user: User = Depends(get_current_user)
) -> ResourceResponse:
    """Create a new resource.

    Args:
        data: The resource data
        current_user: The authenticated user

    Returns:
        The created resource

    Raises:
        HTTPException: If resource creation fails
    """
    try:
        return await resource_service.create(data, current_user)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ResourceError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

### Error Handling

- Handle errors at the beginning of functions
- Use early returns for error conditions
- Place the happy path last
- Use guard clauses for preconditions
- Implement proper error logging
- Use custom error types

```python
async def process_resource(resource_id: int) -> Resource:
    # Guard clause
    if not resource_id:
        raise ValueError("Resource ID is required")

    # Early error handling
    resource = await get_resource(resource_id)
    if not resource:
        raise ResourceNotFound(f"Resource {resource_id} not found")

    # Happy path
    return await process_resource_data(resource)
```

## Dependencies

- FastAPI
- Pydantic v2
- SQLAlchemy 2.0
- psycopg v3

## FastAPI-Specific Guidelines

### Route Definitions

```python
@router.get(
    "/{resource_id}",
    response_model=ResourceResponse,
    responses={404: {"model": ErrorResponse}, 401: {"model": ErrorResponse}},
)
async def get_resource(
    resource_id: int, current_user: User = Depends(get_current_user)
) -> ResourceResponse:
    """Get a resource by ID."""
    return await resource_service.get(resource_id, current_user)
```

### Middleware Usage

```python
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response
```

### Dependency Injection

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


@router.get("/{id}")
async def get_item(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await crud.get_item(db, id, current_user)
```

### Response Types

✅ Use `JSONResponse` for all `/api/v1/web/*` views\
🚫 Never use `TemplateResponse`, Jinja2, or fragment rendering

- All endpoints must define response models with Pydantic
- Use dependency injection for auth, user context, and project scope
- Return clear HTTP status codes and schema-validated JSON

## Performance Optimization

- Use async operations for I/O-bound tasks
- Implement caching strategies
- Use lazy loading for large datasets
- Optimize Pydantic models
- **All caching must use Cashews. No other cache mechanism is permitted.**

```python
# Caching example
from fastapi_cache import FastAPICache
from fastapi_cache.decorator import cache


@router.get("/expensive-operation")
@cache(expire=60)  # Cache for 60 seconds
async def expensive_operation():
    result = await perform_expensive_calculation()
    return result
```

## Testing Guidelines

### Test Structure

```python
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_resource(
    async_client: AsyncClient, test_db: AsyncSession, auth_headers: dict
):
    response = await async_client.post(
        "/api/v1/resources/", json={"name": "Test Resource"}, headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Resource"
```

### Test Categories

1. Unit Tests

   - Test individual functions
   - Mock external dependencies
   - Focus on edge cases

2. Integration Tests

   - Test API endpoints
   - Use test database
   - Test authentication flows

3. Performance Tests

   - Test response times
   - Test concurrent requests
   - Test caching behavior

## Common Patterns

### Pagination

```python
from fastapi import Query
from typing import TypeVar, Generic, Sequence
from pydantic import BaseModel

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: Sequence[T]
    total: int
    page: int
    size: int

    @property
    def pages(self) -> int:
        return (self.total + self.size - 1) // self.size


@router.get("/items", response_model=Page[Item])
async def list_items(
    page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100)
) -> Page[Item]:
    items = await get_items(skip=(page - 1) * size, limit=size)
    total = await get_total_items()
    return Page(items=items, total=total, page=page, size=size)
```

### Background Tasks

```python
from fastapi import BackgroundTasks


@router.post("/send-notification")
async def send_notification(
    background_tasks: BackgroundTasks, notification: NotificationCreate
):
    # Queue the notification for background processing
    background_tasks.add_task(send_notification_task, notification)
    return {"status": "Notification queued"}
```

## References

- [FastAPI Documentation](mdc:https:/fastapi.tiangolo.com)
- [Pydantic Documentation](mdc:https:/docs.pydantic.dev)
- [SQLAlchemy Documentation](mdc:https:/docs.sqlalchemy.org)

## 📦 Request/Response Schemas

- All request and response models **must** inherit from `pydantic.BaseModel`.
- Request and response models **must** be defined in `app/schemas/`, not inline in route files.
- Every field in a schema should include `example=...` in the `Field(...)` definition to improve OpenAPI docs.
- Use `Field(..., description=...)` to explain the purpose of non-obvious fields.
- **Enum fields must always serialize as `.value` (not names or integers) in API responses.**

### Additional Guidelines for Skirmish

- Always raise `HTTPException` with structured error response.
- Never return `None` — always define and use a proper `response_model`.
- Use tags, summaries, and response descriptions to auto-document OpenAPI output.
- v1 of the Agent API is a compatibility layer that **must** maintain perfect compatibility with [swagger.json](mdc:swagger.json)
