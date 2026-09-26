from __future__ import annotations

import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from apps.accounts.models import UserRole
from apps.chat.forms import ChatImageUploadForm
from apps.chat.selectors import (
    conversations_for_customer,
    conversations_for_vendor,
    messages_for_conversation,
    user_can_access_quote,
)
from apps.chat.services import (
    ChatError,
    get_or_open_conversation,
    mark_read,
    send_message,
)
from apps.quotes.models import Quote
from apps.vendors.panel import panel_context

logger = logging.getLogger(__name__)


def _require_vendor(request: HttpRequest):
    vendor = getattr(request.user, "vendor_profile", None)
    if vendor is None:
        raise PermissionDenied
    return vendor


@login_required
@require_http_methods(["GET"])
def inbox(request: HttpRequest) -> HttpResponse:
    vendor = getattr(request.user, "vendor_profile", None)
    if vendor is not None and request.user.role == UserRole.VENDOR:
        return redirect("vendors:chats")

    conversations = list(conversations_for_customer(user=request.user)[:50])
    return render(
        request,
        "pages/chat/inbox.html",
        {
            "conversations": conversations,
            "role": "customer",
        },
    )


@login_required
@require_http_methods(["GET"])
def vendor_inbox(request: HttpRequest) -> HttpResponse:
    vendor = _require_vendor(request)
    conversations = list(conversations_for_vendor(vendor=vendor)[:50])
    return render(
        request,
        "pages/chat/inbox.html",
        panel_context(
            vendor,
            "chats",
            conversations=conversations,
            role="vendor",
        ),
    )


@login_required
@require_http_methods(["GET", "POST"])
def thread(request: HttpRequest, quote_id: int) -> HttpResponse:
    quote = get_object_or_404(
        Quote.objects.select_related(
            "request",
            "request__customer",
            "request__service",
            "request__city",
            "vendor",
            "vendor__user",
            "vendor__city",
        ),
        pk=quote_id,
    )
    if not user_can_access_quote(quote=quote, user=request.user):
        return HttpResponseForbidden("دسترسی مجاز نیست.")

    vendor = getattr(request.user, "vendor_profile", None)
    is_vendor = bool(vendor and quote.vendor_id == vendor.pk)
    is_customer = quote.request.customer_id == request.user.id

    try:
        conversation = get_or_open_conversation(quote=quote, user=request.user)
    except ChatError as exc:
        messages.warning(request, str(exc))
        if is_vendor:
            return redirect("vendors:my_quotes")
        return redirect("chat:inbox")
    except PermissionDenied:
        return HttpResponseForbidden("دسترسی مجاز نیست.")

    if request.method == "POST":
        # Fallback non-WS text send (progressive enhancement).
        body = (request.POST.get("body") or "").strip()
        try:
            send_message(quote=quote, user=request.user, body=body)
        except (ChatError, ValidationError) as exc:
            messages.error(request, str(exc))
        return redirect("chat:thread", quote_id=quote.pk)

    mark_read(conversation=conversation, user=request.user)
    chat_messages = list(messages_for_conversation(conversation=conversation))

    context = {
        "quote": quote,
        "conversation": conversation,
        "chat_messages": chat_messages,
        "is_vendor": is_vendor,
        "is_customer": is_customer,
        "ws_path": f"/ws/chat/{quote.pk}/",
        "upload_url": f"/chats/{quote.pk}/upload/",
        "can_send": conversation.is_open
        and quote.status not in {"rejected", "expired"},
        "counterpart_name": (
            f"مشتری درخواست #{quote.request_id}"
            if is_vendor
            else quote.vendor.business_name
        ),
    }
    if is_vendor and vendor is not None:
        context.update(panel_context(vendor, "chats"))
        return render(request, "pages/chat/thread.html", context)
    return render(request, "pages/chat/thread.html", context)


@login_required
@require_http_methods(["POST"])
def upload_image(request: HttpRequest, quote_id: int) -> HttpResponse:
    quote = get_object_or_404(
        Quote.objects.select_related("request", "vendor", "vendor__user"),
        pk=quote_id,
    )
    if not user_can_access_quote(quote=quote, user=request.user):
        return HttpResponseForbidden("دسترسی مجاز نیست.")

    form = ChatImageUploadForm(request.POST, request.FILES)
    if not form.is_valid():
        messages.error(request, "آپلود تصویر نامعتبر است.")
        return redirect("chat:thread", quote_id=quote.pk)

    try:
        send_message(
            quote=quote,
            user=request.user,
            body=form.cleaned_data.get("body") or "",
            image=form.cleaned_data["image"],
        )
    except (ChatError, ValidationError, PermissionDenied) as exc:
        logger.info("chat upload failed quote=%s: %s", quote_id, exc)
        messages.error(request, str(exc))
    return redirect("chat:thread", quote_id=quote.pk)
