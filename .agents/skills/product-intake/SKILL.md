---
name: product-intake
description: Interview the user before building or planning a new product from this starter. Ask brand, language, RTL/LTR, database, color theme, and other product-design choices. Use when starting a new project, cloning the base, first plan, or PRODUCT.md is missing. Triggers on "new project", "start this product", "bootstrap", "از این بیس پروژه بساز".
---

# Product intake

**Do not write a plan or code until this interview is done** and the user has confirmed the summary.

Skip only when `PRODUCT.md` already exists, is filled in (not the example), and the user is continuing that product.

## How to ask

1. Prefer the **AskQuestion** tool for multiple-choice items. Put related questions in **one** form.
2. Ask free-text items (names, pitch) in the same turn, in the user's language.
3. Do not dump a 20-item questionnaire. Two rounds max, then a written summary to confirm.
4. Offer sensible defaults; never invent a brand or locale.

Persian users: ask in Persian. Keep `PRODUCT.md` keys in English so settings stay stable.

## Round 1 — identity (chat)

Ask:

- **Brand name** (shown in the header)
- **Project / repo name** (slug, e.g. `shop`)
- **One sentence**: what does this product do and for whom?
- **Industry** if not obvious (SaaS, shop, clinic, education, internal tool, …)

## Round 2 — AskQuestion (one form)

Include at least:

**Product type** (single)

- Public marketing site + app
- Logged-in web app / dashboard
- E-commerce
- Content / blog
- Internal admin-heavy tool
- API-first (DRF) with a thin UI

**Database** (single)

- SQLite (local / starter default)
- PostgreSQL
- MySQL

**UI language** (single)

- Persian (`fa`)
- English (`en-us`)
- Both (Persian default)
- Other (user will type the code)

**Text direction** (single)

- RTL (right-to-left) — default if language is `fa` / `ar` / `he` / `ur`
- LTR (left-to-right) — default for `en`
- Follow language automatically

**Color / mood** (single)

- Generate with UI UX Pro Max from the pitch
- Calm / warm (current starter tokens)
- Trust blue / SaaS
- Dark-first
- I will give exact hex colors

**Need now** (multiple)

- Public pages only (home is enough)
- Django admin customization
- REST API (DRF)
- Background jobs (Celery)
- Docker Compose
- Auth pages (login/register) beyond admin

## After answers

1. Write `PRODUCT.md` from the template `PRODUCT.md.example`. Fill every field; use `n/a` only when refused.
2. Show a short summary and wait for confirmation.
3. If they asked for a **plan**, write the plan from `PRODUCT.md`.
4. If they asked to **build**, apply in this order:

   - `.env` / `.env.example`: `DJANGO_SITE_NAME`, `DJANGO_LANGUAGE_CODE`, `DJANGO_TIME_ZONE`, `DJANGO_TEXT_DIRECTION`, `DATABASE_URL`
   - `html` `lang` / `dir` come from settings — do not hardcode
   - For Persian + RTL: follow **`persian-ui`** for complete fa UI, fonts via Vazirmatn/Estedad in tokens, and `ui-ux` quality bar
   - For `fa` products: Jalali dates (`persian-locale`) and تومان pricing if e-commerce (`persian-ecommerce`)
   - If e-commerce / «فروشگاه» / NightRuby-class: run **`persian-shop-playbook`** — copy `.cursor/skills/persian-shop-playbook/design.md` → project-root `design.md` (swap brand mark only), then follow that playbook’s Fast path. Prefer locked cream tokens over a fresh Pro Max palette unless the user asked for a different mood
   - If they chose Pro Max colors **and** it is not a cream shop: run `search.py --design-system -p "<brand>"` and map into `static/css/tokens.css` — then **override Latin-only fonts** for fa products
   - Add optional packages **only** if they selected them (DRF, Celery, Docker)
   - First domain app under `apps/` per `starter-architecture`
   - Do not ship starter skeleton pages as the product UI

## Defaults when they say "you decide"

| Topic | Default |
|-------|---------|
| Database | SQLite until production |
| Language | User's chat language (`fa` → `fa`, else `en-us`) |
| Direction | RTL for `fa`/`ar`/`he`/`ur`, else LTR |
| Theme | Pro Max from pitch |
| Extras | None |
| Time zone | `Asia/Tehran` if Persian, else `UTC` |
| Calendar (fa) | Jalali display — skill `persian-locale` |
| Shop currency (fa) | تومان + thousand separators — skill `persian-ecommerce` |
| Shop UI (fa ecommerce) | Cream NightRuby system — `persian-shop-playbook/design.md` → project `design.md` |
| Non-shop fa marketing UI | `persian-ui` + Pro Max palette with Persian fonts |

## Do not

- Start implementing mid-interview
- Switch `AUTH_USER_MODEL`
- Add Tailwind because Pro Max mentioned it
- Skip confirmation
