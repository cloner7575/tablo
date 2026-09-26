---
name: code-quality
description: Run code quality checks (ruff lint, ruff format, pytest) on a directory and report findings by severity. Use when the user wants to audit code quality, check for type errors, lint issues, or run automated checks on a path. Accepts a directory path. Triggers on "check code quality", "run quality checks", "/code-quality".
---

# Code Quality Review

Review code quality in the directory the user named (default: project root).

## Instructions

1. Collect `.py` files. Skip migrations, `__pycache__`, `.venv`, and generated files.

2. Run:

   ```bash
   .venv/bin/ruff check <directory>
   .venv/bin/ruff format --check <directory>
   .venv/bin/pytest <directory> -v
   ```

   If pytest has nothing to collect, say so and continue.

3. Manual checklist:

   - [ ] No `Any` without justification
   - [ ] No silent exceptions
   - [ ] N+1 avoided
   - [ ] Forms validate in the form class
   - [ ] Views return correct status codes
   - [ ] HTMX partials honor `HX-Request` when HTMX is in play
   - [ ] Celery tasks are idempotent when Celery is in play
   - [ ] Tests use factories once factories exist

4. Report by severity: Critical / Warning / Suggestion. Include file paths.
