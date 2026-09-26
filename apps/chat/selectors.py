from __future__ import annotations

from django.db.models import Count, OuterRef, Q, QuerySet, Subquery

from apps.chat.models import Conversation, Message
from apps.quotes.models import Quote


def conversation_group_name(quote_id: int) -> str:
    return f"chat_quote_{quote_id}"


def user_can_access_quote(*, quote: Quote, user) -> bool:
    if not user.is_authenticated:
        return False
    if user.is_staff:
        return True
    if quote.request.customer_id == user.id:
        return True
    vendor = getattr(user, "vendor_profile", None)
    return bool(vendor and quote.vendor_id == vendor.pk)


def _last_message_subquery() -> Subquery:
    return Subquery(
        Message.objects.filter(conversation_id=OuterRef("pk"))
        .order_by("-created_at")
        .values("body")[:1]
    )


def conversations_for_customer(*, user) -> QuerySet[Conversation]:
    return (
        Conversation.objects.filter(quote__request__customer=user)
        .select_related(
            "quote__vendor",
            "quote__request",
            "quote__request__service",
            "quote__request__city",
        )
        .annotate(
            unread_count=Count(
                "messages",
                filter=Q(messages__read_at__isnull=True) & ~Q(messages__sender=user),
            ),
            last_body=_last_message_subquery(),
        )
        .order_by("-last_message_at", "-created_at")
    )


def conversations_for_vendor(*, vendor) -> QuerySet[Conversation]:
    return (
        Conversation.objects.filter(quote__vendor=vendor)
        .select_related(
            "quote__request",
            "quote__request__customer",
            "quote__request__service",
            "quote__request__city",
            "quote__vendor",
        )
        .annotate(
            unread_count=Count(
                "messages",
                filter=Q(messages__read_at__isnull=True)
                & ~Q(messages__sender=vendor.user_id),
            ),
            last_body=_last_message_subquery(),
        )
        .order_by("-last_message_at", "-created_at")
    )


def messages_for_conversation(*, conversation: Conversation) -> QuerySet[Message]:
    return conversation.messages.select_related("sender").order_by("created_at")


def unread_chat_count_for_vendor(*, vendor) -> int:
    return (
        Message.objects.filter(
            conversation__quote__vendor=vendor,
            read_at__isnull=True,
        )
        .exclude(sender_id=vendor.user_id)
        .count()
    )


def unread_chat_count_for_customer(*, user) -> int:
    return (
        Message.objects.filter(
            conversation__quote__request__customer=user,
            read_at__isnull=True,
        )
        .exclude(sender=user)
        .count()
    )
