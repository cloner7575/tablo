# Persian corporate / marketing sites

Page-by-page recipes for سایت شرکتی، لندینگ خدمات، گالری نمونه کار، بلاگ
آموزشی، فرم مشاوره. Use with `persian-ui`.

## Information architecture (default)

| Route | Purpose | Must include |
|-------|---------|--------------|
| `/` | Trust + convert | Brand hero, short proof, services or featured work, CTA to contact |
| خدمات / نمونه کار | Evidence | Filterable list, detail with story, CTA |
| بلاگ / آموزش | SEO + trust | List with Jalali dates, readable prose width |
| تماس | Lead capture | Form + phone + WhatsApp + address + working hours |
| درباره ما | Legitimacy | Real story, team or workshop photo, city |

Keep nav to 4–6 items. One primary conversion path across the whole site.

## Home composition

**First viewport** — nothing else:

- Brand at hero level (wordmark, not a serif fallback)
- One headline plus one supporting sentence
- One CTA group (primary + optional secondary)
- One dominant visual plane: real photography, workshop atmosphere, or a
  crafted brand graphic — **not** a Latin word as decoration

Not in the first viewport: KPI strips, blog teasers, long service grids,
address blocks, multi-card dashboards.

**Below the fold, in order:** خدمات → نمونه کار / گالری → چرا ما (evidence, not
adjectives) → آموزش teaser → CTA نهایی + contact block.

## Visual recipes by industry

| Industry | Atmosphere | Accent direction |
|----------|------------|------------------|
| تابلو / نئون / چاپ | Dark workshop, controlled glow | Cyan or magenta, sparingly |
| کلینیک / سلامت / زیبایی | Calm light surfaces, soft borders | Trust blue or teal |
| حقوقی / مالی / B2B | Restrained light or charcoal, generous whitespace | One strong accent |
| آموزش / آموزشگاه | Clear hierarchy, readable cards | Warm accent, strong type scale |
| ساختمان / صنعتی | Photo-led, high contrast | Industrial amber or steel |

Commit to one. Do not blend neon cyberpunk with cream linen.

## Gallery / portfolio

- One aspect ratio for every tile (4:5 or 3:2), whole tile clickable
- Title + category under the image, never floating over it unreadably
- Missing image → designed placeholder (gradient or pattern + sprite icon),
  never a collapsed `<img>`
- Detail page: cover, short story (مسئله → راه‌حل → نتیجه), gallery,
  CTA «مشاوره برای پروژه مشابه»
- Filters that return nothing get a written empty state and a way back

## Blog / آموزش

- List: excerpt, category, Jalali date in a `<time>` with a machine-readable
  `datetime` (see `persian-locale`)
- Article: breadcrumb, title, lede, prose at `max-inline-size: ~40rem`,
  `line-height` from the RTL tokens
- Persian prose needs `text-align: start`, never `justify` — justification in
  Persian creates rivers because letters join
- End with a soft CTA when it fits the topic

## Contact page

Two columns on desktop (intro + form), one on mobile. Always visible:

- تلفن ثابت و موبایل as `tel:` links
- WhatsApp deep link `https://wa.me/98…`
- اینستاگرام — usually the most-used channel in Iran
- آدرس + شهر, and ساعات کاری («شنبه تا چهارشنبه، ۹ تا ۱۷»)
- Map: Neshan embed or a static image with a link out

Form rules and the phone validator: `persian-ui/rtl-engineering.md` §5.

## Sticky contact on mobile

Common and expected on Iranian service sites. Keep it out of the way of the
footer and the iPhone home indicator:

```css
.contact-bar {
  position: fixed;
  inset-inline: 0;
  inset-block-end: 0;
  display: flex;
  gap: var(--space-2);
  padding: var(--space-3);
  padding-block-end: calc(var(--space-3) + env(safe-area-inset-bottom));
  background: var(--color-surface);
  border-block-start: 1px solid var(--color-border);
}

@media (min-width: 48rem) {
  .contact-bar { display: none; }
}
```

Add matching `padding-block-end` to `main` so the bar never covers content.

## Trust without fake numbers

Use what is real: city, years active if known, service list, named sample
projects, a photo of the actual place. Commercial sites put نماد اعتماد
الکترونیکی and ساماندهی in the footer — link them once the client supplies the
codes, and leave a labelled placeholder until then. Never invent a certificate.

## Copy tone

- Professional, short sentences, no marketing inflation
- Buttons are verbs: «درخواست مشاوره»، «مشاهده نمونه کار»، «تماس تلفنی»
- Empty state says what happened and what to do: «هنوز نمونه‌ای ثبت نشده است»
- Error copy instructs, never blames: «شماره تماس را وارد کنید»

## Self-review

1. Would this sit credibly next to a real Iranian business site in the niche?
2. Can a visitor call or WhatsApp in one tap from any page?
3. Is anything still English because it came from the starter?
4. Does the hero survive with images blocked?
5. On a 375px screen, is the primary CTA reachable without pinch-zoom?
