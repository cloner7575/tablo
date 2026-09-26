---
name: celery-patterns
description: Celery task patterns including task definition, retry strategies, periodic tasks, and best practices. Use when implementing background tasks, scheduled jobs, or async processing.
---

# Celery Patterns for Django

Celery is intentionally **not** installed in the base — an unused broker is a
dependency, a deploy step, and a failure mode in every derived product. Add it
only when work genuinely must leave the request cycle.

```bash
.venv/bin/pip install "celery[redis]" redis   # then add both to requirements.txt
```

Wire it as `core/celery.py` with `celery -A core`, set `CELERY_BROKER_URL` from
the environment, and set `CELERY_TASK_ALWAYS_EAGER = True` in
`core/settings/test.py` so the suite stays hermetic. Never create a parallel
`config` package for it.

## Core Rules

- Tasks must be idempotent
- Pass IDs, not model instances (JSON-serializable args only)
- Log start, success, and failure
- Retry transient failures; do not retry validation/business errors

## Task Design

Place tasks in `<app>/tasks.py`. Prefer `@shared_task`. Use `bind=True` when you need `self.retry` or the task id. Add type hints.

```python
@shared_task(
    bind=True,
    autoretry_for=(OSError,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
)
def send_invoice(self, invoice_id: int) -> None:
    invoice = Invoice.objects.filter(pk=invoice_id).first()
    if invoice is None:
        return
    # process by id, check current state first
```

## Retry

- Fixed delay: internal, predictable recovery
- Exponential backoff + jitter: external APIs
- No retry: validation, permanent errors
- Cap with `retry_backoff_max` and `max_retries`

## Idempotency

- Check-before-process
- Status field + `select_for_update()`
- Unique constraints against duplicate work

## Beat

Configure `beat_schedule` on the Celery app. Keep periodic tasks light; spawn subtasks for heavy work.

## Commands

```bash
.venv/bin/celery -A core worker -l info
.venv/bin/celery -A core beat -l info
```

## Anti-Patterns

- Passing model instances
- Incrementing without checks
- Bare `except: pass`
- Long tasks with no progress or heartbeat
