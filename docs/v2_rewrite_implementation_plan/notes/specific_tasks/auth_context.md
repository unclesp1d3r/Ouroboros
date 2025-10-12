# Project Context Management

## 🧠 Task: Project Context Management Endpoints

**ID:**

- `auth.get_context`
- `auth.set_context`
  **Context:** Web UI (Authenticated User Session)

---

### 🧭 Purpose

Ouroboros supports strict project-based isolation. Users can belong to multiple projects (especially admins, analysts, and consultants). These endpoints allow the Web UI to:

- **Retrieve** the current user's active project and list of accessible projects
- **Switch** the active project for all future interactions

The active project determines:

- Which campaigns, attacks, agents, and resources the user can see
- What scope new items are created under (e.g., campaign creation)
- How HTMX templates are rendered and filtered

---

### 📥 `GET /api/v1/web/auth/context`

**`task_id:auth.get_context`**

Returns the current user's active project context and all projects they have access to.

**Response Example:**

```json
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "role": "user"
  },
  "active_project": {
    "id": 42,
    "name": "Acme Corp - Red Team"
  },
  "available_projects": [
    {
      "id": 42,
      "name": "Acme Corp - Red Team"
    },
    {
      "id": 99,
      "name": "Internal Testing"
    }
  ]
}
```

---

### 📤 `POST /api/v1/web/auth/context`

**`task_id:auth.set_context`**

Sets the current active project for the user’s session.

**Request Example:**

```json
{
  "project_id": 99
}
```

Must validate that the user has access to the specified project. Updates server-side session or secure cookie state.

---

### 🎨 UI Integration

- Display the current project in the sidebar or account menu
- Allow switching via dropdown or modal
- Trigger a `POST /auth/context` request on change
- Use HTMX swap or full reload to reflect new project scope

---

### 🔒 Security & Behavior Notes

- Only allow users to switch to projects they are assigned to
- Do not cache or persist project selection across users/devices without revalidation
- Session or token context must be cleared on logout
- Agent and Control APIs do **not** use this mechanism — they require explicit project scoping
