"""Account API routes. Included from `core/api_urls.py` under the `api:v1`
namespace, so this module intentionally defines no `app_name`."""

from django.urls import path

from apps.accounts.api import MeView

urlpatterns = [
    path("me/", MeView.as_view(), name="me"),
]
