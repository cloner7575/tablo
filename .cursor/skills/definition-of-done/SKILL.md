---
name: definition-of-done
description: The senior-engineer working loop for this starter — understand, plan, failing test first, implement, verify with ruff/pytest/check, then report. Use at the start of any non-trivial change and before claiming a task is finished. Triggers on "is this done", "ship it", "finish this", planning a feature, or fixing a bug.
---

# Definition of done

A change is done when someone else could deploy it without asking you a
question. Not when the code exists.

## 1. Understand before typing

- Read the surrounding code and match its patterns. A small extension beats a
  new abstraction
- New product from this starter with an empty `PRODUCT.md`? Run
  `product-intake` first and stop until it is confirmed
- Unclear requirement, missing brand, ambiguous data model? Ask. Do not invent
  a domain and build on it

## 2. Plan the change

State, in one short list: which files change, which layer owns each piece
(model / service / form / view / template / serializer), and what could break.
If the plan needs a migration, a settings change, or a new dependency, say so
before writing it.

Layer check before you start:

| Concern | Home |
|---|---|
| State and invariants of one aggregate | model / QuerySet |
| Multi-model or external-system workflow | `services.py` |
| Input validation | form or serializer |
| Orchestration, status codes, redirects | view |
| Presentation | template, tokens, CSS |
| Project wiring | `core/` |

## 3. Failing test first

Write the test that fails for the right reason, then make it pass. Cover the
sad path — permissions, validation errors, empty states — not only the happy
one. List views get a query-count assertion.

## 4. Implement

- Types on public functions, early returns, no `Any`
- `select_related` / `prefetch_related` wherever a relation is touched
- Never swallow an exception: log with context, then re-raise or show the user
- No secrets in code; config comes from the environment
- Any user-facing screen ships finished: chrome, empty/loading/error states,
  labels, focus, keyboard access, responsive, `dir`-aware. A backend-only dump
  into a half-styled page is not done (`ui-ux`, plus `persian-ui` for fa)

## 5. Verify — actually run it

```bash
.venv/bin/ruff format .
.venv/bin/ruff check .
.venv/bin/pytest
.venv/bin/python manage.py makemigrations --check --dry-run
.venv/bin/python manage.py check
```

Touched settings or deploy behaviour? Also:

```bash
DJANGO_SETTINGS_MODULE=core.settings.production \
DJANGO_SECRET_KEY=... DJANGO_ALLOWED_HOSTS=example.com \
.venv/bin/python manage.py check --deploy
```

Touched a template, CSS, or an interaction? Open the page. Screenshots beat
assumptions.

Never report success on a command you did not run.

## 6. Report

Lead with the outcome. Then: what changed and why, anything deliberately left
out, and the follow-up you would pick up next. Surface surprises — a
deprecation, a config that was silently wrong, a test that was already red —
instead of quietly working around them.

## Red flags that mean "not done"

- "It should work" / "tests probably pass"
- A new dependency added without saying why
- A model change with no migration
- A page with no empty or error state
- A fix with no test that would have caught the bug
- Starter leftovers shipped as product UI

## Integration

`product-intake`, `starter-architecture`, `pytest-django-patterns`,
`code-reviewer`, `ui-ux`, `github-workflow`
