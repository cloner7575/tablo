"""API wiring.

Versions are URL namespaces (`api:v1:...`), which is what DRF's
`NamespaceVersioning` reads. Adding v2 means a second `include()` here, not a
rewrite of every app.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.common.api_domain import (
    CityViewSet,
    MeView,
    PortfolioViewSet,
    ProjectRequestViewSet,
    QuoteViewSet,
    ReviewViewSet,
    ServiceViewSet,
    VendorViewSet,
    otp_request,
    otp_verify,
)

router = DefaultRouter()
router.register("cities", CityViewSet, basename="city")
router.register("services", ServiceViewSet, basename="service")
router.register("vendors", VendorViewSet, basename="vendor")
router.register("requests", ProjectRequestViewSet, basename="request")
router.register("quotes", QuoteViewSet, basename="quote")
router.register("portfolio", PortfolioViewSet, basename="portfolio")
router.register("reviews", ReviewViewSet, basename="review")

v1_patterns = [
    path("", include("apps.common.api_urls")),
    path("accounts/", include("apps.accounts.api_urls")),
    path("auth/otp/request/", otp_request, name="otp-request"),
    path("auth/otp/verify/", otp_verify, name="otp-verify"),
    path("auth/me/", MeView.as_view(), name="auth-me"),
    path("", include(router.urls)),
]

app_name = "api"

urlpatterns = [
    path("v1/", include((v1_patterns, "v1"), namespace="v1")),
]
