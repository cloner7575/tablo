from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Count, Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import urlencode
from django.views.decorators.http import require_http_methods

from apps.analytics.services import track
from apps.portfolio.demo import attach_demo_image
from apps.quotes.forms import QuoteForm
from apps.quotes.models import Quote, QuoteStatus
from apps.quotes.services import create_quote
from apps.requests.selectors import (
    GUIDANCE_FILTER,
    filter_by_service,
    matched_requests_for_vendor,
    with_feed_counts,
)
from apps.vendors.demo import attach_demo_cover
from apps.vendors.forms import VendorOnboardingForm, VendorProfileForm
from apps.vendors.models import Vendor, VerificationStatus
from apps.vendors.panel import (
    checklist_progress,
    panel_context,
    profile_checklist,
)

REQUEST_TABS = (
    ("open", "بدون پیشنهاد من"),
    ("quoted", "پیشنهاد داده‌ام"),
    ("all", "همه"),
)
DEFAULT_REQUEST_TAB = "open"
REQUEST_FEED_LIMIT = 50


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
    track("vendor_profile_view", {"slug": slug})
    portfolio = list(vendor.portfolio_items.filter(is_published=True)[:12])
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
    return render(
        request,
        "pages/vendors/public.html",
        {
            "vendor": vendor,
            "portfolio": portfolio,
            "has_portfolio": bool(portfolio),
            "reviews": vendor.reviews.filter(is_published=True)[:10],
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
    quotes = vendor.quotes.select_related(
        "request", "request__service", "request__city"
    )
    quoted_ids = set(quotes.values_list("request_id", flat=True))
    open_requests = [r for r in matched[:20] if r.pk not in quoted_ids][:5]
    checklist = profile_checklist(vendor)
    done, total = checklist_progress(checklist)
    return render(
        request,
        "pages/vendors/dashboard.html",
        panel_context(
            vendor,
            "dashboard",
            matched_count=matched.count(),
            quotes_count=quotes.count(),
            pending_quotes_count=quotes.filter(
                status__in=[QuoteStatus.PENDING, QuoteStatus.VIEWED]
            ).count(),
            accepted_count=quotes.filter(status=QuoteStatus.ACCEPTED).count(),
            portfolio_count=vendor.portfolio_items.count(),
            rating=vendor.rating,
            response_time=vendor.response_time_hours,
            recent_requests=open_requests,
            recent_quotes=quotes.order_by("-created_at")[:5],
            checklist=checklist,
            checklist_done=done,
            checklist_total=total,
        ),
    )


def _feed_url(status: str, service: str) -> str:
    params = {
        key: value
        for key, value in (
            ("status", "" if status == DEFAULT_REQUEST_TAB else status),
            ("service", service),
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

    base = filter_by_service(matched_requests_for_vendor(vendor), service)
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

    chips = [("", "همه")] + [(s.slug, s.title) for s in services]
    chips.append((GUIDANCE_FILTER, "نیاز به راهنمایی"))
    return render(
        request,
        "pages/vendors/requests.html",
        panel_context(
            vendor,
            "requests",
            requests=list(with_feed_counts(feed)[:REQUEST_FEED_LIMIT]),
            quoted_ids=quoted_ids,
            status=status,
            service=service,
            status_tabs=[
                {
                    "key": key,
                    "label": label,
                    "count": counts[key],
                    "url": _feed_url(key, service),
                    "current": key == status,
                }
                for key, label in REQUEST_TABS
            ],
            service_filters=[
                {
                    "label": label,
                    "url": _feed_url(status, slug),
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
            matched_requests_for_vendor(vendor)
            .select_related("service", "city")
            .prefetch_related("images")
        ),
        pk=pk,
    )
    existing = Quote.objects.filter(request=project_request, vendor=vendor).first()
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
    from django.db.models import Exists, OuterRef

    from apps.chat.models import Conversation

    quotes = list(
        vendor.quotes.select_related("request__service", "request__city", "request")
        .annotate(has_chat=Exists(Conversation.objects.filter(quote_id=OuterRef("pk"))))
        .order_by("-created_at")
    )
    return render(
        request,
        "pages/vendors/quotes.html",
        panel_context(
            vendor,
            "quotes",
            quotes=quotes,
            accepted_count=sum(1 for q in quotes if q.status == QuoteStatus.ACCEPTED),
            pending_count=sum(
                1
                for q in quotes
                if q.status in {QuoteStatus.PENDING, QuoteStatus.VIEWED}
            ),
        ),
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
    vendors = list(
        Vendor.objects.filter(
            is_active=True, verification_status=VerificationStatus.APPROVED
        )
        .select_related("city")
        .prefetch_related("services")
        .annotate(
            portfolio_count=Count(
                "portfolio_items",
                filter=Q(portfolio_items__is_published=True),
            )
        )
        .order_by("-is_featured", "-rating")
    )
    for vendor in vendors:
        attach_demo_cover(vendor)
    return render(
        request,
        "pages/vendors/list.html",
        {
            "vendors": vendors,
            "vendors_count": len(vendors),
        },
    )
