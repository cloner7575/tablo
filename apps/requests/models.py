from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import TimeStampedModel


class RequestStatus(models.TextChoices):
    DRAFT = "draft", _("پیش‌نویس")
    SUBMITTED = "submitted", _("ثبت‌شده")
    REVIEWING = "reviewing", _("در حال بررسی")
    RECEIVING_QUOTES = "receiving_quotes", _("دریافت پیشنهاد")
    QUOTED = "quoted", _("پیشنهاد دارد")
    NEGOTIATING = "negotiating", _("در حال مذاکره")
    ACCEPTED = "accepted", _("پذیرفته‌شده")
    COMPLETED = "completed", _("تکمیل‌شده")
    CANCELLED = "cancelled", _("لغو شده")


class LightingType(models.TextChoices):
    NONE = "none", _("بدون نور")
    LED = "led", _("LED")
    NEON = "neon", _("نئون")
    SMD = "smd", _("SMD")
    HIDDEN = "hidden", _("نور مخفی")


class ProjectRequest(TimeStampedModel):
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="project_requests",
        verbose_name=_("مشتری"),
        null=True,
        blank=True,
    )
    title = models.CharField(_("عنوان"), max_length=200, blank=True)
    description = models.TextField(_("توضیحات"), blank=True)
    service = models.ForeignKey(
        "catalog.Service",
        on_delete=models.PROTECT,
        related_name="project_requests",
        verbose_name=_("نوع تابلو"),
        null=True,
        blank=True,
    )
    city = models.ForeignKey(
        "locations.City",
        on_delete=models.PROTECT,
        related_name="project_requests",
        verbose_name=_("شهر"),
        null=True,
        blank=True,
    )
    district = models.CharField(_("محله"), max_length=120, blank=True)
    business_type = models.CharField(_("نوع کسب‌وکار"), max_length=120, blank=True)
    width_cm = models.PositiveIntegerField(_("عرض (سانتی‌متر)"), null=True, blank=True)
    height_cm = models.PositiveIntegerField(
        _("ارتفاع (سانتی‌متر)"), null=True, blank=True
    )
    material = models.CharField(_("متریال"), max_length=120, blank=True)
    lighting_type = models.CharField(
        _("نورپردازی"),
        max_length=20,
        choices=LightingType.choices,
        blank=True,
    )
    text_content = models.CharField(_("متن تابلو"), max_length=300, blank=True)
    budget_min = models.PositiveIntegerField(_("حداقل بودجه"), null=True, blank=True)
    budget_max = models.PositiveIntegerField(_("حداکثر بودجه"), null=True, blank=True)
    installation_required = models.BooleanField(_("نیاز به نصب"), default=True)
    installation_height = models.CharField(_("ارتفاع نصب"), max_length=80, blank=True)
    deadline = models.DateField(_("مهلت"), null=True, blank=True)
    image = models.ImageField(_("عکس محل"), upload_to="requests/", blank=True)
    status = models.CharField(
        max_length=32,
        choices=RequestStatus.choices,
        default=RequestStatus.DRAFT,
        db_index=True,
    )
    preferred_vendor = models.ForeignKey(
        "vendors.Vendor",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="preferred_requests",
        verbose_name=_("تابلو‌ساز ترجیحی"),
    )

    class Meta:
        db_table = "project_requests"
        ordering = ["-created_at"]
        verbose_name = _("درخواست پروژه")
        verbose_name_plural = _("درخواست‌های پروژه")
        indexes = [
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["city", "service", "status"]),
            models.Index(fields=["customer", "-created_at"]),
        ]

    def __str__(self) -> str:
        return self.title or f"Request #{self.pk}"

    @property
    def dimensions_display(self) -> str:
        if self.width_cm and self.height_cm:
            return f"{self.width_cm} × {self.height_cm} سانتی‌متر"
        return "—"
