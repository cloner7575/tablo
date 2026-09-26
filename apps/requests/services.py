from __future__ import annotations

import logging

from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from apps.analytics.services import track
from apps.notifications.services import NotificationEvent, notify
from apps.requests.models import (
    MAX_REQUEST_IMAGES,
    ProjectRequest,
    RequestImage,
    RequestStatus,
)

logger = logging.getLogger(__name__)


@transaction.atomic
def submit_project_request(*, project_request: ProjectRequest) -> ProjectRequest:
    if project_request.customer_id is None:
        raise ValidationError(_("مشتری برای درخواست مشخص نشده است."))
    if project_request.city_id is None:
        raise ValidationError(_("شهر الزامی است."))
    if project_request.service_id is None and not project_request.needs_guidance:
        raise ValidationError(_("نوع تابلو را انتخاب کنید یا گزینهٔ راهنمایی را بزنید."))

    project_request.status = RequestStatus.RECEIVING_QUOTES
    if not project_request.title:
        if project_request.needs_guidance or project_request.service_id is None:
            project_request.title = (
                f"درخواست راهنمایی تابلو — {project_request.city.name}"
            )
        else:
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
        {
            "request_id": project_request.pk,
            "service": (
                project_request.service.slug
                if project_request.service_id
                else "guidance"
            ),
            "needs_guidance": project_request.needs_guidance,
        },
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


@transaction.atomic
def replace_request_images(
    *,
    project_request: ProjectRequest,
    files: list[UploadedFile],
) -> ProjectRequest:
    """Replace gallery photos. Clears legacy single-image field."""
    if len(files) > MAX_REQUEST_IMAGES:
        raise ValidationError(
            _("حداکثر %(n)s عکس می‌توانید بارگذاری کنید.") % {"n": MAX_REQUEST_IMAGES}
        )

    project_request.images.all().delete()
    project_request.image = ""
    project_request.save(update_fields=["image", "updated_at"])

    for index, uploaded in enumerate(files):
        RequestImage.objects.create(
            request=project_request,
            image=uploaded,
            sort_order=index,
        )
    return project_request
