from typing import Literal

from django.db.models import Q, QuerySet
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import BaseModel

from apps.chat.models import Conversation, Message
from apps.integrations.auth import origin
from apps.integrations.models import DesignAsset
from apps.integrations.tools.context import actor, database_tool
from apps.orders.models import Order
from apps.portfolio.models import PortfolioItem
from apps.quotes.models import Quote
from apps.requests.models import ProjectRequest
from apps.requests.selectors import matched_requests_for_vendor


class Page(BaseModel):
    items: list[dict[str, object]]
    next_offset: int | None


def visible_requests(vendor_id: int) -> QuerySet[ProjectRequest]:
    from apps.vendors.models import Vendor

    vendor = Vendor.objects.get(pk=vendor_id)
    return ProjectRequest.objects.filter(
        Q(pk__in=matched_requests_for_vendor(vendor).values('pk'))
        | Q(quotes__vendor=vendor)
    ).distinct()


def list_records(
    kind: Literal[
        'requests',
        'quotes',
        'projects',
        'conversations',
        'portfolio',
        'designs',
        'notifications',
    ],
    query: str = '',
    offset: int = 0,
    limit: int = 20,
) -> Page:
    """
    اطلاعات مجاز پنل خودم؛ هر فهرست حداکثر ۵۰ رکورد دارد. اعلان‌ها رویدادهای
    مربوط به حساب خودم هستند.
    """
    connection = actor()
    vendor = connection.vendor
    offset = max(0, offset)
    limit = min(50, max(1, limit))
    if len(query) > 100 or offset > 10000:
        raise ValueError('جست‌وجو یا شماره صفحه معتبر نیست.')
    if kind == 'requests':
        rows = (
            visible_requests(vendor.pk)
            .filter(title__icontains=query)
            .order_by('-created_at')
            .values('id', 'title', 'status', 'description', 'service_id', 'city_id')
        )
    elif kind == 'quotes':
        rows = (
            Quote.objects.filter(vendor=vendor, request__title__icontains=query)
            .order_by('-created_at')
            .values(
                'id',
                'request_id',
                'price',
                'installation_cost',
                'status',
                'description',
            )
        )
    elif kind == 'projects':
        rows = (
            Order.objects.filter(vendor=vendor, request__title__icontains=query)
            .order_by('-created_at')
            .values(
                'id',
                'request_id',
                'stage',
                'status',
                'design_notes',
                'materials',
                'proposal_version',
            )
        )
    elif kind == 'portfolio':
        rows = (
            PortfolioItem.objects.filter(vendor=vendor, title__icontains=query)
            .order_by('-created_at')
            .values(
                'id', 'title', 'description', 'is_published', 'service_id', 'city_id'
            )
        )
    elif kind == 'designs':
        rows = (
            DesignAsset.objects.filter(vendor=vendor, title__icontains=query)
            .order_by('-created_at')
            .values('id', 'title', 'notes', 'order_id', 'portfolio_id', 'provenance')
        )
    elif kind == 'conversations':
        rows = (
            Conversation.objects.filter(
                quote__vendor=vendor, quote__request__title__icontains=query
            )
            .order_by('-created_at')
            .values('id', 'quote_id', 'status', 'last_message_at')
        )
    else:
        # Legacy notification logs have no owner FK; do not match by phone.
        rows = (
            Message.objects.filter(
                conversation__quote__vendor=vendor,
                read_at__isnull=True,
                body__icontains=query,
            )
            .exclude(sender=vendor.user)
            .order_by('-created_at')
            .values('id', 'conversation_id', 'body', 'created_at')
        )
    items = list(rows[offset : offset + limit + 1])
    return Page(
        items=[
            {
                key: str(value)
                if value is not None and not isinstance(value, (str, int, bool, float))
                else value
                for key, value in row.items()
            }
            for row in items[:limit]
        ],
        next_offset=offset + limit if len(items) > limit else None,
    )


def get_profile() -> dict[str, object]:
    """پروفایل کسب‌وکار متصل و شناسه خدمات و شهرهای فعال برای ویرایش."""
    from apps.catalog.models import Service
    from apps.locations.models import City

    vendor = actor().vendor
    fields = [
        'id',
        'business_name',
        'description',
        'phone',
        'city_id',
        'address',
        'instagram',
        'website',
        'years_of_experience',
    ]
    return {
        'profile': {key: getattr(vendor, key) for key in fields},
        'services': list(vendor.services.values_list('pk', flat=True)),
        'available_services': list(
            Service.objects.filter(is_active=True).values('id', 'title')[:100]
        ),
        'available_cities': list(
            City.objects.filter(is_active=True).values('id', 'name')[:500]
        ),
    }


def panel_summary() -> dict[str, object]:
    """خلاصه وضعیت درخواست‌ها، پروژه‌ها، پیام‌ها و تصاویر خصوصی من."""
    vendor = actor().vendor
    return {
        'business_name': vendor.business_name,
        'requests': visible_requests(vendor.pk).count(),
        'quotes': Quote.objects.filter(vendor=vendor).count(),
        'projects': Order.objects.filter(vendor=vendor).count(),
        'unread_messages': Message.objects.filter(
            conversation__quote__vendor=vendor, read_at__isnull=True
        )
        .exclude(sender=vendor.user)
        .count(),
        'designs': DesignAsset.objects.filter(vendor=vendor).count(),
    }


def read_messages(conversation_id: int, offset: int = 0, limit: int = 20) -> Page:
    """
    پیام‌های یک گفتگوی متعلق به تابلوساز؛ مشاهده پیام، آن را خوانده‌شده
    علامت نمی‌زند.
    """
    from django.shortcuts import get_object_or_404

    conversation = get_object_or_404(
        Conversation, pk=conversation_id, quote__vendor=actor().vendor
    )
    limit = min(50, max(1, limit))
    offset = max(0, offset)
    items = list(
        conversation.messages.order_by('-created_at').values('id', 'body', 'sender_id')[
            offset : offset + limit + 1
        ]
    )
    return Page(
        items=items[:limit], next_offset=offset + limit if len(items) > limit else None
    )


def design_brief(request_id: int) -> dict[str, object]:
    """
    شرح درخواست و تصاویر مرجع مجاز برای طراحی در ChatGPT؛ فقط اطلاعات همین
    درخواست.
    """
    from django.shortcuts import get_object_or_404

    item = get_object_or_404(
        visible_requests(actor().vendor_id).prefetch_related('images'), pk=request_id
    )
    return {
        'id': item.pk,
        'title': item.title,
        'description': item.description,
        'width_cm': item.width_cm,
        'height_cm': item.height_cm,
        'text_content': item.text_content,
        'material': item.material,
        'lighting_type': item.lighting_type,
        'budget_min': item.budget_min,
        'budget_max': item.budget_max,
        'installation_required': item.installation_required,
        'references': [
            origin() + url if url.startswith('/') else url for url in item.photo_urls()
        ],
        'guidance': (
            'طرح مفهومی است. متن فارسی تابلو، ابعاد، متریال، رنگ و نور را '
            'از تابلوساز بپرس؛ تصویر را در ChatGPT بساز و فایل نتیجه را با '
            'save_design در فضای خصوصی ذخیره کن.'
        ),
    }


def register(server: FastMCP) -> None:
    for fn in [list_records, get_profile, panel_summary, read_messages, design_brief]:
        server.add_tool(
            database_tool(fn),
            annotations=ToolAnnotations(
                readOnlyHint=True, destructiveHint=False, openWorldHint=False
            ),
        )
