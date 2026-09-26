from __future__ import annotations

from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from apps.common.models import TimeStampedModel


class Service(TimeStampedModel):
    title = models.CharField(_("عنوان"), max_length=120)
    slug = models.SlugField(_("اسلاگ"), max_length=140, unique=True, allow_unicode=True)
    description = models.TextField(_("توضیحات"), blank=True)
    icon = models.ImageField(_("آیکون"), upload_to="services/icons/", blank=True)
    is_active = models.BooleanField(_("فعال"), default=True)
    sort_order = models.PositiveIntegerField(_("ترتیب"), default=0)

    class Meta:
        db_table = "services"
        ordering = ["sort_order", "title"]
        verbose_name = _("خدمت")
        verbose_name_plural = _("خدمات")
        indexes = [
            models.Index(fields=["is_active", "sort_order"]),
        ]

    def __str__(self) -> str:
        return self.title

    def save(self, *args: object, **kwargs: object) -> None:
        if not self.slug:
            self.slug = slugify(self.title, allow_unicode=True)
        super().save(*args, **kwargs)


class CityServicePage(TimeStampedModel):
    """SEO landing for city+service — only when real content exists."""

    city = models.ForeignKey(
        "locations.City",
        on_delete=models.CASCADE,
        related_name="service_pages",
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name="city_pages",
    )
    title = models.CharField(_("عنوان"), max_length=200)
    slug = models.SlugField(_("اسلاگ"), max_length=160, allow_unicode=True)
    body = models.TextField(_("محتوا"))
    meta_description = models.CharField(_("متا"), max_length=300, blank=True)
    is_published = models.BooleanField(_("منتشر شده"), default=False)

    class Meta:
        db_table = "city_service_pages"
        unique_together = [("city", "service")]
        verbose_name = _("صفحه شهر/خدمت")
        verbose_name_plural = _("صفحات شهر/خدمت")

    def __str__(self) -> str:
        return self.title
