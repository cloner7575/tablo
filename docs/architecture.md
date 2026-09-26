# Architecture — تابلو دات کام

## Stack

- Django 6.1 + DRF + PostgreSQL + Redis (cache)
- Templates + HTMX + `tokens.css` (Persian RTL, Vazirmatn)
- Docker Compose for local/prod-like runs
- OpenAPI via `drf-spectacular`

## Why not Next.js / Tailwind in MVP

Server-rendered Django ships faster for SEO + forms + dashboards.
DRF `/api/v1/` keeps a clean boundary for a future independent frontend.
Starter `persian-ui` and CSS token tests conflict with introducing Tailwind.

## App boundaries

| App | Owns |
|-----|------|
| `accounts` | User (phone, role, OTP), auth screens |
| `locations` | Province, City |
| `catalog` | Service (sign types) |
| `vendors` | Vendor profile, services M2M, public page |
| `requests` | ProjectRequest, wizard |
| `quotes` | Quote, accept/reject |
| `orders` | Thin Order after accept |
| `portfolio` | PortfolioItem |
| `reviews` | Review + rating rollup |
| `notifications` | Provider interface + event dispatch |
| `payments` | Subscription / lead / featured scaffolds |
| `analytics` | Pluggable event tracker |
| `common` | TimeStampedModel, SEO helpers, health |
| `core` | Settings, URLconf, API versions |

## Layers

- **Model / QuerySet** — state and invariants
- **services.py** — multi-model writes, `transaction.atomic`, `on_commit` side effects
- **selectors.py** — read paths (matched requests, dashboard KPIs)
- **forms / serializers** — validation at the boundary
- **views** — orchestration only
- **Signals** — light side effects only (e.g. vendor rating cache)

## Auth

Phone OTP via `PhoneOTP` + `SmsProvider` protocol (`ConsoleSmsProvider` in development).
Rate-limited send/verify. Session auth for HTML; same session for DRF.

## Matching

Approved, active vendors whose `services` and `city` intersect the request see it in the vendor feed.

## Monetization / pricing scaffolds

Models exist without payment gateways:
`SubscriptionPlan`, `VendorSubscription`, `LeadPurchase`, `FeaturedPlacement`, `PriceEstimateConfig`.

## Notifications

`NotificationService.notify(event, user, context)` fans out to registered providers (console stub today; SMS/Email/WhatsApp/Telegram later).

## Analytics

`track(event_name, payload)` — console/noop provider; swap later.
