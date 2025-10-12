# API Reference

This document provides detailed specifications for all Ouroboros APIs.

## API Versioning

Ouroboros provides three distinct APIs:

1. **Agent API** (`/api/v1/client/*`)

   - Used by distributed agents
   - OpenAPI 3.0.1 specification
   - Bearer token authentication (`csa_` prefix)

2. **Web UI API** (`/api/v1/web/*`)

   - Powers the SvelteKit-based interface
   - JWT-based authentication with HTTP-only cookies
   - Real-time updates via Server-Sent Events

3. **Control API** (`/api/v1/control/*`)

   - Command-line and automation interface
   - API key authentication (`cst_` prefix)
   - RFC9457 compliant error responses

## Agent API (`/api/v1/client/*`)

### Authentication

#### Authenticate Agent

```http
GET /api/v1/client/authenticate
Authorization: Bearer csa_<agent_id>_<token>

Response:
{
    "authenticated": true,
    "agent_id": 123
}
```

#### Get Configuration

```http
GET /api/v1/client/configuration
Authorization: Bearer csa_<agent_id>_<token>

Response:
{
    "config": {
        "use_native_hashcat": false,
        "backend_ignore_cuda": false,
        "backend_ignore_hip": false,
        "backend_ignore_metal": false,
        "backend_ignore_opencl": false,
        "opencl_device_types": ["1", "2", "3"],
        "workload_profile": "3",
        "hwmon_temp_abort": 90
    },
    "api_version": 1
}
```

### Agent Management

#### Register Agent

```http
POST /api/v1/client/agents/register
Content-Type: application/json

{
    "name": "agent1",
    "operating_system": "Linux",
    "devices": ["NVIDIA GeForce RTX 3080", "Intel Core i7-9700K"],
    "client_signature": "Ouroboros-Agent/1.0.0"
}

Response:
{
    "agent_id": 123,
    "token": "csa_123_abcdef123456"
}
```

#### Submit Heartbeat

```http
POST /api/v1/client/agents/heartbeat
Authorization: Bearer csa_123_abcdef123456
Content-Type: application/json

{
    "state": "active"
}

Response:
{
    "command": "continue",
    "next_heartbeat_in": 60
}
```

#### Submit Benchmark

```http
POST /api/v1/client/agents/benchmark
Authorization: Bearer csa_123_abcdef123456
Content-Type: application/json

{
    "benchmark_data": {
        "hash_type": 0,
        "device": "NVIDIA GeForce RTX 3080",
        "speed": 1234567890
    }
}

Response:
{
    "acknowledged": true
}
```

### Task Management

#### Get Available Task

```http
GET /api/v1/client/tasks/new
Authorization: Bearer csa_123_abcdef123456

Response:
{
    "task_id": 456,
    "attack_id": 789,
    "hash_list_url": "https://storage.example.com/hashlists/abc123",
    "attack_config": {
        "attack_mode": 0,
        "hash_type": 0,
        "mask": "?a?a?a?a?a?a?a?a",
        "wordlist_url": "https://storage.example.com/wordlists/rockyou.txt"
    },
    "keyspace_start": 0,
    "keyspace_limit": 1000000
}
```

#### Submit Task Status

```http
POST /api/v1/client/tasks/456/status
Authorization: Bearer csa_123_abcdef123456
Content-Type: application/json

{
    "status": "running",
    "progress": 45.5,
    "speed": 1234567,
    "eta": 3600,
    "device_statuses": [
        {
            "device_id": 0,
            "device_name": "NVIDIA GeForce RTX 3080",
            "speed": 1234567,
            "utilization": 95.2,
            "temperature": 75
        }
    ]
}

Response:
{
    "command": "continue"
}
```

#### Submit Crack Results

```http
POST /api/v1/client/tasks/456/crack
Authorization: Bearer csa_123_abcdef123456
Content-Type: application/json

{
    "results": [
        {
            "hash": "5f4dcc3b5aa765d61d8327deb882cf99",
            "plaintext": "password123"
        }
    ]
}

Response:
{
    "acknowledged": true
}
```

