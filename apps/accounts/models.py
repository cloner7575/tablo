from __future__ import annotations

import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.common.models import TimeStampedModel


class UserRole(models.TextChoices):
    CUSTOMER = "customer", _("مشتری")
    VENDOR = "vendor", _("تابلو‌ساز")
    ADMIN = "admin", _("مدیر")


class User(AbstractUser):
    """Project user. Keep AUTH_USER_MODEL pointing here."""

    phone = models.CharField(
        _("شماره موبایل"),
        max_length=15,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
    )
    role = models.CharField(
        _("نقش"),
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.CUSTOMER,
        db_index=True,
    )
    is_verified = models.BooleanField(_("تأیید شده"), default=False)

    class Meta:
        db_table = "users"
        verbose_name = _("کاربر")
        verbose_name_plural = _("کاربران")

    def __str__(self) -> str:
        return self.phone or self.get_username()

    @property
    def is_customer(self) -> bool:
        return self.role == UserRole.CUSTOMER

    @property
    def is_vendor_user(self) -> bool:
        return self.role == UserRole.VENDOR

    @property
    def display_name(self) -> str:
        full = self.get_full_name().strip()
        if full:
            return full
        return self.phone or self.username


class PhoneOTP(TimeStampedModel):
    """One-time password for phone authentication."""

    phone = models.CharField(_("شماره موبایل"), max_length=15, db_index=True)
    code = models.CharField(_("کد"), max_length=6)
    purpose = models.CharField(_("هدف"), max_length=32, default="login")
    is_used = models.BooleanField(default=False)
    attempts = models.PositiveSmallIntegerField(default=0)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = "phone_otps"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["phone", "purpose", "-created_at"]),
        ]
        verbose_name = _("کد یکبارمصرف")
        verbose_name_plural = _("کدهای یکبارمصرف")

    def __str__(self) -> str:
        return f"{self.phone} ({self.purpose})"

    @classmethod
    def generate_code(cls) -> str:
        return f"{secrets.randbelow(1_000_000):06d}"

    @classmethod
    def create_for_phone(
        cls,
        *,
        phone: str,
        purpose: str = "login",
        ttl_minutes: int | None = None,
    ) -> PhoneOTP:
        ttl = ttl_minutes or getattr(settings, "OTP_TTL_MINUTES", 5)
        return cls.objects.create(
            phone=phone,
            code=cls.generate_code(),
            purpose=purpose,
            expires_at=timezone.now() + timedelta(minutes=ttl),
        )

    @property
    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at

    def mark_used(self) -> None:
        self.is_used = True
        self.save(update_fields=["is_used", "updated_at"])
