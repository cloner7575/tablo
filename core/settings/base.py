"""Shared settings. Do not use this module as DJANGO_SETTINGS_MODULE."""

from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import urlparse

from django.conf.locale import LANG_INFO

from core.settings.env import build_mailer, get_bool, get_int, get_list, load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent

load_dotenv(BASE_DIR / ".env")

SITE_NAME = os.getenv("DJANGO_SITE_NAME", "Core")

SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "django-insecure-change-me-in-env",
)

DEBUG = get_bool("DJANGO_DEBUG", default=False)

ALLOWED_HOSTS = get_list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

CSRF_TRUSTED_ORIGINS = get_list("DJANGO_CSRF_TRUSTED_ORIGINS")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "django.contrib.sitemaps",
    "rest_framework",
    "drf_spectacular",
    "apps.accounts.apps.AccountsConfig",
    "apps.common.apps.CommonConfig",
    "apps.locations.apps.LocationsConfig",
    "apps.catalog.apps.CatalogConfig",
    "apps.vendors.apps.VendorsConfig",
    "apps.requests.apps.RequestsConfig",
    "apps.quotes.apps.QuotesConfig",
    "apps.orders.apps.OrdersConfig",
    "apps.portfolio.apps.PortfolioConfig",
    "apps.reviews.apps.ReviewsConfig",
    "apps.notifications.apps.NotificationsConfig",
    "apps.payments.apps.PaymentsConfig",
    "apps.analytics.apps.AnalyticsConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "core.urls"
WSGI_APPLICATION = "core.wsgi.application"
ASGI_APPLICATION = "core.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.template.context_processors.i18n",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.common.context_processors.site",
            ],
        },
    },
]


def _database_config() -> dict[str, object]:
    url = os.getenv("DATABASE_URL", "").strip()
    conn_max_age = get_int("DJANGO_DB_CONN_MAX_AGE", 60)

    if not url or url.startswith("sqlite"):
        name = BASE_DIR / "db.sqlite3"
        if url.startswith("sqlite:///"):
            path = url.removeprefix("sqlite:///")
            name = Path(path) if Path(path).is_absolute() else BASE_DIR / path
        return {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": name,
            "OPTIONS": {
                "transaction_mode": "IMMEDIATE",
                "init_command": "PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL;",
            },
        }

    parsed = urlparse(url)
    engine = {
        "postgres": "django.db.backends.postgresql",
        "postgresql": "django.db.backends.postgresql",
        "postgresql+psycopg": "django.db.backends.postgresql",
    }.get(parsed.scheme)
    if engine is None:
        raise ValueError(f"Unsupported DATABASE_URL scheme: {parsed.scheme!r}")
    return {
        "ENGINE": engine,
        "NAME": parsed.path.lstrip("/"),
        "USER": parsed.username or "",
        "PASSWORD": parsed.password or "",
        "HOST": parsed.hostname or "",
        "PORT": str(parsed.port or ""),
        "CONN_MAX_AGE": conn_max_age,
        "CONN_HEALTH_CHECKS": True,
    }


DATABASES = {"default": _database_config()}

REDIS_URL = os.getenv("REDIS_URL", "").strip()

if REDIS_URL:
    # Requires the `redis` package. See skill: django-caching.
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": REDIS_URL,
        },
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "core-default",
        },
    }

AUTH_USER_MODEL = "accounts.User"
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "common:home"
LOGOUT_REDIRECT_URL = "common:home"

