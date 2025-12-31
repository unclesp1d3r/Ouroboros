# API Error Response Reference

This document provides comprehensive documentation for error responses across all Ouroboros API interfaces, including status codes, response formats, and troubleshooting guidance.

## Error Response Formats

### Agent API v1 (Legacy Format)

The Agent API uses a simple error object format for backward compatibility:

```json
{
  "error": "Human readable error message"
}
```

**Content-Type:** `application/json`

### Web UI API (FastAPI Standard)

The Web UI API uses FastAPI's standard error format:

```json
{
  "detail": "Human readable error message"
}
```

For validation errors, the response includes field-specific details:

```json
{
  "detail": [
    {
      "loc": [
        "field_name"
      ],
      "msg": "Field validation error",
      "type": "value_error"
    }
  ]
}
```

**Content-Type:** `application/json`

### Control API (RFC9457 Problem Details)

The Control API implements [RFC9457](https://datatracker.ietf.org/doc/html/rfc9457) Problem Details format:

```json
{
  "type": "https://ouroboros.example.com/problems/validation-error",
  "title": "Validation Error",
  "status": 422,
  "detail": "The request contains invalid data",
  "instance": "/api/v1/control/campaigns/123",
  "errors": [
    {
      "field": "name",
      "message": "Campaign name is required",
      "code": "required"
    }
  ]
}
```

**Content-Type:** `application/problem+json`

## HTTP Status Codes

### 2xx Success Codes

| Code | Name       | Usage                                    | APIs            | Examples                            |
| ---- | ---------- | ---------------------------------------- | --------------- | ----------------------------------- |
| 200  | OK         | Successful request with response body    | All             | GET requests, successful operations |
| 201  | Created    | Resource successfully created            | Web UI, Control | POST /campaigns/, POST /hash_lists/ |
| 202  | Accepted   | Request accepted for async processing    | Web UI, Control | File uploads, bulk operations       |
| 204  | No Content | Successful request with no response body | All             | DELETE operations, heartbeats       |

### 4xx Client Error Codes

#### 400 Bad Request

**When:** Request is malformed or contains invalid syntax

**Common Causes:**

- Malformed JSON in request body
- Invalid query parameters
- Missing required headers
- Incorrect Content-Type header

**Agent API Example:**

```json
{
  "error": "Invalid JSON in request body"
}
```

**Web UI API Example:**

```json
{
  "detail": "Request body must be valid JSON"
}
```

**Control API Example:**

```json
{
  "type": "https://ouroboros.example.com/problems/bad-request",
  "title": "Bad Request",
  "status": 400,
  "detail": "Request body contains malformed JSON",
  "instance": "/api/v1/control/campaigns",
  "invalid_fields": [
    "campaign_data"
  ]
}
```

#### 401 Unauthorized

**When:** Authentication is required but not provided or invalid

**Common Causes:**

- Missing `Authorization` header
- Invalid token format
- Expired token
- Revoked token

**Agent API Example:**

```json
{
  "error": "Bad credentials"
}
```

**Web UI API Example:**

```json
{
  "detail": "Could not validate credentials"
}
```

**Control API Example:**

```json
{
  "type": "unauthorized",
  "title": "Unauthorized",
  "status": 401,
  "detail": "Valid API key required",
  "instance": "/api/v1/control/campaigns"
}
```

#### 403 Forbidden

**When:** Authentication succeeded but insufficient permissions

**Common Causes:**

- User lacks required role (admin operations)
- Project access denied
- Resource not owned by user
- Agent not authorized for resource

**Agent API Example:**

```json
{
  "error": "Agent not authorized to access this attack"
}
```

**Web UI API Example:**

```json
{
  "detail": "Insufficient permissions for this operation"
}
```

**Control API Example:**

```json
{
  "type": "forbidden",
  "title": "Forbidden",
  "status": 403,
  "detail": "Admin role required for this operation",
  "instance": "/api/v1/control/users/456"
}
```

#### 404 Not Found

**When:** Requested resource does not exist

**Agent API Example:**

```json
{
  "error": "Task with ID 12345 not found"
}
```

**Web UI API Example:**

```json
{
  "detail": "Campaign not found"
}
```

**Control API Example:**

```json
{
  "type": "not-found",
  "title": "Not Found",
  "status": 404,
  "detail": "Campaign with ID 12345 does not exist",
  "instance": "/api/v1/control/campaigns/12345"
}
```

#### 409 Conflict

**When:** Request conflicts with current resource state

**Common Causes:**

- Campaign already started
- Resource in use (cannot delete)
- Duplicate resource name
- Invalid state transition

**Agent API Example:**

```json
{
  "error": "Task is already completed"
}
```

**Web UI API Example:**

```json
{
  "detail": "Campaign name already exists in this project"
}
```

**Control API Example:**

```json
{
  "type": "resource-conflict",
  "title": "Resource Conflict",
  "status": 409,
  "detail": "Cannot delete resource that is currently in use by active campaigns",
  "instance": "/api/v1/control/resources/789",
  "conflicting_resources": [
    {
      "type": "campaign",
      "id": 123,
      "name": "Active Campaign"
    }
  ]
}
```

#### 422 Unprocessable Entity

**When:** Request is well-formed but contains semantic errors

**Agent API Example:**

```json
{
  "error": "Invalid benchmark data: hash_speed must be a positive number"
}
```

**Web UI API Example:**

```json
{
  "detail": [
    {
      "loc": [
        "hash_speed"
      ],
      "msg": "ensure this value is greater than 0",
      "type": "value_error.number.not_gt",
      "ctx": {
        "limit_value": 0
      }
    }
  ]
}
```

**Control API Example:**

```json
{
  "type": "validation-error",
  "title": "Validation Error",
  "status": 422,
  "detail": "Request contains invalid field values",
  "instance": "/api/v1/control/campaigns",
  "errors": [
    {
      "field": "hash_list_id",
      "message": "Hash list ID must be a positive integer",
      "code": "invalid_type",
      "value": "abc"
    },
    {
      "field": "name",
      "message": "Campaign name cannot be empty",
      "code": "required"
    }
  ]
}
```

#### 429 Too Many Requests

**When:** Rate limit exceeded

**Agent API Example:**

```json
{
  "error": "Too many heartbeat requests. Maximum 1 request per 15 seconds"
}
```

**Web UI API Example:**

```json
{
  "detail": "Rate limit exceeded. Please try again later"
}
```

**Control API Example:**

```json
{
  "type": "rate-limit-exceeded",
  "title": "Rate Limit Exceeded",
  "status": 429,
  "detail": "API key has exceeded the allowed request rate",
  "instance": "/api/v1/control/campaigns",
  "retry_after": 60
}
```

### 5xx Server Error Codes

#### 500 Internal Server Error

**When:** Unexpected server error occurred

**All APIs Example:**

```json
{
  "error": "Internal server error occurred"
}
```

**Note:** Server errors never expose internal details, stack traces, or sensitive information to clients. Full error details are logged server-side for debugging.

#### 503 Service Unavailable

**When:** Service is temporarily unavailable

**Common Causes:**

- Database connection issues
- Redis/cache unavailable
- MinIO storage unavailable
- System maintenance

**Control API Example:**

```json
{
  "type": "service-unavailable",
  "title": "Service Unavailable",
  "status": 503,
  "detail": "Database service is temporarily unavailable",
  "instance": "/api/v1/control/campaigns",
  "retry_after": 30
}
```

## Error Handling Best Practices

### For API Clients

1. **Always check status codes** before processing response data
2. **Implement retry logic** with exponential backoff for 5xx errors
3. **Handle rate limiting** by respecting `retry_after` headers
4. **Log errors appropriately** without exposing sensitive data
5. **Provide user-friendly messages** based on error types

### Example Error Handling (Python)

```python
import requests
import time
from typing import Optional


class CipherSwarmAPIError(Exception):
    def __init__(self, status_code: int, message: str, response_data: dict = None):
        self.status_code = status_code
        self.message = message
        self.response_data = response_data or {}
        super().__init__(f"API Error {status_code}: {message}")


def make_api_request(
    url: str, headers: dict, data: dict = None, max_retries: int = 3
) -> dict:
    """Make API request with proper error handling and retries."""

    for attempt in range(max_retries):
        try:
            if data:
                response = requests.post(url, headers=headers, json=data)
            else:
                response = requests.get(url, headers=headers)

            # Handle different status codes
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 204:
                return {}
            elif response.status_code == 401:
                raise CipherSwarmAPIError(401, "Authentication failed", response.json())
            elif response.status_code == 403:
                raise CipherSwarmAPIError(403, "Access denied", response.json())
            elif response.status_code == 404:
                raise CipherSwarmAPIError(404, "Resource not found", response.json())
            elif response.status_code == 409:
                raise CipherSwarmAPIError(409, "Resource conflict", response.json())
            elif response.status_code == 422:
                error_data = response.json()
                raise CipherSwarmAPIError(422, "Validation error", error_data)
            elif response.status_code == 429:
                # Rate limited - implement backoff
                retry_after = int(response.headers.get("Retry-After", 60))
                if attempt < max_retries - 1:
                    time.sleep(retry_after)
                    continue
                raise CipherSwarmAPIError(429, "Rate limit exceeded", response.json())
            elif response.status_code >= 500:
                # Server error - retry with backoff
                if attempt < max_retries - 1:
                    delay = (2**attempt) + random.uniform(0, 1)
                    time.sleep(delay)
                    continue
                raise CipherSwarmAPIError(
                    response.status_code, "Server error", response.json()
                )
            else:
                raise CipherSwarmAPIError(
                    response.status_code, "Unexpected error", response.json()
                )

        except requests.RequestException as e:
            if attempt < max_retries - 1:
                time.sleep(2**attempt)
                continue
            raise CipherSwarmAPIError(0, f"Network error: {e}")

    raise CipherSwarmAPIError(0, "Max retries exceeded")
```

## Troubleshooting Guide

### Common Issues and Solutions

#### Authentication Issues

**Problem:** `401 Unauthorized` responses **Solutions:**

1. Verify token format matches expected pattern
2. Check token hasn't expired
3. Ensure `Authorization` header is properly formatted
4. Verify agent is registered and active

#### Rate Limiting Issues

**Problem:** `429 Too Many Requests` responses **Solutions:**

1. Implement exponential backoff
2. Reduce request frequency
3. Check for request loops or excessive polling
4. Contact administrator if limits seem too restrictive

#### Validation Errors

**Problem:** `422 Unprocessable Entity` responses **Solutions:**

1. Check required fields are present
2. Verify field types and formats
3. Ensure enum values are valid
4. Check field constraints (min/max values)

#### Resource Not Found

**Problem:** `404 Not Found` responses **Solutions:**

1. Verify resource ID is correct
2. Check resource hasn't been deleted
3. Ensure user has access to the resource
4. Verify project context is correct

#### Server Errors

**Problem:** `500 Internal Server Error` responses **Solutions:**

1. Retry the request after a delay
2. Check system status page
3. Contact system administrator
4. Report persistent errors with request details

### Debugging Tips

1. **Enable request logging** to see full HTTP requests/responses
2. **Check response headers** for additional error information
3. **Verify API endpoint URLs** are correct and properly formatted
4. **Test with minimal payloads** to isolate validation issues
5. **Use API documentation examples** as reference implementations
