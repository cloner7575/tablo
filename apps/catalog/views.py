from __future__ import annotations

from django.db.models import Count, Q, QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods

from apps.catalog.demo import attach_demo_image as attach_service_demo
from apps.catalog.forms import ServiceSearchForm
from apps.catalog.models import CityServicePage, Service
from apps.catalog.selectors import active_services
from apps.common.seo import breadcrumbs, public_url
from apps.editorial.selectors import published_articles, published_ideas
from apps.locations.models import City
from apps.portfolio.demo import attach_demo_image
from apps.portfolio.selectors import discoverable_items
from apps.vendors.demo import attach_demo_cover
from apps.vendors.models import Vendor, VerificationStatus


@require_http_methods(["GET"])
def service_index(request: HttpRequest) -> HttpResponse:
    form = ServiceSearchForm(request.GET)
    valid = form.is_valid()
    query = form.cleaned_data.get("q", "") if valid else ""
    services = list(active_services(query)) if valid else []
    for service in services:
        attach_service_demo(service)
    return render(
        request,
        "pages/catalog/services.html",
        {
            "form": form,
            "services": services,
            "query": query,
            "SEO_TITLE": "خدمات تابلوسازی؛ انتخاب نوع تابلو و دریافت پیشنهاد",
            "SEO_DESCRIPTION": (
                "انواع تابلو، کاربرد و متریال را بررسی کنید؛ "
                "نوع مناسب کسب‌وکار خود را انتخاب و از متخصصان پیشنهاد اجرا دریافت کنید."
            ),
            "breadcrumb_schema": breadcrumbs(
                request, [("خانه", "/"), ("خدمات", request.path)]
            ),
        },
        status=200 if valid else 400,
    )


def _approved_vendors() -> QuerySet[Vendor]:
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
        discoverable_items()
        .filter(service=service)
        .select_related("vendor", "city")[:8]
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
            "ideas": published_ideas().filter(service=service)[:3],
            "articles": published_articles().filter(service=service)[:3],
            "SEO_TITLE": f"{service.title} | سفارش و مقایسه پیشنهاد",
            "SEO_DESCRIPTION": (service.description or service.title)[:200],
            "SEO_IMAGE": public_url(request, service.icon.url) if service.icon else "",
            "breadcrumb_schema": breadcrumbs(
                request, [("خانه", "/"), (service.title, request.path)]
            ),
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
        discoverable_items()
        .filter(city=city)
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
            "SEO_TITLE": f"تابلوسازی در {city.name}",
            "SEO_DESCRIPTION": (
                f"نمونه‌کار و متخصصان تأییدشدهٔ تابلوسازی در {city.name}؛ "
                "انتخاب تابلو و دریافت پیشنهاد اجرای پروژه."
            ),
            "breadcrumb_schema": breadcrumbs(
                request, [("خانه", "/"), (city.name, request.path)]
            ),
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
        city__is_active=True,
        service__is_active=True,
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
        {
            "page": page,
            "vendors": vendors,
            "SEO_TITLE": page.title,
            "SEO_DESCRIPTION": page.meta_description or page.title,
            "breadcrumb_schema": breadcrumbs(
                request, [("خانه", "/"), (page.title, request.path)]
            ),
        },
    )
