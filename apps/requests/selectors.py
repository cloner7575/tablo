from __future__ import annotations

from django.db.models import Count, Q, QuerySet

from apps.requests.models import ProjectRequest, RequestStatus
from apps.vendors.models import Vendor, VerificationStatus

GUIDANCE_FILTER = "guidance"


def matched_requests_for_vendor(vendor: Vendor) -> QuerySet[ProjectRequest]:
    if not vendor.is_approved:
        return ProjectRequest.objects.none()

    service_ids = list(vendor.services.values_list("id", flat=True))
    return (
        ProjectRequest.objects.filter(
            Q(preferred_vendor=vendor)
            | Q(city=vendor.city, needs_guidance=True)
            | Q(city=vendor.city, service_id__in=service_ids),
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


def filter_by_service(
    qs: QuerySet[ProjectRequest], service: str
) -> QuerySet[ProjectRequest]:
    """`service` is a service slug, `GUIDANCE_FILTER`, or "" for no filter."""
    if not service:
        return qs
    if service == GUIDANCE_FILTER:
        return qs.filter(Q(needs_guidance=True) | Q(service__isnull=True))
    return qs.filter(service__slug=service)


def with_feed_counts(qs: QuerySet[ProjectRequest]) -> QuerySet[ProjectRequest]:
    return qs.annotate(
        quote_count=Count("quotes", distinct=True),
        image_count=Count("images", distinct=True),
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
