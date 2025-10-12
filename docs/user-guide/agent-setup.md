# Agent Setup Guide

This guide covers the installation, registration, and configuration of Ouroboros v2 agents.

---

## Table of Contents

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=3 --minlevel=1 -->

- [Agent Setup Guide](#agent-setup-guide)
  - [Table of Contents](#table-of-contents)
  - [Prerequisites](#prerequisites)
  - [Agent Registration (Administrator)](#agent-registration-administrator)
    - [1. Web Interface Registration](#1-web-interface-registration)
    - [2. Project-Based Access Control](#2-project-based-access-control)
  - [Installation](#installation)
    - [1. Install Dependencies](#1-install-dependencies)
    - [2. Install Ouroboros Agent](#2-install-ouroboros-agent)
  - [Configuration](#configuration)
    - [1. Basic Setup](#1-basic-setup)
    - [2. Authentication Configuration](#2-authentication-configuration)
    - [3. Advanced Configuration](#3-advanced-configuration)
    - [4. Project Context](#4-project-context)
  - [Running the Agent](#running-the-agent)
    - [1. Systemd Service (Recommended)](#1-systemd-service-recommended)
    - [2. Docker Container](#2-docker-container)
    - [3. Docker Compose](#3-docker-compose)
  - [Agent Management via Web Interface](#agent-management-via-web-interface)
    - [1. Agent Status Monitoring](#1-agent-status-monitoring)
    - [2. Configuration Management](#2-configuration-management)
    - [3. Performance Monitoring](#3-performance-monitoring)
  - [Monitoring and Diagnostics](#monitoring-and-diagnostics)
    - [1. Log Files](#1-log-files)
    - [2. Agent Status Commands](#2-agent-status-commands)
    - [3. Performance Metrics](#3-performance-metrics)
  - [Troubleshooting](#troubleshooting)
    - [1. Authentication Issues](#1-authentication-issues)
    - [2. Project Access Issues](#2-project-access-issues)
    - [3. Performance Issues](#3-performance-issues)
    - [4. Common Problems](#4-common-problems)
  - [Maintenance](#maintenance)
    - [1. Updates](#1-updates)
    - [2. Token Rotation](#2-token-rotation)
    - [3. Backup and Recovery](#3-backup-and-recovery)
    - [4. Cleanup](#4-cleanup)
  - [Security Best Practices](#security-best-practices)
    - [1. Token Security](#1-token-security)
    - [2. Network Security](#2-network-security)
    - [3. System Security](#3-system-security)
    - [4. Container Security](#4-container-security)
  - [Performance Optimization](#performance-optimization)
    - [1. Hardware Optimization](#1-hardware-optimization)
    - [2. Configuration Tuning](#2-configuration-tuning)
    - [3. Monitoring and Tuning](#3-monitoring-and-tuning)

<!-- mdformat-toc end -->

---

## Prerequisites

1. **System Requirements**

   - Python 3.13 or higher
   - hashcat 6.2.6 or higher
   - CUDA/OpenCL drivers (for GPU support)
   - 4GB RAM minimum
   - 10GB disk space

2. **Network Requirements**

   - Outbound HTTPS access to Ouroboros server
   - Port 443 (HTTPS) or custom port accessible
   - Stable internet connection
   - Access to MinIO object storage (for resource downloads)

3. **Administrative Access**

   - Administrator must register the agent via web interface
   - Agent token provided during registration (shown only once)

## Agent Registration (Administrator)

Before installing an agent, an administrator must register it through the Ouroboros web interface:

### 1. Web Interface Registration

1. **Login as Administrator**

   - Access the Ouroboros web interface
   - Login with administrator credentials

2. **Navigate to Agent Management**

   - Go to "Agents" section
   - Click "Register New Agent"

3. **Configure Agent Details**

   ```yaml
   Agent Label: GPU-Node-01
   Description: Primary GPU cracking node
   Project Assignment:
     - Project Alpha: ✓
     - Project Beta: ✓
     - Project Gamma: ✗
   ```

4. **Generate Token**

   - Click "Create Agent"
   - **Copy the generated token immediately** (shown only once)
   - Token format: `csa_<agent_id>_<random_string>`

### 2. Project-Based Access Control

Ouroboros v2 introduces project-based organization:

- **Multi-tenancy**: Agents can be assigned to multiple projects
- **Isolation**: Agents only see tasks from assigned projects
- **Security**: Project boundaries enforce data separation
- **Management**: Administrators control project assignments

## Installation

### 1. Install Dependencies

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3.13 python3.13-venv hashcat

# RHEL/CentOS
sudo dnf install -y python3.13 hashcat

# macOS
brew install python@3.13 hashcat

# Windows
choco install python313 hashcat
```

### 2. Install Ouroboros Agent

```bash
# Create virtual environment
python3.13 -m venv .venv
source .venv/bin/activate  # Unix/macOS
# or
.venv\Scripts\activate     # Windows

# Install agent
pip install ouroboros-agent
```

## Configuration

### 1. Basic Setup

```bash
# Initialize agent
ouroboros-agent init

# Configure server connection (HTTPS required in v2)
ouroboros-agent config set server.url https://ouroboros.example.com
ouroboros-agent config set agent.token "csa_123_abc..."
ouroboros-agent config set agent.name "GPU-Node-01"
```

### 2. Authentication Configuration

Ouroboros v2 uses bearer token authentication:

```yaml
server:
  url: https://ouroboros.example.com
  verify_ssl: true
  timeout: 30

authentication:
  token: csa_123_abc...      # From web interface registration
  token_file: /etc/ouroboros/token
  token_permissions: 0600
```

### 3. Advanced Configuration

Create `agent.yaml`:

```yaml
server:
  url: https://ouroboros.example.com
  verify_ssl: true
  timeout: 30
  api_version: v1      # Agent API version

authentication:
  token: csa_123_abc...
  token_file: /etc/ouroboros/token
  token_permissions: 0600

agent:
  name: GPU-Node-01
  description: Primary GPU cracking node
  update_interval: 10    # Heartbeat interval (1-15 seconds)
    # Hardware capabilities (auto-detected)
  capabilities:
    gpus:
      - id: 0
        type: cuda
        name: NVIDIA GeForce RTX 4090
        memory: 24576
      - id: 1
        type: cuda
        name: NVIDIA GeForce RTX 4090
        memory: 24576
    cpu:
      cores: 16
      threads: 32
    memory: 65536

hashcat:
  binary: /usr/bin/hashcat
  workload: 3    # 1-4, higher = more GPU utilization
  temp_abort: 90    # Temperature abort threshold
  gpu_temp_retain: 80
  optimize: true

    # Backend configuration
  backend_ignore:
    cuda: false
    opencl: false
    hip: false
    metal: false

    # Device selection (1-indexed, comma-separated)
  backend_devices: 1,2      # Enable GPUs 1 and 2
    # Advanced options
  use_native_hashcat: false
  benchmark_all: false    # Enable additional hash types

resources:
  cache_dir: /var/cache/ouroboros
  temp_dir: /tmp/ouroboros
  max_cache: 50GB
  cleanup_interval: 3600

    # MinIO/S3 configuration for resource downloads
  download_timeout: 300
  retry_attempts: 3

performance:
  max_tasks: 5
  min_memory: 4096
  gpu_memory_limit: 90
  cpu_limit: 80

    # Performance monitoring
  metrics_interval: 60
  device_monitoring: true

monitoring:
  interval: 60
  metrics:
    - gpu_temp
    - gpu_load
    - gpu_memory
    - cpu_load
    - memory_usage
    - hash_rate

    # Error reporting
  error_reporting: true
  log_level: INFO

security:
    # TLS/SSL (recommended for production)
  cert_file: /etc/ouroboros/cert.pem
  key_file: /etc/ouroboros/key.pem
  ca_file: /etc/ouroboros/ca.pem

    # Network restrictions
  allowed_ips:
    - 192.168.1.0/24
    - 10.0.0.0/8
```

### 4. Project Context

Agents automatically receive project assignments from the server:

- **Automatic Assignment**: Projects are managed via web interface
- **Dynamic Updates**: Project assignments can change without agent restart
- **Task Filtering**: Agents only receive tasks from assigned projects
- **Resource Access**: Only resources from assigned projects are accessible

## Running the Agent

### 1. Systemd Service (Recommended)

Create `/etc/systemd/system/ouroboros-agent.service`:

```ini
[Unit]
Description=Ouroboros v2 Agent
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=ouroboros
Group=ouroboros
Environment=PATH=/usr/local/bin:/usr/bin:/bin
Environment=PYTHONUNBUFFERED=1
WorkingDirectory=/var/lib/ouroboros
ExecStart=/usr/local/bin/ouroboros-agent run --config /etc/ouroboros/agent.yaml
Restart=always
RestartSec=5
TimeoutStopSec=30

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/lib/ouroboros /var/cache/ouroboros /tmp/ouroboros

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl enable ouroboros-agent
sudo systemctl start ouroboros-agent
sudo systemctl status ouroboros-agent
```

### 2. Docker Container

```dockerfile
FROM python:3.13-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    hashcat \
    cuda-toolkit-12-0 \
    && rm -rf /var/lib/apt/lists/*

# Create user
RUN useradd -m -u 1000 ouroboros

# Install agent
RUN pip install ouroboros-agent

# Create directories
RUN mkdir -p /etc/ouroboros /var/lib/ouroboros /var/cache/ouroboros
RUN chown -R ouroboros:ouroboros /etc/ouroboros /var/lib/ouroboros /var/cache/ouroboros

# Copy configuration
COPY agent.yaml /etc/ouroboros/agent.yaml
COPY token /etc/ouroboros/token
RUN chmod 600 /etc/ouroboros/token
RUN chown ouroboros:ouroboros /etc/ouroboros/token

# Switch to non-root user
USER ouroboros
WORKDIR /var/lib/ouroboros

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD ouroboros-agent status || exit 1

# Run agent
CMD ["ouroboros-agent", "run", "--config", "/etc/ouroboros/agent.yaml"]
```

Build and run:

```bash
# Build image
docker build -t ouroboros-agent:v2 .

# Run container
docker run -d \
    --name ouroboros-agent \
    --gpus all \
    --restart unless-stopped \
    -v /etc/ouroboros:/etc/ouroboros:ro \
    -v /var/cache/ouroboros:/var/cache/ouroboros \
    -v /tmp/ouroboros:/tmp/ouroboros \
    ouroboros-agent:v2
```

### 3. Docker Compose

```yaml
version: '3.8'

services:
  ouroboros-agent:
    image: ouroboros-agent:v2
    container_name: ouroboros-agent
    restart: unless-stopped

    # GPU access
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    # Volumes
    volumes:
      - /etc/ouroboros:/etc/ouroboros:ro
      - /var/cache/ouroboros:/var/cache/ouroboros
      - /tmp/ouroboros:/tmp/ouroboros

    # Environment
    environment:
      - PYTHONUNBUFFERED=1
      - CUDA_VISIBLE_DEVICES=all

    # Health check
    healthcheck:
      test: [CMD, ouroboros-agent, status]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s

    # Logging
    logging:
      driver: json-file
      options:
        max-size: 10m
        max-file: '3'
```

## Agent Management via Web Interface

### 1. Agent Status Monitoring

Administrators can monitor agents through the web interface:

- **Real-time Status**: Online/offline, current tasks, performance
- **Hardware Information**: GPU temperatures, utilization, memory usage
- **Performance Metrics**: Hash rates, task completion times
- **Error Logs**: Agent errors and warnings

### 2. Configuration Management

#### Basic Settings

- **Enable/Disable**: Toggle agent availability
- **Update Interval**: Heartbeat frequency (1-15 seconds)
- **Project Assignment**: Multi-project access control

#### Hardware Configuration

- **Device Toggles**: Enable/disable individual GPUs/CPUs
- **Backend Selection**: CUDA, OpenCL, HIP, Metal
- **Temperature Limits**: Abort thresholds (default 90°C)
- **Workload Settings**: GPU utilization levels (1-4)

#### Advanced Options

- **Native Hashcat**: Use system hashcat instead of bundled version
- **Additional Hash Types**: Enable `--benchmark-all` for more hash types
- **Custom Configurations**: Advanced hashcat parameters

### 3. Performance Monitoring

- **Live Charts**: 8-hour performance trends
- **Device Utilization**: Per-GPU utilization percentages
- **Benchmark Results**: Hash type performance data
- **Task History**: Completed and failed task statistics

## Monitoring and Diagnostics

### 1. Log Files

```bash
# Service logs
journalctl -u ouroboros-agent -f

# Agent logs
tail -f /var/log/ouroboros/agent.log

# Docker logs
docker logs -f ouroboros-agent
```

### 2. Agent Status Commands

```bash
# Check agent status
ouroboros-agent status

# Test server connection
ouroboros-agent test connection

# Verify authentication
ouroboros-agent test auth

# Hardware diagnostics
ouroboros-agent diagnostics

# Benchmark performance
ouroboros-agent benchmark
```

### 3. Performance Metrics

The agent exposes metrics for monitoring:

```text
# Agent status
cipherswarm_agent_status{state="active"} 1

# Task metrics
cipherswarm_agent_tasks_total{status="completed"} 150
cipherswarm_agent_tasks_total{status="failed"} 5

# Hardware metrics
cipherswarm_agent_gpu_temperature{gpu="0"} 75.5
cipherswarm_agent_gpu_utilization{gpu="0"} 85.2
cipherswarm_agent_hash_rate{gpu="0"} 1250000
```

## Troubleshooting

### 1. Authentication Issues

```bash
# Check token validity
ouroboros-agent test auth

# Verify token format
echo $CIPHERSWARM_TOKEN | grep -E '^csa_[0-9]+_[a-zA-Z0-9]+$'

# Test server connectivity
curl -H "Authorization: Bearer $CIPHERSWARM_TOKEN" \
    https://ouroboros.example.com/api/v1/client/configuration
```

### 2. Project Access Issues

- **Verify Project Assignment**: Check web interface for agent's project assignments
- **Contact Administrator**: Request access to required projects
- **Check Logs**: Look for project-related error messages

### 3. Performance Issues

```bash
# Check GPU status
nvidia-smi

# Test hashcat directly
hashcat --benchmark --machine-readable

# Monitor system resources
htop
iotop
```

### 4. Common Problems

1. **Agent Not Appearing in Web Interface**

   - Verify token is correct and not expired
   - Check network connectivity to server
   - Ensure HTTPS is properly configured
   - Review agent logs for authentication errors

2. **No Tasks Assigned**

   - Verify agent is assigned to projects with active campaigns
   - Check agent is enabled in web interface
   - Ensure agent meets task requirements (GPU memory, etc.)

3. **High Resource Usage**

   - Adjust workload settings (reduce from 4 to 3 or 2)
   - Check thermal throttling with `nvidia-smi`
   - Reduce concurrent tasks in configuration
   - Monitor system memory usage

4. **Connection Timeouts**

   - Verify firewall rules allow HTTPS traffic
   - Check DNS resolution for server hostname
   - Test with `curl` or `wget` to verify connectivity
   - Review proxy settings if applicable

5. **GPU Not Detected**

   - Update GPU drivers to latest version
   - Verify CUDA installation: `nvidia-smi`
   - Check hashcat GPU detection: `hashcat -I`
   - Ensure user has GPU access permissions

## Maintenance

### 1. Updates

```bash
# Update agent software
pip install --upgrade ouroboros-agent

# Update configuration
ouroboros-agent config update

# Restart service
sudo systemctl restart ouroboros-agent

# Verify update
ouroboros-agent --version
```

### 2. Token Rotation

When tokens need to be rotated:

1. **Administrator**: Generate new token via web interface
2. **Agent**: Update configuration with new token
3. **Restart**: Restart agent service
4. **Verify**: Check agent appears online in web interface

### 3. Backup and Recovery

```bash
# Backup configuration
cp /etc/ouroboros/agent.yaml /etc/ouroboros/agent.yaml.bak
cp /etc/ouroboros/token /etc/ouroboros/token.bak

# Backup cache (optional)
tar -czf ouroboros-cache-backup.tar.gz /var/cache/ouroboros

# Recovery
cp /etc/ouroboros/agent.yaml.bak /etc/ouroboros/agent.yaml
cp /etc/ouroboros/token.bak /etc/ouroboros/token
sudo systemctl restart ouroboros-agent
```

### 4. Cleanup

```bash
# Clear cache
ouroboros-agent cleanup cache

# Remove temporary files
ouroboros-agent cleanup temp

# Reset agent (removes all local data)
ouroboros-agent reset --confirm
```

## Security Best Practices

### 1. Token Security

- **Secure Storage**: Store tokens in files with 600 permissions
- **Environment Variables**: Use environment variables for containers
- **Regular Rotation**: Rotate tokens periodically
- **Access Control**: Limit who can access token files

### 2. Network Security

- **HTTPS Only**: Always use HTTPS for server communication
- **Certificate Validation**: Verify SSL certificates
- **Firewall Rules**: Restrict outbound connections to necessary ports
- **VPN/Private Networks**: Use private networks when possible

### 3. System Security

- **Non-root User**: Run agent as dedicated non-root user
- **File Permissions**: Restrict access to configuration files
- **System Updates**: Keep system and dependencies updated
- **Monitoring**: Monitor for suspicious activity

### 4. Container Security

- **Non-root Container**: Use non-root user in containers
- **Read-only Filesystem**: Mount configuration as read-only
- **Resource Limits**: Set appropriate CPU/memory limits
- **Security Scanning**: Regularly scan container images

## Performance Optimization

### 1. Hardware Optimization

- **GPU Selection**: Use high-end GPUs for better performance
- **Memory**: Ensure sufficient system RAM (16GB+ recommended)
- **Storage**: Use SSD for cache and temporary files
- **Cooling**: Maintain proper cooling for sustained performance

### 2. Configuration Tuning

```yaml
# High-performance configuration
hashcat:
  workload: 4    # Maximum GPU utilization
  optimize: true

performance:
  max_tasks: 3    # Reduce for stability
  gpu_memory_limit: 95    # Use more GPU memory
resources:
  max_cache: 100GB    # Larger cache for better performance
```

### 3. Monitoring and Tuning

- **Temperature Monitoring**: Keep GPUs below 80°C for optimal performance
- **Utilization Tracking**: Aim for 90%+ GPU utilization
- **Memory Usage**: Monitor system and GPU memory usage
- **Task Completion**: Track task completion rates and adjust settings

For additional information:

- [Web Interface Guide](web-interface.md) - Managing agents via web interface
- [Attack Configuration](attack-configuration.md) - Understanding attack types
- [Troubleshooting Guide](troubleshooting.md) - Common issues and solutions
- [API Documentation](../api/agent.md) - Agent API reference
