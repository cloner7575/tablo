---
name: django-services
description: Service layer and selectors for multi-step domain operations — transactions, on_commit side effects, domain exceptions, and when a service beats a fat model. Use when a workflow touches several models, calls a gateway, or mixes writes with side effects like email or payments.
---

# Services and selectors

Fat models first. Reach for a service only when an operation does not belong to
one model: it writes several models, talks to an external system, or must be
atomic as a unit.

```
apps/<app>/models.py      state and rules of one aggregate
apps/<app>/selectors.py   read paths (complex queries the views reuse)
apps/<app>/services.py    write workflows that span models or systems
```

`apps/common/services.py` is the shipped example (the database probe used by
both the HTML and API health endpoints).

## Writing a service

```python
def place_order(*, user: User, cart: Cart) -> Order:
    """Create an order from a cart. Atomic; side effects run after commit."""
    if not cart.items.exists():
        raise EmptyCartError("Cannot place an order from an empty cart.")

    with transaction.atomic():
        order = Order.objects.create(user=user, total=cart.total())
        OrderLine.objects.bulk_create(cart.to_lines(order))
        cart.clear()

    transaction.on_commit(lambda: send_order_confirmation(order.pk))
    return order
```

Rules:

- Keyword-only arguments, explicit types, one clear return value
- One `transaction.atomic()` around the writes that must succeed together
- Email, Celery tasks, webhooks, and cache busts go in `transaction.on_commit`
  so a rollback cannot send them
- Pass **ids** to background tasks, never model instances
- Raise a domain exception (`EmptyCartError`), not `ValueError`, and let the
  view or serializer translate it into a message and a status code
- Never swallow: log with context, then re-raise

## Domain exceptions

```python
class DomainError(Exception):
    """Base for expected, user-explainable failures in this app."""


class EmptyCartError(DomainError): ...
```

Views catch `DomainError`, add a message, and re-render with 400. Unexpected
exceptions stay unhandled so they reach the logs and the 500 page.

## Selectors

Keep read logic reusable and optimised in one place:

```python
def visible_posts(*, viewer: User) -> QuerySet[Post]:
    return (
        Post.objects.published()
        .select_related("author")
        .prefetch_related("tags")
        .order_by("-published_at")
    )
```

If a selector is one filter chain, put it on the QuerySet instead — do not
create a file to wrap `Model.objects.filter(...)`.

## When NOT to add a service

- Single-model state change → model method (`order.cancel()`)
- Input validation → form or serializer
- A reusable filter → QuerySet method
- "Because the tutorial said so" → no

## Testing

Services are the easiest layer to test: call them directly, assert the database
state and the side effect. Use `django_capture_on_commit_callbacks` to run
`on_commit` work inside a test.

## Integration

`django-models`, `django-signals`, `celery-patterns`, `pytest-django-patterns`
