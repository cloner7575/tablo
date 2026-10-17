from __future__ import annotations

from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
from django.db.models import Avg, Count
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.accounts.models import User
from apps.common.validators import validate_uploaded_image
from apps.notifications.services import NotificationEvent, notify
from apps.orders.models import Order, OrderStage, OrderStatus
from apps.requests.models import RequestStatus
from apps.reviews.models import Review
from apps.vendors.models import Vendor


@transaction.atomic
def complete_order(*, order: Order, user: User) -> Order:
    order = (
        Order.objects.select_for_update()
        .select_related("vendor", "request", "customer")
        .get(pk=order.pk)
    )
    if (
        order.customer_id != user.id
        and order.vendor.user_id != user.id
        and not user.is_staff
    ):
        raise PermissionDenied

    if order.status != OrderStatus.ACTIVE:
        raise ValidationError(_("این سفارش قابل تکمیل نیست."))

    if order.workflow_required and (
        order.stage != OrderStage.DELIVERED or order.customer_id != user.pk
    ):
        raise ValidationError(
            _("نصب و تحویل باید انجام شده باشد؛ تأیید نهایی با مشتری است.")
        )
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


@transaction.atomic
def propose_design(
    *,
    order: Order,
    user: User,
    image: UploadedFile | None,
    price: int,
    installation_cost: int,
    materials: str,
    notes: str,
) -> Order:
    locked = Order.objects.select_for_update().select_related("vendor").get(pk=order.pk)
    if locked.vendor.user_id != user.pk:
        raise PermissionDenied
    if locked.status != OrderStatus.ACTIVE or locked.stage not in {
        OrderStage.DETAILS,
        OrderStage.APPROVAL,
    }:
        raise ValidationError(_("پس از تأیید مشتری، طرح و مبلغ قابل تغییر نیست."))
    if not materials.strip() or not notes.strip() or price < 0 or installation_cost < 0:
        raise ValidationError(_("مشخصات، توضیح طرح و مبلغ معتبر لازم است."))
    if image:
        validate_uploaded_image(image)
        locked.design_image = image
    locked.design_notes = notes
    locked.materials = materials
    locked.proposed_price = price
    locked.proposed_installation_cost = installation_cost
    locked.proposal_version += 1
    locked.stage = OrderStage.APPROVAL
    locked.save()
    order.proposal_version = locked.proposal_version
    return locked


@transaction.atomic
def approve_design(*, order: Order, user: User, version: int) -> Order:
    locked = Order.objects.select_for_update().get(pk=order.pk)
    if locked.customer_id != user.pk:
        raise PermissionDenied
    if (
        locked.status != OrderStatus.ACTIVE
        or locked.stage != OrderStage.APPROVAL
        or locked.proposal_version != version
        or locked.proposed_total is None
    ):
        raise ValidationError(
            _(
                "طرح یا مبلغ تغییر کرده است؛ "
                "صفحه را تازه کنید و نسخه جدید را بررسی کنید."
            )
        )
    locked.agreed_price = locked.proposed_total
    locked.stage = OrderStage.PRODUCTION
    locked.design_approved_at = timezone.now()
    locked.revision_request = ""
    locked.save(
        update_fields=[
            "agreed_price",
            "stage",
            "design_approved_at",
            "revision_request",
            "updated_at",
        ]
    )
    return locked


@transaction.atomic
def request_design_changes(
    *, order: Order, user: User, notes: str, version: int
) -> Order:
    locked = Order.objects.select_for_update().get(pk=order.pk)
    if locked.customer_id != user.pk:
        raise PermissionDenied
    if (
        locked.status != OrderStatus.ACTIVE
        or locked.stage != OrderStage.APPROVAL
        or locked.proposal_version != version
    ):
        raise ValidationError(_("این نسخه دیگر قابل بررسی نیست."))
    locked.revision_request = notes
    locked.stage = OrderStage.DETAILS
    locked.save(update_fields=["revision_request", "stage", "updated_at"])
    return locked


@transaction.atomic
def advance_order(*, order: Order, user: User, stage: str) -> Order:
    locked = Order.objects.select_for_update().select_related("vendor").get(pk=order.pk)
    if locked.vendor.user_id != user.pk:
        raise PermissionDenied
    transitions = {
        OrderStage.PRODUCTION: OrderStage.INSTALLATION,
        OrderStage.INSTALLATION: OrderStage.DELIVERED,
    }
    if (
        locked.status != OrderStatus.ACTIVE
        or transitions.get(locked.stage) != stage
        or locked.design_approved_at is None
    ):
        raise ValidationError(_("ابتدا مرحله قبلی و تأیید مشتری باید انجام شود."))
    locked.stage = stage
    locked.save(update_fields=["stage", "updated_at"])
    return locked
