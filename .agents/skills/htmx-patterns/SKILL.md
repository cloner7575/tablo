---
name: htmx-patterns
description: HTMX patterns for Django including partial templates, hx-* attributes, error swaps, and dynamic UI without a SPA. Use when building interactive UI, handling AJAX requests, progressive enhancement, or creating dynamic components. Triggers on htmx, hx-get, hx-post, partial, fragment.
---

# HTMX Patterns for Django

HTMX is **already wired** in this starter:

- `static/vendor/htmx.min.js` is vendored and loaded from `base.html`
  (no CDN, no build step, works offline and under a strict CSP)
- `<body hx-headers='{"X-CSRFToken": "..."}'>` sends CSRF on every request
- `static/js/app.js` swaps 400/422/503 responses, which HTMX ignores by default
- `apps/common/htmx.py` has `is_htmx()`, `is_boosted()`, `trigger_client_event()`
- The service-status panel on the home page is the working reference

The server renders HTML. If you are about to return JSON and render it with
JavaScript, you want the DRF skill instead.

## Core rules

- HTMX requests get `_partial.html` fragments; everything else gets a full page
- Detect with `apps.common.htmx.is_htmx(request)`, not a raw header string
- A fragment never extends `base.html`
- Always give feedback: `hx-indicator` plus `hx-disabled-elt="this"`
- Return real status codes — 400 for invalid input, 404 for missing, 503 for a
  degraded dependency — and still render a fragment the user can read
- A direct (non-HTMX) hit on a fragment URL must degrade, usually a redirect
- `select_related` / `prefetch_related` still apply inside fragment views

## View pattern

```python
def create_item(request: HttpRequest) -> HttpResponse:
    if request.method != "POST":
        return render(request, "items/create.html", {"form": ItemForm()})

    form = ItemForm(request.POST)
    if not form.is_valid():
        if is_htmx(request):
            return render(request, "items/_form.html", {"form": form}, status=400)
        return render(request, "items/create.html", {"form": form}, status=400)

    item = form.save()
    if is_htmx(request):
        response = render(request, "items/_item.html", {"item": item})
        return trigger_client_event(response, "item-created", {"id": item.pk})
    return redirect("items:detail", pk=item.pk)
```

## Template pattern

```django
<button hx-get="{% url 'items:search' %}"
        hx-target="#results"
        hx-swap="outerHTML"
        hx-indicator="#results-indicator"
        hx-disabled-elt="this">Search</button>
<span id="results-indicator" class="htmx-indicator" role="status">Loading…</span>
```

For POST forms keep `{% csrf_token %}` in the form as well: the body-level
header covers HTMX, the token covers a normal submit when JavaScript fails.

## Response headers

- `HX-Trigger` — fire client events after the swap (`trigger_client_event`)
- `HX-Redirect` — client-side redirect
- `HX-Retarget` / `HX-Reswap` — send errors to a different target
- `HX-Refresh` — full reload after a major state change

## Accessibility

- Swapped regions announce themselves: `role="status"` or `aria-live="polite"`
- Errors get `role="alert"`
- Move focus into the new content when the swap replaces what the user was on
- Indicator transitions respect `prefers-reduced-motion` (already in `base.css`)

## Pitfalls

- Returning `base.html` to an HTMX request (double chrome)
- A 400 or 422 with no swap enabled — the user sees nothing happen
- Missing indicator, so users double-submit
- Fragment URLs that 500 when opened directly
- N+1 queries hidden inside a small fragment
- Reaching for Alpine or a SPA for something one `hx-get` already does

## Testing

```python
def test_fragment_requires_htmx(client):
    assert client.get(url).status_code == 302


def test_fragment_renders_for_htmx(client):
    response = client.get(url, headers={"HX-Request": "true"})
    assert "<html" not in response.content.decode()
```

## Integration

`django-templates`, `django-forms`, `ui-ux`, `pytest-django-patterns`
