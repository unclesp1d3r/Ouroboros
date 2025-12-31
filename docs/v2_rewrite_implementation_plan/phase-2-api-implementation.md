# Phase 2: API Implementation

This document defines the complete Phase 2 API architecture for Ouroboros. To keep this file manageable, detailed implementations are split into sub-files in the `phase-2-api-implementation-parts` directory.

---

## Table of Contents

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=3 --minlevel=1 -->

- [Phase 2: API Implementation](#phase-2-api-implementation)
  - [Table of Contents](#table-of-contents)
  - [Agent API (High Priority)](#agent-api-high-priority)
  - [Supporting Algorithms](#supporting-algorithms)
    - [Hash Guessing Logic](#hash-guessing-logic)
  - [Web UI API (`/api/v1/web/*`) - COMPLETED](#web-ui-api-apiv1web---completed)
    - [Implementation Summary](#implementation-summary)
    - [Detailed Implementation](#detailed-implementation)
  - [Control API (`/api/v1/control/*`)](#control-api-apiv1control)
  - [Shared Schema: Save/Load](#shared-schema-saveload)
    - [Scope](#scope)
    - [Usage](#usage)
    - [Format Requirements](#format-requirements)
    - [Validation](#validation)
    - [Sample Structure](#sample-structure)
    - [Implementation Tasks](#implementation-tasks)
  - [Current Implementation Status](#current-implementation-status)
    - [Completed Components](#completed-components)
    - [Remaining Work](#remaining-work)
    - [Technical Achievements So Far](#technical-achievements-so-far)
    - [Next Steps](#next-steps)

<!-- mdformat-toc end -->

---

<!-- section: agent-api-apiv1client -->

## Agent API (High Priority)

👉 **Full implementation details**: [Phase 2 - Part 1](phase-2-api-implementation-parts/phase-2-api-implementation-part-1.md)

---

<!-- section: supporting-algorithms -->

## Supporting Algorithms

### Hash Guessing Logic

Ouroboros should include a reusable hash analysis and type inference utility built around the [Name-That-Hash](https://github.com/bee-san/Name-That-Hash) library. This utility should be implemented in the service layer and callable from both the Web UI API and the Control API. It is responsible for examining pasted text, extracted hash lines, or uploaded artifacts and returning likely hash types based on structure, length, encoding, and known patterns.

The service must:

- Use `name-that-hash`'s native Python API (not subprocess)
- Wrap its response in Ouroboros-style confidence-ranked outputs
- Be independently unit tested
- Be integration tested via the Web UI's hash validation endpoint capable of examining pasted text, extracted hash lines, or uploaded artifacts and returning likely hash types based on structure, length, encoding, and known patterns.

#### Requirements

- [x] Accept pasted lines, files, or blobs of unknown hash material

- [x] Identify most likely matching hash types (from hashcat-compatible types)

- [x] Return ranked suggestions with confidence scores

- [x] Handle common multiline inputs like:

  - `/etc/shadow` lines
  - `secretsdump` output
  - Cisco IOS config hash lines

- [x] Normalize formatting (e.g., strip usernames, delimiters)

- [x] Expose results in a format usable by both API layers and testable independently

Example response:

```json
{
  "candidates": [
    {
      "hash_type": 1800,
      "name": "sha512crypt",
      "confidence": 0.95
    },
    {
      "hash_type": 7400,
      "name": "sha256crypt",
      "confidence": 0.35
    }
  ]
}
```

This layer will power:

- Crackable Uploads (Web UI)
- Direct hash submission tools (Control API)
- Potential future CLI tools like `ouroboros guess-hash`

---

## Web UI API (`/api/v1/web/*`) - **COMPLETED**

### Implementation Summary

The Web UI API provides a comprehensive REST interface for the SvelteKit frontend, delivering:

- **Campaign Management**: Complete CRUD operations with attack orchestration, lifecycle controls, and progress monitoring
- **Attack Editor**: Full-featured attack configuration with real-time validation, keyspace estimation, and template support
- **Agent Management**: Comprehensive agent monitoring, hardware configuration, performance tracking, and error reporting
- **Resource Browser**: File upload/download with inline editing, validation, and metadata management
- **Hash List Management**: Secure hash import/export with project-level isolation
- **Authentication & Authorization**: JWT-based authentication with role-based access control and project context switching
- **Live Event System**: Server-Sent Events (SSE) for real-time UI updates without polling

### Detailed Implementation

👉 **Complete implementation details**: [Phase 2 - Part 2](phase-2-api-implementation-parts/phase-2-api-implementation-part-2.md)

---

## Control API (`/api/v1/control/*`)

👉 **Implementation details**: [Phase 2 - Part 3](phase-2-api-implementation-parts/phase-2-api-implementation-part-3.md)

---

## Shared Schema: Save/Load

Ouroboros supports export and import of core objects using a shared JSON-based schema. These templates are used by both the Web UI and the Control API to persist, modify, and replicate campaign structures across environments.

### Scope

The following object types support import/export:

- Campaigns
- Attacks
- Resource Bundles (optional future feature)

### Usage

- Web UI: save/load dialogs, Crackable Upload post-processing
- Control API: `csadmin campaign export`, `csadmin attack import`, etc.
- JSON files may be checked into version control or bundled for transport

### Format Requirements

- Schema must match Web UI expectations exactly (round-trip safe)

- All fields must be versioned implicitly or explicitly

- Reserved fields:

  - `schema_version` (optional)
  - `project_id` may be omitted or overridden during import.

### Validation

- JSON templates must be validated against their Pydantic schema before use
- Ouroboros should ignore unknown fields on templates

### Sample Structure

Each referenced resource (wordlist, rule, mask) must use a stable UUID (`guid`) if it is a named, non-ephemeral file. This GUID is assigned at resource creation and used to re-link templates during import.

On import:

- If a referenced resource `guid` does not exist in the target project, the importer must prompt for a replacement, skip the attack, or abort
- Ephemeral files may be inlined in the template (e.g., a `wordlist_inline` or `masks: []` field)
  - `masks` is an array of strings, with each in hashcat mask `hcmask` format (`abcdef,0123,ABC,789,?3?3?3?1?1?1?1?2?2?4?4?4?4`) to allow custom character sets
  - `words` is an array of strings, with each a dictionary word, containing a single word or phrase that will be converted to a newline-separated list of words
- 📌 _Note: Standard Attack Resource Files are not embedded in save/load templates. Campaigns reference existing resources by ID. Resource metadata and crackable hash import/export are handled through the Resource API, not the template layer._

```json
{
  "schema_version": "20250511",
  "name": "Weekly Campaign 12",
  "description": "Pulled from red team box dump",
  "attacks": [
    {
      "mode": "dictionary",
      "wordlist_guid": "f3b85a92-45c8-4e7d-a1cd-6042d0e2deef",
      "rulelist_guid": "f3b85a92-45c8-4e7d-a1cd-6042d0e2deef",
      "min_length": 6,
      "max_length": 16
    },
    {
      "mode": "mask",
      "masklist_guid": "f3b85a92-45c8-4e7d-a1cd-6042d0e2deef"
    },
    {
      "mode": "mask",
      "masks": [
        "abcdef,0123,ABC,789,?3?3?3?1?1?1?1?2?2?4?4?4?4",
        "?l?l?l?l?d?d?d?d?d?d"
      ]
    }
  ]
}
```

### Implementation Tasks

- [x] `schemas.shared.AttackTemplate` - JSON-compatible model for attacks `task_id:schema.attack_template`
- [x] `schemas.shared.CampaignTemplate` - Top-level structure including attacks/hashlist `task_id:schema.campaign_template`
- [x] `schema_loader.validate()` - Helper to validate, coerce, and upgrade templates `task_id:schema.validation_layer`
- [x] `schema_loader.load_campaign_template()` - Helper to validate, coerce, and load campaign template into a `Campaign` object `task_id:schema.campaign_loader`
- [x] `schema_loader.load_attack_template()` - Helper to validate, coerce, and load attack template into a `Attack` object `task_id:schema.attack_loader`
- [x] (task_id:attack.export_json) Implement attack/campaign template import/export endpoints and tests
- [x] Add support to export any single Attack or entire Campaign to a JSON file `task_id:attack.export_json`

---

## Current Implementation Status

**Overall Status: 🔄 IN PROGRESS** (2 of 3 parts completed)

Phase 2 has made significant progress with Parts 1 and 2 completed, delivering core API functionality for Ouroboros:

### Completed Components

#### Agent API Implementation (Part 1) - **COMPLETED**

- **Legacy Compatibility**: Full compliance with `contracts/v1_api_swagger.json` specification for seamless migration from Ruby-on-Rails version
- **Task Distribution**: Complete task lifecycle management including creation, assignment, progress tracking, and result collection
- **Authentication**: Bearer token-based security with automatic agent registration and heartbeat monitoring
- **Resource Management**: S3-compatible object storage integration with presigned URL downloads

👉 _See [Phase 2 - Part 1](phase-2-api-implementation-parts/phase-2-api-implementation-part-1.md) for detailed implementation_

#### Web UI API Implementation (Part 2) - **COMPLETED**

Complete REST interface for SvelteKit frontend with campaign management, attack orchestration, agent monitoring, resource handling, authentication, and real-time SSE events.

👉 _See [Web UI API section](#-web-ui-api-apiv1web---completed) above for summary_

#### Supporting Infrastructure - **COMPLETED**

- **Hash Guessing Service**: Name-That-Hash integration for automatic hash type detection
- **Keyspace Estimation**: Advanced algorithms for attack complexity scoring and time estimation
- **Caching Layer**: Cashews-based caching with Redis/memory backend support
- **Ephemeral Resources**: Attack-local resources for wordlists and mask patterns
- **Template System**: JSON-based import/export for campaigns and attacks
- **Crackable Uploads**: Automated hash extraction from files and paste operations

### Remaining Work

#### Control API Implementation (Part 3) - **NOT STARTED**

- **RFC9457 Compliance**: Standardized error responses using Problem Details for HTTP APIs
- **Programmatic Interface**: Complete API surface for CLI/TUI automation and scripting
- **Batch Operations**: Efficient bulk operations for large-scale campaign management

👉 _See [Phase 2 - Part 3](phase-2-api-implementation-parts/phase-2-api-implementation-part-3.md) for planned implementation_

### Technical Achievements So Far

- **Strong Typing**: Comprehensive Pydantic models throughout the API stack
- **Validation**: Multi-layer validation from input sanitization to business logic constraints
- **Testing**: Extensive unit and integration test coverage with Testcontainers for MinIO
- **Documentation**: Complete API reference with endpoint descriptions and examples
- **Performance**: Optimized database queries with pagination and efficient resource management

### Next Steps

The Web UI API foundation is ready to support **Phase 3: Frontend Implementation**, while the Control API (Part 3) remains to be implemented for CLI/TUI support in the future.