## Web UI API (`/api/v1/web/*`)

### Authentication

#### Login

```http
POST /api/v1/web/auth/login
Content-Type: application/x-www-form-urlencoded

email=admin@example.com&password=secure_password

Response:
Set-Cookie: access_token=jwt_token; HttpOnly; Secure
{
    "message": "Login successful.",
    "level": "success"
}
```

#### Get Current User

```http
GET /api/v1/web/auth/me
Cookie: access_token=jwt_token

Response:
{
    "id": 1,
    "name": "Administrator",
    "email": "admin@example.com",
    "role": "admin",
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z"
}
```

#### Get User Context

```http
GET /api/v1/web/auth/context
Cookie: access_token=jwt_token; active_project_id=123

Response:
{
    "user": {
        "id": 1,
        "name": "Administrator",
        "email": "admin@example.com",
        "role": "admin"
    },
    "active_project": {
        "id": 123,
        "name": "Security Audit 2024",
        "description": "Annual security audit project"
    },
    "available_projects": [
        {
            "id": 123,
            "name": "Security Audit 2024"
        },
        {
            "id": 124,
            "name": "Penetration Test"
        }
    ]
}
```

### Campaign Management

#### List Campaigns

```http
GET /api/v1/web/campaigns?page=1&per_page=10&search=audit
Cookie: access_token=jwt_token; active_project_id=123

Response:
{
    "items": [
        {
            "id": 456,
            "name": "Password Audit 2024",
            "description": "Annual password audit",
            "state": "active",
            "progress": 45.5,
            "hash_list": {
                "id": 789,
                "name": "Domain Hashes"
            },
            "attacks_count": 3,
            "created_at": "2024-03-15T10:00:00Z"
        }
    ],
    "total": 15,
    "page": 1,
    "per_page": 10,
    "pages": 2
}
```

#### Create Campaign

```http
POST /api/v1/web/campaigns
Cookie: access_token=jwt_token; active_project_id=123
Content-Type: application/json

{
    "name": "Password Audit 2024",
    "description": "Annual password audit",
    "hash_list_id": 789
}

Response:
{
    "id": 456,
    "name": "Password Audit 2024",
    "description": "Annual password audit",
    "state": "draft",
    "hash_list": {
        "id": 789,
        "name": "Domain Hashes"
    },
    "created_at": "2024-03-15T10:00:00Z"
}
```

#### Get Campaign Details

```http
GET /api/v1/web/campaigns/456
Cookie: access_token=jwt_token; active_project_id=123

Response:
{
    "id": 456,
    "name": "Password Audit 2024",
    "description": "Annual password audit",
    "state": "active",
    "progress": 45.5,
    "hash_list": {
        "id": 789,
        "name": "Domain Hashes",
        "total_hashes": 10000,
        "cracked_hashes": 4550
    },
    "attacks": [
        {
            "id": 101,
            "name": "Dictionary Attack",
            "attack_mode": 0,
            "position": 1,
            "state": "completed",
            "progress": 100.0,
            "keyspace": 14344384,
            "complexity_score": 2,
            "comment": "Common passwords"
        },
        {
            "id": 102,
            "name": "Mask Attack",
            "attack_mode": 3,
            "position": 2,
            "state": "running",
            "progress": 45.5,
            "keyspace": 208827064576,
            "complexity_score": 4,
            "comment": "8-character patterns"
        }
    ],
    "created_at": "2024-03-15T10:00:00Z"
}
```

### Attack Management

#### Create Attack

```http
POST /api/v1/web/attacks
Cookie: access_token=jwt_token; active_project_id=123
Content-Type: application/json

{
    "campaign_id": 456,
    "name": "Dictionary Attack",
    "attack_mode": 0,
    "hash_type": 0,
    "wordlist_id": "abc123",
    "rule_list_id": "def456",
    "comment": "Common passwords attack"
}

Response:
{
    "id": 101,
    "name": "Dictionary Attack",
    "attack_mode": 0,
    "state": "pending",
    "position": 1,
    "keyspace": 14344384,
    "complexity_score": 2,
    "comment": "Common passwords attack"
}
```

