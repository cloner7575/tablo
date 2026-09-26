from django.db.models import Sum
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET

from apps.analytics.services import track
from apps.catalog.demo import attach_demo_image as attach_service_demo
from apps.catalog.models import Service
from apps.common.htmx import is_htmx
from apps.common.services import database_status
from apps.locations.models import City
from apps.portfolio.demo import PORTFOLIO_DEMO_IMAGES, attach_demo_image
from apps.portfolio.models import PortfolioItem
from apps.reviews.models import Review
from apps.vendors.demo import VENDOR_DEMO_COVERS, attach_demo_cover
from apps.vendors.models import Vendor, VerificationStatus

PORTFOLIO_IMAGES = PORTFOLIO_DEMO_IMAGES
VENDOR_COVERS = VENDOR_DEMO_COVERS


@require_GET
def home(request: HttpRequest) -> HttpResponse:
    track("homepage_view", {})
    services = list(Service.objects.filter(is_active=True)[:6])
    for service in services:
        attach_service_demo(service)

    cities = list(City.objects.filter(is_active=True))
    vendors = list(
        Vendor.objects.filter(
            is_active=True,
            verification_status=VerificationStatus.APPROVED,
        )
        .select_related("city")
        .order_by("-is_featured", "-rating")[:6]
    )
    for vendor in vendors:
        attach_demo_cover(vendor)

    portfolio = list(
        PortfolioItem.objects.filter(is_published=True)
        .select_related("vendor", "service", "city")
        .order_by("-created_at")[:8]
    )
    for item in portfolio:
        attach_demo_image(item)

    reviews = (
        Review.objects.filter(is_published=True)
        .select_related("vendor", "customer")
        .order_by("-created_at")[:4]
    )
    return render(
        request,
        "pages/home.html",
        {
            "services": services,
            "cities": cities,
            "vendors": vendors,
            "portfolio": portfolio,
            "reviews": reviews,
            "stats": {
                "vendors": Vendor.objects.filter(
                    verification_status=VerificationStatus.APPROVED,
                    is_active=True,
                ).count(),
                "projects": Vendor.objects.aggregate(total=Sum("completed_projects"))[
                    "total"
                ]
                or 0,
                "cities": City.objects.filter(is_active=True).count(),
            },
        },
    )


@require_GET
def health(request: HttpRequest) -> JsonResponse:
    reachable, database = database_status()
    payload = {"status": "ok" if reachable else "degraded", "database": database}
    code = 200 if reachable else 503
    return JsonResponse(payload, status=code)


@require_GET
def health_panel(request: HttpRequest) -> HttpResponse:
    if not is_htmx(request):
        return redirect(reverse("common:home"))
    reachable, database = database_status()
    return render(
        request,
        "partials/_health.html",
        {
            "reachable": reachable,
            "database": database,
        },
    )
