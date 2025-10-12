# Ouroboros Phase 5: Master Summary

---

## Table of Contents

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=3 --minlevel=1 -->

- [Ouroboros Phase 5: Master Summary](#ouroboros-phase-5-master-summary)
  - [Table of Contents](#table-of-contents)
  - [Mission](#mission)
  - [DAG-based Cracking Campaigns](#dag-based-cracking-campaigns)
    - [Why a DAG?](#why-a-dag)
  - [CORE PILLARS](#core-pillars)
    - [Advanced Task Scheduling Advanced Task Scheduler](#advanced-task-scheduling-advanced-task-scheduler)
    - [Agent Sync + Health Framework Agent Sync Extensions](#agent-sync--health-framework-agent-sync-extensions)
    - [Agent Collaboration Model Agent-Server Collaboration Vision](#agent-collaboration-model-agent-server-collaboration-vision)
    - [Hard Password Attack Intelligence Hard Password Attack Strategies](#hard-password-attack-intelligence-hard-password-attack-strategies)
  - [INTEGRATION THEMES](#integration-themes)
    - [Intelligence-Driven Strategy](#intelligence-driven-strategy)
    - [Agent Self-Governance](#agent-self-governance)
    - [Fine-Grained Orchestration](#fine-grained-orchestration)
    - [Observability & Learning](#observability--learning)
  - [Immediate Implementation Tracks](#immediate-implementation-tracks)
  - [Suggested Skirmish Sequence](#suggested-skirmish-sequence)

<!-- mdformat-toc end -->

---

## Mission

Phase 5 transforms Ouroboros from a high-performance orchestrator into an **adaptive, feedback-driven cracking intelligence system**, with smarter agents, real-time scheduling, dynamic planning, and strategic attack optimization.

---

## DAG-based Cracking Campaigns

This is the Ouroboros's effort to implement Directed Acyclic Graph (DAG) based cracking campaigns. In Ouroboros’s context, a DAG is used to model the flow of attack phases — where each node represents a cracking strategy (e.g., dictionary+rule, mask, brute-force), and arrows show which phases logically follow others.

### Why a DAG?

- Directed: Attack steps move forward — you don’t re-run prior phases unless explicitly configured.
- Acyclic: No loops — each path flows from start to completion without circling back.
- Graph: Multiple branches can exist in parallel, enabling exploratory or fallback strategies.

---

## CORE PILLARS

### **Advanced Task Scheduling** [Advanced Task Scheduler](advanced_task_scheduler.md)

- WorkSlice + TaskPlan system based on precomputed keyspace divisions
- Fully supports hybrid, mask, brute-force, and incremental attack types
- Real-time slice leasing with reclaim logic and keyspace coverage tracking
- Agent scoring considers hashrate benchmarks, throttling, and uptime
- Supports crackless watchdogs, thermal-aware scoring, and background task prioritization

### **Agent Sync + Health Framework** [Agent Sync Extensions](agent_sync_extensions.md)

- Backoff Signals: Agents are explicitly told to pause based on system or agent health
- Load Smoothing: Randomized heartbeats and sync intervals to prevent traffic spikes
- Failure Pattern Tracking: Rolling agent reliability scores impact task assignment
- Lease Expiry & Reclaim: TTL-based Redis tracking for automatic task reclamation
- Agent Local Heuristics: Agents throttle themselves based on temp, load, or guessrate

### **Agent Collaboration Model** [Agent-Server Collaboration Vision](agent-server-collaboration-vision.md)

- Structured Status Streaming via `/status` with `--status-json` parsing
- Self-Tuning Agents adjust workload profile (`-w`) and runtime params dynamically
- Offline Recovery: Agents checkpoint slice metadata mid-task; server accepts partial completion
- Live Plan Adjustment: Server adapts slice sizing and prioritization in real time
- Crack Feedback Loop: Successful cracks influence dictionary/rule/mask strategy
- Performance History: Server models agent capabilities per hash type
- Capability Signaling: Agents report hash type support, memory, load
- Optional: Agent Karma, Slice Replay, DAG Auto-Growth

### **Hard Password Attack Intelligence** [Hard Password Attack Strategies](hard_password_attack_strategies.md)

- **Dynamic Wordlists**: Meta-wordlists, frequency sorting, crack-informed candidates

- **Rule Learning & Debug Parsing**: Derive rules from cracked pairs and `--debug-mode=3` - [See Learned Rules Parser Plan](learned_rules_parser_plan.md)

- **Markov Modeling**: Automatic hcstat2 generation per project; opt-in UI toggle - [See Markov Auto-Generation Plan](markov_autogen_plan.md)

- **PACK-Inspired Intelligence**:

  - Internal `maskgen`, `rulegen`, `statsgen`, `policygen` clones

- **Graph-Driven Campaigns**: DAG-style phased attack planning

- **LLM/Trigram Expansion**: AI-inspired password candidate generation

- **Advanced DAG Logic**:

  - Crack origin attribution
  - Entropy bucketing
  - DAG trimming or extension
  - Agent-affinity weighting
  - Hot slice promotion

---

## INTEGRATION THEMES

### Intelligence-Driven Strategy

- Project-aware wordlists, rules, and mask evolution
- Feedback from cracks, rejects, and agent behavior
- Environment-specific password morphology modeling

### Agent Self-Governance

- Dynamic resource tuning
- Autonomy in edge cases (overheating, reboots)
- Participation in planning via capability reporting and crack insight

### Fine-Grained Orchestration

- Per-slice telemetry, live reassignment, and execution tracing
- Fault-tolerant leasing
- DAG-based campaign modeling
- Background vs. primary task scheduling

### Observability & Learning

- Per-campaign attribution
- Rule effectiveness graphs
- Cracked-password pattern clustering
- Slice replay for debug/forensics

---

## Immediate Implementation Tracks

| Track                     | Scope                                                         |
| ------------------------- | ------------------------------------------------------------- |
| **TaskPlanner v2**        | WorkSlice slicing, phase-aware scheduling, skip/limit support |
| **AgentStatusStream**     | `/status` SSE or chunked POST for JSON parsing + metrics      |
| **Rule Learning + Debug** | Parse `--debug-mode=3` outputs into rule frequency maps       |
| **Markov Pipeline**       | Project-local hcstat2 generation + Mask Editor checkbox       |
| **PACK-like Modules**     | Native versions of maskgen, rulegen, statsgen, policygen      |
| **Feedback DAG Engine**   | Auto-promotion, DAG trimming, and hot-slice escalation logic  |
| **Agent Lease & Health**  | TTL leases, reclaim logic, sync jitter, failure scoring       |

---

## Suggested Skirmish Sequence

1. ✅ Extend TaskPlan + WorkSlice model
2. ✅ Implement lease tracking + reclaim worker
3. ✅ Implement Markov stats + hcstat2 autogen
4. ✅ Add debug rule parser → learned.rules
5. ✅ Build `/status` endpoint + log pipeline
6. ✅ Add PACK-core modules: mask, rule, stats
7. ✅ Add DAG node scoring + trigger logic
