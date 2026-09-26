# Adapter: NightRuby / falii → this Django starter

Use when the workspace is the **Base/core starter** (or a clone): `apps/`, `core/settings/`,
`AUTH_USER_MODEL = accounts.User`.

**UI source of truth:** [design.md](design.md) (synced from NightRuby `input.css` + https://falii.ir/).  
**If `/home/alisafari/Desktop/nightruby` (or another NightRuby checkout) is available:** copy real
`templates/`, `static/src/input.css` (or built `main.css`), `static/js/main.js`, fonts — do not freestyle.

## Keep starter architecture

| NightRuby | This starter |
|-----------|----------------|
| `core/` + single `store/` app | `core/` + **bounded apps** below |
| Built-in User + UserProfile | `apps.accounts.User` — extend with profile OneToOne if phone needed; **never** change AUTH_USER_MODEL |
| `store/utils/jalali.py` | Prefer `jdatetime` + `apps.common.persian` |
| Tailwind storefront + panel | Prefer **copy NightRuby Tailwind build** when user wants falii parity. Fallback: [design.md](design.md) → tokens + theme CSS |
| Alpine cart/PDP | Required for NightRuby-class; form POST only for thin MVP |
| `/panel/` under `store/panel/` | `apps/panel/` with `app_name='panel'` |
| Seeds `seed_store` | `manage.py seed_shop` (lives in `apps.catalog`) |

Models subclass `TimeStampedModel`.

## App split (scale path — required for large shops)

Do **not** put catalog + cart + orders + payments in one fat `apps/shop`. Use:

```
apps/catalog/       # Category, Product*, CMS home models; adapters; seed; storefront catalog views
apps/cart/          # DB Cart + CartItem; merge-on-login; cart views/API
apps/orders/        # Order + OrderItem snapshots; checkout service
apps/payments/      # Payment + Zarinpal; verify/idempotency; Celery notify
apps/panel/         # Staff UI only (no models)
apps/accounts/      # User + login/register
apps/common/        # TimeStampedModel, persian helpers, /health/
templates/          # mirror NightRuby component names when possible
static/css/…        # cream storefront + separate panel CSS
design.md           # project copy of playbook design.md (brand-swapped)
```

**URL namespace:** keep public paths under `/shop/` with `app_name = "shop"` via a storefront URL module (usually in `apps.catalog`) so templates/tests stay stable.

**Home:** `common.views.home` delegates to `catalog.views.home` — never import a removed monolith.

### Migrating from a legacy `apps/shop` monolith

1. Create the four domain apps and move models/services by ownership.
2. Wire `INSTALLED_APPS` + context processor from `apps.cart`.
3. Data-migrate or re-seed; remove `apps/shop` last.
4. Stock: check on cart mutate; **decrement on successful payment verify**, not at checkout create.

## Token mapping (no Tailwind)

Paste [design.md](design.md) §2 into `static/css/tokens.css`. The starter's
`[dir="rtl"]` layer (zero tracking, 1.8 leading, mirrored icons, bidi isolation,
LTR phone inputs) keeps working underneath — do not strip it, and do not
re-add Latin tracking to Persian headings. Details:
[persian-ui/rtl-engineering.md](../persian-ui/rtl-engineering.md).

Critical:

- `color-scheme: light` + `<meta name="color-scheme" content="light">`
- **No** `prefers-color-scheme: dark` remapping
- Body 14px + cream radial wash
- Charcoal `.btn-ruby-solid` for primary; cream `.btn-add-cart` on cards
- Gold (or brand accent) only for accents / new badges / section line

## Brand-strong identity path (Fitile-class)

When the user wants **falii structure + own brand mood** (not a gold→accent pixel clone):

- Same shell, home order, PDP/cart quality as [storefront.md](storefront.md)
- Swap accent + photography mood in project `design.md`
- Logo image + Estedad wordmark — never a default serif fallback for the brand mark

## UI port order (avoid ugly first paint)

1. Tokens (light cream)  
2. Shell: `base.html`, header (logo image or short mark), footer, mobile nav, **search modal + cart drawer**  
3. `_product_card.html` with **real photos** (4:5)  
4. Home: hero **slider shell** + features + categories + new arrivals (falii order)  
5. Catalog (paginated) / PDP / cart / checkout  

Then deepen Alpine, CMS sections, panel tabs.

## Intake defaults for fa shops

When user says «مثل NightRuby / مثل falii / فروشگاه کامل»:

- Language fa · RTL · Asia/Tehran · Jalali · تومان  
- Write project `design.md` from this playbook’s design.md (brand + accent only)  
- Prefer copying from the NightRuby repo when present  
- Custom `/panel/` · Zarinpal sandbox · variants · home CMS  
- DRF/Celery/Docker: only if they ask  
- Use the **multi-app** layout above (not a single shop app)

## MVP slices (starter-friendly)

1. Cream tokens + falii shell + photo cards + **DB cart** + Zarinpal  
2. Variants + PDP size/color + Alpine cart drawer  
3. Custom `/panel/` dashboard + orders + products  
4. Full home stack (collections, sale, promo, magazine, IG)  

## Related

`product-intake` · `persian-locale` · `persian-ecommerce` · `starter-architecture` · `ui-ux`
