---
name: systematic-debugging
description: Four-phase debugging methodology with root cause analysis for Django. Use when investigating bugs, fixing test failures, or troubleshooting unexpected behavior. Emphasizes NO FIXES WITHOUT ROOT CAUSE FIRST.
---

# Systematic Debugging for Django

**NO FIXES WITHOUT ROOT CAUSE FIRST.** Do not patch over symptoms.

## Four Phases

### 1. Reproduce and Investigate

- Write a failing test that captures the bug
- Read the full error message
- Check recent changes (`git diff`, `git log`) if git exists
- Trace where bad values enter the call chain

```python
@pytest.mark.django_db
def test_bug_reproduction(client):
    response = client.post("/profile/", {"bio": "New"})
    assert response.status_code == 200
```

### 2. Isolate

Log method, POST, user, `form.is_valid()`, and `form.errors` at the failure site. Use `breakpoint()` or `.venv/bin/pytest --pdb -x`.

### 3. Identify Root Cause

Read the stack trace. Check which assumption is false.

### 4. Fix and Verify

Fix at the cause. Re-run the reproduction test, then `.venv/bin/pytest` and `.venv/bin/ruff check .`.

## Django Tools

- Django Debug Toolbar SQL panel for N+1 / slow queries
- `CaptureQueriesContext` in tests
- `LOGGING["loggers"]["django.db.backends"] = DEBUG` for SQL
- CSRF 403: missing `{% csrf_token %}`
- Form not saving: `is_valid()`, `save()`, `commit=False` without instance save
- Celery: call the task directly or set `CELERY_TASK_ALWAYS_EAGER = True`
- HTMX: `htmx.logAll()` and print `HX-Request`

```bash
.venv/bin/python manage.py showmigrations
```

## Stop Conditions

Three failed fix attempts = architectural issue. Stop and discuss. Never "quick fix now, investigate later."

## Integration

- `pytest-django-patterns`, `django-models`, `celery-patterns`, `htmx-patterns`, `django-extensions`
