---
name: django-migrations
description: Safe Django migrations — reviewing generated files, data migrations, backwards-compatible schema changes, zero-downtime deploys, and makemigrations --check. Use when changing models, adding fields, renaming, deleting columns, or fixing migration conflicts.
---

# Migrations

## Every model change

```bash
.venv/bin/python manage.py makemigrations
# read the generated file before doing anything else
.venv/bin/python manage.py migrate
.venv/bin/python manage.py makemigrations --check --dry-run   # must be clean
```

CI runs `makemigrations --check --dry-run`. A model edit without a migration
fails the build, which is the point: missing migrations are the single most
common broken deploy in a Django project.

## Reading a generated migration

Check for:

- An unintended table rewrite (`AlterField` on a large table)
- A new non-nullable column without a default → prompts, then locks on deploy
- A `RenameField` Django guessed from a delete + add (or the reverse)
- Dropped columns you meant to keep
- `AUTH_USER_MODEL` dependencies (`migrations.swappable_dependency`)

## Adding a field safely

1. Add it `null=True` (or with a default) and migrate
2. Backfill in a data migration
3. Tighten to `null=False` in a third migration once the backfill is done

On a small product with a maintenance window, one step is fine — say so in the
PR instead of pretending it is zero-downtime.

## Data migrations

```bash
.venv/bin/python manage.py makemigrations app --empty --name backfill_slugs
```

```python
def backfill_slugs(apps, schema_editor):
    Post = apps.get_model("blog", "Post")  # never import the real model
    for post in Post.objects.filter(slug="").iterator():
        post.slug = slugify(post.title)
        post.save(update_fields=["slug"])


class Migration(migrations.Migration):
    dependencies = [("blog", "0003_post_slug")]
    operations = [
        migrations.RunPython(backfill_slugs, migrations.RunPython.noop),
    ]
```

- `apps.get_model()` only: the historical model is the point
- Always provide a reverse (`noop` is a valid, explicit choice)
- `.iterator()` and `update_fields` on large tables
- No `import` of business logic — the code will change, the migration will not

## Deleting

Removing a field is two deploys: stop reading/writing it in code, then drop the
column. Dropping it in the same deploy breaks the old process still serving
traffic during a rolling restart.

## Conflicts

Two migrations with the same parent → `makemigrations --merge`, then read the
merge file. Never renumber or hand-edit an applied migration; on a shared
branch, rebase and regenerate instead.

## Squashing

Squash only when the number of migrations actually slows the test setup, and
keep the originals until every environment has passed the squash point.

## Rules

- Migrations are committed with the model change, in the same commit
- Never edit a migration that has run in production
- `RunSQL` needs a reverse and a comment explaining why the ORM was not enough
- Review `sqlmigrate` output for anything touching a big table

## Integration

`django-models`, `pytest-django-patterns`, `github-workflow`
