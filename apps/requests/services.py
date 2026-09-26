from __future__ import annotations

import logging

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from apps.analytics.services import track
from apps.notifications.services import NotificationEvent, notify
from apps.requests.models import ProjectRequest, RequestStatus

logger = logging.getLogger(__name__)


@transaction.atomic
def submit_project_request(*, project_request: ProjectRequest) -> ProjectRequest:
    if project_request.customer_id is None:
        raise ValidationError(_("مشتری برای درخواست مشخص نشده است."))
    if project_request.service_id is None or project_request.city_id is None:
        raise ValidationError(_("نوع تابلو و شهر الزامی است."))

    project_request.status = RequestStatus.RECEIVING_QUOTES
    if not project_request.title:
        project_request.title = (
            f"{project_request.service.title} — {project_request.city.name}"
        )
    project_request.save()

    phone = project_request.customer.phone or str(project_request.customer_id)
    notify(
        event=NotificationEvent.REQUEST_CREATED,
        recipient=phone,
        context={"request_id": project_request.pk},
    )
    track(
        "request_completed",
        {"request_id": project_request.pk, "service": project_request.service.slug},
    )
    return project_request


@transaction.atomic
def cancel_project_request(*, project_request: ProjectRequest, user) -> ProjectRequest:
    if project_request.customer_id != user.id and not user.is_staff:
        raise PermissionDenied
    if project_request.status in {
        RequestStatus.COMPLETED,
        RequestStatus.CANCELLED,
        RequestStatus.ACCEPTED,
    }:
        raise ValidationError(_("این درخواست قابل لغو نیست."))
    project_request.status = RequestStatus.CANCELLED
    project_request.save(update_fields=["status", "updated_at"])
    return project_request
