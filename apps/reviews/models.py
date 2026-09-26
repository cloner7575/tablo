from __future__ import annotations

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import TimeStampedModel


class Review(TimeStampedModel):
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reviews_written",
        verbose_name=_("مشتری"),
    )
    vendor = models.ForeignKey(
        "vendors.Vendor",
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name=_("تابلو‌ساز"),
    )
    request = models.OneToOneField(
        "requests.ProjectRequest",
        on_delete=models.CASCADE,
        related_name="review",
        verbose_name=_("درخواست"),
    )
    rating = models.PositiveSmallIntegerField(
        _("امتیاز"),
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    comment = models.TextField(_("نظر"), blank=True)
    is_published = models.BooleanField(default=True)

    class Meta:
        db_table = "reviews"
        ordering = ["-created_at"]
        verbose_name = _("نظر")
        verbose_name_plural = _("نظرات")
        indexes = [
            models.Index(fields=["vendor", "is_published"]),
        ]

    def __str__(self) -> str:
        return f"{self.vendor} — {self.rating}"
