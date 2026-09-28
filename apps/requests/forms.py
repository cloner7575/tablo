from __future__ import annotations

from django import forms
from django.core.files.uploadedfile import UploadedFile
from django.utils.translation import gettext_lazy as _

from apps.catalog.models import Service
from apps.common.forms import MultipleFileInput, MultipleImageField
from apps.common.validators import validate_uploaded_image
from apps.locations.models import City
from apps.requests.models import MAX_REQUEST_IMAGES, LightingType

SERVICE_UNSURE = "unsure"

SIZE_CHOICES: tuple[tuple[str, str], ...] = (
    ("small", _("کوچک")),
    ("medium", _("متوسط")),
    ("large", _("بزرگ")),
    ("unsure", _("نمی‌دانم")),
)

SIZE_CARDS: tuple[dict[str, str | bool], ...] = (
    {
        "value": "small",
        "title": "کوچک",
        "hint": "حدود ۱ متر عرض — ویترین یا سردر کوچک",
    },
    {
        "value": "medium",
        "title": "متوسط",
        "hint": "حدود ۲٫۵ متر — سردر مغازه رایج",
    },
    {
        "value": "large",
        "title": "بزرگ",
        "hint": "حدود ۴ متر یا بیشتر — نمای پهن",
    },
    {
        "value": "unsure",
        "title": "نمی‌دانم",
        "hint": "از روی عکس یا بازدید بگویند",
        "emphasized": True,
    },
)

SIZE_TO_CM: dict[str, tuple[int | None, int | None]] = {
    "small": (120, 50),
    "medium": (250, 80),
    "large": (400, 120),
    "unsure": (None, None),
}

LIGHTING_CARDS: tuple[dict[str, str | bool], ...] = (
    {
        "value": LightingType.UNSURE,
        "title": "نمی‌دانم",
        "hint": "تابلو‌ساز بهترین نور را پیشنهاد می‌دهد",
        "emphasized": True,
    },
    {
        "value": LightingType.NONE,
        "title": "بدون نور",
        "hint": "فقط روز کافی است",
    },
    {
        "value": LightingType.LED,
        "title": "نور LED",
        "hint": "رایج و کم‌مصرف برای شب",
    },
    {
        "value": LightingType.NEON,
        "title": "نئون",
        "hint": "جلوهٔ شبانه و چشمگیر",
    },
    {
        "value": LightingType.SMD,
        "title": "SMD",
        "hint": "نور یکدست و مدرن",
    },
    {
        "value": LightingType.HIDDEN,
        "title": "نور مخفی",
        "hint": "نور از پشت یا لبه، بدون لامپ دیده",
    },
)


class RequestWizardServiceForm(forms.Form):
    """Service pick or 'I don't know' — matching broadens when unsure."""

    choice = forms.ChoiceField(
        label=_("نوع تابلو"),
        widget=forms.RadioSelect,
    )

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        services = list(Service.objects.filter(is_active=True).order_by("sort_order"))
        choices: list[tuple[str, str]] = [
            (str(service.pk), service.title) for service in services
        ]
        choices.append((SERVICE_UNSURE, _("نمی‌دانم؛ تابلو‌سازها راهنمایی کنند")))
        self.fields["choice"].choices = choices
        self.service_cards = [
            {
                "value": str(service.pk),
                "title": service.title,
                "hint": service.suitable_for
                or service.description
                or "برای سردر و برندینگ رایج است.",
            }
            for service in services
        ]
        self.service_cards.append(
            {
                "value": SERVICE_UNSURE,
                "title": "نمی‌دانم؛ راهنمایی می‌خواهم",
                "hint": (
                    "عکس محل و توضیح ساده کافی است. "
                    "تابلو‌سازهای شهر شما نوع مناسب را پیشنهاد می‌دهند."
                ),
                "emphasized": True,
            }
        )


class RequestWizardCityForm(forms.Form):
    city = forms.ModelChoiceField(
        label=_("شهر"),
        queryset=City.objects.filter(is_active=True),
    )


class RequestWizardDimensionsForm(forms.Form):
    size_choice = forms.ChoiceField(
        label=_("اندازه تقریبی"),
        choices=SIZE_CHOICES,
        widget=forms.RadioSelect,
    )

    def resolved_dimensions(self) -> tuple[int | None, int | None]:
        choice = self.cleaned_data["size_choice"]
        return SIZE_TO_CM[choice]

    @property
    def size_cards(self) -> list[dict[str, str | bool]]:
        return list(SIZE_CARDS)


