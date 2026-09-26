from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.utils.translation import gettext_lazy as _


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
