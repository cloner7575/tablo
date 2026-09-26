from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

import jdatetime
from django.conf import settings
from django.utils import timezone

_PERSIAN_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def currency_label() -> str:
    return getattr(settings, "CURRENCY_LABEL", "تومان")


def to_persian_digits(value: object, *, separators: bool = True) -> str:
    """Rewrite ASCII digits as Persian ones (۰-۹) for display only.

    `separators` also swaps the thousands comma for the Arabic separator ٬,
    which is what a grouped Persian number looks like. Never feed the result
    back into `int()` — this is a presentation layer.
    """
    text = str(value).translate(_PERSIAN_DIGITS)
    if separators:
        text = text.replace(",", "٬")
    return text


def format_int_grouped(value: int | str, *, persian_digits: bool = False) -> str:
    """Format an integer with thousand separators (e.g. 185000 → 185,000)."""
    try:
        number = int(value)
    except (TypeError, ValueError):
        return str(value)
    grouped = f"{number:,}"
    if persian_digits:
        grouped = to_persian_digits(grouped)
    return grouped


def format_toman(
    value: int | str | Decimal | None,
    *,
    suffix: str | None = None,
    persian_digits: bool = False,
) -> str:
    """Format a toman amount with thousand separators and currency label."""
    if value is None or value == "":
        return ""
    try:
        amount = int(value)
    except (TypeError, ValueError):
        return str(value)
    label = currency_label() if suffix is None else suffix
    grouped = format_int_grouped(amount, persian_digits=persian_digits)
    if label:
        return f"{grouped} {label}"
    return grouped


def to_jalali(
    value: date | datetime | None,
) -> jdatetime.date | jdatetime.datetime | None:
    """Convert to Jalali for display, with Persian month and weekday names.

    Without the locale, `%B` renders "Farvardin" and `%A` renders "Friday".
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        if timezone.is_aware(value):
            value = timezone.localtime(value)
        return jdatetime.datetime.fromgregorian(
            datetime=value,
            locale=jdatetime.FA_LOCALE,
        )
    return jdatetime.date.fromgregorian(date=value, locale=jdatetime.FA_LOCALE)


def format_jalali(
    value: date | datetime | None,
    fmt: str = "%Y/%m/%d",
    *,
    persian_digits: bool = False,
) -> str:
    """Format a Gregorian date/datetime as Jalali for display."""
    jalali = to_jalali(value)
    if jalali is None:
        return ""
    text = jalali.strftime(fmt)
    if persian_digits:
        text = to_persian_digits(text, separators=False)
    return text


def toman_to_rial(amount_toman: int) -> int:
    """Iranian payment gateways typically charge in rial."""
    return int(amount_toman) * 10
