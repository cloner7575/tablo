from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods

from apps.catalog.models import CityServicePage, Service
from apps.locations.models import City
from apps.portfolio.models import PortfolioItem
from apps.vendors.models import Vendor, VerificationStatus


@require_http_methods(["GET"])
def service_detail(request: HttpRequest, slug: str) -> HttpResponse:
    service = get_object_or_404(Service, slug=slug, is_active=True)
    vendors = (
        Vendor.objects.filter(
            services=service,
            is_active=True,
            verification_status=VerificationStatus.APPROVED,
        )
        .select_related("city")
        .distinct()[:12]
    )
    portfolio = PortfolioItem.objects.filter(
        service=service, is_published=True
    ).select_related("vendor")[:8]
    return render(
        request,
        "pages/seo/service.html",
        {"service": service, "vendors": vendors, "portfolio": portfolio},
    )


@require_http_methods(["GET"])
def city_detail(request: HttpRequest, slug: str) -> HttpResponse:
    city = get_object_or_404(City, slug=slug, is_active=True)
    vendors = Vendor.objects.filter(
        city=city,
        is_active=True,
        verification_status=VerificationStatus.APPROVED,
    ).prefetch_related("services")[:12]
    services = Service.objects.filter(is_active=True)
    return render(
        request,
        "pages/seo/city.html",
        {"city": city, "vendors": vendors, "services": services},
    )


@require_http_methods(["GET"])
def city_service(
    request: HttpRequest, city_slug: str, service_slug: str
) -> HttpResponse:
    page = get_object_or_404(
        CityServicePage.objects.select_related("city", "service"),
        city__slug=city_slug,
        slug=service_slug,
        is_published=True,
    )
    vendors = Vendor.objects.filter(
        city=page.city,
        services=page.service,
        is_active=True,
        verification_status=VerificationStatus.APPROVED,
    )[:12]
    return render(
        request,
        "pages/seo/city_service.html",
        {"page": page, "vendors": vendors},
    )
