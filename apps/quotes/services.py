from __future__ import annotations

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from apps.analytics.services import track
from apps.notifications.services import NotificationEvent, notify
from apps.orders.models import Order, OrderStatus
from apps.quotes.models import Quote, QuoteStatus
from apps.requests.models import ProjectRequest, RequestStatus
from apps.requests.selectors import matched_requests_for_vendor
from apps.vendors.models import Vendor


@transaction.atomic
def create_quote(
    *,
    vendor: Vendor,
    project_request: ProjectRequest,
    price: int,
    estimated_delivery_days: int,
    description: str = "",
    warranty: str = "",
    installation_cost: int = 0,
    material_details: str = "",
) -> Quote:
    if not vendor.is_approved:
        raise PermissionDenied(_("حساب تابلو‌ساز هنوز تأیید نشده است."))

    if not matched_requests_for_vendor(vendor).filter(pk=project_request.pk).exists():
        if project_request.preferred_vendor_id != vendor.pk:
            raise PermissionDenied(_("دسترسی به این درخواست مجاز نیست."))

    if Quote.objects.filter(request=project_request, vendor=vendor).exists():
        raise ValidationError(_("برای این درخواست قبلاً پیشنهاد ثبت کرده‌اید."))

    if project_request.status in {
        RequestStatus.ACCEPTED,
        RequestStatus.COMPLETED,
        RequestStatus.CANCELLED,
        RequestStatus.DRAFT,
    }:
        raise ValidationError(_("امکان ارسال پیشنهاد برای این درخواست وجود ندارد."))

    quote = Quote.objects.create(
        request=project_request,
        vendor=vendor,
        price=price,
        estimated_delivery_days=estimated_delivery_days,
        description=description,
        warranty=warranty,
        installation_cost=installation_cost,
        material_details=material_details,
        status=QuoteStatus.PENDING,
    )

    if project_request.status == RequestStatus.RECEIVING_QUOTES:
        project_request.status = RequestStatus.QUOTED
        project_request.save(update_fields=["status", "updated_at"])

    customer_phone = project_request.customer.phone if project_request.customer else ""
    notify(
        event=NotificationEvent.QUOTE_RECEIVED,
        recipient=customer_phone or str(project_request.customer_id),
        context={"quote_id": quote.pk, "request_id": project_request.pk},
    )
    track("quote_submitted", {"quote_id": quote.pk, "vendor_id": vendor.pk})
    return quote


@transaction.atomic
def accept_quote(*, quote: Quote, user) -> Order:
    project_request = quote.request
    if project_request.customer_id != user.id and not user.is_staff:
        raise PermissionDenied

    if quote.status in {
        QuoteStatus.ACCEPTED,
        QuoteStatus.REJECTED,
        QuoteStatus.EXPIRED,
    }:
        raise ValidationError(_("این پیشنهاد قابل پذیرش نیست."))

    if project_request.status in {
        RequestStatus.ACCEPTED,
        RequestStatus.COMPLETED,
        RequestStatus.CANCELLED,
    }:
        raise ValidationError(_("این درخواست دیگر قابل پذیرش پیشنهاد نیست."))

    quote.status = QuoteStatus.ACCEPTED
    quote.save(update_fields=["status", "updated_at"])

    Quote.objects.filter(request=project_request).exclude(pk=quote.pk).update(
        status=QuoteStatus.REJECTED
    )

    project_request.status = RequestStatus.ACCEPTED
    project_request.save(update_fields=["status", "updated_at"])

    order = Order.objects.create(
        request=project_request,
        quote=quote,
        customer=project_request.customer,
        vendor=quote.vendor,
        agreed_price=quote.price,
        status=OrderStatus.ACTIVE,
    )

    from apps.chat.services import close_losing_conversations

    close_losing_conversations(winning_quote=quote)

    notify(
        event=NotificationEvent.QUOTE_ACCEPTED,
        recipient=quote.vendor.phone or quote.vendor.user.phone or "",
        context={"order_id": order.pk, "quote_id": quote.pk},
    )
    track("quote_accepted", {"quote_id": quote.pk, "order_id": order.pk})
    return order


@transaction.atomic
def mark_quote_viewed(*, quote: Quote, user) -> Quote:
    if quote.request.customer_id != user.id:
        raise PermissionDenied
    if quote.status == QuoteStatus.PENDING:
        quote.status = QuoteStatus.VIEWED
        quote.save(update_fields=["status", "updated_at"])
        track("quote_viewed", {"quote_id": quote.pk})
    return quote
