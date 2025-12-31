# Ouroboros Implementation Plan

This document outlines the phased implementation plan for rebuilding Ouroboros with FastAPI, SvelteKit, and modern backend architecture. Each phase builds upon the last and ensures a modular, testable, and maintainable system.

---

## Table of Contents

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=3 --minlevel=1 -->

- [Ouroboros Implementation Plan](#ouroboros-implementation-plan)
  - [Table of Contents](#table-of-contents)
  - [Implementation Phases](#implementation-phases)
    - [Phase 1: Core Infrastructure (Completed)](#phase-1-core-infrastructure-completed)
    - [Phase 2: API Implementation (In Progress)](#phase-2-api-implementation-in-progress)
    - [Phase 2b: Resource Management (Completed)](#phase-2b-resource-management-completed)
    - [Phase 3: Web UI Development](#phase-3-web-ui-development)
    - [Phase 4: Containerization and Deployment](#phase-4-containerization-and-deployment)
    - [Phase 5: Task Distribution System](#phase-5-task-distribution-system)
    - [Phase 6: Monitoring, Testing and Documentation](#phase-6-monitoring-testing-and-documentation)
    - [Phase 7: TUI Development](#phase-7-tui-development)
  - [Notes](#notes)

<!-- mdformat-toc end -->

---

## Implementation Phases

### Phase 1: Core Infrastructure (Completed)

- [x] 👤 User Model
- [x] 📁 Project Model
- [x] 🧠 OperatingSystem Model
- [x] 🤖 Agent Model
- [x] ⚠️ AgentError Model
- [x] 💥 Attack Model
- [x] 🧾 Task Model

👉 [Read Phase 1: Core Infrastructure Setup](phase-1-core-infrastructure.md)

### Phase 2: API Implementation (In Progress)

- [x] 🔐 Agent API (High Priority)
  - [x] Agent Authentication & Session Management
  - [x] Attack Distribution
- [x] 🧠 Web UI API
  - [x] Campaign Management
  - [x] Attack Management
  - [x] Agent Management
  - [x] Resource Browser
  - [x] Hash List Management
  - [x] Crackable Uploads
  - [x] Authentication & Profile
  - [x] UX Utility
  - [x] Live Event Feeds (SSE)
- [ ] ⌨️ Control API - In Progress

Phase 2 was completed with comprehensive Web UI, including:

- **Web UI API** (`/api/v1/web/*`): Complete REST API supporting the SvelteKit frontend with authentication, campaign/attack management, agent monitoring, resource handling, hash list management, and real-time SSE event feeds
- **Supporting Infrastructure**: Hash guessing service, keyspace estimation algorithms, caching layer, and comprehensive validation
- **Advanced Features**: Ephemeral resources, attack templates, crackable file uploads, and live event broadcasting

👉 [Read Phase 2: API Implementation](phase-2-api-implementation.md)

### Phase 2b: Resource Management (Completed)

- [x] Add `minio-py` support to project
- [x] Add `MinioContainer` testcontainers support for integration tests
- [x] Add `StorageService` to handle MinIO operations
- [x] Migrate `resource_service` to use `StorageService`
- [x] Develop full suite of tests for `StorageService`
- [x] Develop full suite of tests for `resource_service`
- [x] Finalize Resource Management API and implement all endpoints

Phase 2b was fully completed and tested, allowing file-backed resources to be supported via the MinIO object storage.

👉 [Read Phase 2b: Resource Management](phase-2b-resource-management.md)

### Phase 3: Web UI Development

👉 [Read Phase 3: Web UI Development](phase-3-web-ui.md)

### Phase 4: Containerization and Deployment

👉 [Read Phase 4: Containerization and Deployment](phase-4-containerization-deployment.md)

### Phase 5: Task Distribution System

👉 [Read Phase 5: Task Distribution System](phase-5-task-distribution.md)

### Phase 6: Monitoring, Testing and Documentation

👉 [Read Phase 6: Monitoring, Testing, Documentation](phase-6-monitoring-testing-documentation.md)

### Phase 7: TUI Development

👉 [Read Phase 7: TUI Development](phase-7-tui-development.md)

---

## Notes

- [Core Algorithm Implementation Guide](core_algorithm_implementation_guide.md)
- Phase 4 was moved up to phase 2b to allow for the resource management to be completed before the web UI is fully implemented. There's currently a TODO to reshuffle the phases to reflect this, but just move to 5 after 3 is completed.
- As items in the various phases are completed, they are rolled up and added to this overview document.
