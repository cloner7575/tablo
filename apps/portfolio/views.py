from __future__ import annotations

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from apps.common.persian import to_persian_digits
from apps.portfolio.demo import attach_demo_image
from apps.portfolio.forms import (
    PortfolioCreateForm,
    PortfolioForm,
    PortfolioMediaForm,
    max_media,
)
from apps.portfolio.models import PortfolioItem, PortfolioMedia
from apps.portfolio.selectors import (
    detail_queryset,
    portfolio_slides,
    published_items,
    vendor_item_counts,
    vendor_items,
    with_media_counts,
)
from apps.portfolio.services import (
    add_media,
    create_item,
    delete_item,
    delete_media,
    move_media,
    set_cover,
)
from apps.vendors.models import Vendor
from apps.vendors.panel import panel_context

RELATED_LIMIT = 3
THUMB_SLOTS = 5
MEDIA_TABS = ("images", "video", "aparat")
LIST_STATUSES = ("all", "published", "draft")


def _video_hint() -> str:
    max_mb = to_persian_digits(settings.VIDEO_UPLOAD_MAX_BYTES // 2**20)
    return f"حداکثر {max_mb} مگابایت — برای ویدیوی طولانی، لینک آپارات بهتر است"


def _vendor_or_403(request: HttpRequest) -> Vendor:
    vendor = getattr(request.user, "vendor_profile", None)
    if vendor is None:
        raise PermissionDenied
    return vendor


def _related_items(item: PortfolioItem) -> list[PortfolioItem]:
    related_qs = with_media_counts(
        published_items()
        .exclude(pk=item.pk)
        .select_related("vendor", "service", "city")
    ).order_by("-created_at")
    related = list(related_qs.filter(vendor_id=item.vendor_id)[:RELATED_LIMIT])
    if len(related) < RELATED_LIMIT and item.service_id:
        related.extend(
            related_qs.filter(service_id=item.service_id).exclude(
                pk__in=[r.pk for r in related]
            )[: RELATED_LIMIT - len(related)]
        )
    if len(related) < RELATED_LIMIT:
        related.extend(
            related_qs.exclude(pk__in=[r.pk for r in related])[
                : RELATED_LIMIT - len(related)
            ]
        )
    for related_item in related:
        attach_demo_image(related_item)
    return related


@require_http_methods(["GET"])
def portfolio_detail(request: HttpRequest, slug: str) -> HttpResponse:
    item = get_object_or_404(detail_queryset(), slug=slug)
    slides = portfolio_slides(item)
    # The last thumbnail slot turns into a "+N" tile once slides overflow the row.
    overflow = len(slides) > THUMB_SLOTS
    thumbs = slides[: THUMB_SLOTS - 1] if overflow else slides
    return render(
        request,
        "pages/portfolio/detail.html",
        {
            "item": item,
            "vendor": item.vendor,
            "slides": slides,
            "thumbs": thumbs if len(slides) > 1 else [],
            "more_count": len(slides) - len(thumbs),
            "more_index": len(thumbs),
            "more_thumb": slides[len(thumbs)].thumb if overflow else "",
            "photo_count": sum(1 for s in slides if not s.is_video),
            "video_count": sum(1 for s in slides if s.is_video),
            "related": _related_items(item),
        },
    )


@login_required
@require_http_methods(["GET"])
def portfolio_manage(request: HttpRequest) -> HttpResponse:
    vendor = _vendor_or_403(request)
    status = request.GET.get("status", "all")
    if status not in LIST_STATUSES:
        status = "all"
    query = request.GET.get("q", "").strip()[:80]
    items = list(vendor_items(vendor, status=status, query=query))
    for item in items:
        attach_demo_image(item)
    return render(
        request,
        "pages/portfolio/manage.html",
        panel_context(
            vendor,
            "portfolio",
            items=items,
            counts=vendor_item_counts(vendor),
            status=status,
            query=query,
        ),
    )


@login_required
@require_http_methods(["GET", "POST"])
def portfolio_create(request: HttpRequest) -> HttpResponse:
    vendor = _vendor_or_403(request)
    form = PortfolioCreateForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        item = form.save(commit=False)
        item.vendor = vendor
        data = form.cleaned_data
        create_item(
            item=item,
            gallery=data["gallery"],
            video=data["video"],
            poster=data["poster"],
            aparat_url=data["aparat_url"],
        )
        messages.success(
            request,
            "نمونه‌کار اضافه شد. از همین صفحه می‌توانید رسانه‌های بیشتری اضافه کنید.",
        )
        return redirect("portfolio:edit", pk=item.pk)
    return render(
        request,
        "pages/portfolio/create.html",
        panel_context(vendor, "portfolio", form=form, video_hint=_video_hint()),
        status=400 if form.is_bound else 200,
    )


def _owned_item(vendor: Vendor, pk: int) -> PortfolioItem:
    return get_object_or_404(
        PortfolioItem.objects.select_related("service", "city").prefetch_related(
            "media"
        ),
        pk=pk,
        vendor=vendor,
    )


def _owned_media(vendor: Vendor, pk: int) -> PortfolioMedia:
    return get_object_or_404(
        PortfolioMedia.objects.select_related("item"), pk=pk, item__vendor=vendor
    )


def _active_media_tab(form: PortfolioMediaForm) -> str:
    submitted_from = form.data.get("tab")
    if submitted_from in MEDIA_TABS:
        return submitted_from
    if form.files.get("video") or {"video", "poster"} & form.errors.keys():
        return "video"
    if form.data.get("aparat_url") or "aparat_url" in form.errors:
        return "aparat"
    return "images"


def _render_edit(
    request: HttpRequest,
    vendor: Vendor,
    item: PortfolioItem,
    *,
    form: PortfolioForm | None = None,
    media_form: PortfolioMediaForm | None = None,
    status: int = 200,
) -> HttpResponse:
    active_tab = _active_media_tab(media_form) if media_form else "images"
    media_forms: dict[str, PortfolioMediaForm] = {}
    for tab in MEDIA_TABS:
        tab_form = (
            media_form
            if media_form is not None and tab == active_tab
            else PortfolioMediaForm(item=item)
        )
        # Each tab is its own <form>; distinct ids keep labels unambiguous.
        tab_form.auto_id = f"{tab}-%s"
        media_forms[tab] = tab_form
    media = list(item.media.all())
    limit = max_media()
    return render(
        request,
        "pages/portfolio/edit.html",
        panel_context(
            vendor,
            "portfolio",
            item=item,
            form=form or PortfolioForm(instance=item),
            media_forms=media_forms,
            media=media,
            media_limit=limit,
            media_remaining=max(limit - len(media), 0),
            video_hint=_video_hint(),
            active_tab=active_tab,
        ),
        status=status,
    )


@login_required
@require_http_methods(["GET", "POST"])
def portfolio_edit(request: HttpRequest, pk: int) -> HttpResponse:
    vendor = _vendor_or_403(request)
    item = _owned_item(vendor, pk)
    if request.method == "GET":
        return _render_edit(request, vendor, item)
    form = PortfolioForm(request.POST, request.FILES, instance=item)
    if not form.is_valid():
        return _render_edit(request, vendor, item, form=form, status=400)
    form.save()
    messages.success(request, "اطلاعات نمونه‌کار ذخیره شد.")
    return redirect("portfolio:edit", pk=item.pk)


@login_required
@require_http_methods(["POST"])
def portfolio_media_add(request: HttpRequest, pk: int) -> HttpResponse:
    vendor = _vendor_or_403(request)
    item = _owned_item(vendor, pk)
    media_form = PortfolioMediaForm(request.POST, request.FILES, item=item)
    if not media_form.is_valid():
        return _render_edit(request, vendor, item, media_form=media_form, status=400)
    data = media_form.cleaned_data
    try:
        created = add_media(
            item=item,
            images=data["images"],
            video=data["video"],
            poster=data["poster"],
            aparat_url=data["aparat_url"],
            caption=data["caption"],
        )
    except ValidationError as exc:
        media_form.add_error(None, exc)
        return _render_edit(request, vendor, item, media_form=media_form, status=400)
    messages.success(
        request, f"{to_persian_digits(len(created))} رسانه به گالری اضافه شد."
    )
    return redirect(f"{reverse('portfolio:edit', kwargs={'pk': item.pk})}#media")


def _back_to_media(media: PortfolioMedia) -> HttpResponse:
    return redirect(f"{reverse('portfolio:edit', kwargs={'pk': media.item_id})}#media")


@login_required
@require_http_methods(["POST"])
def portfolio_media_cover(request: HttpRequest, pk: int) -> HttpResponse:
    media = _owned_media(_vendor_or_403(request), pk)
    try:
        set_cover(media=media)
    except ValidationError as exc:
        messages.error(request, " ".join(exc.messages))
        return _back_to_media(media)
    messages.success(request, "کاور نمونه‌کار عوض شد.")
    return _back_to_media(media)


@login_required
@require_http_methods(["POST"])
def portfolio_media_move(request: HttpRequest, pk: int, direction: str) -> HttpResponse:
    if direction not in ("up", "down"):
        raise Http404
    media = _owned_media(_vendor_or_403(request), pk)
    move_media(media=media, direction=direction)
    return _back_to_media(media)


@login_required
@require_http_methods(["POST"])
def portfolio_media_delete(request: HttpRequest, pk: int) -> HttpResponse:
    media = _owned_media(_vendor_or_403(request), pk)
    delete_media(media=media)
    messages.success(request, "رسانه از گالری حذف شد.")
    return _back_to_media(media)


@login_required
@require_http_methods(["POST"])
def portfolio_delete(request: HttpRequest, pk: int) -> HttpResponse:
    vendor = _vendor_or_403(request)
    item = get_object_or_404(PortfolioItem, pk=pk, vendor=vendor)
    delete_item(item=item)
    messages.success(request, "نمونه‌کار حذف شد.")
    return redirect("portfolio:manage")
