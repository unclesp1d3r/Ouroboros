# Security Guide

This guide covers security best practices and implementation details for Ouroboros.

## Security Architecture

### Overview

Ouroboros implements a defense-in-depth security strategy:

1. **Network Security**

   - TLS encryption
   - Network segmentation
   - Firewall rules
   - Rate limiting

2. **Application Security**

   - Authentication
   - Authorization
   - Input validation
   - Output encoding

3. **Data Security**

   - Encryption at rest
   - Secure key management
   - Data sanitization
   - Backup protection

4. **Infrastructure Security**

   - Container security
   - Host hardening
   - Monitoring
   - Incident response

## Network Security

### TLS Configuration

```python
from fastapi import FastAPI
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

app = FastAPI()
app.add_middleware(HTTPSRedirectMiddleware)

ssl_context = {
    "cert_file": "/etc/ouroboros/cert.pem",
    "key_file": "/etc/ouroboros/key.pem",
    "ca_file": "/etc/ouroboros/ca.pem",
    "ciphers": "ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384",
    "protocols": ["TLSv1.2", "TLSv1.3"],
}
```

### Network Segmentation

```yaml
# docker-compose.yml
networks:
  frontend:
    driver: bridge
    internal: false
  backend:
    driver: bridge
    internal: true
  storage:
    driver: bridge
    internal: true

services:
  api:
    networks:
      - frontend
      - backend

  database:
    networks:
      - backend

  minio:
    networks:
      - storage
```

### Firewall Rules

```bash
# Allow API access
iptables -A INPUT -p tcp --dport 8000 -j ACCEPT

# Allow agent communication
iptables -A INPUT -p tcp --dport 8001 -s 10.0.0.0/8 -j ACCEPT

# Block everything else
iptables -A INPUT -j DROP
```

## Application Security

### Input Validation

```python
from pydantic import BaseModel, constr, conint
from typing import List


class AttackConfig(BaseModel):
    name: constr(min_length=1, max_length=100)
    type: constr(regex="^(dictionary|mask|hybrid)$")
    wordlist: constr(min_length=1, max_length=255)
    hash_type: conint(ge=0, le=99999)
    rules: List[constr(min_length=1, max_length=255)]


def validate_hash(hash_string: str) -> bool:
    """Validate hash string format."""
    import re

    patterns = {
        "md5": r"^[a-fA-F0-9]{32}$",
        "sha1": r"^[a-fA-F0-9]{40}$",
        "sha256": r"^[a-fA-F0-9]{64}$",
        "ntlm": r"^[a-fA-F0-9]{32}$",
    }
    return any(re.match(pattern, hash_string) for pattern in patterns.values())
```

### Output Encoding

```python
from html import escape
from json import dumps
from base64 import b64encode


def encode_html(data: str) -> str:
    """Encode HTML special characters."""
    return escape(data, quote=True)


def encode_json(data: dict) -> str:
    """Encode JSON with safe characters."""
    return dumps(data, ensure_ascii=True, separators=(",", ":"))


def encode_filename(filename: str) -> str:
    """Encode filename for Content-Disposition header."""
    return b64encode(filename.encode("utf-8")).decode("ascii")
```

### SQL Injection Prevention

```python
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def safe_query(session: AsyncSession, query: str, params: dict) -> list:
    """Execute parameterized query safely."""
    result = await session.execute(text(query), params)
    return result.fetchall()


# Example usage
users = await safe_query(
    session, "SELECT * FROM users WHERE role = :role", {"role": "admin"}
)
```

## Data Security

### Encryption at Rest

```python
from cryptography.fernet import Fernet
from base64 import b64encode
from os import urandom


class DataEncryption:
    def __init__(self, key: bytes = None):
        self.key = key or self._generate_key()
        self.fernet = Fernet(self.key)

    def _generate_key(self) -> bytes:
        """Generate new encryption key."""
        return b64encode(urandom(32))

    def encrypt(self, data: bytes) -> bytes:
        """Encrypt data."""
        return self.fernet.encrypt(data)

    def decrypt(self, token: bytes) -> bytes:
        """Decrypt data."""
        return self.fernet.decrypt(token)


# Usage
encryption = DataEncryption()
encrypted = encryption.encrypt(b"sensitive data")
decrypted = encryption.decrypt(encrypted)
```

### Key Management

```python
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


class KeyManager:
    def __init__(self, master_key: bytes):
        self.master_key = master_key

    def derive_key(self, purpose: str, salt: bytes) -> bytes:
        """Derive purpose-specific key."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000
        )
        return kdf.derive(self.master_key + purpose.encode())

    def rotate_key(self, old_key: bytes) -> bytes:
        """Rotate encryption key."""
        new_key = urandom(32)
        # Re-encrypt data with new key
        return new_key
```

### Secure File Storage

```python
import hashlib
from pathlib import Path
from typing import BinaryIO


class SecureStorage:
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir

    def store_file(self, file: BinaryIO, metadata: dict) -> str:
        """Store file securely."""
        # Calculate hash
        sha256 = hashlib.sha256()
        for chunk in iter(lambda: file.read(8192), b""):
            sha256.update(chunk)
        file_hash = sha256.hexdigest()

        # Store with hash as filename
        target_path = self.root_dir / file_hash
        with open(target_path, "wb") as f:
            file.seek(0)
            for chunk in iter(lambda: file.read(8192), b""):
                f.write(chunk)

        # Store metadata
        self._store_metadata(file_hash, metadata)
        return file_hash
```

