# Welcome to Ouroboros

Ouroboros is a distributed password cracking management system built with FastAPI and SvelteKit. It's a complete rewrite of Ouroboros, preserving backward compatibility while modernizing the architecture. It coordinates multiple agents running hashcat to efficiently distribute password cracking tasks across a network of machines.

## Features

- **Distributed Task Management**: Efficiently distribute password cracking tasks across multiple agents
- **Real-time Monitoring**: Track progress and performance of cracking tasks in real-time
- **Dual Web Interfaces**:
  - **SvelteKit Frontend**: Modern, high-performance web interface with JSON API and Flowbite Svelte/DaisyUI components
  - **NiceGUI Interface**: Python-native web interface integrated directly into the FastAPI backend for simplified deployment
- **RESTful API**: Well-documented API for agent communication and automation
- **Resource Management**: Centralized management of wordlists, rules, and masks
- **Secure Authentication**: JWT-based authentication for both web and agent interfaces
- **Docker Support**: Full containerization support for easy deployment

## Quick Links

- [Installation Guide](getting-started/installation.md)
- [Quick Start Tutorial](getting-started/quick-start.md)
- [Architecture Overview](architecture/overview.md)
- [Web Interface Guide](user-guide/web-interface.md)
- [NiceGUI Interface Guide](user-guide/nicegui-interface.md)
- [API Documentation](api/agent.md)
- [Testing Guide](development/testing.md)
- [Contributing Guide](development/contributing.md)

## Project Status

Ouroboros is under active development as an experimental rewrite of Ouroboros. The core features are stable and the Agent API v1 specification is fixed for backward compatibility, but we're continuously adding new features and improvements.

## Support

If you need help or want to contribute:

- Check out our [Contributing Guide](development/contributing.md)
- Review the [Development Setup](development/setup.md)
- Read the [Architecture Documentation](architecture/overview.md)

## License

Ouroboros is open source software licensed under the MPL-2.0 license.
