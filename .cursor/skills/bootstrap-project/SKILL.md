---
name: bootstrap-project
description: Turn this Django starter into a new product repo while keeping architecture, skills, and rules. Use when the user wants a new project from this base, to clone, fork, or rename the starter.
---

# Bootstrap a project from this starter

Goal: a new codebase that still looks like this starter, so the senior Django + UI assistant keeps working.

## 0. Intake first

Run `product-intake` before copying, renaming, or writing a plan. Persist answers in `PRODUCT.md`. Do not guess brand, language, direction, or database.

## Keep

- `apps/`, `core/`, `templates/`, `static/`, `tests/`, `locale/`, `.cursor/`
  (including `ui-ux-pro-max`), `.github/workflows/`, `AGENTS.md`
- `AUTH_USER_MODEL = "accounts.User"`
- Split settings modules and `core/settings/env.py`
- Ruff / pytest config, including the deprecation-warnings-as-errors filter
- The auth screens, error pages, API envelope, and vendored htmx
- The design system: `static/css/tokens.css`, `base.css`, `img/icons.svg`.
  Restyle by editing tokens; a Persian product swaps the font tokens for
  self-hosted Vazirmatn/Estedad and deletes the latin files in `static/fonts/`
  (recipe: `persian-ui/rtl-engineering.md`).

## Drop or regenerate

- `.venv/`, `db.sqlite3`, `__pycache__/`, `.env`
- Copy `.env.example` → `.env` and set values from `PRODUCT.md` (`DJANGO_SITE_NAME`, language, direction, `DATABASE_URL`)

## Rename (optional)

If they want a package name other than `core`:

1. Rename the `core/` directory and every `core.` import (`DJANGO_SETTINGS_MODULE`, `ROOT_URLCONF`, WSGI/ASGI)
2. Leave `apps.accounts` / `apps.common` labels unchanged
3. Update `AGENTS.md` Quick facts only — do not rewrite skills

If they keep the name `core` (recommended), only change `DJANGO_SITE_NAME`.

## First commands in the new repo

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
cp .env.example .env          # set brand, language, direction, DATABASE_URL
.venv/bin/python manage.py migrate
.venv/bin/pytest
.venv/bin/python manage.py runserver
```

Then replace the starter-only surface before the first demo: `pages/home.html`
(the service-status panel is a reference, not product UI) and the footer copy.
Add the first domain app with `starter-architecture`.

## Do not

- Start from a blank `django-admin startproject` and try to re-apply skills by hand
- Delete `.cursor/` or `AGENTS.md`
- Replace the template shell with an unrelated UI kit on day one
