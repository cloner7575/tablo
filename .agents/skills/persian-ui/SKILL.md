---
name: persian-ui
description: >-
  Production-grade Persian (fa) RTL UI/UX on this Django starter — Vazirmatn
  typography, direction and bidi engineering, Persian numerals, Iranian chrome
  and trust patterns, forms, and a hard quality bar against translated
  skeletons. Use when LANGUAGE_CODE is fa, PRODUCT.md is Persian/RTL, or the
  user asks for طراحی فارسی، UI فارسی، RTL، سایت شرکتی، لندینگ، فرم تماس،
  گالری، بلاگ، یا طراحی سایت ایرانی.
---

# Persian UI (fa / RTL)

Ship a site an Iranian visitor reads as **native**, not as an English starter
with Persian words in it. Two failure modes to design against:

1. **A translated skeleton** — starter layout, Latin fonts, English nav leftovers.
2. **A shell with no substance** — gradient hero, two buttons, empty grey boxes.

Pair with `ui-ux` (tokens, components, a11y). Mechanics — fonts, direction,
numerals, bidi, forms — live in **[rtl-engineering.md](rtl-engineering.md)**.
Page recipes live in **[corporate-sites.md](corporate-sites.md)**. Cream shops
follow `persian-shop-playbook/design.md` instead of freestyling.

## Workflow

1. **Read `PRODUCT.md`** — brand, audience, city, mood. No `PRODUCT.md` yet →
   run `product-intake` first.
2. **Switch the product to fa** (`DJANGO_LANGUAGE_CODE=fa`,
   `DJANGO_TEXT_DIRECTION=rtl`, `DJANGO_TIME_ZONE=Asia/Tehran`) and
   **replace the font** with Vazirmatn before judging any screen — Latin type
   makes every Persian layout look wrong.
3. **Direction** from Pro Max, then override its Latin display fonts:
   ```bash
   python3 .cursor/skills/ui-ux-pro-max/scripts/search.py "<industry> <mood>" --design-system -p "$SITE_NAME"
   ```
4. **Map into `static/css/tokens.css`** — colours, type scale, spacing. Never
   raw hex in `base.css`.
