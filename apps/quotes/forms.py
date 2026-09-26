from __future__ import annotations

from django import forms
from django.utils.translation import gettext_lazy as _

from apps.quotes.models import Quote


class QuoteForm(forms.ModelForm):
    class Meta:
        model = Quote
        fields = [
            "price",
            "estimated_delivery_days",
            "description",
            "warranty",
            "installation_cost",
            "material_details",
        ]
        labels = {
            "price": _("قیمت (تومان)"),
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
