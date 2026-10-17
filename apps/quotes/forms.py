from __future__ import annotations

from django import forms
from django.utils.translation import gettext_lazy as _

from apps.quotes.models import PriceKind, Quote


class QuoteForm(forms.ModelForm):
    class Meta:
        model = Quote
        fields = [
            "price",
            "price_kind",
            "estimated_delivery_days",
            "description",
            "warranty",
            "installation_cost",
            "material_details",
        ]
        labels = {
            "price": _("هزینه ساخت (تومان)"),
            "estimated_delivery_days": _("روز اجرا"),
            "description": _("توضیحات"),
            "warranty": _("گارانتی"),
            "installation_cost": _("هزینه نصب"),
            "material_details": _("جزئیات متریال"),
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "material_details": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self.fields["price_kind"].initial = PriceKind.ESTIMATE
        self.fields["installation_cost"].help_text = _(
            "مبلغ نصب جدا از ساخت است و در مجموع حساب می‌شود. "
            "اگر نصب در هزینه ساخت است، صفر وارد کنید و در توضیحات بنویسید."
        )
        self.fields["material_details"].label = _("جنس، اندازه و اقلام شامل قیمت")
        self.fields["material_details"].help_text = _(
            "نوع حروف، زمینه و زیرسازی؛ "
            "هزینه‌های خارج از پیشنهاد مثل حمل یا تجهیزات نصب را مشخص کنید."
        )
