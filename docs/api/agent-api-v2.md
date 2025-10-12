# Agent API v2 Documentation

## Overview

Agent API v2 is the modernized interface for Ouroboros agents, providing enhanced features, improved security, and better error handling compared to the legacy v1 API. This API is designed to be forward-compatible and includes significant improvements in authentication, state management, and resource handling.

## Version Information

- **Version**: 2.0.0+
- **Base URL**: `/api/v2/client`
- **Status**: Development Preview
- **Backward Compatibility**: Maintains compatibility with v1 agents

## Key Improvements Over v1

### Enhanced Authentication

- Improved token security with cryptographic validation
- Token expiration and revocation support
- Enhanced authorization checks for resource access

### Better State Management

- Finite state machine implementation for agent lifecycle
- Improved heartbeat system with rate limiting
- Enhanced connection tracking and recovery

### Improved Resource Management

- Time-limited presigned URLs for secure resource access
- Hash verification requirements for downloaded resources
- Forward-compatible resource management for Phase 3

### Enhanced Error Handling

- Structured error responses with detailed information
- Proper HTTP status codes and error categorization
- Comprehensive validation and input sanitization

## Authentication

### Token Format

Agent API v2 uses bearer tokens with the format:

```
csa_<agent_id>_<random_token>
```

### Authentication Header

```http
Authorization: Bearer csa_123_abc123def456...
```

### Token Management

- Tokens are generated during agent registration
- Tokens include expiration and revocation capabilities
- Automatic cleanup of expired tokens
- Usage tracking and monitoring

## API Endpoints

### Agent Management

#### Register Agent

```http
POST /api/v2/client/agents/register
```

**Request Body:**

```json
{
  "signature": "agent_signature_string",
  "hostname": "agent-hostname",
  "agent_type": "hashcat",
  "operating_system": "linux"
}
```

**Response (201 Created):**

```json
{
  "agent_id": 123,
  "token": "csa_123_abc123def456..."
}
```

#### Agent Heartbeat

```http
POST /api/v2/client/agents/heartbeat
```

**Request Body:**

```json
{
  "state": "active"
}
```

**Response (204 No Content)**

**Rate Limiting:** Maximum 1 request per 15 seconds per agent

### Task Management

#### Get Next Task

```http
GET /api/v2/client/agents/tasks/next
```

**Response (200 OK):**

```json
{
  "task_id": 456,
  "attack_id": 789,
  "keyspace_start": 0,
  "keyspace_end": 1000000,
  "hash_file_url": "/api/v2/client/agents/resources/hash123/url",
  "dictionary_ids": [
    1,
    2,
    3
  ]
}
```

**Response (204 No Content):** No tasks available

#### Update Task Progress

```http
POST /api/v2/client/agents/tasks/{task_id}/progress
```

**Request Body:**

```json
{
  "progress_percent": 45.5,
  "keyspace_processed": 455000,
  "estimated_completion": "2024-01-01T12:30:00Z",
  "current_speed": 1500000
}
```

**Response (204 No Content)**

#### Submit Task Results

```http
POST /api/v2/client/agents/tasks/{task_id}/results
```

**Request Body:**

```json
{
  "cracked_hashes": [
    {
      "hash": "5d41402abc4b2a76b9719d911017c592",
      "plaintext": "hello",
      "crack_time": "2024-01-01T12:15:30Z"
    }
  ],
  "task_completed": true,
  "error_message": null
}
```

**Response (200 OK):**

```json
{
  "processed_count": 1,
  "duplicate_count": 0,
  "campaign_updated": true
}
```

### Attack Configuration

#### Get Attack Configuration

```http
GET /api/v2/client/agents/attacks/{attack_id}
```

**Response (200 OK):**

```json
{
  "attack_id": 789,
  "hash_type": 0,
  "attack_mode": 0,
  "mask": null,
  "rules": [
    "best64.rule"
  ],
  "wordlist_ids": [
    1,
    2
  ],
  "charset_ids": [],
  "optimization_level": 2,
  "workload_profile": 3
}
```

### Resource Management

#### Get Resource URL

```http
GET /api/v2/client/agents/resources/{resource_id}/url
```

**Response (200 OK):**

```json
{
  "download_url": "https://minio.example.com/bucket/file?X-Amz-Signature=...",
  "expires_at": "2024-01-01T13:00:00Z",
  "expected_hash": "sha256:abc123...",
  "file_size": 1048576
}
```

## Agent State Machine

### States

