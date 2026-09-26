# Product

## Identity

- Brand name: تابلو دات کام
- Project slug: tablo
- Pitch (one sentence): پلتفرم ثبت درخواست ساخت تابلو و دریافت پیشنهاد قیمت از تابلو‌سازهای مرتبط
- Audience: صاحبان مغازه/کسب‌وکار که نیاز به تابلو دارند؛ تابلو‌سازها و شرکت‌های تابلوسازی
- Industry / product type: Marketplace / Lead generation (تابلوسازی)

## Locale

- UI language code: fa
- Text direction: rtl
- Time zone: Asia/Tehran

## Look

- Color / mood: Light commercial like tablosepehrad.com — white/gray canvas, charcoal header, crimson CTA (#D0122D)
- Pro Max query (if used): Iranian signage company commercial light red charcoal
- Notes: Visual language inspired by Sepehrad (rounded dark header, red pills, dark content cards, VIP logo rail); marketplace product copy for تابلو دات کام

## Platform

- Database: postgres
- REST API: DRF at `/api/v1/` — auth, vendors, services, cities, requests, quotes, portfolio, reviews
- Public signup: yes — phone OTP for customers; vendor self-register + admin verification
- Background jobs: no (on_commit stubs; Celery later)
- Cache / Redis: yes (OTP throttle / cache; locmem fallback)
- Docker: yes
- Deploy target: Docker Compose (dev); production-ready gunicorn image

## MVP

- First screens / features:
  - Homepage conversion + request wizard
  - Customer dashboard (requests, quotes, chat, accept, review)
  - Vendor dashboard (matched requests, quotes, chat, portfolio, profile)
  - Public vendor / service / city / portfolio SEO pages
  - Admin management
  - Quote-linked WebSocket chat (Django Channels)
  - Notifications + analytics stubs
  - Monetization + pricing scaffolds (no real payment)

## Confirmed

- Date: 2026-09-26
- By: product owner (intake confirmed)
