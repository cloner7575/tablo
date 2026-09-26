"""Production. Requires DJANGO_SECRET_KEY and DJANGO_ALLOWED_HOSTS."""

from core.settings.base import *  # noqa: F403
from core.settings.base import SECRET_KEY
from core.settings.env import build_mailer, get_bool, get_int, get_list

DEBUG = False

if not SECRET_KEY or SECRET_KEY.startswith("django-insecure-"):
    raise ValueError("Set DJANGO_SECRET_KEY to a non-insecure value in production.")
if len(SECRET_KEY) < 50:
    raise ValueError("DJANGO_SECRET_KEY must be at least 50 characters.")

ALLOWED_HOSTS = get_list("DJANGO_ALLOWED_HOSTS")
if not ALLOWED_HOSTS:
    raise ValueError("Set DJANGO_ALLOWED_HOSTS in production.")

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = get_bool("DJANGO_SECURE_SSL_REDIRECT", default=True)
SECURE_HSTS_SECONDS = get_int("DJANGO_SECURE_HSTS_SECONDS", 60 * 60 * 24 * 365)
SECURE_HSTS_INCLUDE_SUBDOMAINS = get_bool(
    "DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS",
    default=True,
)
SECURE_HSTS_PRELOAD = get_bool("DJANGO_SECURE_HSTS_PRELOAD", default=False)

# Preload is a one-way door: getting a domain off the browser preload list
# takes months. Products opt in with DJANGO_SECURE_HSTS_PRELOAD=true, so the
# matching deploy-check warning is silenced only while it is off.
SILENCED_SYSTEM_CHECKS = [] if SECURE_HSTS_PRELOAD else ["security.W021"]
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

csrf_origins = get_list("DJANGO_CSRF_TRUSTED_ORIGINS")
if csrf_origins:
    CSRF_TRUSTED_ORIGINS = csrf_origins

# Hashed, compressed static files served by WhiteNoise. Run collectstatic on
# deploy; a missing file becomes a build error instead of a broken page.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
    },
}

MAILERS = {
    "default": build_mailer("django.core.mail.backends.smtp.EmailBackend"),
}

ADMINS = [("ops", email) for email in get_list("DJANGO_ADMIN_EMAILS")]
