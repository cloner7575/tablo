from __future__ import annotations

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import TimeStampedModel


class OrderStatus(models.TextChoices):
    ACTIVE = "active", _("فعال")
    COMPLETED = "completed", _("تکمیل‌شده")
    CANCELLED = "cancelled", _("لغو شده")


class Order(TimeStampedModel):
    """Thin order created when a quote is accepted."""

    request = models.OneToOneField(
        "requests.ProjectRequest",
        on_delete=models.PROTECT,
        related_name="order",
        verbose_name=_("درخواست"),
    )
    quote = models.OneToOneField(
        "quotes.Quote",
        on_delete=models.PROTECT,
        related_name="order",
        verbose_name=_("پیشنهاد"),
    )
    customer = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="orders",
    )
    vendor = models.ForeignKey(
        "vendors.Vendor",
        on_delete=models.PROTECT,
        related_name="orders",
    )
    agreed_price = models.PositiveIntegerField(_("مبلغ توافقی"))
    status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.ACTIVE,
        db_index=True,
    )
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "orders"
        ordering = ["-created_at"]
        verbose_name = _("سفارش")
        verbose_name_plural = _("سفارش‌ها")

    def __str__(self) -> str:
        return f"Order #{self.pk}"
