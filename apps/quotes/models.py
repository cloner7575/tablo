from __future__ import annotations

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import TimeStampedModel


class QuoteStatus(models.TextChoices):
    PENDING = "pending", _("در انتظار")
    VIEWED = "viewed", _("مشاهده‌شده")
    SHORTLISTED = "shortlisted", _("در لیست کوتاه")
    ACCEPTED = "accepted", _("پذیرفته‌شده")
    REJECTED = "rejected", _("رد شده")
    EXPIRED = "expired", _("منقضی")


class Quote(TimeStampedModel):
    request = models.ForeignKey(
        "requests.ProjectRequest",
        on_delete=models.CASCADE,
        related_name="quotes",
        verbose_name=_("درخواست"),
    )
    vendor = models.ForeignKey(
        "vendors.Vendor",
        on_delete=models.CASCADE,
        related_name="quotes",
        verbose_name=_("تابلو‌ساز"),
    )
    price = models.PositiveIntegerField(_("قیمت (تومان)"))
    estimated_delivery_days = models.PositiveSmallIntegerField(_("روز اجرا"))
    description = models.TextField(_("توضیحات"), blank=True)
    warranty = models.CharField(_("گارانتی"), max_length=120, blank=True)
    installation_cost = models.PositiveIntegerField(_("هزینه نصب"), default=0)
    material_details = models.TextField(_("جزئیات متریال"), blank=True)
    status = models.CharField(
        max_length=20,
        choices=QuoteStatus.choices,
        default=QuoteStatus.PENDING,
        db_index=True,
    )

    class Meta:
        db_table = "quotes"
        ordering = ["-created_at"]
        verbose_name = _("پیشنهاد قیمت")
        verbose_name_plural = _("پیشنهادهای قیمت")
        constraints = [
            models.UniqueConstraint(
                fields=["request", "vendor"],
                name="unique_quote_per_vendor_request",
            ),
        ]
        indexes = [
            models.Index(fields=["vendor", "status"]),
            models.Index(fields=["request", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.vendor} → {self.request} ({self.price})"
