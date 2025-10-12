# Common Issues and Quick Fixes

This guide covers the most frequently encountered issues in Ouroboros v2 and their quick solutions.

## Authentication Issues

### 1. Cannot Login to Web Interface

**Problem**: Login form shows "Invalid credentials" or redirects back to login page.

**Quick Fixes**:

```bash
# Clear browser cache and cookies
# Try incognito/private browsing mode
# Verify username and password are correct
# Contact administrator to verify account status
```

**Common Causes**:

- Incorrect username/password
- Account disabled or locked
- Browser cache issues
- Network connectivity problems

### 2. Frequent Token Expiration

**Problem**: Getting logged out frequently or seeing "Token expired" errors.

**Quick Fixes**:

```bash
# Check system clock synchronization
timedatectl status

# Clear browser local storage
# Logout and login again
# Check browser developer console for errors
```

**Common Causes**:

- System clock out of sync
- Browser storage issues
- Network interruptions during token refresh

### 3. Agent Authentication Failures

**Problem**: Agent shows "Authentication failed" or not connecting to server.

**Quick Fixes**:

```bash
# Verify token format
echo $CIPHERSWARM_TOKEN | grep -E '^csa_[0-9]+_[a-zA-Z0-9]+$'

# Test token validity
curl -H "Authorization: Bearer $CIPHERSWARM_TOKEN" \
    https://ouroboros.example.com/api/v1/client/configuration

# Regenerate token via web interface if needed
```

**Common Causes**:

- Invalid or expired token
- Network connectivity issues
- Agent not assigned to any projects

## Project Access Issues

### 4. No Projects Available

**Problem**: Empty project dropdown or "No projects assigned" message.

**Quick Fixes**:

```bash
# Contact administrator for project assignment
# Verify user account has appropriate role
# Check if projects exist in the system
# Refresh browser page
```

**Common Causes**:

- User not assigned to any projects
- All projects deleted or archived
- Permission/role issues

### 5. Cannot See Campaigns or Resources

**Problem**: Empty lists when viewing campaigns, attacks, or resources.

**Quick Fixes**:

```bash
# Check current project selection in header
# Switch to different project if available
# Verify user role and permissions
# Contact administrator for access
```

**Common Causes**:

- Wrong project context selected
- Insufficient permissions for current project
- No data exists in selected project

## Agent Issues

### 6. Agent Not Appearing Online

**Problem**: Agent shows as "Offline" in web interface despite running locally.

**Quick Fixes**:

```bash
# Check agent status
systemctl status ouroboros-agent

# Verify network connectivity
ping ouroboros.example.com

# Check agent logs
journalctl -u ouroboros-agent -f

# Test authentication
ouroboros-agent test auth
```

**Common Causes**:

- Network connectivity issues
- Authentication problems
- Agent not assigned to projects
- Firewall blocking connections

### 7. Low Agent Performance

**Problem**: Agent hash rates significantly lower than expected.

**Quick Fixes**:

```bash
# Check GPU temperatures
nvidia-smi

# Verify GPU utilization
watch -n 1 nvidia-smi

# Increase workload setting
# Check for thermal throttling
# Verify adequate power supply
```

**Common Causes**:

- Thermal throttling
- Insufficient power supply
- Driver issues
- Suboptimal configuration

### 8. Agent Task Failures

**Problem**: Tasks marked as "Failed" with agent errors.

**Quick Fixes**:

```bash
# Check agent logs for errors
journalctl -u ouroboros-agent --since "1 hour ago"

# Test hashcat directly
hashcat --benchmark

# Verify available memory
free -h

# Check disk space
df -h
```

**Common Causes**:

- Insufficient GPU memory
- Hashcat crashes
- Resource download failures
- System resource limitations

## Campaign and Attack Issues

### 9. Campaign Won't Start

**Problem**: Campaign remains in "Draft" state or "Start Campaign" button disabled.

**Quick Fixes**:

```bash
# Verify hash list is assigned
# Check that attacks are properly configured
# Ensure at least one agent is online and available
# Verify all required resources exist
```

**Common Causes**:

