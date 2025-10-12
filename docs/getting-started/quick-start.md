# Quick Start Guide

This guide will walk you through your first steps with Ouroboros after installation. You'll create a project, register an agent, upload resources, and run your first password cracking campaign.

> **Prerequisites**: Complete the [Installation Guide](installation.md) before proceeding.

---

## Table of Contents

<!-- mdformat-toc start --slug=gitlab --no-anchors --maxlevel=2 --minlevel=1 -->

- [Quick Start Guide](#quick-start-guide)
  - [Table of Contents](#table-of-contents)
  - [Initial Setup](#initial-setup)
  - [Create Your First Project](#create-your-first-project)
  - [Register Your First Agent](#register-your-first-agent)
  - [Upload Attack Resources](#upload-attack-resources)
  - [Create Your First Campaign](#create-your-first-campaign)
  - [Monitor Progress](#monitor-progress)
  - [Agent Management](#agent-management)
  - [Best Practices](#best-practices)
  - [Common Workflows](#common-workflows)
  - [Troubleshooting](#troubleshooting)
  - [Next Steps](#next-steps)
  - [Additional Resources](#additional-resources)
  - [Support](#support)

<!-- mdformat-toc end -->

---

## Initial Setup

### 1. Access the Web Interface

Open your web browser and navigate to your Ouroboros installation:

- Direct access: `http://your-server:8000`
- Through reverse proxy: `http://your-domain.com`

### 2. First Login

Login with the admin credentials you configured during installation:

- **Email**: The value you set for `FIRST_SUPERUSER` in your `.env` file
- **Password**: The value you set for `FIRST_SUPERUSER_PASSWORD` in your `.env` file

### 3. Change Default Password

For security, immediately change your admin password:

1. Click your profile icon in the top-right corner
2. Select "Profile Settings"
3. Click "Change Password"
4. Enter a strong, unique password

## Create Your First Project

Projects provide multi-tenant isolation in Ouroboros. Each project has its own campaigns, hash lists, and resources.

### 1. Navigate to Projects

1. Click "Projects" in the main navigation
2. Click "Create Project"

### 2. Configure Project

Fill in the project details:

- **Name**: Choose a descriptive name (e.g., "Penetration Test 2024")
- **Description**: Brief description of the project's purpose
- **Visibility**: Set to "Private" for sensitive work

### 3. Set Active Project

After creation, make sure your new project is selected as the active project in the project selector dropdown.

## Register Your First Agent

Agents are the machines that will run hashcat to crack passwords. You need at least one agent to perform cracking tasks.

### 1. Navigate to Agents

1. Click "Agents" in the main navigation
2. Click "Register Agent"

### 2. Configure Agent

Fill in the agent details:

- **Agent Name**: Descriptive name for the machine (e.g., "GPU-Server-01")
- **Projects**: Select the project(s) this agent can work on
- **Description**: Optional description of the agent's capabilities

### 3. Copy Agent Token

After creation, **immediately copy the agent token** - it will only be shown once. You'll need this token to configure the agent software on your cracking machine.

### 4. Install Agent Software

On your cracking machine (the one with hashcat installed):

1. Download the Ouroboros agent from the releases page
2. Configure the agent with your server URL and token
3. Start the agent service

The agent will appear as "Online" in the web interface once connected.

## Upload Attack Resources

Before creating campaigns, you'll need attack resources like wordlists, rules, and masks.

### 1. Navigate to Resources

1. Click "Resources" in the main navigation
2. Click "Upload Resource"

### 2. Upload a Wordlist

Start with a basic wordlist:

- **File**: Upload a wordlist file (e.g., `rockyou.txt`)
- **Name**: Give it a descriptive name
- **Type**: Select "Word List"
- **Description**: Brief description of the wordlist

### 3. Upload Rules (Optional)

If you have hashcat rule files:

- **File**: Upload a `.rule` file
- **Type**: Select "Rule List"
- **Name**: Descriptive name for the rules

### 4. Upload Masks (Optional)

For mask attacks:

- **File**: Upload a mask file
- **Type**: Select "Mask List"
- **Name**: Descriptive name for the masks

## Create Your First Campaign

Campaigns organize your password cracking efforts around a specific set of hashes.

### 1. Prepare Your Hashes

Create a hash list file with one hash per line. Supported formats include:

- Raw hashes: `5d41402abc4b2a76b9719d911017c592`
- Shadow format: `user:$6$salt$hash`
- NTLM format: `user:1001:hash1:hash2:::`

### 2. Create Hash List

1. Click "Hash Lists" in the main navigation
2. Click "Create Hash List"
3. **Name**: Give your hash list a descriptive name
4. **Upload**: Upload your hash file or paste hashes directly
5. **Hash Type**: Ouroboros will attempt to detect the hash type automatically

### 3. Create Campaign

1. Click "Campaigns" in the main navigation
2. Click "Create Campaign"
3. Fill in the campaign details:
   - **Name**: Descriptive campaign name
   - **Description**: Purpose and scope of the campaign
   - **Hash List**: Select the hash list you just created
   - **Priority**: Set campaign priority (Normal is fine for first campaign)

### 4. Add Attacks to Campaign

After creating the campaign, add attacks:

1. Click "Add Attack" in the campaign detail view
2. Choose attack type:

#### Dictionary Attack (Recommended for beginners)

- **Attack Type**: Dictionary
- **Wordlist**: Select your uploaded wordlist
- **Rules**: Optionally select rule files for password mutations
- **Min/Max Length**: Set password length constraints

#### Mask Attack

- **Attack Type**: Mask
- **Mask**: Enter a hashcat mask (e.g., `?u?l?l?l?l?l?d?d` for "Ullllldd" pattern)
- **Custom Charsets**: Define custom character sets if needed

#### Brute Force Attack

- **Attack Type**: Brute Force
- **Character Sets**: Select character types (lowercase, uppercase, numbers, symbols)
- **Length Range**: Set minimum and maximum password length

### 5. Start the Campaign

1. Review your attack configuration
2. Click "Start Campaign"
3. The campaign will begin distributing tasks to available agents

## Monitor Progress

### 1. Campaign Dashboard

Monitor your campaign progress:

- **Overall Progress**: Percentage of keyspace searched
- **Cracked Hashes**: Number of passwords found
- **Active Tasks**: Current agent activity
- **Performance**: Hashes per second across all agents

### 2. Real-time Updates

The interface updates in real-time as agents report progress and find passwords.

### 3. View Results

When passwords are cracked:

1. Navigate to the campaign detail view
2. Click "Results" tab
3. View cracked passwords (if you have appropriate permissions)
4. Export results in various formats

## Agent Management

### 1. Monitor Agent Health

Keep an eye on your agents:

- **Status**: Online/Offline status
- **Performance**: Current hash rate
- **Temperature**: GPU/CPU temperatures
- **Utilization**: Hardware utilization percentages

### 2. Agent Configuration

Configure agent settings:

- **Enable/Disable**: Toggle agent availability
- **Device Selection**: Choose which GPUs/CPUs to use
- **Workload Profile**: Adjust hashcat workload settings
- **Update Interval**: How often the agent checks for new tasks

## Best Practices

### 1. Resource Management

- **Organize Resources**: Use descriptive names and organize by type
- **Test Small First**: Start with small wordlists to verify setup
- **Monitor Storage**: Keep an eye on MinIO storage usage

### 2. Campaign Strategy

- **Start Simple**: Begin with dictionary attacks before trying complex masks
- **Layer Attacks**: Use multiple attack types in sequence
- **Monitor Performance**: Adjust based on agent capabilities

### 3. Security

- **Project Isolation**: Use separate projects for different clients/purposes
- **Access Control**: Limit user access to appropriate projects
- **Regular Backups**: Backup your database and MinIO data

### 4. Performance Optimization

- **Agent Placement**: Place agents close to the server network-wise
- **Resource Sizing**: Match attack complexity to agent capabilities
- **Workload Balancing**: Distribute work across multiple agents

## Common Workflows

### 1. Penetration Testing

1. Create project for the engagement
2. Upload client-specific wordlists
3. Create hash list from extracted hashes
4. Run progressive attacks (dictionary → rules → masks → brute force)
5. Export results for reporting

### 2. Security Assessment

1. Create hash list from system dumps
2. Start with common passwords (dictionary attack)
3. Add complexity with rule-based mutations
4. Use masks for organization-specific patterns
5. Monitor for policy compliance

### 3. Research and Training

1. Create educational projects
2. Use known hash sets for testing
3. Experiment with different attack strategies
4. Benchmark agent performance

## Troubleshooting

### 1. Agent Won't Connect

- Verify network connectivity between agent and server
- Check agent token is correct
- Ensure firewall allows agent communication
- Review agent logs for error messages

### 2. Poor Performance

- Check agent hardware utilization
- Verify hashcat is properly installed on agents
- Monitor network bandwidth usage
- Consider workload profile adjustments

### 3. Campaign Not Starting

- Ensure at least one agent is online and enabled
- Verify hash list is properly formatted
- Check attack configuration is valid
- Review campaign logs for errors

### 4. Resource Upload Issues

- Verify MinIO is running and accessible
- Check file size limits
- Ensure proper file format
- Review MinIO logs for errors

## Next Steps

Now that you have Ouroboros running:

1. **Scale Up**: Add more agents to increase cracking power
2. **Optimize**: Fine-tune attack strategies based on your results
3. **Automate**: Use the API to integrate with other security tools
4. **Monitor**: Set up monitoring and alerting for production use

## Additional Resources

- [User Guide](../user-guide/web-interface.md): Detailed interface documentation
- [API Reference](../development/api-reference.md): REST API documentation
- [Troubleshooting](../user-guide/troubleshooting.md): Common issues and solutions
- [Security Guide](../development/security.md): Security best practices

## Support

If you need help:

1. Check the [Troubleshooting Guide](../user-guide/troubleshooting.md)
2. Review the logs for error messages
3. Search [GitHub Issues](https://github.com/unclesp1d3r/Ouroboros/issues)
4. Create a new issue with detailed information about your problem
