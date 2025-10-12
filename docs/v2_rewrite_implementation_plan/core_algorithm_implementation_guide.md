# Ouroboros: Skirmish Implementation Guide - Progress, Compatibility, and Task Assignment

This guide documents key algorithms from the legacy Ouroboros system that must be reimplemented or updated for the new FastAPI + PostgreSQL backend. It provides functional requirements and implementation notes for Skirmish.

---

<!-- mdformat-toc start --slug=gitlab --no-anchors --maxlevel=4 --minlevel=2 -->

- [1. Agent Benchmark Compatibility](#1-agent-benchmark-compatibility)
  - [✅ Functionality](#-functionality)
  - [💡 What Are Hashcat Benchmarks?](#-what-are-hashcat-benchmarks)
  - [💡 Implementation](#-implementation)
  - [🔧 Method Signature](#-method-signature)
- [2. State Machines (Campaign to Attack to Task)](#2-state-machines-campaign-to-attack-to-task)
  - [✅ Functionality](#-functionality-1)
  - [🔧 Method Signatures](#-method-signatures)
- [3. Progress Calculation (Percent-Based)](#3-progress-calculation-percent-based)
  - [✅ Functionality](#-functionality-2)
  - [🔧 Method Signatures](#-method-signatures-1)
- [3B. Keyspace-Weighted Progress Calculation (Enhanced)](#3b-keyspace-weighted-progress-calculation-enhanced)
  - [✅ Why Weight by Keyspace?](#-why-weight-by-keyspace)
- [4. Task Assignment Algorithm](#4-task-assignment-algorithm)
  - [✅ Functionality](#-functionality-3)
  - [🔧 Method Signature](#-method-signature-1)
  - [🔒 Requirements](#-requirements)
- [5. Hash Crack Result Aggregation](#5-hash-crack-result-aggregation)
  - [✅ Functionality](#-functionality-4)
  - [🔧 Aggregates](#-aggregates)
- [6. Edge Cases](#6-edge-cases)
- [7. Keyspace Estimation (All Attack Types)](#7-keyspace-estimation-all-attack-types)
  - [✅ Functionality](#-functionality-5)
  - [💡 What is Keyspace?](#-what-is-keyspace)
  - [💡 Implementation](#-implementation-1)
  - [🔧 Method Signature](#-method-signature-2)
  - [🧪 Validation](#-validation)
  - [🔒 Requirements](#-requirements-1)
  - [📎 Related Features](#-related-features)
- [✅ Implementation Order](#-implementation-order)

<!-- mdformat-toc end -->

---

## 1. Agent Benchmark Compatibility

### ✅ Functionality

Determine whether an agent is compatible with a given hash type.

### 💡 What Are Hashcat Benchmarks?

Hashcat benchmarks are performance tests that measure how many hashes per second an agent's hardware can process for each supported hash type. These benchmarks:

- Are collected during agent registration or re-benchmarking
- Indicate agent capability for each hash type
- Are used to **determine eligibility for specific attacks**
- Provide **relative performance estimates** that can be used for **load balancing**

This allows Ouroboros to distribute work intelligently, avoiding weaker agents for resource-heavy tasks and splitting work proportionally across stronger ones.

### 💡 Implementation

Agents store benchmark results in the format:

```json
{
  "hash_type_id": 0,
  "speed": 1234.5
}
```

### 🔧 Method Signature

```python
def can_handle_hash_type(agent: Agent, hash_type_id: int) -> bool:
    return hash_type_id in agent.benchmark_map
```

Benchmarks should be stored in a DB field or table, indexed by hash type. Agents without benchmark data for a hash type are ineligible.

---

## 2. State Machines (Campaign to Attack to Task)

### ✅ Functionality

Each object in the hierarchy calculates its completion based on its children.

- `Task`: complete if progress is 100% or a result has been submitted
- `Attack`: complete if all Tasks are complete
- `Campaign`: complete if all Attacks are complete

### 🔧 Method Signatures

```python
def task_is_complete(task: Task) -> bool:
    return task.progress_percent == 100 or task.result_submitted


def attack_is_complete(attack: Attack) -> bool:
    return all(task_is_complete(t) for t in attack.tasks)


def campaign_is_complete(campaign: Campaign) -> bool:
    return all(attack_is_complete(a) for a in campaign.attacks)
```

Each level should also store a calculated progress percentage (see next section).

---

## 3. Progress Calculation (Percent-Based)

### ✅ Functionality

Higher-level progress is calculated as the average of lower-level progress.

### 🔧 Method Signatures

```python
def attack_progress(attack: Attack) -> float:
    if not attack.tasks:
        return 0.0
    return sum(t.progress_percent for t in attack.tasks) / len(attack.tasks)


def campaign_progress(campaign: Campaign) -> float:
    if not campaign.attacks:
        return 0.0
    return sum(attack_progress(a) for a in campaign.attacks) / len(campaign.attacks)
```

---

## 3B. Keyspace-Weighted Progress Calculation (Enhanced)

### ✅ Why Weight by Keyspace?

Not all tasks are equal — some take longer than others due to larger keyspaces. If we just average `progress_percent`, a small task at 100% can skew results.

Instead, weight each task’s progress by its total keyspace:

```python
def attack_progress(attack: Attack) -> float:
    total_keyspace = sum(t.keyspace_total for t in attack.tasks)
    if total_keyspace == 0:
        return 0.0
    weighted_sum = sum(
        (t.progress_percent / 100.0) * t.keyspace_total for t in attack.tasks
    )
    return (weighted_sum / total_keyspace) * 100.0
```

Campaign progress would then be calculated from weighted attack progress, or further weighted by total attack keyspace.

---

## 4. Task Assignment Algorithm

### ✅ Functionality

Assigns pending tasks to available agents based on hash type compatibility.

### 🔧 Method Signature

```python
def assign_task_to_agent(agent: Agent) -> Optional[Task]:
    for task in get_pending_tasks():
        if can_handle_hash_type(agent, task.attack.hash_type_id):
            return task
    return None
```

### 🔒 Requirements

- Task must be in `pending` state
- Agent must have benchmark support for the task’s hash type
- Only one active task per agent at a time

---

## 5. Hash Crack Result Aggregation

### ✅ Functionality

Track cracked hash counts for UI and export.

### 🔧 Aggregates

- `hash_list.hash_items.count()`
- `hash_list.hash_items.filter(cracked=True).count()`
- `campaign.total_cracked` = sum of cracked items across associated hash lists

Use indexes on `HashItem.cracked` for performance.

---

## 6. Edge Cases

- Agents without benchmark data should be flagged and not assigned work
- Tasks with 0 `keyspace_total` should be logged and excluded
- Cracked hashes submitted twice should be deduplicated
- Failed tasks should trigger retries or manual reassignment

## 7. Keyspace Estimation (All Attack Types)

### ✅ Functionality

Estimate the total keyspace for a given attack configuration. This enables Ouroboros to:

- Predict total cracking time
- Support progress tracking and weighted aggregation
- Display attack difficulty and ETA in the UI
- Precompute task sizes for agent scheduling

Keyspace estimation must handle **dictionary**, **mask**, **combinator**, **hybrid**, and **incremental** modes, as well as **rulesets** and **custom charsets**.

### 💡 What is Keyspace?

Keyspace is the total number of password candidates an attack will generate. For any attack, the cracking time can be estimated as:

```text
ETA = (keyspace_total - keyspace_progressed) / hashes_per_second
```

This works across all hashcat attack modes by adjusting how the keyspace is calculated.

---

### 💡 Implementation

Each attack mode has its own formula:

| Attack Mode      | Keyspace Formula                                       |
| ---------------- | ------------------------------------------------------ |
| Dictionary       | `len(wordlist)`                                        |
| Mask             | `∏ charset_length(pos_i)`                              |
| Incremental Mask | `Σ (∏ charset_length(pos_i))` for each length in range |
| Combinator       | `len(left_wordlist) * len(right_wordlist)`             |
| Hybrid 6         | `len(wordlist) * mask_keyspace`                        |
| Hybrid 7         | `mask_keyspace * len(wordlist)`                        |
| Rules applied    | Multiply total keyspace by `len(ruleset)`              |

This logic is best encapsulated in a single utility service:

```python
class KeyspaceEstimator:
    def estimate(self, attack: Attack, resources: AttackResources) -> int:
        # Dispatch to mode-specific estimator
        ...

    def _estimate_mask(
        self,
        mask: str,
        custom_charsets: dict[str, str],
        increment: bool,
        min_len: int,
        max_len: int,
    ) -> int:
        # Calculate product of charset lengths per position
        # If increment, sum across length range
        ...

    def _estimate_dictionary(self, wordlist_size: int, rule_count: int) -> int:
        return wordlist_size * rule_count

    def _estimate_combinator(self, left_size: int, right_size: int) -> int:
        return left_size * right_size

    def _estimate_hybrid(
        self, mode: Literal[6, 7], wordlist_size: int, mask_keyspace: int
    ) -> int:
        return (
            wordlist_size * mask_keyspace
            if mode == 6
            else mask_keyspace * wordlist_size
        )
```

This allows you to precompute `attack.keyspace_total` on attack submission and store it for use in task distribution and progress reporting.

---

### 🔧 Method Signature

```python
def estimate_keyspace(attack: Attack, resources: AttackResources) -> int: ...
```

Where `AttackResources` includes:

```python
@dataclass
class AttackResources:
    wordlist_size: int
    rule_count: int
    left_wordlist_size: Optional[int] = None
    right_wordlist_size: Optional[int] = None
    mask: Optional[str] = None
    custom_charsets: dict[str, str] = field(default_factory=dict)
    increment: bool = False
    increment_min: int = 1
    increment_max: int = 0
```

---

### 🧪 Validation

- Compare results to `--keyspace` output from hashcat for known configurations
- Unit test edge cases: empty mask, multi-mask with custom charsets, large rule sets
- Ensure invalid or malformed inputs return `0` or raise validation errors

---

### 🔒 Requirements

- Must match hashcat’s actual candidate space within ±1%
- Required for task distribution, UI display, and progress weighting
- Must support multi-mode campaigns (combinator, hybrid, etc.)

---

### 📎 Related Features

- Weighted progress calculation 【see Section 3B】
- Agent scheduling based on chunked keyspace
- Web UI display of "estimated time remaining" and "difficulty score"
- API validation endpoint on attack submission

---

## ✅ Implementation Order

1. [ ] Agent benchmark ingestion & capability check
2. [ ] Task assignment endpoint & logic
3. [ ] Task completion detection
4. [ ] Attack & campaign progress calculation
5. [ ] Campaign & attack completion transitions
6. [ ] Hash crack aggregation

---

This guide is intended to serve as a reference and contract for implementing Ouroboros's orchestration logic in a stateless API model using FastAPI and SQLAlchemy.
