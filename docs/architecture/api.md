# API Documentation

Ouroboros provides four distinct API interfaces, each serving different client types with specific authentication and error handling requirements:

1. **Agent API** (`/api/v1/client/*`) - For distributed agents
2. **Web UI API** (`/api/v1/web/*`) - For the SvelteKit dashboard
3. **Control API** (`/api/v1/control/*`) - For TUI/CLI clients
4. **Shared Infrastructure API** (`/api/v1/*`) - Common endpoints

## Agent API (`/api/v1/client/*`)

The Agent API follows the OpenAPI 3.0.1 specification defined in `contracts/v1_api_swagger.json` and is locked for backward compatibility.

### Authentication

Agents use bearer token authentication with tokens in the format `csa_{agent_id}_{random_string}`.

```http
POST /api/v1/client/authenticate
Content-Type: application/json

{
    "name": "agent1",
    "operating_system": "Linux",
    "devices": ["NVIDIA GeForce RTX 3080", "Intel Core i7-9700K"]
}

Response:
{
    "token": "csa_550e8400-e29b-41d4-a716-446655440000_abcdef123456"
}
```

### Agent Management

```http
GET /api/v1/client/agents/heartbeat
Authorization: Bearer csa_550e8400-e29b-41d4-a716-446655440000_abcdef123456

Response:
{
    "config": {
        "agent_update_interval": 30,
        "backend_device": "1,2",
        "opencl_devices": "1,2",
        "use_native_hashcat": false
    }
}
```

### Task Management

```http
GET /api/v1/client/tasks/next
Authorization: Bearer csa_550e8400-e29b-41d4-a716-446655440000_abcdef123456

Response:
{
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "attack_id": "987fcdeb-51d2-11e9-8647-d663bd873d93",
    "attack_mode": 0,
    "hash_list_url": "https://storage.example.com/tasks/123/hashes.txt",
    "wordlist_url": "https://storage.example.com/wordlists/rockyou.txt",
    "rules_url": "https://storage.example.com/rules/best64.rule"
}
```

### Progress Reporting

```http
POST /api/v1/client/tasks/{task_id}/status
Authorization: Bearer csa_550e8400-e29b-41d4-a716-446655440000_abcdef123456
Content-Type: application/json

{
    "status": "running",
    "progress": 45.5,
    "device_statuses": [
        {
            "device_id": 1,
            "device_name": "NVIDIA GeForce RTX 3080",
            "speed": 1234567,
            "utilization": 95,
            "temperature": 75
        }
    ]
}
```

## Web UI API (`/api/v1/web/*`)

The Web UI API powers the SvelteKit dashboard with comprehensive campaign, attack, and resource management capabilities.

### Authentication

Web users authenticate with JWT tokens that include refresh token support.

```http
POST /api/v1/web/auth/login
Content-Type: application/json

{
    "username": "admin@example.com",
    "password": "secure_password"
}

Response:
{
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer",
    "expires_in": 3600
}
```

### Project Context

Users can switch between projects they have access to:

```http
GET /api/v1/web/auth/context
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...

Response:
{
    "user": {
        "id": "user123",
        "email": "admin@example.com",
        "role": "admin"
    },
    "current_project": {
        "id": "proj456",
        "name": "Security Assessment 2024"
    },
    "available_projects": [
        {"id": "proj456", "name": "Security Assessment 2024"},
        {"id": "proj789", "name": "Penetration Test"}
    ]
}
```

### Campaign Management

```http
GET /api/v1/web/campaigns/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
?page=1&size=20&search=test&state=active

Response:
{
    "items": [
        {
            "id": "camp123",
            "name": "Test Campaign",
            "state": "active",
            "hash_list": {
                "id": "hash456",
                "name": "Corporate Hashes",
                "total_hashes": 1000,
                "cracked_hashes": 150
            },
            "attacks": [
                {
                    "id": "att789",
                    "name": "Dictionary Attack",
                    "attack_mode": 0,
                    "status": "running",
                    "progress": 45.5,
                    "position": 1
                }
            ],
            "created_at": "2024-01-01T12:00:00Z"
        }
    ],
    "total": 1,
    "page": 1,
    "size": 20,
    "pages": 1
}
```

### Attack Configuration

