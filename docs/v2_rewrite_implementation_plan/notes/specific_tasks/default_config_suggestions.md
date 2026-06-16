# Default Attack Config Suggestions

Here's the updated version of the `attack.default_config_suggestions.md` note with your hybrid plan fully captured:

---

## Task: Show Default Attack Config Suggestions

**ID:** `attack.default_config_suggestions` **Context:** Attack Editor UI (Web)

### 🧭 Purpose

Provide a curated list of **default attack configurations** (e.g., common mask patterns, rulesets, and charset combos) to guide new or casual users. These suggestions should be admin-managed and project-aware, enabling power users to surface battle-tested configurations to the rest of the team.

### [x] Final Design Approach

Rather than hardcoding suggestions or adding a new system, we will **extend the existing `AttackTemplate` concept** to allow templates to be stored and flagged as "recommended" in the backend.

Templates with `recommended: true` will be exposed to the frontend as default suggestions for use in the attack editor. These templates will be stored in the database (not just as import/export files) and may be project-scoped or global.

---

## Implementation Tasks

### Backend Tasks

- [ ] Add a new `AttackTemplateRecord` database model to persist named templates server-side

- [ ] Include fields:

  - `name: str`
  - `description: str`
  - `attack_mode: AttackMode`
  - `recommended: bool`
  - `project_id: list[int]|None`
  - `template_json: dict`
  - `created_at: datetime`

- [ ] Create API endpoint `GET /api/v1/web/templates/` - Returns only templates where `recommended = true` and `project_id` is null or matches the current project (unless the user is an admin)

  - Takes a parameter `attack_mode: AttackMode` to filter templates by attack mode
  - Takes a parameter `project_id: int|None` to filter templates by project (unless the user is an admin)
  - Returns a list of `AttackTemplateRecord` objects

- [ ] Add `POST /api/v1/web/templates/` for creating a new template in the database (admin-only)

- [ ] Add `GET /api/v1/web/templates/{id}` for retrieving a template from the database

- [ ] Add `PATCH /api/v1/web/templates/{id}` for updating a template in the database (admin-only)

- [ ] Add `DELETE /api/v1/web/templates/{id}` for deleting a template in the database (admin-only)

### 🧑‍ Admin UI Tasks

- [ ] Add UI to list and manage stored templates (admin-only)
- [ ] Add an upload form that accepts an AttackTemplate JSON file via drag and drop or file upload
- [ ] Allow global (project-less) templates to be marked as reusable across the entire instance
- [ ] Add a button to remove a template
- [ ] Add a button to open a modal to allow the assigned projects to be edited via checkbox selection, with a save button, cancel button, and a unselect all button.

### Attack Editor UI Tasks

- [ ] Display a new dropdown or section labeled "_"Use a Recommended Template"_
- [ ] Pull recommended templates from the new endpoint (show all templates that have no project_id assigned, and all templates that have a project_id assigned to the current project)
- [ ] Autofill the attack editor with the selected template's config (mask, rule, charset, etc.)
- [ ] Allow editing after selection — this is just a starting point to prefill the attack editor with a template, but the user should be able to edit the attack editor after selection.

---

## Benefits

- Admins can define reusable, pre-tuned configurations
- New users get battle-tested starting points without needing to understand hashcat internals
- Project-scoped recommendations allow tailored templates for different customers or ops
- TUI and CLI workflows can reuse the same backend logic
