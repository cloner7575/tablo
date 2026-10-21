"""Small .env loader so the starter has no extra runtime dependency."""

from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import urlsplit


def load_dotenv(path: Path) -> None:
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if not key:
            continue
        value = value.strip().strip("'").strip('"')
        os.environ.setdefault(key, value)


def get_bool(key: str, default: bool = False) -> bool:
    raw = os.getenv(key)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def get_int(key: str, default: int) -> int:
    raw = os.getenv(key)
    if raw is None or not raw.strip():
        return default
    try:
        return int(raw.strip())
    except ValueError as exc:
        raise ValueError(f"{key} must be an integer, got {raw!r}") from exc


def build_mailer(default_backend: str) -> dict[str, object]:
    """Build one `MAILERS` entry from the environment.

    Django 6.1 deprecated the EMAIL_* settings in favour of MAILERS, and a
    mailer rejects OPTIONS its backend does not accept — so SMTP credentials
    are only attached to the SMTP backend.
    """
    backend = os.getenv("DJANGO_EMAIL_BACKEND", "").strip() or default_backend
    if not backend.endswith("smtp.EmailBackend"):
        return {"BACKEND": backend}

    return {
        "BACKEND": backend,
        "OPTIONS": {
            "host": os.getenv("DJANGO_EMAIL_HOST", "localhost"),
            "port": get_int("DJANGO_EMAIL_PORT", 25),
            "username": os.getenv("DJANGO_EMAIL_HOST_USER", ""),
            "password": os.getenv("DJANGO_EMAIL_HOST_PASSWORD", ""),
            "use_tls": get_bool("DJANGO_EMAIL_USE_TLS", default=False),
        },
    }


def get_list(key: str, default: list[str] | None = None) -> list[str]:
    raw = os.getenv(key)
    if not raw:
        return list(default or [])
    return [item.strip() for item in raw.split(",") if item.strip()]


def get_site_url() -> str:
    """Resolve one canonical origin, including the existing MCP deployment alias."""
    value = (
        os.getenv('DJANGO_SITE_URL', '').strip()
        or os.getenv('MCP_PUBLIC_BASE_URL', '').strip()
    ).rstrip('/')
    if not value:
        return ''
    parsed = urlsplit(value)
    if (
        parsed.scheme not in {'http', 'https'}
        or not parsed.hostname
        or parsed.path
        or parsed.query
        or parsed.fragment
        or parsed.username is not None
        or parsed.password is not None
    ):
        raise ValueError(
            'DJANGO_SITE_URL (or MCP_PUBLIC_BASE_URL) must be an absolute site '
            'origin, such as https://example.com, without an endpoint path.'
        )
    return value
