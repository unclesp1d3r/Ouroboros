# Ouroboros System Health UX Design

Last updated: 2025-05-27

---

## Table of Contents

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=2 --minlevel=1 -->

- [Ouroboros System Health UX Design](#ouroboros-system-health-ux-design)
  - [Table of Contents](#table-of-contents)
  - [Purpose](#purpose)
  - [Layout Overview](#layout-overview)
  - [Service Status Cards](#service-status-cards)
  - [Design Considerations](#design-considerations)
  - [Real-Time Behavior](#real-time-behavior)
  - [Access Control](#access-control)
  - [Data Collection Strategy](#data-collection-strategy)
  - [Observability Notes](#observability-notes)
  - [Implementation Notes](#implementation-notes)

<!-- mdformat-toc end -->

---

## Purpose

The System Health page serves as an operational dashboard, offering immediate insights into the status and performance of critical backend services. It aims to facilitate proactive monitoring and swift issue identification, ensuring the reliability and efficiency of Ouroboros's infrastructure.

## Layout Overview

The page uses a **responsive grid layout**, with each service (MinIO, Redis, PostgreSQL) represented as a distinct **status card**. Each card provides real-time metrics and status indicators at a glance. The visual design is inspired by Flowbite's Server Status component, aligning with existing Ouroboros styling.

## Service Status Cards

In addition to backend services, this page also displays the current operational state of all registered agents. Agents are considered system-level participants and should be included in the health view.

### MinIO

- **Status Indicator**: [GREEN] Healthy, [YELLOW] Degraded, [RED] Unreachable (color-coded badge)

- **Metrics**:

  - Latency (API response time)
  - Errors (I/O and timeout count)
  - Storage Utilization (used vs total capacity)

- **Health Source**: `/minio/health/live` endpoint

### Redis

#### Redis via `redis.asyncio`

Use the official `redis-py` client with asyncio support (`redis.asyncio.Redis`) to gather metrics directly from memory. Do **not** use shell commands like `redis-cli`.

| Metric             | Method                            | Notes                               |
| ------------------ | --------------------------------- | ----------------------------------- |
| Up/Down State      | `await redis.ping()`              | Fast and safe health check          |
| Latency            | Manual timing of a simple command | e.g., `SET` or `GET` roundtrip time |
| Memory Usage       | `info()["used_memory"]`           | Returns bytes in use                |
| Active Connections | `info()["connected_clients"]`     | Useful for system health card       |
| Keyspace Stats     | `info("keyspace")`                | Admin-only detailed breakdown       |

> These values are readily available without external tooling and can be updated live via SSE polling or background jobs.

- **Status Indicator**: Color-coded badge

- **Metrics**:

  - Command Latency
  - Memory Usage
  - Active Connections

- **Health Source**: Redis INFO command and/or Prometheus

### PostgreSQL

#### PostgreSQL via `psycopg` + SQLAlchemy

Use the pooled connection support from `psycopg[binary,pool]` in combination with `SQLAlchemy 2.x` async session to query system stats safely. No shell commands should be used.

| Metric               | Query or Method                                       | Notes                                        |
| -------------------- | ----------------------------------------------------- | -------------------------------------------- |
| Up/Down State        | Try simple `SELECT 1` with timeout                    | Indicates connection availability            |
| Query Latency        | Time an example query execution                       | Consider averaging or sampling over interval |
| Connection Pool      | Use SQLAlchemy pool inspection tools                  | Or count active from `pg_stat_activity`      |
| Long-running Queries | `SELECT * FROM pg_stat_activity WHERE state='active'` | Admin-only display                           |
| Replication Lag      | `SELECT * FROM pg_stat_replication`                   | Shown only if replication is configured      |
| Background Workers   | `SELECT * FROM pg_stat_bgwriter`                      | Admin-only, useful for diagnosing slowdowns  |

> Data should be cached briefly (5–15s) if queried frequently. Limit admin-only data to a collapsed view by default.

- **Status Indicator**: Color-coded badge

- **Metrics**:

  - Query Latency
  - Connection Pool Usage
  - Replication Lag (if applicable)

- **Health Source**: PostgreSQL system views

### Agents

- **Status Indicator**: Color-coded badge ([GREEN] Online, [RED] Offline)

- **Metrics**:

  - Last seen timestamp
  - Current assigned task (if any)
  - Guess rate (if available)

- **Grouping**: Display as a collapsible section or in its own row below Redis/PostgreSQL

## Design Considerations

### Empty/Error State UX

- If a service cannot be reached, show a red badge and a concise message (e.g., “Redis unreachable — last seen 2m ago”).

- Use skeleton loaders during initial load.

- If no data is available for a metric, show a subtle placeholder (e.g., “N/A” or gray indicator) with tooltip explaining why.

- Align with style-guide.md (dark mode, purple accent, etc.)

- Use Flowbite + Shadcn-Svelte components

- Emphasize clarity and minimalism — show only relevant metrics

- Enable hover tooltips for metric definitions if space is tight

## Real-Time Behavior

### Update Strategy

- Live metrics should update every 5–10 seconds via SSE from the JSON API.

- Expensive queries (like object count or PostgreSQL WAL stats) should be cached for 30–60 seconds server-side.

- Consider staggered refresh intervals or jitter to avoid burst load after page load.

- SSE-driven live updates for all metrics

- Stale data indication if no update received in 30s

- Optional retry/backoff on failure, with error banners if a system is unreachable

## Access Control

### Admin Access Enhancements

Users with administrative privileges may see additional diagnostic data on this page, including:

- **MinIO**:

  - Bucket count and object totals
  - Disk I/O metrics

- **Redis**:

  - Keyspace breakdown (e.g., # keys by TTL)
  - Eviction stats

- **PostgreSQL**:

  - Long-running queries
  - Background worker stats
  - Write-ahead log (WAL) volume

This data is hidden for standard users to reduce clutter and limit sensitive system-level insight.

- Visible to all authenticated users
- Admins see more detailed metrics, logs, or advanced diagnostics

## Data Collection Strategy

> [WARN] Implementation Note: All system metrics should be gathered **from in-process Python code** using libraries or internal APIs.
>
> Do **not** shell out to external binaries or system commands to collect data in production.

| Service        | Python Access Notes                                                                     |
| -------------- | --------------------------------------------------------------------------------------- |
| **MinIO**      | Use `httpx` to query MinIO's `/health/live` endpoint or admin API with access keys      |
| **Redis**      | Use `redis.asyncio.Redis.info()` from `redis-py`                                        |
| **PostgreSQL** | Use async SQLAlchemy or `asyncpg` to run queries like `SELECT * FROM pg_stat_activity`  |
| **Agents**     | Query internal ORM models + use `get_agent_device_performance_timeseries()` for metrics |

- **MinIO**: Built-in health endpoints or basic probes via `minio-py`
- **Redis**: `INFO` command or `/metrics` via Prometheus
- **PostgreSQL**: `pg_stat_activity`, `pg_stat_replication`, etc.

## Observability Notes

Ouroboros prioritizes lightweight, embedded observability over heavy external integration. This health dashboard reflects that intent:

- Metrics should be pulled directly from local service APIs or shallow internal probes.

- Do **not** require Prometheus, OpenTelemetry, or external collectors to render this page.

- However, hooks should be designed with extensibility in mind:

  - A shared `metrics.ts` module or Svelte store can abstract the source
  - If Prometheus or OpenTelemetry is adopted later, it should be easy to drop in as a provider

This keeps the UX fast, testable, and offline-compatible — aligning with Ouroboros's goals.

### MinIO via `minio-py`

The `minio-py` client can be used for basic health checks and metadata without shelling out:

| Metric                   | Method                        | Notes                            |
| ------------------------ | ----------------------------- | -------------------------------- |
| Up/Down State            | `list_buckets()`              | Fast + safe connectivity check   |
| Bucket Count             | `len(list_buckets())`         | Low cost                         |
| Object Count (optional)  | `list_objects()` + `sum()`    | Expensive; use caching if needed |
| Storage Usage (optional) | Sum `obj.size` across buckets | Also expensive; cache if shown   |

> Recommended approach: show only bucket count and service reachability by default. Larger metrics should be backgrounded or admin-only.

## Implementation Notes

- Status cards should be uniform height and width
- Use icons and badge color to reinforce state
- Consider sparkline or mini-chart if historical data is available
