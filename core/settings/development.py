"""Local development. Default for manage.py and runserver."""

from core.settings.base import *  # noqa: F403
from core.settings.env import build_mailer, get_bool, get_list

DEBUG = True

ALLOWED_HOSTS = get_list(
    "DJANGO_ALLOWED_HOSTS",
    default=["localhost", "127.0.0.1", "[::1]"],
)

INTERNAL_IPS = ["127.0.0.1"]

# Emails land in the console unless DJANGO_EMAIL_BACKEND points elsewhere.
MAILERS = {
    "default": build_mailer("django.core.mail.backends.console.EmailBackend"),
}

# Browsable API is a development convenience, never a production surface.
REST_FRAMEWORK = {
    **REST_FRAMEWORK,  # noqa: F405
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
}

if get_bool("DJANGO_LOG_SQL"):
    LOGGING["loggers"]["django.db.backends"] = {  # noqa: F405
        "handlers": ["console"],
        "level": "DEBUG",
        "propagate": False,
    }
