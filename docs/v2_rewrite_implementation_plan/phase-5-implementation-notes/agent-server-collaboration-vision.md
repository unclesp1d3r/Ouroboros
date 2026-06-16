# Ouroboros Phase 5 - Agent & Server Collaboration Vision

---

## Table of Contents

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=3 --minlevel=1 -->

- [Ouroboros Phase 5 - Agent & Server Collaboration Vision](#ouroboros-phase-5---agent--server-collaboration-vision)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [Agent as Observant Executor](#agent-as-observant-executor)
    - [Structured Status Streaming](#structured-status-streaming)
  - [Agent as Local Governor](#agent-as-local-governor)
    - [Self-Tuning Execution](#self-tuning-execution)
  - [Agent Fault Recovery](#agent-fault-recovery)
    - [Offline Slice Recovery](#offline-slice-recovery)
  - [Server as Strategic Coordinator](#server-as-strategic-coordinator)
    - [Live Plan Adjustment](#live-plan-adjustment)
    - [Crack Result Feedback Loop](#crack-result-feedback-loop)
  - [Performance Learning & Forecasting](#performance-learning--forecasting)
    - [Historical Agent Performance](#historical-agent-performance)
    - [Agent Capability Signaling](#agent-capability-signaling)
  - [Optional Concepts](#optional-concepts)
    - [Slice Replay for Debug](#slice-replay-for-debug)
    - [Agent Karma Score](#agent-karma-score)
    - [Adaptive Task Graphs](#adaptive-task-graphs)
  - [Summary](#summary)

<!-- mdformat-toc end -->

---

## Overview

This document outlines a future-forward vision for Phase 5 of Ouroboros: transforming agents into adaptive, observant, and partially autonomous nodes that work *with* the server, not *for* it. These ideas extend the Sync Extensions model by elevating both agent responsibility and server strategy.

The goal is a smarter, more cooperative distributed cracking system — one that adapts to real-world conditions, anticipates failure, and evolves over time.

---

## Agent as Observant Executor

### Structured Status Streaming

Agents will parse `--status-json` internally and emit structured telemetry on an interval (e.g. every 5s).

#### Fields to Stream

- Slice ID
- Total guesses completed
- Percent progress (relative to `--skip/--limit`)
- Cracked hashes (count + list)
- Device temperatures
- Guessrate per device
- Rejected guesses
- Host metadata (load average, memory, thermal status)

#### Protocols

- Stream to `/api/v2/client/status` via chunked POST or SSE
- Use JWT auth to tag source agent and project

#### Benefits

- Real-time dashboards
- Predictive failure detection
- Live slice reassignment if an agent lags
- Audit-grade traceability per slice

---

## Agent as Local Governor

### Self-Tuning Execution

Agent adjusts hashcat launch parameters based on:

- Thermal envelope
- Load average
- Historical guessrate vs benchmark

#### Adjustments

- Workload profile (`-w`) from 1 to 4
- Manual tuning of `-n`, `-u`, `-T` if available
- Preemptive cooldown mode if device crosses critical threshold

#### Benefits

- Avoids wasteful slicing
- Helps survive degraded environments (e.g. closet rigs)
- Reduces silent throttling artifacts

---

## Agent Fault Recovery

### Offline Slice Recovery

Agent writes a checkpoint file mid-task (e.g. every 15s) to disk:

- Last known hashcat status
- Command used
- Slice metadata

On restart:

- Agent uploads checkpoint to `/client/recover`

- Server may:

  - Mark slice `complete` if near 100%
  - Reassign remaining % as new slice
  - Flag slice as `recovered`

#### Benefits

- Prevents full slice loss during crash
- Enables graceful resumption
- Server doesn't need to re-calculate or guess slice state

---

## Server as Strategic Coordinator

### Live Plan Adjustment

Server tracks slice completion durations and guessrate over time. It dynamically adjusts:

- Slice size
- Assigned hash types
- Task priority

Server maintains slice history:

```json
{
  "slice_id": 42,
  "agent_id": 3,
  "duration": 68.2,
  "average_speed": "2.1 GH/s"
}
```

#### Benefits

- Better utilization
- Easier load spreading
- Can accelerate campaign completion by tuning on the fly

---

### Crack Result Feedback Loop

Each crack submission:

- Triggers UI toast
- Is written to dynamic wordlist for this project
- May influence future rule generation (loopback-inspired)

#### Server roles

- Deduplicate cracks
- Update stats
- Integrate with Attack templates for reuse

---

## Performance Learning & Forecasting

### Historical Agent Performance

Each agent stores hash-type-specific baseline speeds:

```json
{
  "hash_type": "sha512crypt",
  "benchmark": 80000,
  "recent_avg": 60000,
  "stdev": 5000
}
```

Server uses this to:

- Predict duration of unstarted attacks
- Estimate completion time for campaigns
- Alert on underperformance

---

### Agent Capability Signaling

Agents self-report:

- Supported hash types (via `--backend-info`)
- Disabled devices (opt-out, failed diagnostics)
- RAM, swap, CPU, GPU memory

Server uses this to prefilter `/pickup` results.

---

## Optional Concepts

### Slice Replay for Debug

- Server can export a slice config and replay it offline for debugging
- Useful for triaging slice errors or verifying crack speed issues

### Agent Karma Score

- Long-running performance metric
- Affects priority in slice selection (stable agents go first)
- UI badge: " Veteran" or "[WARN] Unstable"

### Adaptive Task Graphs

- Campaigns can be pre-planned as DAGs (mask length → fallback)
- Slices report status back to adjust execution order
- More useful in exploratory or speculative cracking

---

## Summary

By promoting the agent to an active peer — one that communicates, adapts, and recovers — Ouroboros unlocks a new generation of distributed cracking. This vision puts control where it belongs: in the hands of the orchestrator, informed by smart, situationally aware agents.
