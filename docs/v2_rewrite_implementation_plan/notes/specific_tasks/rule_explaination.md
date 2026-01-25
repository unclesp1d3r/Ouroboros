### Task: Add Human-Readable Rule Preview Tooltips

**ID:** `attack.rule_preview_explanation`\
**Context:** Web UI (Phase 2/3) - Dictionary Attack Editor

#### Backend Requirements (Already Done)

This task is already implemented on the backend and exposes a mapping from rule lines (e.g., `c`, `u`, `T0`, `r`) to short human-readable explanations (e.g., `c → lowercase all characters`, `T0 → toggle case of first character`, etc.).

#### UI Goals

Enhance the **Rule List Dropdown** (used in the dictionary attack editor) by displaying **tooltips** next to each rule in the dropdown that show a short explanation of the rule.

#### [x] Implementation Instructions for Skirmish

- Use a [Flowbite Dropdown with search](https://flowbite.com/docs/components/dropdowns/#dropdown-with-search) for rule selection.

- For each rule entry:

  - Display the **rule file name** (e.g., `common-case-modifiers.rule`)
  - Underneath or beside it, list each **rule line** with a brief explanation.
    - Example rendering:

      ```text
      Title Case Rules
      ├─ c  → Lowercase all characters
      ├─ u  → Uppercase all characters
      ├─ T0 → Toggle case of first character
      ```

    - Can be inline with tooltips (`<span data-tooltip>`) or as a collapsible block beneath the rule name.

    - For full rule syntax, fallback to a modal.

- This is **preview only** — selecting the rule still works as usual.

#### TIP: Optional Enhancements

- Add an info icon (`?`) next to the rule dropdown.
  - Clicking it opens a modal via HTMX (`GET /api/v1/web/modals/rule_explanation`).
  - Modal content includes a longer explanation of rule syntax and examples.

#### Notes for Skirmish

- HTMX can be used to preload rule explanations inline or lazy-load on hover.
- If shown inline in the dropdown, explanations must not overflow or break alignment.
- Tooltips should be styled clearly and be screen-reader accessible.
- Do not allow users to edit rule lines here — this is strictly a read-only preview.
