from __future__ import annotations

from django.db.models import Count, Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods

from apps.catalog.demo import attach_demo_image as attach_service_demo
from apps.catalog.models import CityServicePage, Service
from apps.locations.models import City
from apps.portfolio.demo import attach_demo_image
from apps.portfolio.models import PortfolioItem
from apps.vendors.demo import attach_demo_cover
from apps.vendors.models import Vendor, VerificationStatus


def _approved_vendors():
    return (
        Vendor.objects.filter(
            is_active=True,
            verification_status=VerificationStatus.APPROVED,
        )
        .select_related("city")
        .prefetch_related("services")
        .annotate(
            portfolio_count=Count(
                "portfolio_items",
                filter=Q(portfolio_items__is_published=True),
            )
        )
    )


@require_http_methods(["GET"])
def service_detail(request: HttpRequest, slug: str) -> HttpResponse:
    service = get_object_or_404(Service, slug=slug, is_active=True)
    attach_service_demo(service)
    vendors = list(_approved_vendors().filter(services=service).distinct()[:12])
    for vendor in vendors:
        attach_demo_cover(vendor)
    portfolio = list(
        PortfolioItem.objects.filter(service=service, is_published=True)
        .select_related("vendor", "city")
        .order_by("-created_at")[:8]
    )
    for item in portfolio:
        attach_demo_image(item)
    related_services = list(
        Service.objects.filter(is_active=True).exclude(pk=service.pk)[:6]
    )
    for related in related_services:
        attach_service_demo(related)
    faq = service.faq if isinstance(service.faq, list) else []
    return render(
        request,
        "pages/seo/service.html",
        {
            "service": service,
            "vendors": vendors,
            "vendors_count": len(vendors),
            "portfolio": portfolio,
            "related_services": related_services,
            "faq": faq,
        },
    )


@require_http_methods(["GET"])
def city_detail(request: HttpRequest, slug: str) -> HttpResponse:
    city = get_object_or_404(City, slug=slug, is_active=True)
    vendors = list(
        _approved_vendors().filter(city=city).order_by("-is_featured", "-rating")[:12]
    )
    for vendor in vendors:
        attach_demo_cover(vendor)
    services = list(Service.objects.filter(is_active=True))
    portfolio = list(
        PortfolioItem.objects.filter(city=city, is_published=True)
        .select_related("vendor", "service")
        .order_by("-created_at")[:6]
    )
    for item in portfolio:
        attach_demo_image(item)
    return render(
        request,
        "pages/seo/city.html",
        {
            "city": city,
            "vendors": vendors,
            "services": services,
            "portfolio": portfolio,
        },
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
    vendors = list(
        _approved_vendors()
        .filter(city=page.city, services=page.service)
        .distinct()[:12]
    )
    for vendor in vendors:
        attach_demo_cover(vendor)
    return render(
        request,
        "pages/seo/city_service.html",
        {"page": page, "vendors": vendors},
    )
