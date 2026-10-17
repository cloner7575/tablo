---
name: django-caching
description: Django cache framework, Redis, cached_property, invalidation, and N+1 / QuerySet optimization overlap. Use when adding caching, Redis, cache_page, or fixing slow queries and duplicate cache keys.
---

# Django Caching

`CACHES` is already configured in `core/settings/base.py`: locmem by default,
and the Redis backend as soon as `REDIS_URL` is set in the environment. Locmem
is per-process, so it does not share between gunicorn workers — any product
with more than one worker, or with throttling that must be enforced globally,
needs Redis.

```bash
.venv/bin/pip install redis    # only then set REDIS_URL
```

## When to Cache

Cache expensive **read** paths with a clear invalidation key. Do not cache as a substitute for missing `select_related` / `prefetch_related`.

Fix the query first (`django-models`), then cache if it is still hot.

## Tuning the configured backend

Add `KEY_PREFIX` and `TIMEOUT` to the Redis branch in `core/settings/base.py`
when a product shares one Redis between environments:

```python
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
        "KEY_PREFIX": "core",
        "TIMEOUT": 300,
    }
}
```

The URL comes from the environment. Never hardcode a Redis password in
settings, and remember `core/settings/test.py` pins locmem so the suite never
talks to a live server.

## Patterns

**Low-level cache** for computed payloads:

```python
def trending_post_ids() -> list[int]:
    key = "posts:trending:ids"
    cached = cache.get(key)
    if cached is not None:
        return cached
    ids = list(Post.objects.trending().values_list("pk", flat=True)[:20])
    cache.set(key, ids, timeout=60)
    return ids
```

**`cached_property`** for per-instance computed values in a single request, not across requests.

**Per-view** `cache_page` only for anonymous, cookie-free responses. Authenticated HTML/API almost never belongs in `cache_page`.

**Template fragment** `{% cache %}` needs a key that includes every varying bit (user, language, query).

## Invalidation

Invalidate on write, preferably in `transaction.on_commit` (see `django-signals`):

```python
def invalidate_post_cache(post_id: int) -> None:
    cache.delete_many([f"posts:{post_id}", "posts:trending:ids"])
```

- Prefer delete-by-key over `cache.clear()`
- Include object id and a schema version in keys (`posts:v2:{id}`)
- Do not store ORM instances in cache; store IDs or primitive DTOs

## Query Overlap (N+1)

Caching a view that still does N+1 just caches slowness until TTL. In the view or `get_queryset`:

```python
posts = Post.objects.select_related("author").prefetch_related("tags")
```

Use `django.test.utils.CaptureQueriesContext` to assert query counts before adding Redis.

## Anti-Patterns

- Caching `request.user`-specific pages without the user id in the key (data leak)
- Infinite TTL
- `cache.set` of a QuerySet (it is lazy; evaluate first)
- Redis as a second database for writes that must be durable

## Integration

- `django-models`, `django-signals`, `django-rest-framework`, `docker-django`
