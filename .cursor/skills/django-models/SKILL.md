---
name: django-models
description: Django model design patterns emphasizing fat models/thin views, QuerySet optimization, and domain logic encapsulation. Use when designing models, optimizing queries, implementing business logic, or working with the ORM.
---

# Django Model Patterns

New models in this starter subclass `apps.common.models.TimeStampedModel` unless timestamps do not apply.

## Core Philosophy: Fat Models, Thin Views

Business logic belongs in models and managers, not views. Views orchestrate; models implement domain behavior.

**Good**: Model methods handle business rules, state transitions, validation.
**Bad**: Views contain if/else domain rules or calculate derived values.

## Model Design

- Use `TextChoices`/`IntegerChoices` for status fields
- Add `get_absolute_url()` for canonical object URLs
- Include `__str__()` for readable representations
- Set `ordering` in `Meta` when a default sort is meaningful
- Add indexes for frequently filtered/sorted fields
- Use abstract base models for shared fields (timestamps, soft deletes)

### Field Selection

- Optional text: `blank=True, default=""` (avoid `null` on strings)
- Optional FK: `null=True, blank=True`
- Unique optional fields: `null=True` to avoid unique-constraint collisions on empty string
- Use `JSONField` for flexible metadata instead of many optional columns
- Set `max_length` from real data needs

### Encapsulate Business Logic

- State transitions: `post.publish()`, `order.cancel()`
- Permission checks: `post.is_editable_by(user)`
- Complex calculations: `invoice.calculate_total()`
- Properties for computed read-only values
- Pass `update_fields` when saving partial changes

## QuerySet Patterns

Custom QuerySet classes make queries reusable, chainable, and testable.

```python
class PostQuerySet(models.QuerySet):
    def published(self) -> "PostQuerySet":
        return self.filter(status=Post.Status.PUBLISHED)

    def owned_by(self, user: AbstractBaseUser) -> "PostQuerySet":
        return self.filter(author=user)


class Post(models.Model):
    objects = PostQuerySet.as_manager()
```

- QuerySets: chainable filters (`Post.objects.published().owned_by(user)`)
- Managers: factory-style operations (`User.objects.create_user(...)`)
- Prefer a custom QuerySet over a custom Manager in most cases

## Query Optimization

1. `select_related()` for ForeignKey and OneToOneField (SQL JOIN)
2. `prefetch_related()` for ManyToMany and reverse FKs
3. `only()` / `defer()` for wide models
4. `Prefetch()` to customize prefetches
5. `.exists()` instead of `if queryset:`
6. `.count()` instead of `len(queryset)`
7. `annotate()` / `aggregate()` / `F()` for DB-level work

```python
# BAD — N+1
for post in Post.objects.all():
    print(post.author.name)

# GOOD
for post in Post.objects.select_related("author"):
    print(post.author.name)
```

## Signals

Prefer explicit method calls. See the `django-signals` skill for `on_commit`, M2M, and when a service layer is better.

Use signals only for audit logging, cache invalidation, or cross-app decoupling you do not control.

## Migrations

- `makemigrations` after model changes, then **review** the file
- Prefer reversible migrations
- Data migrations: `makemigrations --empty app_name`, use `apps.get_model()`, never import models directly

## Anti-Patterns

- Iterating and touching relations without `select_related`/`prefetch_related`
- `if queryset:` or `len()` instead of `.exists()` / `.count()`
- Business logic in views
- Overusing signals for synchronous domain work
- Missing indexes on filtered/sorted fields

## Integration

- `pytest-django-patterns`: factory-based model tests
- `celery-patterns`: pass IDs, not instances
- `django-forms`: ModelForm save path
- `django-caching` / `django-signals`: invalidation and `on_commit`
