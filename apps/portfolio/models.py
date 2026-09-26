from __future__ import annotations

from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from apps.common.models import TimeStampedModel


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
