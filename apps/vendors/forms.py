from __future__ import annotations

from django import forms
from django.utils.translation import gettext_lazy as _

from apps.catalog.models import Service
from apps.common.validators import validate_uploaded_image
from apps.locations.models import City
from apps.vendors.models import Vendor


class VendorSearchForm(forms.Form):
    q = forms.CharField(
        label=_("جست‌وجوی تابلوساز"),
        required=False,
        max_length=80,
        widget=forms.TextInput(
            attrs={"type": "search", "placeholder": _("نام مجموعه یا تخصص")}
        ),
    )
    city = forms.ModelChoiceField(
        label=_("شهر"),
        queryset=City.objects.filter(is_active=True),
        to_field_name="slug",
        required=False,
        empty_label=_("همهٔ شهرها"),
    )
    service = forms.ModelChoiceField(
        label=_("نوع تابلو"),
        queryset=Service.objects.filter(is_active=True),
        to_field_name="slug",
        required=False,
        empty_label=_("همهٔ خدمات"),
    )
    sort = forms.ChoiceField(
        label=_("مرتب‌سازی"),
        required=False,
        choices=(
            ("", _("پیشنهادی")),
            ("rating", _("بالاترین امتیاز")),
            ("experience", _("بیشترین تجربه")),
        ),
    )


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
            "cover_image",
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
            "cover_image": _("تصویر کاور"),
        }

    def clean_logo(self):
        logo = self.cleaned_data.get("logo")
        if logo:
            validate_uploaded_image(logo)
        return logo

    def clean_cover_image(self):
        cover = self.cleaned_data.get("cover_image")
        if cover:
            validate_uploaded_image(cover)
        return cover


class VendorProfileForm(VendorOnboardingForm):
    """Same fields as onboarding — kept for clear view naming."""


class QuoteWorkspaceFilterForm(forms.Form):
    q = forms.CharField(
        label=_("جست‌وجوی پروژه"),
        required=False,
        max_length=80,
        widget=forms.TextInput(attrs={"type": "search"}),
    )
    status = forms.ChoiceField(
        label=_("وضعیت پیشنهاد"),
        required=False,
        choices=(
            ("", _("همهٔ پیشنهادها")),
            ("pending", _("در انتظار تصمیم")),
            ("viewed", _("مشاهده‌شده")),
            ("accepted", _("پذیرفته‌شده")),
            ("rejected", _("انتخاب‌نشده")),
            ("expired", _("منقضی‌شده")),
        ),
    )


class ProjectWorkspaceFilterForm(forms.Form):
    q = forms.CharField(
        label=_("جست‌وجوی پروژه"),
        required=False,
        max_length=80,
        widget=forms.TextInput(attrs={"type": "search"}),
    )
    status = forms.ChoiceField(
        label=_("وضعیت اجرا"),
        required=False,
        choices=(
            ("", _("همهٔ پروژه‌ها")),
            ("active", _("در حال اجرا")),
            ("completed", _("تکمیل‌شده")),
            ("cancelled", _("لغوشده")),
        ),
    )


class RequestFeedSearchForm(forms.Form):
    q = forms.CharField(
        label=_("جست‌وجوی درخواست"),
        required=False,
        max_length=80,
        widget=forms.TextInput(
            attrs={"type": "search", "placeholder": _("نام پروژه، محله یا کسب‌وکار")}
        ),
    )