#### Validate Attack Configuration

```http
POST /api/v1/web/attacks/validate
Cookie: access_token=jwt_token; active_project_id=123
Content-Type: application/json

{
    "attack_mode": 0,
    "hash_type": 0,
    "wordlist_id": "abc123",
    "rule_list_id": "def456"
}

Response:
{
    "valid": true,
    "keyspace": 14344384,
    "complexity_score": 2,
    "estimated_runtime": "2 hours 15 minutes"
}
```

### Resource Management

#### List Resources

```http
GET /api/v1/web/resources?type=word_list&page=1&per_page=10
Cookie: access_token=jwt_token; active_project_id=123

Response:
{
    "items": [
        {
            "id": "abc123",
            "name": "rockyou.txt",
            "resource_type": "word_list",
            "file_size": 139921507,
            "line_count": 14344384,
            "checksum": "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8",
            "created_at": "2024-03-15T10:00:00Z"
        }
    ],
    "total": 25,
    "page": 1,
    "per_page": 10,
    "pages": 3
}
```

#### Upload Resource

```http
POST /api/v1/web/resources
Cookie: access_token=jwt_token; active_project_id=123
Content-Type: application/json

{
    "name": "custom_wordlist.txt",
    "resource_type": "word_list",
    "description": "Custom wordlist for this project"
}

Response:
{
    "resource_id": "xyz789",
    "upload_url": "https://storage.example.com/upload/xyz789?signature=...",
    "expires_at": "2024-03-15T11:00:00Z"
}
```

### Agent Management

#### List Agents

```http
GET /api/v1/web/agents?page=1&per_page=10&state=active
Cookie: access_token=jwt_token; active_project_id=123

Response:
{
    "items": [
        {
            "id": 123,
            "name": "agent1",
            "display_name": "GPU Workstation",
            "operating_system": "Linux",
            "state": "active",
            "last_seen": "2024-03-15T10:55:00Z",
            "current_task": {
                "id": 456,
                "campaign_name": "Password Audit 2024",
                "attack_name": "Dictionary Attack"
            },
            "performance": {
                "current_speed": 1234567,
                "average_speed": 1200000,
                "temperature": 75,
                "utilization": 95.2
            }
        }
    ],
    "total": 5,
    "page": 1,
    "per_page": 10,
    "pages": 1
}
```

#### Get Agent Details

```http
GET /api/v1/web/agents/123
Cookie: access_token=jwt_token; active_project_id=123

Response:
{
    "id": 123,
    "name": "agent1",
    "display_name": "GPU Workstation",
    "operating_system": "Linux",
    "state": "active",
    "enabled": true,
    "last_seen": "2024-03-15T10:55:00Z",
    "devices": [
        "NVIDIA GeForce RTX 3080",
        "Intel Core i7-9700K"
    ],
    "configuration": {
        "use_native_hashcat": false,
        "backend_ignore_cuda": false,
        "update_interval": 10
    },
    "current_task": {
        "id": 456,
        "campaign_name": "Password Audit 2024",
        "attack_name": "Dictionary Attack",
        "progress": 45.5
    }
}
```

### Hash List Management

#### List Hash Lists

```http
GET /api/v1/web/hash_lists?page=1&per_page=10
Cookie: access_token=jwt_token; active_project_id=123

Response:
{
    "items": [
        {
            "id": 789,
            "name": "Domain Hashes",
            "description": "Active Directory password hashes",
            "hash_count": 10000,
            "cracked_count": 4550,
            "hash_type": 1000,
            "created_at": "2024-03-15T09:00:00Z"
        }
    ],
    "total": 3,
    "page": 1,
    "per_page": 10,
    "pages": 1
}
```

#### Create Hash List

```http
POST /api/v1/web/hash_lists
Cookie: access_token=jwt_token; active_project_id=123
Content-Type: application/json

{
    "name": "Domain Hashes",
    "description": "Active Directory password hashes",
    "hash_type": 1000
}

Response:
{
    "id": 789,
    "name": "Domain Hashes",
    "description": "Active Directory password hashes",
    "hash_count": 0,
    "cracked_count": 0,
    "hash_type": 1000,
    "created_at": "2024-03-15T09:00:00Z"
}
```

