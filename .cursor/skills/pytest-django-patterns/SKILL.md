---
name: pytest-django-patterns
description: pytest-django testing patterns for this starter — fixtures, TDD, query counts, HTMX and API tests, and hermetic test settings. Use when writing tests, adding fixtures, or following the red-green-refactor cycle.
---

# pytest-django Testing Patterns

## TDD

1. **RED** — a failing test that describes the behaviour
2. **GREEN** — the minimum code that passes it
3. **REFACTOR** — clean up with the test still green

For a bug fix, the test reproduces the bug first. A fix with no test is a fix
that comes back.

## What the starter gives you

`pytest.ini` pins `DJANGO_SETTINGS_MODULE=core.settings.test`, enables
`--strict-markers`, and turns Django deprecation warnings into **errors** so a
deprecated API fails the build instead of scrolling past.

`core/settings/test.py` is hermetic on purpose: language, direction, timezone,
cache, mailer, media root, and throttling are pinned so a developer's `.env`
cannot change the result. Keep it that way — a test that only passes on your
laptop is worse than no test.

`tests/conftest.py` provides `user`, `staff_user`, and `auth_client`
(`client.force_login`). Add shared fixtures there; keep single-use data in the
test.

```
tests/
├── conftest.py
├── test_starter.py     shell, health, error pages
├── test_accounts.py    auth screens
├── test_api.py         DRF surface
├── test_settings.py    settings guardrails
└── test_<app>_<area>.py
```

## Database

`@pytest.mark.django_db` per test, or `pytestmark = pytest.mark.django_db` for
the module. Anything that renders a page which touches the ORM needs it —
including a health endpoint.

## Patterns worth copying

Query counts on every list view and list endpoint:

```python
def test_list_is_not_n_plus_one(client, django_assert_num_queries, posts):
    with django_assert_num_queries(3):
        client.get(reverse("blog:list"))
```

HTMX fragments — modern header syntax:

```python
response = client.get(url, headers={"HX-Request": "true"})
assert "<html" not in response.content.decode()
```

API, through the namespaced reverse:

```python
response = auth_client.patch(
    reverse("api:v1:me"),
    data={"email": "taken@example.com"},
    content_type="application/json",
)
assert response.status_code == 400
assert response.json()["code"] == "invalid"
```

Parametrise the sad paths:

```python
@pytest.mark.parametrize(("payload", "status"), [({}, 400), ({"title": "x"}, 201)])
def test_create(auth_client, payload, status): ...
```

Deferred side effects:

```python
with django_capture_on_commit_callbacks(execute=True):
    place_order(user=user, cart=cart)
assert len(mail.outbox) == 1
```

## What to test

- **Views**: status code, authorization, redirect target, side effect
- **Forms**: invalid input, `clean_*`, the error the user actually sees
- **Models / QuerySets**: methods, constraints, state transitions
- **Services**: database state plus the side effect, via `on_commit` capture
- **API**: anonymous access, ownership scoping, validation error shape
- **Tasks**: logic and idempotency with I/O mocked, never a live worker

Test behaviour, not Django internals. Do not mock your own domain code.

## Factories

Factory Boy is not installed in the base. Plain fixtures are enough for a
starter; add `factory-boy` per product once a model needs more than three
fields to build, and put factories in `tests/factories.py`.

## Commands

```bash
.venv/bin/pytest
.venv/bin/pytest -x --lf
.venv/bin/pytest -k "health"
```

## Pitfalls

- Missing `django_db` (the error says so — read it)
- Asserting on rendered HTML strings that change with every design tweak
- Tests that depend on `.env`, the clock, or network access
- One test that asserts fifteen things
- Writing tests after the fact and only covering the happy path

## Integration

`definition-of-done`, `systematic-debugging`, `django-performance`,
`django-rest-framework`, `htmx-patterns`
