# Configuration Guide

This guide covers all configuration options for Ouroboros. Configuration is managed through environment variables that can be set in a `.env` file or through your system's environment

---

## Table of Contents

<!-- mdformat-toc start --slug=gitlab --no-anchors --maxlevel=2 --minlevel=1 -->

- [Configuration Guide](#configuration-guide)
  - [Table of Contents](#table-of-contents)
  - [Configuration File](#configuration-file)
  - [Core Settings](#core-settings)
  - [External Services](#external-services)
  - [Hashcat Configuration](#hashcat-configuration)
  - [Logging Configuration](#logging-configuration)
  - [Resource Limits](#resource-limits)
  - [Environment-Specific Configurations](#environment-specific-configurations)
  - [Advanced Configuration](#advanced-configuration)
  - [Configuration Validation](#configuration-validation)
  - [Security Best Practices](#security-best-practices)
  - [Performance Tuning](#performance-tuning)
  - [Monitoring Configuration](#monitoring-configuration)
  - [Troubleshooting Configuration](#troubleshooting-configuration)
  - [Configuration Templates](#configuration-templates)
  - [Next Steps](#next-steps)

<!-- mdformat-toc end -->

---

## Configuration File

Ouroboros uses a `.env` file for configuration. Create this file in the root directory of your Ouroboros installation.

```bash
# Copy the example configuration
cp env.example .env

# Edit with your settings
nano .env
```

## Core Settings

### Application Settings

```env
# Project identification
PROJECT_NAME=Ouroboros
VERSION=0.1.0

# CORS origins (comma-separated list of allowed origins)
BACKEND_CORS_ORIGINS=http://localhost:3000,http://localhost:8000,https://yourdomain.com
```

### Security Configuration

```env
# JWT Secret Key - CHANGE THIS IN PRODUCTION
SECRET_KEY=your_very_secure_secret_key_here_at_least_32_characters

# JWT token expiration (in minutes)
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

> **Important**: The `SECRET_KEY` is used for JWT token signing. Use a strong, random key in production. Generate one with: `openssl rand -hex 32`

### Database Configuration

```env
# PostgreSQL connection settings
POSTGRES_SERVER=localhost
POSTGRES_USER=ouroboros
POSTGRES_PASSWORD=your_secure_database_password
POSTGRES_DB=ouroboros
```

The application automatically constructs the database URI as: `postgresql+psycopg://POSTGRES_USER:POSTGRES_PASSWORD@POSTGRES_SERVER/POSTGRES_DB`

### Initial Admin User

```env
# Default admin user created on first startup
FIRST_SUPERUSER=admin@yourdomain.com
FIRST_SUPERUSER_PASSWORD=your_secure_admin_password
```

> **Security Note**: Change the admin password immediately after first login.

## External Services

### Redis Configuration (Optional)

Redis is used for caching and background task processing:

```env
# Redis connection settings
REDIS_HOST=localhost
REDIS_PORT=6379

# Celery task queue (uses Redis)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### MinIO S3-Compatible Storage

MinIO stores attack resources (wordlists, rules, masks):

```env
# MinIO connection settings
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=your_minio_access_key
MINIO_SECRET_KEY=your_minio_secret_key
MINIO_BUCKET=ouroboros-resources
MINIO_SECURE=false
MINIO_REGION=
```

**Settings Explanation:**

- `MINIO_ENDPOINT`: MinIO server address and port
- `MINIO_ACCESS_KEY`: MinIO access key (like AWS Access Key ID)
- `MINIO_SECRET_KEY`: MinIO secret key (like AWS Secret Access Key)
- `MINIO_BUCKET`: Bucket name for storing resources
- `MINIO_SECURE`: Set to `true` if using HTTPS
- `MINIO_REGION`: Optional region setting (e.g., `us-east-1`)

### Cache Configuration

```env
# Cache connection string for cashews
CACHE_CONNECT_STRING=mem://?check_interval=10&size=10000
```

**Cache Options:**

- **Memory**: `mem://?check_interval=10&size=10000` (default, development)
- **Redis**: `redis://localhost:6379/1` (recommended for production)

## Hashcat Configuration

```env
# Hashcat binary path
HASHCAT_BINARY_PATH=hashcat

# Default workload profile (1-4, where 4 is highest performance)
DEFAULT_WORKLOAD_PROFILE=3

# Enable additional hash types (--benchmark-all)
ENABLE_ADDITIONAL_HASH_TYPES=false
```

**Workload Profiles:**

- `1`: Low performance, desktop usable
- `2`: Economic performance
- `3`: High performance (default)
- `4`: Nightmare performance, system unusable

## Logging Configuration

```env
# Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL=INFO

# File logging
LOG_TO_FILE=true
LOG_FILE_PATH=/var/log/ouroboros/app.log
LOG_RETENTION=30 days
LOG_ROTATION=100 MB
```

**Log Levels:**

- `DEBUG`: Detailed debugging information
- `INFO`: General information (recommended for production)
- `WARNING`: Warning messages only
- `ERROR`: Error messages only
- `CRITICAL`: Critical errors only

## Resource Limits

### File Upload Limits

```env
# Maximum upload size for crackable uploads (in bytes)
UPLOAD_MAX_SIZE=104857600  # 100MB

# Resource editing limits
RESOURCE_EDIT_MAX_SIZE_MB=5
RESOURCE_EDIT_MAX_LINES=10000
```

### Resource Processing

```env
# Timeout for resource upload verification (in seconds)
RESOURCE_UPLOAD_TIMEOUT_SECONDS=900  # 15 minutes
```

## Environment-Specific Configurations

### Development Environment

```env
# Development settings
SECRET_KEY=development_secret_key_not_for_production
POSTGRES_SERVER=localhost
POSTGRES_PASSWORD=development_password
LOG_LEVEL=DEBUG
LOG_TO_FILE=false
MINIO_SECURE=false
CACHE_CONNECT_STRING=mem://?check_interval=10&size=10000
```

### Production Environment

```env
# Production settings
SECRET_KEY=your_very_secure_production_secret_key
POSTGRES_SERVER=your-db-server.com
POSTGRES_PASSWORD=very_secure_production_password
LOG_LEVEL=INFO
LOG_TO_FILE=true
LOG_FILE_PATH=/var/log/ouroboros/app.log
MINIO_SECURE=true
CACHE_CONNECT_STRING=redis://localhost:6379/1
BACKEND_CORS_ORIGINS=https://yourdomain.com
```

## Advanced Configuration

### Database Debugging

```env
# Enable SQLAlchemy query logging (development only)
DB_ECHO=false
```

> [!WARNING]
> Never enable `DB_ECHO=true` in production as it logs all SQL queries including sensitive data.

### JWT Configuration

```env
# Alternative JWT secret (if different from SECRET_KEY)
JWT_SECRET_KEY=your_jwt_specific_secret_key
```

### Resource Upload Verification

```env
# Enable/disable resource upload verification
RESOURCE_UPLOAD_VERIFICATION_ENABLED=true
```

## Configuration Validation

Ouroboros validates configuration on startup. Common validation errors:

### Database Connection

```bash
# Test database connection
psql -U ouroboros -h localhost -d ouroboros -c "SELECT version();"
```

### MinIO Connection

```bash
# Test MinIO connection
curl http://localhost:9000/minio/health/live
```

### Redis Connection

```bash
# Test Redis connection
redis-cli ping
```

## Security Best Practices

### 1. Secret Management

- **Never commit secrets to version control**
- **Use strong, unique passwords**
- **Rotate secrets regularly**
- **Use environment-specific secrets**

### 2. Database Security

```env
# Use strong database passwords
POSTGRES_PASSWORD=complex_password_with_numbers_123_and_symbols_!@#

# Consider using connection pooling for production
# (handled automatically by SQLAlchemy)
```

### 3. Network Security

```env
# Restrict CORS origins in production
BACKEND_CORS_ORIGINS=https://yourdomain.com,https://admin.yourdomain.com

# Use HTTPS for MinIO in production
MINIO_SECURE=true
MINIO_ENDPOINT=minio.yourdomain.com:443
```

### 4. Logging Security

```env
# Ensure log files are properly secured
LOG_FILE_PATH=/var/log/ouroboros/app.log

# Set appropriate log retention
LOG_RETENTION=90 days
```

## Performance Tuning

### Database Performance

```env
# For high-load environments, consider connection pooling
# (SQLAlchemy handles this automatically, but you can tune via database settings)
```

### Cache Performance

```env
# Use Redis for better cache performance in production
CACHE_CONNECT_STRING=redis://localhost:6379/1

# For distributed deployments
CACHE_CONNECT_STRING=redis://redis-cluster.yourdomain.com:6379/1
```

### Resource Limits

```env
# Adjust based on your hardware and usage patterns
RESOURCE_EDIT_MAX_SIZE_MB=10
RESOURCE_EDIT_MAX_LINES=50000
UPLOAD_MAX_SIZE=1073741824  # 1GB for large wordlists
```

## Monitoring Configuration

### Health Checks

The application provides health check endpoints that use these configurations:

- Database connectivity (uses `POSTGRES_*` settings)
- Redis connectivity (uses `REDIS_*` settings)
- MinIO connectivity (uses `MINIO_*` settings)

### Metrics Collection

```env
# Enable detailed logging for monitoring
LOG_LEVEL=INFO
LOG_TO_FILE=true

# Cache metrics (automatically collected)
CACHE_CONNECT_STRING=redis://localhost:6379/1
```

## Troubleshooting Configuration

### Common Issues

1. **Database Connection Failed**

   ```bash
   # Check PostgreSQL is running
   sudo systemctl status postgresql

   # Test connection manually
   psql -U ouroboros -h localhost -d ouroboros
   ```

2. **MinIO Connection Failed**

   ```bash
   # Check MinIO is running
   ps aux | grep minio

   # Test MinIO health
   curl http://localhost:9000/minio/health/live
   ```

3. **Redis Connection Failed**

   ```bash
   # Check Redis is running
   sudo systemctl status redis

   # Test Redis connection
   redis-cli ping
   ```

### Configuration Validation

```bash
# Test configuration loading
cd /path/to/ouroboros
uv run python -c "from app.core.config import settings; print('Configuration loaded successfully')"
```

### Environment Variable Debugging

```bash
# Check environment variables are loaded
uv run python -c "from app.core.config import settings; print(f'Database: {settings.POSTGRES_SERVER}')"
```

## Configuration Templates

### Small Deployment (Single Server)

```env
# Single server deployment
SECRET_KEY=your_secure_secret_key
POSTGRES_SERVER=localhost
POSTGRES_USER=ouroboros
POSTGRES_PASSWORD=secure_password
POSTGRES_DB=ouroboros
REDIS_HOST=localhost
REDIS_PORT=6379
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=secure_minio_password
CACHE_CONNECT_STRING=redis://localhost:6379/1
LOG_LEVEL=INFO
LOG_TO_FILE=true
```

### Large Deployment (Distributed)

```env
# Distributed deployment
SECRET_KEY=your_very_secure_secret_key
POSTGRES_SERVER=db.internal.yourdomain.com
POSTGRES_USER=ouroboros
POSTGRES_PASSWORD=very_secure_password
POSTGRES_DB=ouroboros
REDIS_HOST=redis.internal.yourdomain.com
REDIS_PORT=6379
MINIO_ENDPOINT=minio.internal.yourdomain.com:9000
MINIO_ACCESS_KEY=production_access_key
MINIO_SECRET_KEY=production_secret_key
MINIO_SECURE=true
CACHE_CONNECT_STRING=redis://redis.internal.yourdomain.com:6379/1
BACKEND_CORS_ORIGINS=https://ouroboros.yourdomain.com
LOG_LEVEL=INFO
LOG_TO_FILE=true
LOG_FILE_PATH=/var/log/ouroboros/app.log
```

## Next Steps

After configuring Ouroboros:

1. **Test the configuration** with the validation commands above
2. **Start the application** and verify all services connect properly
3. **Review the logs** for any configuration warnings
4. **Set up monitoring** for the configured services
5. **Create backups** of your configuration and data

For more information, see:

- [Installation Guide](installation.md): Complete installation instructions
- [Quick Start Guide](quick-start.md): Getting started with Ouroboros
- [Troubleshooting Guide](../user-guide/troubleshooting.md): Common issues and solutions
