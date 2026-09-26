from __future__ import annotations

from django.db.models import Q, QuerySet

from apps.requests.models import ProjectRequest, RequestStatus
from apps.vendors.models import Vendor, VerificationStatus


def matched_requests_for_vendor(vendor: Vendor) -> QuerySet[ProjectRequest]:
    if not vendor.is_approved:
        return ProjectRequest.objects.none()

    service_ids = list(vendor.services.values_list("id", flat=True))
    return (
        ProjectRequest.objects.filter(
            Q(city=vendor.city, service_id__in=service_ids)
            | Q(preferred_vendor=vendor),
            status__in=[
                RequestStatus.SUBMITTED,
                RequestStatus.REVIEWING,
                RequestStatus.RECEIVING_QUOTES,
                RequestStatus.QUOTED,
                RequestStatus.NEGOTIATING,
            ],
        )
        .select_related("service", "city", "customer")
        .distinct()
        .order_by("-created_at")
    )


def customer_requests(user) -> QuerySet[ProjectRequest]:
    return (
        ProjectRequest.objects.filter(customer=user)
        .select_related("service", "city")
        .prefetch_related("quotes__vendor")
        .order_by("-created_at")
    )


def active_vendors() -> QuerySet[Vendor]:
    return (
        Vendor.objects.filter(
            is_active=True,
            verification_status=VerificationStatus.APPROVED,
        )
        .select_related("city")
        .prefetch_related("services")
    )
