---
name: docker-django
description: Docker and Compose patterns for Django including multi-stage Dockerfiles, gunicorn/uvicorn, env files, and Postgres. Use when writing Dockerfiles, docker-compose, or preparing deployment. Do not dockerize the app unless the user asked.
---

# Docker for Django

This project is not containerized. These patterns apply when the user asks for Docker. Do not add Docker files unsolicited.

## Multi-Stage Dockerfile

- Build deps in a builder stage; copy site-packages / wheels into a slim runtime
- Run as a non-root user
- `PYTHONUNBUFFERED=1`, `PYTHONDONTWRITEBYTECODE=1`
- Collectstatic in the image or an entrypoint, not at import time in `settings.py`

```dockerfile
FROM python:3.12-slim AS runtime
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
RUN useradd --create-home appuser
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
USER appuser
CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000"]

Set `DJANGO_SETTINGS_MODULE=core.settings.production` in the container.
```

ASGI: `uvicorn core.asgi:application --host 0.0.0.0 --port 8000`.

## Compose Sketch

Typical services: `web`, `db` (Postgres), optional `redis`, optional `worker`.

- `web` depends on `db` healthy
- Mount source only in development
- Pass secrets through env_file / Compose secrets, never `ENV SECRET_KEY=...` in the Dockerfile
- Persist Postgres on a named volume

`DEBUG=0` in production images. `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` from env.

## Gunicorn

- `gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 3`
- Workers ≈ 2–4 × CPU for sync workers; use gevent/uvicorn workers only if the app is written for it
- Do not use `runserver` in production

## Entrypoint

- Wait for Postgres
- `manage.py migrate --noinput` only when the deployment strategy wants migrations at boot (one-shot job is safer)
- Then exec gunicorn

## Anti-Patterns

- Baking `.venv` or `db.sqlite3` into the image
- Copying `.env` with real secrets into the image
- Running as root
- `CMD python manage.py runserver 0.0.0.0:8000` for production
- Host networking to skip Compose service names

## Integration

- `django-caching` (Redis service), `celery-patterns` (worker service), `django-auth` (secure cookies behind TLS)
