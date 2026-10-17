---
name: persian-ecommerce
description: >-
  Persian e-commerce patterns for this Django starter — shop apps, Toman as
  default currency, thousand-separated prices, catalog/cart/checkout with fa/RTL.
  Use when building فروشگاه، shop، ecommerce، قیمت، تومان، سبد خرید، or Iranian
  storefronts on this base.
---

# Persian e-commerce (فروشگاه)

For shop / ecommerce products on this starter when the UI is Persian (or the user asks for an Iranian storefront).

## Hard rules — money

1. **Default currency is تومان (Toman), not ریال.** Label UI and model `verbose_name`s with تومان unless the user explicitly chooses ریال.
2. Store amounts as **integers** (whole تومان). No `Decimal`/`Float` for catalog prices unless the user requires subunits.
3. **Always** show prices with thousand separators (three-digit groups), e.g. `185,000 تومان` or `۱۸۵٬۰۰۰ تومان`. Never print raw `185000 تومان` in templates.
4. Zarinpal and many Iranian gateways expect **ریال** (تومان × ۱۰). Convert only at the payment boundary; keep the domain model in تومان.

```python
amount_rial = amount_toman * 10  # when calling the gateway
```

## Display helpers (this starter)

```django
{% load persian %}
{{ product.price|toman }}              {# 185,000 تومان #}
{{ product.price|toman|fa_digits }}    {# ۱۸۵٬۰۰۰ تومان #}
{{ line.line_total|toman:"" }}         {# 185,000  (no suffix) #}
{{ order.total_amount|toman }}
```

Pick Persian or Latin digits once and use it on every price in the product.
Prices in a column (cart, invoice, order list) line up only with
`font-variant-numeric: tabular-nums`. Order numbers and tracking codes stay
Latin and isolated: `<bdi>{{ order.number }}</bdi>`.

Python:

```python
from apps.common.persian import format_toman

format_toman(185000)  # "185,000 تومان"
```

Settings (optional overrides in `.env`):

- `DJANGO_CURRENCY_LABEL=تومان` (default)
- Prices remain integers in the DB regardless of label

## Domain layout

For shops that may grow, split apps (see `persian-shop-playbook` / `domain.md`):

| App | Owns |
|-----|------|
| `apps.catalog` | Category / Product / variants / home CMS; `product_to_dict`; seed |
| `apps.cart` | DB `Cart` + `CartItem` (user XOR session); merge on login |
| `apps.orders` | `Order` / `OrderItem` snapshots; checkout create (no stock decrement) |
| `apps.payments` | `Payment` + Zarinpal; stock decrement on paid verify |
| `apps.panel` | Staff UI only |

Tiny MVPs may start thinner, but do not grow a single fat `apps/shop` with everything.

Models subclass `apps.common.models.TimeStampedModel`. Dates shown to users → Jalali (`persian-locale`).

## Checkout / payment

- Require login before pay unless the product says otherwise
- Idempotent verify (`select_for_update` on `Payment` / `Order`)
- Secrets only from env (`ZARINPAL_MERCHANT_ID`, sandbox flag)
- After paid: `transaction.on_commit` → Celery notify if Celery is in the product

## UI

- `fa` + RTL + self-hosted Vazirmatn → **`persian-ui`** and its
  [rtl-engineering.md](../persian-ui/rtl-engineering.md)
- Full cream shop look → **`persian-shop-playbook`** + its **`design.md`** (do not freestyle a SaaS palette)
- One primary CTA per view. On a PDP that is «افزودن به سبد خرید» — everything
  else is secondary
- Write every state: empty cart، empty catalog، ناموجود، خطای پرداخت،
  پرداخت موفق. A shop with an undesigned empty cart is unfinished
- Stock and variant feedback must be immediate and Persian
  («این سایز موجود نیست»), not a silent disabled button
- Checkout is the highest-anxiety screen: show the total, the address, and the
  gateway you are about to send the user to
- Seed demo data with `manage.py seed_shop` when a seed command exists

## Do not

- Default new shops to ریال
- Show unformatted integers as prices
- Put gateway merchant IDs in code or templates
- Fork a parallel `config/` package or change `AUTH_USER_MODEL`
- Skip `design.md` and invent empty product cards / dark-mode cream flips

## Related

- Full NightRuby-class shop + reusable UI → `persian-shop-playbook` ([design.md](../persian-shop-playbook/design.md))
- Persian RTL UI quality bar → `persian-ui`
- Jalali / fa locale → `persian-locale`
- Product intake → `product-intake`
- DRF catalog → `django-rest-framework`
- HTMX cart partials → `htmx-patterns`