```http
POST /api/v1/web/attacks/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
Content-Type: application/json

{
    "name": "Dictionary Attack",
    "attack_mode": 0,
    "campaign_id": "camp123",
    "wordlist_id": "word456",
    "rule_list_id": "rule789",
    "min_password_length": 8,
    "max_password_length": 32,
    "comment": "Standard dictionary attack with best64 rules"
}

Response:
{
    "id": "att789",
    "name": "Dictionary Attack",
    "status": "pending",
    "keyspace_estimate": 14344384000,
    "complexity_score": 3,
    "position": 1
}
```

### Resource Management

```http
GET /api/v1/web/resources/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
?resource_type=word_list&search=rockyou

Response:
{
    "items": [
        {
            "id": "res123",
            "name": "rockyou.txt",
            "resource_type": "word_list",
            "file_size": 139921497,
            "line_count": 14344384,
            "checksum": "3f3a1c2d5e6b7890",
            "created_at": "2024-01-01T12:00:00Z",
            "can_edit": true
        }
    ],
    "total": 1,
    "page": 1,
    "size": 20
}
```

### Line-Oriented Resource Editing

```http
GET /api/v1/web/resources/{id}/lines
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
?page=1&size=50&validate=true

Response:
{
    "lines": [
        {
            "id": 1,
            "index": 0,
            "content": "?l?l?l?l?l?l?l?l",
            "valid": true,
            "error_message": null
        },
        {
            "id": 2,
            "index": 1,
            "content": "?u?l?l?l?l?l?l?l",
            "valid": true,
            "error_message": null
        }
    ],
    "total": 1000,
    "page": 1,
    "size": 50
}
```

### Agent Monitoring

```http
GET /api/v1/web/agents/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...

Response:
{
    "items": [
        {
            "id": "agent123",
            "display_name": "Mining Rig 01",
            "host_name": "mining-01.local",
            "operating_system": "Linux",
            "status": "active",
            "last_seen": "2024-01-01T12:00:00Z",
            "current_task": {
                "id": "task456",
                "campaign_name": "Test Campaign",
                "attack_name": "Dictionary Attack"
            },
            "performance": {
                "current_speed": 1234567,
                "average_speed": 1200000,
                "utilization": 95,
                "temperature": 75
            }
        }
    ],
    "total": 1,
    "page": 1,
    "size": 20
}
```

### Hash List Management

```http
POST /api/v1/web/hash_lists/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
Content-Type: application/json

{
    "name": "Corporate Hashes",
    "description": "Hashes from corporate domain controller",
    "hash_mode": 1000,
    "separator": ":"
}

Response:
{
    "id": "hash123",
    "name": "Corporate Hashes",
    "hash_mode": 1000,
    "total_hashes": 0,
    "cracked_hashes": 0,
    "created_at": "2024-01-01T12:00:00Z"
}
```

### Crackable Uploads

```http
POST /api/v1/web/uploads/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
Content-Type: multipart/form-data

file: <uploaded_file>
name: "NTDS.dit Extract"
description: "Domain controller hash dump"

Response:
{
    "id": "upload123",
    "status": "processing",
    "estimated_hashes": 1500,
    "detected_hash_types": [
        {
            "mode": 1000,
            "name": "NTLM",
            "confidence": 0.95
        }
    ]
}
```

## Real-time Updates (SSE)

Server-Sent Events provide real-time notifications to web clients without the complexity of WebSockets.

### Campaign Updates

```http
GET /api/v1/web/live/campaigns
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
Accept: text/event-stream

# SSE Messages
data: {"trigger": "refresh", "timestamp": "2024-01-01T12:00:00Z"}

data: {"trigger": "refresh", "target": "campaign", "id": "camp123"}
```

### Agent Status Updates

```http
GET /api/v1/web/live/agents
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
Accept: text/event-stream

# SSE Messages
data: {"trigger": "refresh", "timestamp": "2024-01-01T12:00:00Z"}

data: {"trigger": "refresh", "target": "agent", "id": "agent123"}
```

### Toast Notifications

```http
GET /api/v1/web/live/toasts
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
Accept: text/event-stream

# SSE Messages
data: {"message": "Hash cracked: admin:password123", "type": "success", "timestamp": "2024-01-01T12:00:00Z"}

data: {"message": "Agent mining-01 disconnected", "type": "warning", "timestamp": "2024-01-01T12:01:00Z"}
```

