from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import urlencode
from django.views.decorators.http import require_http_methods

from apps.analytics.services import track
from apps.common.seo import breadcrumbs, public_url
from apps.orders.models import Order, OrderStatus
from apps.portfolio.demo import attach_demo_image
from apps.portfolio.selectors import published_items
from apps.quotes.forms import QuoteForm
from apps.quotes.models import Quote, QuoteStatus
from apps.quotes.services import create_quote
from apps.requests.models import ProjectRequest
from apps.requests.selectors import (
    GUIDANCE_FILTER,
    filter_by_service,
    matched_requests_for_vendor,
    with_feed_counts,
)
from apps.vendors.demo import attach_demo_cover
from apps.vendors.forms import (
    ProjectWorkspaceFilterForm,
    QuoteWorkspaceFilterForm,
    RequestFeedSearchForm,
    VendorOnboardingForm,
    VendorProfileForm,
    VendorSearchForm,
)
from apps.vendors.models import Vendor, VerificationStatus
from apps.vendors.panel import (
    checklist_progress,
    panel_context,
    profile_checklist,
)
from apps.vendors.selectors import discoverable_vendors, vendor_quotes

REQUEST_TABS = (
    ("open", "بدون پیشنهاد من"),
    ("quoted", "پیشنهاد داده‌ام"),
    ("all", "همه"),
)
DEFAULT_REQUEST_TAB = "open"


def _require_vendor(request: HttpRequest) -> Vendor:
    if not request.user.is_authenticated:
        raise PermissionDenied
    vendor = getattr(request.user, "vendor_profile", None)
    if vendor is None:
        raise PermissionDenied
    return vendor


