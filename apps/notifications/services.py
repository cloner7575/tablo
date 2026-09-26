from __future__ import annotations

import logging
from typing import Protocol

from django.conf import settings
from django.db import transaction

from apps.notifications.models import NotificationChannel, NotificationLog

logger = logging.getLogger(__name__)


class NotificationEvent:
    REQUEST_CREATED = "RequestCreated"
    QUOTE_RECEIVED = "QuoteReceived"
    QUOTE_ACCEPTED = "QuoteAccepted"
    PROJECT_COMPLETED = "ProjectCompleted"
    REVIEW_REQUESTED = "ReviewRequested"
    NEW_CHAT_MESSAGE = "NewChatMessage"


class NotificationProvider(Protocol):
    channel: str

    def send(
        self, *, recipient: str, event: str, context: dict[str, object]
    ) -> None: ...


class ConsoleNotificationProvider:
    channel = NotificationChannel.CONSOLE

    def send(self, *, recipient: str, event: str, context: dict[str, object]) -> None:
        logger.info(
            "Notify [%s] → %s | %s | %s", self.channel, recipient, event, context
        )
        print(f"[NOTIFY:{self.channel}] {event} → {recipient} {context}")


def get_notification_providers() -> list[NotificationProvider]:
    return [ConsoleNotificationProvider()]


def notify(
    *, event: str, recipient: str, context: dict[str, object] | None = None
) -> None:
    ctx = context or {}

    def _send() -> None:
        for provider in get_notification_providers():
            try:
                provider.send(recipient=recipient, event=event, context=ctx)
                NotificationLog.objects.create(
                    event=event,
                    channel=provider.channel,
                    recipient=recipient,
                    payload=ctx,
                    success=True,
                )
            except Exception:
                logger.exception(
                    "Notification failed event=%s recipient=%s", event, recipient
                )
                NotificationLog.objects.create(
                    event=event,
                    channel=getattr(provider, "channel", "unknown"),
                    recipient=recipient,
                    payload=ctx,
                    success=False,
                )
                if not getattr(settings, "NOTIFICATIONS_SWALLOW_ERRORS", True):
                    raise

    transaction.on_commit(_send)
