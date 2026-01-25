# Ouroboros Phase 5 - Learned Rules from Debug Mode

---

## Table of Contents

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=2 --minlevel=1 -->

- [Ouroboros Phase 5 - Learned Rules from Debug Mode](#ouroboros-phase-5---learned-rules-from-debug-mode)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [Key Concepts](#key-concepts)
  - [Models](#models)
  - [Celery Task: `parse_and_score_debug_rules()`](#celery-task-parse_and_score_debug_rules)
  - [Promotion Heuristics](#promotion-heuristics)
  - [Future Enhancements](#future-enhancements)

<!-- mdformat-toc end -->

---

## Overview

This document defines how Ouroboros will extract, score, and promote Hashcat rules from `--debug-mode=3` output during rule-based attacks. The goal is to create a `learned.rules` set for each project that reflects the most successful transformation patterns used in cracking real-world passwords.

All operations are async and non-blocking. Agents offload debug artifacts to storage and immediately return to cracking. Server-side background jobs handle parsing and promotion.

---

## Key Concepts

### [x] Debug Artifact Submission

- Agents always run rule-based attacks with `--debug-mode=3`
- Output is compressed and uploaded to MinIO/S3
- Reference is returned as part of task completion payload
- Agent does not parse anything — it just pushes and forgets

### [x] Asynchronous Parsing

- Server records metadata in `SubmittedDebugArtifact`
- Celery job `parse_and_score_debug_rules(debug_file_url, task_id, project_id)` is queued
- Background worker fetches, decompresses, parses, scores, and promotes

---

## Models

### `SubmittedDebugArtifact`

Tracks agent-submitted debug files.

| Field        | Type         |
| ------------ | ------------ |
| id           | int          |
| project_id   | FK → Project |
| attack_id    | FK → Attack  |
| task_id      | FK → Task    |
| agent_id     | FK → Agent   |
| storage_url  | str          |
| compressed   | bool         |
| status       | enum         |
| submitted_at | datetime     |
| parsed_at    | datetime     |

### `RuleUsageLog`

Tracks how often rules are observed successfully.

| Field         | Type         |
| ------------- | ------------ |
| id            | int          |
| project_id    | FK → Project |
| rule          | str          |
| cracked_count | int          |
| hash_type     | int          |
| first_seen_at | datetime     |
| last_seen_at  | datetime     |

### `LearnedRule`

Stores promoted rules ready for attack use.

| Field               | Type         |          |
| ------------------- | ------------ | -------- |
| id                  | int          |          |
| project_id          | FK → Project |          |
| rule                | str          |          |
| score               | float        |          |
| source_count        | int          |          |
| auto_promoted       | bool         |          |
| last_updated        | datetime     |          |
| used_in_last_attack | bool         | datetime |

---

## Celery Task: `parse_and_score_debug_rules()`

### Steps

1. **Retrieve & Decompress**

   - Download debug file from MinIO/S3
   - Decompress (gzip/zstd)

2. **Parse Debug Entries**

   - Parse `<hash>:<base>:<cracked>:<rule>`
   - Extract `rule`, `hash_type`, `project_id`

3. **Update Rule Usage Log**

   - Upsert into `RuleUsageLog`
   - Increment `cracked_count`
   - Update `last_seen_at`

4. **Check for Promotion**

   - If `cracked_count >= threshold` (e.g., 3), promote to `LearnedRule`
   - Upsert with `auto_promoted = true`, update `score`

5. **Regenerate File (optional)**

   - If new rules were promoted, regenerate `learned.rules` for project
   - Save to disk or cache for use in future attacks

6. **Mark Artifact Parsed**

   - Set `status = parsed`
   - Set `parsed_at = now()`

---

## Promotion Heuristics

Ouroboros will promote rules into `learned.rules` based on observed cracking success, recency, and project relevance. The promotion logic is run by background tasks and incorporates rule aging, scoring, and deduplication.

### Promotion Criteria

A rule is promoted if:

- It has been observed cracking at least `MIN_COUNT = 3` distinct hashes
- Its most recent use is within `RECENT_DAYS = 60`
- The project has cracked at least `MIN_PROJECT_CRACKS = 50` hashes overall

Promotion is tracked per `(rule, hash_type)` to ensure hash-mode specificity.

### Dynamic Scoring

Every rule is assigned a `score` that reflects not just usage frequency, but also relative cost and freshness:

```python
score = (cracked_count / estimated_cost) * freshness_factor
```

Where:

```python
freshness_factor = (
    1.0 if days_since_last_seen < 30 else 0.5 if days_since_last_seen < 60 else 0.1
)
```

`estimated_cost` represents a normalized estimate of how much time or resource load the attack incurred when using that rule. Lower-cost, high-success rules rise in the rankings.

This score is used to:

- Sort the contents of `learned.rules`
- Trim stale rules from promotion pool
- Visualize rule effectiveness in UI
- Guide DAG-level rule prioritization### Filters (Pre-Promotion)
- [FAIL] Reject empty rules (`rule == ""`)
- [FAIL] Ignore rules with `cracked_count == 1`
- [FAIL] Optionally ignore rules on a project-wide blacklist

### 🔃 Re-Aggregation and Aging

Rules that no longer meet recency or usage thresholds may be:

- Aged off from the `LearnedRule` table
- Soft-deleted or archived for audit
- Retained but excluded from output until reactivated
- Rule seen ≥ 3 times with unique cracks
- Most recent occurrence within last 60 days
- Not already disabled or flagged as invalid

---

## Future Enhancements

Each `LearnedRule` will include a flag to indicate whether it was used in the most recent campaign. This supports active/dormant rule separation, and enables analytics on recent effectiveness.

### Rule Impact Feedback Loop

As DAGs execute, rule effectiveness will be monitored in real time. Rules with zero impact in recent DAG nodes may be deprioritized or rotated out. Conversely, rules that yield cracks mid-campaign may be reprioritized dynamically.

### 🔖 Campaign Attribution

Tag rules with the IDs of campaigns in which they were observed. This supports retrospective analysis, attribution scoring, and fine-grained DAG adaptation.

### 🧼 Cross-Agent Deduplication

Deduplicate debug entries across agents to ensure cleaner aggregate scoring. Prevent inflation of cracked_count by repeat submissions of the same crack from multiple agents.

### 🧿 Rule Explorer UI (Planned)

Expose rule frequency, score, and campaign context in the UI. Support:

- Rule tagging (disable, boost, isolate)
- Histogram visualizations
- Inline editing of `learned.rules` preview
- Score weighting by attack cost
- Deduplication across agents for same task
- Tagging rules with campaign ID for attribution
- UI rule explorer with frequency visualizations
