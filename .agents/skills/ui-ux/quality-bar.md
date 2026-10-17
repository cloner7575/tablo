# UI quality bar

Use before calling any user-facing screen “done”.

## Composition

- [ ] Header and footer are product-complete (not starter placeholders)
- [ ] Primary nav matches real IA (no Admin/Health in public nav)
- [ ] One H1; visual hierarchy obvious without reading CSS
- [ ] Sections each have one purpose and enough content to feel real
- [ ] CTA copy matches the business goal

## Visual system

- [ ] All colors/spacing/radii/fonts come from tokens (`base.css` keeps zero
      raw colour literals — `tests/test_ui.py` checks this)
- [ ] Icons come from `static/img/icons.svg` via `components/_icon.html`;
      decorative ones are `aria-hidden`, meaningful ones carry `label`
- [ ] Accent used for actions and focus — not rainbow decoration
- [ ] Imagery or crafted atmosphere present where marketing needs it
- [ ] Missing images have intentional placeholders
- [ ] Dark/light (if supported) both readable

## Interaction

- [ ] Hover/focus/active states on controls
- [ ] Forms validate and explain errors next to fields
- [ ] Empty lists explain what happens next
- [ ] Success feedback is visible after submit

## Responsive

- [ ] 375px: no horizontal scroll, tap targets ok, hero readable
- [ ] 768px: layout adapts (not only stacked clones of desktop)
- [ ] 1024px+: max width respected; hero not sparse-and-broken

## Direction (any language)

- [ ] New CSS uses logical properties; no `left` / `padding-left` / `translateX`
- [ ] Directional icons mirror (sprite defaults, or `flip=True`)
- [ ] Latin values inside translated copy are wrapped in `<bdi>` or `.ltr`

## Persian extras (if fa)

- [ ] `persian-ui` definition of done passed
- [ ] Vazirmatn self-hosted; no foreign CDN request in the network tab
- [ ] No accidental English UI strings
- [ ] نیم‌فاصله and Persian punctuation correct («…»، ؟، ٪)
- [ ] Tel/WhatsApp reachable in one tap; phone numbers not reversed
- [ ] Jalali dates and تومان prices wherever numbers show
- [ ] Checked at 375px **in RTL**, not only LTR

## Fail examples (rewrite)

| Symptom | Fix |
|---------|-----|
| English skip/nav | Persian copy; remove starter links |
| Giant Latin deco word | Real photo, pattern, or brand mark |
| Grey empty tiles | Seed media or designed empty state |
| Orbitron / Inter on fa site | Vazirmatn / Estedad in tokens |
| One long homepage dump | Split sections; move secondary content below fold |
