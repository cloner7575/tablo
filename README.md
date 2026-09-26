# تابلو دات کام

پلتفرم Lead Generation برای سفارش و مقایسه خدمات تابلوسازی.

## Stack

- Django 6.1 + DRF + PostgreSQL + Redis
- Templates + HTMX + Vazirmatn (فارسی RTL)
- Docker Compose

## Installation

```bash
cp .env.example .env
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

Or with Docker:

```bash
cp .env.example .env
docker compose up --build
```

## Environment Variables

See [`.env.example`](.env.example). Important keys:

| Variable | Purpose |
|----------|---------|
| `DJANGO_SECRET_KEY` | Secret key |
| `DJANGO_SITE_NAME` | Brand (تابلو دات کام) |
| `DJANGO_LANGUAGE_CODE` | `fa` |
| `DJANGO_TEXT_DIRECTION` | `rtl` |
| `DATABASE_URL` | `sqlite:///...` or `postgres://...` |
| `REDIS_URL` | optional cache |
| `SMS_PROVIDER` | OTP SMS backend class path |

## Database Setup

```bash
.venv/bin/python manage.py migrate
```

Docker Compose sets `DATABASE_URL=postgres://tablo:tablo@db:5432/tablo` and runs migrate on start.

## Seed Data

```bash
.venv/bin/python manage.py seed_demo
```

Creates: ۶ سرویس، تهران/کرج، ۱۰ Vendor، ۲۰ Portfolio، ۲۰ Request، حدود ۵۰ Quote.

## Run Development Server

```bash
.venv/bin/python manage.py runserver
```

Open http://127.0.0.1:8000/

## Run Tests

```bash
.venv/bin/python -m pytest
.venv/bin/ruff check .
.venv/bin/python manage.py makemigrations --check --dry-run
```

## API Documentation

- OpenAPI schema: `/api/schema/`
- Swagger UI: `/api/docs/`
- Versioned API: `/api/v1/`

Key resources: `auth/otp/`, `cities/`, `services/`, `vendors/`, `requests/`, `quotes/`, `portfolio/`, `reviews/`

## Main flows

1. **Customer:** Homepage → «قیمت بگیر» → wizard → OTP → request → quotes → accept → complete → review
2. **Vendor:** ثبت‌نام → onboarding → Admin approve → dashboard → submit quote
3. **Admin:** `/admin/` — تأیید Vendor، مدیریت محتوا

OTP codes print to the console in development (`ConsoleSmsProvider`).

## Docs

- [`PRODUCT.md`](PRODUCT.md)
- [`docs/product-spec.md`](docs/product-spec.md)
- [`docs/architecture.md`](docs/architecture.md)
- [`docs/roadmap.md`](docs/roadmap.md)
- [`docs/progress.md`](docs/progress.md)
