from __future__ import annotations

import re
from urllib.parse import urlsplit

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from apps.common.models import TimeStampedModel

APARAT_HOSTS = frozenset({"aparat.com", "www.aparat.com", "m.aparat.com"})
APARAT_PATHS = (
    re.compile(r"^/v/(?P<hash>[A-Za-z0-9]{3,32})/?$"),
    re.compile(r"^/video/video/embed/videohash/(?P<hash>[A-Za-z0-9]{3,32})(?:/.*)?$"),
)
APARAT_EMBED_URL = "https://www.aparat.com/video/video/embed/videohash/{hash}/vt/frame"
APARAT_PAGE_URL = "https://www.aparat.com/v/{hash}"


def parse_aparat_hash(url: str) -> str:
    """Return the video hash of an Aparat page or embed link."""
    invalid = ValidationError(
        _("لینک آپارات معتبر نیست. نمونه: https://www.aparat.com/v/abc123"),
        code="invalid_aparat",
    )
    parts = urlsplit((url or "").strip())
    if parts.scheme not in {"http", "https"}:
        raise invalid
    if (parts.hostname or "").lower() not in APARAT_HOSTS:
        raise invalid
    for pattern in APARAT_PATHS:
        match = pattern.match(parts.path)
        if match:
            return match.group("hash")
    raise invalid


class PortfolioItem(TimeStampedModel):
    vendor = models.ForeignKey(
        "vendors.Vendor",
        on_delete=models.CASCADE,
        related_name="portfolio_items",
        verbose_name=_("تابلو‌ساز"),
    )
    title = models.CharField(_("عنوان"), max_length=200)
    slug = models.SlugField(_("اسلاگ"), max_length=220, unique=True, allow_unicode=True)
    description = models.TextField(_("توضیحات"), blank=True)
    service = models.ForeignKey(
        "catalog.Service",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="portfolio_items",
    )
    city = models.ForeignKey(
        "locations.City",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="portfolio_items",
    )
    image = models.ImageField(_("تصویر"), upload_to="portfolio/", blank=True)
    is_published = models.BooleanField(default=True)

    class Meta:
        db_table = "portfolio_items"
        ordering = ["-created_at"]
        verbose_name = _("نمونه‌کار")
        verbose_name_plural = _("نمونه‌کارها")
        indexes = [
            models.Index(fields=["vendor", "is_published"]),
            models.Index(fields=["slug"]),
        ]

    def __str__(self) -> str:
        return self.title

    def save(self, *args: object, **kwargs: object) -> None:
        if not self.slug:
            base = slugify(self.title, allow_unicode=True) or "portfolio"
            candidate = base
            n = 1
            while (
                PortfolioItem.objects.filter(slug=candidate)
                .exclude(pk=self.pk)
                .exists()
            ):
                n += 1
                candidate = f"{base}-{n}"
            self.slug = candidate
        super().save(*args, **kwargs)


class MediaKind(models.TextChoices):
    IMAGE = "image", _("عکس")
    VIDEO = "video", _("ویدیو")
    APARAT = "aparat", _("ویدیوی آپارات")


class PortfolioMedia(TimeStampedModel):
    """Extra gallery media; the item's own ``image`` stays the cover."""

    item = models.ForeignKey(
        PortfolioItem,
        on_delete=models.CASCADE,
        related_name="media",
        verbose_name=_("نمونه‌کار"),
    )
    kind = models.CharField(
        _("نوع"), max_length=10, choices=MediaKind.choices, default=MediaKind.IMAGE
    )
    image = models.ImageField(_("عکس"), upload_to="portfolio/gallery/", blank=True)
    video = models.FileField(_("ویدیو"), upload_to="portfolio/videos/", blank=True)
    poster = models.ImageField(
        _("تصویر پیش‌نمایش ویدیو"), upload_to="portfolio/posters/", blank=True
    )
    aparat_hash = models.CharField(_("شناسه آپارات"), max_length=32, blank=True)
    caption = models.CharField(_("توضیح کوتاه"), max_length=160, blank=True)
    sort_order = models.PositiveSmallIntegerField(_("ترتیب"), default=0)

    class Meta:
        db_table = "portfolio_media"
        ordering = ["sort_order", "id"]
        verbose_name = _("رسانه نمونه‌کار")
        verbose_name_plural = _("رسانه‌های نمونه‌کار")
        constraints = [
            models.CheckConstraint(
                condition=(
                    (Q(kind=MediaKind.IMAGE) & ~Q(image=""))
                    | (Q(kind=MediaKind.VIDEO) & ~Q(video=""))
                    | (Q(kind=MediaKind.APARAT) & ~Q(aparat_hash=""))
                ),
                name="portfolio_media_kind_has_source",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.get_kind_display()} #{self.pk} ({self.item_id})"

    @property
    def embed_url(self) -> str:
        if self.kind != MediaKind.APARAT:
            return ""
        return APARAT_EMBED_URL.format(hash=self.aparat_hash)

    @property
    def page_url(self) -> str:
        if self.kind != MediaKind.APARAT:
            return ""
        return APARAT_PAGE_URL.format(hash=self.aparat_hash)
