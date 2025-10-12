# Frequently Asked Questions (FAQ)

This FAQ covers common questions about Ouroboros v2.

---

## Table of Contents

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=2 --minlevel=1 -->

- [Frequently Asked Questions (FAQ)](#frequently-asked-questions-faq)
  - [Table of Contents](#table-of-contents)
  - [General Questions](#general-questions)
  - [Authentication and Access](#authentication-and-access)
  - [Agents and Hardware](#agents-and-hardware)
  - [Campaigns and Attacks](#campaigns-and-attacks)
  - [Resources and Storage](#resources-and-storage)
  - [Live Updates and Real-time Features](#live-updates-and-real-time-features)
  - [Hash Lists and Crackable Uploads](#hash-lists-and-crackable-uploads)
  - [Performance and Optimization](#performance-and-optimization)
  - [Security and Best Practices](#security-and-best-practices)
  - [Troubleshooting](#troubleshooting)
  - [Integration and API](#integration-and-api)
  - [Getting Help](#getting-help)

<!-- mdformat-toc end -->

---

## General Questions

### What's new in Ouroboros v2?

Ouroboros v2 introduces several major improvements:

- **Project-based Organization**: Multi-tenant architecture with project isolation
- **Enhanced Authentication**: JWT-based authentication with role-based access control
- **Modern Web Interface**: Complete UI redesign with real-time updates
- **Advanced Attack Types**: New brute force attacks and enhanced dictionary/mask attacks
- **Resource Management**: Line-level editing, ephemeral resources, and MinIO integration
- **Live Updates**: Server-Sent Events (SSE) for real-time dashboard updates
- **Hash List Management**: Improved hash management with crackable uploads
- **Agent Enhancements**: Better hardware management and performance monitoring

### Is Ouroboros v2 compatible with v1 agents?

Yes, Ouroboros v2 maintains backward compatibility with v1 agents through the Agent API v1. However, some new features (like enhanced hardware management) require agent updates.

### How do I migrate from Ouroboros v1?

Migration involves:

1. **Data Migration**: Existing campaigns, attacks, and resources are preserved
2. **User Accounts**: User accounts are migrated with appropriate project assignments
3. **Agent Re-registration**: Agents need new tokens and may require configuration updates
4. **Project Assignment**: Existing data is assigned to a default project

Contact your administrator for migration assistance.

## Authentication and Access

### How do I log into Ouroboros v2?

1. Navigate to the Ouroboros web interface
2. Enter your username and password
3. Select your active project (if assigned to multiple projects)
4. Access the dashboard and features

### What are the different user roles?

Ouroboros v2 has three user roles:

- **User**: Basic access, can view campaigns and results
- **Power User**: Can create and manage campaigns, attacks, and resources
- **Admin**: Full system access, user management, and system configuration

### How do projects work?

Projects provide multi-tenant organization:

- **Isolation**: Each project has separate campaigns, attacks, hash lists, and resources
- **Access Control**: Users are assigned to specific projects
- **Security**: No data sharing between projects without explicit export
- **Management**: Administrators control project membership and permissions

### Can I access multiple projects?

Yes, users can be assigned to multiple projects. Use the project selector in the header to switch between projects. Your current project context determines what data you can see and modify.

### I can't see any campaigns or resources. What's wrong?

This usually indicates a project access issue:

1. **Check Project Assignment**: Verify you're assigned to projects with data
2. **Contact Administrator**: Request access to appropriate projects
3. **Verify Project Context**: Ensure you've selected the correct project
4. **Check Role**: Verify you have appropriate permissions

## Agents and Hardware

### How do I register a new agent?

Agent registration is now done through the web interface:

1. **Administrator Access**: Only administrators can register agents
2. **Web Registration**: Use the "Register New Agent" button in the Agents section
3. **Project Assignment**: Select which projects the agent can access
4. **Token Generation**: Copy the generated token (shown only once)
5. **Agent Configuration**: Configure the agent with the token and restart

### Why isn't my agent appearing online?

Common causes:

1. **Authentication Issues**: Verify the agent token is correct and not expired
2. **Network Connectivity**: Ensure the agent can reach the server via HTTPS
3. **Project Assignment**: Verify the agent is assigned to at least one project
4. **Configuration Errors**: Check agent configuration and logs

### How do I manage agent hardware settings?

Ouroboros v2 provides enhanced hardware management:

1. **Device Toggles**: Enable/disable individual GPUs and CPUs
2. **Backend Selection**: Choose CUDA, OpenCL, HIP, or Metal backends
3. **Temperature Limits**: Set thermal abort thresholds
4. **Workload Settings**: Adjust GPU utilization levels (1-4)
5. **Performance Monitoring**: View real-time performance metrics

### Can agents work on multiple projects simultaneously?

Yes, agents can be assigned to multiple projects and will receive tasks from any assigned project. Task distribution is automatic based on agent capabilities and project priorities.

### How do I benchmark agent performance?

1. **Automatic Benchmarks**: Agents automatically benchmark on first connection
2. **Manual Triggers**: Use the "Trigger Benchmark" button in agent details
3. **Performance Monitoring**: View live performance charts and metrics
4. **Capabilities View**: See detailed hash type performance data

## Campaigns and Attacks

### What attack types are available?

Ouroboros v2 supports:

- **Dictionary Attacks**: Wordlist-based attacks with optional rules
- **Mask Attacks**: Pattern-based attacks using character masks
- **Brute Force Attacks**: Exhaustive attacks with configurable character sets
- **Hybrid Attacks**: Combinations of dictionary and mask attacks

### How do I create a campaign?

1. **Navigate to Campaigns**: Click "Campaigns" in the main navigation
2. **Create Campaign**: Click "New Campaign" button
3. **Configure Details**: Set name, description, and select hash list
4. **Add Attacks**: Configure one or more attacks for the campaign
5. **Review and Start**: Review configuration and start the campaign

### What are ephemeral resources?

Ephemeral resources are temporary resources created within attacks:

- **Lifecycle**: Created with attack, deleted when attack is removed
- **Usage**: Single-attack only, not reusable across campaigns
- **Types**: Custom wordlists, mask lists, and character sets
- **Storage**: Stored in database, not in external storage
- **Export**: Included inline when exporting attack configurations

### How do I use previous passwords in attacks?

Ouroboros v2 can automatically generate wordlists from previously cracked passwords:

1. **Dictionary Attack**: Select "Use Previous Passwords" option
2. **Automatic Generation**: System creates wordlist from project's cracked passwords
3. **Dynamic Updates**: Wordlist updates as new passwords are cracked
4. **Project Scope**: Only includes passwords from the current project

### Can I edit attacks while they're running?

Yes, but with restrictions:

- **Warning Prompt**: System warns about resetting attack progress
- **State Reset**: Editing resets attack to "pending" state
- **Confirmation Required**: Must confirm understanding of impact
- **Resource Updates**: Linked resource changes trigger automatic restarts

## Resources and Storage

### How do I upload resources?

1. **Navigate to Resources**: Click "Resources" in main navigation
2. **Upload Button**: Click "Upload Resource" or drag-and-drop files
3. **File Selection**: Choose file and resource type (auto-detected)
4. **Configuration**: Set name, description, and project scope
5. **Validation**: System validates format and content

### What file formats are supported?

- **Wordlists**: `.txt`, `.lst`, `.dict` (UTF-8 or ASCII)
- **Rule Lists**: `.rule`, `.rules` (ASCII, hashcat syntax)
- **Mask Lists**: `.mask`, `.masks` (ASCII, hashcat mask syntax)
- **Charsets**: `.charset`, `.hchr` (ASCII, custom charset definitions)

### Can I edit resources online?

Yes, for smaller resources:

- **Size Limits**: Resources under 5MB or 10,000 lines
- **Line Editing**: Add, edit, or remove individual lines
- **Real-time Validation**: Syntax checking for rules and masks
- **Larger Files**: Must download, edit offline, and reupload

### How does project scoping work for resources?

Resources can be:

- **Project-Specific**: Only accessible within assigned projects
- **Global**: Available to all projects (admin-created only)
- **Automatic Assignment**: Based on user's current project context

### What happens to resources when I delete an attack?

- **Ephemeral Resources**: Deleted automatically with the attack
- **Regular Resources**: Unlinked but preserved for reuse
- **Usage Tracking**: System tracks which resources are in use

## Live Updates and Real-time Features

### How do live updates work?

Ouroboros v2 uses Server-Sent Events (SSE) for real-time updates:

- **Automatic Updates**: Dashboard and campaign views update automatically
- **No Refresh Needed**: Changes appear without page reloads
- **Selective Updates**: Only relevant data is refreshed
- **Browser Support**: Works with modern browsers supporting EventSource

### Why aren't my live updates working?

Common issues:

1. **Browser Compatibility**: Ensure browser supports EventSource
2. **Network Issues**: Check for proxy/firewall blocking SSE connections
3. **Connection Drops**: Verify stable network connectivity
4. **JavaScript Errors**: Check browser console for errors

### Can I disable live updates?

Yes, live updates can be disabled:

- **Per-View Basis**: Toggle updates for specific views
- **Browser Setting**: Disable in browser preferences
- **Manual Refresh**: Use refresh buttons when updates are disabled

## Hash Lists and Crackable Uploads

### How do I create a hash list?

1. **Manual Creation**: Create empty hash list and add hashes individually
2. **File Upload**: Upload file containing hashes (various formats supported)
3. **Crackable Upload**: Upload files or paste hashes for automatic processing
4. **Import**: Import from other systems or previous campaigns

### What is the crackable upload feature?

Crackable uploads automate hash extraction and campaign creation:

- **File Support**: Upload `.zip`, `.pdf`, `.docx`, `.kdbx` files for hash extraction
- **Text Parsing**: Paste raw hash data from various sources
- **Auto-Detection**: Automatically detect hash types and formats
- **Campaign Generation**: Create campaigns with appropriate attacks automatically

### How does hash type detection work?

Ouroboros v2 includes intelligent hash type detection:

- **Pattern Matching**: Analyzes hash format and length
- **Confidence Scoring**: Provides confidence levels for detected types
- **Manual Override**: Allows manual hash type selection
- **Validation**: Verifies compatibility with hashcat

### Can I edit hash lists after creation?

Yes, hash lists support various editing operations:

- **Add Hashes**: Add individual hashes or import additional files
- **Remove Hashes**: Delete specific hashes or clear entire lists
- **Export**: Export to various formats (TSV, CSV, hashcat format)
- **Search and Filter**: Find specific hashes or filter by status

## Performance and Optimization

### How can I improve cracking performance?

1. **Hardware Optimization**:

   - Use high-end GPUs with sufficient memory
   - Ensure proper cooling and power supply
   - Optimize agent workload settings

2. **Attack Strategy**:

   - Start with targeted wordlists and rules
   - Use complexity scoring to prioritize attacks
   - Leverage previous passwords for targeted attacks

3. **Resource Management**:

   - Use appropriate resource sizes
   - Cache frequently used resources
   - Monitor agent performance and adjust settings

### Why are my attacks running slowly?

Common causes:

1. **Large Keyspace**: Attacks with huge keyspaces take longer
2. **Hardware Limitations**: Insufficient GPU memory or processing power
3. **Network Issues**: Slow resource downloads or connectivity problems
4. **Configuration**: Suboptimal workload or performance settings

### How do I monitor system performance?

Ouroboros v2 provides comprehensive monitoring:

- **Dashboard Metrics**: Real-time system overview
- **Agent Performance**: Individual agent performance charts
- **Campaign Progress**: Detailed progress tracking and estimates
- **Health Status**: System component health monitoring

## Security and Best Practices

### How secure is Ouroboros v2?

Ouroboros v2 includes multiple security features:

- **HTTPS Only**: All communication encrypted in transit
- **JWT Authentication**: Secure token-based authentication
- **Project Isolation**: Strict data separation between projects
- **Role-Based Access**: Granular permission controls
- **Audit Logging**: Comprehensive activity logging

### What are the password requirements?

Password requirements are configurable but typically include:

- **Minimum Length**: 8-12 characters
- **Complexity**: Mix of uppercase, lowercase, numbers, symbols
- **Rotation**: Regular password changes recommended
- **Uniqueness**: Cannot reuse recent passwords

### How should I organize projects?

Best practices for project organization:

- **Purpose-Based**: Organize by engagement, client, or objective
- **Security Boundaries**: Separate sensitive and non-sensitive data
- **Team Access**: Assign users based on need-to-know
- **Resource Sharing**: Use global resources for common tools

### What should I do if I suspect a security issue?

1. **Report Immediately**: Contact security team or administrator
2. **Document Evidence**: Preserve logs and evidence
3. **Isolate Systems**: Disconnect affected systems if necessary
4. **Don't Investigate**: Let security professionals handle the investigation

## Troubleshooting

### Where can I find logs?

Log locations vary by component:

- **Web Interface**: Browser developer console
- **Agent Logs**: `journalctl -u ouroboros-agent` or `/var/log/ouroboros/`
- **Server Logs**: Contact administrator for access
- **Application Logs**: Available through admin interface

### How do I report bugs or issues?

1. **Collect Information**: Gather error messages, logs, and reproduction steps
2. **Check Documentation**: Review troubleshooting guide first
3. **Contact Support**: Use appropriate support channels
4. **Provide Details**: Include environment details and exact error messages

### What information should I include in bug reports?

Essential information:

- **Ouroboros Version**: System version and build information
- **Environment**: Browser, OS, agent configuration
- **Error Messages**: Exact error text and codes
- **Reproduction Steps**: How to reproduce the issue
- **Expected Behavior**: What should have happened
- **Logs**: Relevant log entries and timestamps

## Integration and API

### Does Ouroboros v2 have an API?

Yes, Ouroboros v2 provides multiple APIs:

- **Agent API v1**: For Ouroboros agents (backward compatible)
- **Web API v1**: For web interface functionality
- **Control API v1**: For command-line tools and automation (partially implemented)
- **Future APIs**: Agent API v2 planned for enhanced features

### Can I automate Ouroboros operations?

Yes, through various methods:

- **Control API**: RESTful API for automation scripts (basic functionality available)
- **Command-line Tools**: CLI tools for common operations (planned)
- **Webhooks**: Event notifications for external systems (planned)
- **Export/Import**: JSON-based configuration sharing

### How do I integrate with external tools?

Integration options:

- **API Access**: Use RESTful APIs for data access
- **Export Formats**: Export results in various formats
- **Webhook Notifications**: Receive real-time event notifications (planned)
- **Custom Scripts**: Develop custom automation scripts

### What Control API features are currently available?

The Control API is partially implemented with:

- **Campaign Listing**: List campaigns with filtering and pagination
- **Hash Analysis**: Hash type detection and guessing
- **API Key Authentication**: Bearer token authentication for automation
- **RFC9457 Error Format**: Standardized error responses

**Note**: Full Control API functionality including campaign management, batch operations, and CLI tools are planned for future releases.

## Getting Help

### Where can I find more documentation?

- **User Guides**: Comprehensive guides for all features
- **API Documentation**: Complete API reference
- **Troubleshooting**: Common issues and solutions
- **Best Practices**: Optimization and security guidelines

### How do I contact support?

Support channels depend on your deployment:

- **Administrator**: Contact your local Ouroboros administrator
- **Documentation**: Check user guides and troubleshooting
- **Community**: Participate in user forums or communities
- **Professional Support**: Contact vendor for commercial support

### What training is available?

Training options may include:

- **Documentation**: Self-paced learning through user guides
- **Video Tutorials**: Step-by-step video demonstrations
- **Workshops**: Hands-on training sessions
- **Certification**: Professional certification programs

For additional information, see:

- [Web Interface Guide](web-interface.md) - Complete UI documentation
- [Agent Setup Guide](agent-setup.md) - Agent installation and configuration
- [Attack Configuration Guide](attack-configuration.md) - Attack types and configuration
- [Resource Management Guide](resource-management.md) - Resource handling
- [Troubleshooting Guide](troubleshooting.md) - Common issues and solutions
