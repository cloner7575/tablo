"""Read-side helpers for portfolio pages."""

from __future__ import annotations

import mimetypes
from dataclasses import dataclass

from django.db.models import Count, Prefetch, Q, QuerySet
from django.templatetags.static import static

from apps.common.daylight_images import SCENE_SOURCES
from apps.portfolio.demo import demo_image_path
from apps.portfolio.models import (
    TIME_IMAGE_FIELDS,
    MediaKind,
    PortfolioItem,
    PortfolioMedia,
)
from apps.vendors.models import Vendor, VerificationStatus

VIDEO_KINDS = (MediaKind.VIDEO, MediaKind.APARAT)


@dataclass(frozen=True, slots=True)
class Slide:
    """One gallery entry, already resolved to URLs the template can print."""

    kind: str
    src: str
    href: str
    thumb: str
    caption: str
    mime: str = ""
    is_cover: bool = False

    @property
    def is_video(self) -> bool:
        return self.kind in VIDEO_KINDS


def published_items() -> QuerySet[PortfolioItem]:
    """Prioritize complete clock previews before applying limits or pagination."""
    uploaded = Q()
    for field in TIME_IMAGE_FIELDS:
        uploaded &= ~Q(**{field: ''})
    bundled_references = [
        source.replace('img/references/', 'industry/references/', 1)
        for source in SCENE_SOURCES
        if source.startswith('img/references/')
    ]
    # Covers without uploads use a registered four-exposure demo scene.
    complete = uploaded | Q(image__in=bundled_references) | Q(image='')
    return (
        PortfolioItem.objects.filter(is_published=True)
        .alias(has_complete_time_images=complete)
        .order_by('-has_complete_time_images', '-created_at', '-pk')
    )


def detail_queryset() -> QuerySet[PortfolioItem]:
    return (
        published_items()
        .select_related("vendor", "vendor__city", "service", "city")
        .prefetch_related(Prefetch("media", queryset=PortfolioMedia.objects.all()))
    )


def with_media_counts(qs: QuerySet[PortfolioItem]) -> QuerySet[PortfolioItem]:
    return qs.annotate(
        image_count=Count("media", filter=Q(media__kind=MediaKind.IMAGE)),
        video_count=Count("media", filter=Q(media__kind__in=VIDEO_KINDS)),
    )


def vendor_items(
    vendor: Vendor, *, status: str = "all", query: str = ""
) -> QuerySet[PortfolioItem]:
    qs = vendor.portfolio_items.select_related("service", "city")
    if status == "published":
        qs = qs.filter(is_published=True)
    elif status == "draft":
        qs = qs.filter(is_published=False)
    if query:
        qs = qs.filter(title__icontains=query)
    return with_media_counts(qs).order_by("-created_at")


def vendor_item_counts(vendor: Vendor) -> dict[str, int]:
    counts = vendor.portfolio_items.aggregate(
        all=Count("pk"),
        published=Count("pk", filter=Q(is_published=True)),
    )
    return {
        "all": counts["all"],
        "published": counts["published"],
        "draft": counts["all"] - counts["published"],
    }


def _media_slide(media: PortfolioMedia) -> Slide:
    if media.kind == MediaKind.VIDEO:
        mime = mimetypes.guess_type(media.video.name)[0] or "video/mp4"
        return Slide(
            kind=media.kind,
            src=media.video.url,
            href=media.video.url,
            thumb=media.poster.url if media.poster else "",
            caption=media.caption,
            mime=mime,
        )
    if media.kind == MediaKind.APARAT:
        return Slide(
            kind=media.kind,
            src=media.embed_url,
            href=media.page_url,
            thumb="",
            caption=media.caption,
        )
    return Slide(
        kind=media.kind,
        src=media.image.url,
        href=media.image.url,
        thumb=media.image.url,
        caption=media.caption,
    )


def portfolio_slides(item: PortfolioItem) -> list[Slide]:
    """Cover first, then gallery media in vendor order; demo art if nothing exists.

    Expects ``item.media`` to be prefetched.
    """
    slides: list[Slide] = []
    if item.image or any(getattr(item, name) for name in TIME_IMAGE_FIELDS):
        url = item.image.url if item.image else static(demo_image_path(item))
        slides.append(
            Slide(
                kind=MediaKind.IMAGE,
                src=url,
                href=url,
                thumb=url,
                caption=item.title,
                is_cover=True,
            )
        )
    slides.extend(_media_slide(media) for media in item.media.all())
    if slides:
        return slides
    url = static(demo_image_path(item))
    return [
        Slide(
            kind=MediaKind.IMAGE,
            src=url,
            href=url,
            thumb=url,
            caption=item.title,
            is_cover=True,
        )
    ]


def discoverable_items() -> QuerySet[PortfolioItem]:
    return (
        published_items()
        .filter(
            Q(
                vendor__is_active=True,
                vendor__verification_status=VerificationStatus.APPROVED,
            )
            | (
                Q(vendor__isnull=True)
                & ~Q(source_name="")
                & ~Q(source_url="")
                & ~Q(image="")
            )
        )
        .select_related("vendor", "service", "city")
    )
