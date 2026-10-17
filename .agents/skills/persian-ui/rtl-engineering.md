# RTL engineering (fa) — the mechanical half of Persian UI

Everything here is verified against this starter's design system. Read it once
before the first Persian screen; come back for the bug table.

`persian-ui/SKILL.md` owns taste and composition. This file owns direction,
type, numerals and bidi — the things that silently look wrong.

---

## 1. What already flips, and what never will

Turning the product Persian is two env values:

```bash
DJANGO_LANGUAGE_CODE=fa
DJANGO_TEXT_DIRECTION=rtl   # inferred from the language anyway; set it to be explicit
DJANGO_TIME_ZONE=Asia/Tehran
```

`base.html` reads them through the context processor, so `<html lang="fa" dir="rtl">`
is correct from the first request. From there:

| Concern | Handled by | Where |
|---------|-----------|-------|
| Layout mirroring | Logical properties (`margin-inline`, `inset-inline-start`, `text-align: start`) | `base.css` throughout |
| Latin tracking / leading | `[dir="rtl"]` token overrides (tracking → 0, leading → 1.8) | `tokens.css` |
| Directional icons | `[dir="rtl"] .icon:has(use[href$="#arrow-right"])` + `.icon--flip` | `base.css` |
| Uppercase / mono Latin labels | `[dir="rtl"] .eyebrow, .badge, .hero__meta, .steps li::before, .site-footer h2` | `base.css` |
| Latin fragments in Persian prose | `unicode-bidi: isolate` on `code`, `kbd`, `samp`, `.ltr` | `base.css` |
| Phone / email / URL / password inputs | `direction: ltr` on those input types | `base.css` |

**Never automatic — you must handle these per screen:**

- Persian copy (the starter ships English strings)
- The font (the starter ships latin-only IBM Plex Sans)
- نیم‌فاصله (ZWNJ) in words like می‌شود، کتاب‌ها
- Persian numerals, Jalali dates, تومان
- `<bdi>` around user-generated or mixed-direction values
- Any new `transform: translateX()` you write

Verify the layer on a running page (DevTools console):

```js
getComputedStyle(document.querySelector("h1")).letterSpacing;   // "normal", not "-0.035em"
getComputedStyle(document.body).lineHeight;                      // ~1.8em
getComputedStyle(document.querySelector(".btn .icon")).transform; // matrix(-1, 0, 0, 1, 0, 0)
document.documentElement.scrollWidth > innerWidth;                // false — no RTL overflow
```

---

## 2. Font: self-host Vazirmatn

The starter's `@font-face` blocks are latin-only. A Persian product **replaces**
them; it does not stack a Persian face after a Latin one.

```bash
# Variable font, two subsets: arabic (~46 KB) and latin (~34 KB) for digits,
# brand words and code. URLs come from the Google Fonts css2 API.
curl -sL "https://fonts.googleapis.com/css2?family=Vazirmatn:wght@100..900&display=swap" \
  -H "User-Agent: Mozilla/5.0 Chrome/120" | grep -A4 "arabic\|latin"
curl -o static/fonts/vazirmatn-arabic.woff2 "<arabic url>"
curl -o static/fonts/vazirmatn-latin.woff2  "<latin url>"
rm static/fonts/ibm-plex-sans-latin.woff2   # no longer referenced
```

In `tokens.css`, replacing the two starter blocks:

```css
@font-face {
  font-family: "Vazirmatn";
  src: url("../fonts/vazirmatn-arabic.woff2") format("woff2");
  font-weight: 100 900;
  font-display: swap;
  unicode-range: U+0600-06FF, U+200C-200E, U+2010-2011, U+204F, U+2E41, U+FB8A,
    U+FBFC-FBFD;
}

@font-face {
  font-family: "Vazirmatn";
  src: url("../fonts/vazirmatn-latin.woff2") format("woff2");
  font-weight: 100 900;
  font-display: swap;
  unicode-range: U+0000-00FF, U+2000-206F, U+20AC, U+2122;
}

:root {
  --font-sans: "Vazirmatn", "Segoe UI", system-ui, sans-serif;
  --font-mono: "Vazirmatn", ui-monospace, monospace; /* only if you show no code */
}
```

Update the preload in `templates/base.html` to the arabic file, and keep
`font-display: swap` so Persian text is never invisible on a slow connection.

Estedad is the usual display companion (headings only). Two families maximum.

---

## 3. Numerals

Pick one policy per product and hold it:

| Content | Digits | Why |
|---------|--------|-----|
| Prose, counts, dates, prices | Persian ۰-۹ | Reads native |
| Phone numbers | Latin, `dir="ltr"` | Users copy and dial them |
| Codes, SKUs, tracking, IDs, URLs | Latin | Machine-facing, must round-trip |
| Form inputs | Latin | The value is posted back; convert on display only |

```django
{% load persian %}
{{ product.price|toman|fa_digits }}          {# ۱۸۵٬۰۰۰ تومان #}
{{ order.created_at|jalali|fa_digits }}      {# ۱۴۰۴/۰۱/۰۱ #}
<bdi dir="ltr">{{ profile.phone }}</bdi>     {# 0912 345 6789 — never reversed #}
```

