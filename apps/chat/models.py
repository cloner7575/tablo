from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import TimeStampedModel


class ConversationStatus(models.TextChoices):
    OPEN = "open", _("باز")
    CLOSED = "closed", _("بسته")


class Conversation(TimeStampedModel):
    quote = models.OneToOneField(
        "quotes.Quote",
        on_delete=models.CASCADE,
        related_name="conversation",
        verbose_name=_("پیشنهاد"),
    )
    status = models.CharField(
        max_length=20,
        choices=ConversationStatus.choices,
        default=ConversationStatus.OPEN,
        db_index=True,
    )
    last_message_at = models.DateTimeField(
        _("آخرین پیام"),
        null=True,
        blank=True,
        db_index=True,
    )

    class Meta:
        db_table = "chat_conversations"
        ordering = ["-last_message_at", "-created_at"]
        verbose_name = _("گفتگو")
        verbose_name_plural = _("گفتگوها")

    def __str__(self) -> str:
        return f"Conversation quote={self.quote_id} ({self.status})"

    @property
    def is_open(self) -> bool:
        return self.status == ConversationStatus.OPEN


class Message(TimeStampedModel):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
        verbose_name=_("گفتگو"),
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_messages",
        verbose_name=_("فرستنده"),
    )
    body = models.TextField(_("متن"), blank=True)
    image = models.ImageField(
        _("تصویر"),
        upload_to="chat/",
        blank=True,
    )
    read_at = models.DateTimeField(_("خوانده‌شده در"), null=True, blank=True)

    class Meta:
        db_table = "chat_messages"
        ordering = ["created_at"]
        verbose_name = _("پیام")
        verbose_name_plural = _("پیام‌ها")
        indexes = [
            models.Index(fields=["conversation", "created_at"]),
            models.Index(fields=["conversation", "read_at"]),
        ]

    def __str__(self) -> str:
        return f"Message #{self.pk} in conversation {self.conversation_id}"
