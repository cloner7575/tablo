from __future__ import annotations

import logging
import re

from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

from apps.accounts.models import UserRole
from apps.accounts.otp import PhoneOTP
from apps.accounts.sms import get_sms_provider

logger = logging.getLogger(__name__)
User = get_user_model()

PHONE_RE = re.compile(r"^09\d{9}$")


def normalize_phone(raw: str) -> str:
    phone = (raw or "").strip().translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789"))
    phone = phone.replace("+98", "0").replace(" ", "").replace("-", "")
    if phone.startswith("989") and len(phone) == 12:
        phone = "0" + phone[2:]
    return phone


def validate_phone(phone: str) -> str:
    normalized = normalize_phone(phone)
    if not PHONE_RE.match(normalized):
        raise ValidationError(_("شماره موبایل معتبر نیست. مثال: ۰۹۱۲۱۲۳۴۵۶۷"))
    return normalized


def _otp_send_cache_key(phone: str) -> str:
    return f"otp:send:{phone}"


def _otp_verify_cache_key(phone: str) -> str:
    return f"otp:verify:{phone}"


@transaction.atomic
def request_otp(*, phone: str, purpose: str = "login") -> PhoneOTP:
    phone = validate_phone(phone)
    send_limit = getattr(settings, "OTP_SEND_LIMIT", 5)
    window = getattr(settings, "OTP_SEND_WINDOW_SECONDS", 3600)
    key = _otp_send_cache_key(phone)
    count = cache.get(key, 0)
    if count >= send_limit:
        raise ValidationError(
            _("تعداد درخواست کد بیش از حد مجاز است. کمی بعد تلاش کنید.")
        )

    otp = PhoneOTP.create_for_phone(phone=phone, purpose=purpose)
    provider = get_sms_provider()
    provider.send(phone, f"کد ورود تابلو دات کام: {otp.code}")
    cache.set(key, count + 1, timeout=window)
    logger.info("OTP requested phone=%s purpose=%s", phone, purpose)
    return otp


@transaction.atomic
def verify_otp_and_login(
    *,
    request: HttpRequest,
    phone: str,
    code: str,
    purpose: str = "login",
    role: str = UserRole.CUSTOMER,
) -> User:
    phone = validate_phone(phone)
    code = (code or "").strip().translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789"))

    verify_limit = getattr(settings, "OTP_VERIFY_LIMIT", 10)
    window = getattr(settings, "OTP_VERIFY_WINDOW_SECONDS", 3600)
    vkey = _otp_verify_cache_key(phone)
    vcount = cache.get(vkey, 0)
    if vcount >= verify_limit:
        raise ValidationError(_("تعداد تلاش برای تأیید کد بیش از حد مجاز است."))

    otp = (
        PhoneOTP.objects.filter(phone=phone, purpose=purpose, is_used=False)
        .order_by("-created_at")
        .first()
    )
    if otp is None:
        cache.set(vkey, vcount + 1, timeout=window)
        raise ValidationError(_("کد معتبری یافت نشد. دوباره درخواست کنید."))

    if otp.is_expired:
        cache.set(vkey, vcount + 1, timeout=window)
        raise ValidationError(_("کد منقضی شده است. دوباره درخواست کنید."))

    max_attempts = getattr(settings, "OTP_MAX_ATTEMPTS", 5)
    if otp.attempts >= max_attempts:
        raise ValidationError(_("تعداد تلاش‌ها تمام شده است. کد جدید بگیرید."))

    if otp.code != code:
        otp.attempts += 1
        otp.save(update_fields=["attempts", "updated_at"])
        cache.set(vkey, vcount + 1, timeout=window)
        raise ValidationError(_("کد وارد شده نادرست است."))

    otp.mark_used()
    user, created = User.objects.get_or_create(
        phone=phone,
        defaults={
            "username": phone,
            "role": role,
            "is_verified": True,
        },
    )
    if not created and not user.is_verified:
        user.is_verified = True
        user.save(update_fields=["is_verified"])

    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    return user
