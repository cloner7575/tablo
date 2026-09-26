---
name: django-rest-framework
description: Django REST Framework patterns for serializers, ViewSets, permissions, versioning, throttling, pagination, and queryset optimization. Use when building APIs, serializers, viewsets, or DRF permissions. Triggers on DRF, REST API, serializer, ViewSet, APIView, api/v1.
---

# Django REST Framework

DRF is **already wired** in this starter. Do not re-install it or invent a
second API layout.

```
core/api_urls.py          version namespaces (api:v1)
apps/common/api.py        DefaultPagination, api_exception_handler, health
apps/<app>/serializers.py input/output contracts
apps/<app>/api.py         views and viewsets
apps/<app>/api_urls.py    routes, no app_name (the version owns the namespace)
```

Defaults already set in `core/settings/base.py`: session auth,
`IsAuthenticated`, JSON-only renderers, page size 20, anon/user throttles,
`NamespaceVersioning` with `ALLOWED_VERSIONS = ["v1"]`, and one error envelope.
Development adds the browsable renderer; tests disable throttling.

## Adding an endpoint

1. Serializer in `apps/<app>/serializers.py`
2. View in `apps/<app>/api.py`
3. Route in `apps/<app>/api_urls.py` (no `app_name`)
4. Include it in `v1_patterns` in `core/api_urls.py`
5. Reverse it as `api:v1:<name>` in tests and templates

## Serializers

- One serializer per use case when create, list, and nested write differ
- Validate in `validate_<field>` / `validate`, never in the view
- `read_only_fields` for anything the client must not set (`id`, owner, stamps)
- `SerializerMethodField` sparingly — it is the usual source of N+1
- Never feed `request.data` into a model constructor

```python
class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ("id", "title", "author", "created_at")
        read_only_fields = ("id", "author", "created_at")
```

## Views and ViewSets

- `ModelViewSet` when CRUD maps cleanly; `APIView`/`GenericAPIView` when not
- **Always** override `get_queryset()` with `select_related`/`prefetch_related`
- Scope the queryset to `self.request.user`; never trust a client-supplied id
- `perform_create` stamps ownership
- Business rules belong on the model or a service, not in the view

```python
class PostViewSet(viewsets.ModelViewSet):
    serializer_class = PostSerializer

    def get_queryset(self) -> QuerySet[Post]:
        return (
            Post.objects.filter(author=self.request.user)
            .select_related("author")
            .order_by("-created_at")
        )

    def perform_create(self, serializer: PostSerializer) -> None:
        serializer.save(author=self.request.user)
```

## Errors

`apps.common.api.api_exception_handler` returns every handled error as:

```json
{"detail": "Invalid input.", "code": "invalid", "errors": {"email": ["..."]}}
```

Unhandled exceptions deliberately return `None` from the handler so DRF
re-raises: a 500 belongs in the logs, not in a prettified body. Keep that
behaviour — do not wrap views in bare `except Exception`.

## Versioning and pagination

- `/api/v1/...` is a URL namespace; `request.version` comes from it
- A breaking change means `v2_patterns` in `core/api_urls.py`, not a mutated v1
- List endpoints are paginated by the default class; `?page_size=` caps at 100

## Permissions and auth

- Authenticated by default; `permission_classes = [AllowAny]` only for genuinely
  public reads (the health probe is the one example in the base)
- Object-level rules implement `has_object_permission`
- Token/JWT choices live in the `django-auth` skill

## Testing

```python
def test_endpoint_scopes_to_the_owner(auth_client, other_users_post):
    response = auth_client.get(reverse("api:v1:posts-list"))
    assert response.status_code == 200
    assert response.json()["count"] == 0
```

Cover: anonymous access, ownership scoping, validation error shape, and the
query count for list endpoints.

## Anti-patterns

- `queryset = Model.objects.all()` on a ViewSet that filters later in `list()`
- Serializers that walk relations without prefetching
- Hand-rolled `JsonResponse` error shapes next to the shared envelope
- `AllowAny` on write endpoints
- Adding `rest_framework` settings in an app instead of `core/settings/`

## Integration

`django-models`, `django-auth`, `django-caching`, `django-performance`,
`pytest-django-patterns`
