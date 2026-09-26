from __future__ import annotations

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import TimeStampedModel


class SubscriptionPlan(TimeStampedModel):
    code = models.SlugField(unique=True)
    title = models.CharField(max_length=100)
    monthly_price = models.PositiveIntegerField(default=0)
    lead_quota = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "subscription_plans"
        verbose_name = _("پلن اشتراک")
        verbose_name_plural = _("پلن‌های اشتراک")

    def __str__(self) -> str:
        return self.title


class VendorSubscription(TimeStampedModel):
    vendor = models.ForeignKey(
        "vendors.Vendor", on_delete=models.CASCADE, related_name="subscriptions"
    )
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "vendor_subscriptions"
        verbose_name = _("اشتراک تابلو‌ساز")
        verbose_name_plural = _("اشتراک‌های تابلو‌ساز")


class LeadPurchase(TimeStampedModel):
    vendor = models.ForeignKey(
        "vendors.Vendor", on_delete=models.CASCADE, related_name="lead_purchases"
    )
    request = models.ForeignKey(
        "requests.ProjectRequest",
        on_delete=models.CASCADE,
        related_name="lead_purchases",
    )
    amount = models.PositiveIntegerField(default=0)
    is_paid = models.BooleanField(default=False)

    class Meta:
        db_table = "lead_purchases"
        verbose_name = _("خرید لید")
        verbose_name_plural = _("خریدهای لید")


class FeaturedPlacement(TimeStampedModel):
    vendor = models.ForeignKey(
        "vendors.Vendor", on_delete=models.CASCADE, related_name="featured_placements"
    )
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "featured_placements"
        verbose_name = _("جایگاه ویژه")
        verbose_name_plural = _("جایگاه‌های ویژه")


class PriceEstimateConfig(TimeStampedModel):
    """Configurable pricing inputs for a future estimator.

    Not used for final quotes in the MVP.
    """

    service = models.ForeignKey(
        "catalog.Service",
        on_delete=models.CASCADE,
        related_name="price_configs",
    )
    base_price_per_sqm = models.PositiveIntegerField(default=0)
    lighting_multiplier = models.DecimalField(max_digits=4, decimal_places=2, default=1)
    city_multiplier = models.DecimalField(max_digits=4, decimal_places=2, default=1)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "price_estimate_configs"
        verbose_name = _("پیکربندی تخمین قیمت")
        verbose_name_plural = _("پیکربندی‌های تخمین قیمت")
