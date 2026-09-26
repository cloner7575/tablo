# Persian shop design system (NightRuby / falii)

**Authority:** live look = [falii.ir](https://falii.ir/). Pixel / class / shell source =
`/home/alisafari/Desktop/nightruby` (`tailwind.config.js`, `static/src/input.css`, `templates/`).

**Audience:** agents building Iranian RTL shops on this Django starter **or** cloning NightRuby.

**Goal:** cream linen storefront that feels like falii — soft oat bands, charcoal “ruby”, gold accents,
photo hero, **real product photos** at 4:5, Alpine cart/search, 5-tab mobile nav — not a SaaS landing,
not purple, not jar-only MVP chrome sold as the final look.

When `PRODUCT.md` exists, copy this file to project-root `design.md` and change **only** brand bits
(logo/mark, accent hex if asked, category names, pitch). Keep structure and class semantics.

---

## 0. Source of truth (do not invent)

| Artifact | Path / URL |
|----------|------------|
| Live reference | https://falii.ir/ |
| Tokens + theme | `nightruby/tailwind.config.js` |
| Component CSS | `nightruby/static/src/input.css` (~2800 lines) |
| Shell | `nightruby/templates/base.html` |
| Header / footer / mobile nav / card / hero | `nightruby/templates/components/*.html` |
| Home order | `nightruby/templates/home.html` |
| Deep skill (Tailwind clone) | `~/.cursor/skills/nightruby-storefront/` |

**If the NightRuby repo is available:** copy templates + `input.css` / built `main.css` + Alpine `main.js`
instead of reconstructing from memory.

**Starter CSS path:** map the same tokens and class names into `static/css/tokens.css` + `base.css`.
Do not invent parallel BEM. Prefer Tailwind+Alpine when the user wants “exactly like falii”.

---

## 1. Mental model

| Layer | NightRuby | Starter CSS |
|-------|-----------|-------------|
| Tokens | Tailwind `theme.extend` + `:root` in `input.css` | `tokens.css` (`color-scheme: light` only) |
| Components | `@layer components` in `input.css` | `base.css` — same class names |
| Panel | `static/src/panel.css` + cyan | `panel.css` — **never** on storefront |
| Shell | `base.html` + Alpine `appStore` | same include order; Alpine when matching falii UX |
| Cards | `product_card.html` + real `image_url` | same anatomy; soft gradient only under/without photo |
| Money | `fa-IR` / Persian digits + `تومان` | `{% load persian %}` + `persian_digits=True` |

Desktop chrome breakpoint: **`lg` = 1024px**. Below: mobile header + bottom nav. Never treat `md` as desktop.

---

## 2. Tokens (verbatim from NightRuby)

```css
:root {
  color-scheme: light;
  --ruby: #14110f;           /* charcoal — NOT crimson */
  --ruby-dark: #0a0908;
  --ruby-deep: #050504;
  --ruby-light: #5a534c;
  --ruby-glow: #f3ebdf;
  --ruby-muted: #8a8176;
  --gold: #a67c52;           /* warm bronze highlights — default NightRuby */
  --gold-light: #d4c2a6;
  --background: #f5f0e8;
  --cream: #fffefb;
  --linen: #faf6f0;
  --oat: #f0e9df;
  --dusty-rose: #ebe3d7;
  --rose: #f4eee6;
  --footer: #e9e1d5;
  --border: #d6cbbc;
  --search-bg: #f4eee6;
  --stone: #c2b5a3;
  --muted: #5a534c;

  --font-sans: "Vazirmatn", Tahoma, sans-serif;
  --font-display: "Estedad", "Vazirmatn", Tahoma, sans-serif;
  --max: 82.5rem;            /* 1320px */
  --radius-card: 16px;
  --radius-section: 24px;
  --radius-btn: 10px;
  --radius-pill: 9999px;
  --header-h: 4.25rem;
  --mobile-nav-h: 4.25rem;
  --shadow: 0 8px 28px rgb(20 17 15 / 0.08);
  --shadow-lg: 0 16px 44px rgb(20 17 15 / 0.12);
  --duration: 350ms;
}
```

**Brand accent swap (example — فیتیله شاپ):** keep cream + charcoal; replace `--gold` / gold UI with pink
`#C45A7A` and light `#E8B4C4`. Do **not** change `--ruby` to crimson or panel cyan.

Starter alias mapping (optional):

| NightRuby | Starter tokens often used |
|-----------|---------------------------|
| `--background` | `--color-bg` |
| `--cream` | `--color-bg-elevated` |
| `--ruby` | `--color-ink` / `--color-primary` |
| `--gold` | `--color-accent` |
| `--border` | `--color-border` |
| `--muted` | `--color-muted` |

### Body (required)

```css
body {
  font-family: var(--font-sans);
  font-size: 14px;
  line-height: 1.7;
  color: #14110f;
  background-color: #f5f0e8;
  background-image:
    radial-gradient(ellipse 90% 42% at 50% -8%, #fffefb 0%, transparent 60%);
}
h1, h2, h3, h4 {
  font-family: var(--font-display);
  font-weight: 700;
  letter-spacing: -0.5px;
  line-height: 1.3;
}
```

Section bands: `.section-tone-a` `#FFFEFB` · `b` `#F0E9DF` · `c` `#F5F0E8` · `d` `#EBE3D7`.

**Forbidden:** `@media (prefers-color-scheme: dark)` remapping cream tokens.

---

## 3. Brand in the UI (falii pattern)

| Place | What falii does | Starter without logo asset |
|-------|-----------------|----------------------------|
| Header | **Logo image** `.logo-header` / `.logo-header-mobile` | Short mark word (e.g. `فیتیله`) — not full legal name |
| Hero H1 | CMS slide headline + accent span | Same — not necessarily the brand mark alone |
| `<title>` / footer | Brand name + slogan | `SITE_NAME` from settings |
| Eyebrow / badge | Gold (or brand accent) pill | `--gold` / swapped accent |

Brand test: first viewport = logo/mark + one headline + one primary CTA + **one strong visual**
(photo hero preferred). Removing the nav must still read as this brand.

---

## 4. Shell (copy order from `base.html`)

```
html lang=fa dir=rtl
meta csrf-token
fonts.css → main.css   (or tokens.css → base.css)
body.has-mobile-nav  x-data="appStore"
  flash (fixed under header)
  loading_screen
  header
  main#main-content
  footer
  mobile_nav          (lg:hidden)
  search_modal
  cart_drawer
  main.js then alpine.min.js
```

Body pad: `padding-bottom: calc(4.25rem + env(safe-area-inset-bottom))` — **zero** at `lg+`.

### Header (exact falii layout)

- Sticky `top-0 z-50 border-b border-border/70 bg-cream/95 backdrop-blur-md`
- Scroll > 40px → `.header-scrolled` shadow
- **Desktop `lg+`:** CSS grid `1fr auto 1fr`
  1. Search button `.header-search` (opens modal — does not navigate)
  2. Centered logo image
  3. Cart (badge) · wishlist · `ورود / ثبت‌نام`
- Row 2: centered `.nav-link` / `.nav-link-active` (underline charcoal, RTL flip)
- **Mobile:** hamburger | logo | search + cart. Expand menu under header — **does not** replace bottom nav
- Icons: stroke ~1.35–1.5, charcoal — never emoji text «منو» / «سبد»

### Mobile bottom nav (5)

خانه · فروشگاه · علاقه‌مندی · سبد · حساب — `.mobile-nav-bar` / `.mobile-nav-item` · `lg:hidden`

### Footer

Oat/cream main · logo · tagline · socials · columns (mobile `<details>` accordion) · Enamad/Samandehi ·
dark `.footer-ruby-bar`

### Cart drawer + search modal

Required for NightRuby-class UX. Panel from **end** edge (RTL). Empty cart: bag icon + «سبد خرید شما خالی است».

---

## 5. Home composition (exact order — `home.html`)

1. `hero` — slider (themes `dark` / `light` / `photo`), ~7s autoplay, dots + arrows  
2. `features` — trust bar  
3. `categories` — round image circles  
4. `new_arrivals` — product cards + section header  
5. `home_collections` — large banner cards  
6. `sale_products`  
7. `ruby_banner` — photo + countdown (Persian digits)  
8. `home_brand_story`  
9. `best_sellers`  
10. `home_magazine`  
11. `testimonials`  
12. `instagram`

MVP may ship **1–4 + 9 + 11**, but do not invent a flat single-cream page with CSS jars as the hero.

### Hero rules (from `input.css`)

- `.hero-shell` radius **20px**, min-height ~340 → 380 → 420 (`md`/`lg`)
- Photo slides: full media + scrim + content stack
- Primary CTA: `.btn-ruby-solid` (charcoal gradient + shimmer)
- Secondary: outline / glass on photo
- Do **not** use a two-column “text + decorative jar cluster” as the falii hero substitute unless no CMS photos exist — and even then prefer a soft abstract/photo panel over jar theater

### Section chrome

Diamond SVG + `.section-title` + «مشاهده همه» · `.section-ruby-line`
(`gradient transparent → #0A0908 → #A67C52 → #0A0908 → transparent`, 16×1px)

---

## 6. Product cards (critical — match falii)

Template: `components/product_card.html` (starter: `_product_card.html`) fed by `product_to_dict`.

### Anatomy (do not invent new names)

```
article.product-card.group
  a.product-image-wrap          ← aspect 4/5
    img object-cover            ← REAL product photo (primary)
    badge تخفیف (bg-ruby) | جدید (bg-gold)
    wishlist heart button
  body
    title · color dots (max 4) · price (+ old) + تومان
    rating stars · .btn-add-cart
```

### Hard rules

| Rule | Detail |
|------|--------|
| Photos first | Cards sell with **photographs**. Soft oat gradient on `.product-image-wrap` is the stage **behind** the image |
| Aspect | Mobile/desktop card media **4:5** (`aspect-[4/5]`) |
| Hover | Card lift `-2px` + deeper shadow; image `scale-105` over 700ms |
| Add to cart | `.btn-add-cart` = **cream outline** (`bg-cream border-[#D6CBBC]`), **not** solid charcoal |
| Primary solid | `.btn-ruby-solid` only for hero / empty / checkout primary |
| No size on card | Uses `default_variant_id` |
| Prices | Persian digits preferred on storefront |
| Fallback only | If no `image_url`, show a **soft product-shaped placeholder** (gradient stage ± subtle brand mark). Do **not** make painted “jam jars” the default visual language of every shop |

### Buttons (verbatim intent)

**`.btn-ruby-solid`**

- `rounded-btn px-7 py-2.5 text-[13px] font-semibold text-white`
- `linear-gradient(135deg, #2C2622 0%, #14110F 50%, #050504 100%)`
- shadow + inset gold hairline + shimmer `::before`
- hover: `translateY(-2px)`

**`.btn-add-cart`**

- full width, cream bg, border `#D6CBBC`, charcoal text
- hover: `border-ruby-light bg-rose`

---

## 7. Catalog & PDP

### Catalog

- Page banner (dark cream box + small logo) — compact, **not** a tall marketing hero
- Category circles row
- Desktop: sticky filter sidebar + grid 2→3→4
- Mobile: filter/sort bar + bottom sheet (~92dvh)
- Alpine filter/sort on `products_json` (NightRuby v1)

### PDP

- `.nr-pdp-grid` 1 → `lg:2`
- Gallery sticky; stage square then `5/6`
- Color swatches + size chips + qty
- Desktop add: `.btn-ruby-solid.nr-pdp-cta`
- Mobile sticky CTA: `bottom: calc(4.25rem + env(safe-area-inset-bottom))` — never `bottom: 0`
- Tabs: توضیحات | راهنمای سایز | نظرات

---

## 8. Required class map (stable names)

| Class | Role |
|-------|------|
| `.container-nr` | max 1320 + horizontal padding |
| `.btn-ruby-solid` `.btn-ruby-outline` `.btn-add-cart` | Actions |
| `.product-card` `.product-image-wrap` `.product-price` `.product-color-dot` | Cards |
| `.section-header` `.section-ruby-line` `.section-tone-a`…`d` | Sections |
| `.hero-shell` `.hero-slide` `.hero-headline` | Home hero |
| `.mobile-nav-bar` `.mobile-nav-item` | Bottom nav |
| `.header-search` `.header-icon-btn` `.nav-link` `.logo-header` | Chrome |
| `.nr-pdp-grid` `.nr-size-chip` `.nr-color-swatch` `.mobile-sticky-cta` | PDP |
| `.ruby-banner` `.countdown-box` | Promo |

Logical properties only (`start`/`end`, `ps`/`pe`).

---

## 9. Money & Persian display

```python
format_toman(amount, suffix="", persian_digits=True)  # ۱۶۵٬۰۰۰
```

Gateway: `amount_rial = amount_toman * 10`. Domain stays تومان integers. Jalali for user-facing dates.

---

## 10. Anti-patterns (learned from bad starter clones)

1. **Jar theater as the brand** — falii sells with product photography + photo hero, not CSS pickle jars.  
2. **Solid charcoal add-to-cart on every card** — cards use cream outline; solid is for primary CTAs.  
3. **Text-only logo + long SITE_NAME as H1** — use logo image (or short mark).  
4. **Dark-mode cream flip** — unreadable.  
5. **Empty cream image cells** — always photo or soft gradient stage.  
6. **Panel cyan `#00E5FF` on storefront.**  
7. **Purple/indigo SaaS**, Inter/Roboto, crimson “ruby”.  
8. **Sticky CTA `bottom: 0`** under the mobile nav.  
9. **Hamburger-only mobile IA** — bottom nav is mandatory.  
10. **Skipping cart drawer / search modal** and calling it NightRuby-complete.  
11. **Treating `md` as desktop** — chrome switches at `lg` (1024).

---

## 11. Agent workflow

```
1. product-intake → PRODUCT.md confirmed
2. Read THIS design.md + open falii.ir + (if present) nightruby templates/input.css
3. Prefer copy from nightruby over freestyle CSS
4. Wire tokens (light only) → shell → product_card with photos → home stack
5. Alpine: appStore + cart drawer + search + sticky header
6. Browser-check against falii: header two-row, hero photo shell, 4:5 cards, bottom nav
7. Then panel / Zarinpal / CMS depth
```

---

## 12. Brand-swap checklist (next shop)

- [ ] Logo images (`logo-header.png`, `logo-full.png`) or short mark string  
- [ ] `SITE_NAME` / slogan in PRODUCT.md  
- [ ] Accent: keep gold **or** swap to requested mood (e.g. pink `#C45A7A`) — keep charcoal primary  
- [ ] Seed categories + **real or stock product photos** (4:5)  
- [ ] Hero CMS slides with images  
- [ ] Keep class names and shell structure identical  

Do **not** redesign tokens from Pro Max scratch for “like falii” requests.
