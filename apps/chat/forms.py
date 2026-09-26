from __future__ import annotations

from django import forms
from django.utils.translation import gettext_lazy as _


class ChatImageUploadForm(forms.Form):
    image = forms.ImageField(
        label=_("تصویر"),
        required=True,
        widget=forms.ClearableFileInput(
            attrs={
                "accept": "image/*",
                "class": "chat-composer__file",
            }
        ),
    )
    body = forms.CharField(
        label=_("توضیح"),
        required=False,
        max_length=4000,
        widget=forms.TextInput(
            attrs={
                "placeholder": _("توضیح اختیاری برای عکس"),
                "class": "chat-composer__input",
            }
        ),
    )
