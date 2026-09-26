---
name: django-logging
description: Logging and error handling for this starter — logger naming, levels, exception logging with context, what never to log, and the LOGGING config. Use when adding logging, handling exceptions, debugging production behaviour, or reviewing error handling.
---

# Logging and error handling

## Config already in the base

`core/settings/base.py` sends everything to the console (the right choice under
systemd, Docker, or a PaaS — the platform collects stdout):

- root at `DJANGO_LOG_LEVEL` (default INFO)
- `apps` logger at `DJANGO_APP_LOG_LEVEL`, so product code can be noisier than
  Django without turning on framework debug spam
- `django.request` and `django.security` at WARNING
- `DJANGO_LOG_SQL=true` adds query logging in development only

## Using it

```python
import logging

logger = logging.getLogger(__name__)  # -> "apps.orders.services"
```

Module `__name__` only. Never `logging.getLogger("mylogger")` — the hierarchy
is how the config reaches your module.

```python
try:
    gateway.charge(order.total)
except GatewayError:
    logger.exception("Payment failed for order %s", order.pk)
    raise
```

- `logger.exception` inside an `except` block: it attaches the traceback
- `%s` placeholders, not f-strings: the formatter skips the work when the level
  is disabled, and log aggregators can group by template
- Log the identifier (`order.pk`), not the whole object

## Levels

| Level | Use |
|---|---|
| DEBUG | developer detail, off in production |
| INFO | a business event completed (order placed, user registered) |
| WARNING | recoverable, someone should look eventually (retry, fallback used) |
| ERROR | the request failed; a human must act |
| CRITICAL | the process or a dependency is down |

## Never swallow

```python
# BAD — the bug disappears
try:
    do_work()
except Exception:
    pass

# GOOD — narrow, logged with context, re-raised or surfaced to the user
try:
    do_work()
except LookupError:
    logger.exception("do_work failed for %s", key)
    raise
```

"Surfaced to the user" means a message plus a real status code, not a silent
200. Unhandled exceptions must stay unhandled: they render `500.html`, and the
API exception handler deliberately returns `None` for them.

## Never log

Passwords, tokens, API keys, session ids, full card numbers, national ids, or
whole request bodies. `django.security` events are already separated; do not
copy their payloads into your own INFO logs.

## Production

Add an error tracker (Sentry or equivalent) per product, not to the base. Keep
`ADMINS` set (`DJANGO_ADMIN_EMAILS`) so Django can mail unhandled 500s when no
tracker exists.

## Integration

`django-services`, `systematic-debugging`, `django-security` rule
