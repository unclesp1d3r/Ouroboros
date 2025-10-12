# Ouroboros Template Salvage Plan (HTMX to SvelteKit)

This document lists all templates in `templates/**/*.html.j2` and provides a recommendation for each: **Refactor as Svelte component** (with context) or **Discard** (with rationale). Use this as a migration checklist for the SvelteKit UI rewrite. All Svelte components must comply with the SvelteKit v5 (@svelte-runes) and Tailwind v4 idioms and best practices, and must be tested with `just frontend-check`.

---

## Table of Contents

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=3 --minlevel=1 -->

- [Ouroboros Template Salvage Plan (HTMX to SvelteKit)](#ouroboros-template-salvage-plan-htmx-to-sveltekit)
  - [Table of Contents](#table-of-contents)
  - [Migration Conventions & Clarifications](#migration-conventions--clarifications)
  - [Additional Migration Guidance (Clarifications)](#additional-migration-guidance-clarifications)
  - [Dashboard & Layout](#dashboard--layout)
  - [Agents](#agents)
  - [Campaigns](#campaigns)
  - [Attacks](#attacks)
  - [Resources](#resources)
  - [Users](#users)
  - [Projects](#projects)
  - [Fragments (General UI)](#fragments-general-ui)
  - [Templates to Discard](#templates-to-discard)
  - [General Notes](#general-notes)

<!-- mdformat-toc end -->

---

## Migration Conventions & Clarifications

**These conventions are authoritative for all template salvage and SvelteKit migration work.**

1. **Component Naming:**
   - Svelte components should use PascalCase names that reflect their purpose, not the original Jinja filename. For example, `benchmarks_fragment.html.j2` becomes `AgentBenchmarks.svelte`.
2. **Directory Structure:**
   - Place new Svelte components in `frontend/src/lib/components/` with appropriate subfolders (e.g., `agents/`, `campaigns/`, etc.).
3. **Testing:**
   - If a fragment is subsumed into a larger component, test the larger component. Do not force a 1:1 mapping if it is not logical, but ensure all functionality is covered.
   - Tests must cover rendering, interaction, state, functionality, and error conditions. Err on the side of more comprehensive tests.
4. **Discarded Templates:**
   - Delete `.html.j2` files immediately when marked as "Discard." All changes are tracked in source control.
5. **Design/UX Authority:**
   - The UI screen notes in `docs/v2_rewrite_implementation_plan/notes/ui_screens/`, `docs/v2_rewrite_implementation_plan/notes/user_flows_notes.md`, and the UX Design Goals in `docs/v2_rewrite_implementation_plan/phase-2-api-implementation-parts/phase-2-api-implementation-part-2.md` are authoritative. If a conflict cannot be resolved after consulting these, stop and propose a solution for approval.
6. **Fragment Handling:**
   - If a fragment is only used once, inline it into the parent component unless the referenced design/UX notes indicate it should be reusable. Always review the original context in `phase-2-api-implementation-part-2.md` and the relevant API endpoint to ensure the best approach.

---

## Additional Migration Guidance (Clarifications)

+**Always consult the 'References' line under each checklist item below for the authoritative notes and design docs to use for that task. Do not search all notes files for every task—use the provided references as your primary source.**

1. **Fragment Usage Audits:**
   - For each fragment, if its usage is ambiguous based on the notes, perform a usage audit (list all templates where it appears). If you cannot resolve whether it should be inlined or reusable, flag it for review.
2. **Styling:**
   - Use Shadcn-Svelte and Tailwind exclusively. Only use custom classes if absolutely necessary, and derive them from Tailwind/Shadcn as much as possible. Do not port legacy styles.
3. **Legacy JS/HTMX Logic:**
   - No legacy JS or HTMX logic is to be preserved. All interactivity should be reimplemented idiomatically in Svelte. If something cannot be mapped, approximate the intent and note the issue in the checklist.
4. **Props/Data Shape:**
   - Infer props and data shape from the UI/UX notes, API docs, and backend endpoints. No need to propose interfaces in advance unless ambiguity remains after review.
5. **Error/Empty States:**
   - All components must implement error and empty states as described in the dashboard and UX notes, even if the original template did not.
6. **Testing Utilities:**
   - The frontend is a clean SvelteKit v5 install with Shadcn-Svelte, Tailwind v4, Vitest, Playwright, ESLint, and Prettier. No custom test utilities exist; create any needed helpers or mocks as part of the migration.

---

The goal for this effort is to salvage whatever we can from the templates we originally created for use by HTMX and Jinja to be used in the SvelteKit UI. If it is not used in the SvelteKit UI, it should be discarded. If it is used in the SvelteKit UI, it should be refactored as a Svelte component and should follow the SvelteKit idioms and best practices. We are using SvelteKit v5 and Tailwind CSS v4 with Shadcn-Svelte components.

Each converted template should also have a playwright e2e test, and potentially a vitest unit test, that verifies the template is converted correctly and that the Svelte component is working as expected. The unit test should be for any simple component that does not require a page or modal or for basic algorithm logic. The playwright test must be for the integration of the component into the page or modal and must be created for each template that is converted. This MUST be verified by running `just frontend-check` and ensuring the tests pass. The vitest unit test should be placed next to the component file and named `<template_name>.spec.ts`. The playwright e2e test should be placed in the `frontend/e2e` directory and named `<template_name>.test.ts`. Because the backend is not running during the tests, we need to mock the API responses within the playwright test.

Follow the conventions of shadcn-svelte closely and do not reuse any of the templates CSS classes except as references.

Due to the frontend being mounted as a static site by FastAPI, the frontend is pre-rendered and we are not using SSR. We are using SvelteKit's client-side routing and hydration. All forms should be implemented using idiomatic formsnap (<https://formsnap.dev/docs>).

---

## Dashboard & Layout

- [x] **base.html.j2** → **Refactor as SvelteKit layout** - `task_id:salvage_templates.base_html_j2`

  - _Context_: Provides navigation, layout, and global structure. Should become `+layout.svelte` and `Sidebar`, `Header`, and `Toast` components using Shadcn-Svelte. Remove all HTMX/Alpine/Flowbite JS. Navigation links and user menu should be Svelte stores and role-aware.
  - **References:**
    - `docs/v2_rewrite_implementation_plan/notes/ui_screens/dashboard-ux.md` (Layout Overview, Sidebar, Header, Toast, Component Inventory)
    - `docs/v2_rewrite_implementation_plan/notes/user_flows_notes.md` (Authentication & Session, Access Behavior)
    - `docs/v2_rewrite_implementation_plan/phase-2-api-implementation-parts/phase-2-api-implementation-part-2.md` (Web UI API, Authentication)

- [x] **dashboard.html.j2** → **Refactor as Svelte page** - `task_id:salvage_templates.dashboard_html_j2` (Refactored as SvelteKit dashboard page with full test and lint coverage)

  - _Context_: Maps directly to the v2 Dashboard UX. Cards (Active Agents, Running Tasks, Cracked Hashes, Resource Usage) become Svelte components with live data via SSE. Recent Activity and Active Tasks sections should be Svelte tables fed by stores. Remove all Jinja/HTMX logic.
  - **References:**
    - `docs/v2_rewrite_implementation_plan/notes/ui_screens/dashboard-ux.md` (Dashboard Cards, Campaign Overview Section, Agent Status Overview, Live Toast Notifications)
    - `docs/v2_rewrite_implementation_plan/notes/user_flows_notes.md` (Monitoring & Feedback, Health & System Status)
    - `docs/v2_rewrite_implementation_plan/phase-2-api-implementation-parts/phase-2-api-implementation-part-2.md` (Web UI API, Campaign Management)

---

## Agents

- [x] **agents/list.html.j2** → **Refactor as Svelte page** - `task_id:salvage_templates.agents_list_html_j2` (Implemented as AgentList.svelte with full test and lint coverage.)

  - _Context_: Agent list/table, filters, and actions map to the Agent Status Sheet and Agent List views. Use Svelte table, filter/search as reactive stores, and modal for registration. Actions (Details, Shutdown) become Svelte modals/dialogs.
  - **References:**
    - `docs/v2_rewrite_implementation_plan/notes/ui_screens/dashboard-ux.md` (Agent Status Overview)
    - `docs/v2_rewrite_implementation_plan/notes/user_flows_notes.md` (Agent Visibility & Control)
    - `docs/v2_rewrite_implementation_plan/phase-2-api-implementation-parts/phase-2-api-implementation-part-2.md` (Web UI API, Agent Management)

- [x] **agents/details_modal.html.j2** → **Refactor as Svelte modal** - `task_id:salvage_templates.agents_details_modal_html_j2` (Refactored as AgentDetailsModal.svelte with full test and lint coverage.)

  - _Context_: Agent detail modal, including device toggles and advanced config, should be a Shadcn-Svelte dialog (<https://next.shadcn-svelte.com/docs/components/dialog>). All forms become Shadcn-Svelte forms (<https://next.shadcn-svelte.com/docs/components/form>) with validation. Device toggles will be Shadcn-Svelte switches (<https://next.shadcn-svelte.com/docs/components/switch>). Device toggles and config are admin-only.
  - **References:**
    - `docs/v2_rewrite_implementation_plan/notes/ui_screens/dashboard-ux.md` (Agent Status Overview, Agent Card Example)
    - `docs/v2_rewrite_implementation_plan/notes/user_flows_notes.md` (Agent Visibility & Control)
    - `docs/v2_rewrite_implementation_plan/phase-2-api-implementation-parts/phase-2-api-implementation-part-2.md` (Agent display name logic, Agent Management)

- [x] **agents/register_modal.html.j2** → **Refactor as Svelte modal** - `task_id:salvage_templates.agents_register_modal_html_j2`

  - Refactored as Svelte modal (AgentRegisterModal.svelte) with full test coverage and lint clean.
  - _Context_: Agent registration modal. Use Shadcn-Svelte form (<https://next.shadcn-svelte.com/docs/components/form>), validation, and modal dialog. Remove all HTMX.
  - **References:**
    - `docs/v2_rewrite_implementation_plan/notes/user_flows_notes.md` (Agent Visibility & Control)
    - `docs/v2_rewrite_implementation_plan/phase-2-api-implementation-parts/phase-2-api-implementation-part-2.md` (Agent Management)

- [x] **agents/table_fragment.html.j2**/**row_fragment.html.j2**/**benchmarks_fragment.html.j2**/**hardware_fragment.html.j2**/**performance_fragment.html.j2**/**error_log_fragment.html.j2** → **Refactor as Svelte components** - `task_id:salvage_templates.agents_table_fragment_html_j2` (Refactored as Svelte components, composed in AgentDetailsModal as five tabs (Settings, Hardware, Performance, Log, Capabilities) per agent_notes.md, with full e2e and lint coverage.)

  - _Context_: These fragments are used in agent detail/status views. Each should become a Svelte component (e.g., AgentBenchmarks, AgentHardware, AgentPerformance, AgentErrorLog) and be composed in the Agent modal/page.
  - **References:**
    - `docs/v2_rewrite_implementation_plan/notes/ui_screens/dashboard-ux.md` (Agent Status Overview, Agent Card Example)
    - `docs/v2_rewrite_implementation_plan/notes/user_flows_notes.md` (Agent Visibility & Control)

---

## Campaigns

- [x] **campaigns/list.html.j2** → **Refactor as Svelte page** - `task_id:salvage_templates.campaigns_list_html_j2` (Implemented as CampaignsList SvelteKit page using Shadcn-Svelte, Tailwind v4, and idiomatic SvelteKit v5. Includes Card, Accordion, Progress, Badge, Tooltip, Table, Button, DropdownMenu, and Pagination components. Supports pagination, filtering, live updates, and empty/error states. Full test and lint coverage.)

  - _Context_: Campaign list view. Use Svelte table, filters, and pagination. Maps to Campaign Overview List in dashboard-ux.md.
  - **References:**
    - `docs/v2_rewrite_implementation_plan/notes/ui_screens/dashboard-ux.md` (Campaign Overview Section)
    - `docs/v2_rewrite_implementation_plan/notes/ui_screens/campaign_list_view.md` (General Notes, Layout Description)
    - `docs/v2_rewrite_implementation_plan/notes/user_flows_notes.md` (Campaign Management)
    - `docs/v2_rewrite_implementation_plan/phase-2-api-implementation-parts/phase-2-api-implementation-part-2.md` (Campaign Management)

- [x] **campaigns/detail.html.j2** → **Refactor as Svelte page** - `task_id:salvage_templates.campaigns_detail_html_j2`

  - Refactored as SvelteKit page (CampaignsDetail) with Shadcn-Svelte, Tailwind v4, and full test coverage. Lint clean.
  - _Context_: Campaign detail view, including attack table. Attack rows/actions map to Svelte components. Use Svelte accordion for attack rows.
  - **References:**
    - `docs/v2_rewrite_implementation_plan/notes/ui_screens/campaign_list_view.md` (Attack Table, Row Action Menu)
    - `docs/v2_rewrite_implementation_plan/notes/user_flows_notes.md` (Campaign Management, DAG Awareness)
    - `docs/v2_rewrite_implementation_plan/phase-2-api-implementation-parts/phase-2-api-implementation-part-2.md` (Campaign Management, Attack Management)

- [x] **campaigns/editor_modal.html.j2**/**form.html.j2**/**delete_confirm.html.j2** → **Refactor as Svelte modals/forms** - `task_id:salvage_templates.campaigns_editor_modal_html_j2` (✅ **COMPLETED**: Refactored as CampaignEditorModal.svelte and CampaignDeleteModal.svelte with Shadcn-Svelte, Tailwind v4, and Svelte 5 runes. Integrated into campaigns page with full functionality. Includes Playwright e2e tests and lint clean. Original Jinja templates deleted.)

  - _Context_: Campaign create/edit/delete flows. Use Svelte forms and dialogs.
  - **References:**
    - `docs/v2_rewrite_implementation_plan/notes/user_flows_notes.md` (Campaign Management)
    - `docs/v2_rewrite_implementation_plan/phase-2-api-implementation-parts/phase-2-api-implementation-part-2.md` (Campaign Management)

- [x] **campaigns/progress_fragment.html.j2**/**metrics_fragment.html.j2** → **Refactor as Svelte components** - `task_id:salvage_templates.campaigns_progress_fragment_html_j2` (✅ **COMPLETED**: Created `CampaignProgress.svelte` and `CampaignMetrics.svelte` components with live data fetching, auto-refresh every 5 seconds, comprehensive test coverage (unit and e2e), and integrated into campaign detail page. Original templates removed.)

  - _Context_: Progress and metrics widgets for campaign detail. Use Svelte stores for live updates.
  - **References:**
    - `docs/v2_rewrite_implementation_plan/notes/ui_screens/dashboard-ux.md` (Dashboard Cards, Campaign Overview Section)
    - `docs/v2_rewrite_implementation_plan/notes/user_flows_notes.md` (Monitoring & Feedback)
    - `docs/v2_rewrite_implementation_plan/phase-2-api-implementation-parts/phase-2-api-implementation-part-2.md` (Campaign Management, Implementation Tasks)

---

## Attacks

- [x] **attacks/list.html.j2** → **Refactor as Svelte page** - `task_id:salvage_templates.attacks_list_html_j2`

  - _Context_: Attack list for a campaign. Table layout, row actions, and modals map to Svelte components. See campaign_list_view.md.
  - **References:**
    - `docs/v2_rewrite_implementation_plan/notes/ui_screens/campaign_list_view.md` (Attack Table, Row Action Menu)
    - `docs/v2_rewrite_implementation_plan/notes/user_flows_notes.md` (Attack Configuration)
    - `docs/v2_rewrite_implementation_plan/phase-2-api-implementation-parts/phase-2-api-implementation-part-2.md` (Attack Management, UX Design Goals)

- [x] **attacks/editor_modal.html.j2**/**view_modal.html.j2** → **Refactor as Svelte modals** - `task_id:salvage_templates.attacks_editor_modal_html_j2` (Refactored as AttackEditorModal.svelte and AttackViewModal.svelte with Shadcn-Svelte, Tailwind v4, and Svelte 5 runes. Integrated into attacks page with full functionality. Includes Playwright e2e tests and lint clean. Original Jinja templates deleted.)

  - _Context_: Attack editor/view modals. Use Svelte forms, validation, and modal dialogs. All attack mode editors (dictionary, mask, brute-force) should be Svelte components, referencing the attack editor notes.
  - **References:**
    - `docs/v2_rewrite_implementation_plan/notes/ui_screens/new_dictionary_attack_editor.md`
    - `docs/v2_rewrite_implementation_plan/notes/ui_screens/new_mask_attack_editor.md`
    - `docs/v2_rewrite_implementation_plan/notes/ui_screens/brute_force_attack_editor.md`
    - `docs/v2_rewrite_implementation_plan/notes/ui_screens/previous_password_dictionary_attack_editor.md`
    - `docs/v2_rewrite_implementation_plan/notes/user_flows_notes.md` (Attack Configuration)
    - `docs/v2_rewrite_implementation_plan/phase-2-api-implementation-parts/phase-2-api-implementation-part-2.md` (Attack Management, UX Design Goals)

- [x] **attacks/brute_force_preview_fragment.html.j2**/**live_updates_toggle_fragment.html.j2**/**performance_summary_fragment.html.j2**/**estimate_fragment.html.j2**/**validate_summary_fragment.html.j2**/**attack_table_body.html.j2** → **Refactor as Svelte components** - `task_id:salvage_templates.attacks_brute_force_preview_fragment_html_j2`

  - Refactored as BruteForcePreview.svelte, LiveUpdatesToggle.svelte, PerformanceSummary.svelte, Estimate.svelte, ValidateSummary.svelte, and AttackTableBody.svelte with Shadcn-Svelte, Tailwind v4, and Svelte 5 runes. Integrated into attacks page with full functionality. Includes Playwright e2e tests and lint clean.
  - _Context_: Used in attack editor and attack list. Each fragment becomes a Svelte component (e.g., BruteForcePreview, LiveUpdatesToggle, PerformanceSummary, Estimate, ValidateSummary, AttackTableBody).
  - **References:**
    - `docs/v2_rewrite_implementation_plan/notes/ui_screens/brute_force_attack_editor.md`
    - `docs/v2_rewrite_implementation_plan/notes/ui_screens/new_dictionary_attack_editor.md`
    - `docs/v2_rewrite_implementation_plan/notes/ui_screens/new_mask_attack_editor.md`
    - `docs/v2_rewrite_implementation_plan/notes/user_flows_notes.md` (Attack Configuration)
    - `docs/v2_rewrite_implementation_plan/phase-2-api-implementation-parts/phase-2-api-implementation-part-2.md` (Attack Management, Implementation Tasks)

---

## Resources

- [x] **resources/list_fragment.html.j2** → **Refactor as Svelte page/component** - `task_id:salvage_templates.resources_list_fragment_html_j2` (✅ **COMPLETED**: Implemented as SvelteKit page with Shadcn-Svelte components, search/filter functionality, pagination, loading states, error handling, and comprehensive Playwright e2e test coverage. All tests passing.)

  - _Context_: Resource list/table, filters, and pagination. Use Svelte table and stores. Maps to resource management UI in dashboard-ux.md.
  - **References:**
    - `docs/v2_rewrite_implementation_plan/notes/user_flows_notes.md` (Resource Management)
    - `docs/v2_rewrite_implementation_plan/phase-2-api-implementation-parts/phase-2-api-implementation-part-2.md` (Web UI API, Resource Management)

- [x] **resources/detail_fragment.html.j2**/**preview_fragment.html.j2**/**content_fragment.html.j2**/**lines_fragment.html.j2**/**line_row_fragment.html.j2**/**rulelist_dropdown_fragment.html.j2**/**wordlist_dropdown_fragment.html.j2** → **Refactor as Svelte components** - `task_id:salvage_templates.resources_detail_fragment_html_j2` (✅ **COMPLETED**: Created 7 Svelte components - ResourceDetail, ResourcePreview, ResourceContent, ResourceLines, ResourceLineRow, RulelistDropdown, WordlistDropdown. Integrated into resource detail page at `/resources/[id]` with comprehensive Playwright e2e tests. All tests passing.)

  - _Context_: Resource detail/preview, dropdowns, and line views. Each fragment becomes a Svelte component.
  - **References:**
    - `docs/v2_rewrite_implementation_plan/notes/user_flows_notes.md` (Resource Management)
    - `docs/v2_rewrite_implementation_plan/phase-2-api-implementation-parts/phase-2-api-implementation-part-2.md` (Resource Management)

---

## Users

- [x] **users/list.html.j2** → **Refactor as Svelte page** - `task_id:salvage_templates.users_list_html_j2`

  - _Context_: User management table, filters, and actions. Use Svelte table, stores, and modals for edit/delete. Admin-only.
  - **References:**
    - `docs/v2_rewrite_implementation_plan/notes/user_flows_notes.md` (Authentication & Session)
    - `docs/v2_rewrite_implementation_plan/phase-2-api-implementation-parts/phase-2-api-implementation-part-2.md` (Authentication & Profile)

- [x] **users/detail.html.j2**/**create_form.html.j2** → **Refactor as Svelte components** - `task_id:salvage_templates.users_detail_html_j2` (✅ **COMPLETED**: Implemented UserDetail.svelte and UserCreateForm.svelte with Shadcn-Svelte forms, modals, and validation. Integrated into users page with comprehensive Playwright e2e tests. All tests passing.)

  - _Context_: User detail and create form. Use Shadcn-Svelte forms and modals.
  - **References:**
    - `docs/v2_rewrite_implementation_plan/notes/user_flows_notes.md` (Authentication & Session)
    - `docs/v2_rewrite_implementation_plan/phase-2-api-implementation-parts/phase-2-api-implementation-part-2.md` (Authentication & Profile)

---

## Projects

- [x] **projects/list.html.j2** → **Refactor as Svelte page** - `task_id:salvage_templates.projects_list_html_j2` (✅ **COMPLETED**: Implemented SvelteKit projects list page with Shadcn-Svelte components, TypeScript interfaces, search functionality, pagination, loading/error/empty states, action menus, and comprehensive Playwright e2e test coverage. All tests passing.)

  - _Context_: Project list/table, filters, and pagination. Use Shadcn-Svelte table and stores. Maps to project selector in dashboard-ux.md.
  - **References:**
    - `docs/v2_rewrite_implementation_plan/notes/user_flows_notes.md` (Authentication & Session, Project Admin)
    - `docs/v2_rewrite_implementation_plan/phase-2-api-implementation-parts/phase-2-api-implementation-part-2.md` (Authentication & Profile)

- [x] **projects/project_info.html.j2** → **Refactor as Svelte component** - `task_id:salvage_templates.projects_project_info_html_j2` (✅ **COMPLETED**: Implemented ProjectInfo.svelte component with Shadcn-Svelte Card, Badge, and Separator components. Displays project details including name, description, visibility, status, user count, notes, and timestamps. Includes comprehensive unit tests (Vitest) and integration e2e tests (Playwright). All tests passing and lint clean. Original Jinja template deleted.)

  - _Context_: Project info card/detail. Use Svelte component.
  - **References:**
    - `docs/v2_rewrite_implementation_plan/notes/user_flows_notes.md` (Authentication & Session, Project Admin)
    - `docs/v2_rewrite_implementation_plan/phase-2-api-implementation-parts/phase-2-api-implementation-part-2.md` (Authentication & Profile)

---

## Fragments (General UI)

- [x] **fragments/alert.html.j2** → **Refactor as Svelte component** - `task_id:salvage_templates.fragments_alert_html_j2` (✅ **COMPLETED**: Implemented comprehensive toast utility functions using svelte-sonner. Removed redundant custom Alert component in favor of existing Shadcn-Svelte Alert and Sonner toast components. Added specialized toast functions for Ouroboros events (hash cracking, agent status, campaign status). All tests passing.)

  - _Context_: Alert/toast/notification. Use Shadcn-Svelte Toast or Alert component.
  - **References:**
    - `docs/v2_rewrite_implementation_plan/notes/ui_screens/dashboard-ux.md` (Live Toast Notifications)
    - `docs/v2_rewrite_implementation_plan/notes/user_flows_notes.md` (Monitoring & Feedback)

- [x] **fragments/rule_explanation_modal.html.j2**/**profile.html.j2**/**context.html.j2**/**attack_edit_warning.html.j2** → **Refactor as Svelte components** - `task_id:salvage_templates.fragments_rule_explanation_modal_html_j2` - (✅ **COMPLETED**: Refactored rule_explanation_modal.html.j2 as RuleExplanationModal.svelte with Shadcn-Svelte, Tailwind v4, and Svelte 5 runes. Integrated into attacks page with full functionality. Includes Playwright e2e tests and lint clean. Original Jinja templates deleted.)

  - _Context_: Used in various modals and detail views. Each should be a Svelte component/modal as appropriate.
  - **References:**
    - `docs/v2_rewrite_implementation_plan/notes/user_flows_notes.md` (Attack Configuration, Authentication & Session)
    - `docs/v2_rewrite_implementation_plan/phase-2-api-implementation-parts/phase-2-api-implementation-part-2.md` (Attack Management, Authentication & Profile)

---

## Templates to Discard

- [x] **Any template whose only purpose is HTMX partial update, or is tightly coupled to server-side Jinja/HTMX logic** - `task_id:salvage_templates.discard_templates_html_j2` (✅ **COMPLETED**: All Jinja templates in `templates/` should be deleted and the empty directories removed.)

  - _Rationale_: SvelteKit will handle all UI updates client-side. Any template that only exists for HTMX fragment swaps, or is not referenced in the v2 UI notes, should be deleted.
  - **References:**
    - `docs/v2_rewrite_implementation_plan/notes/ui_screens/` (review for relevance)
    - `docs/v2_rewrite_implementation_plan/notes/user_flows_notes.md`

- [x] **All inline scripts, Alpine.js, and Flowbite JS usage** - `task_id:salvage_templates.discard_templates_html_j2` - (✅ **COMPLETED**: All inline scripts, Alpine.js, and Flowbite JS usage should be removed. All interactivity and state will be handled by Svelte. Removed references from cursor rules.)

  - _Rationale_: All interactivity and state will be handled by Svelte. Remove all legacy JS and HTMX attributes.
  - **References:**
    - `docs/v2_rewrite_implementation_plan/notes/ui_screens/` (review for relevance)
    - `docs/v2_rewrite_implementation_plan/notes/user_flows_notes.md`

- [x] **All Jinja templates** - `task_id:salvage_templates.discard_templates_html_j2` (✅ **COMPLETED**: All Jinja templates in `templates/` should be deleted and the empty directories removed.)

  - _Rationale_: Jinja templates are not used in the SvelteKit UI. As conversion is complete, all Jinja templates in `templates/` should be deleted and the empty directories removed.

---

## General Notes

- All forms, tables, and modals should use SvelteKit idioms, Shadcn-Svelte, and bits-ui Svelte components.
- All forms should use formsnap (<https://formsnap.dev/docs>) and Zod for validation.
- All data should be loaded via axios and Svelte stores, not via HTMX or Jinja.
- All role-based access and admin-only features should be implemented using SvelteKit's session/auth store.
- Use the UI screen notes in `docs/v2_rewrite_implementation_plan/notes/ui_screens/` for detailed component requirements and design references.
- All styling should follow the style guide in `docs/development/style-guide.md`.

---

**This checklist should be updated as templates are refactored or deleted.**
