---
name: django-templates
description: Django template patterns including inheritance, partials, components, error pages, context processors, tags, and filters. Use when working with templates, creating reusable components, or organizing template structure.
---

# Django Template Patterns

## What the starter already provides

```
templates/
├── base.html                  shell: lang/dir, skip link, htmx, blocks
├── 403.html 403_csrf.html 404.html 500.html
├── partials/_header.html _footer.html _messages.html
├── partials/_form_errors.html   non-field errors, role="alert"
├── partials/_health.html        HTMX fragment reference
├── components/_button.html _field.html _icon.html
├── registration/                login, password change, password reset
└── pages/home.html
```

Blocks in `base.html`: `title`, `meta_description`, `body_class`, `content`,
`extra_css`, `extra_js`. Use `{{ block.super }}` when appending.

`500.html` is deliberately standalone: Django renders it with **no context
processors and no request**, so it must not depend on `SITE_NAME`, `user`, or
anything from the database. Keep it that way.

## Conventions

- Full pages extend `base.html` (or a section template that does)
- HTMX fragments are `_name.html` and extend nothing
- Shared chrome in `partials/`, reusable UI in `components/`
- App templates in `templates/<app>/` — `list.html`, `detail.html`, `_form.html`
- `{% url %}` always; never a hardcoded path
- `{% empty %}` on every loop that can be empty
- `{% include ... with x=y only %}` when the partial should not inherit context

## Forms

Render fields through `components/_field.html`. Django sets `aria-invalid` and
`aria-describedby` on the widget pointing at `<auto_id>_helptext` and
`<auto_id>_error`; the component uses exactly those ids, so do not rename them.
Pair it with `partials/_form_errors.html` for `non_field_errors`.

## Components

`_button.html` takes `text`, optional `href`, `variant`, `size`, `icon`, and
`full` (full width). The full-width flag is **not** called `block`: Django
binds `block` to the enclosing BlockNode, so `{% if block %}` is always true
inside a page.

`_icon.html` pulls a `<symbol>` from `static/img/icons.svg`; pass `label` only
when the icon carries meaning that no nearby text repeats.

## Context processors

`apps.common.context_processors.site` provides `SITE_NAME` and
`TEXT_DIRECTION`. Add to it only for values every page needs — a context
processor runs on every render, so it must never query the database per
request without caching.

## Custom tags and filters

Put them in `apps/<app>/templatetags/<name>.py` with an `__init__.py`:

- `simple_tag` returns a string
- `inclusion_tag` renders a fragment
- filters transform one value (see `apps/common/templatetags/persian.py`)

## Translatable copy

`USE_I18N` is on and `LocaleMiddleware` is installed. Wrap user-visible strings
in `{% translate %}` / `{% blocktranslate %}` so a product can localise without
re-writing templates. See the `django-i18n` skill.

## Anti-patterns

- Business conditionals in templates — expose a model method or property
- Inline styles instead of classes and tokens
- A partial that extends `base.html`
- Copy-pasted markup that should be a component
- Query logic in the template (`{% for x in obj.related.all %}` without prefetch)

## Integration

`ui-ux`, `htmx-patterns`, `django-forms`, `django-i18n`, `pytest-django-patterns`
