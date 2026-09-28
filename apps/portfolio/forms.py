from __future__ import annotations

from collections.abc import Callable

from django import forms
from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from django.utils.translation import gettext_lazy as _

from apps.common.forms import MultipleFileInput, MultipleImageField
from apps.common.persian import to_persian_digits
from apps.common.validators import validate_uploaded_image, validate_uploaded_video
from apps.portfolio.models import PortfolioItem, parse_aparat_hash

IMAGE_ACCEPT = "image/jpeg,image/png,image/webp"
VIDEO_ACCEPT = "video/mp4,video/webm"


def max_media() -> int:
    return int(getattr(settings, "PORTFOLIO_MAX_MEDIA", 20))


def _gallery_field(label: str) -> MultipleImageField:
    return MultipleImageField(
        label=label,
        required=False,
        widget=MultipleFileInput(
            attrs={"accept": IMAGE_ACCEPT, "data-multi-preview": "true"}
        ),
        help_text=_("می‌توانید چند عکس را با هم انتخاب کنید. JPEG، PNG یا WebP."),
    )


def _video_field() -> forms.FileField:
    return forms.FileField(
        label=_("فایل ویدیو"),
        required=False,
        widget=forms.FileInput(
            attrs={"accept": VIDEO_ACCEPT, "data-multi-preview": "true"}
        ),
        help_text=_("MP4 یا WebM، کوتاه و افقی بهتر دیده می‌شود."),
    )


def _poster_field() -> forms.ImageField:
    return forms.ImageField(
        label=_("تصویر پیش‌نمایش (اختیاری)"),
        required=False,
        widget=forms.FileInput(attrs={"accept": IMAGE_ACCEPT}),
        help_text=_("قبل از پخش ویدیو نمایش داده می‌شود."),
    )


def _aparat_field() -> forms.CharField:
    return forms.CharField(
        label=_("لینک ویدیو در آپارات"),
        required=False,
        max_length=300,
        widget=forms.URLInput(
            attrs={
                "dir": "ltr",
                "inputmode": "url",
                "placeholder": "https://www.aparat.com/v/abc123",
            }
        ),
        help_text=_("لینک صفحه ویدیو یا کد embed آپارات را وارد کنید."),
    )


def _limit_error(limit: int, remaining: int) -> forms.ValidationError:
    return forms.ValidationError(
        _(
            "هر نمونه‌کار حداکثر %(limit)s رسانه دارد؛ "
            "فقط %(remaining)s جای خالی باقی مانده است."
        )
        % {
            "limit": to_persian_digits(limit),
            "remaining": to_persian_digits(remaining),
        }
    )


class VideoInputsMixin:
    """Validation for the video/poster/Aparat trio; the form declares the fields."""

    cleaned_data: dict[str, object]
    add_error: Callable[[str | None, object], None]

    def clean_video(self) -> UploadedFile | None:
        video = self.cleaned_data.get("video")
        if isinstance(video, UploadedFile):
            validate_uploaded_video(video)
        return video if isinstance(video, UploadedFile) else None

    def clean_poster(self) -> UploadedFile | None:
        poster = self.cleaned_data.get("poster")
        if isinstance(poster, UploadedFile):
            validate_uploaded_image(poster)
        return poster if isinstance(poster, UploadedFile) else None

    def clean_aparat_url(self) -> str:
        url = str(self.cleaned_data.get("aparat_url") or "").strip()
        if url:
            parse_aparat_hash(url)
        return url

    def _check_poster(self, cleaned: dict[str, object]) -> bool:
        if cleaned.get("poster") and not cleaned.get("video"):
            self.add_error("poster", _("تصویر پیش‌نمایش فقط همراه فایل ویدیو لازم است."))
            return False
        return True

    @staticmethod
    def _video_count(cleaned: dict[str, object]) -> int:
        return int(bool(cleaned.get("video"))) + int(bool(cleaned.get("aparat_url")))


class PortfolioForm(forms.ModelForm):
    class Meta:
        model = PortfolioItem
        fields = ["title", "description", "service", "city", "image", "is_published"]
        labels = {
            "service": _("نوع تابلو"),
            "city": _("شهر اجرا"),
            "image": _("عکس کاور"),
            "is_published": _("نمایش عمومی در سایت"),
        }
        help_texts = {
            "image": _("این عکس روی کارت‌ها و بالای گالری نمایش داده می‌شود."),
            "is_published": _("اگر خاموش باشد، فقط خودتان آن را می‌بینید."),
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "image": forms.FileInput(attrs={"accept": IMAGE_ACCEPT}),
        }

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self.fields["service"].empty_label = _("انتخاب نوع تابلو")
        self.fields["city"].empty_label = _("انتخاب شهر")

    def clean_image(self) -> UploadedFile | None:
        image = self.cleaned_data.get("image")
        if isinstance(image, UploadedFile):
            validate_uploaded_image(image)
        return image


class PortfolioCreateForm(VideoInputsMixin, PortfolioForm):
    gallery = _gallery_field(_("عکس‌های بیشتر از همین پروژه"))
    video = _video_field()
    poster = _poster_field()
    aparat_url = _aparat_field()

    def clean_gallery(self) -> list[UploadedFile]:
        files: list[UploadedFile] = self.cleaned_data.get("gallery") or []
        for uploaded in files:
            validate_uploaded_image(uploaded)
        return files

    def clean(self) -> dict[str, object]:
        cleaned = super().clean()
        if self.errors or not self._check_poster(cleaned):
            return cleaned
        gallery = cleaned.get("gallery") or []
        incoming = len(gallery) + self._video_count(cleaned)
        limit = max_media()
        if incoming > limit:
            raise _limit_error(limit, limit)
        return cleaned


class PortfolioMediaForm(VideoInputsMixin, forms.Form):
    images = _gallery_field(_("عکس‌ها"))
    video = _video_field()
    poster = _poster_field()
    aparat_url = _aparat_field()
    caption = forms.CharField(
        label=_("توضیح کوتاه (اختیاری)"),
        required=False,
        max_length=160,
        help_text=_("مثلاً «نمای شب بعد از نصب»."),
    )

    def __init__(self, *args: object, item: PortfolioItem, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self.item = item

    def clean_images(self) -> list[UploadedFile]:
        files: list[UploadedFile] = self.cleaned_data.get("images") or []
        for uploaded in files:
            validate_uploaded_image(uploaded)
        return files

    def clean(self) -> dict[str, object]:
        cleaned = super().clean()
        if self.errors or not self._check_poster(cleaned):
            return cleaned
        images = cleaned.get("images") or []
        incoming = len(images) + self._video_count(cleaned)
        if not incoming:
            raise forms.ValidationError(
                _("حداقل یک عکس، فایل ویدیو یا لینک آپارات انتخاب کنید.")
            )
        limit = max_media()
        remaining = max(limit - self.item.media.count(), 0)
        if incoming > remaining:
            raise _limit_error(limit, remaining)
        return cleaned
