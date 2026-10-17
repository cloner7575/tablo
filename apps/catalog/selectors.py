from django.db.models import Q, QuerySet

from apps.catalog.models import Service


def active_services(query: str = "") -> QuerySet[Service]:
    services = Service.objects.filter(is_active=True)
    if not query:
        return services
    return services.filter(
        Q(title__icontains=query)
        | Q(description__icontains=query)
        | Q(suitable_for__icontains=query)
        | Q(materials__icontains=query)
    )