## Control API (`/api/v1/control/*`)

The Control API provides a command-line interface with RFC9457-compliant error responses.

### Authentication

TUI clients use API key authentication with tokens in the format `cst_{user_id}_{random_string}`.

```http
POST /api/v1/control/auth/token
Content-Type: application/json

{
    "api_key": "cst_user123_abcdef123456"
}

Response:
{
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer",
    "expires_in": 3600
}
```

### Campaign Operations

```http
GET /api/v1/control/campaigns/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...

Response:
{
    "campaigns": [
        {
            "id": "camp123",
            "name": "Test Campaign",
            "state": "active",
            "progress": 45.5,
            "attacks_count": 3,
            "active_tasks": 5
        }
    ]
}
```

### Hash Type Detection

```http
POST /api/v1/control/hash_guess/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
Content-Type: application/json

{
    "hashes": [
        "5d41402abc4b2a76b9719d911017c592",
        "098f6bcd4621d373cade4e832627b4f6"
    ]
}

Response:
{
    "results": [
        {
            "hash": "5d41402abc4b2a76b9719d911017c592",
            "possible_types": [
                {
                    "mode": 0,
                    "name": "MD5",
                    "confidence": 0.95
                }
            ]
        }
    ]
}
```

### RFC9457 Error Format

Control API errors follow the RFC9457 Problem Details specification:

```http
HTTP/1.1 400 Bad Request
Content-Type: application/problem+json

{
    "type": "https://ouroboros.org/problems/validation-error",
    "title": "Validation Error",
    "status": 400,
    "detail": "The request contains invalid parameters",
    "instance": "/api/v1/control/campaigns/",
    "errors": [
        {
            "field": "name",
            "message": "Campaign name is required"
        }
    ]
}
```

## Shared Infrastructure API

Common endpoints used by multiple API interfaces.

### User Management

```http
GET /api/v1/users/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...

Response:
{
    "items": [
        {
            "id": "user123",
            "email": "admin@example.com",
            "role": "admin",
            "is_active": true,
            "created_at": "2024-01-01T12:00:00Z"
        }
    ],
    "total": 1,
    "page": 1,
    "size": 20
}
```

### Resource Downloads

```http
GET /api/v1/resources/{resource_id}/download
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...

Response:
HTTP/1.1 302 Found
Location: https://storage.example.com/presigned-url-for-resource
```

## Common Response Formats

### Pagination

All list endpoints support consistent pagination:

```json
{
  "items": [],
  "total": 100,
  "page": 1,
  "size": 20,
  "pages": 5
}
```

### Error Responses

#### Web UI API Errors

```http
HTTP/1.1 422 Unprocessable Entity
Content-Type: application/json

{
    "detail": [
        {
            "type": "missing",
            "loc": ["body", "name"],
            "msg": "Field required",
            "input": {}
        }
    ]
}
```

#### Agent API Errors

```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
    "error": "Invalid request parameters"
}
```

#### Control API Errors

```http
HTTP/1.1 404 Not Found
Content-Type: application/problem+json

{
    "type": "https://ouroboros.org/problems/not-found",
    "title": "Resource Not Found",
    "status": 404,
    "detail": "The requested campaign was not found",
    "instance": "/api/v1/control/campaigns/invalid-id"
}
```

## Authentication Summary

| API Interface | Authentication Method | Token Format              | Error Format     |
| ------------- | --------------------- | ------------------------- | ---------------- |
| Agent API     | Bearer Token          | `csa_{agent_id}_{random}` | Legacy JSON      |
| Web UI API    | JWT + Refresh         | Standard JWT              | FastAPI/Pydantic |
| Control API   | API Key               | `cst_{user_id}_{random}`  | RFC9457          |
| Shared API    | JWT                   | Standard JWT              | FastAPI/Pydantic |

## Rate Limiting

All APIs implement rate limiting based on:

- IP address for unauthenticated requests
- User/agent identity for authenticated requests
- Different limits per API interface and endpoint type

## Security Headers

All API responses include security headers:

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Strict-Transport-Security` (HTTPS only)

## API Versioning

- **Agent API v1**: Locked specification, no breaking changes allowed
- **Web UI API**: FastAPI-native, breaking changes allowed with proper versioning
- **Control API**: Independent versioning, RFC9457 compliance required
- **Future versions**: Each API interface versions independently
