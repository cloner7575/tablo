from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET

from apps.analytics.services import track
from apps.catalog.demo import attach_demo_image as attach_service_demo
from apps.catalog.industry import industry_providers
from apps.catalog.models import Service
from apps.common.htmx import is_htmx
from apps.common.seo import public_url
from apps.common.services import database_status
from apps.editorial.collections import saved_idea_ids
from apps.editorial.selectors import published_articles, published_ideas
from apps.locations.models import City
from apps.portfolio.demo import PORTFOLIO_DEMO_IMAGES, attach_demo_image
from apps.portfolio.inspiration import board_ids
from apps.portfolio.selectors import discoverable_items
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

    portfolio = list(discoverable_items()[:8])
    for item in portfolio:
        attach_demo_image(item)

    reviews = (
        Review.objects.filter(
            is_published=True,
            vendor__is_active=True,
            vendor__verification_status=VerificationStatus.APPROVED,
        )
        .select_related("vendor", "customer")
        .order_by("-created_at")[:4]
    )
    return render(
        request,
        "pages/home.html",
        {
            "business_collections": [
                {
                    "title": "فروشگاه",
                    "query": "فروشگاه",
                    "description": "سردر و نما",
                    "image": "img/landing-boutique-v1.webp",
                },
                {
                    "title": "رستوران",
                    "query": "رستوران",
                    "description": "نور و حروف",
                    "image": "img/landing-restaurant-v1.webp",
                },
                {
                    "title": "شرکت",
                    "query": "شرکت",
                    "description": "نام و نشان",
                    "image": "img/landing-office-v1.webp",
                },
                {
                    "title": "راهنما",
                    "query": "راهنما",
                    "description": "مسیر و طبقات",
                    "image": "img/landing-wayfinding-v1.webp",
                },
            ],
            "services": services,
            "cities": cities,
            "vendors": vendors,
            "industry_providers": industry_providers()[:4],
            "portfolio": portfolio,
            "saved_ids": board_ids(request),
            "reviews": reviews,
            "ideas": published_ideas()[:3],
            "articles": published_articles()[:3],
            "idea_saved_ids": saved_idea_ids(request),
            "SEO_TITLE": "سفارش تابلو مغازه و مقایسه قیمت تابلوسازها",
            "SEO_DESCRIPTION": (
                "سفارش تابلو برای مغازه و شرکت؛ مقایسه پیشنهادهای ساخت و نصب "
                "و متخصصان تابلوسازی؛ "
                "از طرح‌های هوش مصنوعی و مفهومی تا اجرای پروژه."
            ),
            "stats": {
                "vendors": Vendor.objects.filter(
                    verification_status=VerificationStatus.APPROVED,
                    is_active=True,
                ).count(),
                "cities": len(cities),
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


@require_GET
def robots(request: HttpRequest) -> HttpResponse:
    return render(
        request,
        'robots.txt',
        {
            'SITEMAP_URL': public_url(
                request, reverse('django.contrib.sitemaps.views.sitemap')
            )
        },
        content_type='text/plain; charset=utf-8',
    )


@require_GET
def guide(request: HttpRequest) -> HttpResponse:
    return render(request, "pages/guide.html", {"articles": published_articles()[:3]})
