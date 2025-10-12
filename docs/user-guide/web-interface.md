# Web Interface Guide

The Ouroboros v2 web interface provides a modern, responsive dashboard for managing your password cracking operations with real-time updates and project-based organization.

---

## Table of Contents

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=2 --minlevel=1 -->

- [Web Interface Guide](#web-interface-guide)
  - [Table of Contents](#table-of-contents)
  - [Authentication & Project Context](#authentication--project-context)
  - [Dashboard Overview](#dashboard-overview)
  - [Campaign Management](#campaign-management)
  - [Attack Management](#attack-management)
  - [Hash List Management](#hash-list-management)
  - [Resource Management](#resource-management)
  - [Agent Management](#agent-management)
  - [Live Updates & Real-time Features](#live-updates--real-time-features)
  - [Settings & Administration](#settings--administration)
  - [Keyboard Shortcuts](#keyboard-shortcuts)
  - [Dark Mode & Theming](#dark-mode--theming)
  - [Troubleshooting](#troubleshooting)

<!-- mdformat-toc end -->

---

## Authentication & Project Context

### Login Process

1. Navigate to the Ouroboros web interface
2. Enter your email and password
3. Click "Sign In"
4. If you have access to multiple projects, select your active project from the project selector

### Project Context

Ouroboros v2 introduces project-based organization:

- **Project Selector**: Located in the header, allows switching between projects you have access to
- **Project Scoping**: All campaigns, hash lists, and resources are scoped to the selected project
- **Multi-tenancy**: Data is isolated between projects for security

```html
<div class="project-selector">
 <select class="form-select">
  <option value="project1">
   Project Alpha
  </option>
  <option value="project2">
   Project Beta
  </option>
 </select>
</div>
```

## Dashboard Overview

The main dashboard provides real-time operational awareness with live updates via Server-Sent Events (SSE).

### Status Cards

The top of the dashboard displays four key metrics:

1. **Active Agents**

   - Shows online agents vs total registered
   - Click to open Agent Status Sheet
   - Real-time updates via SSE

2. **Running Tasks**

   - Active campaigns and task breakdown
   - Percentage of running vs completed tasks
   - Links to campaign details

3. **Recently Cracked Hashes**

   - Hashes cracked in the last 24 hours
   - Scoped to accessible projects
   - Links to results view

4. **Resource Usage**

   - Aggregate hash rate across all agents
   - Sparkline chart showing 8-hour trend
   - Real-time performance metrics

### Campaign Overview

The main content area shows all campaigns with:

- **Accordion Layout**: Expandable campaign rows
- **Live Progress**: Real-time progress bars with SSE updates
- **State Indicators**: Color-coded badges (Running=purple, Completed=green, Error=red, Paused=gray)
- **Attack Details**: Expandable view showing individual attacks

```html
<div class="campaign-row">
 <div class="campaign-header">
  <h3>
   Campaign Name
  </h3>
  <div class="progress-bar">
   <div class="progress-fill" style="width: 45%">
   </div>
  </div>
  <span class="badge badge-running">
   ⚡ 3 attacks / 1 running / ETA 3h
  </span>
 </div>
</div>
```

### Live Toast Notifications

Real-time notifications appear when hashes are cracked:

- **Individual Toasts**: For single hash cracks
- **Batch Toasts**: For multiple cracks (e.g., "5 new hashes cracked")
- **Rate Limiting**: Prevents notification spam
- **Contextual Info**: Shows plaintext, attack used, timestamp

## Campaign Management

### Creating a Campaign

1. Navigate to "Campaigns" → "New Campaign"

2. Fill in campaign details:

   ```yaml
   Name: Descriptive campaign name
   Description: Optional description
   Hash List: Select existing or create new
   Project: Automatically set to current context
   ```

3. Configure initial attacks (optional)

4. Click "Create Campaign"

### Campaign States

Campaigns have the following states:

- **Draft**: Newly created, not yet started
- **Active**: Running with active attacks
- **Paused**: Temporarily stopped
- **Completed**: All attacks finished
- **Archived**: Completed and archived

### Campaign Actions

- **Start/Stop**: Toggle campaign execution
- **Add Attack**: Configure new attacks within the campaign
- **Reorder Attacks**: Drag-and-drop or use move buttons
- **Export/Import**: Save campaign configuration as JSON
- **Archive**: Mark campaign as completed

## Attack Management

### Attack Types

Ouroboros v2 supports multiple attack types with enhanced configuration:

#### Dictionary Attacks

Modern dictionary attack editor with:

- **Wordlist Selection**: Searchable dropdown with entry counts
- **Length Constraints**: Min/max password length
- **Modifiers**: User-friendly rule presets
  - Change Case (uppercase, lowercase, capitalize, toggle)
  - Change Order (duplicate, reverse)
  - Substitute Characters (leetspeak, combinator)
- **Previous Passwords**: Dynamic wordlist from project's cracked passwords
- **Ephemeral Wordlists**: Add custom words directly in the editor

```html
<div class="attack-editor">
 <select class="wordlist-selector">
  <option value="rockyou">
   rockyou.txt (14,344,391 words)
  </option>
  <option value="common">
   common-passwords.txt (10,000 words)
  </option>
 </select>
 <div class="modifiers">
  <button class="modifier-btn">
   + Change Case
  </button>
  <button class="modifier-btn">
   + Substitute Characters
  </button>
 </div>
 <div class="ephemeral-wordlist">
  <input placeholder="Add custom word" type="text"/>
  <button>
   +
  </button>
 </div>
</div>
```

#### Mask Attacks

Enhanced mask attack configuration:

- **Inline Mask Editor**: Add/remove mask patterns directly
- **Real-time Validation**: Syntax checking as you type
- **Ephemeral Masks**: Store masks with the attack
- **Custom Charsets**: Define character sets for mask tokens

#### Brute Force Attacks

Simplified brute force interface:

- **Charset Selection**: Checkboxes for character types
  - Lowercase `(a-z)`
  - Uppercase `(A-Z)`
  - Numbers `(0-9)`
  - Symbols `(!@#$...)`
  - Space `( )`
- **Length Range**: Min/max length slider
- **Auto-generation**: Automatically creates appropriate masks

### Attack Features

#### Real-time Estimation

- **Keyspace Calculation**: Live updates as you configure
- **Complexity Score**: 1-5 scale based on estimated difficulty
- **Time Estimates**: Projected completion time

#### Attack Lifecycle

- **Edit Protection**: Warnings when editing running/completed attacks
- **State Reset**: Editing resets attack to pending state
- **Progress Tracking**: Real-time progress updates via SSE

## Hash List Management

### Creating Hash Lists

1. **Manual Creation**: Create empty hash list and add hashes
2. **File Upload**: Upload hash files in various formats
3. **Crackable Upload**: Automated hash extraction and campaign creation

### Hash List Features

- **Project Scoping**: Hash lists are strictly project-scoped
- **Search & Filter**: Find hashes by value, plaintext, or status
- **Export Options**: TSV and CSV export formats
- **Status Tracking**: Cracked vs uncracked hash counts

### Crackable Uploads

New streamlined workflow for non-technical users:

#### Supported Formats

- **File Uploads**: .zip, .pdf, .docx, .kdbx files
- **Text Input**: Paste hashes from various sources
- **Shadow Files**: Linux /etc/shadow format
- **NTLM Dumps**: Windows hash dumps

#### Upload Process

1. **Upload/Paste**: Drag files or paste hash text
2. **Auto-detection**: System detects hash types automatically
3. **Preview**: Review detected hashes and types
4. **Confirmation**: Approve campaign creation
5. **Processing**: Background processing with status updates

```html
<div class="upload-area">
 <div class="drop-zone">
  <p>
   Drag files here or click to browse
  </p>
  <input accept=".zip,.pdf,.txt" type="file"/>
 </div>
 <div class="text-input">
  <textarea placeholder="Or paste hashes here..."></textarea>
 </div>
</div>
```

#### Processing Status

- **Real-time Updates**: Live status via SSE
- **Error Reporting**: Line-by-line error details
- **Preview Results**: Sample of detected hashes
- **Auto-campaign**: Automatic campaign and attack creation

## Resource Management

### Resource Types

Ouroboros manages several resource types:

- **Wordlists**: Dictionary files for attacks
- **Rule Lists**: Hashcat rule files
- **Mask Lists**: Collections of mask patterns
- **Charsets**: Custom character set definitions

### Resource Features

#### Upload & Management

- **Presigned URLs**: Secure direct-to-storage uploads
- **Metadata Tracking**: Size, line count, usage statistics
- **Project Linking**: Resources can be project-specific or global

#### Line-Level Editing

For smaller resources (under configured size limits):

- **Inline Editor**: Edit resources directly in browser
- **Line Validation**: Real-time syntax checking
- **Add/Remove Lines**: Interactive line management
- **Batch Operations**: Multiple line edits

```html
<div class="resource-editor">
 <div class="line-editor">
  <input type="text" value="?d?d?d?d"/>
  <button class="delete-line">
   ×
  </button>
 </div>
 <button class="add-line">
  + Add Line
 </button>
</div>
```

## Agent Management

### Agent Overview

The Agent Status Sheet (accessible from dashboard) shows:

- **Agent Cards**: Individual agent status
- **Performance Metrics**: Current hash rates and trends
- **Task Assignment**: Current campaign/attack assignments
- **Hardware Status**: Temperature and utilization

### Agent Registration

Administrators can register new agents:

1. Click "Register Agent" in agent management
2. Enter agent label and description
3. Select project assignments
4. Copy the generated token (shown only once)
5. Configure agent with token

### Agent Configuration

#### Basic Settings

- **Display Name**: Custom label or hostname fallback
- **Enable/Disable**: Toggle agent availability
- **Update Interval**: Heartbeat frequency (1-15 seconds)
- **Project Assignment**: Multi-project access control

#### Hardware Management

- **Device Toggles**: Enable/disable individual GPUs/CPUs
- **Backend Selection**: CUDA, OpenCL, HIP, Metal
- **Temperature Limits**: Abort thresholds (default 90°C)
- **Performance Monitoring**: Real-time utilization tracking

#### Capabilities

- **Benchmark Results**: Hash type performance data
- **Device Information**: Hardware specifications
- **Performance History**: 8-hour performance trends

## Live Updates & Real-time Features

### Server-Sent Events (SSE)

Ouroboros v2 uses SSE for real-time updates:

- **Campaign Feed**: Attack progress and state changes
- **Agent Feed**: Agent status and performance updates
- **Toast Feed**: New crack results and notifications

### Connection Status

- **Live Indicator**: Shows SSE connection status
- **Fallback Polling**: Automatic fallback if SSE unavailable
- **Stale Data Warning**: Alerts when data is >30 seconds old

## Settings & Administration

### User Management (Admin Only)

- **User Creation**: Add new users with role assignment
- **Role Management**: Admin, User, Power User roles
- **Project Assignment**: Multi-project user access
- **Password Policies**: Complexity requirements and rotation

### System Health

#### Health Overview

- **Agent Status**: Online/offline counts
- **System Performance**: Database latency, task backlog
- **Error Monitoring**: Recent errors and warnings

#### Component Health

- **Database**: Connection status and performance
- **MinIO**: Object storage health and capacity
- **Redis**: Cache status (if configured)

### Performance Settings

```yaml
# Task Distribution:
max_tasks_per_agent: 5
adaptive_distribution: true

# Resource Management:
cache_wordlists: true
cleanup_interval: 3600

# Upload Limits:
max_file_size: 100MB
allowed_extensions: [.txt, .zip, .pdf]
```

## Keyboard Shortcuts

| Action           | Shortcut |
| ---------------- | -------- |
| New Campaign     | `Ctrl+N` |
| Refresh          | `F5`     |
| Search           | `Ctrl+/` |
| Toggle Dark Mode | `Ctrl+D` |
| Help             | `?`      |

## Dark Mode & Theming

Ouroboros v2 includes comprehensive dark mode support:

- **Auto-detection**: Respects system preferences
- **Manual Toggle**: Theme switcher in navigation
- **Persistent**: Remembers user preference
- **Catppuccin Theme**: Modern color palette with DarkViolet accents

```html
<button class="theme-toggle" onclick="toggleTheme()">
 <svg class="sun-icon hidden dark:block">
  ...
 </svg>
 <svg class="moon-icon block dark:hidden">
  ...
 </svg>
</button>
```

## Troubleshooting

### Common Issues

1. **SSE Connection Failed**

   - Check browser console for errors
   - Verify network connectivity
   - System falls back to polling automatically

2. **Project Context Issues**

   - Ensure you have access to the selected project
   - Try switching projects and back
   - Contact admin for project access

3. **Upload Processing Stuck**

   - Check upload status endpoint
   - Review error logs for failed lines
   - Verify file format compatibility

4. **Agent Not Appearing**

   - Verify agent token is correct
   - Check agent logs for connection errors
   - Ensure agent has project access

### Performance Tips

- **Use targeted wordlists** for faster attacks
- **Monitor agent temperatures** to prevent throttling
- **Batch similar attacks** in campaigns for efficiency
- **Regular cleanup** of completed campaigns and unused resources
