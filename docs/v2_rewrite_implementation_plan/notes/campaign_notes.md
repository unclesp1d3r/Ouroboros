# Ouroboros Campaign UX and Behavior

## Ouroboros — Campaign UX and Behavior Context

### Campaign Attack Ordering

- Attack order should be **user-controlled**, not locked to creation time or estimated complexity.
- The campaign view must support **manual reordering** of attacks.

---

### Campaign View Toolbar

- Toolbar should include:
  - **Add Attack** button:
    - Opens the attack editor in a **modal dialog**.
    - Appends the new attack to the **end** of the attack list.
  - **Sort by Complexity/Duration** button.
  - **Bulk Select Controls**:
    - Checkbox toggle for each attack.
    - **Check All** option.
    - **Bulk Delete** button (enabled only when at least one attack is selected).
  - **Start/Stop Toggle**:
    - Defaults to **Stop** while editing.
    - **Start** makes the campaign active and eligible for agent tasking.

---

### Attack List Display (Within Campaign)

- Display attacks in a **table-like list view**.
- Each row includes:
  - **Attack Type** — Rendered as a meaningful human-friendly label.
  - **Length** — If defined (e.g., 1-8 characters); otherwise blank.
  - **Settings** — One-line summary of config (non-technical), clickable to open editor modal.
    - Blank if using simple defaults (e.g., dictionary attack with no modifiers).
  - **Passwords to Check** — Estimated keyspace.
  - **Complexity** — Graphical (e.g., 1-5 stars or dots).
  - **Comments** — User-provided description, truncated for display.

---

### Attack Row Actions (Context Menu)

- Each attack row should have a menu (via right-click or button).
- Menu options:
  - **Edit**
  - **Duplicate**
  - **Remove**
  - **Move Up**
  - **Move Down**
  - **Move To Top**
  - **Move To Bottom**
- These should be **logically grouped** for clarity (e.g., editing vs. movement actions).

---

Old notes:

For the original stream-of-consciousness notes on the campaign stuff, see [Campaign Notes](original_notes/campaigns.md).