class RequestWizardLightingForm(forms.Form):
    lighting_type = forms.ChoiceField(
        label=_("نورپردازی"),
        choices=LightingType.choices,
        widget=forms.RadioSelect,
        initial=LightingType.UNSURE,
    )

    @property
    def lighting_cards(self) -> list[dict[str, str | bool]]:
        return list(LIGHTING_CARDS)


class RequestWizardDescriptionForm(forms.Form):
    description = forms.CharField(
        label=_("با زبان خودتان بگویید چه می‌خواهید"),
        widget=forms.Textarea(
            attrs={
                "rows": 4,
                "placeholder": (
                    "مثلاً: مغازه میوه‌فروشی در ونک دارم، "
                    "می‌خواهم شب هم از خیابان دیده شود، "
                    "اسم مغازه «میوه‌سرای آریا» است…"
                ),
            }
        ),
        required=False,
        help_text=_(
            "نوع تابلو را لازم نیست بلد باشید. کسب‌وکار، محل و حس موردنظرتان کافی است."
        ),
    )
    text_content = forms.CharField(
        label=_("متن روی تابلو (اگر می‌دانید)"),
        required=False,
        help_text=_("اختیاری. همان اسم یا شعاری که باید روی تابلو باشد."),
    )
    business_type = forms.CharField(
        label=_("نوع کسب‌وکار"),
        required=False,
        help_text=_("مثلاً کافه، داروخانه، بوتیک، شرکت…"),
    )
    district = forms.CharField(
        label=_("محله"),
        required=False,
        help_text=_("کمک می‌کند تابلو‌ساز فاصله و شرایط نصب را بهتر بفهمد."),
    )

    def __init__(
        self,
        *args: object,
        needs_guidance: bool = False,
        **kwargs: object,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.needs_guidance = needs_guidance
        if needs_guidance:
            self.fields["description"].required = True
            self.fields["description"].help_text = _(
                "چون نوع تابلو را انتخاب نکرده‌اید، "
                "یک توضیح کوتاه لازم است تا تابلو‌ساز بداند چه کمکی کند."
            )

    def clean(self):
        cleaned = super().clean()
        if not self.needs_guidance:
            return cleaned
        description = (cleaned.get("description") or "").strip()
        business = (cleaned.get("business_type") or "").strip()
        if not description and not business:
            raise forms.ValidationError(
                _(
                    "لطفاً حداقل بگویید چه کسب‌وکاری دارید "
                    "یا چه می‌خواهید — حتی دو سه جمله کافی است."
                )
            )
        return cleaned


class RequestWizardImageForm(forms.Form):
    images = MultipleImageField(
        label=_("عکس‌های محل یا نمونه"),
        required=False,
        widget=MultipleFileInput(
            attrs={
                "accept": "image/jpeg,image/png,image/webp",
                "data-multi-preview": "true",
            }
        ),
        help_text=_(
            "اگر جزئیات را نمی‌دانید، عکس بهترین کمکتان است. "
            "تا %(n)s عکس: محل نصب، لوگوی فعلی، یا نمونه‌ای که دوست دارید."
        )
        % {"n": MAX_REQUEST_IMAGES},
    )

    def clean_images(self) -> list[UploadedFile]:
        files = self.cleaned_data.get("images") or []
        if len(files) > MAX_REQUEST_IMAGES:
            raise forms.ValidationError(
                _("حداکثر %(n)s عکس مجاز است.") % {"n": MAX_REQUEST_IMAGES}
            )
        for uploaded in files:
            validate_uploaded_image(uploaded)
        return files


class RequestWizardBudgetForm(forms.Form):
    budget_min = forms.IntegerField(
        label=_("حداقل بودجه (تومان)"),
        required=False,
        min_value=0,
        help_text=_("اختیاری. اگر نمی‌دانید خالی بگذارید."),
    )
    budget_max = forms.IntegerField(
        label=_("حداکثر بودجه (تومان)"),
        required=False,
        min_value=0,
        help_text=_("اختیاری. بازه بودجه پیشنهادهای نامربوط را کم می‌کند."),
    )

    def clean(self):
        cleaned = super().clean()
        lo = cleaned.get("budget_min")
        hi = cleaned.get("budget_max")
        if lo is not None and hi is not None and lo > hi:
            self.add_error("budget_max", _("حداکثر بودجه باید بزرگ‌تر از حداقل باشد."))
        return cleaned


class ReviewForm(forms.Form):
    rating = forms.IntegerField(label=_("امتیاز"), min_value=1, max_value=5)
    comment = forms.CharField(
        label=_("نظر"),
        widget=forms.Textarea(attrs={"rows": 3}),
        required=False,
    )