# Phone OTP
OTP_TTL_MINUTES = get_int("OTP_TTL_MINUTES", 5)
OTP_SEND_LIMIT = get_int("OTP_SEND_LIMIT", 5)
OTP_SEND_WINDOW_SECONDS = get_int("OTP_SEND_WINDOW_SECONDS", 3600)
OTP_VERIFY_LIMIT = get_int("OTP_VERIFY_LIMIT", 10)
OTP_VERIFY_WINDOW_SECONDS = get_int("OTP_VERIFY_WINDOW_SECONDS", 3600)
OTP_MAX_ATTEMPTS = get_int("OTP_MAX_ATTEMPTS", 5)
SMS_PROVIDER = os.getenv(
    "SMS_PROVIDER",
    "apps.accounts.sms.ConsoleSmsProvider",
)
ANALYTICS_PROVIDER = os.getenv(
    "ANALYTICS_PROVIDER",
    "apps.analytics.services.ConsoleAnalyticsProvider",
)
NOTIFICATIONS_SWALLOW_ERRORS = get_bool("NOTIFICATIONS_SWALLOW_ERRORS", default=True)

# Uploads
FILE_UPLOAD_MAX_MEMORY_SIZE = get_int("FILE_UPLOAD_MAX_MEMORY_SIZE", 5 * 1024 * 1024)
DATA_UPLOAD_MAX_MEMORY_SIZE = get_int("DATA_UPLOAD_MAX_MEMORY_SIZE", 6 * 1024 * 1024)
IMAGE_UPLOAD_MAX_BYTES = get_int("IMAGE_UPLOAD_MAX_BYTES", 5 * 1024 * 1024)
ALLOWED_IMAGE_CONTENT_TYPES = ("image/jpeg", "image/png", "image/webp")

LANGUAGE_CODE = os.getenv("DJANGO_LANGUAGE_CODE", "en-us")
TIME_ZONE = os.getenv("DJANGO_TIME_ZONE", "UTC")
USE_I18N = True
USE_TZ = True
LOCALE_PATHS = [BASE_DIR / "locale"]


def _language_label(code: str) -> str:
    info = LANG_INFO.get(code) or LANG_INFO.get(code.split("-", maxsplit=1)[0], {})
    return str(info.get("name_local") or code)


# Single-language by default so LocaleMiddleware cannot switch a product's UI
# language from Accept-Language. Set DJANGO_LANGUAGES to opt into a switcher.
_language_codes = get_list("DJANGO_LANGUAGES", default=[LANGUAGE_CODE])
if LANGUAGE_CODE not in _language_codes:
    _language_codes.insert(0, LANGUAGE_CODE)
LANGUAGES = [(code, _language_label(code)) for code in _language_codes]

_RTL_LANGS = frozenset({"ar", "fa", "he", "ur"})
_direction = os.getenv("DJANGO_TEXT_DIRECTION", "").strip().lower()
if _direction in {"rtl", "ltr"}:
    TEXT_DIRECTION = _direction
else:
    TEXT_DIRECTION = (
        "rtl"
        if LANGUAGE_CODE.split("-", maxsplit=1)[0].lower() in _RTL_LANGS
        else "ltr"
    )

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

MAILERS = {
    "default": build_mailer("django.core.mail.backends.console.EmailBackend"),
}
DEFAULT_FROM_EMAIL = os.getenv("DJANGO_DEFAULT_FROM_EMAIL", "noreply@example.com")
SERVER_EMAIL = DEFAULT_FROM_EMAIL

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
    "DEFAULT_PAGINATION_CLASS": "apps.common.api.DefaultPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": [
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": os.getenv("DJANGO_THROTTLE_ANON", "60/min"),
        "user": os.getenv("DJANGO_THROTTLE_USER", "600/min"),
        "otp": os.getenv("DJANGO_THROTTLE_OTP", "10/min"),
    },
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_VERSIONING_CLASS": "rest_framework.versioning.NamespaceVersioning",
    "DEFAULT_VERSION": "v1",
    "ALLOWED_VERSIONS": ["v1"],
    "EXCEPTION_HANDLER": "apps.common.api.api_exception_handler",
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Tablo.com API",
    "DESCRIPTION": "REST API for تابلو دات کام marketplace",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
    },
    "loggers": {
        "django.request": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "django.security": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "apps": {
            "handlers": ["console"],
            "level": os.getenv("DJANGO_APP_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
    },
}
