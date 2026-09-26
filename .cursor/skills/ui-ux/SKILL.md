---
name: ui-ux
description: >-
  Production UI/UX for this Django starter — complete page compositions, tokens,
  accessibility, forms, and Pro Max → CSS mapping. Rejects skeleton/starter
  screens. Use when editing templates, CSS, JS, HTMX, landing pages, dashboards,
  restyling, or reviewing look-and-feel. For Persian/RTL also load persian-ui.
---

# UI/UX for Django screens

You are the product **designer and implementer**. A 200 OK with bare markup is a failure. Ship screens that look intentional, complete, and usable.

For a **new product**, finish `product-intake` (`PRODUCT.md`) first. Then choose look with `ui-ux-pro-max` and implement here. If `PRODUCT.md` is `fa` / RTL → also follow **`persian-ui`** (mandatory).

## Quality bar (non-negotiable)

**Do not mark UI work done if any of these are true:**

- Page still reads like the Django starter (“reusable base”, English chrome, Health link in primary nav)
- First viewport is empty gradient + headline with no brand craft
- Decorative Latin words stand in for design (e.g. giant “NEON” / “SHOP”)
- Missing designed empty / error / success states
- New colors sprinkled outside `tokens.css`
- Pro Max Latin display font used as the primary UI face on a Persian product
- Only “works on my laptop width” — 375px ignored

**Done means:** full chrome (header + footer), coherent tokens, hierarchy, one primary action, responsive, accessible, and (for fa) passes `persian-ui` definition of done.

Detail checklist: [quality-bar.md](quality-bar.md).

## Workflow

1. **Intent** — Who is this page for? What is the one action?
2. **Direction** — Pro Max design-system (or locked `design.md` for cream shops):
   ```bash
   python3 .cursor/skills/ui-ux-pro-max/scripts/search.py "<product industry mood>" --design-system -p "$SITE_NAME"
   python3 .cursor/skills/ui-ux-pro-max/scripts/search.py "error summary validation" --domain ux
   ```
3. **Tokens first** — Map palette into `static/css/tokens.css` before large template CSS.
4. **Compose** — Full page: header → content sections → footer. Extend `templates/base.html`.
5. **States** — Empty, loading, error, success for every list/detail/form.
6. **Verify** — [quality-bar.md](quality-bar.md) + a11y list below. Browser check when available.

Persist Pro Max with `--persist` only if the user wants a lasting design-system folder. Never `--force` without asking.

Persian cream shops: do **not** freestyle from Pro Max — follow `persian-shop-playbook/design.md` (and project `design.md`).

## What the starter already ships

The shell is a finished design system, not a blank slate. Extend it; do not
rebuild it next to itself.

**Direction** (from Pro Max, `developer tool · technical · minimal`): cool
slate neutrals, emerald accent, IBM Plex Sans with JetBrains Mono for anything
technical. Both fonts are self-hosted variable woff2 in `static/fonts/`.

| Layer | Where | Notes |
|-------|-------|-------|
| Tokens | `static/css/tokens.css` | Type scale, space (4px base), radii, shadows, motion, layout, light + dark colour roles |
| Components | `static/css/base.css` | No raw colours allowed — a test enforces it |
| Icons | `static/img/icons.svg` + `components/_icon.html` | Lucide geometry, `currentColor`, decorative by default |
| Buttons | `components/_button.html` | `variant` primary/secondary/ghost/danger, `size="sm"`, `full=True` |
| Fields | `components/_field.html` | Label, required marker, help text, errors, `aria-*` from Django |

Class inventory in `base.css`: `.container` `.stack` `.cluster` `.grid-auto`
`.card` `.card--interactive` `.panel` `.badge` `.hero` `.eyebrow` `.lede`
`.section-title` `.status` `.steps` `.messages` `.form-errors` `.auth-card`
`.error-page` `.htmx-indicator` `.visually-hidden` `.ltr` `.icon--flip`.

