from django import forms
from django.utils.translation import gettext_lazy as _


class ServiceSearchForm(forms.Form):
    q = forms.CharField(
        label=_("جست‌وجوی خدمت یا کسب‌وکار"),
        required=False,
        max_length=80,
        widget=forms.TextInput(
            attrs={"type": "search", "placeholder": _("مثلاً چلنیوم، کافه یا استیل")}
        ),
    )
