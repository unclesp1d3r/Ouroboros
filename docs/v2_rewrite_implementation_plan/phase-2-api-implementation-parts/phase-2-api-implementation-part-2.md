# Web UI API (`/api/v1/web/*`)

These endpoints support the Svelte-base dashboard that human users interact with. They power views, forms, toasts, and live updates. Agents do not use these endpoints. All list endpoints must support pagination and query filtering (the response object should derive from the `PaginatedResponse` object).

---

🧭 These endpoints define the backend interface needed to support the user-facing views described in [Phase 3 - Web UI Foundation](../phase-3-web-ui-foundation.md). As you implement the frontend (Phase 3), be sure to reference this section to ensure every view or modal maps to a corresponding route here. We recommend annotating components with source endpoint comments and may add cross-references in Phase 3 to maintain that alignment. Some amount of the frontend has already been implemented and will need to be maintained and refactored as the backend is implemented.

These endpoints support the Svelte-base dashboard that human users interact with. They power views, forms, toasts, and live updates. Agents do not use these endpoints. All list endpoints must support pagination and query filtering.

---

## Table of Contents

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=3 --minlevel=1 -->

- [Web UI API (`/api/v1/web/*`)](#web-ui-api-apiv1web)
  - [Table of Contents](#table-of-contents)
  - [Authentication and Profile](#authentication-and-profile)
  - [Campaign Management](#campaign-management)
    - [Model Requirements](#model-requirements)
    - [Implementation Tasks](#implementation-tasks)
  - [Attack Management](#attack-management)
    - [UX Design Goals](#ux-design-goals)
    - [Implementation Tasks](#implementation-tasks-1)
  - [Hash List Management](#hash-list-management)
    - [UX Design Goals](#ux-design-goals-1)
    - [Agent Management](#agent-management)
    - [Resource Browser](#resource-browser)
    - [Line-Oriented Editing](#line-oriented-editing)
  - [UX Support and Utility](#ux-support-and-utility)
    - [Purpose](#purpose)
    - [Implementation Tasks](#implementation-tasks-2)
    - [Crackable Uploads](#crackable-uploads)
    - [Live Event Feeds (Server-Sent Events)](#live-event-feeds-server-sent-events)
    - [Implementation Tasks (SSE Event System)](#implementation-tasks-sse-event-system)
  - [Supporting Infrastructure](#supporting-infrastructure)
    - [File Layout](#file-layout)
    - [Module Responsibilities](#module-responsibilities)
    - [Migration from WebSocket Implementation](#migration-from-websocket-implementation)
    - [Documentation Updates](#documentation-updates)
    - [Additional Tasks](#additional-tasks)

<!-- mdformat-toc end -->

---

## Authentication and Profile

_Includes endpoints for administrator management of users and project access rights._

💡 _Note: Users can only update their own name and email. Role assignment and project membership changes are restricted to admins._

- [x] `POST /api/v1/web/auth/login` - Login `task_id:auth.login`
- Authentication for the web interface is handled by JWT tokens in the `Authorization` header and the `app.auth` module. Authorization is handled by the `app.auth.get_current_user` dependency and by casbin in the `app.authz` module.
- [x] `POST /api/v1/web/auth/logout` - Logout `task_id:auth.logout`
- [x] `POST /api/v1/web/auth/refresh` - Refresh JWT token `task_id:auth.refresh`
- [x] `GET /api/v1/web/auth/me` - Profile details `task_id:auth.me`
- [x] `PATCH /api/v1/web/auth/me` - Update name/email `task_id:auth.update_me`
- [x] `POST /api/v1/web/auth/change_password` - Change password `task_id:auth.change_password`
- [x] `GET /api/v1/web/auth/context` - Get current user + project context `task_id:auth.get_context` - See [Auth Context](../notes/specific_tasks/auth_context.md) for details.
- [x] `POST /api/v1/web/auth/context` - Switch active project `task_id:auth.set_context` - See [Auth Context](../notes/specific_tasks/auth_context.md) for details.
- [x] `GET /api/v1/web/users/` - 🔐 Admin: list all users (paginated, filterable) `task_id:auth.list_users` - This uses the flowbite table component (see [Table with Users](https://flowbite.com/docs/components/tables/#table-with-users) for inspiration) and supports filtering and pagination.
- [x] `POST /api/v1/web/users/` - 🔐 Admin: create user `task_id:auth.create_user`
- [x] `GET /api/v1/web/users/{id}` - 🔐 Admin: view user detail `task_id:auth.get_user`
- [x] `PATCH /api/v1/web/users/{id}` - 🔐 Admin: update user info or role `task_id:auth.update_user`
- [x] `DELETE /api/v1/web/users/{id}` - 🔐 Admin: deactivate or delete user `task_id:auth.delete_user`
- [x] `GET /api/v1/web/projects/` - 🔐 Admin: list all projects `task_id:auth.list_projects`
- [x] POST /api/v1/web/projects/ - 🔐 Admin: create project `task_id:web.projects.create_project`
- [x] `GET /api/v1/web/projects/{id}` - 🔐 Admin: view project info `task_id:auth.get_project`
- [x] `PATCH /api/v1/web/projects/{id}` - 🔐 Admin: update name, visibility, user assignment `task_id:auth.update_project` - Users have a many-to-many relationship with projects through `ProjectUserAssociation` and `ProjectUserRole`.
- [x] `DELETE /api/v1/web/projects/{id}` - 🔐 Admin: archive project `task_id:auth.delete_project` - This should be a soft delete, and the project should be archived.
- Audit existing endpoints in `/api/v1/web` for authentication/authorization. - This will be done in its own project.
  - See [Authentication Cleanup](../side_quests/authentication_cleanup.md) for audit results and implementation plan.
  - Ensure that all endpoints in `/api/v1/web`, except for `/api/v1/web/auth/login`, require authentication using the `get_current_user` dependency.
  - Ensure that all endpoints in `/api/v1/web` are protected by the `user_can` function.
  - Ensure that all endpoints in `/api/v1/web` check the currently selected project context (see `task_id:auth.get_context`) and only return data for the currently selected project.

---

## Campaign Management

For additional notes on the campaign management, see [Campaign Notes](../notes/campaign_notes.md).

### Model Requirements

To fully support UI ordering, user-friendly attack summaries, and richer campaign lifecycle controls, the following model-level fields must be added or updated:

- [x] Add `Attack.position: int` - numeric ordering field within a campaign `task_id:model.attack.position`
- [x] Add `Attack.comment: Optional[str]` - user-provided description for UI display `task_id:model.attack.comment`
- [x] Add `Attack.complexity_score: Optional[int]` - derived from keyspace or agent benchmarks, range 1-5 `task_id:model.attack.complexity_score`
- [x] Optionally evolve `Campaign.active: bool` into `Campaign.state: Enum` (`draft`, `active`, `archived`, etc.) to support lifecycle toggles and clear workflow states `task_id:model.campaign.state_enum`

These fields must be integrated into campaign detail responses, sortable/queryable in the DB layer, and respected in API output.

---

### Implementation Tasks

#### Note: Agent Configuration and Telemetry

Some agent configuration and telemetry endpoints (e.g., fine-grained device toggles, temperature abort thresholds, hashcat backend flags) may not be fully supported by the current v1 Agent API.

These are earmarked for Phase 5 implementation when Agent API v2 is introduced.

Be sure to encapsulate such features behind feature flags or optional fields in the backend to avoid breaking compatibility.

#### Note: Agent Display Name Fallback

logic:

`display_name = agent.custom_label or agent.host_name`

This fallback logic must be applied anywhere an agent is shown to the user. Include this behavior in both API response schemas and frontend component logic to ensure consistent display.

- [x] Add `guid: UUID = uuid4()` field to `AttackResourceFile` to enable export/import referencing `task_id:model.resource.guid_support`
- [x] Add `POST /api/v1/web/campaigns/{id}/reorder_attacks` to accept a list of attack IDs and persist order `task_id:campaign.reorder_attacks`
- [x] Add `POST /api/v1/web/attacks/{id}/move` with direction (`up`, `down`, `top`, `bottom`) to reposition relative to other attacks `task_id:attack.move_relative` (refactored to use service-layer only, no DB code in endpoint)
- [x] Add `POST /api/v1/web/attacks/{id}/duplicate` to clone an attack in-place `task_id:attack.duplicate`
- [x] Add `DELETE /api/v1/web/attacks/bulk` to delete multiple attacks by ID `task_id:attack.bulk_delete`
- [x] Add `POST /api/v1/web/campaigns/{id}/start` and `POST /api/v1/web/campaigns/{id}/stop` to manage lifecycle state `task_id:campaign.lifecycle_toggle`
- [x] Add or enrich campaign attack view model to support: type label, length, friendly settings summary, keyspace, complexity, and user comments `task_id:campaign.attack_summary_viewmodel`
- [x] `GET /api/v1/web/campaigns/` - List campaigns (paginated, filterable). Should support JSON polling or SSE-driven update triggers to notify the browser when campaign progress changes and refresh the relevant list view. `task_id:campaign.list_view`
- [x] `POST /api/v1/web/campaigns/` - Create a new campaign `task_id:campaign.create`
- [x] `GET /api/v1/web/campaigns/{id}` - Campaign detail view with attacks/tasks `task_id:campaign.detail_view`
- [x] `PATCH /api/v1/web/campaigns/{id}` - Update campaign `task_id:campaign.update`
- [x] `DELETE /api/v1/web/campaigns/{id}` - Archive/delete campaign `task_id:campaign.archive_delete`
- [x] `POST /api/v1/web/campaigns/{id}/add_attack` - Add attack to campaign `task_id:campaign.add_attack`
- [x] `GET /api/v1/web/campaigns/{id}/progress` - Structure and return campaign progress/status JSON data for polling `task_id:campaign.progress_data`
- [x] `GET /api/v1/web/campaigns/{id}/metrics` - Aggregate stats (see items 3 and 5 of [Core Algorithm Implementation Guide](../core_algorithm_implementation_guide.md)) `task_id:campaign.metrics_summary`
- [x] `POST /api/v1/web/campaigns/{id}/relaunch` - Relaunch attack if previously failed, or if any linked resource (wordlist, mask, rule) has been modified since the last run. Requires re-validation and explicit user confirmation. `task_id:campaign.rerun_attack`

---

## Attack Management

For additional notes on the attack editor UX, see [Attack Notes](../notes/attack_notes.md).

### UX Design Goals

These design goals are for the attack editor modal and should be applied to the data sent to the client. Though not exclusively API-related, these are important considerations for the API implementation and will be finalized in Phase 3 with the full user interface implementation. After adding the appropriate supporting functionality to the models and endpoints, Skirmish should add stub components for these views with TODO comments to ease implementing phase 3 frontend.

#### Common Editing Features

- [x] Dynamically update keyspace and complexity score for unsaved changes `task_id:attack.ux_estimate_unpersisted`
- [x] Show these values in attack editor view like campaign detail view `task_id:attack.ux_estimate_view`
- [x] Warn and require confirmation when editing an `exhausted` or `running` attack `task_id:attack.ux_edit_lifecycle_reset`
- [x] Confirming edit resets attack to `pending` and triggers reprocessing `task_id:attack.ux_edit_lifecycle_reset`
- [x] Allow export/import of JSON files for Attack or Campaign (supports template reuse) `task_id:attack.ux_export_import_json`

#### Dictionary Attack UX

See [New Dictionary Attack Editor](../notes/ui_screens/new_dictionary_attack_editor.md) for more details.

- [x] Min/max length fields default to typical hash type range (e.g., 1-32) `task_id:attack.ux_dictionary_length_defaults`
- [x] Wordlist dropdown with search, sorted by last modified, includes entry count `task_id:attack.ux_dictionary_wordlist_dropdown`
- [x] "Modifiers" button group for non-expert users (e.g., `+ Change Case`, `+ Substitute Characters`) in dictionary attack editor (`task_id:attack.ux_dictionary_modifiers`)
- [x] Optional rule list dropdown for expert users `task_id:attack.ux_dictionary_rule_dropdown`
  - This should be a [Searchable Dropdown](https://flowbite.com/docs/components/dropdowns/#dropdown-with-search) that allows the user to search for a rule by name and select one.
- [x] Support "Previous Passwords" as dynamic wordlist option `task_id:attack.ux_dictionary_previous_passwords`
  - This will automatically generate a dynamic wordlist from the previous project's cracked passwords. When this option is select, the wordlist dropdown and the option for ephemeral wordlist should be hidden. The dynamic wordlist is not persisted and is generated on the fly when the attack is run or rerun.
- [x] Support ephemeral wordlist field with "Add Word" UI for small lists `task_id:attack.ux_dictionary_ephemeral_wordlist`
  - This should be a [Flowbite Text Input](https://flowbite.com/docs/forms/input/) with a "+" button to add a new word. The words should be persisted in the attack resource file and used as a generated wordlist when the attack is run.

#### Mask Attack UX

See [New Mask Attack Editor](../notes/ui_screens/new_mask_attack_editor.md) for more details.

- [x] Add/remove inline mask lines (ephemeral mask list) `task_id:attack.ux_mask_inline_lines`
- [x] Validate mask syntax in real-time `task_id:attack.ux_mask_syntax_validation`
  - This should follow hashcat's mask syntax restrictions. This applies to the mask input field implemented in `task_id:attack.ux_mask_inline_lines` and the validation should be triggered when the user leaves the input field.
- [x] Ephemeral mask list stored only with the attack, deleted when attack is removed `task_id:attack.ux_mask_ephemeral_storage`
- [x] Add/remove inline mask lines (ephemeral mask list) `task_id:attack.ux_mask_inline_lines`
  - This should be a [Flowbite Text Input](https://flowbite.com/docs/forms/input/) with a "+" button to add a new word. The masks should be persisted in the attack resource file and used as a generated mask list when the attack is run.

#### Brute Force UX

See [New Brute Force Attack Editor](../notes/ui_screens/brute_force_attack_editor.md) for more details.

- [x] Checkbox UI for charset selection (`Lowercase`, `Uppercase`, `Numbers`, `Symbols`, `Space`) `task_id:attack.ux_brute_force_charset_selection`
  - Each charset maps to a mask token for the `?1` character (i.e. `?l` for lowercase, etc.). The user should be able to select one or more charsets and the selected charsets should be used to generate the mask.
- [x] Range selector for mask length (min/max) `task_id:attack.ux_brute_force_length_selector`
  - This should be a [Flowbite Range Slider](https://flowbite.com/docs/forms/range/) and it is used to set the `min_length` and `max_length` of the the incremental attack.
  - The max length is also used to set the number of `?1` tokens in the mask (see `task_id:attack.ux_brute_force_mask_generation`)
- [x] Automatically generate `?1?1?...` style mask based on selected length `task_id:attack.ux_brute_force_mask_generation`
  - The brute force attack is just a user friendly way to generate an increment attack with a mask. The mask is generated by the `?1` token which is repeated for the length of the maximum character length (defined by the `max_length` in `task_id:attack.ux_brute_force_length_selector`). The selected character types are used to set the tokens used in the custom character set 1 for the attack.
- [x] Derive `?1` charset from selected charsets (e.g., `?l?d` for lowercase + digits) `task_id:attack.ux_brute_force_charset_derivation`
  - This is determined from the character types chosen in `task_id:attack.ux_brute_force_charset_selection` and should be set as the `custom_charset_1` for the attack.

---

### Implementation Tasks

_Includes support for a full-featured attack editor with configurable mask, rule, wordlist resources; charset fields; and validation logic. Endpoints must power form-based creation, preview validation, reordering, and config visualization._

Note: See [Attack Notes](../notes/attack_notes.md) for more details on the attack editor UX and implementation.

- [x] Implement `POST /attacks/validate` for dry-run validation with error + keyspace response `task_id:attack.validate`
- [x] Validate resource linkage: masks, rules, wordlists must match attack mode and resource type (task_id: resource-linkage-validation)
- [x] Support creation via `POST /attacks/` with full config validation `task_id:attack.create_endpoint`
- [x] Return Pydantic validation error format on failed creation `task_id:attack.create_validation_error_format`
- [x] Support reordering attacks in campaigns (if UI exposes it) `task_id:attack.reorder_within_campaign`
- [x] Implement performance summary endpoint: `GET /attacks/{id}/performance` `task_id:attack.performance_summary`
  - This supports the display of a text summary of the attack's hashes per second, total hashes, and the number of agents used and estimated time to completion. See items 3 and 3b in the [Core Algorithm Implementation Guide](../core_algorithm_implementation_guide.md) for more details. This should be live updated via SSE when the attack status changes (see `task_id:attack.live_updates_json`).
- [x] Implement toggle: `POST /attacks/{id}/disable_live_updates` `task_id:attack.disable_live_updates` (now UI-only, not persisted in DB)
- [x] All views must return JSON data suitable for Svelte rendering `task_id:attack.json_data_svelte`.
- [x] All views should support SSE/Svelte auto-refresh triggers `task_id:attack.live_updates_svelte`
- SSE endpoints have been implemented on the backend to notify the client when attack status (progress, status, etc.) has changed. Frontend functionality will need to be implemented to handle the SSE events and update the UI accordingly using Svelte stores and EventSource
- [x] Add human-readable formatting for rule preview (e.g., rule explanation tooltips) `task_id:attack.rule_preview_explanation`
  - This is implemented in `task_id:attack.rule_preview_explanation` on the backend and displays a tooltip with the rule explanation when the user hovers over the rule name in the rule dropdown. See [Rule Explaination](../notes/specific_tasks/rule_explaination.md) for more details.
- [x] Implement default value suggestions (e.g., for masks, charset combos) `task_id:attack.default_config_suggestions`
  - This is implemented in `task_id:attack.default_config_suggestions` on the backend and displays a dropdown of suggested masks, charsets, and rules for the attack. See [Default Config Suggestions](../notes/specific_tasks/default_config_suggestions.md) for implementation details and specific tasks.

_All views should support Svelte SSE triggers or polling to allow dynamic refresh when agent-submitted updates occur._

- [x] `GET /api/v1/web/attacks/` - List attacks (paginated, searchable) `task_id:attack.list_paginated_searchable`
- [x] `POST /api/v1/web/attacks/` - Create attack with config validation `task_id:attack.ux_created_with_validation`
  - This supports the creation of a new attack with validation of the attack's config using pydantic validation.
- [x] `GET /api/v1/web/attacks/{id}` - View attack config and performance `task_id:attack.ux_view_config_performance`
  - This supports the display of the attack's config and performance information in a modal when the user clicks on an attack in the campaign detail view.
- [x] `PATCH /api/v1/web/attacks/{id}` - Edit attack `task_id:attack.ux_edit_attack`
  - This supports the editing of the attack's config in a modal when the user clicks on an attack in the campaign detail view.
- [x] `DELETE /api/v1/web/attacks/{id}` - Delete attack `task_id:attack.ux_delete_attack`
  - This deletes an attack from the campaign. The attack should be removed from the campaign. If the attack has not been started, it should be deleted from the database.
  - If the attack has been started, it should be marked as deleted and the attack should be stopped.
    - Any ephemeral resources should be deleted from deleted attacks, but non-ephemeral resources should be unlinked from the attack.
- [x] `POST /api/v1/web/attacks/validate` - Return validation errors or keyspace estimate (see [Core Algorithm Implementation Guide](../core_algorithm_implementation_guide.md)) `task_id:attack.validate_errors_keyspace`
- [x] `GET /api/v1/web/attacks/{id}/performance` - Return task/agent spread, processing rate, and agent participation for a given attack.
  - Used to diagnose bottlenecks or performance issues by surfacing which agents worked the task, their individual speed, and aggregate throughput.
  - Useful for verifying whether a slow campaign is due to insufficient agent coverage or unexpectedly large keyspace. `task_id:attack.performance_diagnostics`

---

## Hash List Management

Hash lists are a collection of hashes that can be used in a campaign. They are a fundemental core component of Ouroboros and are the primary way to manage hashes within a project. When a hash list is added to the system, either through the upload of a file containing hashes or through the creation of a new hash list, the hashes are stored in the database as hash items and are associated with the hash list. When a campaign is created, the hash list can be selected and the hashes in the hash list will be the focus of the attacks. When an agent requests a task, which is a subset of an attack, the agent will receive a dynamically generated download file containing the uncracked hashes from the hash list in a format that is compatible with hashcat. As the agent processes the hashes, the agent will submit the cracked hashes back to the system and the system will update the hash list with the cracked hashes. If another agent successfully cracks a hash that is part of a hash list that is being worked by another agent, all agents working on the hash list will be notified and directed to download a zap list, which contains the hashes that have been cracked since the they downloaded the hash list. The agent portion of this process is handled by the Agent API, here we will be implementing the endpoints for the user interface to manage hash lists.

Since hash lists are one of the most sensitive components of the system, they are always restricted to a specific project and are never visible to other projects. This is enforced by the system and the user interface should reflect this restriction. If an attack successfully cracks a hash that appears in multiple hash lists across different projects, the hash item in each project will be updated with the found plaintext value, but it is not revealed to the user what attack found the plaintext (unlike when a hash is cracked in a campaign that is part of the user's project). This is to avoid leaking information about password reuse across multiple projects.

### UX Design Goals

- [x] Add `POST /api/v1/web/hash_lists/` - Create a new hash list `task_id:hash_list.create`
- [x] `GET /api/v1/web/hash_lists/` - List hash lists (paginated, searchable) `task_id:hash_list.list_paginated_searchable`
- [x] `GET /api/v1/web/hash_lists/{id}/items` - List hash items in hash list `task_id:hash_list.list_items` - This should return a paginated list of hash items in the hash list and should be searchable by hash value, plaintext, and status. The status is simply cracked or uncracked, depending on whether plaintext is found or not. The list should be exportable as TSV and CSV files.
- [x] `GET /api/v1/web/hash_lists/{id}` - View hash list `task_id:hash_list.view`
- [x] `PATCH /api/v1/web/hash_lists/{id}` - Update hash list `task_id:hash_list.update`
- [x] `DELETE /api/v1/web/hash_lists/{id}` - Delete hash list `task_id:hash_list.delete`

---

#### Save/Load Schema Design

Ouroboros should allow saving and loading of both individual Attacks and entire Campaigns via a custom JSON format. This will support backup, sharing, and preconfiguration workflows.

🔐 The exported format must include:

- All editable fields of the attack or campaign, including position and comment
- For campaigns: the order of attached attacks must be preserved
- Any ephemeral word or mask lists used by an attack must be serialized as inline content
- For linked non-ephemeral resources (wordlists, masks, rules), include their stable UUID (`guid`) for re-linking

🚫 The exported format must **not** include:

- Project ID or User ID bindings
- Internal database primary keys

📥 On import:

- The backend must validate schema correctness
- Rehydrate ephemeral resources directly
- Look up non-ephemeral resources by GUID (`guid`)
- Prompt the user or fail gracefully if a GUID reference does not resolve

This schema should be versioned and tested against a validation spec.

A new `guid: UUID` field must be added to the `AttackResourceFile` model to support this. It should be unique, stable across sessions, and used as the canonical identifier for serialization workflows. The GUID should be generated using `uuid4()` at the time the resource is first created, and must remain immutable and internal-only (not exposed to Agent APIs).

If a resource referenced by GUID cannot be matched during import (either due to deletion or lack of permission), the user must be prompted with three fallback options:

1. **Select a Replacement** - Choose a compatible resource of the same `resource_type` from a dropdown
2. **Skip Affected Attack** - Import the rest of the campaign, omitting attacks missing required resources
3. **Abort Import** - Cancel the import entirely

All fallback logic should be implemented server-side with support for frontend prompting. to support this. It should be unique, stable across sessions, and used as the canonical identifier for serialization workflows. of both individual Attacks and entire Campaigns via a custom JSON format. This will support backup, sharing, and preconfiguration workflows.

🔐 The exported format must include:

- All editable fields of the attack or campaign, including position and comment
- For campaigns: the order of attached attacks must be preserved
- Any ephemeral word or mask lists used by an attack must be serialized as inline content

🚫 The exported format must **not** include:

- Project ID or User ID bindings
- Hash list references (campaigns must be re-linked to a hash list upon import)
- Internal database IDs

📥 On import:

- The backend must validate schema correctness
- Attachments to new or existing campaigns must be confirmed explicitly
- Inline ephemeral resources must be rehydrated as temporary DB records

This schema should be versioned and tested against a validation spec.

---

#### Ephemeral Resources

Attacks can support ephemeral resources that can be created and edited within the attack editor. These resources are still persisted to the database, but they are stored as part of an AttackResourceFile record as a JSON structure, and are not visible in the Resource Browser or available for reuse in other attacks. They are deleted when the attack is deleted, they do not have a backing file in S3, and they are exported inline if the attack is exported within the same JSON file. The Agent API will provide a non-signed URL to agents to access these resources when the attack is running and they are downloaded directly from Ouroboros, rather than the MinIO service.

---

#### 🧩 Extended Implementation Tasks

These tasks expand the attack editing interface and logic to support contextual UIs, one-off resources, and user-friendly modifiers without exposing raw hashcat details.

- [x] Implement `POST /api/v1/web/attacks/estimate` to return keyspace + complexity score for unsaved attack input `task_id:attack.estimate_unpersisted` (see [Phase 2 Implementation Tasks](../phase-2-api-implementation-tasks.md#hash-guessing-logic))
- [x] Add edit-protection logic to warn if attack is `running` or `completed` before allowing edit (Web UI API) `task_id:attack.edit_protect`
- [x] Support ephemeral inline wordlists (multiple `add word` fields) stored in memory or DB during attack creation, deleted when the attack is deleted. (Web UI API) `task_id:attack.ephemeral_wordlist`
- [x] Support ephemeral inline masks (`add mask` line interface) with same lifecycle behavior `task_id:attack.ephemeral_masklist` (see section [Ephemeral Resources](#ephemeral-resources) above)
- [x] `task_id:attack.modifier_ui_to_rules` Implement "Modifiers" UI: Map UI modifier buttons to rule file UUIDs for dictionary attacks (see `notes/ui_screens/new_dictionary_attack_editor.md`, `attack.md`). Ensure the mapping is robust, testable, and extensible. Add tests for all supported modifiers.
- [x] Dictionary attack UI must support: min/max length, searchable wordlist dropdown (sorted by last modified), option to use dynamic wordlist from previous project cracks `task_id:attack.dictionary_ui_controls`
  - See [Dictionary Attack UX](../notes/ui_screens/new_dictionary_attack_editor.md) for more details.
- [x] Brute force UI must allow checkbox-driven charset selection, range selector, and generate corresponding `?1?1?...` style masks and `?1` custom charset `task_id:attack.brute_force_ui_logic` (strong typing enforced)
- [x] Add support to export any single Attack or entire Campaign to a JSON file `task_id:attack.export_json`
- [x] Add support to load campaign or attack JSON file and prefill the editor `task_id:attack.import_json_schema`
  - See [Save/Load Schema Design](../notes/specific_tasks/save_load_schema_design.md) for more details.

The attack editor must support a modal-based, multi-form interface with per-attack-type customization. It should dynamically update keyspace estimates and complexity scores as the user changes input.

- ⚙️ The editor must show real-time keyspace and complexity values, even for non-persisted attacks. Backend support is needed for live estimation.
- ⚠️ Editing an attack that is already running or exhausted must trigger a confirmation prompt and reset the state if confirmed. This restarts the attack lifecycle.
- ✍️ User-facing options should be simplified (e.g. "+ Change Case") and map to hashcat rule resources internally.
- 🔁 Certain attack types (e.g., dictionary, brute force) must support one-off word/mask lists that are ephemeral and attack-local.

---

### Agent Management

For additional notes on the agent management, see [Agent Notes](../notes/agent_notes.md).

#### 🧩 UX Design Goals

##### 🖥️ Agent List View

- Everyone can see all agents and their state

- Admin-only gear menu (Disable Agent / View Details)

- Columns:

  - Agent Name + OS
  - Status
  - Temp (°C) and Utilization (avg of enabled devices)
  - Current and Average Attempts/sec
  - Current Job (Project, Campaign, Attack)

##### ➕ Agent Registration

- Modal to enter label and select Projects (multi-toggle)

  - Upon creating a new agent, the UI must immediately display the generated token for copy/paste. Tokens are only shown once.

- Upon save, display generated token to admin

##### ⚙️ Agent Detail Tabs

###### 🔧 Settings

- `display_name = agent.custom_label or agent.host_name`
- Toggle: Enabled/Disabled
- Agent Update Interval (sec, default randomized 1-15)
- Toggle: Use Native Hashcat (sets `AdvancedAgentConfiguration.use_native_hashcat = true`)
- Toggle: Enable Additional Hash Types (`--benchmark-all`)
- List: Project assignment toggles
- Static: OS, IP, Signature, Token

###### 🖥️ Hardware

- List of backend devices from `--backend-info`

- Toggle each device on/off → updates `backend_device`

- Device toggling prompts: Apply now / Next Task / Cancel if task is running

- Show gray placeholder if no devices reported yet

- HW Settings:

  - `--hwmon-temp-abort` (note only, default to 90°C)

    - Note: This field is not yet supported by the v1 Agent API, but could be added safely to `AdvancedAgentConfiguration` as an optional key. The agent will ignore unknown fields.

  - OpenCL Device Type selector (`opencl_devices`)

- Backend toggles: CUDA, HIP, Metal, OpenCL → affect `--backend-ignore-*`

###### 📈 Performance

- Line chart of `DeviceStatus.guess_rate` over time (8hr window)
- Donut chart per device within card: Utilization as a percentage (or N/A)
- Live updating via SSE

###### 🪵 Log

- Timeline of `AgentError` entries
- Color-coded severity
- Fields: message, code, task link, details

###### 🧠 Capabilities

- Pulls from `HashcatBenchmark`
- Table (rollup view): Toggle / Hash ID / Name / Speed / Category
- Expandable rows per device
- Filterable + searchable
- Caption with benchmark timestamp
- Header button to trigger benchmark (sets `agent.state = pending`)

---

#### 🧩 Implementation Tasks

- [x] `GET /api/v1/web/agents/` - List/filter agents `task_id:agent.list_filter`
  - This will display a paginated, filterable datatable of all agents, with search and state filter. Used for the main agent management view. `task_id:agent.list_filter`
- [x] `GET /api/v1/web/agents/{id}` - Detail view `task_id:agent.detail_view`
  - This will display a detailed view of the agent as described in the [Agent Detail Tabs](../notes/ui_screens/agent_detail_tabs.md) section.
- [x] `PATCH /api/v1/web/agents/{id}` - Toggle enable/disable `task_id:agent.toggle_state`
  - This will be a toggle in the list of agents that changes the agent's `enabled` state and prevents the agent from picking up new tasks.
- [x] `GET /api/v1/web/agents/{id}/benchmarks` - View benchmark summary `task_id:agent.benchmark_summary`
  - This will display a summary of the agent's benchmark results as described in the [Agent Detail Tabs](../notes/ui_screens/agent_detail_tabs.md) section. See also [Agent Benchmark Compatibility](../core_algorithm_implementation_guide.md#agent-benchmark-compatibility) for more details.
- [x] `POST /api/v1/web/agents/{id}/test_presigned` - Validate URL access `task_id:agent.presigned_url_test`
  - This will validate the presigned URL for the agent. It should take a `url` as a parameter and return a boolean value indicating whether the URL is valid. See [Phase 2b: Resource Management](../phase-2b-resource-management.md) for more details. See [Presigned URL Test](../notes/specific_tasks/presigned_url_test.md) for more details.
- [x] `PATCH /api/v1/web/agents/{id}/config` - Update `AdvancedAgentConfiguration` toggles (backend_ignore, opencl, etc.) `task_id:agent.config_update`
- [x] `PATCH /api/v1/web/agents/{id}/devices` - Toggle individual backend devices (stored as stringified int list) `task_id:agent.device_toggle`
  - This will toggle the individual backend devices for the agent. It should take a `devices` as a parameter and update the `backend_device` for the agent.
  - The backend devices are stored in Ouroboros on the Agent model as `list[str]` of their descriptive names in `Agent.devices` and the actual setting of what should be enabled is a comma-seperated list of integers, 1-indexed, so it'll be a little weird to figure out. We'll probably need a better way to do this in the future, but this is a limitation of v1 of the Agent API. See [Hardware](../notes/ui_screens/agent_detail_tabs.md#hardware) above for more details.
- [x] `POST /api/v1/web/agents/{id}/benchmark` - Trigger new benchmark run (set to `pending`) `task_id:agent.benchmark_trigger`
  - This changes the agent's state to `pending`, which causes the agent to run a benchmark. See [Agent Benchmark Compatibility](../core_algorithm_implementation_guide.md#agent-benchmark-compatibility) for more details.
- [x] `GET /api/v1/web/agents/{id}/errors` - Fetch structured log stream `task_id:agent.log_stream`
  - This will fetch the structured log stream for the agent. It should return a list of `AgentError` entries as described in the Logs section of the [Agent Detail Tabs](../notes/ui_screens/agent_detail_tabs.md) above. The log stream should be updated in real-time as new errors are reported and should use a human-readable visual style, color-coding, etc.
- [x] `GET /api/v1/web/agents/{id}/performance` - Stream guesses/sec time series for agent devices as Pydantic models (`task_id:agent.web_agents_performance_data`)
  - This will stream the guesses/sec time series for the agent. It should return a list of `DeviceStatus` entries as described in the [Agent Detail Tabs](../notes/ui_screens/agent_detail_tabs.md) section.
  - This will be used to populate Flowbite Charts using the [ApexCharts library](https://flowbite.com/docs/plugins/charts/). See [Agent Performance Graph](../notes/ui_screens/agent_detail_tabs.md#performance) above for more details.
- [x] Generate time series storage and reduction service for the AgentDevicePerformance model, including:
  - SQLAlchemy model for time series device performance
  - Service for storing and reducing time series data (bucketed averages)
  - Integration with agent performance data endpoint
  - Tests for time series storage and reduction
  - `task_id:agent.agent_device_performance_timeseries`
- [x] Refactor the endpoint created in `task_id:agent.web_agents_performance_data` to use the times series data generated in `task_id:agent.agent_device_performance_timeseries` `task_id:agent.refactor_performance_endpoint`
- [x] Add a call to `record_agent_device_performance` in `app/core/services/agent_service.py` from `submit_task_status_service` in `app/api/v1/endpoints/agent/tasks.py` `task_id:agent.add_timeseries_call` - This will record the agent device performance timeseries data when a task status is submitted.
- [x] `POST /api/v1/web/agents` - Register new agent + return token `task_id:agent.create`
  - This will register a new agent and return a token for the agent. See [Agent Registration](../notes/ui_screens/agent_registration.md) above for more details.
- [x] `GET /api/v1/web/agents/{id}/hardware` - Report backend devices, temp limits, platform support flags `task_id:agent.hardware_detail`
  - This will report the backend devices, temp limits, and platform support flags for the agent. See [Hardware](../notes/ui_screens/agent_detail_tabs.md#hardware) above for more details.
- [x] `PATCH /api/v1/web/agents/{id}/hardware` - Update hardware limits + platform toggles `task_id:agent.hardware_update`
  - This will update the hardware limits and platform toggles for the agent. See [Hardware](../notes/ui_screens/agent_detail_tabs.md#hardware) above for more details.
- [x] `GET /api/v1/web/agents/{id}/capabilities` - Show benchmark results (table + graph) `task_id:agent.capabilities_table` - This will show the benchmark results for the agent. See [Agent Capabilities](../notes/ui_screens/agent_detail_tabs.md#capabilities) above for more details. See also [Agent Benchmark Compatibility](../core_algorithm_implementation_guide.md#agent-benchmark-compatibility) for more details.

_Includes real-time updating views, hardware configuration toggles, performance monitoring, and error visibility. Most endpoints should use JSON requests and SSE triggers to refresh data without full page reloads._ should be supported on list and detail views for dynamic agent status refresh.\*

- [x] `GET /api/v1/web/agents/` - List/filter agents `task_id:agent.list_filter`
  - This will display a paginated, filterable datatable of all agents, with search and state filter. Used for the main agent management view. `task_id:agent.list_filter`
- [x] `GET /api/v1/web/agents/{id}` - Detail view `task_id:agent.detail_view`
  - This will display a detailed view of the agent as described in the [Agent Detail Tabs](../notes/ui_screens/agent_detail_tabs.md) section.
- [x] `PATCH /api/v1/web/agents/{id}` - Toggle enable/disable `task_id:agent.toggle_state`
  - This will be a toggle in the list of agents that changes the agent's `enabled` state and prevents the agent from picking up new tasks.
- [x] `POST /api/v1/web/agents/{id}/requeue` - Requeue failed task `task_id:agent.manual_requeue`
- [x] `GET /api/v1/web/agents/{id}/benchmarks` - View benchmark summary `task_id:agent.benchmark_summary`
  - This will display a summary of the agent's benchmark results as described in the [Agent Detail Tabs](../notes/ui_screens/agent_detail_tabs.md) section. See also [Agent Benchmark Compatibility](../core_algorithm_implementation_guide.md#agent-benchmark-compatibility) for more details.
- [x] `POST /api/v1/web/agents/{id}/test_presigned` - Validate URL access `task_id:agent.presigned_url_test`

---

### Resource Browser

Ouroboros uses `AttackResourceFile` objects to represent reusable cracking resources such as mask lists, wordlists, rule files, and custom charsets. All uploads go through the Ouroboros backend, which creates the database record and issues a presigned S3 upload URL. No object in storage should exist without a matching DB entry. Each file includes a declared `resource_type` that drives editor behavior, validation rules, and allowed usage in attacks.

Line-oriented resources (masks, rules, small wordlists) may be edited interactively in the Web UI. Each line is validated individually and exposed via a dedicated endpoint. Larger files must be downloaded, edited offline, and reuploaded.

#### 🧩 Implementation Tasks

- [x] Implement `AttackResourceFile.resource_type` with enum (`mask_list`, `rule_list`, etc.) `task_id:resource.define_enum`

- [x] Store and expose `line_format`, `line_encoding`, `used_for_modes`, `source` `task_id:resource.augment_metadata`

- [x] Expose line-count and byte-size metadata for edit gating `task_id:resource.expose_editability_metrics`

- [x] Validate allowed attack usage based on resource type `task_id:resource.enforce_attack_mode_constraints`

- [x] Reject in-browser editing of resources over configured size/line threshold (configurable) `task_id:resource.edit_limit_check`

  - Add `RESOURCE_EDIT_MAX_SIZE_MB` and `RESOURCE_EDIT_MAX_LINES` settings to `config.py`

- [x] Create line-editing endpoints: `task_id:resource.line_api_endpoints`

  - This will create the line-editing endpoints for the resource. It should be a set of endpoints that allow the user to add, edit, and delete lines in the resource. This is different than the ephemeral attack resources, which are for very small resources that are used directly in attacks. This is an in-editor experience for editing larger, previously uploaded attack resource files. See [Line-Oriented Editing](../notes/ui_screens/new_dictionary_attack_editor.md#line-oriented-editing) for more details.
  - [x] `GET /resources/{id}/lines` - This will return a list of lines in the resource. It should be a paginated list of `ResourceLine` objects as described in the [Resource Line Editing](../notes/ui_screens/new_dictionary_attack_editor.md#line-oriented-editing) section.
  - [x] `POST /resources/{id}/lines` - This will add a new line to the resource. It should take a `line` as a parameter and add it to the resource.
  - [x] `PATCH /resources/{id}/lines/{line_id}` - This will update an existing line in the resource. It should take a `line_id` and a `line` as parameters and update the line in the resource.
  - [x] `DELETE /resources/{id}/lines/{line_id}` - This will delete an existing line in the resource. It should take a `line_id` as a parameter and delete the line from the resource.

- [x] Add model: `ResourceLineValidationError` `task_id:resource.line_validation_model`

  - This will be a model that is used to validate the lines in the resource. It should be a Pydantic model that validates the lines in the resource. It should be a list of `ResourceLineValidationError` objects conforming to idomatic Pydantic validation error response.

- [x] Validate line syntax per type (`mask_list`, `rule_list`) and return structured JSON `task_id:resource.validate_line_content`

  - This will validate the lines in the resource. It should be a list of `ResourceLineValidationError` objects conforming to idomatic Pydantic validation error response. It should us the same validation functionality as the attack editor line validation using for ephemeral attack resources.

- [x] Return `204 No Content` on valid edits, `422` JSON otherwise `task_id:resource.line_edit_response`

- [x] Disable editing for `dynamic_word_list` and oversize files `task_id:resource.edit_restrictions`

  - This will disable editing for `dynamic_word_list` and oversize files. It should be a boolean flag that is used to determine if the resource can be edited.

- [x] Support inline preview and batch validation (`?validate=true`) `task_id:resource.line_preview_mode`

- [x] Ensure file uploads always create an `AttackResourceFile` (via presign + DB insert) `task_id:resource.upload_contract_enforcement`

  - This will ensure that file uploads always create an `AttackResourceFile` (via presign + DB insert). If the upload fails, it should raise an error and not create the database entry. The `content` field is not used in regular file uploads, but is used for the ephemeral attack resources.

- [x] Implement orphan file audit to catch mislinked objects `task_id:resource.orphan_audit`

- [x] Detect `resource_type` from user input during upload `task_id:resource.detect_type_on_upload`

  - This will detect the `resource_type` from user input during upload. It should be a string that is used to determine the `resource_type` of the resource.

- [x] Store resource metadata in `AttackResourceFile` for frontend use `task_id:resource.persist_frontend_metadata`

  - This will store the resource metadata in `AttackResourceFile` for frontend use. It should include the `resource_type`, `line_count`, `byte_size`, and `source`, as well as the `used_for_modes`, `line_encoding` and which projects the resource is linked to or if it is unrestricted.

🧠 Attack resource files share a common storage and metadata model, but differ significantly in validation, UI affordances, and where they are used within attacks. To support this diversity while enabling structured handling, each resource must declare a `resource_type`, which drives editor behavior, validation rules, and attack compatibility.

Supported `resource_type` values:

```python
class AttackResourceType(str, enum.Enum):
    MASK_LIST = "mask_list"
    RULE_LIST = "rule_list"
    WORD_LIST = "word_list"
    CHARSET = "charset"
    DYNAMIC_WORD_LIST = "dynamic_word_list"  # Read-only, derived from cracked hashes
```

Each `AttackResourceFile` (defined in `app/models/attack_resource_file.py`) should include:

```python
resource_type: AttackResourceType
used_for_modes: list[AttackMode]  # Enforced compatibility with hashcat attack modes
line_encoding: Literal["ascii", "utf-8"]  # Affects validation + editor behavior
line_format: Literal["freeform", "mask", "rule", "charset"]
source: Literal["upload", "generated", "linked"]
```

Editor behavior must respect the declared type:

| **Resource TypeEditable?Line FormatEncodingNotes** |      |              |       |                                           |
| -------------------------------------------------- | ---- | ------------ | ----- | ----------------------------------------- |
| `mask_list`                                        | ✅   | mask syntax  | ASCII | one per line, validated mask syntax       |
| `rule_list`                                        | ✅   | rule grammar | ASCII | strict per-line validation                |
| `word_list`                                        | ✅\* | freeform     | UTF-8 | loose rules, allow unicode, strip control |
| `charset`                                          | ✅   | charset def  | ASCII | e.g. `custom1 = abc123`, used in attacks  |
| `dynamic_word_list`                                | ❌   | N/A          | UTF-8 | read-only, generated from cracked hashes  |

(\*) Editing of large word lists may be disabled based on configured size thresholds.

Uploads must be initiated via Ouroboros, which controls both presigned S3 access and DB row creation. No orphaned files should exist. The backend remains source of truth for metadata, content type, and validation enforcement.

🚨 Validation errors for resource line editing should follow FastAPI + Pydantic idioms. Use `HTTPException(status_code=422, detail=...)` for top-level form errors, and structured `ValidationError` objects for per-line issues:

Example response for per-line validation:

Suggested reusable model:

```python
class ResourceLineValidationError(BaseModel):
    line_index: int
    content: str
    valid: bool = False
    message: str
```

```json
{
  "errors": [
    {
      "line_index": 3,
      "content": "+rfoo",
      "valid": false,
      "message": "Unknown rule operator 'f'"
    },
    {
      "line_index": 7,
      "content": "?u?d?l?l",
      "valid": false,
      "message": "Duplicate character class at position 3"
    }
  ]
}
```

This should be returned from:

- `GET /resources/{id}/lines?validate=true`
- `PATCH /resources/{id}/lines/{line_id}` if content is invalid

For valid input, return `204 No Content` or the updated data, which controls both presign + DB insert. No orphaned files should exist. The backend remains source of truth for metadata, content type, and validation enforcement.

🔒 All uploaded resource files must originate from the Ouroboros backend, which controls presigned upload URLs and creates the corresponding database entry in `AttackResourceFile` (defined in `app.models.attack_resource_file`). There should never be a case where a file exists in the object store without a corresponding DB row. The S3-compatible backend is used strictly for offloading large file transfer workloads (uploads/downloads by UI and agents), not as an authoritative metadata source.

💡 The UI should detect resource type and size to determine whether inline editing or full download is allowed. The backend should expose content metadata to guide this decision, such as `line_count`, `byte_size`, and `resource_type`. The frontend may display masks, rules, and short wordlists with line-level controls; long wordlists or binary-formatted resources must fall back to download/reupload workflows.

_Includes support for uploading, viewing, linking, and editing attack resources (mask lists, word lists, rule lists, and custom charsets). Resources are stored in an S3-compatible object store (typically MinIO), but Ouroboros must track metadata, linkage, and validation. Users should be able to inspect and edit resource content directly in the browser via web-based interactions._

🔐 Direct editing is permitted only for resources under a safe size threshold (e.g., < 5,000 lines or < 1MB). Larger files must be downloaded, edited offline, and reuploaded. This threshold should be configurable via an environment variable or application setting (e.g., `RESOURCE_EDIT_MAX_SIZE_MB`, `RESOURCE_EDIT_MAX_LINES`) to allow for deployment-specific tuning.

---

### Line-Oriented Editing

For eligible resource types (e.g., masks, rules, short wordlists), the Web UI should support a line-oriented editor mode:

- Each line can be edited, removed, or validated individually.
- Validation logic should be performed per line to ensure syntax correctness (e.g., valid mask syntax, hashcat rule grammar).
- Inline editing should be driven via client-side javascript using AJAX requests to the backend.

Suggested line-editing endpoints:

- [x] `GET /api/v1/web/resources/{id}/lines` - Paginated and optionally validated list of individual lines `task_id:resource.line_api_endpoints`
- [x] `POST /api/v1/web/resources/{id}/lines` - Add a new line `task_id:resource.add_line`
- [x] `PATCH /api/v1/web/resources/{id}/lines/{line_id}` - Modify an existing line `task_id:resource.update_line`
- [x] `DELETE /api/v1/web/resources/{id}/lines/{line_id}` - Remove a line `task_id:resource.delete_line`

The backend should expose a virtual `ResourceLine` model:

```python
class ResourceLine(BaseModel):
    id: int
    index: int
    content: str
    valid: bool
    error_message: Optional[str]
```

These may be backed by temporary parsed representations for S3-stored resources, cached in memory or a staging DB table for edit sessions.

_Includes support for uploading, viewing, linking, and editing attack resources (mask lists, word lists, rule lists, and custom charsets). Resources are stored in an S3-compatible object store (typically MinIO), but Ouroboros must track metadata, linkage, and validation. Users should be able to inspect and edit resource content directly in the browser via HTMX-supported interactions._

🔐 Direct editing is permitted only for resources under a safe size threshold (e.g., < 5,000 lines or < 1MB). Larger files must be downloaded, edited offline, and reuploaded. This threshold should be configurable via an environment variable or application setting (e.g., `RESOURCE_EDIT_MAX_SIZE_MB`, `RESOURCE_EDIT_MAX_LINES`) to allow for deployment-specific tuning.

- [x] `GET /api/v1/web/resources/` - Combined list of all resources (filterable by type) `task_id:resource.list_all`
- [x] `GET /api/v1/web/resources/{id}` - Metadata + linking `task_id:resource.get_by_id`
- [x] `GET /api/v1/web/resources/{id}/preview` - Small content preview `task_id:resource.preview`
- [x] `GET /api/v1/web/resources/upload` - Render form to upload new resource `task_id:resource.upload_form`
- [x] `POST /api/v1/web/resources/` - Upload metadata, request presigned upload URL `task_id:resource.upload_metadata`
- [x] `PATCH /api/v1/web/resources/{id}` (`task_id: web-resources-patch`)
- [x] `GET /api/v1/web/resources/{id}/edit` - View/edit metadata (name, tags, visibility) `task_id:resource.edit_metadata`
- [x] `PATCH /api/v1/web/resources/{id}` - Update metadata `task_id:resource.update_metadata`
- [x] `DELETE /api/v1/web/resources/{id}` - Remove or disable resource `task_id:resource.delete` - If the resource is linked to an attack, return a 409 Conflict error, otherwise it should be a hard delete by deleting the resource from the database and the object store. Both should be done in a way that is atomic and does not leave the system in an inconsistent state. Both scenarios should be covered by integration tests.
- [x] `GET /api/v1/web/resources/{id}/content` - Get raw editable text content (masks, rules, wordlists) `task_id:resource.get_content`
- [x] `PATCH /api/v1/web/resources/{id}/content` - Save updated content (inline edit) `task_id:resource.update_content` - This should be a PATCH request that updates the content of the resource. It should apply to file-backed resources only, as there are already other endpoints for ephemeral resources. It should not allow editing of resources larger than the configured size threshold and it should trigger a restart of any attacks, running or completed, that are using the resource.
- [x] `POST /api/v1/web/resources/{id}/refresh_metadata` - Recalculate hash, size, and linkage from updated file `task_id:resource.refresh_metadata` - This should be a POST request that recalculates the hash, size, and linkage from the updated file. It should be a soft refresh, meaning it should not trigger a restart of any attacks, running or completed, that are using the resource.

---

## UX Support and Utility

### Purpose

This section defines endpoints used by the frontend to dynamically populate UI elements, fetch partials, and support dropdowns, summaries, and metadata helpers that don't belong to a specific resource type.

### Implementation Tasks

- [x] `GET /api/v1/web/modals/agents` - Populate agent dropdowns `task_id:ux.populate_agents`

  - This should return a list of agents with their name and status, based on the `Agent` model. - Any authenticated user should be able to see all agents.

- [x] `GET /api/v1/web/modals/resources` - Populate resource selectors (mask, wordlist, rule) `task_id:ux.populate_resources`

  - This should return a list of resources with their name, and type, based on the `AttackResourceFile` model. It does not show dynamic wordlists or ephemeral resources and only shows resources that are linked to the current project (based on the Project context created in `task_id:auth.get_context`) or are unrestricted, unless the user is an admin. Should allow for filtering by resource type and name, sorted by most recently modified.

- [x] `GET /api/v1/web/modals/hash_types` - Populate hash type dropdowns `task_id:ux.populate_hash_types`

  - This should return a list of hash types with their name and numeric mode, based on the `HashMode` model. It should be filterable by name and mode and return a nullable confidence score for the guess service if the guess service was involved in populating the dropdown (to support the hash type override UI in task `task_id:guess.hash_type_override_ui`). Sort by confidence score descending (unless it is None), then by mode ascending.

- [x] `GET /api/v1/web/dashboard/summary` - Return campaign/task summary data as a Pydantic model containing aggregated data the various dashboard widgets `task_id:ux.summary_dashboard` - see `docs/v2_rewrite_implementation_plan/notes/ui_screens/dashboard-ux.md` for the expected structure and widgets - See `docs/v2_rewrite_implementation_plan/notes/ui_screens/dashboard-ux.md` for the complete description of the dashboard and the widgets that should be supported.

- [x] `GET /api/v1/web/health/overview` - System health snapshot (agents online, DB latency, task backlog) `task_id:ux.system_health_overview` - This is more focused on the functionality of the system than the components and should be a overview of the number of agents online, the number of campaigns, tasks, and hash lists, as well as their current status and performance metrics and any errors that have occurred with any of the various agents, campaigns, tasks, and hash lists. See `docs/v2_rewrite_implementation_plan/notes/ui_screens/health_status_screen.md` for the complete description of the health status screen and the components that should be supported.

- [x] `GET /api/v1/web/health/components` - Detailed health of core services (MinIO, Redis, DB) `task_id:ux.system_health_components`

  - This should include the detailed health of the MinIO, Redis, and DB services and their status, including latency and errors. See [Health Status Screen Notes](docs/v2_rewrite_implementation_plan/notes/ui_screens/health_status_screen.md) for the complete description of the health status screen and the components that should be supported.

- [x] Implement basic [cashews](https://github.com/Krukov/cashews) cache for the health overview and components `task_id:ux.system_health_cache` - This should be configured using the cashews cache decorator and should be configured to cache the health overview and components for 60 seconds. The cache should support memory and redis backends, with the memory backend being the default. It should be configured in `app/core/config.py` as `settings.CACHE_CONNECT_STRING`, defaulting to `mem://?check_interval=10&size=10000`, and the connection string should be passed to `cache.setup` in `app/main.py`. Caching should be disabled in tests.

- [x] `GET /api/v1/web/modals/rule_explanation` - Return rule explanation data `task_id:ux.rule_explanation_modal`

  - This should return data to populate a rule explanation modal, which is a modal that explains the rule syntax for the selected rule. It should be a modal that is triggered by a button in the UI. - See `docs/v2_rewrite_implementation_plan/notes/specific_tasks/rule_explaination.md`

---

### Crackable Uploads

To streamline the cracking workflow for non-technical users, we should support uploading raw data (files or hash datas) and automating the detection, validation, and campaign creation process. The system must distinguish between:

- **File uploads** (e.g., `.zip`, `.docx`, `.pdf`, `.kdbx`) that require binary hash extraction
- **Pasted or raw hash text** (e.g., lines from `/etc/shadow`, `impacket`'s `secretsdump`, Cisco config dumps)

In the case of pasted hashes, the system should automatically isolate the actual hash portion, remove surrounding metadata, and sanitize formatting issues. This includes stripping login expiration flags from shadow lines or extracting just the hash field from NTLM pairs.

**Use cases include:**

- Uploading a file (e.g., `.zip`, `.pdf`, `.docx`) to extract hashes
- Pasting a hash from a source like `/etc/shadow`, even if it includes surrounding shadow metadata

This process should:

- Extract or isolate the hash automatically

- Perform validation on the extracted hash (type, syntax, format)

- Prevent campaign creation if the hash is malformed or would fail in hashcat

- Detect the hash type

- Validate hashcat compatibility

- Provide preview/feedback of what will be created

- Automatically create:

  - A `HashList`
  - A `Campaign`
  - One or more preconfigured `Attacks`

Users can then launch the campaign immediately or review/edit first.

#### Implementation Tasks

- [x] Complete all tasks in ``` docs/v2_rewrite_implementation_plan/side_quests/crackable_uploads_plan.md``task_id:upload.crackable_uploads_side_quest ```
- [x] Implement `GET /api/v1/web/hash/guess` endpoint for live hash validation and guessing via service layer `task_id:guess.web_endpoint`
  - Fully implemented with a backend service later in `app/core/services/hash_guess_service.py` that can be reused for this task.
- [x] Ensure Crackable Upload UI (implemented in `frontend/`) uses guess response to validate pasted hashes before campaign creation `task_id:guess.integrate_into_crackable_uploads`
- [x] Add hash type selection UI (implementedin `frontend/`) allowing user to confirm or override guess results - should be a dropdown with the hash types and a button to confirm the guess with the dropdown populated from the modals endpoints, but prefiltered to only include the hash types identified by the guess service. Display `name-that-hash` results with confidence scores and let user manually adjust if needed `task_id:upload.hash_type_override_ui`
- [x] Automatically generate dictionary attack with an emphemeral wordlist derived from the uploaded content when usernames or prior passwords are available from the uploaded content. Useful for NTLM pairs, `/etc/shadow`, or cracked zip headers `task_id:upload.create_dynamic_wordlist`
- [x] Add confirmation/preview screen before launching a generated campaign to the crackable upload UI (implemented in `frontend/`). Shows detected hash type, parsed sample lines, and proposed attacks/resources `task_id:upload.preview_summary_ui` - (check `docs/v2_rewrite_implementation_plan/notes/user_flows_notes.md` and `docs/v2_rewrite_implementation_plan/side_quests/salvage_templates.md` for the expected structure and UI)
- [x] `POST /api/v1/web/uploads/` - Upload file or pasted hash blob `task_id:upload.upload_file_or_hash` - Nearly all of the wiring for this should have been completed as part of the crackable uploads side quest `task_id:upload.crackable_uploads_side_quest` and will just need to be verified and wired up to the endpoints for the UI. A new uploaded resource file type will need to be created to store in the database for the duration of processing the upload into a hash list and campaign. If uploaded as a file, the endpoint should accept a file upload and return a presigned URL for the file to be uploaded to S3. If uploaded as a hash blob, the endpoint should accept a text blob and store it in the database as a temporary resource. The endpoint should return a 201 Created response with the ID of the uploaded resource file, along with an upload task ID that can be used to view the new upload processing progress in the UI. The campaign and associated hash list will need to be marked as unavailable until the upload and background processing tasks are fully complete, so that it can be reflected in the UI.
- [x] `GET /api/v1/web/uploads/{id}/status` - Show analysis result: hash type, extracted preview, validation state `task_id:upload.show_analysis_result` - This should return the status of the upload task, including the hash type, extracted preview, and validation state. It should also return the ID of the uploaded resource file, along with an upload task ID that can be used to view the new upload processing progress in the UI. Status information and task completion information should be returned for each step of the upload and processing process to reflect the current state in the UI. Ensure UI pages are wired up to the endpoints, the endpoints are mocked in the playwright tests, and the UI follows idiomatic Shadcn-Svelte and bits-ui components.
- [x] `POST /api/v1/web/uploads/{id}/launch_campaign` - Generate resources and create campaign with default attacks `task_id:upload.launch_campaign`
- [x] `GET /api/v1/web/uploads/{id}/errors` - Show extraction errors or unsupported file type warnings `task_id:upload.show_extraction_errors`
- [x] `DELETE /api/v1/web/uploads/{id}` - Remove discarded or invalid upload `task_id:upload.delete_upload`

---

### Live Event Feeds (Server-Sent Events)

These endpoints provide Server-Sent Events (SSE) streams that Svelte components can subscribe to for real-time **trigger notifications**, prompting the client to issue targeted `fetch` requests. No data is pushed directly via SSE streams - only lightweight notification signals (e.g., `{ "trigger": "refresh" }`) to inform the client that updated content is available.

SSE is preferred over WebSockets for this use case because:

- **Simpler architecture**: No Redis dependency or complex pub/sub infrastructure
- **Better reliability**: Browser handles reconnection automatically
- **Easier testing**: No external dependencies or connection management
- **HTTP-based**: Works through proxies and firewalls
- **Perfect fit**: One-way notifications are exactly what SSE is designed for

#### Core Infrastructure

- ✅ FastAPI `StreamingResponse` for SSE endpoints
- ✅ In-memory event broadcasting (no Redis required)
- ✅ JavaScript `EventSource` client-side support
- ✅ JWT-based auth and project scoping

#### Event Triggers by Feed

- `campaigns`: On `Attack`, `Task`, or `Campaign` state change; `CrackResult` submission.
- `agents`: On agent heartbeat, performance update, or error report.
- `toasts`: On new `CrackResult`; displayed via UI toast notification.

---

### Implementation Tasks (SSE Event System)

#### Core Event Infrastructure

- [x] Create event broadcasting service (`app/core/services/event_service.py`) `task_id:sse.event_service`
  - [x] Implement in-memory event broadcaster with topic-based subscriptions `task_id:sse.memory_broadcaster`
  - [x] Add event listener registration/deregistration `task_id:sse.listener_management`
  - [x] Support project-scoped event filtering `task_id:sse.project_scoping`

#### SSE Endpoint Routes

Each route provides an SSE stream for specific event types:

- [x] `GET /api/v1/web/live/campaigns` - Campaign/attack/task state changes `task_id:sse.campaign_feed`
- [x] `GET /api/v1/web/live/agents` - Agent status, performance, and error updates `task_id:sse.agent_feed`
- [x] `GET /api/v1/web/live/toasts` - New crack results and system notifications `task_id:sse.toast_feed`

#### Event Broadcasting Integration

- [x] Create service-layer event triggers `task_id:sse.service_triggers`
  - [x] Trigger campaign events on `Attack`, `Task`, `Campaign` updates `task_id:sse.campaign_triggers`
  - [x] Trigger agent events on `Agent`, `DeviceStatus`, `AgentError` changes `task_id:sse.agent_triggers`
  - [x] Trigger toast events on `CrackResult` submission `task_id:sse.toast_triggers`

#### Authorization & Security

- [x] Enforce JWT authentication on SSE connections `task_id:sse.jwt_auth`
- [x] Implement project-based event filtering `task_id:sse.project_filtering`
- [x] Add connection timeout and cleanup `task_id:sse.connection_cleanup`

#### Event Message Format

Standard lightweight event format:

```json
{
  "trigger": "refresh",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

Optional targeted events:

```json
{
  "trigger": "refresh",
  "target": "campaign",
  "id": 123
}
```

---

## Supporting Infrastructure

### File Layout

```text
app/
├── api/
│   └── v1/
│       └── endpoints/
│           └── web/
│               └── live.py             # SSE endpoints for /api/v1/web/live/*
├── core/
│   └── services/
│       └── event_service.py            # In-memory event broadcasting
```

### Module Responsibilities

- **`web/live.py`**

  - FastAPI SSE route handlers using `StreamingResponse`
  - Authentication via `Depends(get_current_user)`
  - Project scoping and event filtering

- **`core/services/event_service.py`**

  - In-memory event broadcaster
  - Topic-based subscription management
  - Event listener lifecycle management
  - Project-scoped event filtering

### Migration from WebSocket Implementation

- [x] Remove WebSocket dependencies and Redis pub/sub code `task_id:sse.cleanup_websocket`
- [x] Update existing broadcast functions to use new event service `task_id:sse.migrate_broadcasts`
- [x] Remove `fastapi-websocket-pubsub` dependency `task_id:sse.remove_websocket_deps`
- [x] Update tests to use SSE instead of WebSocket connections `task_id:sse.update_tests`

---

### Documentation Updates

With the many changes to the API, we need to update the documentation to reflect the changes. These changes go beyond just the SSE implementation, but also include the new endpoints and changes to the existing endpoints, as well as changes to the UI and user flows documented in `docs/v2_rewrite_implementation_plan/side_quests/salvage_templates.md` and `docs/v2_rewrite_implementation_plan/notes/user_flows_notes.md`. The changes to be made are:

- [x] Update the architecture documentation to reflect the changes. (found in `docs/architecture/*.md`)
- [x] Update the API reference documentation to reflect the structure of the API and the endpoints that are available. (found in `docs/api/overview.md` and `docs/development/api-reference.md`)
- [x] Update the user guide to reflect the changes. (found in `docs/user-guide/*.md`)
- [x] Update the developer guide to reflect the changes. (found in `docs/development/*.md`)
- [x] Update the getting started guide to reflect the changes. (found in `docs/getting-started/*.md`)
- [x] Update the troubleshooting guide to reflect the changes. (found in `docs/user-guide/troubleshooting.md`) - The primary audience for this guide is the administrator configuring the system, and the end user trying to figure out why their campaign is behaving as expected. It is not for developers and each section should be a single topic with a clear title and a description of the problem and the solution.
- [x] Update the FAQ to accurately reflect the current state of the system. (found in `docs/user-guide/faq.md`)

---

### Additional Tasks

- [x] Add robust unit tests for KeyspaceEstimator covering all attack modes and edge cases
- [x] Ensure all estimation logic (AttackEstimationService, endpoints, tests) uses strong typing (Pydantic models, enums) instead of dicts/Any for attack/resource parameters
  ms) instead of dicts/Any for
