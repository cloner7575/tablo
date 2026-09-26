---
name: django-i18n
description: Django translation and localisation in this starter — gettext in templates and Python, makemessages/compilemessages, LANGUAGES, LocaleMiddleware, and RTL. Use when adding translatable copy, a language switcher, a locale, or when LANGUAGE_CODE is not English.
---

# i18n and l10n

## What is already configured

- `USE_I18N = True`, `LocaleMiddleware`, `LOCALE_PATHS = [BASE_DIR / "locale"]`
- `LANGUAGES` defaults to **only** `LANGUAGE_CODE`, on purpose: with a single
  entry, `LocaleMiddleware` cannot flip a Persian product to English because a
  browser sent `Accept-Language: en`
- `DJANGO_LANGUAGES=fa,en` in `.env` opts into a multilingual site
- `/i18n/setlang/` is routed for a language switcher form
- `TEXT_DIRECTION` (`rtl`/`ltr`) is derived from the language and exposed to
  every template through the `site` context processor

## Marking copy

Templates:

```django
{% load i18n %}
{% translate "Sign in" %}
{% blocktranslate %}Welcome back, {{ name }}.{% endblocktranslate %}
{% blocktranslate count counter=items|length %}{{ counter }} item{% plural %}{{ counter }} items{% endblocktranslate %}
```

Python — lazy at import time, eager at call time:

```python
from django.utils.translation import gettext as _, gettext_lazy as _lazy


class Order(models.Model):
    status = models.CharField(verbose_name=_lazy("status"), max_length=20)


def view(request):
    messages.success(request, _("Your order was placed."))
```

Module-level strings (model fields, form labels, choices) use `gettext_lazy`.
Anything evaluated per request uses `gettext`. A non-lazy string at import time
freezes the language of whoever started the process.

## Workflow

```bash
.venv/bin/python manage.py makemessages -l fa        # writes locale/fa/LC_MESSAGES/django.po
# translate the .po
.venv/bin/python manage.py compilemessages           # writes django.mo
```

Commit both `.po` and `.mo` so a deploy does not need gettext installed.
`makemessages` needs the GNU gettext tools on the machine.

## Switching language

```django
<form action="{% url 'set_language' %}" method="post">
  {% csrf_token %}
  <input type="hidden" name="next" value="{{ request.path }}">
  <select name="language" onchange="this.form.submit()">
    {% get_available_languages as languages %}
    {% for code, name in languages %}<option value="{{ code }}">{{ name }}</option>{% endfor %}
  </select>
</form>
```

Only ship this when `DJANGO_LANGUAGES` really has more than one entry.

## Formatting

- Dates and numbers follow the active locale; do not hand-format in templates
- Jalali dates and Toman prices are **not** plain l10n — use the
  `persian-locale` helpers (`{{ dt|jalali }}`, `{{ price|toman }}`)
- Avoid `USE_THOUSAND_SEPARATOR = True` globally: it also groups ids and years

## RTL

Direction comes from `dir="{{ TEXT_DIRECTION }}"` on `<html>`. Write CSS with
logical properties (`margin-inline-start`, `padding-inline`, `inset-inline`) so
one stylesheet serves both directions.

The stylesheet also ships a `[dir="rtl"]` layer: Latin tracking reset, looser
leading, mirrored directional icons, bidi-isolated `code`, LTR tel/email
inputs. Two gotchas translation alone will not fix — wrap Latin values inside a
translated string in `<bdi>`, and never let a `{% translate %}` string carry a
hardcoded direction or digit set.

Full RTL mechanics: `persian-ui/rtl-engineering.md`.

## Pitfalls

- Concatenating translated fragments — translate whole sentences
- `gettext` at module level
- Translating log messages and internal identifiers
- Forgetting `{% load i18n %}` in a template that uses `{% translate %}`
- Adding a language to `LANGUAGES` without a compiled `.mo`

## Integration

`django-templates`, `persian-locale`, `persian-ui`, `ui-ux`
