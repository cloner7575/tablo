from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from django import template

from apps.common.persian import format_jalali, format_toman, to_persian_digits

register = template.Library()


@register.filter(name="toman")
def toman_filter(
    value: int | str | Decimal | None,
    suffix: str | None = None,
) -> str:
    """Format amount as grouped toman. Use `{{ n|toman }}` or `{{ n|toman:'' }}`."""
    if suffix == "":
        return format_toman(value, suffix="")
    if suffix is None:
        return format_toman(value)
    return format_toman(value, suffix=suffix)


@register.filter(name="jalali")
def jalali_filter(value: date | datetime | None, fmt: str = "%Y/%m/%d") -> str:
    """Format Gregorian date/datetime as Jalali. `{{ dt|jalali }}`."""
    return format_jalali(value, fmt=fmt)


@register.filter(name="fa_digits")
def fa_digits_filter(value: object) -> str:
    """Display ASCII digits as Persian ones. Chains: `{{ n|toman|fa_digits }}`.

    Presentation only — do not apply it to values a form or URL reads back.
    """
    return to_persian_digits(value)
