"""Isolated settings for pytest.

Everything a product can change through `.env` is pinned here so the suite
behaves identically on a laptop and in CI.
"""

import tempfile

from core.settings.base import *  # noqa: F403

DEBUG = False

ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]

SITE_NAME = "Core"
LANGUAGE_CODE = "en-us"
LANGUAGES = [("en-us", "English")]
TEXT_DIRECTION = "ltr"
TIME_ZONE = "UTC"

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

MAILERS = {
    "default": {"BACKEND": "django.core.mail.backends.locmem.EmailBackend"},
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "core-test",
    },
}

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    },
}

MEDIA_ROOT = tempfile.mkdtemp(prefix="core-test-media-")
STATIC_ROOT = tempfile.mkdtemp(prefix="core-test-static-")
IMAGE_UPLOAD_MAX_BYTES = 5 * 1024 * 1024
VIDEO_UPLOAD_MAX_BYTES = 50 * 1024 * 1024
PORTFOLIO_MAX_MEDIA = 20

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
WHITENOISE_AUTOREFRESH = True
WHITENOISE_USE_FINDERS = True

# Rate limits are asserted explicitly in the tests that care about them.
REST_FRAMEWORK = {
    **REST_FRAMEWORK,  # noqa: F405
    "DEFAULT_THROTTLE_CLASSES": [],
}
