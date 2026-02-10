# Instinct: RFC9457 Error Responses

**Confidence**: 100% **Source**: Control API implementation, design specs **Category**: api-design

## Pattern

Control API errors must return `application/problem+json` format per RFC9457:

```python
{
    "type": "https://example.com/problems/invalid-request",
    "title": "Invalid Request",
    "status": 400,
    "detail": "The request parameters are invalid",
    "instance": "/api/v1/control/campaigns/123",
}
```

### Extension Fields

Add context-specific extension fields:

```python
# For state transition errors
{
    "type": "...",
    "title": "Invalid State Transition",
    "status": 409,
    "detail": "Cannot start campaign from COMPLETED state",
    "instance": "/api/v1/control/campaigns/123/start",
    "current_state": "COMPLETED",
    "valid_actions": ["archive"],  # What CAN be done
}

# For validation errors
{
    "type": "...",
    "title": "Validation Error",
    "status": 422,
    "detail": "Request validation failed",
    "instance": "/api/v1/control/campaigns",
    "errors": [
        {"field": "name", "message": "Field is required"},
    ],
}
```

## Middleware Implementation

Use `app/core/control_rfc9457_middleware.py` for automatic exception translation.

## Trigger

Activate when:

- Implementing Control API endpoints
- Handling errors in Control API
- Adding new exception types for Control API