@require_http_methods(["GET"])
def vendor_public(request: HttpRequest, slug: str) -> HttpResponse:
    vendor = get_object_or_404(
        Vendor.objects.select_related("city").prefetch_related(
            "services", "portfolio_items", "reviews__customer"
        ),
        slug=slug,
        is_active=True,
        verification_status=VerificationStatus.APPROVED,
    )
    published_reviews = [
        review for review in vendor.reviews.all() if review.is_published
    ]
    vendor.review_count = len(published_reviews)
    if published_reviews:
        from decimal import Decimal

        vendor.rating = (
            sum(Decimal(review.rating) for review in published_reviews)
            / Decimal(len(published_reviews))
        ).quantize(Decimal("0.1"))
    track("vendor_profile_view", {"slug": slug})
    portfolio = list(published_items().filter(vendor=vendor)[:12])
    for item in portfolio:
        attach_demo_image(item)
    attach_demo_cover(vendor)
    related = list(
        Vendor.objects.filter(
            is_active=True,
            verification_status=VerificationStatus.APPROVED,
            city_id=vendor.city_id,
        )
        .exclude(pk=vendor.pk)
        .select_related("city")
        .prefetch_related("services")
        .annotate(
            portfolio_count=Count(
                "portfolio_items",
                filter=Q(portfolio_items__is_published=True),
            )
        )
        .order_by("-rating")[:3]
    )
    for peer in related:
        attach_demo_cover(peer)
    vendor_schema = {
        '@context': 'https://schema.org',
        '@type': 'LocalBusiness',
        'name': vendor.business_name,
        'url': public_url(request, request.path),
        'description': vendor.description[:200],
        'address': {'@type': 'PostalAddress', 'addressLocality': vendor.city.name},
    }
    if vendor.cover_image:
        vendor_schema['image'] = public_url(request, vendor.cover_image.url)
    if vendor.review_count:
        vendor_schema['aggregateRating'] = {
            '@type': 'AggregateRating',
            'ratingValue': str(vendor.rating),
            'reviewCount': vendor.review_count,
        }
    return render(
        request,
        "pages/vendors/public.html",
        {
            "vendor": vendor,
            "SEO_TITLE": f"{vendor.business_name} | تابلوساز در {vendor.city.name}",
            "SEO_DESCRIPTION": (
                f"{vendor.business_name} در {vendor.city.name}؛ "
                "مشاهدهٔ خدمات و نمونه‌کارها و درخواست پیشنهاد اجرای تابلو."
            ),
            "SEO_IMAGE": public_url(request, vendor.cover_image.url)
            if vendor.cover_image
            else "",
            "portfolio": portfolio,
            "has_portfolio": bool(portfolio),
            "vendor_schema": vendor_schema,
            "breadcrumb_schema": breadcrumbs(
                request, [("خانه", "/"), (vendor.business_name, request.path)]
            ),
            "reviews": published_reviews[:10],
            "related_vendors": related,
            "services": list(vendor.services.all()),
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def onboarding(request: HttpRequest) -> HttpResponse:
    if hasattr(request.user, "vendor_profile"):
        return redirect("vendors:dashboard")

    form = VendorOnboardingForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        vendor = form.save(commit=False)
        vendor.user = request.user
        vendor.phone = vendor.phone or request.user.phone or ""
        vendor.verification_status = VerificationStatus.PENDING
        vendor.save()
        form.save_m2m()
        messages.success(
            request,
            (
                "پروفایل ثبت شد و در انتظار تأیید مدیریت است. "
                "تا تأیید، در فهرست عمومی دیده نمی‌شوید."
            ),
        )
        return redirect("vendors:dashboard")
    return render(request, "pages/vendors/onboarding.html", {"form": form})


@login_required
@require_http_methods(["GET"])
def dashboard(request: HttpRequest) -> HttpResponse:
    try:
        vendor = _require_vendor(request)
    except PermissionDenied:
        return redirect("vendors:onboarding")

    matched = matched_requests_for_vendor(vendor)
    quotes = vendor_quotes(vendor)
    quote_stats = quotes.aggregate(
        total=Count("pk"),
        pending=Count(
            "pk",
            filter=Q(
                status__in=[
                    QuoteStatus.PENDING,
                    QuoteStatus.VIEWED,
                    QuoteStatus.SHORTLISTED,
                ]
            ),
        ),
        accepted=Count("pk", filter=Q(status=QuoteStatus.ACCEPTED)),
    )
    open_feed = matched.exclude(pk__in=vendor.quotes.values("request_id"))
    open_requests = list(open_feed[:5])
    checklist = profile_checklist(vendor)
    done, total = checklist_progress(checklist)
    return render(
        request,
        "pages/vendors/dashboard.html",
        panel_context(
            vendor,
            "dashboard",
            matched_count=matched.count(),
            quotes_count=quote_stats["total"],
            pending_quotes_count=quote_stats["pending"],
            accepted_count=quote_stats["accepted"],
            active_projects_count=Order.objects.filter(
                vendor=vendor, status=OrderStatus.ACTIVE
            ).count(),
            new_requests_count=open_feed.count(),
            portfolio_count=vendor.portfolio_items.count(),
            rating=vendor.rating,
            response_time=vendor.response_time_hours,
            recent_requests=open_requests,
            recent_quotes=quotes[:5],
            recent_orders=Order.objects.filter(
                vendor=vendor, status=OrderStatus.ACTIVE
            ).select_related("request", "quote")[:3],
            checklist=checklist,
            checklist_done=done,
            checklist_total=total,
        ),
    )


def _feed_url(status: str, service: str, query: str = "") -> str:
    params = {
        key: value
        for key, value in (
            ("status", "" if status == DEFAULT_REQUEST_TAB else status),
            ("service", service),
            ("q", query),
        )
        if value
    }
    base = reverse("vendors:requests")
    return f"{base}?{urlencode(params)}" if params else base


@login_required
@require_http_methods(["GET"])
def request_list(request: HttpRequest) -> HttpResponse:
    vendor = _require_vendor(request)
    services = list(vendor.services.all())

    status = request.GET.get("status", DEFAULT_REQUEST_TAB)
    if status not in dict(REQUEST_TABS):
        status = DEFAULT_REQUEST_TAB
    service = request.GET.get("service", "")
    if service not in {s.slug for s in services} | {GUIDANCE_FILTER}:
        service = ""

    form = RequestFeedSearchForm(request.GET)
    valid = form.is_valid()
    query = form.cleaned_data["q"] if valid else ""
    base = filter_by_service(matched_requests_for_vendor(vendor), service)
    if query:
        base = base.filter(
            Q(title__icontains=query)
            | Q(district__icontains=query)
            | Q(business_type__icontains=query)
        )
    if not valid:
        base = base.none()
    quoted_ids = set(vendor.quotes.values_list("request_id", flat=True))
    all_count = base.count()
    quoted_count = base.filter(pk__in=quoted_ids).count()
    counts = {
        "open": all_count - quoted_count,
        "quoted": quoted_count,
        "all": all_count,
    }

    feed = base
    if status == "open":
        feed = feed.exclude(pk__in=quoted_ids)
    elif status == "quoted":
        feed = feed.filter(pk__in=quoted_ids)

    page_obj = Paginator(with_feed_counts(feed), 20).get_page(request.GET.get("page"))
    filters = {"status": status, "service": service, "q": query}
    chips = [("", "همه")] + [(s.slug, s.title) for s in services]
    chips.append((GUIDANCE_FILTER, "نیاز به راهنمایی"))
    return render(
        request,
        "pages/vendors/requests.html",
        panel_context(
            vendor,
            "requests",
            requests=list(page_obj.object_list),
            page_obj=page_obj,
            form=form,
            filter_query=urlencode(
                {key: value for key, value in filters.items() if value}
            ),
            quoted_ids=quoted_ids,
            status=status,
            service=service,
            status_tabs=[
                {
                    "key": key,
                    "label": label,
                    "count": counts[key],
                    "url": _feed_url(key, service, query),
                    "current": key == status,
                }
                for key, label in REQUEST_TABS
            ],
            service_filters=[
                {
                    "label": label,
                    "url": _feed_url(status, slug, query),
                    "current": slug == service,
                }
                for slug, label in chips
            ],
        ),
    )


@login_required
@require_http_methods(["GET"])
def request_detail(request: HttpRequest, pk: int) -> HttpResponse:
    vendor = _require_vendor(request)
    project_request = get_object_or_404(
        with_feed_counts(
            ProjectRequest.objects.filter(
                Q(pk__in=matched_requests_for_vendor(vendor).values("pk"))
                | Q(quotes__vendor=vendor)
            )
            .distinct()
            .select_related("service", "city")
            .prefetch_related("images")
        ),
        pk=pk,
    )
    existing = (
        Quote.objects.select_related("conversation", "order")
        .filter(request=project_request, vendor=vendor)
        .first()
    )
    return render(
        request,
        "pages/vendors/request_detail.html",
        panel_context(
            vendor,
            "requests",
            project_request=project_request,
            photos=project_request.photo_urls(),
            existing=existing,
        ),
    )


@login_required
@require_http_methods(["GET", "POST"])
def request_quote(request: HttpRequest, pk: int) -> HttpResponse:
    vendor = _require_vendor(request)
    project_request = get_object_or_404(
        matched_requests_for_vendor(vendor)
        .select_related("service", "city")
        .prefetch_related("images"),
        pk=pk,
    )
    existing = Quote.objects.filter(request=project_request, vendor=vendor).first()
    if existing is not None:
        messages.info(request, "برای این درخواست قبلاً پیشنهاد ثبت کرده‌اید.")
        return redirect("vendors:request_detail", pk=pk)

    form = QuoteForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            create_quote(
                vendor=vendor,
                project_request=project_request,
                **form.cleaned_data,
            )
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, str(exc))
        else:
            messages.success(request, "پیشنهاد شما ارسال شد.")
            return redirect("vendors:my_quotes")
    return render(
        request,
        "pages/vendors/request_quote.html",
        panel_context(
            vendor,
            "requests",
            project_request=project_request,
            photos=project_request.photo_urls(),
            form=form,
        ),
    )


@login_required
@require_http_methods(["GET"])
def my_quotes(request: HttpRequest) -> HttpResponse:
    vendor = _require_vendor(request)
    base = vendor_quotes(vendor)
    stats = base.aggregate(
        total=Count("pk"),
        accepted=Count("pk", filter=Q(status=QuoteStatus.ACCEPTED)),
        pending=Count(
            "pk",
            filter=Q(
                status__in=[
                    QuoteStatus.PENDING,
                    QuoteStatus.VIEWED,
                    QuoteStatus.SHORTLISTED,
                ]
            ),
        ),
    )
    form = QuoteWorkspaceFilterForm(request.GET)
    valid = form.is_valid()
    filtered = base if valid else base.none()
    if valid:
        if form.cleaned_data["q"]:
            filtered = filtered.filter(request__title__icontains=form.cleaned_data["q"])
        status = form.cleaned_data["status"]
        if status == "pending":
            filtered = filtered.filter(
                status__in=[
                    QuoteStatus.PENDING,
                    QuoteStatus.VIEWED,
                    QuoteStatus.SHORTLISTED,
                ]
            )
        elif status == "viewed":
            filtered = filtered.filter(
                status__in=[QuoteStatus.VIEWED, QuoteStatus.SHORTLISTED]
            )
        elif status:
            filtered = filtered.filter(status=status)
    page_obj = Paginator(filtered, 12).get_page(request.GET.get("page"))
    filters = request.GET.copy()
    filters.pop("page", None)
    return render(
        request,
        "pages/vendors/quotes.html",
        panel_context(
            vendor,
            "quotes",
            quotes=list(page_obj.object_list),
            page_obj=page_obj,
            form=form,
            filter_query=filters.urlencode(),
            total_count=stats["total"],
            accepted_count=stats["accepted"],
            pending_count=stats["pending"],
        ),
        status=200 if valid else 400,
    )


@login_required
@require_http_methods(["GET"])
def projects(request: HttpRequest) -> HttpResponse:
    vendor = _require_vendor(request)
    base = (
        Order.objects.filter(vendor=vendor)
        .select_related("request__service", "request__city", "quote__conversation")
        .order_by("-created_at", "-pk")
    )
    stats = base.aggregate(
        total=Count("pk"),
        active=Count("pk", filter=Q(status=OrderStatus.ACTIVE)),
        completed=Count("pk", filter=Q(status=OrderStatus.COMPLETED)),
    )
    form = ProjectWorkspaceFilterForm(request.GET)
    valid = form.is_valid()
    filtered = base if valid else base.none()
    if valid:
        if form.cleaned_data["q"]:
            filtered = filtered.filter(request__title__icontains=form.cleaned_data["q"])
        if form.cleaned_data["status"]:
            filtered = filtered.filter(status=form.cleaned_data["status"])
    page_obj = Paginator(filtered, 12).get_page(request.GET.get("page"))
    filters = request.GET.copy()
    filters.pop("page", None)
    return render(
        request,
        "pages/vendors/projects.html",
        panel_context(
            vendor,
            "projects",
            orders=list(page_obj.object_list),
            page_obj=page_obj,
            form=form,
            summary=stats,
            filter_query=filters.urlencode(),
        ),
        status=200 if valid else 400,
    )


@login_required
@require_http_methods(["GET", "POST"])
def profile_edit(request: HttpRequest) -> HttpResponse:
    vendor = _require_vendor(request)
    form = VendorProfileForm(
        request.POST or None, request.FILES or None, instance=vendor
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "پروفایل به‌روز شد.")
        return redirect("vendors:profile")
    return render(
        request,
        "pages/vendors/profile.html",
        panel_context(
            vendor,
            "profile",
            form=form,
            checklist=profile_checklist(vendor),
        ),
    )


@require_http_methods(["GET"])
def vendor_list(request: HttpRequest) -> HttpResponse:
    form = VendorSearchForm(request.GET)
    valid = form.is_valid()
    queryset = (
        discoverable_vendors(
            query=form.cleaned_data["q"],
            city=form.cleaned_data["city"],
            service=form.cleaned_data["service"],
            sort=form.cleaned_data["sort"],
        )
        if valid
        else Vendor.objects.none()
    )
    page_obj = Paginator(queryset, 12).get_page(request.GET.get("page"))
    vendors = list(page_obj.object_list)
    for vendor in vendors:
        attach_demo_cover(vendor)
    filters = request.GET.copy()
    filters.pop("page", None)
    from apps.catalog.industry import industry_providers

    references = (
        industry_providers(
            query=form.cleaned_data["q"],
            city_slug=form.cleaned_data["city"].slug
            if form.cleaned_data["city"]
            else "",
            service_slug=form.cleaned_data["service"].slug
            if form.cleaned_data["service"]
            else "",
        )
        if valid
        else []
    )
    return render(
        request,
        "pages/vendors/list.html",
        {
            "vendors": vendors,
            "industry_providers": references,
            "vendors_count": page_obj.paginator.count,
            "page_obj": page_obj,
            "form": form,
            "filter_query": filters.urlencode(),
            "has_filters": bool(filters),
            "SEO_TITLE": "متخصصان و تابلوسازهای تأییدشده",
            "SEO_DESCRIPTION": (
                "تابلوسازهای تأییدشده را با خدمات، شهر و نمونه‌کارهایشان بشناسید "
                "و برای پروژهٔ خود پیشنهاد بگیرید."
            ),
        },
        status=200 if valid else 400,
    )