## Infrastructure Security

### Container Hardening

```dockerfile
# Use minimal base image
FROM python:3.13-slim

# Run as non-root user
RUN useradd -r -s /bin/false ouroboros
USER ouroboros

# Set security options
LABEL security.capabilities="cap_net_bind_service"
LABEL security.seccomp="docker-default"

# Enable health checks
HEALTHCHECK --interval=30s --timeout=3s \
    CMD curl -f http://localhost:8000/health || exit 1

# Set resource limits
LABEL resources.limits.cpu="2"
LABEL resources.limits.memory="4G"
```

### Host Hardening

```bash
#!/bin/bash

# System updates
apt update && apt upgrade -y

# Disable unnecessary services
systemctl disable bluetooth
systemctl disable cups

# Set secure permissions
chmod 600 /etc/shadow
chmod 600 /etc/gshadow
chmod 644 /etc/passwd
chmod 644 /etc/group

# Configure sysctl
cat > /etc/sysctl.d/99-security.conf << EOF
kernel.randomize_va_space = 2
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv4.conf.all.secure_redirects = 0
net.ipv4.conf.default.secure_redirects = 0
net.ipv6.conf.all.accept_redirects = 0
net.ipv6.conf.default.accept_redirects = 0
EOF

sysctl -p /etc/sysctl.d/99-security.conf
```

### Monitoring

```python
from prometheus_client import Counter, Histogram
from logging import getLogger

# Metrics
auth_failures = Counter(
    "auth_failures_total", "Authentication failures", ["method", "source"]
)

request_duration = Histogram(
    "request_duration_seconds", "Request duration in seconds", ["endpoint", "method"]
)

# Logging
logger = getLogger("security")


def log_security_event(event_type: str, severity: str, details: dict) -> None:
    """Log security event."""
    logger.warning(
        "Security event: %s",
        {"type": event_type, "severity": severity, "details": details},
    )
```

### Incident Response

```python
from enum import Enum
from datetime import datetime, UTC
from typing import List, Optional


class IncidentSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SecurityIncident:
    def __init__(self, type: str, severity: IncidentSeverity, description: str):
        self.id = str(uuid4())
        self.type = type
        self.severity = severity
        self.description = description
        self.created_at = datetime.now(UTC)
        self.resolved_at: Optional[datetime] = None
        self.actions: List[str] = []

    async def respond(self) -> None:
        """Initial incident response."""
        if self.severity >= IncidentSeverity.HIGH:
            # Alert security team
            await alert_security_team(self)

            # Block suspicious IPs
            await block_suspicious_ips()

            # Rotate security keys
            await rotate_security_keys()

    async def resolve(self, resolution: str) -> None:
        """Mark incident as resolved."""
        self.resolved_at = datetime.now(UTC)
        self.actions.append(f"Resolved: {resolution}")
        await store_incident(self)
```

## Security Testing

### Vulnerability Scanning

```python
from typing import List
import subprocess


def scan_dependencies() -> List[dict]:
    """Scan dependencies for vulnerabilities."""
    result = subprocess.run(["safety", "check"], capture_output=True, text=True)
    return parse_safety_output(result.stdout)


def scan_docker_image(image: str) -> List[dict]:
    """Scan Docker image for vulnerabilities."""
    result = subprocess.run(["trivy", "image", image], capture_output=True, text=True)
    return parse_trivy_output(result.stdout)
```

### Security Testing

```python
import pytest
from fastapi.testclient import TestClient


def test_sql_injection(client: TestClient):
    """Test SQL injection prevention."""
    response = client.get("/users?name=admin' OR '1'='1")
    assert response.status_code == 400


def test_xss_prevention(client: TestClient):
    """Test XSS prevention."""
    payload = "<script>alert('xss')</script>"
    response = client.post("/comments", json={"content": payload})
    assert "<script>" not in response.text


def test_csrf_protection(client: TestClient):
    """Test CSRF protection."""
    response = client.post("/api/v1/web/users", headers={"X-CSRF-Token": "invalid"})
    assert response.status_code == 403
```

## Security Checklist

1. **Authentication**

   - [ ] Implement strong password policies
   - [ ] Enable two-factor authentication
   - [ ] Use secure session management
   - [ ] Implement account lockout

2. **Authorization**

   - [ ] Implement role-based access control
   - [ ] Validate user permissions
   - [ ] Secure API endpoints
   - [ ] Audit access logs

3. **Data Protection**

   - [ ] Encrypt sensitive data
   - [ ] Secure key management
   - [ ] Implement backup strategy
   - [ ] Data sanitization

4. **Network Security**

   - [ ] Enable TLS/SSL
   - [ ] Configure firewalls
   - [ ] Implement rate limiting
   - [ ] Network monitoring

5. **Infrastructure**

   - [ ] Secure container configuration
   - [ ] Host hardening
   - [ ] Regular updates
   - [ ] Security monitoring

For more information:

- [Authentication Guide](authentication.md)
- [API Security](../api/security.md)
- [Deployment Guide](../deployment/production.md)
