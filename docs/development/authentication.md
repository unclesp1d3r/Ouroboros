# Authentication Guide

This guide covers the authentication mechanisms used in Ouroboros.

## Authentication Types

Ouroboros implements three distinct authentication mechanisms:

1. **Bearer Token Authentication** (Agent API)

   - Used by distributed agents
   - Token format: `csa_<agent_id>_<random_string>`
   - Automatic token generation on agent registration
   - Token rotation on security events

2. **Session-based Authentication** (Web UI)

   - Used by web interface users
   - Secure HTTP-only cookies
   - CSRF protection
   - Session management

3. **API Key Authentication** (TUI API)

   - Used by command-line interface
   - Token format: `cst_<user_id>_<random_string>`
   - Configurable scopes and expiration
   - Multiple active keys per user

## Agent Authentication

### Token Generation

```python
from secrets import token_urlsafe
from uuid import uuid4


def generate_agent_token(agent_id: str) -> str:
    """Generate a secure agent token."""
    random_part = token_urlsafe(32)
    return f"csa_{agent_id}_{random_part}"
```

### Token Validation

```python
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()


async def validate_agent_token(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> str:
    """Validate agent token and return agent ID."""
    token = credentials.credentials

    if not token.startswith("csa_"):
        raise HTTPException(401, "Invalid token format")

    try:
        _, agent_id, _ = token.split("_", 2)
        # Verify token in database
        if not await verify_token_in_db(token):
            raise HTTPException(401, "Invalid token")
        return agent_id
    except ValueError:
        raise HTTPException(401, "Invalid token format")
```

### Token Rotation

```python
async def rotate_agent_token(agent_id: str) -> str:
    """Generate new token and invalidate old one."""
    new_token = generate_agent_token(agent_id)
    await update_agent_token(agent_id, new_token)
    return new_token
```

## Web UI Authentication

### Session Management

```python
from fastapi_sessions import SessionMiddleware
from fastapi_sessions.backends.redis import RedisBackend

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    session_cookie="session",
    max_age=settings.SESSION_LIFETIME,
    same_site="lax",
    https_only=True,
)
```

### User Authentication

```python
from passlib.hash import argon2
from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


async def authenticate_user(request: LoginRequest) -> User:
    """Authenticate user with username and password."""
    user = await get_user_by_username(request.username)
    if not user:
        raise HTTPException(401, "Invalid credentials")

    if not argon2.verify(request.password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")

    return user
```

### Session Creation

```python
from datetime import datetime, timedelta, UTC


async def create_session(user: User) -> str:
    """Create new session for user."""
    session_id = token_urlsafe(32)
    session_data = {
        "user_id": str(user.id),
        "created_at": datetime.now(UTC).isoformat(),
        "expires_at": (
            datetime.now(UTC) + timedelta(minutes=settings.SESSION_LIFETIME)
        ).isoformat(),
    }

    await redis.setex(
        f"session:{session_id}",
        settings.SESSION_LIFETIME * 60,
        json.dumps(session_data),
    )

    return session_id
```

### CSRF Protection

```python
from fastapi_csrf_protect import CsrfProtect
from fastapi_csrf_protect.exceptions import CsrfProtectError


@CsrfProtect.load_config
def get_csrf_config():
    """Get CSRF configuration."""
    return {
        "secret_key": settings.SECRET_KEY,
        "token_location": ("headers", "cookies"),
        "cookie": {
            "key": "csrf_token",
            "path": "/",
            "secure": True,
            "httponly": True,
            "samesite": "lax",
        },
    }


@app.exception_handler(CsrfProtectError)
def csrf_protect_exception_handler(request, exc):
    """Handle CSRF protection errors."""
    return JSONResponse(
        status_code=403, content={"error": {"code": "csrf_error", "message": str(exc)}}
    )
```

## TUI API Authentication

### API Key Generation

```python
from typing import List
from datetime import datetime, timedelta, UTC


class ApiKeyRequest(BaseModel):
    name: str
    expires_in: int  # seconds
    scopes: List[str]


async def generate_api_key(user_id: str, request: ApiKeyRequest) -> dict:
    """Generate new API key."""
    key_id = str(uuid4())
    random_part = token_urlsafe(32)
    api_key = f"cst_{user_id}_{random_part}"

    expires_at = datetime.now(UTC) + timedelta(seconds=request.expires_in)

    await store_api_key(
        key_id=key_id,
        api_key=api_key,
        user_id=user_id,
        name=request.name,
        scopes=request.scopes,
        expires_at=expires_at,
    )

    return {"key_id": key_id, "api_key": api_key, "expires_at": expires_at.isoformat()}
```

### Scope Validation

```python
from typing import List
from datetime import datetime, timedelta, UTC


class ApiKey(BaseModel):
    key_id: str
    user_id: str
    scopes: List[str]
    expires_at: datetime


async def validate_api_key_scope(api_key: ApiKey, required_scope: str) -> bool:
    """Validate API key has required scope."""
    if datetime.now(UTC) > api_key.expires_at:
        raise HTTPException(401, "API key expired")

    if required_scope not in api_key.scopes:
        raise HTTPException(403, "Insufficient scope")

    return True
```

