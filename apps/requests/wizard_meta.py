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
        "hint": (
            "اگر اسم‌ها برایتان آشنا نیست، «نمی‌دانم» را بزنید — "
            "تابلو‌سازها راهنمایی می‌کنند."
        ),
    },
    {
        "number": 2,
        "key": "city",
        "label": "شهر",
        "title": "پروژه در کدام شهر است؟",
        "hint": "پیشنهادها از تابلو‌سازهای همان شهر برایتان می‌آید.",
    },
    {
        "number": 3,
        "key": "dimensions",
        "label": "ابعاد",
        "title": "اندازهٔ تقریبی تابلو",
        "hint": "یکی را انتخاب کنید؛ دقیق بودن لازم نیست.",
    },
    {
        "number": 4,
        "key": "lighting",
        "label": "نور",
        "title": "نور برای شب لازم است؟",
        "hint": "اگر مطمئن نیستید همان «نمی‌دانم» را بزنید.",
    },
    {
        "number": 5,
        "key": "description",
        "label": "توضیحات",
        "title": "با زبان خودتان بگویید چه می‌خواهید",
        "hint": (
            "کسب‌وکار، محل و حسی که دوست دارید. لازم نیست اصطلاحات تابلو را بلد باشید."
        ),
    },
    {
        "number": 6,
        "key": "image",
        "label": "عکس",
        "title": "عکس بگذارید تا کار راحت‌تر شود",
        "hint": (
            "اگر جزئیات را نمی‌دانید، عکس سردر بهترین راهنماست. "
            "تا ۶ عکس می‌توانید بفرستید."
        ),
    },
    {
        "number": 7,
        "key": "budget",
        "label": "بودجه",
        "title": "بودجه تقریبی دارید؟",
        "hint": "اختیاری است. اگر نمی‌دانید خالی بگذارید و ادامه دهید.",
    },
    {
        "number": 8,
        "key": "phone",
        "label": "تماس",
        "title": "شماره موبایل برای پیگیری",
        "hint": "کد تأیید پیامک می‌شود تا پیشنهادها را در پنل ببینید.",
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
