---
name: django-admin
description: Django Admin customization for ModelAdmin, list_display, filters, inlines, and queryset optimization. Use when registering models, customizing admin, or fixing slow admin changelists.
---

# Django Admin

Admin is already enabled at `/admin/` via `core/urls.py`. Register models in each app's `admin.py`.

## ModelAdmin Basics

```python
@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("title", "author__email")
    autocomplete_fields = ("author",)
    readonly_fields = ("created_at",)
    date_hierarchy = "created_at"
    list_select_related = ("author",)

    def get_queryset(self, request: HttpRequest) -> QuerySet[Post]:
        qs = super().get_queryset(request)
        return qs.select_related("author")
```

## Performance (Critical)

Changelists N+1 easily. Always:

- `list_select_related` for FKs shown in `list_display`
- `get_queryset()` with `select_related` / `prefetch_related`
- `autocomplete_fields` or `raw_id_fields` instead of giant `<select>` widgets
- Avoid callable columns that hit the DB per row; annotate instead

```python
def get_queryset(self, request: HttpRequest) -> QuerySet[Post]:
    return (
        super()
        .get_queryset(request)
        .select_related("author")
        .annotate(comment_count=Count("comments"))
    )
```

## Inlines

- `TabularInline` / `StackedInline` for tight parent/child edits
- Set `extra = 0`
- `show_change_link = True` when the child has its own admin
- Prefetch on the parent admin queryset if inlines walk relations

## Permissions

- Honor `has_add_permission` / `has_change_permission` / `has_delete_permission`
- For staff-only subsets, filter in `get_queryset` rather than hiding buttons with CSS
- Never register models with secrets (API keys, raw tokens) as editable fields; use `readonly_fields` or exclude them

## Safety

- `actions` must be explicit and confirm bulk deletes
- Do not put irreversible business transitions only in admin without a model method
- `save_model` / `delete_model` should call the same domain methods as the rest of the app

## Anti-Patterns

- `list_display` of FKs without `list_select_related`
- Unbounded `list_per_page` on large tables
- Business logic that exists only in `save_model`
- Importing `admin.site.register` for every proxy without `ModelAdmin`

## Integration

- `django-models`, `django-auth`, `django-caching`
