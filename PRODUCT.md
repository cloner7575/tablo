# Product

## Identity

- Brand name: تابلو دات کام
- Project slug: tablo
- Pitch (one sentence): سفارش راحت تابلو؛ ثبت نیاز، مقایسه پیشنهاد تابلوسازها و پیگیری طرح تا نصب
- Audience: صاحبان مغازه و کسب‌وکار برای سفارش ساده؛ تابلوسازها و شرکت‌های تابلوسازی برای دریافت درخواست و مدیریت اجرا
- Industry / product type: Marketplace / Lead generation (تابلوسازی)

## Locale

- UI language code: fa
- Text direction: rtl
- Time zone: Asia/Tehran

## Look

- Color / mood: Jeddy reference: light #f8fafc / dark #0c1424, slate surfaces, blue #1464c4 / #79b8ff and a cobalt action button
- Pro Max query (if used): professional service marketplace blue slate dark light
- Notes: Service marketplace with Jeddy’s light and dark themes, Persian typography, original blue isometric signage hero and coherent mobile layouts; latest owner request supersedes the earlier red palette

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
  - Customer-first homepage + three-part request form
  - Public signage examples + account-synced saved references and concept gallery in the customer panel
  - Inspiration references attached to project requests + side-by-side quote comparison
  - Customer dashboard (requests, quote totals, chat, design and final-price approval, installation, delivery, review)
  - Vendor dashboard (matched requests, quotes, chat, portfolio, profile)
  - Public vendor / service / city / portfolio SEO pages
  - Admin management
  - Quote-linked WebSocket chat (Django Channels)
  - Notifications + analytics stubs
  - Monetization + pricing scaffolds (no real payment)

## Confirmed

- Date: 2026-09-26
- By: product owner (intake confirmed)

## Product evolution

- 2026-10-12: Product owner requested a distinctive professional experience for sign makers and designers; added creative workspace features within the existing architecture.
- Implementation and storage limits: `docs/professional-workspace.md`.

- Owner feedback: restored the original white/grey, charcoal and crimson palette; removed the concept editor and focused the experience on gallery, specialists and projects.

- Owner requested an independent shop-inspiration gallery for AI-created signage images, with direct owner uploads, source labels and a magazine with SEO-ready article pages. Implemented in `apps/editorial`; see `docs/editorial-seo.md`.

- Owner requested a shared white, red, black and light-grey UI with animations and stronger mobile layouts across the site. Added native accessible motion, mobile navigation, responsive filters, refreshed public and workspace surfaces, and unified Persian auth screens; see `docs/ui-experience.md`.

- 2026-10-13: Owner selected https://jeddy.ir/ as the UI/UX reference. Adapted its spacious portfolio hierarchy, restrained header, two-column hero with an original isometric signage illustration, light cards and footer to this product. Mobile cards use one readable column below 481px; existing gallery, project and specialist workflows remain available.

- 2026-10-13 (revised owner direction): rebuilt the shared UI with the actual blue/slate light and dark reference palette and persistent theme switching. Added a searchable service directory, contextual service/guidance handoff, and city/service/search/sort/pagination for specialist discovery. Product decisions and validation: `docs/product-review.md`.

- 2026-10-13: Owner approved the industry review and customer-first structure. Simplified landing/navigation and copy, introduced a three-part request form, made direct requests exclusive, clarified construction/installation totals and estimate/final prices, added account-synced saved references and a role-scoped design approval → production → installation → delivery workflow. See `docs/simple-ordering.md`.

- Owner requested more polished cards, buttons and menus plus a stronger animated landing. The shared Jeddy palette remains; native progressive motion has manual pause, offscreen/hidden-page suspension and live reduced-motion support. See `docs/ui-experience.md`.

- Owner requested actual industry examples and removal of fake public data. Added 11 attributed source projects, 12 researched service types, 7 official-site provider references and an original photographic AI hero; source providers have no invented marketplace membership, ratings or prices. Exact demo identities were archived on the local preview after a backup. See `docs/industry-content.md`.

- Owner clarified that imported material is seed data, with no public source credits or links to the original sites. Public templates, article captions and portfolio API omit source information; internal provenance remains available for maintenance.
