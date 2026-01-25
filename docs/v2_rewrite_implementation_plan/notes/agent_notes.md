# Ouroboros Agent Monitoring & Configuration

## Ouroboros — Agent Monitoring & Configuration Context

### General Goals

- Agent monitoring and configuration will be significantly expanded in a future phase (likely Phase 5).
- Current users report confusion around whether agents are truly running or idle.
- All users (including non-admins) should be able to view agent status; **only admins** can modify agents or view detailed controls.

---

### Agent List View (Overview Table)

Display all agents in a table with the following columns:

- **Agent Name + OS**
- **Status**
- **Temperature (°C)** — from most recent `DeviceStatus`
- **Utilization** — average of enabled devices
- **Current Attempts/sec** — most recent device guess rate
- **Average Attempts/sec** — average over the last minute
- **Current Job** — Show Project, Campaign, and Attack name
- **Gear Icon Menu** — Admin-only:
  - Options: Disable Agent, View Details

Relevant data sources: `DeviceStatus`, `TaskStatus`, and `HashcatGuess` from `contracts/v1_api_swagger.json`.

---

### ➕ Agent Registration Flow

- Triggered via **modal dialog**.
- Requires:
  - **Label** (Agent name override)
  - **Project toggles** (which projects this agent can work on)
- After creation, show **agent token** to copy/paste.

---

### 🔎 Agent Detail View (Tabbed Interface)

Admins only. Tabs:

---

#### Settings

- **Agent Label**:
  - Editable field. Sets `custom_label`.
  - Fallback to `host_name` if blank:\
    `display_name = agent.custom_label or agent.host_name`
- **Enabled**:
  - Toggle. If disabled, the agent will not receive tasks.
- **Agent Update Interval**:
  - Seconds between agent check-ins. Should default to random 1-15s, currently 30s.
- **Use Native Hashcat**:
  - Toggle `AdvancedAgentConfiguration.use_native_hashcat = true`.
- **Enable Additional Hash Types**:
  - Toggle to run `--benchmark-all` instead of `--benchmark`.
- **Project Assignment**:
  - Multi-toggle list of allowed projects.
- **System Info**:
  - Read-only. Displays:
    - Operating System
    - Last seen IP
    - Client signature
    - Agent token

---

#### Hardware

- **Computational Units** (aka Backend Devices):
  - Pulled from `--backend-info` on agent check-in.
  - Until check-in: show placeholder + gray-out controls.
  - Stored as:
    - Descriptive names → `Agent.devices` (list of `str`)
    - Enabled devices → `backend_device` (comma-separated 1-indexed integers)
  - UI:
    - Each device has an enable/disable toggle (Flowbite toggle).
    - If task is active:
      - Prompt with: 1. Restart task immediately 2. Apply change to next task 3. Cancel change
- **Hardware Acceleration Settings**:
  - Temperature abort (`--hwmon-temp-abort`): Not yet implemented, suggest default to 90°C or capture as a note.
  - `opencl_devices` toggle: defines allowed OpenCL device types.
  - Backend support toggles:
    - `--backend-ignore-cuda`
    - `--backend-ignore-opencl`
    - `--backend-ignore-hip`
    - `--backend-ignore-metal`

All the above are part of `AdvancedAgentConfiguration` in `contracts/v1_api_swagger.json`.

---

#### 📈 Performance

- **Line Chart (8h window)**:
  - Shows guess rate over time per device.
  - X-axis = time, Y-axis = hashes/sec.
  - Source: `DeviceStatus.speed`.
- **Device Cards**:
  - One per device.
  - Donut chart (Flowbite) for utilization.
  - Temperature text below.
    - If `-1`, show "Not Monitored".
- **Updates in real-time** from incoming `TaskStatus`.

---

#### 🪵 Log

- Displays agent error timeline.

- Use colored severity indicators for readability.

- Source: `AgentError` records, real-time updates.

- Fields:

  ```text
  id: Error ID
  message: Human-readable message
  severity: Level (info, warning, critical, etc.)
  error_code: Optional
  details: Optional JSON
  agent_id: FK
  task_id: Optional FK
  ```

---

#### Capabilities

- Shows benchmark results (latest only).
- Used to determine which hash types the agent can handle.
- Source: `app.models.hashcat_benchmark.HashcatBenchmark`

Benchmark model fields:

```python
class HashcatBenchmark(Base):
    id: int
    agent_id: int(FK)
    hash_type_id: int(FK)
    runtime: int(ms)
    hash_speed: float(h / s)
    device: str
    created_at: datetime
```

- **Top-level table**:
  - Columns:
    - Toggle (to disable hash mode)
    - Hash ID
    - Name
    - Speed (e.g. 3.2 Gh/s)
    - Category (from `current_hashcat_hashmodes.txt`)
  - Rows = one per hash mode, across all devices
  - Expandable rows show per-device breakdown
  - Filterable by category
  - Searchable by name or hash ID
  - Caption: Last benchmark date
  - Header button: "Rebenchmark" (sets `agent.state = pending`)

---

## Original notes

For the original stream-of-consciousness notes on the agent stuff, see [Agent Notes](original_notes/agent.md).
