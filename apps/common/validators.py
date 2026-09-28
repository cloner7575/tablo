from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.utils.translation import gettext_lazy as _

WEBM_SIGNATURE = b"\x1a\x45\xdf\xa3"


def validate_uploaded_image(file: UploadedFile) -> None:
    max_bytes = getattr(settings, "IMAGE_UPLOAD_MAX_BYTES", 5 * 1024 * 1024)
    allowed = getattr(
        settings,
        "ALLOWED_IMAGE_CONTENT_TYPES",
        ("image/jpeg", "image/png", "image/webp"),
    )
    if file.size and file.size > max_bytes:
        raise ValidationError(_("حجم تصویر بیش از حد مجاز است."))
    content_type = getattr(file, "content_type", "") or ""
    if content_type and content_type not in allowed:
        raise ValidationError(_("فرمت تصویر مجاز نیست. JPEG، PNG یا WebP."))


def _looks_like_video(head: bytes) -> bool:
    return head[4:8] == b"ftyp" or head.startswith(WEBM_SIGNATURE)


def validate_uploaded_video(file: UploadedFile) -> None:
    """Size, declared type, and magic bytes — the browser's type is not trusted."""
    max_bytes = getattr(settings, "VIDEO_UPLOAD_MAX_BYTES", 50 * 1024 * 1024)
    allowed = getattr(
        settings, "ALLOWED_VIDEO_CONTENT_TYPES", ("video/mp4", "video/webm")
    )
    if file.size and file.size > max_bytes:
        limit_mb = max_bytes // (1024 * 1024) or 1
        raise ValidationError(
            _("حجم ویدیو بیش از %(mb)s مگابایت است.") % {"mb": limit_mb}
        )
    content_type = getattr(file, "content_type", "") or ""
    if content_type not in allowed:
        raise ValidationError(_("فرمت ویدیو مجاز نیست. فقط MP4 یا WebM."))
    file.seek(0)
    head = file.read(16)
    file.seek(0)
    if not _looks_like_video(head):
        raise ValidationError(_("فایل انتخاب‌شده ویدیوی معتبر MP4 یا WebM نیست."))
