---
name: django-views-urls
description: Function-based view and URLconf patterns for this starter — typing, request handling, redirects, messages, pagination, permissions, and status codes. Use when writing views.py or urls.py, routing a new screen, or deciding between FBV and CBV.
---

# Views and URLs

## Default shape

Function-based views, fully typed, thin. They orchestrate; models, QuerySets,
forms, and services do the work.

```python
def post_detail(request: HttpRequest, slug: str) -> HttpResponse:
    post = get_object_or_404(
        Post.objects.select_related("author").published(),
        slug=slug,
    )
    return render(request, "blog/detail.html", {"post": post})
```

Rules:

- Type every view: `HttpRequest` in, `HttpResponse` (or a subclass) out
- Early return. Handle `request.method != "POST"` first and get out
- `get_object_or_404` instead of `try/except Model.DoesNotExist`
- Never `Model.objects.get(pk=request.GET["id"])` without an ownership filter
- `select_related` / `prefetch_related` on anything the template walks
- Redirect after a successful POST (POST/redirect/GET), never re-render success
- `django.contrib.messages` for cross-request feedback, not a session key
- Return the right status: 400 invalid, 403 forbidden, 404 missing, 409 conflict

## When a class-based view is right

Subclass Django's built-ins when the upstream class carries security-sensitive
logic you should not reimplement — `LoginView`, `PasswordResetConfirmView`,
`PasswordChangeView` (see `apps/accounts/views.py`). Write generic CBV CRUD only
when the app already uses it. Do not convert an FBV to a CBV to "look modern".

## Permissions

```python
@login_required
def dashboard(request: HttpRequest) -> HttpResponse: ...


@permission_required("orders.change_order", raise_exception=True)
def refund(request: HttpRequest, pk: int) -> HttpResponse: ...
```

`raise_exception=True` renders `403.html` instead of bouncing a logged-in user
to the login page. Object ownership is a queryset filter, not an `if` after the
fetch.

## Pagination

```python
page = Paginator(queryset, 20).get_page(request.GET.get("page"))
```

`get_page` clamps bad input instead of raising. Pass `page` to the template and
render previous/next with `{% url %}` plus the querystring.

## URLconf

- One `urls.py` per app with `app_name`, namespaced reverse (`blog:detail`)
- API routes live in `api_urls.py` and carry **no** `app_name` (see
  `django-rest-framework`)
- Path converters over regex: `<int:pk>`, `<slug:slug>`, `<uuid:token>`
- Trailing slashes, matching the rest of the project
- Include from `core/urls.py`; keep project wiring out of apps

```python
app_name = "blog"

urlpatterns = [
    path("", views.post_list, name="list"),
    path("<slug:slug>/", views.post_detail, name="detail"),
]
```

## Anti-patterns

- Untyped views
- Domain rules or price maths inside the view
- Catching `Exception` to hide a bug
- `HttpResponse("ok")` instead of a template or a real status code
- Hardcoded `/blog/` paths in redirects
- A view that returns 200 with an error message embedded in the HTML

## Integration

`django-models`, `django-forms`, `django-services`, `htmx-patterns`,
`pytest-django-patterns`
