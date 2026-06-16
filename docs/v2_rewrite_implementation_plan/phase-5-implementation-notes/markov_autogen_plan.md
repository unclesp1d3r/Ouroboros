# Ouroboros Phase 5 - Markov Model (hcstat2) Auto-Generation

---

## Table of Contents

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=2 --minlevel=1 -->

- [Ouroboros Phase 5 - Markov Model (hcstat2) Auto-Generation](#ouroboros-phase-5---markov-model-hcstat2-auto-generation)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [Purpose of hcstat2](#purpose-of-hcstat2)
  - [Auto-Generation Strategy](#auto-generation-strategy)
  - [UI Integration](#ui-integration)
  - [Model Object](#model-object)
  - [Internal Markov Generator: `markov_statsgen()` Design](#internal-markov-generator-markov_statsgen-design)
  - [Future Enhancements](#future-enhancements)

<!-- mdformat-toc end -->

---

## Overview

This document defines how Ouroboros will automatically generate and evolve `hcstat2` files used for Markov-mode brute-force attacks. These models are built from recovered passwords and used to prioritize high-probability guesses during mask-based cracking. Markov support will be seamlessly integrated into the Brute-Force Attack configuration.

An internal implementation based on PACK’s `statsgen` will be developed and maintained by Ouroboros to ensure performance, correctness, and long-term support.

---

## Purpose of hcstat2

Hashcat’s `--markov` mode uses `.hcstat2` files to:

- Rank character choices at each password position (positional frequency)
- Score transitions from one character to the next (n-gram chain likelihood)
- Optimize brute-force attack ordering for efficiency

These models dramatically improve cracking performance for long or unknown-structure passwords.

---

## Auto-Generation Strategy

### 🧬 Initial Seeding

- Use prebuilt seed corpora:

  - Aspell dictionaries for: English, Spanish, French, German, Russian
  - RockYou or similar as default training base

- System will generate:

  - `global_default.hcstat2`
  - Language-specific variants (`hcstat2_en`, `hcstat2_de`, etc.)

### Per-Project Evolution

- Every project has a local `project.hcstat2` file

- This file evolves over time based on cracked password submissions

- Generation is triggered by:

  - Threshold (e.g. ≥100 new cracks)
  - Stale model (older than 48 hours)
  - Manual admin override

### 🔁 Background Job: `update_markov_model(project_id)`

- Collect all known `CrackedPassword` values for a project
- Feed into internal `markov_statsgen()` engine
- Generate new `.hcstat2` binary blob
- Store in cache and/or on disk
- Update `ProjectMarkovModel` metadata

---

## UI Integration

### Brute-Force Attack Editor

```text
☑️ Enable Smart Guess Ordering
     ( ) Use this project’s learned model
     ( ) Use default global model
     ( ) Upload custom Markov model

ℹ️ Tooltip: "Smart Guess Ordering prioritizes likely character patterns using your cracked passwords. Known as 'Markov mode' in Hashcat."
```

### Visual Aids (Future)

- Histogram preview of most probable mask shapes
- Char transition matrix preview (top N transitions)

---

## Model Object

### `ProjectMarkovModel`

| Field        | Type         | Description                           |
| ------------ | ------------ | ------------------------------------- |
| id           | int          |                                       |
| project_id   | FK → Project |                                       |
| version      | str          | e.g. `v1`, `v2`, `hcstat2-r1`         |
| generated_at | datetime     | Timestamp of last build               |
| model_path   | str          | Location of `.hcstat2` binary         |
| input_cracks | int          | How many passwords it was trained on  |
| seed_source  | str          | e.g. `rockyou`, `aspell_en`, `custom` |

---

## Internal Markov Generator: `markov_statsgen()` Design

### Purpose

Create a dependency-free, reproducible generator for `.hcstat2` files used in Markov-mode brute-force attacks.

### Input

- List of recovered passwords (strings)
- Charset specification (ASCII, UTF-8, etc.)
- Max character positions (default 15–20)

### Output

- Binary `.hcstat2` blob matching Hashcat's format
- Summary data: character position frequency and char transitions

### Steps

1. **Preprocessing**

   - Normalize inputs (optional lowercase, printable-only)
   - Group by length (if needed for analysis)

2. **Positional Frequency Table**

```python
position_freq[pos][char] += 1
```

Example for `password`:

```text
position_freq[0]['p'] += 1
position_freq[1]['a'] += 1
...
```

1. **Transition Frequency Table**

```python
transition_freq[prev_char][next_char] += 1
```

Captures common bigram transitions like `'s' → 's'`, `'a' → 's'`, etc.

1. **Encoding**

- Format into `.hcstat2` binary layout:

  - Header/version block
  - Char index map
  - Positional table (256 × N positions)
  - Transition matrix (256 × 256)
  - All weights as 16-bit integers

1. **Return**

- Binary bytes (`bytes`)
- Metadata: number of entries, top transitions, charset used

---

## Future Enhancements

- Language detection from cracked passwords (auto-tune seed dictionaries)
- Cross-project `hcstat2` fusion (for global DAG attacks)
- Weighting recent cracks higher than older ones
- Live Markov model preview in campaign editor
- Scheduled model rotation for time-limited training sets
