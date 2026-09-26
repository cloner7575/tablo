from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from apps.common.models import TimeStampedModel


class VerificationStatus(models.TextChoices):
    PENDING = "pending", _("در انتظار تأیید")
    APPROVED = "approved", _("تأیید شده")
    SUSPENDED = "suspended", _("معلق")


class Vendor(TimeStampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="vendor_profile",
        verbose_name=_("کاربر"),
    )
    business_name = models.CharField(_("نام کسب‌وکار"), max_length=200)
    slug = models.SlugField(_("اسلاگ"), max_length=220, unique=True, allow_unicode=True)
    description = models.TextField(_("توضیحات"), blank=True)
    phone = models.CharField(_("تلفن"), max_length=20, blank=True)
    city = models.ForeignKey(
        "locations.City",
        on_delete=models.PROTECT,
        related_name="vendors",
        verbose_name=_("شهر"),
    )
    address = models.CharField(_("آدرس"), max_length=400, blank=True)
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    logo = models.ImageField(upload_to="vendors/logos/", blank=True)
    cover_image = models.ImageField(upload_to="vendors/covers/", blank=True)
    website = models.URLField(blank=True)
    instagram = models.CharField(max_length=120, blank=True)
    years_of_experience = models.PositiveSmallIntegerField(default=0)
    verification_status = models.CharField(
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING,
        db_index=True,
    )
    rating = models.DecimalField(
        max_digits=3, decimal_places=2, default=Decimal("0.00")
    )
    review_count = models.PositiveIntegerField(default=0)
    completed_projects = models.PositiveIntegerField(default=0)
    response_time_hours = models.PositiveIntegerField(
        default=24, help_text=_("میانگین زمان پاسخ به ساعت")
    )
    services = models.ManyToManyField(
        "catalog.Service",
        related_name="vendors",
        blank=True,
        verbose_name=_("خدمات"),
    )
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)

    class Meta:
        db_table = "vendors"
        ordering = ["-is_featured", "-rating", "business_name"]
        verbose_name = _("تابلو‌ساز")
        verbose_name_plural = _("تابلو‌سازها")
        indexes = [
            models.Index(fields=["verification_status", "is_active"]),
            models.Index(fields=["city", "is_active"]),
        ]

    def __str__(self) -> str:
        return self.business_name

    def save(self, *args: object, **kwargs: object) -> None:
        if not self.slug:
            base = slugify(self.business_name, allow_unicode=True) or "vendor"
            candidate = base
            n = 1
            while Vendor.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
                n += 1
                candidate = f"{base}-{n}"
            self.slug = candidate
        super().save(*args, **kwargs)

    @property
    def is_approved(self) -> bool:
        return (
            self.verification_status == VerificationStatus.APPROVED and self.is_active
        )
