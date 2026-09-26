from __future__ import annotations

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apps.accounts.services import validate_phone


class LoginForm(AuthenticationForm):
    username = forms.CharField(label=_("نام کاربری"))
    password = forms.CharField(label=_("رمز عبور"), widget=forms.PasswordInput)


class PhoneRequestOTPForm(forms.Form):
    phone = forms.CharField(
        label=_("شماره موبایل"),
        max_length=15,
        widget=forms.TextInput(
            attrs={
                "inputmode": "tel",
                "autocomplete": "tel",
                "dir": "ltr",
                "placeholder": "09121234567",
            }
        ),
    )

    def clean_phone(self) -> str:
        return validate_phone(self.cleaned_data["phone"])


class PhoneVerifyOTPForm(forms.Form):
    phone = forms.CharField(widget=forms.HiddenInput)
    code = forms.CharField(
        label=_("کد تأیید"),
        max_length=6,
        widget=forms.TextInput(
            attrs={
                "inputmode": "numeric",
                "autocomplete": "one-time-code",
                "dir": "ltr",
                "placeholder": "123456",
            }
        ),
    )

    def clean_phone(self) -> str:
        return validate_phone(self.cleaned_data["phone"])

    def clean_code(self) -> str:
        code = (
            self.cleaned_data["code"]
            .strip()
            .translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789"))
        )
        if not code.isdigit() or len(code) != 6:
            raise ValidationError(_("کد باید ۶ رقم باشد."))
        return code
