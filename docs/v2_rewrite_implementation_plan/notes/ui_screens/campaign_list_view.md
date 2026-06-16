## Campaign View: Attack List Interface (Legacy "Attack Settings" Mockup)

This screen represents the primary **Campaign detail view**, listing all attacks attached to a specific campaign. The title should reflect the **Campaign Name** dynamically.

---

### TIP: General Notes

- The interface is a **table-like layout** rendered in the main content area, showing all active and configured attacks
- Sidebar selection shows attack types, but creation flow is triggered via a toolbar button (`+ Add Attack`)

---

## Layout Description

### 🏷️ Title Bar

```html
<h1 class="text-2xl font-semibold text-gray-900 dark:text-white">
 [Campaign Name]
</h1>
```

The text should reflect the name of the current campaign (e.g., "Fall PenTest Roundup", "ACME Internal Audit").

---

### Attack Table

The main table has **six columns**, styled like a data grid:

| Column                 | Content                                                                        |
| ---------------------- | ------------------------------------------------------------------------------ |
| **Attack**             | Human-readable label (e.g., "Dictionary", "Brute-force", "Previous Passwords") |
| **Language**           | Usually "English", may be blank for dynamic sets                               |
| **Length**             | Min → Max (e.g., `1-4`, `0-15`, `Trim from 1 to 13`)                           |
| **Settings**           | Blue-linked summary of applied modifiers or charset                            |
| **Passwords to Check** | Numeric value (comma-separated thousands)                                      |
| **Complexity**         | 0-5 dot visual meter (grey-filled circles)                                     |

Each row ends with a **gear icon** for a context menu (see [Campaign Notes - Attack Row Actions](../campaign_notes.md#attack-row-actions))

#### Attack Row Example

```html
<div class="grid grid-cols-6 items-center gap-4 py-2 border-b border-gray-200 dark:border-gray-700">
 <div>
  Brute-force
 </div>
 <div>
  English
 </div>
 <div>
  1 - 4
 </div>
 <div class="text-blue-600 hover:underline">
  Lowercase, Uppercase, Numbers, Symbols
 </div>
 <div>
  78,914,410
 </div>
 <div>
  <div class="flex space-x-1">
   <span class="w-2 h-2 bg-gray-600 rounded-full">
   </span>
   <span class="w-2 h-2 bg-gray-600 rounded-full">
   </span>
   <span class="w-2 h-2 bg-gray-600 rounded-full">
   </span>
   <span class="w-2 h-2 bg-gray-600 rounded-full">
   </span>
   <span class="w-2 h-2 bg-gray-200 rounded-full">
   </span>
  </div>
 </div>
</div>
```

---

### Row Action Menu

Each attack row has a trailing **gear icon** button (`<button class="icon-btn"><CogIcon /></button>`)

Trigger a Flowbite dropdown:

```html
<ul class="dropdown-menu">
 <li>
  <a href="#">
   Edit
  </a>
 </li>
 <li>
  <a href="#">
   Duplicate
  </a>
 </li>
 <li>
  <a href="#">
   Move Up
  </a>
 </li>
 <li>
  <a href="#">
   Move Down
  </a>
 </li>
 <li>
  <a class="text-red-600" href="#">
   Remove
  </a>
 </li>
</ul>
```

---

### ➕ Add Attack Button (Footer Left)

```html
<button class="btn btn-outline" hx-get="/api/v1/web/attacks/new" hx-swap="innerHTML" hx-target="#attack-modal">
 + Add Attack...
</button>
```

Triggers modal dialog for choosing a new attack type and entering config.

---

### Remove All Attacks

- Located at the bottom toolbar, uses a trash icon with “All” text
- Clicking it clears all attacks after confirmation

```html
<button class="btn btn-outline text-red-600" hx-confirm="Remove all attacks from this campaign?" hx-post="/api/v1/web/campaigns/{id}/clear_attacks">
 <trashicon>
 </trashicon>
 All
</button>
```

---

### ⏱️ Sort + Presets

Other toolbar buttons include:

- **Reset to Default**: Restores default attack list template (optional)
- **Save / Load**: Import/export JSON-encoded campaign configs
- **Sort by Duration**: Changes order of attack rows (sorted by estimated cracking time)

Each of these uses standard HTMX interactions (GET for load fragments, POST for save).

---

### Backend Notes

The attack list is populated from:

```jsonc
GET /api/v1/web/campaigns/{id}
```

Each attack is rendered from:

```jsonc
{
    "id": 123,
    "type": "brute_force",
    "language": "english",
    "length_min": 1,
    "length_max": 4,
    "settings_summary": "Lowercase, Uppercase, Numbers, Symbols",
    "keyspace": 78914410,
    "complexity_score": 4,
    "position": 3
}
```
