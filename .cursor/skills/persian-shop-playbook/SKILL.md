---
name: persian-shop-playbook
description: >-
  End-to-end playbook to build Iranian Persian RTL shops like NightRuby/falii:
  cream storefront, dark cyan /panel/, size×color variants, session/DB cart,
  Zarinpal, Jalali, تومان. Use when creating فروشگاه آنلاین, online shop,
  NightRuby, falii, storefront, پنل ادمین, catalog, PDP, cart, checkout,
  or when the user wants a reusable shop design system / design.md.
---

# Persian shop playbook (NightRuby / falii)

One entry point for shops that should feel like **[falii.ir](https://falii.ir/)** / NightRuby:
cream linen storefront + dark staff `/panel/` + photo hero + 4:5 product photos + Alpine cart + Zarinpal.

Read this skill first. Then open only the section files you need. Do **not** invent a generic SaaS shop UI.

**Local reference repo (when present):** `/home/alisafari/Desktop/nightruby` — copy `templates/`, `static/`, Tailwind configs; do not reconstruct from memory.

## Read order

1. **[design.md](design.md)** — UI system locked to NightRuby `input.css` + falii. **Before any HTML/CSS.**
2. [starter-adapter.md](starter-adapter.md) — map onto `apps/shop` + `apps/panel`
3. [domain.md](domain.md) — models / cart / order snapshots
4. [storefront.md](storefront.md) — home order, Alpine, hard rules
5. [panel.md](panel.md) — dark `/panel/`

Deep originals (personal skills — pixel authority for Tailwind clones):

| Skill | Path |
|-------|------|
| `nightruby-store` | `~/.cursor/skills/nightruby-store/` |
| `nightruby-storefront` | `~/.cursor/skills/nightruby-storefront/` |
| `nightruby-panel` | `~/.cursor/skills/nightruby-panel/` |

## Decide the target repo (before coding)

| Situation | Do this |
|-----------|---------|
| NightRuby/falii repo available | **Copy** real `store/`, `templates/`, `static/` |
| This Django **starter** | [starter-adapter.md](starter-adapter.md) + **[design.md](design.md)**. Prefer copying Tailwind/Alpine from NightRuby when user wants falii parity; otherwise map tokens → `tokens.css`/`base.css` |
| Greenfield “exactly like falii” | NightRuby stack (Tailwind ×2, Alpine, single `store` app). See [domain.md](domain.md) |

Always run **`product-intake`** first if `PRODUCT.md` is empty.

After intake: **write project-root `design.md`** from this skill’s design.md (brand / accent only).

## Non-negotiables (every shop)

1. `html lang="fa" dir="rtl"` · `Asia/Tehran` · user dates **Jalali**
2. Money = integer **تومان**; thousand groups + `تومان`; storefront prefers **Persian digits**; gateway = تومان × ۱۰ ریال
3. Sellable unit = **variant** (size × optional color). Colors are **per-product**
4. `OrderItem` is a **snapshot**
5. Day-to-day ops use custom **`/panel/`** (dark RTL)
6. Storefront ≠ panel — never mix cyan `#00E5FF` into cream storefront
7. Storefront: cream `#F5F0E8` + charcoal `#14110F` + gold `#A67C52` (or brand accent) · Estedad+Vazirmatn · **product photos 4:5** · photo/theme hero · 5-tab mobile nav · light-only tokens
8. Card CTA = cream outline `.btn-add-cart`; primary CTA = charcoal `.btn-ruby-solid`
9. Thin views; logic in services / `product_to_dict`
10. Compare against falii.ir before calling UI done

## Fast path — “مثل falii” on this starter

```
□ PRODUCT.md confirmed
□ Open falii.ir + nightruby templates/input.css (if present)
□ Copy skill design.md → project design.md (brand / accent swap only)
□ Apps: catalog + cart + orders + payments + panel (not one fat shop)
□ Prefer copy NightRuby CSS/templates; else paste tokens into tokens.css
□ Shell: header (logo), footer, mobile nav, search modal, cart drawer
□ product_card with real/stock photos (4:5) — not jar theater
□ Home: hero slider shell + features + categories + new arrivals …
□ product_to_dict + seed with images; DB cart + stock-on-paid
□ Browser-check vs falii structure (or brand-strong Fitile-class path)
□ Then panel / Zarinpal / CMS depth
```

## Build checklist

```
Product
- [ ] PRODUCT.md confirmed
- [ ] design.md in project root (from playbook + brand swap)
- [ ] Target: copy NightRuby vs brand-strong identity path

Backend
- [ ] apps.catalog / cart / orders / payments (+ panel)
- [ ] Models per domain.md ownership
- [ ] DB Cart + merge-on-login; stock decrement on verify
- [ ] Paginated catalog selectors; product_to_dict
- [ ] seed_shop in catalog

Storefront (design.md FIRST)
- [ ] Light-only cream tokens + body radial wash
- [ ] Shell + logo + mobile nav + search + cart drawer
- [ ] Photo hero shell; category circles; 4:5 photo cards; cream .btn-add-cart
- [ ] Catalog / PDP / cart / checkout
- [ ] Mobile checklist pass

Panel
- [ ] /panel/ login, KPIs, orders, products

Pay
- [ ] Checkout → Zarinpal sandbox → idempotent verify → stock decrement
```

## Stack defaults

### NightRuby clone (“دقیقاً مثل falii”)

Django 6 · Python 3.12 · PostgreSQL · Tailwind 3.4 ×2 · Alpine 3.14 · Chart.js · Zarinpal v4 · WhiteNoise · **no** DRF/Celery/custom user unless asked.

### This starter

Keep `apps.*`, `accounts.User`, `TimeStampedModel`, split settings. Commerce = **catalog / cart / orders / payments**. Map [design.md](design.md) into tokens/theme CSS **or** vendor NightRuby Tailwind. Optional DRF/Celery/Docker only if intake selected them.

## Quick UI map

| Surface | Palette | Notes |
|---------|---------|--------|
| Storefront | cream `#F5F0E8`, charcoal `#14110F`, gold `#A67C52` | Photos + light only |
| Panel | bg `#0f0f10`, cyan `#00E5FF` | Separate CSS |

## Do not

- Skip design.md / freestyle purple SaaS
- Dark-mode cream flips
- Jar CSS as the default product visual
- Empty image cells / text-only mobile chrome
- Solid charcoal add-to-cart on every card
- Panel cyan on storefront; crimson “ruby”; Inter/Roboto
- Sticky PDP CTA under the bottom nav
- Change `AUTH_USER_MODEL` away from `accounts.User`

## Related

`product-intake` · `persian-locale` · `persian-ecommerce` · `starter-architecture` · `ui-ux`
