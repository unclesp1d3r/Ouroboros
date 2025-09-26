---
inclusion: fileMatch
fileMatchPattern:
  - "app/core/tasks/**/*.py"
  - "app/core/jobs/**/*.py"
---

## Background Task Handling

- Use `FastAPI.BackgroundTasks` or `asyncio.create_task` for async jobs. This will later be upgraded to use Celery.
- Use Cashews caching wherever possible.
- Jobs that run on a predefined schedule must line in `app/core/jobs/` and be named clearly (e.g. `daily_cleanup_job.py`).
- Jobs that are triggered by user-initiated actions in the endpoints must live in `app/core/tasks/` and be named clearly (e.g. `dispatch_tasks.py`).
- Long-lived jobs should be tracked and idempotent.

## Cursor Rules

- NEVER block the main FastAPI event loop with long CPU tasks.
- Write jobs to be restartable or self-checking.
- Schedule recurring logic using `asyncio` or a simple task loop — avoid Celery unless the user asks.
- ALL background tasks must have unit and integration tests to ensure proper functionality.

### Additional Guidelines for Skirmish

- Recurring tasks must be idempotent and safe to rerun.
- Define and respect retry limits for any job that might fail.
- Heartbeat checker should log agents marked stale and trigger task requeue.
- Long-lived jobs should emit periodic logs and track last checkpoint.
