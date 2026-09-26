"""UI metadata for the customer request wizard."""

from __future__ import annotations

from typing import TypedDict


class WizardStep(TypedDict):
    number: int
    key: str
    label: str
    title: str
    hint: str


WIZARD_STEPS: tuple[WizardStep, ...] = (
    {
        "number": 1,
        "key": "service",
        "label": "نوع تابلو",
        "title": "چه نوع تابلویی می‌خواهید؟",
        "hint": "چلنیوم، نئون، فلکسی و بقیه — همین انتخاب به تابلو‌سازهای مرتبط می‌رسد.",
    },
    {
        "number": 2,
        "key": "city",
        "label": "شهر",
        "title": "پروژه در کدام شهر است؟",
        "hint": "پیشنهادها از تابلو‌سازهای همان شهر (و نزدیک) برایتان می‌آید.",
    },
    {
        "number": 3,
        "key": "dimensions",
        "label": "ابعاد",
        "title": "ابعاد تقریبی تابلو چقدر است؟",
        "hint": "اگر دقیق نمی‌دانید، عدد نزدیک کافی است؛ بعداً قابل اصلاح است.",
    },
    {
        "number": 4,
        "key": "lighting",
        "label": "نور",
        "title": "نورپردازی مد نظرتان چیست؟",
        "hint": "نور روی دیده شدن تابلو در شب اثر زیادی دارد.",
    },
    {
        "number": 5,
        "key": "description",
        "label": "توضیحات",
        "title": "کمی از پروژه‌تان بگویید",
        "hint": "متن تابلو، نوع کسب‌وکار و محله کمک می‌کند پیشنهادها دقیق‌تر شوند.",
    },
    {
        "number": 6,
        "key": "image",
        "label": "عکس",
        "title": "عکس محل نصب دارید؟",
        "hint": "اختیاری است؛ ولی با یک عکس سردر، قیمت‌گذاری خیلی بهتر می‌شود.",
    },
    {
        "number": 7,
        "key": "budget",
        "label": "بودجه",
        "title": "بودجه تقریبی‌تان چقدر است؟",
        "hint": "اختیاری است. بازه بودجه، پیشنهادهای نامربوط را کم می‌کند.",
    },
    {
        "number": 8,
        "key": "phone",
        "label": "تماس",
        "title": "شماره موبایل برای پیگیری",
        "hint": "کد تأیید پیامک می‌شود تا بتوانید پیشنهادها را در پنل ببینید.",
    },
    {
        "number": 9,
        "key": "submit",
        "label": "ثبت",
        "title": "همه‌چیز آماده ثبت است",
        "hint": "با تأیید، درخواست برای تابلو‌سازهای مرتبط ارسال می‌شود.",
    },
)

BACK_URLS: dict[int, str | None] = {
    1: None,
    2: "requests:wizard_service",
    3: "requests:wizard_city",
    4: "requests:wizard_dimensions",
    5: "requests:wizard_lighting",
    6: "requests:wizard_description",
    7: "requests:wizard_image",
    8: "requests:wizard_budget",
    9: "requests:wizard_budget",
}


def wizard_shell(
    step: int,
    *,
    step_title: str | None = None,
    step_hint: str | None = None,
    total: int = 9,
) -> dict[str, object]:
    meta = WIZARD_STEPS[step - 1]
    return {
        "step": step,
        "total": total,
        "step_title": step_title or meta["title"],
        "step_hint": step_hint or meta["hint"],
        "step_label": meta["label"],
        "wizard_steps": WIZARD_STEPS,
        "back_url_name": BACK_URLS.get(step),
    }
