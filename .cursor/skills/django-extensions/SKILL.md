---
name: django-extensions
description: Django-extensions management commands for project introspection, debugging, and development. Use when exploring URLs, models, settings, database schema, running scripts, or profiling. Triggers on questions about Django project structure, model fields, URL routes, or requests to run development servers.
---

# Django Extensions

This package is **not installed** in the current project. If the task needs introspection commands, install it first:

```bash
.venv/bin/pip install django-extensions
```

Then add `"django_extensions"` to `INSTALLED_APPS` in `core/settings/base.py`. Until then, fall back to `showmigrations`, `shell`, and reading `core/urls.py` / `core/settings/`.

## Introspection

```bash
.venv/bin/python manage.py show_urls
.venv/bin/python manage.py list_model_info
.venv/bin/python manage.py list_model_info --model <app.Model> --signature --field-class
.venv/bin/python manage.py print_settings --format=pprint
.venv/bin/python manage.py print_settings AUTH*
.venv/bin/python manage.py show_permissions
.venv/bin/python manage.py show_template_tags
```

## Development

```bash
.venv/bin/python manage.py shell_plus
.venv/bin/python manage.py shell_plus --print-sql
.venv/bin/python manage.py runserver_plus
```

`shell_plus` auto-imports models. `runserver_plus` includes the Werkzeug debugger.

## Database, Scripts, Profiling

```bash
.venv/bin/python manage.py sqldiff -a -t
.venv/bin/python manage.py runscript <script_name>
.venv/bin/python manage.py runprofileserver --prof-path=/tmp/profiles
```

Scripts live in `scripts/` and must define `run()`.

## Notes

- Model notation: `app.ModelName`
- Settings wildcards: `AUTH*`, `*_DIRS`, `DATABASE*`
- Run commands from the project root
