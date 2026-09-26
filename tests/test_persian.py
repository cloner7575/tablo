from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from django.template import Context, Template
from django.utils import timezone

from apps.common.persian import (
    format_jalali,
    format_toman,
    to_persian_digits,
    toman_to_rial,
)


def test_format_toman_groups_thousands() -> None:
    assert format_toman(185000) == "185,000 تومان"
    assert format_toman(185000, suffix="") == "185,000"
    assert format_toman(None) == ""


def test_toman_to_rial() -> None:
    assert toman_to_rial(185000) == 1_850_000


def test_format_jalali() -> None:
    dt = timezone.make_aware(
        datetime(2025, 3, 21, 12, 0, 0),
        ZoneInfo("Asia/Tehran"),
    )
    # 1404/01/01 is Nowruz 2025
    assert format_jalali(dt) == "1404/01/01"
    # Month and weekday names must be Persian, not "Farvardin" / "Friday"
    assert format_jalali(dt, "%A %d %B %Y") == "جمعه 01 فروردین 1404"


def test_to_persian_digits() -> None:
    assert to_persian_digits("185,000 تومان") == "۱۸۵٬۰۰۰ تومان"
    assert to_persian_digits("1404/01/01", separators=False) == "۱۴۰۴/۰۱/۰۱"
    assert format_jalali(None, persian_digits=True) == ""


def test_fa_digits_filter_chains_after_toman_and_jalali() -> None:
    html = Template(
        "{% load persian %}{{ price|toman|fa_digits }}|{{ when|jalali|fa_digits }}"
    ).render(
        Context(
            {
                "price": 185000,
                "when": timezone.make_aware(
                    datetime(2025, 3, 21, 8, 0, 0),
                    ZoneInfo("Asia/Tehran"),
                ),
            }
        )
    )
    assert html == "۱۸۵٬۰۰۰ تومان|۱۴۰۴/۰۱/۰۱"


@pytest.mark.django_db
def test_toman_and_jalali_template_filters() -> None:
    html = Template("{% load persian %}{{ price|toman }}|{{ when|jalali }}").render(
        Context(
            {
                "price": 12000,
                "when": timezone.make_aware(
                    datetime(2025, 3, 21, 8, 0, 0),
                    ZoneInfo("Asia/Tehran"),
                ),
            }
        )
    )
    assert html == "12,000 تومان|1404/01/01"
