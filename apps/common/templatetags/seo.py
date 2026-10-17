import json

from django import template
from django.utils.html import format_html
from django.utils.safestring import SafeString, mark_safe

register = template.Library()


@register.simple_tag
def structured_data(data: dict[str, object]) -> SafeString:
    # JSON is escaped for script-element context, including user-written titles.
    payload = (
        json.dumps(data, ensure_ascii=False)
        .replace('<', '\\u003C')
        .replace('>', '\\u003E')
        .replace('&', '\\u0026')
    )
    return format_html(
        '<script type="application/ld+json">{}</script>', mark_safe(payload)
    )
