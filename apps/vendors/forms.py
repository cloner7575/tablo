from __future__ import annotations

from django import forms
from django.utils.translation import gettext_lazy as _

from apps.catalog.models import Service
from apps.common.validators import validate_uploaded_image
from apps.vendors.models import Vendor


class VendorOnboardingForm(forms.ModelForm):
    services = forms.ModelMultipleChoiceField(
        queryset=Service.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple,
        label=_("خدمات"),
    )

    class Meta:
        model = Vendor
        fields = [
            "business_name",
            "description",
            "phone",
            "city",
            "address",
            "instagram",
            "website",
            "years_of_experience",
            "logo",
            "services",
        ]
        labels = {
            "business_name": _("نام کسب‌وکار"),
            "description": _("توضیحات"),
            "phone": _("تلفن"),
            "city": _("شهر"),
            "address": _("آدرس"),
            "instagram": _("اینستاگرام"),
            "website": _("وب‌سایت"),
            "years_of_experience": _("سال تجربه"),
            "logo": _("لوگو"),
        }

    def clean_logo(self):
        logo = self.cleaned_data.get("logo")
        if logo:
            validate_uploaded_image(logo)
        return logo


class VendorProfileForm(VendorOnboardingForm):
    class Meta(VendorOnboardingForm.Meta):
        fields = VendorOnboardingForm.Meta.fields + ["cover_image"]
        labels = {
            **VendorOnboardingForm.Meta.labels,
            "cover_image": _("تصویر کاور"),
        }

    def clean_cover_image(self):
        cover = self.cleaned_data.get("cover_image")
        if cover:
            validate_uploaded_image(cover)
        return cover
