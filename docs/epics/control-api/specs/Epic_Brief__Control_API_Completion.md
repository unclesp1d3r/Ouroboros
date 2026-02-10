# Epic Brief: Control API Completion

## Summary

Complete the Control API to provide a comprehensive programmatic interface for Ouroboros that supports terminal-based workflows, automation scripts, and third-party integrations. Primary users include red team operators running automated cracking campaigns, system administrators managing deployments, and CLI/TUI power users who prefer not to rely on a browser. The Control API must support both operational workflows (campaigns/resources/monitoring/results) and headless administration (users/projects/API keys). It should be stable and machine-friendly (consistent pagination, structured responses, and RFC9457 problem details), while remaining flexible enough to support both official tooling and external clients.

## Context & Problem

### Who's Affected

**Primary Users:**

- **Red Team Operators**: Security professionals running automated password cracking campaigns as part of penetration testing and security assessments
- **System Administrators**: Infrastructure managers who need to configure, monitor, and maintain Ouroboros deployments programmatically
- **CLI/TUI Power Users**: Terminal-focused users who prefer command-line workflows over browser-based interfaces

**Secondary Stakeholders:**

- **Third-Party Tool Developers**: Engineers building integrations with Ouroboros for security toolchains and CI/CD pipelines
- **Automation Script Authors**: Users creating custom workflows and batch operations for repetitive tasks

### Current pain (validated)

- **Browser dependency** blocks terminal-first workflows and automation.
- **Incomplete end-to-end headless coverage**: core actions (create campaigns/resources, run campaigns, monitor, retrieve results) are not consistently available through a single programmatic surface.
- **Missing programmatic admin** makes headless operations difficult (user/project/key management).
- **Integration friction**: third-party tools need a clear, stable, machine-readable API contract.

### Where in the Product

The Control API sits alongside the existing Web UI API and Agent API as one of three primary interfaces to Ouroboros:

- **Agent API** (`/api/v1/client/*`): For distributed hashcat agents executing tasks
- **Web UI API** (`/api/v1/web/*`): For the SvelteKit browser-based dashboard
- **Control API**: For CLI/TUI clients, automation scripts, and third-party integrations (this Epic)

The Control API reuses the same underlying business capabilities as the Web UI, but is optimized for machine workflows (stable error format, pagination, and clear project scoping).

### Success Criteria

This Epic is successful when:

1. **Headless workflow completeness**: users can manage campaigns end-to-end (including results retrieval/exports) without touching the Web UI.
2. **Headless administration**: admins can manage users/projects/API keys without the Web UI.
3. **Reliable integration**: third-party tools and scripts can integrate through stable, machine-readable behaviors.
4. **Automation efficiency**: bulk operations and scripted workflows are materially faster than manual UI workflows.

### Out of Scope

- Building the CLI/TUI client itself (the Control API is the foundation)
- Web UI-only helper behaviors and presentation-specific endpoints
- Changes to the Agent API contract
