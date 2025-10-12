# Ouroboros Product Overview

Ouroboros is a distributed password cracking management system designed for efficiency, scalability, and airgapped networks. It coordinates multiple hashcat instances across different machines to efficiently crack password hashes using various attack strategies.

## Key Features

- **Distributed Architecture**: Manages hash-cracking tasks across a network of agents/nodes
- **Web Interface**: Modern SvelteKit-powered UI with real-time monitoring
- **RESTful API**: OpenAPI 3.0.1 compliant API for programmatic access
- **Scalable Workload Distribution**: Efficiently distributes tasks across multiple machines
- **Hashcat Integration**: Leverages hashcat for versatile hash cracking capabilities
- **Airgap Support**: Designed for secure, isolated network environments

## Core Concepts

- **Campaigns**: Comprehensive units of work focused on a single hash list
- **Attacks**: Defined units of hashcat work (mode, wordlist, rules, etc.)
- **Tasks**: Smallest units of work assigned to agents for parallel processing
- **Agents**: Registered clients that execute tasks and report results
- **HashLists**: Sets of hashes targeted by campaigns
- **Templates**: Reusable attack definitions for consistent workflows

## Target Audience

- Medium to large-scale cracking infrastructure teams
- Organizations requiring secure, controlled password recovery operations
- Teams operating in airgapped or high-security network environments
- Users with reliable, high-speed LAN connections between cracking nodes

## License

Mozilla Public License Version 2.0 (MPL-2.0)
