from __future__ import annotations

from django import forms
from django.utils.translation import gettext_lazy as _

from apps.catalog.models import Service
from apps.common.validators import validate_uploaded_image
from apps.locations.models import City
from apps.requests.models import LightingType


class RequestWizardServiceForm(forms.Form):
    service = forms.ModelChoiceField(
        label=_("نوع تابلو"),
        queryset=Service.objects.filter(is_active=True),
    )


class RequestWizardCityForm(forms.Form):
    city = forms.ModelChoiceField(
        label=_("شهر"),
        queryset=City.objects.filter(is_active=True),
    )


class RequestWizardDimensionsForm(forms.Form):
    width_cm = forms.IntegerField(
        label=_("عرض (سانتی‌متر)"), min_value=10, max_value=5000
    )
    height_cm = forms.IntegerField(
        label=_("ارتفاع (سانتی‌متر)"), min_value=10, max_value=2000
    )


class RequestWizardLightingForm(forms.Form):
    lighting_type = forms.ChoiceField(
        label=_("نورپردازی"),
        choices=LightingType.choices,
    )


class RequestWizardDescriptionForm(forms.Form):
    description = forms.CharField(
        label=_("توضیحات پروژه"),
        widget=forms.Textarea(attrs={"rows": 4}),
        required=False,
    )
    text_content = forms.CharField(label=_("متن تابلو"), required=False)
    business_type = forms.CharField(label=_("نوع کسب‌وکار"), required=False)
    district = forms.CharField(label=_("محله"), required=False)


class RequestWizardImageForm(forms.Form):
    image = forms.ImageField(label=_("عکس محل نصب"), required=False)

    def clean_image(self):
        image = self.cleaned_data.get("image")
        if image:
            validate_uploaded_image(image)
        return image


class RequestWizardBudgetForm(forms.Form):
    budget_min = forms.IntegerField(
        label=_("حداقل بودجه (تومان)"), required=False, min_value=0
    )
    budget_max = forms.IntegerField(
        label=_("حداکثر بودجه (تومان)"), required=False, min_value=0
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