`fa_digits` is display-only: never feed its output to `int()`, a URL, or a form
initial. Accept both digit sets on input instead — Persian keyboards produce ۱۲۳:

```python
PERSIAN_TO_ASCII = str.maketrans("۰۱۲۳۴۵۶۷۸۹٬،", "0123456789,,")


def clean_phone(self) -> str:
    return self.cleaned_data["phone"].translate(PERSIAN_TO_ASCII).strip()
```

Numbers in tables and price columns line up with `font-variant-numeric: tabular-nums`.

Numbered lists (`.steps`) can use Persian counters:

```css
[dir="rtl"] .steps li::before { content: counter(step, persian); }
```

---

## 4. Bidi: where Persian pages actually break

A Latin run inside Persian text drags its neighbouring punctuation with it. The
fix is isolation, not `dir` sprinkling.

```django
{# Wrong: the trailing period jumps to the wrong side #}
<p>سرویس روی {{ domain }} اجرا می‌شود.</p>

{# Right #}
<p>سرویس روی <bdi>{{ domain }}</bdi> اجرا می‌شود.</p>
```

- `<bdi>` — any value you do not control (usernames, domains, filenames, search terms)
- `.ltr` class — a block you know is Latin (log output, a command, an email column)
- `code` / `kbd` / `samp` — already isolated by `base.css`
- Parentheses and brackets around Latin inside Persian: wrap the whole group,
  not just the Latin word

Persian punctuation: `،` not `,` · `؛` not `;` · `؟` not `?` · «گیومه» not "quotes"
· `٪` after the number (`۲۰٪`).

نیم‌فاصله (ZWNJ, U+200C) is not optional in good Persian copy: می‌شود، نمی‌کند،
کتاب‌ها، برنامه‌ریزی. Type it with `AltGr+Shift+Space`, or paste `‌`. In Python
source use `"\u200c"` so it survives a careless editor.

---

## 5. Forms for Iranian users

```python
from django import forms
from django.core.validators import RegexValidator

IRANIAN_MOBILE = RegexValidator(
    r"^09\d{9}$",
    message="شماره موبایل را به شکل ۰۹۱۲۳۴۵۶۷۸۹ وارد کنید.",
)


class ConsultationForm(forms.Form):
    full_name = forms.CharField(label="نام و نام خانوادگی", max_length=80)
    phone = forms.CharField(
        label="شماره تماس",
        validators=[IRANIAN_MOBILE],
        widget=forms.TextInput(
            attrs={"inputmode": "tel", "autocomplete": "tel", "dir": "ltr"},
        ),
    )
    note = forms.CharField(label="توضیح کوتاه", widget=forms.Textarea, required=False)

    def clean_phone(self) -> str:
        return self.cleaned_data["phone"].translate(PERSIAN_TO_ASCII)
```

- Labels are visible and Persian; a placeholder is never the label
- Submit button names the outcome: «ارسال درخواست مشاوره»، not «ثبت»
- Errors sit next to the field (`components/_field.html` already does this) and
  are written as instructions, not blame: «شماره تماس را وارد کنید»
- Success is a real message, not a silent redirect: what happens next, and when

---

## 6. Bug table (symptom → cause → fix)

| Symptom | Cause | Fix |
|---------|-------|-----|
| Persian headline looks cramped, letters pulled apart | Negative `letter-spacing` from Latin tokens | Already reset under `[dir="rtl"]`; do not re-add tracking to headings |
| Arrow in a CTA points away from the reading direction | `transform` not mirrored | Use a sprite icon (auto-mirrored) or `flip=True` |
| Hover arrow slides the wrong way | `transform: translateX()` | Use `translate: 0.2em 0` and an RTL override |
| Period or parenthesis lands on the wrong side | Missing bidi isolation | `<bdi>` or `.ltr` |
| Phone number displays reversed | RTL paragraph direction | `<bdi dir="ltr">` |
| Label in ALL CAPS looks like noise | `text-transform: uppercase` inherited from a Latin label style | Covered for starter classes; do not add new uppercase rules |
| Numbers render in a different face than the text | Mono/Latin font has no Persian glyphs, browser falls back | Keep one family; set `--font-mono` to Vazirmatn when no code is displayed |
| Layout scrolls horizontally on mobile | A fixed `left/right` or `padding-left` | Replace with logical properties |
| Dates show میلادی | `{{ dt }}` instead of the filter | `{{ dt|jalali }}` — see `persian-locale` |
| Sticky call bar covers the footer on iPhone | No safe-area padding | `padding-block-end: env(safe-area-inset-bottom)` |

---

## 7. Checking RTL locally

```bash
DJANGO_LANGUAGE_CODE=fa DJANGO_TEXT_DIRECTION=rtl \
  .venv/bin/python manage.py runserver
```

In tests, flip direction per test rather than per environment:

```python
def test_shell_flips_direction(client, settings) -> None:
    settings.TEXT_DIRECTION = "rtl"
    assert 'dir="rtl"' in client.get("/").content.decode()
```

Check 375px, 768px and 1024px in RTL specifically — a layout that survives LTR
mobile can still overflow when a hard-coded offset flips.
