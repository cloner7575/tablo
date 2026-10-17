# تابلو دات کام

فضای تخصصی الهام، طراحی و ساخت تابلو برای طراح‌ها، تابلوسازها و کسب‌وکارها.

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
.venv/bin/python manage.py migrate
.venv/bin/python manage.py seed_site
```

سید فعلی: ۱۲ نوع تابلو، ۱۱ نمونهٔ واقعی با عکس، ۷ دستهٔ کسب‌وکار و شهرهای تهران، کرج و مشهد. داده‌ها در `apps/catalog/industry_content.json` و عکس‌ها در `static/img/references/` هستند. اجرای مجدد دادهٔ تکراری نمی‌سازد؛ اطلاعات منابع فقط داخلی باقی می‌ماند. معرفی ۷ مجموعه نیز از همان فایل JSON خوانده می‌شود. این دستور حساب، سفارش یا قیمت آزمایشی ایجاد نمی‌کند.

راهنمای کامل: [docs/site-seed.md](docs/site-seed.md). دستور قدیمی `seed_demo` فقط برای سناریوهای آزمایشی است.

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

1. **Creative workspace:** `/portfolio/` → بورد الهام → شروع پروژه با نمونه‌های مرجع → دریافت پیشنهاد اجرا
2. **Customer:** Homepage → «قیمت بگیر» → wizard → OTP → request → quotes → accept → complete → review
3. **Vendor:** ثبت‌نام → onboarding → Admin approve → dashboard → submit quote
4. **Admin:** `/admin/` — تأیید Vendor، مدیریت محتوا

OTP codes print to the console in development (`ConsoleSmsProvider`).

## Docs

- [`PRODUCT.md`](PRODUCT.md)
- [`Professional workspace`](docs/professional-workspace.md)
- [`تجربهٔ بصری و موبایل`](docs/ui-experience.md)
- [`بازطراحی محصول و مسیر خدمات`](docs/product-review.md)
- [`docs/product-spec.md`](docs/product-spec.md)
- [`docs/architecture.md`](docs/architecture.md)
- [`docs/roadmap.md`](docs/roadmap.md)
- [`docs/progress.md`](docs/progress.md)

### گالری الهام، مقاله‌ها و سئو

گالری مستقل برای تصاویر هوش مصنوعی و مفهومی در `/inspiration/`، مجله در `/articles/` و مدیریت محتوا برای مدیر سایت در `/inspiration/manage/` قرار دارد. راهنمای بارگذاری، انتشار، مهاجرت‌ها و دامنهٔ اصلی: [docs/editorial-seo.md](docs/editorial-seo.md).

### سفارش ساده و اجرای تابلو

فرم سه‌بخشی درخواست، درخواست مستقیم خصوصی، ذخیره‌های حساب و تأیید طرح/مبلغ تا نصب و تحویل: [راهنمای پیاده‌سازی](docs/simple-ordering.md). این نسخه پنج migration جدید دارد؛ پیش از اجرای نسخهٔ جدید، `manage.py migrate` و `manage.py collectstatic --noinput` را اجرا کنید.

### نمونه‌های منبع‌دار صنعت تابلو

پس از migration، برای واردکردن دسته‌ها و تصاویر واقعیِ بررسی‌شده از `python manage.py import_industry_content` استفاده کنید. فایل‌های تصویر همراه پروژه‌اند و این فرمان به شبکه وصل نمی‌شود. `--archive-demo` فقط در پیش‌نمایش DEBUG، داده‌های شناخته‌شدهٔ seed را بایگانی می‌کند. `seed_demo` برای نمایش عمومیِ محصول مناسب نیست. منابع، رفتار واردسازی، پشتیبان این جلسه و پرامپت تصویر لندینگ در [docs/industry-content.md](docs/industry-content.md) ثبت شده‌اند.
