"""Helpers for the vendor staff panel."""

from __future__ import annotations

from apps.chat.selectors import unread_chat_count_for_vendor
from apps.requests.selectors import matched_requests_for_vendor
from apps.vendors.models import Vendor, VerificationStatus


def profile_checklist(vendor: Vendor) -> list[dict[str, object]]:
    """Practical checklist items to make the public profile more complete."""
    items: list[dict[str, object]] = [
        {
            "label": "توضیحات کسب‌وکار",
            "done": bool(vendor.description.strip()),
            "hint": "یک پاراگراف درباره تخصص و سبک کار بنویسید.",
        },
        {
            "label": "آدرس یا محدوده خدمت",
            "done": bool(vendor.address.strip()),
            "hint": "آدرس کارگاه یا محدوده نصب را مشخص کنید.",
        },
        {
            "label": "اینستاگرام یا وب‌سایت",
            "done": bool(vendor.instagram.strip() or vendor.website),
            "hint": "لینک شبکه‌های اجتماعی اعتماد مشتری را بالا می‌برد.",
        },
        {
            "label": "حداقل یک خدمت",
            "done": vendor.services.exists(),
            "hint": "خدمات فعال برای مچ شدن با درخواست‌ها لازم است.",
        },
        {
            "label": "حداقل یک نمونه‌کار",
            "done": vendor.portfolio_items.filter(is_published=True).exists(),
            "hint": "نمونه‌کار واقعی شانس پذیرش پیشنهاد را زیاد می‌کند.",
        },
        {
            "label": "تأیید مدیریت",
            "done": vendor.verification_status == VerificationStatus.APPROVED,
            "hint": "تا تأیید نشوید درخواست‌های عمومی را نمی‌بینید.",
        },
    ]
    return items


def checklist_progress(items: list[dict[str, object]]) -> tuple[int, int]:
    done = sum(1 for item in items if item["done"])
    return done, len(items)


def open_requests_count(vendor: Vendor) -> int:
    quoted_ids = vendor.quotes.values_list("request_id", flat=True)
    return matched_requests_for_vendor(vendor).exclude(pk__in=quoted_ids).count()


def panel_context(vendor: Vendor, active: str, **extra: object) -> dict[str, object]:
    return {
        "vendor": vendor,
        "panel_active": active,
        "new_requests_count": open_requests_count(vendor),
        "unread_chat_count": unread_chat_count_for_vendor(vendor=vendor),
        **extra,
    }