Do not pass `block=...` to `_button.html`: Django binds `block` to the current
BlockNode inside every `{% block %}`, so the flag is named `full`.

### Direction

`<html dir>` comes from `TEXT_DIRECTION`, and the stylesheet already carries an
RTL layer: tracking reset to zero, leading raised to 1.8, direction-bearing
sprite icons mirrored, Latin fragments (`code`, `.ltr`) bidi-isolated, and
tel/email/url/password inputs forced LTR. Keep it working:

- Logical properties only — `margin-inline`, `inset-inline-start`, `text-align: start`
- Animate with `translate: 0.2em 0`, not `transform: translateX()`, so mirroring
  and motion do not overwrite each other
- Mirror a new directional icon with `flip=True` on `components/_icon.html`
- Wrap Latin values inside translated copy in `<bdi>`

Persian products: the whole engineering checklist is in
`persian-ui/rtl-engineering.md`.

## Django adapter (this starter)

Pro Max often assumes Tailwind. **This repo is Django templates + `static/css`.** Do not add Tailwind/shadcn/React SPA unless asked.

| Pro Max output | Apply here |
|----------------|------------|
| Color roles | `static/css/tokens.css` (`--color-bg`, `--color-ink`, `--color-accent`, …). Light **and** dark when product supports both |
| Font pairing | `--font-sans` / `--font-display`; Persian → Vazirmatn/Estedad via `persian-ui` |
| Sections | `templates/pages/` or app templates extending `base.html` |
| UX / a11y | Templates + CSS |
| Utilities | Translate into `base.css` / page CSS classes |
| Icons | Inline SVG (Heroicons/Lucide/Phosphor), never emoji-as-icon |

## Source of truth

- Tokens: `static/css/tokens.css`
- Chrome: `templates/base.html`, `partials/_header.html`, `_footer.html`, `_messages.html`
- Primitives: `components/_button.html`, `components/_field.html`
- Intelligence: `.cursor/skills/ui-ux-pro-max/`

## Hierarchy and layout

- One `<h1>` per page. One primary action.
- Prefer existing layout primitives (`.stack`, `.site-main`, …); add page CSS when primitives are not enough — unfinished “card grid of docs” is not a product UI
- Spacing from `--space-*` only
- Reading measure ~40rem for long Persian/English prose
- Marketing first viewport: brand-led, sparse (see user frontend rules + `persian-ui/corporate-sites.md`)

## Accessibility (must pass)

- Skip link → `#main` (localize label for fa)
- Landmarks: header / labeled `nav` / `main` / footer
- `:focus-visible` via `--focus`; never `outline: none` without replacement
- Every input has a visible `<label for>`
- Failures: `role="alert"`; confirmations: `role="status"` / `aria-live="polite"`
- Buttons name the action
- Images: meaningful `alt`, or `alt=""` if decorative
- Contrast ≥ 4.5:1 for body text
- `prefers-reduced-motion` respected
- `cursor: pointer` on clickable non-links

## Forms

- `components/_field.html` per field; `non_field_errors` above
- Labels visible; placeholders are not labels
- `autocomplete` on name/email/tel/password
- Touch target ≥ ~2.75rem
- HTMX: `hx-indicator`, `hx-disabled-elt="this"`, partial on `HX-Request`

## Anti-patterns

- Inline `style=` except true one-offs
- Physical offsets (`left`, `padding-left`, `translateX`) — they break RTL
- Icon-only controls without accessible name
- Modal/drawer without focus trap + Escape
- Bootstrap/Tailwind CDN fighting tokens
- Mixing a new Pro Max style into templates without updating tokens first
- Shipping half a redesign (“I’ll polish later”)

## Integration

- `ui-ux-pro-max`, `persian-ui` (fa), `django-templates`, `htmx-patterns`, `django-forms`, `code-reviewer`
- Shop UI lockfile: `persian-shop-playbook`
