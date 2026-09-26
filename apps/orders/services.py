from __future__ import annotations

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Avg, Count
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.notifications.services import NotificationEvent, notify
from apps.orders.models import Order, OrderStatus
from apps.requests.models import RequestStatus
from apps.reviews.models import Review
from apps.vendors.models import Vendor


@transaction.atomic
def complete_order(*, order: Order, user) -> Order:
    if (
        order.customer_id != user.id
        and order.vendor.user_id != user.id
        and not user.is_staff
    ):
        raise PermissionDenied

    if order.status != OrderStatus.ACTIVE:
        raise ValidationError(_("این سفارش قابل تکمیل نیست."))

    order.status = OrderStatus.COMPLETED
    order.completed_at = timezone.now()
    order.save(update_fields=["status", "completed_at", "updated_at"])

    project_request = order.request
    project_request.status = RequestStatus.COMPLETED
    project_request.save(update_fields=["status", "updated_at"])

    vendor = order.vendor
    vendor.completed_projects = vendor.completed_projects + 1
    vendor.save(update_fields=["completed_projects", "updated_at"])

    notify(
        event=NotificationEvent.PROJECT_COMPLETED,
        recipient=order.customer.phone or str(order.customer_id),
        context={"order_id": order.pk},
    )
    notify(
        event=NotificationEvent.REVIEW_REQUESTED,
        recipient=order.customer.phone or str(order.customer_id),
        context={"request_id": project_request.pk},
    )
    return order


@transaction.atomic
def create_review(
    *,
    user,
    project_request,
    rating: int,
    comment: str = "",
) -> Review:
    if project_request.customer_id != user.id:
        raise PermissionDenied
    if project_request.status != RequestStatus.COMPLETED:
        raise ValidationError(_("فقط پس از تکمیل پروژه می‌توانید نظر ثبت کنید."))
    if hasattr(project_request, "review"):
        raise ValidationError(_("برای این پروژه قبلاً نظر ثبت شده است."))
    if not hasattr(project_request, "order"):
        raise ValidationError(_("سفارش مرتبط یافت نشد."))

    vendor = project_request.order.vendor
    review = Review.objects.create(
        customer=user,
        vendor=vendor,
        request=project_request,
        rating=rating,
        comment=comment,
    )
    _refresh_vendor_rating(vendor)
    return review


def _refresh_vendor_rating(vendor: Vendor) -> None:
    stats = vendor.reviews.filter(is_published=True).aggregate(
        avg=Avg("rating"),
        count=Count("id"),
    )
    vendor.rating = stats["avg"] or 0
    vendor.review_count = stats["count"] or 0
    vendor.save(update_fields=["rating", "review_count", "updated_at"])
