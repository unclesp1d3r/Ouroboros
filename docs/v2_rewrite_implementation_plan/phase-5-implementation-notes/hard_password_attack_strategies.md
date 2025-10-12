# Ouroboros Phase 5 - Hard Password Attack Strategies

---

## Table of Contents

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=3 --minlevel=1 -->

- [Ouroboros Phase 5 - Hard Password Attack Strategies](#ouroboros-phase-5---hard-password-attack-strategies)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [Smarter Dictionaries](#smarter-dictionaries)
    - [Context-Aware Meta-Wordlist](#context-aware-meta-wordlist)
    - [Frequency-Weighted Wordlist Reordering](#frequency-weighted-wordlist-reordering)
  - [Rule Mutation and Discovery](#rule-mutation-and-discovery)
    - [Dynamic Rule Learning](#dynamic-rule-learning)
    - [Failure-Driven Rule Mutation](#failure-driven-rule-mutation)
  - [Feedback-Driven Attacks](#feedback-driven-attacks)
    - [Loopback-Like Candidate Promotion](#loopback-like-candidate-promotion)
  - [Graph-Based Planning](#graph-based-planning)
    - [Attack DAGs (Directed Acyclic Graphs)](#attack-dags-directed-acyclic-graphs)
  - [Markov Modeling](#markov-modeling)
    - [Markov Chain Resynthesis (Deeper Dive)](#markov-chain-resynthesis-deeper-dive)
  - [LLM-Inspired Expansion](#llm-inspired-expansion)
    - [Machine-Generated Candidates](#machine-generated-candidates)
  - [PACK-Style Adaptive Mask and Rule Integration](#pack-style-adaptive-mask-and-rule-integration)
    - [Internal `maskgen` Equivalent](#internal-maskgen-equivalent)
    - [Internal `rulegen` Equivalent](#internal-rulegen-equivalent)
    - [Internal `statsgen` Equivalent](#internal-statsgen-equivalent)
    - [Internal `policygen` Equivalent](#internal-policygen-equivalent)
  - [Rule-Based Effectiveness from Debug Output](#rule-based-effectiveness-from-debug-output)
    - [Data Captured](#data-captured)
    - [Uses](#uses)
    - [Benefits](#benefits-1)
  - [Strategic Enhancements & Forward Tactics](#strategic-enhancements--forward-tactics)
    - [Crack Origin Attribution](#crack-origin-attribution)
    - [Crack Replay Mode](#crack-replay-mode)
    - [Entropy Bucketing for Hashlists](#entropy-bucketing-for-hashlists)
    - [Agent-Weighted Hash Affinity](#agent-weighted-hash-affinity)
    - [Campaign Similarity Inference](#campaign-similarity-inference)
    - [Hot Slice Prioritization](#hot-slice-prioritization)
    - [Agent-Assisted DAG Growth](#agent-assisted-dag-growth)
  - [Bonus Tactics](#bonus-tactics)
  - [Summary](#summary)

<!-- mdformat-toc end -->

---

## Overview

This document outlines advanced techniques for targeting difficult-to-crack passwords within Ouroboros. These strategies build on insights from over 50,000 previously recovered passwords and propose a framework for leveraging those successes to crack harder, more resistant hashes.

The focus is on smarter wordlists, adaptive rules, and feedback-informed attack planning. These techniques are complementary to the meta-dictionary strategy and can be integrated into Ouroboros as part of Phase 5 enhancements.

---

## Smarter Dictionaries

### Context-Aware Meta-Wordlist

- Parse recovered passwords into base forms (words, years, patterns).

- Cluster by type: `base + symbol`, `leet`, `base + year`, `name + digit`.

- Generate new candidates using templates:

  - `[word] + [year]`
  - `[leetified(word)] + [symbol]`
  - `[common_prefix] + [name]`

### Frequency-Weighted Wordlist Reordering

- Track how often words or patterns appear in cracked passwords.
- Sort future dictionaries by hit frequency.
- Prioritize reuse of high-value candidates.

---

## Rule Mutation and Discovery

### Dynamic Rule Learning

- Derive rule transformations from cracked hash pairs.
- Store frequency of rule usage.
- Generate environment-specific rule files (e.g., `top_128_rules.learned`).

### Failure-Driven Rule Mutation

- When a slice yields no cracks, mutate the attack:

  - Reverse dictionary
  - Add prefix/suffix
  - Leetify
  - Change charset

- Retry as fallback with altered ruleset.

---

## Feedback-Driven Attacks

### Loopback-Like Candidate Promotion

- Monitor slices that yield no cracks but high rejection or format match rates.
- Promote candidates with high rejection counts to priority testing.
- Useful for salted formats and near-miss passwords.

---

## Graph-Based Planning

### Attack DAGs (Directed Acyclic Graphs)

- Design campaign flows as graph stages:

  ```text
  [dict base] → [dict+rules] → [mask variants] → [markov/brute]
  ```

- Promote cracked results from one phase to next phase dictionary.

- Automatically trigger dependent nodes upon partial success.

---

## Markov Modeling

### Markov Chain Resynthesis (Deeper Dive)

Hashcat's Markov mode prioritizes guesses based on statistical likelihood using an `.hcstat2` file. This file models:

- **Position frequency**: Which characters appear most at each position.
- **Transition frequency**: Given character `c`, what likely comes next.

#### Ouroboros Usage

- Ouroboros will generate per-project `hcstat2` files from cracked passwords.
- These will be stored and versioned for each campaign or hashlist.
- Markov-based brute-force will be an *opt-in checkbox* in the Mask Attack Editor UI, requiring no special knowledge to activate.

#### Benefits

- Prioritizes high-probability guesses.
- Efficient for long passwords or speculative brute-force.
- Adapts to organization- or dataset-specific patterns.

#### Automation Plan

- Background job scans new cracked passwords.
- Updates Markov stats incrementally.
- Optionally purges low-signal data.
- Triggers regeneration of `project.hcstat2` when thresholds are met.

#### UI & DAG Integration

- Markov brute-force appears as a post-mask fallback in DAGs.

- Editor UI will include:

  - ☑️ Use adaptive Markov model (recommended)
  - ℹ️ Tooltip: “Prioritizes likely guesses using real cracked data.”

---

## LLM-Inspired Expansion

### Machine-Generated Candidates

- Train trigram models or use LLMs to morph known cracked passwords.
- Generate new dictionary candidates matching observed structure.
- Filter through validation (e.g., mask structure, length limits).

---

## PACK-Style Adaptive Mask and Rule Integration

Ouroboros will natively integrate PACK-style tools to make cracking more adaptive and self-tuning. Rather than rely on aging external scripts, Ouroboros will embed the following capabilities directly into the platform:

### Internal `maskgen` Equivalent

- Analyze recovered passwords using internal character class recognition.
- Derive high-frequency structural masks (`?l?l?l?d?d?s`, etc).
- Store masks per project as `SuggestedMasks`.
- Auto-use in post-dictionary DAG phase.

### Internal `rulegen` Equivalent

- Compare cracked passwords to dictionaries used.
- Extract hashcat-compatible rules via diffing.
- Rank by frequency and success rate.
- Offer to users as `learned.rules` file or auto-include in templates.

### Internal `statsgen` Equivalent

- Use cracked passwords to create Markov transition stats.
- Build and cache project-local Markov models.
- Enable project-specific `--markov` attacks that mimic prior success.

### Internal `policygen` Equivalent

- Infer probable password policies from cracked sample:

  - Required charsets
  - Minimum and maximum length

- Use this info to filter out bad masks or rulefiles.

- Warn if attack parameters violate inferred policy.

---

## Rule-Based Effectiveness from Debug Output

Ouroboros will leverage hashcat’s `--debug-mode` output (specifically mode 3) to analyze how cracked passwords were transformed from base dictionary inputs.

### Data Captured

- Base word
- Cracked word
- Rule used
- Hash type and attack ID

### Uses

- Score rules by frequency and success rate
- Identify which rules are effective per project
- Build heat maps of rule performance
- Associate rules with time/guess cost (per slice)
- Create campaign-specific rule pruning logic

### Benefits

- Turns cracked data into empirical rule scoring
- Optimizes rulefile generation dynamically
- Helps identify bad or ineffective rules fast

---

## Strategic Enhancements & Forward Tactics

### Crack Origin Attribution

- For each cracked hash, log the originating dictionary/rule/mask/slice.
- Generate campaign-wide success attribution reports.
- Use results to prune ineffective DAG paths.

### Crack Replay Mode

- Export a slice config and cracked hash for reproduction.
- Useful for triage, debugging, or auditing unusual results.

### Entropy Bucketing for Hashlists

- Separate easy vs. hard hashes based on crack rate and structure.
- Target each class with different strategies.
- Can suppress brute-force on high-entropy tail.

### Agent-Weighted Hash Affinity

- Score agents per hash type based on performance history.
- Prefer high-performing agents for high-cost tasks (e.g. bcrypt).

### Campaign Similarity Inference

- Detect similarity between current project and historical ones.
- Offer to re-use past DAGs, learned rules, and masks.

### Hot Slice Prioritization

- If a slice cracks multiple hashes early, escalate its siblings.
- Temporarily pause low-priority jobs to accelerate productive slices.

### Agent-Assisted DAG Growth

- Agents may flag novel patterns discovered mid-task.
- Server can inject new DAG nodes for deeper exploration.

---

## Bonus Tactics

- **Success-Weighted Agent Assignment**: Assign faster agents to high-potential attacks, others to speculative or background jobs.
- **Hash Clustering**: Group hashes by length, format, or similarity; tailor attacks per cluster.
- **Slice Convergence Detection**: Auto-cancel attack paths if multiple consecutive slices fail.

---

## Summary

These strategies turn Ouroboros from a traditional orchestrator into an adaptive, learning, and feedback-driven cracking engine. The best passwords to crack are the ones that teach you how to crack the rest. By folding every success and failure back into the system, Ouroboros stays ahead of static dictionaries and rulesets.
