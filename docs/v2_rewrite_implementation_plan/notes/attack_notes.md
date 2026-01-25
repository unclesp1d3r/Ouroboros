# Ouroboros Attack Editor UX & Behavior

## Ouroboros — Attack Editor UX & Behavior Context

### 🔁 General Issues with Current Attack Editor

- The legacy attack editor monopolizes the session UI as a single massive form that includes every hashcat option. Many of these options are never used by typical users, making the UI cumbersome.
- All attack editors must display **estimated keyspace size** and **complexity score** (same as shown in the campaign view). These values should update dynamically as users modify settings — even for unsaved attacks. The backend must support keyspace estimation for unsaved/pending attacks.
- Editing an attack that is either `running` or `exhausted` should:
  - Prompt a warning and require confirmation.
  - Upon confirmation, reset the attack state to `pending` and restart it on the assigned agent.

---

### Dictionary Attack Behavior

- Min/max length fields should default to the recommended range for the selected hash type (or default to 1-32).
- Wordlist selection should use a **searchable dropdown**, showing:
  - Entry count for each wordlist.
  - Sort order: most recently modified first.
- Users should be able to add common “modifiers” via buttons:
  - `+ Change Case`
  - `+ Substitute Characters`
  - `+ Change Character Order`
  - These should abstract rule-based logic without requiring the user to understand how hashcat rules work.
- For advanced users, allow direct rule list file selection.
- Support a **dynamic "Previous Passwords" option**, which uses all previously cracked plaintexts for the current project.
- Additionally, allow users to define **ephemeral wordlists**:
  - Instead of selecting a dictionary or dynamic list, the user can click “Add Word” to create a small, inline list.
  - Each word appears in its own input field; users can add/remove entries.
  - These lists are stored only on the Attack object and are deleted when the attack is deleted.
  - Ephemeral wordlists do not appear in the shared Resource Browser.

---

### Mask Attack (Manual Entry, Not Mask List File)

- Users should be able to enter a mask directly in an input field.
- Button: `+ Add Mask` — adds another input row.
- Each row must include an `X` delete button to remove it.
- These masks form an **ephemeral mask list** scoped only to that attack.
  - Not shown in the global Resource Browser.
  - Deleted with the attack.
- Validate each mask field in real-time; invalid input should show inline error indicators (like any normal form field).

---

### Brute Force (Incremental Mask) UI

- This is a convenience wrapper around incremental mask logic.
- Provide checkboxes for character classes:
  - `Lowercase`, `Uppercase`, `Numbers`, `Symbols`, `Space`
- Allow users to specify min/max length.
- Internally generates:
  - A mask of `?1` repeated max-length times (e.g., `?1?1?1?1?1?1?1`)
  - Sets `custom_charset_1` to a combination like `?l?d` depending on selected charsets.
- Simplifies creating a brute-force config without needing to understand `?1` syntax.

---

### Save/Load Support

- Users should be able to **export** a single Attack or an entire Campaign as a JSON file for reuse.
- This supports offline backup, sharing, and templating.
- Format must:
  - Include all editable fields, including `position`, `comment`, keyspace config, etc.
  - Include ephemeral mask/word lists as inline content.
  - Reference persistent resources (e.g., rule list) by their `guid`, not DB primary key.
- The schema must:
  - Omit project/user IDs and database PKs.
  - Be versioned and validated at load time.
- On import, the backend must:
  - Validate schema structure.
  - Restore ephemeral items inline.
  - Re-link persistent resources by GUID.
  - Prompt if a resource is missing or cannot be re-associated.

## Old notes

For the original stream-of-consciousness notes on the attack editor, see [Attack Notes](original_notes/attack.md).
