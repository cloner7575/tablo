---
name: django-signals
description: Django signals, transaction.on_commit, M2M signals, and when to prefer a service layer instead. Use when writing post_save, pre_save, m2m_changed, or side effects after database writes.
---

# Django Signals

Prefer **explicit calls**. If you control both the writer and the reaction, put the reaction in a model method or service and call it. Signals hide control flow and duplicate easily.

## When Signals Are Appropriate

- Audit logging
- Cache invalidation
- Notifying another app you do not want to import
- Third-party hooks

## When They Are Not

- Domain state transitions (`order.pay()` should call `order.mark_paid()`, not hope `post_save` does it)
- Anything that must happen in the same request and fail the request if it fails — call it directly
- Nested saves that re-enter the same `post_save`

## `transaction.on_commit`

Side effects that talk to the world (email, Celery, cache, HTTP) must wait until the transaction commits. Otherwise a rollback still sends the email or enqueues the task.

```python
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=Invoice)
def enqueue_invoice_email(
    sender, instance: Invoice, created: bool, **kwargs: object
) -> None:
    if not created:
        return

    transaction.on_commit(lambda: send_invoice_email.delay(instance.pk))
```

Pass IDs into the lambda/task, not unsaved instances.

## Connecting Receivers

- Put receivers in `<app>/signals.py`
- Import them from `AppConfig.ready()` so they register once
- Use `@receiver` with an explicit `sender`
- Always accept `**kwargs`

```python
class InvoicesConfig(AppConfig):
    name = "invoices"

    def ready(self) -> None:
        from invoices import signals  # noqa: F401
```

## M2M

`m2m_changed` fires with `action` in `pre_add`, `post_add`, `pre_remove`, `post_remove`, `pre_clear`, `post_clear`. `pk_set` may be `None` on clear. Do not assume one row changed.

## Duplicate Fires

- `save()` from admin, serializers, and your service can each fire `post_save`
- `update()` / `bulk_create()` **do not** send `post_save` — do not hide required logic only in a signal
- Guard with `if kwargs.get("raw"): return` so loaddata does not loop
- Use a `uid` on `connect()` if connecting manually

## Transactions

```python
with transaction.atomic():
    order.save()
    order.lines.all().delete()
    # signal on_commit runs after this block succeeds
```

`select_for_update()` belongs in the same atomic block as the write.

## Anti-Patterns

- Importing `signals.py` from `models.py` (circular imports, double register)
- Celery `.delay()` inside `post_save` without `on_commit`
- Business rules that only exist in a receiver
- Catching all exceptions inside a receiver and swallowing them

## Integration

- `django-models`, `celery-patterns`, `django-caching`
