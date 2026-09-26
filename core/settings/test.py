"""Isolated settings for pytest.

Everything a product can change through `.env` is pinned here so the suite
behaves identically on a laptop and in CI.
"""

import tempfile

from core.settings.base import *  # noqa: F403

DEBUG = False

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

MEDIA_ROOT = tempfile.mkdtemp(prefix="core-test-media-")

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
