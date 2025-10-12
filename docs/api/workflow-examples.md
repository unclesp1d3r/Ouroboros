# API Workflow Examples

This document provides detailed workflow examples for common Ouroboros operations across all API interfaces.

## Table of Contents

- [Campaign Creation and Management](#campaign-creation-and-management)
- [Agent Registration and Task Execution](#agent-registration-and-task-execution)
- [Hash Analysis and Type Detection](#hash-analysis-and-type-detection)
- [Resource Management](#resource-management)
- [Real-time Monitoring](#real-time-monitoring)
- [Batch Operations](#batch-operations)
- [Error Recovery Scenarios](#error-recovery-scenarios)

## Campaign Creation and Management

### Complete Campaign Lifecycle (Web UI API)

This workflow demonstrates creating, configuring, and managing a campaign through the Web UI API.

#### Step 1: Authentication and Project Context

```bash
# Login and get JWT tokens
curl -X POST \
    -H "Content-Type: application/json" \
    -d '{
        "email": "admin@example.com",
        "password": "secure_password"
    }' \
    -c cookies.txt \
    "https://api.example.com/api/v1/web/auth/login"

# Get current context
curl -b cookies.txt \
    "https://api.example.com/api/v1/web/auth/context"

# Switch to specific project if needed
curl -X POST \
    -H "Content-Type: application/json" \
    -d '{"project_id": 1}' \
    -b cookies.txt \
    "https://api.example.com/api/v1/web/auth/context"
```

#### Step 2: Create Hash List

```bash
# Create new hash list
curl -X POST \
    -H "Content-Type: application/json" \
    -d '{
        "name": "Corporate Domain Hashes",
        "description": "NTLM hashes from domain controller",
        "hash_type": 1000,
        "project_id": 1
    }' \
    -b cookies.txt \
    "https://api.example.com/api/v1/web/hash_lists/"

# Response includes hash list ID
{
    "id": 123,
    "name": "Corporate Domain Hashes",
    "hash_type": 1000,
    "hash_count": 0,
    "project_id": 1,
    "created_at": "2024-01-01T12:00:00Z"
}
```

#### Step 3: Upload Hash Data

```bash
# Upload hash file or paste hashes
curl -X POST \
    -F "file=@domain_hashes.txt" \
    -F "hash_list_id=123" \
    -b cookies.txt \
    "https://api.example.com/api/v1/web/uploads/"

# Or paste hashes directly
curl -X POST \
    -H "Content-Type: application/json" \
    -d '{
        "hash_input": "user1:1000:aad3b435b51404eeaad3b435b51404ee:8846f7eaee8fb117ad06bdd830b7586c:::\nuser2:1001:aad3b435b51404eeaad3b435b51404ee:e19ccf75ee54e06b06a5907af13cef42:::",
        "hash_list_id": 123
    }' \
    -b cookies.txt \
    "https://api.example.com/api/v1/web/uploads/"
```

#### Step 4: Create Campaign

```bash
# Create campaign
curl -X POST \
    -H "Content-Type: application/json" \
    -d '{
        "name": "Corporate Password Recovery 2024",
        "description": "Recovering passwords from corporate domain controller dump",
        "project_id": 1,
        "hash_list_id": 123,
        "priority": 50
    }' \
    -b cookies.txt \
    "https://api.example.com/api/v1/web/campaigns/"

# Response includes campaign details
{
    "id": 456,
    "name": "Corporate Password Recovery 2024",
    "state": "draft",
    "project_id": 1,
    "hash_list_id": 123,
    "priority": 50,
    "created_at": "2024-01-01T12:30:00Z"
}
```

#### Step 5: Add Attacks to Campaign

```bash
# Add dictionary attack
curl -X POST \
    -H "Content-Type: application/json" \
    -d '{
        "name": "Dictionary Attack - Common Passwords",
        "description": "Using rockyou.txt wordlist",
        "campaign_id": 456,
        "attack_mode": "dictionary",
        "wordlist_id": 1,
        "rulelist_id": 2,
        "position": 1
    }' \
    -b cookies.txt \
    "https://api.example.com/api/v1/web/campaigns/456/add_attack"

# Add mask attack
curl -X POST \
    -H "Content-Type: application/json" \
    -d '{
        "name": "Mask Attack - 8 Digit Numeric",
        "description": "Common 8-digit numeric patterns",
        "campaign_id": 456,
        "attack_mode": "mask",
        "mask_list": ["?d?d?d?d?d?d?d?d"],
        "position": 2
    }' \
    -b cookies.txt \
    "https://api.example.com/api/v1/web/campaigns/456/add_attack"

# Add hybrid attack
curl -X POST \
    -H "Content-Type: application/json" \
    -d '{
        "name": "Hybrid Dictionary + Mask",
        "description": "Dictionary words with numeric suffixes",
        "campaign_id": 456,
        "attack_mode": "hybrid_dict",
        "wordlist_id": 3,
        "mask_list": ["?d?d", "?d?d?d", "?d?d?d?d"],
        "position": 3
    }' \
    -b cookies.txt \
    "https://api.example.com/api/v1/web/campaigns/456/add_attack"
```

#### Step 6: Validate and Start Campaign

```bash
# Get campaign details to verify configuration
curl -b cookies.txt \
    "https://api.example.com/api/v1/web/campaigns/456"

# Start campaign execution
curl -X POST \
    -b cookies.txt \
    "https://api.example.com/api/v1/web/campaigns/456/start"

# Verify campaign started
curl -b cookies.txt \
    "https://api.example.com/api/v1/web/campaigns/456/progress"
```

#### Step 7: Monitor Progress with SSE

```javascript
// JavaScript example for real-time monitoring
const eventSource = new EventSource(
    "https://api.example.com/api/v1/web/live/campaigns", {
        withCredentials: true
    }
);

eventSource.onmessage = function(event) {
    const data = JSON.parse(event.data);

    if (
        data.trigger === "refresh" &&
        data.target === "campaign" &&
        data.id === 456
    ) {
        // Refresh campaign data
        fetch("/api/v1/web/campaigns/456/progress", {
                credentials: "include"
            })
            .then((response) => response.json())
            .then((progress) => {
                console.log(`Campaign progress: ${progress.percent_complete}%`);
                console.log(
                    `Cracked hashes: ${progress.cracked_count}/${progress.total_count}`
                );
            });
    }
};
```

### Campaign Management via Control API

```bash
# Set API key
export CIPHERSWARM_API_KEY="cst_123_abc123def456..."

# List campaigns
curl -H "Authorization: Bearer $CIPHERSWARM_API_KEY" \
    "https://api.example.com/api/v1/control/campaigns/?state=active"

# Get campaign status
curl -H "Authorization: Bearer $CIPHERSWARM_API_KEY" \
    "https://api.example.com/api/v1/control/campaigns/456/status"

# Stop campaign
curl -X POST \
    -H "Authorization: Bearer $CIPHERSWARM_API_KEY" \
    "https://api.example.com/api/v1/control/campaigns/456/stop"

# Export campaign configuration
curl -X POST \
    -H "Authorization: Bearer $CIPHERSWARM_API_KEY" \
    "https://api.example.com/api/v1/control/campaigns/456/export" \
    -o campaign_456_config.json
```

## Agent Registration and Task Execution

### Complete Agent Workflow (Agent API)

This workflow shows the complete lifecycle of an agent from registration to task completion.

#### Step 1: Agent Registration

```bash
# Register new agent
curl -X POST \
    -H "Content-Type: application/json" \
    -d '{
        "client_signature": "Ouroboros-Agent/2.1.0",
        "hostname": "gpu-worker-01.corp.local",
        "operating_system": "linux",
        "devices": [
            {
                "device_id": 0,
                "device_name": "NVIDIA RTX 4090",
                "device_type": "GPU"
            },
            {
                "device_id": 1,
                "device_name": "NVIDIA RTX 4090",
                "device_type": "GPU"
            }
        ]
    }' \
    "https://api.example.com/api/v1/client/agents"

# Response includes agent token
{
    "id": 789,
    "token": "csa_789_xyz987abc654...",
    "client_signature": "Ouroboros-Agent/2.1.0",
    "hostname": "gpu-worker-01.corp.local"
}
```

#### Step 2: Authentication and Configuration

```bash
# Store token for subsequent requests
export AGENT_TOKEN="csa_789_xyz987abc654..."

# Verify authentication
curl -H "Authorization: Bearer $AGENT_TOKEN" \
    "https://api.example.com/api/v1/client/authenticate"

# Get agent configuration
curl -H "Authorization: Bearer $AGENT_TOKEN" \
    "https://api.example.com/api/v1/client/configuration"

# Response includes configuration
{
    "config": {
        "agent_update_interval": 30,
        "use_native_hashcat": false,
        "backend_device": "1,2",
        "opencl_devices": "1,2",
        "enable_additional_hash_types": true
    },
    "api_version": 1
}
```

#### Step 3: Initial Heartbeat and Benchmarks

```bash
# Send initial heartbeat
curl -X POST \
    -H "Authorization: Bearer $AGENT_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "status": "idle",
        "current_task_id": null,
        "devices_status": {
            "GPU0": "ready",
            "GPU1": "ready"
        }
    }' \
    "https://api.example.com/api/v1/client/agents/789/heartbeat"

# Submit benchmark results for common hash types
curl -X POST \
    -H "Authorization: Bearer $AGENT_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "hash_type": 0,
        "runtime": 1000,
        "hash_speed": 15000000.0,
        "device": 0
    }' \
    "https://api.example.com/api/v1/client/agents/789/submit_benchmark"

curl -X POST \
    -H "Authorization: Bearer $AGENT_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "hash_type": 1000,
        "runtime": 1000,
        "hash_speed": 8500000.0,
        "device": 0
    }' \
    "https://api.example.com/api/v1/client/agents/789/submit_benchmark"
```

#### Step 4: Task Request and Acceptance

```bash
# Request new task
curl -H "Authorization: Bearer $AGENT_TOKEN" \
    "https://api.example.com/api/v1/client/tasks/new"

# Response includes task assignment
{
    "id": 1001,
    "attack_id": 2001,
    "keyspace_start": 0,
    "keyspace_end": 10000000,
    "status": "pending",
    "priority": 50,
    "created_at": "2024-01-01T13:00:00Z"
}

# Accept the task
curl -X POST \
    -H "Authorization: Bearer $AGENT_TOKEN" \
    "https://api.example.com/api/v1/client/tasks/1001/accept_task"

# Update heartbeat with current task
curl -X POST \
    -H "Authorization: Bearer $AGENT_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "status": "running",
        "current_task_id": 1001,
        "devices_status": {
            "GPU0": "running",
            "GPU1": "running"
        }
    }' \
    "https://api.example.com/api/v1/client/agents/789/heartbeat"
```

#### Step 5: Get Attack Configuration and Resources

```bash
# Get attack details
curl -H "Authorization: Bearer $AGENT_TOKEN" \
    "https://api.example.com/api/v1/client/attacks/2001"

# Response includes attack configuration
{
    "id": 2001,
    "attack_mode": "dictionary",
    "hash_type": 1000,
    "wordlist_url": "https://storage.example.com/wordlists/rockyou.txt?signature=...",
    "rules_url": "https://storage.example.com/rules/best64.rule?signature=...",
    "mask_list": null,
    "charset": null
}

# Download hash list
curl -H "Authorization: Bearer $AGENT_TOKEN" \
    "https://api.example.com/api/v1/client/attacks/2001/hashlist" \
    -o target_hashes.txt

# Download wordlist and rules using presigned URLs
curl "https://storage.example.com/wordlists/rockyou.txt?signature=..." \
    -o rockyou.txt

curl "https://storage.example.com/rules/best64.rule?signature=..." \
    -o best64.rule
```

#### Step 6: Execute Task with Progress Updates

```bash
# Start hashcat process and send progress updates
# (This would be done programmatically by the agent)

# Progress update at 10%
curl -X POST \
    -H "Authorization: Bearer $AGENT_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "status": "running",
        "progress": 10.5,
        "estimated_completion": "2024-01-01T14:30:00Z",
        "hash_speed": 8500000.0
    }' \
    "https://api.example.com/api/v1/client/tasks/1001/submit_status"

# Progress update at 25%
curl -X POST \
    -H "Authorization: Bearer $AGENT_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "status": "running",
        "progress": 25.0,
        "estimated_completion": "2024-01-01T14:15:00Z",
        "hash_speed": 8750000.0
    }' \
    "https://api.example.com/api/v1/client/tasks/1001/submit_status"
```

#### Step 7: Submit Crack Results

```bash
# Submit cracked hashes as they are found
curl -X POST \
    -H "Authorization: Bearer $AGENT_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "hash": "8846f7eaee8fb117ad06bdd830b7586c",
        "plain_text": "password123"
    }' \
    "https://api.example.com/api/v1/client/tasks/1001/submit_crack"

curl -X POST \
    -H "Authorization: Bearer $AGENT_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "hash": "e19ccf75ee54e06b06a5907af13cef42",
        "plain_text": "admin2024"
    }' \
    "https://api.example.com/api/v1/client/tasks/1001/submit_crack"
```

#### Step 8: Task Completion

```bash
# Final progress update
curl -X POST \
    -H "Authorization: Bearer $AGENT_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "status": "completed",
        "progress": 100.0,
        "hash_speed": 8600000.0
    }' \
    "https://api.example.com/api/v1/client/tasks/1001/submit_status"

# Mark task as exhausted (completed)
curl -X POST \
    -H "Authorization: Bearer $AGENT_TOKEN" \
    "https://api.example.com/api/v1/client/tasks/1001/exhausted"

# Update heartbeat to idle status
curl -X POST \
    -H "Authorization: Bearer $AGENT_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "status": "idle",
        "current_task_id": null,
        "devices_status": {
            "GPU0": "ready",
            "GPU1": "ready"
        }
    }' \
    "https://api.example.com/api/v1/client/agents/789/heartbeat"
```

#### Step 9: Error Handling Example

```bash
# Report error if something goes wrong
curl -X POST \
    -H "Authorization: Bearer $AGENT_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "message": "GPU temperature exceeded 85°C, reducing performance",
        "severity": "warning",
        "attack_id": 2001
    }' \
    "https://api.example.com/api/v1/client/agents/789/submit_error"

# Abandon task if critical error occurs
curl -X POST \
    -H "Authorization: Bearer $AGENT_TOKEN" \
    "https://api.example.com/api/v1/client/tasks/1001/abandon_task"

# Report critical error
curl -X POST \
    -H "Authorization: Bearer $AGENT_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "message": "GPU driver crashed, agent shutting down",
        "severity": "error",
        "attack_id": 2001
    }' \
    "https://api.example.com/api/v1/client/agents/789/submit_error"
```

#### Step 10: Graceful Shutdown

```bash
# Notify server of shutdown
curl -X POST \
    -H "Authorization: Bearer $AGENT_TOKEN" \
    "https://api.example.com/api/v1/client/agents/789/shutdown"
```

## Hash Analysis and Type Detection

### Hash Type Detection Workflow

This workflow demonstrates using the hash analysis capabilities across different APIs.

#### Using Control API for Hash Analysis

```bash
# Analyze single hash
curl -X POST \
    -H "Authorization: Bearer $CIPHERSWARM_API_KEY" \
    -H "Content-Type: application/json" \
    -d '{
        "hash_input": "5d41402abc4b2a76b9719d911017c592"
    }' \
    "https://api.example.com/api/v1/control/hash/guess"

# Response with hash type candidates
{
    "candidates": [
        {
            "hash_type": "MD5",
            "name": "MD5",
            "confidence": 95.5,
            "hashcat_mode": 0,
            "description": "32-character hexadecimal string"
        },
        {
            "hash_type": "NTLM",
            "name": "NTLM",
            "confidence": 15.2,
            "hashcat_mode": 1000,
            "description": "32-character hexadecimal string (less likely)"
        }
    ],
    "input_format": "single_hash",
    "analysis_time": 0.045
}
```

#### Using Web UI API for Hash Analysis

```bash
# Analyze multiple hash formats
curl -X POST \
    -H "Content-Type: application/json" \
    -d '{
        "hash_input": "user1:1000:aad3b435b51404eeaad3b435b51404ee:8846f7eaee8fb117ad06bdd830b7586c:::\nuser2:1001:aad3b435b51404eeaad3b435b51404ee:e19ccf75ee54e06b06a5907af13cef42:::\n$2b$12$GhvMmNVjRW29ulnudl.LbuAnUtN/LRfe1JsBm1Xu6LE3059z5Tr8m"
    }' \
    -b cookies.txt \
    "https://api.example.com/api/v1/web/hash/guess"

# Response with detailed analysis
{
    "candidates": [
        {
            "hash_type": "NTLM",
            "name": "NTLM",
            "confidence": 98.7,
            "hashcat_mode": 1000,
            "description": "Windows NTLM hash format",
            "sample_count": 2,
            "format_detected": "pwdump"
        },
        {
            "hash_type": "bcrypt",
            "name": "bcrypt $2*$, Blowfish (Unix)",
            "confidence": 99.1,
            "hashcat_mode": 3200,
            "description": "bcrypt hash with cost factor 12",
            "sample_count": 1,
            "format_detected": "single_hash"
        }
    ],
    "input_format": "mixed",
    "total_hashes": 3,
    "analysis_time": 0.123
}
```

#### Batch Hash Analysis

```bash
# Analyze large hash file
curl -X POST \
    -F "file=@unknown_hashes.txt" \
    -b cookies.txt \
    "https://api.example.com/api/v1/web/uploads/"

# Check analysis status
curl -b cookies.txt \
    "https://api.example.com/api/v1/web/uploads/567/status"

# Response with analysis results
{
    "upload_id": 567,
    "status": "completed",
    "analysis_results": {
        "total_lines": 15000,
        "valid_hashes": 14850,
        "invalid_lines": 150,
        "detected_types": [
            {
                "hash_type": "MD5",
                "count": 8500,
                "confidence": 96.2,
                "hashcat_mode": 0
            },
            {
                "hash_type": "SHA1",
                "count": 4200,
                "confidence": 94.8,
                "hashcat_mode": 100
            },
            {
                "hash_type": "NTLM",
                "count": 2150,
                "confidence": 98.1,
                "hashcat_mode": 1000
            }
        ]
    },
    "processing_time": 12.456
}
```

## Resource Management

### Resource Upload and Management Workflow

This workflow demonstrates managing attack resources (wordlists, rules, masks).

#### Step 1: Upload Wordlist

```bash
# Upload wordlist file
curl -X POST \
    -F "file=@custom_wordlist.txt" \
    -F "resource_type=wordlist" \
    -F "name=Custom Corporate Wordlist" \
    -F "description=Company-specific terms and patterns" \
    -b cookies.txt \
    "https://api.example.com/api/v1/web/resources/"

# Response includes resource details
{
    "id": 101,
    "name": "Custom Corporate Wordlist",
    "resource_type": "wordlist",
    "file_size": 2048576,
    "line_count": 125000,
    "checksum": "sha256:abc123...",
    "upload_url": "https://storage.example.com/upload/...",
    "status": "processing"
}
```

#### Step 2: Monitor Upload Progress

```bash
# Check upload status
curl -b cookies.txt \
    "https://api.example.com/api/v1/web/resources/101"

# Response when processing complete
{
    "id": 101,
    "name": "Custom Corporate Wordlist",
    "resource_type": "wordlist",
    "file_size": 2048576,
    "line_count": 125000,
    "checksum": "sha256:abc123...",
    "status": "ready",
    "created_at": "2024-01-01T14:00:00Z",
    "metadata": {
        "encoding": "utf-8",
        "unique_lines": 124850,
        "duplicate_lines": 150
    }
}
```

#### Step 3: Line-Level Resource Editing

```bash
# Get resource lines for editing
curl -b cookies.txt \
    "https://api.example.com/api/v1/web/resources/101/lines?page=1&size=100"

# Add new line to resource
curl -X POST \
    -H "Content-Type: application/json" \
    -d '{
        "content": "newpassword2024",
        "position": 1
    }' \
    -b cookies.txt \
    "https://api.example.com/api/v1/web/resources/101/lines"

# Update existing line
curl -X PATCH \
    -H "Content-Type: application/json" \
    -d '{
        "content": "updatedpassword2024"
    }' \
    -b cookies.txt \
    "https://api.example.com/api/v1/web/resources/101/lines/12345"

# Delete line
curl -X DELETE \
    -b cookies.txt \
    "https://api.example.com/api/v1/web/resources/101/lines/12346"
```

#### Step 4: Create Rule File

```bash
# Upload hashcat rules file
curl -X POST \
    -F "file=@custom_rules.rule" \
    -F "resource_type=rules" \
    -F "name=Custom Transformation Rules" \
    -F "description=Company-specific password transformation rules" \
    -b cookies.txt \
    "https://api.example.com/api/v1/web/resources/"

# Or create rules inline
curl -X POST \
    -H "Content-Type: application/json" \
    -d '{
        "name": "Simple Rules",
        "resource_type": "rules",
        "content": [
            ":",
            "l",
            "u",
            "c",
            "$1",
            "$2",
            "$3",
            "$!",
            "$@"
        ]
    }' \
    -b cookies.txt \
    "https://api.example.com/api/v1/web/resources/"
```

#### Step 5: Create Mask List

```bash
# Create mask patterns
curl -X POST \
    -H "Content-Type: application/json" \
    -d '{
        "name": "Corporate Mask Patterns",
        "resource_type": "masks",
        "description": "Common corporate password patterns",
        "content": [
            "?u?l?l?l?l?l?d?d",
            "?u?l?l?l?l?d?d?d?d",
            "?l?l?l?l?l?l?d?d",
            "?l?l?l?l?l?l?l?l?d?d",
            "?d?d?d?d?d?d?d?d",
            "?u?l?l?l?l?l?l?l?s",
            "?u?l?l?l?l?l?l?d?d?s"
        ]
    }' \
    -b cookies.txt \
    "https://api.example.com/api/v1/web/resources/"
```

#### Step 6: Resource Validation and Preview

```bash
# Get resource preview
curl -b cookies.txt \
    "https://api.example.com/api/v1/web/resources/101/preview"

# Response with sample content
{
    "resource_id": 101,
    "preview_lines": [
        "password123",
        "admin2024",
        "corporate123",
        "company2024",
        "secure123"
    ],
    "total_lines": 125000,
    "encoding": "utf-8",
    "file_size": 2048576
}

# Validate resource content
curl -X POST \
    -b cookies.txt \
    "https://api.example.com/api/v1/web/resources/101/refresh_metadata"
```

## Real-time Monitoring

### SSE-Based Real-time Monitoring

This workflow demonstrates setting up real-time monitoring using Server-Sent Events.

#### JavaScript/Browser Implementation

```javascript
class CipherSwarmMonitor {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
        this.eventSources = new Map();
        this.listeners = new Map();
    }

    // Connect to campaign updates
    monitorCampaigns(campaignIds = []) {
        const eventSource = new EventSource(
            `${this.baseUrl}/api/v1/web/live/campaigns`, {
                withCredentials: true
            }
        );

        eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);

            // Filter events if specific campaigns requested
            if (campaignIds.length > 0 && !campaignIds.includes(data.id)) {
                return;
            }

            this.handleCampaignEvent(data);
        };

        eventSource.onerror = (error) => {
            console.error("Campaign SSE error:", error);
            // Implement reconnection logic
            setTimeout(() => this.monitorCampaigns(campaignIds), 5000);
        };

        this.eventSources.set("campaigns", eventSource);
    }

    // Connect to agent updates
    monitorAgents() {
        const eventSource = new EventSource(
            `${this.baseUrl}/api/v1/web/live/agents`, {
                withCredentials: true
            }
        );

        eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleAgentEvent(data);
        };

        this.eventSources.set("agents", eventSource);
    }

    // Connect to toast notifications
    monitorToasts() {
        const eventSource = new EventSource(
            `${this.baseUrl}/api/v1/web/live/toasts`, {
                withCredentials: true
            }
        );

        eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleToastEvent(data);
        };

        this.eventSources.set("toasts", eventSource);
    }

    handleCampaignEvent(event) {
        console.log("Campaign event:", event);

        switch (event.trigger) {
            case "refresh":
                if (event.target === "campaign") {
                    this.refreshCampaignData(event.id);
                } else if (event.target === "attack") {
                    this.refreshAttackData(event.id);
                } else if (event.target === "task") {
                    this.refreshTaskData(event.id);
                }
                break;

            case "state_change":
                this.handleStateChange(event);
                break;
        }
    }

    handleAgentEvent(event) {
        console.log("Agent event:", event);

        switch (event.trigger) {
            case "status_update":
                this.updateAgentStatus(event.id, event.data);
                break;

            case "performance_update":
                this.updateAgentPerformance(event.id, event.data);
                break;

            case "error_reported":
                this.showAgentError(event.id, event.data);
                break;
        }
    }

    handleToastEvent(event) {
        console.log("Toast event:", event);

        switch (event.type) {
            case "crack_result":
                this.showCrackNotification(event.data);
                break;

            case "campaign_complete":
                this.showCampaignCompleteNotification(event.data);
                break;

            case "system_alert":
                this.showSystemAlert(event.data);
                break;
        }
    }

    async refreshCampaignData(campaignId) {
        try {
            const response = await fetch(
                `${this.baseUrl}/api/v1/web/campaigns/${campaignId}/progress`, {
                    credentials: "include"
                }
            );
            const data = await response.json();

            // Update UI with new campaign data
            this.updateCampaignUI(campaignId, data);
        } catch (error) {
            console.error("Failed to refresh campaign data:", error);
        }
    }

    showCrackNotification(data) {
        // Show toast notification for new crack
        const notification = {
            type: "success",
            title: "Hash Cracked!",
            message: `Found password for hash ${data.hash.substring(0, 8)}...`,
            duration: 5000,
        };

        this.showToast(notification);
    }

    disconnect() {
        this.eventSources.forEach((eventSource) => eventSource.close());
        this.eventSources.clear();
    }
}

// Usage example
const monitor = new CipherSwarmMonitor("https://api.example.com");

// Start monitoring specific campaigns
monitor.monitorCampaigns([456, 457, 458]);

// Monitor all agents
monitor.monitorAgents();

// Monitor toast notifications
monitor.monitorToasts();

// Cleanup on page unload
window.addEventListener("beforeunload", () => {
    monitor.disconnect();
});
```

#### Python Implementation for CLI Monitoring

```python
import requests
import json
import time
from typing import Dict, List, Optional, Callable


class CipherSwarmCLIMonitor:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        self.running = False

    def monitor_campaigns(
        self,
        campaign_ids: List[int],
        interval: int = 5,
        callback: Optional[Callable] = None,
    ):
        """Monitor campaign progress with polling."""
        self.running = True

        print(f"Monitoring campaigns: {campaign_ids}")
        print("Press Ctrl+C to stop monitoring\n")

        try:
            while self.running:
                for campaign_id in campaign_ids:
                    try:
                        # Get campaign status
                        response = requests.get(
                            f"{self.base_url}/api/v1/control/campaigns/{campaign_id}/status",
                            headers=self.headers,
                        )

                        if response.ok:
                            data = response.json()
                            self.display_campaign_status(campaign_id, data)

                            if callback:
                                callback(campaign_id, data)
                        else:
                            print(
                                f"Error getting status for campaign {campaign_id}: {response.status_code}"
                            )

                    except Exception as e:
                        print(f"Error monitoring campaign {campaign_id}: {e}")

                print("-" * 80)
                time.sleep(interval)

        except KeyboardInterrupt:
            print("\nMonitoring stopped.")
            self.running = False

    def display_campaign_status(self, campaign_id: int, data: Dict):
        """Display campaign status in CLI format."""
        print(f"Campaign {campaign_id}: {data.get('name', 'Unknown')}")
        print(f"  State: {data.get('state', 'unknown')}")
        print(f"  Progress: {data.get('progress', 0):.1f}%")
        print(f"  Tasks: {data.get('completed_tasks', 0)}/{data.get('total_tasks', 0)}")
        print(
            f"  Cracked: {data.get('cracked_hashes', 0)}/{data.get('total_hashes', 0)}"
        )

        if data.get("current_hash_rate"):
            print(f"  Hash Rate: {data['current_hash_rate']:,} H/s")

        if data.get("estimated_completion"):
            print(f"  ETA: {data['estimated_completion']}")

        print()

    def monitor_agents(self, interval: int = 10):
        """Monitor agent status."""
        self.running = True

        print("Monitoring agent status")
        print("Press Ctrl+C to stop monitoring\n")

        try:
            while self.running:
                try:
                    # Get agent summary
                    response = requests.get(
                        f"{self.base_url}/api/v1/control/agents/summary",
                        headers=self.headers,
                    )

                    if response.ok:
                        data = response.json()
                        self.display_agent_summary(data)
                    else:
                        print(f"Error getting agent summary: {response.status_code}")

                except Exception as e:
                    print(f"Error monitoring agents: {e}")

                print("-" * 80)
                time.sleep(interval)

        except KeyboardInterrupt:
            print("\nAgent monitoring stopped.")
            self.running = False

    def display_agent_summary(self, data: Dict):
        """Display agent summary in CLI format."""
        print(f"Agent Summary ({data.get('timestamp', 'unknown')})")
        print(f"  Total Agents: {data.get('total_agents', 0)}")
        print(f"  Active Agents: {data.get('active_agents', 0)}")
        print(f"  Idle Agents: {data.get('idle_agents', 0)}")
        print(f"  Offline Agents: {data.get('offline_agents', 0)}")
        print(f"  Total Hash Rate: {data.get('total_hash_rate', 0):,} H/s")

        if data.get("agents"):
            print("\nAgent Details:")
            for agent in data["agents"][:10]:  # Show top 10 agents
                print(
                    f"  {agent['id']}: {agent['hostname']} - {agent['status']} - {agent.get('hash_rate', 0):,} H/s"
                )

        print()


# Usage example
if __name__ == "__main__":
    import sys

    monitor = CipherSwarmCLIMonitor(
        base_url="https://api.example.com", api_key="cst_123_abc123def456..."
    )

    if len(sys.argv) > 1 and sys.argv[1] == "agents":
        monitor.monitor_agents()
    else:
        # Monitor specific campaigns
        campaign_ids = [456, 457, 458]
        monitor.monitor_campaigns(campaign_ids)
```

## Batch Operations

### Bulk Campaign Management

This workflow demonstrates managing multiple campaigns simultaneously using the Control API.

#### Step 1: Bulk Campaign Creation

```bash
# Create multiple campaigns from template
for i in {1..5}; do
    curl -X POST \
        -H "Authorization: Bearer $CIPHERSWARM_API_KEY" \
        -H "Content-Type: application/json" \
        -d "{
            \"name\": \"Batch Campaign $i\",
            \"description\": \"Automated campaign creation batch $i\",
            \"project_id\": 1,
            \"hash_list_id\": $((100 + i)),
            \"priority\": $((i * 10))
        }" \
        "https://api.example.com/api/v1/control/campaigns/"
done
```

#### Step 2: Bulk Campaign Start

```bash
# Start multiple campaigns simultaneously
curl -X POST \
    -H "Authorization: Bearer $CIPHERSWARM_API_KEY" \
    -H "Content-Type: application/json" \
    -d '{
        "campaign_ids": [501, 502, 503, 504, 505]
    }' \
    "https://api.example.com/api/v1/control/campaigns/bulk_start"

# Response includes operation results
{
    "successful_count": 4,
    "failed_count": 1,
    "results": [
        {"campaign_id": 501, "status": "started"},
        {"campaign_id": 502, "status": "started"},
        {"campaign_id": 503, "status": "started"},
        {"campaign_id": 504, "status": "started"},
        {"campaign_id": 505, "status": "failed", "error": "Campaign already running"}
    ]
}
```

#### Step 3: Bulk Status Monitoring

```bash
# Get status of multiple campaigns
curl -H "Authorization: Bearer $CIPHERSWARM_API_KEY" \
    "https://api.example.com/api/v1/control/campaigns/bulk_status?campaign_ids=501,502,503,504"

# Response with all campaign statuses
{
    "campaigns": [
        {
            "id": 501,
            "name": "Batch Campaign 1",
            "state": "active",
            "progress": 15.5,
            "completed_tasks": 3,
            "total_tasks": 20,
            "cracked_hashes": 125,
            "total_hashes": 10000
        },
        {
            "id": 502,
            "name": "Batch Campaign 2",
            "state": "active",
            "progress": 8.2,
            "completed_tasks": 1,
            "total_tasks": 15,
            "cracked_hashes": 67,
            "total_hashes": 8500
        }
    ],
    "timestamp": "2024-01-01T15:30:00Z"
}
```

#### Step 4: Conditional Bulk Operations

```bash
# Stop campaigns that have low progress after 1 hour
curl -X POST \
    -H "Authorization: Bearer $CIPHERSWARM_API_KEY" \
    -H "Content-Type: application/json" \
    -d '{
        "campaign_ids": [501, 502, 503, 504],
        "conditions": {
            "min_runtime_minutes": 60,
            "max_progress_percent": 5.0
        }
    }' \
    "https://api.example.com/api/v1/control/campaigns/bulk_stop_conditional"

# Restart campaigns with specific criteria
curl -X POST \
    -H "Authorization: Bearer $CIPHERSWARM_API_KEY" \
    -H "Content-Type: application/json" \
    -d '{
        "campaign_ids": [501, 502, 503, 504],
        "conditions": {
            "states": ["failed", "paused"],
            "last_activity_hours": 2
        }
    }' \
    "https://api.example.com/api/v1/control/campaigns/bulk_restart_conditional"
```

## Error Recovery Scenarios

### Campaign Recovery Workflow

This workflow demonstrates handling and recovering from various error scenarios.

#### Scenario 1: Agent Disconnection Recovery

```bash
# Detect disconnected agents
curl -H "Authorization: Bearer $CIPHERSWARM_API_KEY" \
    "https://api.example.com/api/v1/control/agents/summary"

# Response shows offline agents
{
    "total_agents": 10,
    "active_agents": 7,
    "offline_agents": 3,
    "offline_agent_ids": [789, 790, 791],
    "affected_campaigns": [456, 457]
}

# Reassign tasks from offline agents
curl -X POST \
    -H "Authorization: Bearer $CIPHERSWARM_API_KEY" \
    -H "Content-Type: application/json" \
    -d '{
        "offline_agent_ids": [789, 790, 791],
        "reassign_tasks": true,
        "notify_campaigns": true
    }' \
    "https://api.example.com/api/v1/control/agents/handle_offline"

# Monitor campaign recovery
curl -H "Authorization: Bearer $CIPHERSWARM_API_KEY" \
    "https://api.example.com/api/v1/control/campaigns/456/status"
```

#### Scenario 2: Campaign Failure Recovery

```bash
# Detect failed campaigns
curl -H "Authorization: Bearer $CIPHERSWARM_API_KEY" \
    "https://api.example.com/api/v1/control/campaigns/?state=failed"

# Get failure details
curl -H "Authorization: Bearer $CIPHERSWARM_API_KEY" \
    "https://api.example.com/api/v1/control/campaigns/456/errors"

# Response with error details
{
    "campaign_id": 456,
    "errors": [
        {
            "timestamp": "2024-01-01T14:30:00Z",
            "severity": "error",
            "message": "All agents disconnected during execution",
            "error_code": "AGENT_DISCONNECTION",
            "affected_tasks": [1001, 1002, 1003]
        }
    ],
    "recovery_suggestions": [
        "Restart campaign with available agents",
        "Check agent connectivity",
        "Verify network configuration"
    ]
}

# Reset and restart campaign
curl -X POST \
    -H "Authorization: Bearer $CIPHERSWARM_API_KEY" \
    "https://api.example.com/api/v1/control/campaigns/456/reset"

curl -X POST \
    -H "Authorization: Bearer $CIPHERSWARM_API_KEY" \
    "https://api.example.com/api/v1/control/campaigns/456/start"
```

#### Scenario 3: Resource Corruption Recovery

```bash
# Detect corrupted resources
curl -b cookies.txt \
    "https://api.example.com/api/v1/web/resources/101"

# Response indicates corruption
{
    "id": 101,
    "name": "Custom Corporate Wordlist",
    "status": "corrupted",
    "error": "Checksum mismatch detected",
    "checksum_expected": "sha256:abc123...",
    "checksum_actual": "sha256:def456..."
}

# Re-upload resource
curl -X POST \
    -F "file=@custom_wordlist.txt" \
    -F "replace_resource_id=101" \
    -b cookies.txt \
    "https://api.example.com/api/v1/web/resources/"

# Update campaigns using the resource
curl -X POST \
    -H "Content-Type: application/json" \
    -d '{
        "resource_id": 101,
        "update_campaigns": true,
        "restart_affected": false
    }' \
    -b cookies.txt \
    "https://api.example.com/api/v1/web/resources/101/refresh_metadata"
```

#### Scenario 4: Database Consistency Recovery

```bash
# Check system health
curl -H "Authorization: Bearer $CIPHERSWARM_API_KEY" \
    "https://api.example.com/api/v1/control/system/health"

# Response shows database issues
{
    "overall_status": "degraded",
    "components": {
        "database": {
            "status": "warning",
            "message": "Detected orphaned tasks",
            "details": {
                "orphaned_tasks": 15,
                "stale_sessions": 3,
                "inconsistent_progress": 2
            }
        }
    }
}

# Run consistency check and repair
curl -X POST \
    -H "Authorization: Bearer $CIPHERSWARM_API_KEY" \
    "https://api.example.com/api/v1/control/system/repair"

# Response with repair results
{
    "repair_actions": [
        "Cleaned up 15 orphaned tasks",
        "Removed 3 stale agent sessions",
        "Recalculated progress for 2 campaigns"
    ],
    "affected_campaigns": [456, 457],
    "recommended_actions": [
        "Restart affected campaigns",
        "Verify agent connectivity"
    ]
}
```

These workflow examples demonstrate the comprehensive capabilities of the Ouroboros API across all three interfaces, showing real-world usage patterns and error handling scenarios that developers and administrators will encounter when integrating with the system.