- Missing hash list assignment
- Invalid attack configuration
- No available agents
- Missing or inaccessible resources

### 10. No Tasks Generated

**Problem**: Campaign shows "Running" but no progress or tasks assigned.

**Quick Fixes**:

```bash
# Check agent project assignments
# Verify agents are enabled and online
# Check attack configuration validity
# Look for task generation errors in logs
```

**Common Causes**:

- Agents not assigned to campaign's project
- Keyspace too small for distribution
- Invalid attack parameters
- Agent capability mismatches

### 11. Attack Validation Errors

**Problem**: Cannot save attack configuration with validation errors.

**Quick Fixes**:

```bash
# Check resource file formats and syntax
# Verify mask patterns are valid
# Ensure rule files use correct syntax
# Check for resource accessibility
```

**Common Causes**:

- Invalid mask syntax (e.g., `?x?d?d` with unknown charset `?x`)
- Malformed rule files
- Missing or inaccessible resources
- Incompatible hash type settings

## Resource Management Issues

### 12. Upload Failures

**Problem**: Resource uploads fail or files don't appear in resource list.

**Quick Fixes**:

```bash
# Check file size and format
ls -lh wordlist.txt

# Verify file encoding
file wordlist.txt

# Test upload connectivity
curl -I https://ouroboros.example.com/api/v1/web/resources/

# Try smaller files first
```

**Common Causes**:

- File too large for upload limits
- Network timeout during upload
- Invalid file format or encoding
- Storage space limitations

### 13. Resource Access Denied

**Problem**: Resources not visible in dropdowns or "Access denied" errors.

**Quick Fixes**:

```bash
# Verify resource is assigned to current project
# Check user role and permissions
# Contact administrator for resource access
# Switch to correct project context
```

**Common Causes**:

- Resource not assigned to current project
- Insufficient user permissions
- Resource marked as private/restricted

### 14. Line Editing Not Working

**Problem**: Cannot edit resources inline or changes not saving.

**Quick Fixes**:

```bash
# Check file size (must be under 5MB)
# Verify line count (must be under 10,000 lines)
# Check for syntax errors in edits
# Ensure user has edit permissions
```

**Common Causes**:

- File too large for inline editing
- Invalid syntax in edited content
- Insufficient permissions
- Resource marked as read-only

## Live Updates and SSE Issues

### 15. Real-time Updates Not Working

**Problem**: Dashboard not updating automatically or stale data displayed.

**Quick Fixes**:

```javascript
// Check EventSource support in browser console
if (typeof EventSource !== "undefined") {
    console.log("SSE supported");
} else {
    console.log("SSE not supported - try different browser");
}
```

Test SSE endpoint manually:

```bash
curl -H "Accept: text/event-stream" -H "Authorization: Bearer $TOKEN" https://ouroboros.example.com/api/v1/web/live/campaigns
```

**Common Causes**:

- Browser doesn't support EventSource
- Network proxy buffering SSE streams
- Firewall blocking persistent connections
- JavaScript errors preventing updates

### 16. Frequent Connection Drops

**Problem**: "Connection lost" notifications or intermittent update failures.

**Quick Fixes**:

```bash
# Test network stability
ping -c 100 ouroboros.example.com

# Check for packet loss
mtr ouroboros.example.com

# Try different browser
# Disable browser power saving features
# Check proxy/VPN settings
```

**Common Causes**:

- Unstable network connection
- Aggressive browser power management
- Proxy/VPN interference
- Server-side connection limits

### 17. "Real-time updates disconnected" Toast Message

**Problem**: Toast notification appears saying "Real-time updates disconnected. Please refresh the page."

**What This Means**:

This message appears when the system has exhausted all automatic reconnection attempts for real-time updates (Server-Sent Events). The system tries to reconnect 5 times with exponential backoff delays before giving up.

**Quick Fixes**:

```bash
# Click the "Refresh Now" button in the yellow warning banner
# Alternatively, refresh the entire page (F5 or Ctrl+R)
# Check network connectivity
# Try switching to a different network if available
```

**When You'll See This**:

- Network connectivity issues lasting more than ~30 seconds
- Proxy or firewall blocking persistent connections
- Server maintenance or temporary outages
- Browser power saving features interrupting connections

**What Happens Next**:

- Dashboard data becomes "stale" and shows a warning indicator
- You can manually refresh data using the "Refresh Now" button
- Real-time updates will resume when you refresh or navigate to a new page
- Your session and authentication remain valid

## Performance Issues

### 18. Slow Web Interface

**Problem**: Pages load slowly or UI elements are unresponsive.

**Quick Fixes**:

```bash
# Clear browser cache and cookies
# Disable browser extensions
# Try incognito/private mode
# Check available system memory
# Test with different browser
```

**Common Causes**:

- Browser cache issues
- Insufficient system memory
- Network latency
- Server performance issues

### 19. High System Resource Usage

**Problem**: High CPU, memory, or disk usage affecting performance.

**Quick Fixes**:

```bash
# Check system resources
htop
free -h
df -h

# Monitor GPU usage
nvidia-smi

# Reduce concurrent tasks
# Lower agent workload settings
# Check for runaway processes
```

**Common Causes**:

- Too many concurrent tasks
- Memory leaks
- Inefficient resource usage
- Hardware limitations

## Hash List and Data Issues

### 20. Hash Type Detection Failures

**Problem**: System cannot detect hash type or shows incorrect detection.

**Quick Fixes**:

```bash
# Manually specify hash type
# Check hash format consistency
# Verify hash length and character set
# Remove invalid or malformed hashes
```

**Common Causes**:

- Mixed hash types in single list
- Malformed hash strings
- Unsupported hash formats
- Encoding issues

### 21. Crackable Upload Errors

**Problem**: Uploaded files fail to process or extract hashes.

**Quick Fixes**:

```bash
# Check file format support
# Verify file is not corrupted
# Try extracting hashes manually first
# Check file size limitations
```

**Common Causes**:

- Unsupported file format
- Corrupted or encrypted files
- File size exceeding limits
- Processing timeout

## Quick Diagnostic Commands

### System Health Check

```bash
# Check all system components
curl https://ouroboros.example.com/api/v1/web/health/components

# Test database connectivity
curl https://ouroboros.example.com/api/v1/web/health/database

# Check MinIO storage
curl https://minio.example.com/health/live
```

### Agent Diagnostics

```bash
# Agent status and configuration
ouroboros-agent status
ouroboros-agent config show

# Test connectivity
ouroboros-agent test connection

# Benchmark performance
ouroboros-agent benchmark

# Check logs
journalctl -u ouroboros-agent --since "1 hour ago"
```

### Network Diagnostics

```bash
# Test server connectivity
ping ouroboros.example.com
curl -I https://ouroboros.example.com

# Check DNS resolution
nslookup ouroboros.example.com

# Test API endpoints
curl -H "Authorization: Bearer $TOKEN" \
    https://ouroboros.example.com/api/v1/client/configuration
```

### Browser Diagnostics

```javascript
// Check browser console for errors
// Open Developer Tools (F12) and check:
// - Console tab for JavaScript errors
// - Network tab for failed requests
// - Application tab for storage issues

// Test EventSource support
console.log("EventSource supported:", typeof EventSource !== "undefined");

// Check local storage
console.log("Local storage:", localStorage.getItem('ouroboros-token'));
```

## When to Contact Support

Contact your administrator or support team when:

1. **Security Issues**: Any suspected security breaches or unauthorized access
2. **Data Loss**: Missing campaigns, attacks, or results
3. **System Outages**: Complete system unavailability
4. **Performance Degradation**: Significant system-wide performance issues
5. **Configuration Issues**: Problems requiring administrative access

## Information to Provide

When reporting issues, include:

1. **Error Messages**: Exact error text and error codes
2. **Steps to Reproduce**: Detailed steps that led to the issue
3. **Environment**: Browser version, OS, agent configuration
4. **Timing**: When the issue started and frequency
5. **Logs**: Relevant log entries and timestamps
6. **Screenshots**: Visual evidence of the problem

For comprehensive troubleshooting, see the [Troubleshooting Guide](troubleshooting.md).