### Real-Time Updates (Server-Sent Events)

#### Campaign Updates

```http
GET /api/v1/web/live/campaigns
Cookie: access_token=jwt_token; active_project_id=123
Accept: text/event-stream

Response (SSE Stream):
data: {"trigger": "refresh", "timestamp": "2024-03-15T10:55:00Z"}

data: {"trigger": "refresh", "target": "campaign", "id": 456, "timestamp": "2024-03-15T10:56:00Z"}
```

#### Agent Updates

```http
GET /api/v1/web/live/agents
Cookie: access_token=jwt_token; active_project_id=123
Accept: text/event-stream

Response (SSE Stream):
data: {"trigger": "refresh", "timestamp": "2024-03-15T10:55:00Z"}

data: {"trigger": "refresh", "target": "agent", "id": 123, "timestamp": "2024-03-15T10:56:00Z"}
```

### Crackable Uploads

#### Upload File or Hash Data

```http
POST /api/v1/web/uploads
Cookie: access_token=jwt_token; active_project_id=123
Content-Type: application/json

{
    "name": "shadow_file",
    "content_type": "text/plain",
    "hash_data": "user1:$6$salt$hash...\nuser2:$6$salt$hash..."
}

Response:
{
    "upload_id": "upload123",
    "status": "processing",
    "estimated_completion": "2024-03-15T11:05:00Z"
}
```

#### Check Upload Status

```http
GET /api/v1/web/uploads/upload123/status
Cookie: access_token=jwt_token; active_project_id=123

Response:
{
    "upload_id": "upload123",
    "status": "completed",
    "detected_hash_type": {
        "mode": 1800,
        "name": "sha512crypt",
        "confidence": 0.95
    },
    "extracted_hashes": 150,
    "preview": [
        "$6$salt$hash1...",
        "$6$salt$hash2...",
        "$6$salt$hash3..."
    ]
}
```

## Control API (`/api/v1/control/*`)

### Authentication

Control API uses API key authentication with `cst_` prefixed tokens.

```http
Authorization: Bearer cst_<user_id>_<token>
```

### Campaign Operations

#### List Campaigns

```http
GET /api/v1/control/campaigns
Authorization: Bearer cst_user123_xyz789

Response:
{
    "campaigns": [
        {
            "id": 456,
            "name": "Password Audit 2024",
            "state": "active",
            "progress": 45.5,
            "project": {
                "id": 123,
                "name": "Security Audit 2024"
            }
        }
    ]
}
```

### Hash Analysis

#### Guess Hash Type

```http
POST /api/v1/control/hash/guess
Authorization: Bearer cst_user123_xyz789
Content-Type: application/json

{
    "hash_string": "$6$salt$hash..."
}

Response:
{
    "results": [
        {
            "mode": 1800,
            "name": "sha512crypt",
            "confidence": 0.95,
            "description": "Unix SHA-512 crypt"
        }
    ],
    "most_likely": {
        "mode": 1800,
        "name": "sha512crypt",
        "confidence": 0.95
    }
}
```

## Error Responses

### Agent API Errors

```json
{
  "error": "Bad credentials"
}
```

### Web UI API Errors

```json
{
  "detail": "Campaign not found"
}
```

### Control API Errors (RFC9457)

```json
{
  "type": "https://ouroboros.example.com/problems/validation-error",
  "title": "Validation Error",
  "status": 422,
  "detail": "The hash string format is invalid",
  "instance": "/api/v1/control/hash/guess"
}
```

## Common Response Patterns

### Paginated Responses

```json
{
  "items": [],
  "total": 100,
  "page": 1,
  "per_page": 10,
  "pages": 10
}
```

### Success Responses

```json
{
  "message": "Operation completed successfully",
  "level": "success"
}
```

### Validation Errors

```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": [
        "body",
        "name"
      ],
      "msg": "String should have at least 1 character",
      "input": ""
    }
  ]
}
```
