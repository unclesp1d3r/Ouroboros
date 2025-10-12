# Troubleshooting Guide

This guide covers common issues and solutions for Ouroboros v2.

---

## Table of Contents

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=2 --minlevel=1 -->

- [Troubleshooting Guide](#troubleshooting-guide)
  - [Table of Contents](#table-of-contents)
  - [Authentication Issues](#authentication-issues)
  - [Project Access Issues](#project-access-issues)
  - [Agent Issues](#agent-issues)
  - [Campaign and Attack Issues](#campaign-and-attack-issues)
  - [Resource Management Issues](#resource-management-issues)
  - [Live Updates and Real-Time Features](#live-updates-and-real-time-features)
  - [Performance Issues](#performance-issues)
  - [Storage and MinIO Issues](#storage-and-minio-issues)
  - [System Health Issues](#system-health-issues)
  - [Getting Help](#getting-help)

<!-- mdformat-toc end -->

---

## Authentication Issues

### 1. Login Problems

#### Cannot Login to Web Interface

**Symptoms:**

- Login form shows "Invalid credentials"
- Redirected back to login page
- No error message displayed

**Solutions:**

1. **Verify Credentials**

   - Check if user exists in the system
   - Contact administrator to verify account status
   - Ensure correct email format is used

2. **Check Account Status**

   - Account may be disabled (`is_active = false`)
   - Contact administrator to verify account status
   - Check if account has been locked due to failed attempts

3. **Browser Issues**

   - Clear browser cache and cookies
   - Try incognito/private browsing mode
   - Disable browser extensions
   - Try different browser

4. **Network Connectivity**

   ```bash
   # Test HTTPS connectivity
   curl -I https://ouroboros.example.com/api/v1/web/auth/me

   # Check for proxy/firewall issues
   # Verify DNS resolution
   nslookup ouroboros.example.com
   ```

#### JWT Token Issues

**Symptoms:**

- "Token expired" errors
- Frequent re-login prompts
- API calls return 401 Unauthorized

**Solutions:**

1. **Token Refresh**

   - Tokens automatically refresh via `/api/v1/web/auth/refresh` endpoint
   - Manual refresh: Logout and login again
   - Check browser developer tools for token errors

2. **Cookie Issues**

   - Ensure cookies are enabled in browser
   - Check that `access_token` cookie is being set
   - Verify cookie domain and path settings
   - Clear browser cookies for the site

3. **Clock Synchronization**

   ```bash
   # Ensure system clock is synchronized
   timedatectl status
   ntpdate -s time.nist.gov
   ```

### 2. Agent Authentication

#### Agent Not Connecting

**Symptoms:**

- Agent shows "Authentication failed"
- Agent not visible in web interface
- Connection timeouts

**Solutions:**

1. **Verify Token**

   ```bash
   # Check token format (should start with csa_)
   echo $CIPHERSWARM_TOKEN | grep -E '^csa_[0-9]+_[a-zA-Z0-9]+$'

   # Test token validity
   curl -H "Authorization: Bearer $CIPHERSWARM_TOKEN" \
       https://ouroboros.example.com/api/v1/client/configuration
   ```

2. **Token Regeneration**

   - Administrator must generate new token via web interface
   - Update agent configuration with new token
   - Restart agent service

3. **Network Configuration**

   ```bash
   # Test HTTPS connectivity
   curl -v https://ouroboros.example.com/api/v1/client/configuration

   # Check firewall rules
   # Verify outbound HTTPS (port 443) is allowed
   ```

## Project Access Issues

### 1. No Projects Available

**Symptoms:**

- Empty project dropdown
- "No projects assigned" message
- Cannot create campaigns

**Solutions:**

1. **Contact Administrator**

   - Request project assignment
   - Verify user role and permissions
   - Check if projects exist in system

2. **Check Project Context**

   - Verify current project selection in header
   - Try switching projects if multiple are available
   - Refresh browser page

### 2. Limited Functionality

**Symptoms:**

- Cannot see certain campaigns/attacks
- Missing resources in dropdowns
- "Access denied" errors

**Solutions:**

1. **Verify Project Assignment**

   - Check which projects you're assigned to
   - Contact administrator for additional access
   - Verify project-specific permissions

2. **Role-Based Access**

   ```yaml
   User Roles:
     - user: Basic access, view-only for most features
     - power_user: Can create campaigns and attacks
     - admin: Full system access
   ```

## Agent Issues

### 1. Agent Not Appearing Online

**Symptoms:**

- Agent shows as "Offline" in web interface
- No heartbeat received
- Agent appears to be running locally

**Solutions:**

1. **Check Agent Status**

   ```bash
   # Verify agent is running
   systemctl status ouroboros-agent

   # Check agent logs
   journalctl -u ouroboros-agent -f

   # Test agent connectivity
   ouroboros-agent test connection
   ```

2. **Network Connectivity**

   ```bash
   # Test server reachability
   ping ouroboros.example.com

   # Test HTTPS connectivity
   curl -I https://ouroboros.example.com

   # Check for proxy/firewall blocking
   ```

3. **Configuration Issues**

   ```bash
   # Verify configuration
   ouroboros-agent config show

   # Test authentication
   ouroboros-agent test auth

   # Check token validity
   ouroboros-agent verify token
   ```

### 2. Agent Performance Issues

#### Low Hash Rates

**Symptoms:**

- Significantly lower than expected performance
- GPU utilization below 90%
- Thermal throttling warnings

**Solutions:**

1. **Hardware Monitoring**

   ```bash
   # Check GPU status
   nvidia-smi

   # Monitor temperatures
   watch -n 1 nvidia-smi

   # Check for thermal throttling
   nvidia-smi -q -d TEMPERATURE
   ```

2. **Configuration Tuning**

   ```yaml
   # Increase workload (1-4)
   hashcat:
     workload: 4

   # Optimize GPU settings
   performance:
     gpu_memory_limit: 95
     max_tasks: 2    # Reduce for stability
   ```

3. **System Resources**

   ```bash
   # Check system memory
   free -h

   # Monitor CPU usage
   htop

   # Check disk I/O
   iotop
   ```

#### Task Failures

**Symptoms:**

- Tasks marked as "Failed"
- Agent errors in logs
- Hashcat crashes

**Solutions:**

1. **Check Agent Logs**

   ```bash
   # View recent errors
   journalctl -u ouroboros-agent --since "1 hour ago"

   # Check for specific error patterns
   grep -i error /var/log/ouroboros/agent.log
   ```

2. **Hashcat Issues**

   ```bash
   # Test hashcat directly
   hashcat --benchmark

   # Check GPU detection
   hashcat -I

   # Verify drivers
   nvidia-smi
   ```

3. **Resource Issues**

   ```bash
   # Check available memory
   free -h

   # Verify disk space
   df -h

   # Check for file permission issues
   ls -la /var/cache/ouroboros/
   ```

## Campaign and Attack Issues

### 1. Campaigns Not Starting

**Symptoms:**

- Campaign remains in "Draft" state
- No tasks generated
- "Start Campaign" button disabled

**Solutions:**

1. **Verify Configuration**

   - Ensure hash list is assigned
   - Check that attacks are properly configured
   - Verify at least one agent is available and enabled

2. **Check Dependencies**

   - Verify all required resources exist in MinIO storage
   - Check resource accessibility via presigned URLs
   - Ensure hash list contains valid hashes

3. **Agent Availability**

   - Verify agents are online and enabled
   - Check agent project assignments via `ProjectUserAssociation`
   - Ensure agents meet attack requirements

### 2. No Tasks Assigned to Agents

**Symptoms:**

- Campaign shows "Running" but no progress
- Agents show "Idle" status
- No tasks in agent task list

**Solutions:**

1. **Agent Compatibility**

   ```bash
   # Check agent capabilities
   ouroboros-agent capabilities

   # Verify GPU memory requirements
   # Check hash type support
   ```

2. **Project Assignment**

   - Verify agents are assigned to campaign's project
   - Check agent enable/disable status
   - Confirm agent authentication

3. **Task Generation**

   - Check if keyspace is too small
   - Verify attack configuration is valid
   - Look for task generation errors in logs

### 3. Attack Validation Errors

**Symptoms:**

- Cannot save attack configuration
- "Validation failed" messages
- Red error indicators in attack editor

**Solutions:**

1. **Resource Validation**

   ```text
   Common Issues:
   - Wordlist file not found in MinIO
   - Invalid mask syntax
   - Rule file format errors
   - Charset definition problems
   ```

2. **Configuration Conflicts**

   ```yaml
   # Check for incompatible settings
   dictionary_attack:
     wordlist: required
     rules: optional
     min_length: must be <= max_length
   ```

3. **Hash Type Compatibility**

   - Verify hash type supports selected attack mode
   - Check for mode-specific requirements
   - Ensure sufficient GPU memory

## Resource Management Issues

### 1. Upload Failures

**Symptoms:**

- Upload progress stops
- "Upload failed" errors
- Files not appearing in resource list

**Solutions:**

1. **File Size and Format**

   ```bash
   # Check file size (default limit: 100MB for crackable uploads)
   ls -lh wordlist.txt

   # Verify file format
   file wordlist.txt

   # Check for binary content in text files
   hexdump -C wordlist.txt | head
   ```

2. **Network Issues**

   ```bash
   # Test upload connectivity
   curl -I https://ouroboros.example.com/api/v1/web/resources/

   # Check for timeout issues
   # Verify stable internet connection
   ```

3. **Storage Issues**

   - Check MinIO storage availability
   - Verify disk space on server
   - Contact administrator for storage limits

### 2. Resource Access Denied

**Symptoms:**

- Resources not visible in dropdowns
- "Access denied" when selecting resources
- Empty resource browser

**Solutions:**

1. **Project Scoping**

   - Verify resource is assigned to current project
   - Check if resource is marked as global
   - Contact administrator for access

2. **Permission Issues**

   - Verify user role allows resource access
   - Check resource-specific permissions
   - Ensure user is in correct project

### 3. Line Editing Issues

**Symptoms:**

- Cannot edit resource inline
- "Edit" button disabled
- Changes not saving

**Solutions:**

1. **Size Limitations**

- Edit Restrictions
  - Files over 1MB require download/reupload (RESOURCE_EDIT_MAX_SIZE_MB)
  - Resources with >5,000 lines not editable (RESOURCE_EDIT_MAX_LINES)
  - Binary files cannot be edited inline

1. **Validation Errors**

- Common Validation Issues
  - Invalid mask syntax: ?x?d?d (unknown charset ?x)
  - Invalid rule syntax: +rfoo (unknown operator f)
  - Encoding issues: non-ASCII characters in ASCII-only files

1. **Permission Issues**

   - Verify edit permissions for resource
   - Check if resource is read-only
   - Ensure user has power_user or admin role

## Live Updates and Real-Time Features

### 1. Real-time Updates Not Working

**Symptoms:**

- Dashboard not updating automatically
- Campaign progress not refreshing
- Agent status appears stale

**Solutions:**

1. **Browser Compatibility**

   ```javascript
   // Check EventSource support
   if (typeof EventSource !== "undefined") {
       console.log("SSE supported");
   } else {
       console.log("SSE not supported");
   }
   ```

2. **Network Configuration**

   ```bash
   # Test SSE endpoint
   curl -H "Accept: text/event-stream" \
       -H "Authorization: Bearer $TOKEN" \
       https://ouroboros.example.com/api/v1/web/live/campaigns
   ```

3. **Proxy/Firewall Issues**

   - Check if proxy buffers SSE streams
   - Verify firewall allows persistent connections
   - Test with direct connection (bypass proxy)

### 2. Connection Drops

**Symptoms:**

- Frequent reconnection messages
- Intermittent update failures
- "Connection lost" notifications

**Solutions:**

1. **Network Stability**

   ```bash
   # Test connection stability
   ping -c 100 ouroboros.example.com

   # Check for packet loss
   mtr ouroboros.example.com
   ```

2. **Browser Settings**

   - Disable aggressive power saving
   - Check browser connection limits
   - Try different browser

3. **Server Configuration**

   - Contact administrator about SSE timeout settings
   - Check server load and performance
   - Verify SSE endpoint health

## Performance Issues

### 1. Slow Web Interface

**Symptoms:**

- Pages load slowly
- Unresponsive UI elements
- Timeout errors

**Solutions:**

1. **Browser Performance**

   - Clear browser cache
   - Disable unnecessary extensions
   - Check available memory
   - Try incognito mode

2. **Network Latency**

   ```bash
   # Test latency to server
   ping ouroboros.example.com

   # Check bandwidth
   speedtest-cli

   # Test API response times
   curl -w "@curl-format.txt" https://ouroboros.example.com/api/v1/web/dashboard/summary
   ```

3. **Server Load**

   - Contact administrator about server performance
   - Check if maintenance is scheduled
   - Verify system resources

### 2. Database Performance

**Symptoms:**

- Slow query responses
- Timeout errors
- High CPU usage on server

**Solutions:**

1. **Query Optimization**

   - Contact administrator about database performance
   - Check for missing indexes
   - Review slow query logs

2. **Data Volume**

   - Large hash lists may impact performance
   - Consider archiving old campaigns
   - Optimize resource usage

## Storage and MinIO Issues

### 1. Resource Download Failures

**Symptoms:**

- Agents cannot download resources
- "Resource not found" errors
- Presigned URL failures

**Solutions:**

1. **MinIO Connectivity**

   ```bash
   # Test MinIO endpoint
   curl -I https://minio.example.com/health/live

   # Check presigned URL
   curl -I "$PRESIGNED_URL"
   ```

2. **Network Configuration**

   - Verify agents can reach MinIO endpoint
   - Check firewall rules for MinIO ports
   - Test DNS resolution for MinIO hostname

3. **Storage Issues**

   - Check MinIO disk space
   - Verify bucket permissions
   - Contact administrator for storage health

### 2. Upload Corruption

**Symptoms:**

- Uploaded files appear corrupted
- Checksum mismatches
- Download failures

**Solutions:**

1. **Integrity Verification**

   ```bash
   # Check file checksums
   sha256sum original_file.txt

   # Compare with stored checksum
   # Verify file size matches
   ```

2. **Network Issues**

   - Check for network packet loss
   - Verify stable connection during upload
   - Try uploading smaller files first

3. **Storage Verification**

   - Contact administrator about storage integrity
   - Check MinIO error logs
   - Verify backup and recovery procedures

## System Health Issues

### 1. Component Failures

**Symptoms:**

- Health dashboard shows red status
- Service unavailable errors
- Partial functionality loss

**Solutions:**

1. **Check Component Status**

   ```bash
   # Database connectivity
   curl https://ouroboros.example.com/api/v1/web/health/components

   # Individual service health
   # Check system logs
   ```

2. **Service Recovery**

   - Contact administrator immediately
   - Check if maintenance is in progress
   - Verify backup systems are available

### 2. Performance Degradation

**Symptoms:**

- Slow response times
- High resource usage
- Frequent timeouts

**Solutions:**

1. **Monitor System Resources**

   - Check CPU, memory, and disk usage
   - Monitor network bandwidth
   - Review system logs for errors

2. **Load Balancing**

   - Contact administrator about system load
   - Check if additional resources are needed
   - Verify scaling configuration

## Getting Help

### 1. Log Collection

When reporting issues, collect relevant logs:

```bash
# Web interface issues
# Browser developer console logs
# Network tab for failed requests

# Agent issues
journalctl -u ouroboros-agent --since "1 hour ago" > agent.log

# System issues
# Server logs (admin access required)
# Database logs
# MinIO logs
```

### 2. Information to Include

When contacting support:

1. **Environment Details**

   - Ouroboros version
   - Browser type and version (for web issues)
   - Operating system
   - Agent configuration (for agent issues)

2. **Problem Description**

   - Exact error messages
   - Steps to reproduce
   - When the issue started
   - Frequency of occurrence

3. **System State**

   - Current project context
   - Active campaigns/attacks
   - Agent status
   - Recent configuration changes

### 3. Emergency Procedures

For critical issues:

1. **System Outage**

   - Contact administrator immediately
   - Document current state
   - Prepare for potential data recovery

2. **Security Incidents**

   - Report immediately to security team
   - Do not attempt to fix security issues
   - Preserve logs and evidence

3. **Data Loss**

   - Stop all operations immediately
   - Contact administrator
   - Do not attempt recovery without guidance

For additional support:

- [Agent Setup Guide](agent-setup.md) - Agent-specific troubleshooting
- [Web Interface Guide](web-interface.md) - UI-related issues
- [Resource Management Guide](resource-management.md) - Resource problems
- [FAQ](faq.md) - Frequently asked questions