5. **Compose whole pages** — header → hero → sections that each do one job →
   footer. Then pass the [definition of done](#definition-of-done).

## Hard rules

| Topic | Rule |
|-------|------|
| Direction | `dir="{{ TEXT_DIRECTION }}"` from settings, never hardcoded. Logical CSS only: `margin-inline`, `inset-inline-start`, `text-align: start` |
| Type | Vazirmatn (Estedad for display), self-hosted under `static/fonts/`. Two families maximum |
| Assets | **Self-host everything.** Google Fonts, jsDelivr and unpkg are slow or unreachable from Iran — a CDN dependency is a blank page for your user |
| Copy | Every user-facing string in Persian: nav, buttons, skip link, empty states, errors, `aria-label`, `<title>`, meta description |
| نیم‌فاصله | می‌شود، کتاب‌ها، برنامه‌ریزی — ZWNJ is a spelling requirement, not a nicety |
| Punctuation | `،` `؛` `؟` «گیومه» `٪`. No ASCII commas or straight quotes in Persian sentences |
| Numerals | Persian digits in prose and prices; Latin + `dir="ltr"` for phones, codes and inputs |
| Dates | Jalali only for end users (`{{ dt|jalali }}`) — see `persian-locale` |
| Money | تومان with thousand separators (`{{ price|toman }}`) — see `persian-ecommerce` |
| Contact | Phone reachable in one tap from every page; WhatsApp deep link; Instagram is usually the main social channel in Iran |
| Maps | Neshan or a static image before Google Maps embeds |
| Trust | Commercial sites: نماد اعتماد الکترونیکی (enamad) and ساماندهی placeholders in the footer, with real links once the client has them |
| Forms | Visible Persian labels, `inputmode`/`autocomplete` set, errors next to fields, Persian success message |
| Admin | Persian `verbose_name` / `verbose_name_plural` when the product is fa-first |

## Design direction

Iranian users skim on mobile, on an unreliable connection, and decide in the
first viewport whether the business is real. So:

- **Brand first.** The name (as a wordmark, not a serif fallback) is the
  hero-level signal. Remove the nav — the page should still be identifiable.
- **One conversion path.** سفارش، مشاوره، تماس، خرید — pick one and repeat it.
- **Evidence over adjectives.** Real photos of the workshop/clinic/product beat
  «کیفیت بی‌نظیر». No invented «۵۰۰+ پروژه» or «۹۸٪ رضایت».
- **Mobile is the design, desktop is the adaptation.** Most Iranian traffic is
  mobile; a sticky call bar is normal, a 1400px hero is not the starting point.
- **Weight over decoration.** Persian text at heavier weights and generous
  leading reads better than thin type with glow effects.

Per-industry atmospheres and page-by-page recipes: [corporate-sites.md](corporate-sites.md).

## Quality bar

**Reject and rewrite when you see:**

- Starter leftovers: English `Home / Admin / Health` nav, "A reusable Django base"
- Latin decorative words as the hero identity («NEON», «LUXURY») for a Persian brand
- Pro Max Latin display fonts still set as the UI font
- A hero that is only a gradient and text — no photography, no crafted brand plane
- Empty grey boxes labelled «گالری», or an undesigned empty state
- Thin footer: one sentence, no phone, no address, no links
- Desktop-only polish that collapses into an unreadable stack at 375px
- Purple-on-white / cream-serif-terracotta AI clichés nobody asked for

**Accept when:**

- Persian text is set in a Persian face, at ~1.8 leading, with zero tracking
- Each section has one job, real Persian copy, and spacing from tokens
- Header and footer look like a real Iranian business site (تلفن، واتساپ، شهر، اینستاگرام)
- Empty, loading, error and success states are all written in Persian
- Motion is 2–3 intentional cues and respects `prefers-reduced-motion`
- The page works with images blocked and on a slow connection

## Definition of done

```bash
# 1. No English strings left in the templates you touched
rg -n "[A-Za-z]{4,}" templates/ --glob '!*.txt' | rg -v "href|src|class|hx-|aria-|csrf|static|url|block|endblock"

# 2. Renders and stays green
DJANGO_LANGUAGE_CODE=fa DJANGO_TEXT_DIRECTION=rtl .venv/bin/python manage.py runserver
.venv/bin/pytest && .venv/bin/ruff check .
```

- [ ] Font is Vazirmatn, self-hosted, preloaded; no `fonts.googleapis.com` request
- [ ] `dir` comes from settings; no hardcoded `rtl` and no `translateX` in new CSS
- [ ] نیم‌فاصله and Persian punctuation correct in all copy you wrote
- [ ] Dates Jalali, prices تومان with separators, phones `<bdi dir="ltr">`
- [ ] Header + footer complete for this product type, contact one tap away
- [ ] Empty / loading / error / success states written in Persian
- [ ] 375 / 768 / 1024 checked **in RTL**, no horizontal scroll
- [ ] `ui-ux` a11y bar still holds: skip link, landmarks, labels, `:focus-visible`
- [ ] Brand test passes: hide the nav, the first viewport still says who this is

## Do not

- Adapt the starter home template with one Persian headline and call it a design
- Leave `Inter` / `Roboto` / `Orbitron` as the primary face because Pro Max said so
- Use emoji as icons — the sprite plus `components/_icon.html`
- Hardcode `dir="rtl"`, or add `text-transform: uppercase` to Persian text
- Load fonts, icons or JS from a foreign CDN
- Invent statistics, certificates, or client logos

## Related

- Direction, fonts, numerals, bidi, forms → **[rtl-engineering.md](rtl-engineering.md)**
- Page recipes for corporate/marketing → **[corporate-sites.md](corporate-sites.md)**
- Tokens, components, a11y → `ui-ux`; design intelligence → `ui-ux-pro-max`
- Jalali and locale → `persian-locale` · تومان and shops → `persian-ecommerce`
- Full NightRuby-class shop → `persian-shop-playbook`
