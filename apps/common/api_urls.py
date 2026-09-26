"""Version-agnostic API routes for the common app.

Included from `core/api_urls.py`; no `app_name` here so the version namespace
stays `api:v1`.
"""

from django.urls import path

from apps.common.api import HealthAPIView

urlpatterns = [
    path("health/", HealthAPIView.as_view(), name="health"),
]
