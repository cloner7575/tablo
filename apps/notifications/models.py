from __future__ import annotations

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import TimeStampedModel


class NotificationChannel(models.TextChoices):
    SMS = "sms", "SMS"
    EMAIL = "email", "Email"
    WHATSAPP = "whatsapp", "WhatsApp"
    TELEGRAM = "telegram", "Telegram"
    CONSOLE = "console", "Console"


class NotificationLog(TimeStampedModel):
    event = models.CharField(max_length=64)
    channel = models.CharField(max_length=20, choices=NotificationChannel.choices)
    recipient = models.CharField(max_length=200)
    payload = models.JSONField(default=dict, blank=True)
    success = models.BooleanField(default=True)

    class Meta:
        db_table = "notification_logs"
        ordering = ["-created_at"]
        verbose_name = _("لاگ اعلان")
        verbose_name_plural = _("لاگ‌های اعلان")
