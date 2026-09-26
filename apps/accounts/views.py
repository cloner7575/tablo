from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.core.exceptions import ValidationError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_http_methods

from apps.accounts.forms import LoginForm, PhoneRequestOTPForm, PhoneVerifyOTPForm
from apps.accounts.models import UserRole
from apps.accounts.services import request_otp, verify_otp_and_login
from apps.analytics.services import track


class LoginView(auth_views.LoginView):
    template_name = "registration/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True


class PasswordChangeView(auth_views.PasswordChangeView):
    template_name = "registration/password_change_form.html"
    success_url = reverse_lazy("accounts:password_change_done")


class PasswordChangeDoneView(auth_views.PasswordChangeDoneView):
    template_name = "registration/password_change_done.html"


class PasswordResetView(auth_views.PasswordResetView):
    template_name = "registration/password_reset_form.html"
    email_template_name = "registration/password_reset_email.html"
    subject_template_name = "registration/password_reset_subject.txt"
    success_url = reverse_lazy("accounts:password_reset_done")


class PasswordResetDoneView(auth_views.PasswordResetDoneView):
    template_name = "registration/password_reset_done.html"


class PasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    template_name = "registration/password_reset_confirm.html"
    success_url = reverse_lazy("accounts:password_reset_complete")


class PasswordResetCompleteView(auth_views.PasswordResetCompleteView):
    template_name = "registration/password_reset_complete.html"


@require_http_methods(["GET", "POST"])
def phone_login(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("common:home")

    form = PhoneRequestOTPForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            request_otp(phone=form.cleaned_data["phone"], purpose="login")
        except ValidationError as exc:
            form.add_error("phone", exc.message)
        else:
            messages.success(request, "کد تأیید ارسال شد.")
            return redirect("accounts:phone_verify", phone=form.cleaned_data["phone"])
    return render(request, "registration/phone_login.html", {"form": form})


@require_http_methods(["GET", "POST"])
def phone_verify(request: HttpRequest, phone: str) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("common:home")

    initial = {"phone": phone}
    form = PhoneVerifyOTPForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        try:
            user = verify_otp_and_login(
                request=request,
                phone=form.cleaned_data["phone"],
                code=form.cleaned_data["code"],
                purpose="login",
                role=UserRole.CUSTOMER,
            )
        except ValidationError as exc:
            form.add_error("code", exc.message)
        else:
            messages.success(request, "با موفقیت وارد شدید.")
            next_url = request.GET.get("next") or "common:home"
            if user.is_vendor_user:
                return redirect("vendors:dashboard")
            return redirect(next_url)
    return render(
        request,
        "registration/phone_verify.html",
        {"form": form, "phone": phone},
    )


@require_http_methods(["GET", "POST"])
def vendor_register(request: HttpRequest) -> HttpResponse:
    """Step 1 of vendor onboarding — phone OTP then profile form."""
    track("vendor_register_started", {})
    form = PhoneRequestOTPForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            request_otp(phone=form.cleaned_data["phone"], purpose="vendor_register")
        except ValidationError as exc:
            form.add_error("phone", exc.message)
        else:
            return redirect("accounts:vendor_verify", phone=form.cleaned_data["phone"])
    return render(request, "registration/vendor_register.html", {"form": form})


@require_http_methods(["GET", "POST"])
def vendor_verify(request: HttpRequest, phone: str) -> HttpResponse:
    form = PhoneVerifyOTPForm(request.POST or None, initial={"phone": phone})
    if request.method == "POST" and form.is_valid():
        try:
            user = verify_otp_and_login(
                request=request,
                phone=form.cleaned_data["phone"],
                code=form.cleaned_data["code"],
                purpose="vendor_register",
                role=UserRole.VENDOR,
            )
            if user.role != UserRole.VENDOR:
                user.role = UserRole.VENDOR
                user.save(update_fields=["role"])
        except ValidationError as exc:
            form.add_error("code", exc.message)
        else:
            return redirect("vendors:onboarding")
    return render(
        request,
        "registration/vendor_verify.html",
        {"form": form, "phone": phone},
    )
