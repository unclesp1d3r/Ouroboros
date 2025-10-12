# Installation Guide

This guide will help you install and deploy Ouroboros for production use. Ouroboros is a distributed password cracking management system that coordinates multiple hashcat instances across your network.

> **Important**: Ouroboros is currently in active development. Docker-based deployment is planned for a future release. This guide covers the current installation method suitable for production deployment.

---

## Table of Contents

<!-- mdformat-toc start --slug=gitlab --no-anchors --maxlevel=2 --minlevel=1 -->

- [Installation Guide](#installation-guide)
  - [Table of Contents](#table-of-contents)
  - [Prerequisites](#prerequisites)
  - [Installation Steps](#installation-steps)
  - [Verification](#verification)
  - [Security Considerations](#security-considerations)
  - [Maintenance](#maintenance)
  - [Common Issues](#common-issues)
  - [Next Steps](#next-steps)
  - [Production Notes](#production-notes)
  - [Support](#support)

<!-- mdformat-toc end -->

---

## Prerequisites

### System Requirements

- **CPU**: 4+ cores recommended
- **RAM**: 8GB minimum, 16GB+ recommended for production
- **Storage**: 50GB+ available space
- **Network**: Reliable network connectivity between server and agents
- **OS**: Linux (Ubuntu 20.04+ or CentOS 8+ recommended), macOS, or Windows with WSL2

### Required Software

1. **Python 3.13+**

   - [Python Installation Guide](https://www.python.org/downloads/)
   - Verify: `python3 --version`

2. **PostgreSQL 16+**

   - [PostgreSQL Installation Guide](https://www.postgresql.org/download/)
   - Required for storing campaigns, tasks, and results
   - Verify: `psql --version`

3. **Redis** (Optional but recommended)

   - Used for caching and background task processing
   - Install: `sudo apt install redis-server` (Ubuntu) or `brew install redis` (macOS)
   - Verify: `redis-cli ping`

4. **MinIO** (S3-compatible storage)

   - Required for storing attack resources (wordlists, rules, masks)
   - [MinIO Installation Guide](https://min.io/docs/minio/linux/index.html)

5. **uv** (Python package manager)

   - Install: `curl -LsSf https://astral.sh/uv/install.sh | sh`
   - Or: `pip install uv`
   - Verify: `uv --version`

6. **just** (Task runner)

   - Install: `cargo install just` or see [installation guide](https://github.com/casey/just#installation)
   - Verify: `just --version`

## Installation Steps

### 1. Create System User

Create a dedicated user for Ouroboros:

```bash
# Create ouroboros user
sudo useradd -m -s /bin/bash ouroboros
sudo usermod -aG sudo ouroboros

# Switch to ouroboros user
sudo su - ouroboros
```

### 2. Download and Setup Ouroboros

```bash
# Clone the repository
git clone https://github.com/unclesp1d3r/Ouroboros.git
cd Ouroboros

# Install dependencies
uv sync
```

### 3. Database Setup

1. **Create PostgreSQL Database**

```bash
# Connect to PostgreSQL as admin
sudo -u postgres psql

# Create database and user
CREATE DATABASE ouroboros;
CREATE USER ouroboros WITH PASSWORD 'your_secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE ouroboros TO ouroboros;
ALTER USER ouroboros CREATEDB;  -- Needed for migrations
\q
```

1. **Configure Database Connection**

Create `.env` file with your configuration:

```bash
cp env.example .env
```

Edit `.env` with your settings:

```env
# Security - CHANGE THESE VALUES
SECRET_KEY=your_very_secure_secret_key_here_at_least_32_characters
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Database Configuration
POSTGRES_SERVER=localhost
POSTGRES_USER=ouroboros
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_DB=ouroboros

# Initial Admin User - CHANGE THESE VALUES
FIRST_SUPERUSER=admin@yourdomain.com
FIRST_SUPERUSER_PASSWORD=your_secure_admin_password

# Redis Configuration (if using Redis)
REDIS_HOST=localhost
REDIS_PORT=6379

# Celery Configuration (for background tasks)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Hashcat Configuration
HASHCAT_BINARY_PATH=hashcat
DEFAULT_WORKLOAD_PROFILE=3
ENABLE_ADDITIONAL_HASH_TYPES=false

# MinIO Configuration
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=your_minio_access_key
MINIO_SECRET_KEY=your_minio_secret_key
MINIO_BUCKET=ouroboros-resources
MINIO_SECURE=false

# Logging Configuration
LOG_LEVEL=INFO
LOG_TO_FILE=true
LOG_FILE_PATH=/var/log/ouroboros/app.log
LOG_RETENTION=30 days
LOG_ROTATION=100 MB

# Resource Limits
RESOURCE_EDIT_MAX_SIZE_MB=5
RESOURCE_EDIT_MAX_LINES=10000
UPLOAD_MAX_SIZE=104857600

# Cache Configuration
CACHE_CONNECT_STRING=redis://localhost:6379/1
```

1. **Run Database Migrations**

```bash
# Initialize the database
uv run alembic upgrade head
```

### 4. MinIO Setup

1. **Install and Start MinIO**

```bash
# Download MinIO (Linux)
wget https://dl.min.io/server/minio/release/linux-amd64/minio
chmod +x minio
sudo mv minio /usr/local/bin/

# Create data directory
sudo mkdir -p /opt/minio/data
sudo chown ouroboros:ouroboros /opt/minio/data

# Start MinIO (as ouroboros user)
minio server /opt/minio/data --console-address ":9001"
```

1. **Configure MinIO**

- Access MinIO Console: <http://your-server:9001>
- Login with your MinIO credentials
- Create bucket: `ouroboros-resources`
- Set appropriate access policies

### 5. Create System Service

Create a systemd service for Ouroboros:

```bash
sudo tee /etc/systemd/system/ouroboros.service > /dev/null <<EOF
[Unit]
Description=Ouroboros Password Cracking Management System
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=ouroboros
Group=ouroboros
WorkingDirectory=/home/ouroboros/Ouroboros
Environment=PATH=/home/ouroboros/Ouroboros/.venv/bin
ExecStart=/home/ouroboros/Ouroboros/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable ouroboros
sudo systemctl start ouroboros
```

### 6. Setup Reverse Proxy (Recommended)

Install and configure Nginx as a reverse proxy:

```bash
# Install Nginx
sudo apt update
sudo apt install nginx

# Create Nginx configuration
sudo tee /etc/nginx/sites-available/ouroboros > /dev/null <<EOF
server {
    listen 80;
    server_name your-domain.com;  # Replace with your domain

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # For SSE (Server-Sent Events)
    location /api/v1/web/live/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_buffering off;
        proxy_cache off;
        proxy_set_header Connection '';
        proxy_http_version 1.1;
        chunked_transfer_encoding off;
    }
}
EOF

# Enable the site
sudo ln -s /etc/nginx/sites-available/ouroboros /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Verification

### 1. Check Services

```bash
# Check Ouroboros service
sudo systemctl status ouroboros

# Check database connection
psql -U ouroboros -d ouroboros -h localhost -c "SELECT version();"

# Check Redis (if using)
redis-cli ping

# Check MinIO
curl http://localhost:9000/minio/health/live
```

### 2. Access Web Interface

- Direct access: <http://your-server:8000>
- Through Nginx: <http://your-domain.com>
- Login with your admin credentials from `.env`

### 3. Check API Documentation

- OpenAPI UI: <http://your-server:8000/docs>
- ReDoc UI: <http://your-server:8000/redoc>

## Security Considerations

### 1. Firewall Configuration

```bash
# Allow SSH, HTTP, and HTTPS
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443

# Allow Ouroboros port (if not using reverse proxy)
sudo ufw allow 8000

# Enable firewall
sudo ufw enable
```

### 2. SSL/TLS Setup (Recommended)

Use Let's Encrypt for free SSL certificates:

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### 3. Secure Configuration

- Change all default passwords
- Use strong, unique passwords
- Regularly update the system and dependencies
- Monitor logs for suspicious activity
- Backup database and MinIO data regularly

## Maintenance

### 1. Updates

```bash
# Update Ouroboros
cd /home/ouroboros/Ouroboros
git pull origin main
uv sync
uv run alembic upgrade head
sudo systemctl restart ouroboros
```

### 2. Backups

```bash
# Database backup
pg_dump -U ouroboros -h localhost ouroboros > backup_$(date +%Y%m%d).sql

# MinIO backup
# Use MinIO client (mc) or your preferred backup solution
```

### 3. Monitoring

```bash
# Check logs
sudo journalctl -u ouroboros -f

# Check application logs
tail -f /var/log/ouroboros/app.log

# Monitor system resources
htop
```

## Common Issues

### 1. Database Connection Issues

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Test connection
psql -U ouroboros -d ouroboros -h localhost
```

### 2. Permission Issues

```bash
# Fix file permissions
sudo chown -R ouroboros:ouroboros /home/ouroboros/Ouroboros
sudo chmod -R 755 /home/ouroboros/Ouroboros
```

### 3. Service Won't Start

```bash
# Check service logs
sudo journalctl -u ouroboros -n 50

# Check configuration
cd /home/ouroboros/Ouroboros
uv run python -c "from app.core.config import settings; print('Config loaded successfully')"
```

### 4. MinIO Connection Issues

```bash
# Check MinIO is running
ps aux | grep minio

# Test MinIO health
curl http://localhost:9000/minio/health/live
```

## Next Steps

After installation:

1. **Create your first project**: Projects provide multi-tenant isolation
2. **Register agents**: Set up hashcat agents on your cracking machines
3. **Upload resources**: Add wordlists, rules, and masks for attacks
4. **Create campaigns**: Set up your first password cracking campaign

See the [Quick Start Guide](quick-start.md) for a walkthrough of these steps.

## Production Notes

- **Performance**: Consider using a dedicated database server for large deployments
- **Scaling**: Multiple Ouroboros instances can share the same database and MinIO
- **Monitoring**: Implement proper monitoring and alerting for production use
- **Backup**: Establish regular backup procedures for database and MinIO data
- **Security**: Follow security best practices for your environment

## Support

If you encounter issues:

1. Check the [Troubleshooting Guide](../user-guide/troubleshooting.md)
2. Review the logs for error messages
3. Search [GitHub Issues](https://github.com/unclesp1d3r/Ouroboros/issues)
4. Create a new issue with detailed information about your problem
