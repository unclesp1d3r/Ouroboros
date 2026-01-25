# Ouroboros Phase 5 - Agent Sync Extensions

---

## Table of Contents

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=2 --minlevel=1 -->

- [Ouroboros Phase 5 - Agent Sync Extensions](#ouroboros-phase-5---agent-sync-extensions)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [Feature: Backoff Signals](#feature-backoff-signals)
  - [Feature: Load Smoothing Hooks](#feature-load-smoothing-hooks)
  - [Feature: Failure Pattern Tracking](#feature-failure-pattern-tracking)
  - [Feature: Lease Expiry & Reclaim](#feature-lease-expiry--reclaim)
  - [Optional: Agent Local Heuristics](#optional-agent-local-heuristics)
  - [Summary](#summary)

<!-- mdformat-toc end -->

---

## Overview

This document outlines planned enhancements to Ouroboros's agent heartbeat and coordination system. These features aim to make the platform more resilient, adaptive, and aware of environmental conditions, particularly in trusted lab environments with mixed agent quality and workloads.

Agent Sync Extensions are complementary to Phase 5's enhanced task scheduler but can be developed and deployed independently.

---

## Feature: Backoff Signals

### Purpose

Allows the server to explicitly instruct agents to back off when they are overloading the system, overheating, or behaving poorly.

### Implementation

- Extend `/heartbeat` and `/pickup` responses with optional `backoff_seconds` field:

```json
{
  "status": "ok",
  "backoff_seconds": 30
}
```

- Agent sleeps for `backoff_seconds` before retrying heartbeat or pickup.

- Server emits backoff if:

  - Agent is overheating.
  - Agent has recently failed several tasks.
  - Redis/server health indicates high load.

### Notes

- Backoff cap can be enforced by agent (e.g. max 120s).
- Randomized jitter can avoid herding effect.

---

## Feature: Load Smoothing Hooks

### Purpose

Avoid sync spikes from agents performing periodic `/heartbeat` at the same time.

### Implementation

- Agents generate a randomized sync interval on first run (e.g. 10–30s).
- Report their next sync interval during `/heartbeat`.
- Server can use this to stagger slice distribution and telemetry flow.

### Optional

- Server can suggest next `sync_interval` on response to further deconflict.

---

## Feature: Failure Pattern Tracking

### Purpose

Detect flaky or failing agents and penalize them during scoring.

### Implementation

- Track per-agent stats:

  - `success_count`, `fail_count`, `timeout_count`

- Derive a rolling reliability score:

```python
reliability = success_count / (success_count + fail_count + timeout_count)
```

- Include in AgentScorer to reduce task assignment priority.
- Optional UI badge:

```text
[GREEN] Stable (97%)
[YELLOW] Intermittent (82%)
[RED] Flaky (42%)
```

---

## Feature: Lease Expiry & Reclaim

### Purpose

Reclaim tasks from agents that crash or silently go offline during execution.

### Implementation

- All slice leases tracked in Redis (`task:lease:AGENT_ID:SLICE_ID`).

- TTL set to `max_task_duration + 15% buffer`.

- Background job scans expired leases every 10s.

- Expired leases trigger:

  - Slice unassignment.
  - Optionally mark task as `stalled` or `orphaned`.

---

## Optional: Agent Local Heuristics

### Purpose

Empower agents to self-throttle or report degraded conditions.

### Ideas

- If `temperature > 90°C` → skip next pickup.
- If guess rate drops below 25% of benchmark → warn or sleep.
- If system load average > 8.0 → backoff automatically.

### Goal

Not a replacement for orchestrator logic, but adds "politeness" in heterogeneous or noisy environments.

---

## Summary

These sync extensions provide a robust framework for smarter agent orchestration and health tracking without introducing external dependencies. When combined with enhanced task planning, they form the foundation of a fully adaptive distributed cracking system.
