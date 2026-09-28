"""Write workflows for portfolio items and their gallery media."""

from __future__ import annotations

import logging
from collections.abc import Iterable, Sequence
from typing import Literal

from django.core.exceptions import ValidationError
from django.core.files.storage import Storage
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
from django.db.models import Max
from django.db.models.fields.files import FieldFile
from django.utils.translation import gettext as _

from apps.portfolio.forms import max_media
from apps.portfolio.models import (
    MediaKind,
    PortfolioItem,
    PortfolioMedia,
    parse_aparat_hash,
)

logger = logging.getLogger(__name__)

Direction = Literal["up", "down"]


def _delete_files_on_commit(files: Iterable[FieldFile]) -> None:
    targets: list[tuple[Storage, str]] = [(f.storage, f.name) for f in files if f]

    def _delete() -> None:
        for storage, name in targets:
            storage.delete(name)
            logger.info("portfolio file deleted", extra={"file_name": name})

    if targets:
        transaction.on_commit(_delete, robust=True)


def _media_files(media: PortfolioMedia) -> list[FieldFile]:
    return [media.image, media.video, media.poster]


@transaction.atomic
def add_media(
    *,
    item: PortfolioItem,
    images: Sequence[UploadedFile] = (),
    video: UploadedFile | None = None,
    poster: UploadedFile | None = None,
    aparat_url: str = "",
    caption: str = "",
) -> list[PortfolioMedia]:
    """Append media to the end of the item's gallery, in the given order."""
    locked = PortfolioItem.objects.select_for_update().get(pk=item.pk)
    pending: list[PortfolioMedia] = [
        PortfolioMedia(item=locked, kind=MediaKind.IMAGE, image=image, caption=caption)
        for image in images
    ]
    if video:
        pending.append(
            PortfolioMedia(
                item=locked,
                kind=MediaKind.VIDEO,
                video=video,
                poster=poster or "",
                caption=caption,
            )
        )
    if aparat_url:
        pending.append(
            PortfolioMedia(
                item=locked,
                kind=MediaKind.APARAT,
                aparat_hash=parse_aparat_hash(aparat_url),
                caption=caption,
            )
        )
    if not pending:
        return []

    existing = locked.media.count()
    if existing + len(pending) > max_media():
        raise ValidationError(
            _("سقف رسانه‌های این نمونه‌کار پر شده است."), code="media_limit"
        )

    last = locked.media.aggregate(last=Max("sort_order"))["last"]
    next_order = 0 if last is None else last + 1
    for offset, media in enumerate(pending):
        media.sort_order = next_order + offset
        media.save()
    return pending


@transaction.atomic
def create_item(
    *,
    item: PortfolioItem,
    gallery: Sequence[UploadedFile] = (),
    video: UploadedFile | None = None,
    poster: UploadedFile | None = None,
    aparat_url: str = "",
) -> PortfolioItem:
    """Save a new item (vendor already set) together with its first gallery media."""
    item.save()
    add_media(
        item=item, images=gallery, video=video, poster=poster, aparat_url=aparat_url
    )
    return item


@transaction.atomic
def set_cover(*, media: PortfolioMedia) -> None:
    """Make a gallery image the cover; the old cover takes its gallery slot."""
    if media.kind != MediaKind.IMAGE:
        raise ValidationError(_("فقط عکس می‌تواند کاور باشد."), code="cover_kind")
    item = PortfolioItem.objects.select_for_update().get(pk=media.item_id)
    new_cover = media.image.name
    if not item.image:
        item.image.name = new_cover
        item.save(update_fields=["image", "updated_at"])
        media.delete()
        return
    media.image.name, item.image.name = item.image.name, new_cover
    item.save(update_fields=["image", "updated_at"])
    media.save(update_fields=["image", "updated_at"])


@transaction.atomic
def move_media(*, media: PortfolioMedia, direction: Direction) -> None:
    """Swap the media with its neighbour and renumber the gallery densely."""
    PortfolioItem.objects.select_for_update().get(pk=media.item_id)
    ordered = list(PortfolioMedia.objects.filter(item_id=media.item_id))
    index = next(i for i, m in enumerate(ordered) if m.pk == media.pk)
    target = index - 1 if direction == "up" else index + 1
    if target < 0 or target >= len(ordered):
        return
    ordered[index], ordered[target] = ordered[target], ordered[index]
    for position, row in enumerate(ordered):
        row.sort_order = position
    PortfolioMedia.objects.bulk_update(ordered, ["sort_order"])


@transaction.atomic
def delete_media(*, media: PortfolioMedia) -> None:
    files = _media_files(media)
    media.delete()
    _delete_files_on_commit(files)


@transaction.atomic
def delete_item(*, item: PortfolioItem) -> None:
    files: list[FieldFile] = [item.image]
    for media in item.media.all():
        files.extend(_media_files(media))
    item.delete()
    _delete_files_on_commit(files)
