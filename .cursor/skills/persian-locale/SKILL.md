---
name: persian-locale
description: >-
  Persian (fa) locale conventions for this Django starter — Jalali calendar
  display and input, Persian numerals, Tehran time, week start, and number
  formatting. Use when LANGUAGE_CODE is fa, PRODUCT.md sets RTL/Persian,
  building Iranian products, or the user mentions تقویم جلالی، شمسی، فارسی،
  تاریخ فارسی، یا اعداد فارسی.
---

# Persian locale (fa)

Applies when the product UI language is Persian or `PRODUCT.md` says RTL + `fa`.
Visual/RTL work lives in `persian-ui`; this skill is dates, numbers and time.

## Hard rules

1. **Store Gregorian, display Jalali.** Datetimes stay timezone-aware Gregorian
   in the database (Django default). Convert at the display and input boundary
   only.
2. **No میلادی in front of end users** — order history, «عضویت از», blog dates,
   staff screens that are Persian. Only when the user explicitly asks.
3. `TIME_ZONE = "Asia/Tehran"` and `USE_TZ = True` for Iranian products.
4. Direction comes from settings (`{{ TEXT_DIRECTION }}`), never hardcoded.
5. Persian numerals are a **display** transform. Never store or post them.

## Settings

```bash
DJANGO_LANGUAGE_CODE=fa
DJANGO_TEXT_DIRECTION=rtl
DJANGO_TIME_ZONE=Asia/Tehran
```

The Iranian week starts on Saturday — set `FIRST_DAY_OF_WEEK = 6` when you
render any calendar or date picker.

Leave `USE_THOUSAND_SEPARATOR` off: it groups *every* number Django renders,
including years and IDs. Group deliberately with the filters below.

## Package

```bash
.venv/bin/pip install jdatetime
```

Pinned in `requirements.txt`. Add `django-jalali` only when you need Jalali
**model fields or admin widgets** for user-entered dates.

## Display (this starter)

```django
{% load persian %}
{{ order.created_at|jalali }}                      {# 1404/01/01 #}
{{ order.created_at|jalali:"%A %d %B %Y" }}        {# جمعه 01 فروردین 1404 #}
{{ order.created_at|jalali|fa_digits }}            {# ۱۴۰۴/۰۱/۰۱ #}
{{ product.price|toman|fa_digits }}                {# ۱۸۵٬۰۰۰ تومان #}
```

Python:

```python
from apps.common.persian import format_jalali, to_jalali, to_persian_digits

format_jalali(order.created_at)  # "1404/01/01"
format_jalali(order.created_at, "%d %B %Y")  # "01 فروردین 1404"
format_jalali(order.created_at, persian_digits=True)
```

`to_jalali` binds the `fa_IR` locale, which is what makes `%B` and `%A` render
Persian names instead of "Farvardin" and "Friday".

Give machines the Gregorian value and humans the Jalali one:

```django
<time datetime="{{ post.published_at|date:'c' }}">
  {{ post.published_at|jalali:"%d %B %Y"|fa_digits }}
</time>
```

## Input

Persian keyboards emit ۰-۹ and users type `1404/01/01`. Normalise, then convert:

```python
import jdatetime
from django import forms

PERSIAN_TO_ASCII = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")


class InvoiceForm(forms.Form):
    issued_on = forms.CharField(label="تاریخ صدور")  # 1404/01/01

    def clean_issued_on(self):
        raw = self.cleaned_data["issued_on"].translate(PERSIAN_TO_ASCII).strip()
        try:
            return jdatetime.datetime.strptime(raw, "%Y/%m/%d").togregorian().date()
        except ValueError:
            raise forms.ValidationError("تاریخ را به شکل ۱۴۰۴/۰۱/۰۱ وارد کنید.")
```

Return a Gregorian `date` from `clean_*` so the rest of the stack stays normal.

## Admin

- Read-only timestamps: format with `format_jalali` in a `list_display` callable
  or a small mixin.
- Editable dates in a Persian staff UI: `django-jalali` fields or a Jalali JS
  widget. Never leave a Gregorian HTML5 picker as the only input on an fa-first
  product.

## APIs

ISO-8601 Gregorian in JSON — it is a machine contract. Document it. Convert in
the client or in a serializer field explicitly named for display
(`created_at_jalali`), never by mutating `created_at`.

## Do not

- Store Jalali strings as the source of truth
- Store Persian digits in the database
- Mix میلادی and شمسی on one screen without a stated reason
- Convert with `jdatetime` on a naive datetime — `timezone.localtime` first
  (`to_jalali` already does)

## Related

- RTL, fonts, numerals in UI → **`persian-ui`** (+ `rtl-engineering.md`)
- Money / تومان → `persian-ecommerce`
- Intake defaults → `product-intake`
- Translation workflow → `django-i18n`
