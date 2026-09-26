from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import TimeStampedModel

MAX_REQUEST_IMAGES = 6


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
    UNSURE = "unsure", _("نمی‌دانم — تابلو‌ساز پیشنهاد دهد")
    NONE = "none", _("بدون نور / فقط روز")
    LED = "led", _("نور LED (رایج و کم‌مصرف)")
    NEON = "neon", _("نئون (جلوهٔ شبانه)")
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
    needs_guidance = models.BooleanField(
        _("نیاز به راهنمایی"),
        default=False,
        help_text=_("مشتری نوع تابلو یا جزئیات فنی را نمی‌داند"),
    )
    size_choice = models.CharField(
        _("اندازه تقریبی"),
        max_length=20,
        blank=True,
        help_text=_("small / medium / large / unsure"),
    )
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
        labels = {
            "small": "کوچک (حدود ۱ متر)",
            "medium": "متوسط (حدود ۲٫۵ متر)",
            "large": "بزرگ (حدود ۴ متر یا بیشتر)",
            "unsure": "هنوز مشخص نیست",
        }
        if self.size_choice == "unsure":
            return labels["unsure"]
        if self.width_cm and self.height_cm:
            base = f"{self.width_cm} × {self.height_cm} سانتی‌متر"
            preset = labels.get(self.size_choice)
            if preset and self.size_choice != "unsure":
                return f"{preset} — {base}"
            return base
        if self.size_choice in labels:
            return labels[self.size_choice]
        return "—"

    def photo_urls(self) -> list[str]:
        """Gallery URLs — RequestImage first, legacy single image as fallback."""
        urls = [item.image.url for item in self.images.all() if item.image]
        if urls:
            return urls
        if self.image:
            return [self.image.url]
        return []

    @property
    def photo_count(self) -> int:
        count = self.images.count() if self.pk else 0
        if count:
            return count
        return 1 if self.image else 0


class RequestImage(TimeStampedModel):
    request = models.ForeignKey(
        ProjectRequest,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name=_("درخواست"),
    )
    image = models.ImageField(_("تصویر"), upload_to="requests/gallery/")
    sort_order = models.PositiveSmallIntegerField(_("ترتیب"), default=0)
    caption = models.CharField(_("توضیح کوتاه"), max_length=120, blank=True)

    class Meta:
        db_table = "request_images"
        ordering = ["sort_order", "id"]
        verbose_name = _("عکس درخواست")
        verbose_name_plural = _("عکس‌های درخواست")

    def __str__(self) -> str:
        return f"RequestImage #{self.pk} ({self.request_id})"
