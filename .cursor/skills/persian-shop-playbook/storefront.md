# Storefront UI (NightRuby / falii)

**Live look:** https://falii.ir/  
**Repo authority:** `/home/alisafari/Desktop/nightruby` — copy templates + CSS when available.

**Starter CSS shops:** follow **[design.md](design.md)** first (rewritten from NightRuby `input.css` + falii).  
Use this file for home-section order, Alpine APIs, and Tailwind class names when cloning the full front.

Full pixel detail: `~/.cursor/skills/nightruby-storefront/{tokens,visual-rules,components,pages}.md`

Reproduce the look **exactly** when the user wants NightRuby-class UI. No shadcn / indigo / Inter / jar-first MVP sold as final.

**Brand-strong path (Fitile-class):** keep this skeleton (shell, home order, PDP/cart quality, Alpine). Swap gold → brand accent, photography mood, and logo in project `design.md`. Do not weaken structure while branding.

## Tokens (verbatim)

```
ruby (charcoal): #14110F  dark #0A0908  light #5A534C  glow #F3EBDF  muted #8A8176
gold: #A67C52  light #D4C2A6
background #F5F0E8  cream #FFFEFB  dusty-rose #EBE3D7  soft/oat #F0E9DF
border #D6CBBC  footer #E9E1D5  linen #FAF6F0  search-bg #F4EEE6  rose #F4EEE6
```

Type: **Estedad** display, **Vazirmatn** body (14px / 1.7). Container max **1320px**.  
Radius: card 16 / section 24 / btn 10 / pill full / hero shell 20.

Section tones: a `#FFFEFB` · b `#F0E9DF` · c `#F5F0E8` · d `#EBE3D7`

Required classes: `.btn-ruby-solid` · `.btn-ruby-outline` · `.btn-add-cart` · `.product-card` +
`.product-image-wrap` aspect **4/5** · `.mobile-nav-bar` · `.header-search` · `.section-ruby-line` ·
`.hero-shell` · `.logo-header`

## Shell order (`base.html`)

```
html lang=fa dir=rtl
body.has-mobile-nav  x-data="appStore"
  flash · loading_screen · header · main#main-content · footer
  mobile_nav (lg:hidden) · search_modal · cart_drawer
  main.js then alpine.min.js
```

Body pad for bottom nav: `padding-bottom: calc(4.25rem + env(safe-area-inset-bottom))` — none at `lg+`.

**Desktop = `lg` (1024).** Do not treat `md` as desktop.

## Hard visual rules

- Logical CSS (`start`/`end`). Currency `تومان` + prefer fa digits on storefront.
- Sticky header cream/95; after 40px scroll add shadow.
- Desktop header **two rows**: search | **logo image** | cart+wishlist+auth → centered nav.
- Mobile: hamburger | logo | search+cart — does **not** replace bottom nav.
- Bottom nav **5**: خانه، فروشگاه، علاقه‌مندی، سبد، حساب.
- Sticky PDP/cart bars: `bottom: calc(4.25rem + safe-area)` — never `bottom-0`.
- **Product cards = photographs** at 4:5. Soft oat gradient is the image stage, not the product.
- Card CTA = cream outline `.btn-add-cart`. Hero/checkout primary = `.btn-ruby-solid`.
- No size picker on product **card** — add uses `default_variant_id`.
- No panel cyan on storefront. Ruby is charcoal, not crimson.
- **No dark-mode token flip** on cream shops.
- Hero = photo/theme **slider** in `.hero-shell` (radius 20px), not decorative jar clusters.

## Alpine surface (full NightRuby)

| API | Role |
|-----|------|
| `appStore` | sticky header, search/cart/menu, cart fetch/mutate |
| `Alpine.store('app')` | wishlist localStorage |
| `productDetailPage` | size/color/qty, gallery by color, add |
| `catalogPage` | client filter/sort on products_json |
| `checkoutWizard` | آدرس → ارسال → تأیید |
| `heroSlider` / `testimonialSlider` / … | home/static |

MVP starter may begin with form POST + `app.js`, but NightRuby-class requires Alpine drawer + search.

## Home section order (exact — falii)

1 hero · 2 features · 3 categories · 4 new_arrivals · 5 collections · 6 sale ·
7 promo banner · 8 brand story · 9 best_sellers · 10 magazine · 11 testimonials · 12 instagram

MVP may ship 1–4 + 9 + 11. Alternate section tones. Do not one flat cream page.

## PDP

Grid 1 → `lg:2`. Sticky gallery + sticky info. Color swatches + size chips + qty.  
Tabs: توضیحات | راهنمای سایز | نظرات. Mobile sticky CTA above bottom nav.

## Checkout steps

آدرس / ارسال / تأیید → Zarinpal. Success: order number + ref.

## Mobile checklist (every page)

Bottom nav + active · content not under nav · sticky CTA clears nav · tap ≥40px · safe-area ·
no overflow 320px · filters as sheet · footer accordion · flashes under header · icons not raw text.
