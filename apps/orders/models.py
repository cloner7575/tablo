from __future__ import annotations

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import TimeStampedModel
from apps.common.validators import validate_uploaded_image


class OrderStatus(models.TextChoices):
    ACTIVE = "active", _("فعال")
    COMPLETED = "completed", _("تکمیل‌شده")
    CANCELLED = "cancelled", _("لغو شده")


class OrderStage(models.TextChoices):
    DETAILS = "details", _("بررسی محل و آماده‌کردن طرح")
    APPROVAL = "approval", _("منتظر تأیید طرح و قیمت شما")
    PRODUCTION = "production", _("در حال ساخت")
    INSTALLATION = "installation", _("هماهنگی نصب و تحویل")
    DELIVERED = "delivered", _("نصب انجام شده؛ منتظر تأیید تحویل")


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
    workflow_required = models.BooleanField(default=False)
    stage = models.CharField(
        _("مرحله اجرا"),
        max_length=20,
        choices=OrderStage.choices,
        default=OrderStage.DETAILS,
    )
    design_image = models.ImageField(
        _("تصویر طرح"),
        upload_to="orders/designs/",
        blank=True,
        validators=[validate_uploaded_image],
    )
    design_notes = models.TextField(_("توضیح طرح و زمان اجرا"), blank=True)
    materials = models.TextField(_("مشخصات و اقلام قیمت نهایی"), blank=True)
    proposed_price = models.PositiveIntegerField(
        _("هزینه ساخت نهایی"), null=True, blank=True
    )
    proposed_installation_cost = models.PositiveIntegerField(
        _("هزینه نصب نهایی"), null=True, blank=True
    )
    proposal_version = models.PositiveIntegerField(default=0)
    design_approved_at = models.DateTimeField(null=True, blank=True)
    revision_request = models.TextField(_("تغییرات درخواستی مشتری"), blank=True)

    @property
    def proposed_total(self) -> int | None:
        if self.proposed_price is None or self.proposed_installation_cost is None:
            return None
        return self.proposed_price + self.proposed_installation_cost

    class Meta:
        db_table = "orders"
        ordering = ["-created_at"]
        verbose_name = _("سفارش")
        verbose_name_plural = _("سفارش‌ها")

    def __str__(self) -> str:
        return f"Order #{self.pk}"