- `registered`: Initial state after registration
- `active`: Ready to receive and execute tasks
- `disconnected`: Lost connection, temporary state
- `reconnecting`: Attempting to reconnect
- `retired`: Permanently disabled

### State Transitions

```
registered → active → disconnected → reconnecting → active
                   ↓
                retired
```

### Heartbeat Requirements

- Minimum interval: 15 seconds
- Maximum missed heartbeats: 3
- Automatic state transition to `disconnected` after missed heartbeats

## Error Handling

### Error Response Format

```json
{
  "error": "error_code",
  "message": "Human-readable error message",
  "details": {
    "field": "Additional error context"
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Common Error Codes

#### Authentication Errors (401)

- `invalid_token`: Token is malformed or invalid
- `expired_token`: Token has expired
- `revoked_token`: Token has been revoked

#### Authorization Errors (403)

- `insufficient_permissions`: Agent lacks required permissions
- `resource_access_denied`: Access to specific resource denied
- `agent_disabled`: Agent account is disabled

#### Rate Limiting (429)

- `rate_limit_exceeded`: Too many requests in time window
- `heartbeat_too_frequent`: Heartbeat sent too frequently

#### Validation Errors (422)

- `invalid_input`: Request data validation failed
- `missing_required_field`: Required field not provided
- `invalid_field_format`: Field format is incorrect

#### Resource Errors (404)

- `task_not_found`: Requested task does not exist
- `attack_not_found`: Requested attack does not exist
- `resource_not_found`: Requested resource does not exist

#### Conflict Errors (409)

- `agent_already_registered`: Agent signature already exists
- `task_already_assigned`: Agent already has an active task
- `duplicate_result`: Result already submitted

## Rate Limiting

### Per-Agent Limits

- **Heartbeat**: 1 request per 15 seconds
- **Task Assignment**: 10 requests per minute
- **Progress Updates**: 60 requests per minute
- **Result Submission**: 30 requests per minute

### Global Limits

- **Registration**: 100 requests per hour per IP
- **Resource Access**: 1000 requests per hour per agent

### Rate Limit Headers

```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1640995200
Retry-After: 15
```

## Security Considerations

### Token Security

- Tokens use cryptographically secure random generation
- Tokens are transmitted only over HTTPS
- Tokens include expiration timestamps
- Automatic token rotation on security events

### Resource Protection

- Presigned URLs with time-based expiration
- Hash verification required for all downloads
- IP-based access restrictions where applicable
- Audit logging for all resource access

### Input Validation

- Comprehensive input sanitization
- SQL injection prevention
- XSS protection for any rendered content
- File upload validation and scanning

## Migration from v1

### Compatibility

- v1 and v2 APIs can run simultaneously
- Existing v1 agents continue to work unchanged
- No breaking changes to v1 contract

### Migration Steps

1. Update agent software to support v2 endpoints
2. Test v2 functionality in development environment
3. Gradually migrate agents to v2 API
4. Monitor performance and error rates
5. Complete migration when all agents are updated

### Key Differences

- Enhanced authentication with token management
- Improved error responses with structured format
- Rate limiting with proper HTTP headers
- Resource URLs with expiration and hash verification
- State machine implementation for agent lifecycle

## Development Status

### Implemented Features (v2.0.0)

- [x] Basic routing structure and endpoint organization
- [x] Authentication framework and token validation
- [x] Error handling middleware and response formatting
- [x] Rate limiting infrastructure

### Planned Features

- [ ] Agent registration with secure token generation
- [ ] Heartbeat system with state management
- [ ] Task assignment with keyspace distribution
- [ ] Progress tracking with real-time updates
- [ ] Result submission with duplicate detection
- [ ] Attack configuration with capability validation
- [ ] Resource management with presigned URLs
- [ ] Comprehensive testing suite
- [ ] Performance monitoring and metrics

### Future Enhancements

- Advanced capability negotiation
- Distributed task coordination
- Enhanced security features
- Performance optimizations
- Extended monitoring and analytics

## Support and Feedback

For questions, issues, or feedback regarding Agent API v2:

- **GitHub Issues**: [Ouroboros Issues](https://github.com/unclesp1d3r/Ouroboros/issues)
- **Documentation**: [API Documentation](http://localhost:8000/docs)
- **Community**: [Discussions](https://github.com/unclesp1d3r/Ouroboros/discussions)

## Changelog

### v2.0.0 (2025-01-XX)

- Initial Agent API v2 implementation
- Enhanced authentication and authorization
- Improved error handling and validation
- Rate limiting and security enhancements
- Forward-compatible resource management
- Comprehensive documentation and testing framework
