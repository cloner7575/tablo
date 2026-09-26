from __future__ import annotations

import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.analytics.services import track
from apps.chat.models import Conversation, ConversationStatus, Message
from apps.chat.selectors import conversation_group_name, user_can_access_quote
from apps.notifications.services import NotificationEvent, notify
from apps.quotes.models import Quote, QuoteStatus
from apps.requests.models import RequestStatus

logger = logging.getLogger(__name__)

MAX_BODY_LENGTH = 4000


class ChatError(ValidationError):
    """Domain validation for chat operations."""


def serialize_message(message: Message) -> dict[str, object]:
    image_url = ""
    if message.image:
        image_url = message.image.url
    return {
        "id": message.pk,
        "body": message.body,
        "image_url": image_url,
        "sender_id": message.sender_id,
        "created_at": message.created_at.isoformat(),
        "read_at": message.read_at.isoformat() if message.read_at else None,
    }


def _broadcast(quote_id: int, payload: dict[str, object]) -> None:
    channel_layer = get_channel_layer()
    if channel_layer is None:
        logger.warning("No channel layer configured; skip chat broadcast")
        return
    async_to_sync(channel_layer.group_send)(
        conversation_group_name(quote_id),
        {"type": "chat.event", "payload": payload},
    )


def _schedule_broadcast(quote_id: int, payload: dict[str, object]) -> None:
    transaction.on_commit(lambda: _broadcast(quote_id, payload))


def _mark_negotiating(*, quote: Quote) -> None:
    changed = False
    if quote.status in {QuoteStatus.PENDING, QuoteStatus.VIEWED}:
        quote.status = QuoteStatus.SHORTLISTED
        quote.save(update_fields=["status", "updated_at"])
        changed = True

    project_request = quote.request
    if project_request.status in {
        RequestStatus.SUBMITTED,
        RequestStatus.REVIEWING,
        RequestStatus.RECEIVING_QUOTES,
        RequestStatus.QUOTED,
    }:
        project_request.status = RequestStatus.NEGOTIATING
        project_request.save(update_fields=["status", "updated_at"])
        changed = True

    if changed:
        track(
            "chat_negotiation_started",
            {"quote_id": quote.pk, "request_id": project_request.pk},
        )


@transaction.atomic
def get_or_open_conversation(*, quote: Quote, user) -> Conversation:
    """Open chat for a quote.

    Only the customer may start a conversation. Vendors may join an existing
    thread after the customer has opened it.
    """
    if not user_can_access_quote(quote=quote, user=user):
        raise PermissionDenied(_("دسترسی به این گفتگو مجاز نیست."))

    conversation = (
        Conversation.objects.select_related("quote__request", "quote__vendor")
        .filter(quote=quote)
        .first()
    )
    if conversation is not None:
        if conversation.status == ConversationStatus.OPEN:
            _mark_negotiating(quote=quote)
        return conversation

    is_customer = quote.request.customer_id == user.id
    if not is_customer:
        raise ChatError(_("گفتگو هنوز توسط مشتری شروع نشده است."))

    conversation = Conversation.objects.create(quote=quote)
    _mark_negotiating(quote=quote)
    track("chat_opened", {"quote_id": quote.pk, "user_id": user.pk})
    return conversation


@transaction.atomic
def send_message(
    *,
    quote: Quote,
    user,
    body: str = "",
    image: UploadedFile | None = None,
) -> Message:
    conversation = get_or_open_conversation(quote=quote, user=user)

    if conversation.status == ConversationStatus.CLOSED:
        raise ChatError(_("این گفتگو بسته شده و فقط قابل مشاهده است."))

    if quote.status in {QuoteStatus.REJECTED, QuoteStatus.EXPIRED}:
        conversation.status = ConversationStatus.CLOSED
        conversation.save(update_fields=["status", "updated_at"])
        raise ChatError(_("این پیشنهاد دیگر فعال نیست."))

    text = (body or "").strip()
    if not text and image is None:
        raise ChatError(_("پیام خالی ارسال نکنید."))
    if len(text) > MAX_BODY_LENGTH:
        raise ChatError(_("پیام بیش از حد طولانی است."))

    message = Message(
        conversation=conversation,
        sender=user,
        body=text,
    )
    if image is not None:
        message.image = image
    message.save()
    conversation.last_message_at = message.created_at
    conversation.save(update_fields=["last_message_at", "updated_at"])

    recipient = _notify_recipient(quote=quote, sender=user)
    if recipient:
        notify(
            event=NotificationEvent.NEW_CHAT_MESSAGE,
            recipient=recipient,
            context={
                "quote_id": quote.pk,
                "message_id": message.pk,
                "conversation_id": conversation.pk,
            },
        )

    track(
        "chat_message_sent",
        {"quote_id": quote.pk, "message_id": message.pk, "user_id": user.pk},
    )

    _schedule_broadcast(
        quote.pk,
        {"type": "message.new", "message": serialize_message(message)},
    )
    return message


def _notify_recipient(*, quote: Quote, sender) -> str:
    if quote.request.customer_id == sender.id:
        vendor = quote.vendor
        return vendor.phone or vendor.user.phone or str(vendor.user_id)
    customer = quote.request.customer
    if customer is None:
        return ""
    return customer.phone or str(customer.pk)


@transaction.atomic
def mark_read(*, conversation: Conversation, user) -> int:
    if not user_can_access_quote(quote=conversation.quote, user=user):
        raise PermissionDenied

    now = timezone.now()
    updated = (
        conversation.messages.filter(read_at__isnull=True)
        .exclude(sender=user)
        .update(read_at=now)
    )
    if updated:
        _schedule_broadcast(
            conversation.quote_id,
            {
                "type": "message.read",
                "reader_id": user.pk,
                "read_at": now.isoformat(),
            },
        )
    return updated


@transaction.atomic
def close_losing_conversations(*, winning_quote: Quote) -> int:
    """Close chat threads for sibling quotes rejected when one is accepted."""
    losers = Conversation.objects.filter(
        quote__request_id=winning_quote.request_id,
        status=ConversationStatus.OPEN,
    ).exclude(quote_id=winning_quote.pk)

    closed_ids = list(losers.values_list("quote_id", flat=True))
    count = losers.update(status=ConversationStatus.CLOSED)
    for quote_id in closed_ids:
        _schedule_broadcast(quote_id, {"type": "conversation.closed"})
    return count


@transaction.atomic
def close_conversation_for_quote(*, quote: Quote) -> Conversation | None:
    conversation = Conversation.objects.filter(quote=quote).first()
    if conversation is None:
        return None
    if conversation.status != ConversationStatus.CLOSED:
        conversation.status = ConversationStatus.CLOSED
        conversation.save(update_fields=["status", "updated_at"])
        _schedule_broadcast(quote.pk, {"type": "conversation.closed"})
    return conversation