## Security Best Practices

### Password Storage

```python
from passlib.hash import argon2


def hash_password(password: str) -> str:
    """Hash password using Argon2."""
    return argon2.hash(password)


def verify_password(password: str, hash: str) -> bool:
    """Verify password against hash."""
    return argon2.verify(password, hash)
```

### Token Security

1. **Token Format**

   ```python
   def validate_token_format(token: str) -> bool:
       """Validate token format."""
       parts = token.split("_")
       if len(parts) != 3:
           return False

       prefix = parts[0]
       if prefix not in ["csa", "cst"]:
           return False

       try:
           UUID(parts[1])
       except ValueError:
           return False

       if len(parts[2]) < 32:
           return False

       return True
   ```

2. **Token Storage**

   ```python
   async def store_token(token: str, metadata: dict) -> None:
       """Store token securely."""
       token_hash = hashlib.sha256(token.encode()).hexdigest()
       await redis.setex(
           f"token:{token_hash}", settings.TOKEN_LIFETIME, json.dumps(metadata)
       )
   ```

### Rate Limiting

```python
from fastapi import Request
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter


@app.on_event("startup")
async def startup():
    """Initialize rate limiter."""
    await FastAPILimiter.init(redis)


@app.post("/api/v1/auth/login")
@limiter.limit("5/minute")
async def login(request: Request):
    """Rate limited login endpoint."""
    pass
```

### Audit Logging

```python
from datetime import datetime, UTC
from typing import Optional


async def log_auth_event(
    event_type: str, user_id: Optional[str], ip_address: str, metadata: dict = None
) -> None:
    """Log authentication event."""
    event = {
        "timestamp": datetime.now(UTC).isoformat(),
        "event_type": event_type,
        "user_id": user_id,
        "ip_address": ip_address,
        "metadata": metadata or {},
    }

    await store_auth_log(event)
```

## Session Management

### Session Cleanup

```python
async def cleanup_expired_sessions():
    """Clean up expired sessions."""
    async for key in redis.scan_iter("session:*"):
        session_data = await redis.get(key)
        if not session_data:
            continue

        data = json.loads(session_data)
        expires_at = datetime.fromisoformat(data["expires_at"])

        if datetime.now(UTC) > expires_at:
            await redis.delete(key)
```

### Session Invalidation

```python
async def invalidate_user_sessions(user_id: str) -> int:
    """Invalidate all sessions for user."""
    count = 0
    async for key in redis.scan_iter("session:*"):
        session_data = await redis.get(key)
        if not session_data:
            continue

        data = json.loads(session_data)
        if data["user_id"] == user_id:
            await redis.delete(key)
            count += 1

    return count
```

## Two-Factor Authentication

```python
import pyotp
from base64 import b32encode


class TwoFactorSetup(BaseModel):
    secret: str
    qr_code: str
    backup_codes: List[str]


async def setup_2fa(user_id: str) -> TwoFactorSetup:
    """Set up 2FA for user."""
    # Generate secret
    secret = b32encode(os.urandom(20)).decode()

    # Generate QR code
    totp = pyotp.TOTP(secret)
    qr_code = totp.provisioning_uri(name=user.email, issuer_name="Ouroboros")

    # Generate backup codes
    backup_codes = [token_urlsafe(12) for _ in range(10)]

    # Store in database
    await store_2fa_data(
        user_id=user_id,
        secret=secret,
        backup_codes=[
            hashlib.sha256(code.encode()).hexdigest() for code in backup_codes
        ],
    )

    return TwoFactorSetup(secret=secret, qr_code=qr_code, backup_codes=backup_codes)
```

## Security Headers

```python
from fastapi.middleware.security import SecurityMiddleware

app.add_middleware(
    SecurityMiddleware,
    headers={
        "X-Frame-Options": "DENY",
        "X-Content-Type-Options": "nosniff",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline';"
        ),
    },
)
```

## What is Casbin?

[Casbin](https://casbin.org/) is a powerful, flexible access control library supporting role-based access control (RBAC), attribute-based access control (ABAC), and more. Ouroboros uses Casbin for all user/project/role authorization logic.

## Where Do Policies Live?

- **Model file:** `config/model.conf`
- **Policy file:** `config/policy.csv`
- **Casbin wrapper:** `app/core/authz.py`
- **Permission helpers:** `app/core/permissions.py`

## How to Add a New Role, Object, or Action

1. **Add a new role:**
   - Add a new `g,` (role inheritance) or `p,` (policy) line to `policy.csv`.
2. **Add a new object:**
   - Use the format `project:{project_id}`, `campaign:{campaign_id}`, etc.
   - Add new `p,` lines for the object and allowed actions.
3. **Add a new action:**
   - Add a new `p,` line for the action (e.g., `p, project_admin, project:*, archive`).

## Usage Pattern

- **Never check user roles inline.**
- Always use the helpers in `permissions.py`:
  - `can_access_project(user, project, action)`
  - `can(user, resource, action)`

This ensures all RBAC logic is consistent, testable, and centrally managed.

---

For more information:

- [Security Guide](security.md)
- [API Reference](../api/overview.md)
- [Development Setup](setup.md)
