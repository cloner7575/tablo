from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from apps.portfolio.demo import attach_demo_image
from apps.portfolio.forms import PortfolioForm
from apps.portfolio.models import PortfolioItem
from apps.vendors.panel import panel_context


@require_http_methods(["GET"])
def portfolio_detail(request: HttpRequest, slug: str) -> HttpResponse:
    item = get_object_or_404(
        PortfolioItem.objects.select_related(
            "vendor",
            "vendor__city",
            "service",
            "city",
        ),
        slug=slug,
        is_published=True,
    )
    attach_demo_image(item)

    related_qs = (
        PortfolioItem.objects.filter(is_published=True)
        .exclude(pk=item.pk)
        .select_related("vendor", "service", "city")
    )
    related = list(
        related_qs.filter(vendor_id=item.vendor_id).order_by("-created_at")[:3]
    )
    if len(related) < 3 and item.service_id:
        extra = list(
            related_qs.filter(service_id=item.service_id)
            .exclude(pk__in=[r.pk for r in related])
            .order_by("-created_at")[: 3 - len(related)]
        )
        related.extend(extra)
    if len(related) < 3:
        extra = list(
            related_qs.exclude(pk__in=[r.pk for r in related]).order_by("-created_at")[
                : 3 - len(related)
            ]
        )
        related.extend(extra)
    for related_item in related:
        attach_demo_image(related_item)

    vendor = item.vendor
    return render(
        request,
        "pages/portfolio/detail.html",
        {
            "item": item,
            "related": related,
            "vendor": vendor,
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def portfolio_manage(request: HttpRequest) -> HttpResponse:
    vendor = getattr(request.user, "vendor_profile", None)
    if vendor is None:
        raise PermissionDenied
    items = vendor.portfolio_items.all()
    form = PortfolioForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        item = form.save(commit=False)
        item.vendor = vendor
        item.save()
        messages.success(request, "نمونه‌کار اضافه شد.")
        return redirect("portfolio:manage")
    return render(
        request,
        "pages/portfolio/manage.html",
        panel_context(
            vendor,
            "portfolio",
            items=items,
            form=form,
        ),
    )


@login_required
@require_http_methods(["POST"])
def portfolio_delete(request: HttpRequest, pk: int) -> HttpResponse:
    vendor = getattr(request.user, "vendor_profile", None)
    if vendor is None:
        raise PermissionDenied
    item = get_object_or_404(PortfolioItem, pk=pk, vendor=vendor)
    item.delete()
    messages.success(request, "نمونه‌کار حذف شد.")
    return redirect("portfolio:manage")
