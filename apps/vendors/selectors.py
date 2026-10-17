from django.db.models import Count, Exists, OuterRef, Prefetch, Q, QuerySet

from apps.catalog.models import Service
from apps.chat.models import Conversation
from apps.locations.models import City
from apps.quotes.models import Quote
from apps.vendors.models import Vendor, VerificationStatus


def discoverable_vendors(
    *,
    query: str = "",
    city: City | None = None,
    service: Service | None = None,
    sort: str = "",
) -> QuerySet[Vendor]:
    vendors = Vendor.objects.filter(
        is_active=True,
        verification_status=VerificationStatus.APPROVED,
        city__is_active=True,
    )
    if query:
        vendors = vendors.filter(
            Q(business_name__icontains=query) | Q(description__icontains=query)
        )
    if city:
        vendors = vendors.filter(city=city)
    if service:
        vendors = vendors.filter(services=service)
    ordering = {
        "rating": ("-rating", "-review_count", "pk"),
        "experience": ("-years_of_experience", "-rating", "pk"),
    }.get(sort, ("-is_featured", "-rating", "pk"))
    return (
        vendors.select_related("city")
        .prefetch_related(
            Prefetch("services", queryset=Service.objects.filter(is_active=True))
        )
        .annotate(
            portfolio_count=Count(
                "portfolio_items",
                filter=Q(portfolio_items__is_published=True),
                distinct=True,
            )
        )
        .order_by(*ordering)
    )


def vendor_quotes(vendor: Vendor) -> QuerySet[Quote]:
    return (
        Quote.objects.filter(vendor=vendor)
        .select_related('request__service', 'request__city', 'request', 'order')
        .annotate(has_chat=Exists(Conversation.objects.filter(quote_id=OuterRef('pk'))))
        .order_by('-created_at', '-pk')
    )
