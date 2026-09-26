---
name: starter-architecture
description: Architecture of this Django starter and how to extend it for any new product. Use when adding apps, changing settings, cloning the base, or deciding where a file belongs.
---

# Starter architecture

This repo is a **cookie-cutter Django base**. Derived projects keep the same tree so Cursor skills keep working.

## Boundaries

| Path | Owns |
|------|------|
| `core/settings/` | `base` / `development` / `test` / `production`, plus `env.py` |
| `core/urls.py` | Root URLconf: admin, accounts, `api/`, `i18n/`, common |
| `core/api_urls.py` | API version namespaces (`api:v1`) |
| `apps/accounts` | `User`, auth screens, `me` endpoint. Not product features |
| `apps/common` | `TimeStampedModel`, health, htmx helpers, DRF pagination and error envelope, context processors |
| `apps/<name>` | One bounded context (billing, catalog, …) |
| `templates/` | Shell, error pages, `registration/`, components, partials |
| `static/` | `css/tokens.css`, `css/base.css`, `js/app.js`, `vendor/htmx.min.js` |
| `locale/` | Compiled translations (`LOCALE_PATHS`) |
| `tests/` | pytest. Mirror app names: `tests/test_<app>_*.py` |

Per-app file conventions:

```
apps/<app>/
├── models.py        state and invariants
├── selectors.py     reusable read paths (optional)
├── services.py      multi-model / external-system writes (optional)
├── forms.py         HTML input validation
├── views.py         HTML orchestration
├── urls.py          app_name = "<app>"
├── serializers.py   API contracts
├── api.py           API views
└── api_urls.py      API routes, no app_name
```

Never add a second settings module outside `core/settings/`. Never introduce a top-level Django app beside `apps/`.

## Settings

- Shared: `core/settings/base.py`
- Local: `core/settings/development.py` (`DEBUG=True`, default for `manage.py`)
- Tests: `core.settings.test` — hermetic; pins locale, cache, mailer, throttling
- Prod: `core.settings.production` — refuses an insecure or short `SECRET_KEY`,
  refuses empty `ALLOWED_HOSTS`, forces HSTS/SSL/secure cookies, and serves
  hashed static files through WhiteNoise

Already wired in the base and not worth re-inventing: WhiteNoise, `STORAGES`,
`CACHES` (locmem, Redis when `REDIS_URL` is set), `MAILERS` (Django 6.1's
replacement for the deprecated `EMAIL_*` settings), `LocaleMiddleware` with a
single-language default, DRF defaults, and console logging with an `apps`
logger.

Secrets live in `.env` (see `.env.example`). Product identity (brand, locale, DB, theme) lives in `PRODUCT.md` after `product-intake`. `AUTH_USER_MODEL` is already `accounts.User` — do not switch it.

## New domain app

```bash
.venv/bin/python manage.py startapp catalog apps/catalog
```

1. `AppConfig.name = "apps.catalog"` and `label = "catalog"`
2. Append `"apps.catalog.apps.CatalogConfig"` to `INSTALLED_APPS`
3. `path("catalog/", include("apps.catalog.urls"))` in `core/urls.py`
4. API too? Add `apps/catalog/api_urls.py` (no `app_name`) and include it in
   `v1_patterns` in `core/api_urls.py`
5. Models subclass `TimeStampedModel`
6. Tests under `tests/`, plus the migration in the same commit

## Commerce example (large shops)

Prefer bounded apps over one monolith:

```
apps/catalog   products, categories, CMS heroes
apps/cart      DB cart + merge-on-login
apps/orders    checkout + order snapshots
apps/payments  gateway + paid side effects
apps/panel     staff UI (no models)
```

Public storefront URLs can still live under `/shop/` with `app_name = "shop"`.
Home at `/` should call into `catalog`, not a removed fat app.

## What not to do

- Do not create `config/` as a second project package
- Do not use `django.contrib.auth.models.User`
- Do not put business views in `core/`
- Do not copy-paste a new CSS framework that ignores `tokens.css`
- Do not dump an entire product catalog into one JSON blob for the browser

## Integration

- Cloning/renaming a product → `bootstrap-project`
- UI → `ui-ux`
- Models → `django-models`
