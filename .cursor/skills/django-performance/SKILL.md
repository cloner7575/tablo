---
name: django-performance
description: Find and fix Django performance problems — N+1 queries, missing indexes, assertNumQueries, pagination, bulk operations, and slow templates. Use when a page or endpoint is slow, when reviewing querysets, or when adding a list view.
---

# Performance

Measure, then fix. A guess about which query is slow is usually wrong.

## Counting queries in a test

This is the cheapest permanent guard, and it belongs on every list view and
list endpoint:

```python
def test_list_does_not_n_plus_one(client, django_assert_num_queries, posts):
    with django_assert_num_queries(3):
        client.get(reverse("blog:list"))
```

If the count changes, the test fails and the reviewer sees why. Write it with
enough rows (≥ 3) that an N+1 actually shows up — with one row it never does.

## The usual causes

| Symptom | Fix |
|---|---|
| A query per row in a loop or template | `select_related` (FK/O2O), `prefetch_related` (M2M/reverse) |
| Slow `WHERE` or `ORDER BY` | index the column; `Meta.indexes` for composites |
| `len(qs)` / `if qs:` | `.count()` / `.exists()` |
| Counting in Python | `annotate(Count(...))` |
| Loop of `save()` | `bulk_create` / `bulk_update` / `update()` |
| Wide model, few fields used | `.only()` / `.defer()` |
| Repeated identical query per request | `cached_property` or the cache framework |
| Unbounded list page | paginate (the API already does) |

```python
Post.objects.select_related("author").prefetch_related(
    Prefetch("comments", queryset=Comment.objects.select_related("author"))
)
```

## Inspecting

```bash
DJANGO_LOG_SQL=true .venv/bin/python manage.py runserver   # logs every query
```

`.explain()` on a suspect queryset shows the plan. `connection.queries` works
inside a shell with `DEBUG=True`. django-debug-toolbar and
django-extensions are optional installs — add them per product, not to the base.

## Indexes

Index what you filter and sort on, in that order for composites. Every index
costs write time and disk, so index the queries you actually run — not every
column. Use `db_index=True` for one field, `Meta.indexes` with `Index(fields=[...])`
for composites, and a partial/conditional index when only a subset is queried.

## Caching interplay

Cache after the query is already sane. Caching an N+1 hides it until the cache
misses under load. See `django-caching` for keys, timeouts, and invalidation.

## Templates and serializers

- A `{% for %}` that walks a relation needs the prefetch in the view
- `SerializerMethodField` that queries per object is an N+1 with extra steps
- Paginate before serialising, never after

## Integration

`django-models`, `django-caching`, `django-rest-framework`,
`pytest-django-patterns`, `systematic-debugging`
