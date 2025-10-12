# Ouroboros v2: Intent and Strategic Direction

## 🔄 Context & Motivation

Ouroboros v2 is a full rewrite of the original Ouroboros project (legacy Ruby on Rails + Hotwire UI). The legacy system was functional but limited — it provided basic agent/task control and some UI affordances, but was hard to scale, automate, or modernize.

The rewrite is about more than just porting code. It's a shift in philosophy:

- From _a tool_ to _a platform_
- From _manual config_ to _guided workflows_
- From _hard-to-debug_ to _live feedback and observability_

We're building this for red team operators, system admins, and long-term maintainability — with the flexibility to grow into automation, integration, and multi-user coordination.

---

## ✅ Design Intent by Feature

### 🧠 **Live Agent Monitoring**

- **Intent:** Give users and admins better visibility into what's really happening with agents — speed, utilization, errors, job assignments.
- **Pain Point Solved:** In v1, it was unclear if agents were alive or doing anything meaningful.
- **What We Built:** Real-time telemetry, performance graphs, per-agent tabs (settings, performance, errors, capabilities).

### 🛠️ **Redesigned Attack Editor**

- **Intent:** Make the creation and tuning of attacks easier and more approachable for both non-experts and power users.
- **Pain Point Solved:** v1 used a massive form with all hashcat options shown at once. It was overwhelming.
- **What We Built:** Modal-based editors with attack-specific fields, live keyspace/complexity estimates, intuitive modifiers, and JSON import/export.

### 🎯 **Campaign Dashboard & Orchestration**

- **Intent:** Make campaign state and flow easier to control, understand, and monitor.
- **Pain Point Solved:** v1 had poor visibility into attack order, lifecycle, or status.
- **What We Built:** Live progress indicators, sortable/controllable attack tables, editable metadata, and start/stop toggles.

### 📂 **Inline Resource Management**

- **Intent:** Let users iteratively refine resources without having to download, edit, and re-upload files repeatedly.
- **Pain Point Solved:** Editing a wordlist or mask required deleting and recreating linked attacks.
- **What We Built:** In-browser editing for wordlists, masks, and rules with line validation, metadata previews, and size-based gating.

### 🔓 **Crackable Uploads (in progress)**

- **Intent:** Simplify cracking workflows for less-technical users by handling extraction, validation, and attack building automatically.
- **Pain Point Solved:** Users had to manually extract hashes and guess types before running attacks.
- **What We're Building:** Upload UI that accepts files or pasted hash dumps, detects hash types, and pre-generates attacks.

### 🧪 **Infrastructure & Testing**

- **Intent:** Build a stable, testable foundation that’s easier to maintain and extend.
- **Pain Point Solved:** The v1 stack was brittle, poorly modularized, and hard to test.
- **What We Built:** Switched to `psycopg`, added browser-based tests with Playwright, improved API typing and error handling, and cleaned up the justfile/dev environment.

### 🧑‍💻 **Control API + TUI**

- **Intent:** Provide a scriptable, headless interface for red team automation and CLI use.
- **Pain Point Solved:** v1 had no CLI/TUI or integration interface.
- **What We're Building:** A full Control API with planned Textual-based TUI client; will support scripting, outside system integration, and role-scoped control surfaces.

---

## 🧭 Strategic North Star

Ouroboros v2 isn't just about cracking faster — it's about cracking **smarter**:

- Give users the tools they need without making them learn internals
- Make live feedback and visibility the default
- Design for automation, auditability, and multi-user coordination

This rewrite is where the platform becomes real.
