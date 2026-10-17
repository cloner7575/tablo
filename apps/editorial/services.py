"""Image preparation for editorial uploads; no external services."""

from __future__ import annotations

import io
import uuid
from typing import TYPE_CHECKING

from django.core.files.base import ContentFile
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
from PIL import Image, ImageOps

from apps.accounts.models import User
from apps.editorial.models import Article, Idea

if TYPE_CHECKING:
    from apps.editorial.forms import ArticleForm, IdeaForm


def image_preview(file: UploadedFile) -> ContentFile:
    file.seek(0)
    with Image.open(file) as original:
        preview = ImageOps.exif_transpose(original)
        preview.thumbnail((1000, 1000), Image.Resampling.LANCZOS)
        preview = preview.convert('RGBA' if 'A' in preview.getbands() else 'RGB')
        output = io.BytesIO()
        preview.save(output, format='WEBP', quality=84, method=4)
    file.seek(0)
    return ContentFile(output.getvalue(), name=f'{uuid.uuid4().hex}.webp')


@transaction.atomic
def save_content(*, form: IdeaForm | ArticleForm, actor: User) -> Idea | Article:
    item = form.save(commit=False)
    if not item.created_by_id:
        item.created_by = actor
    item.save()
    form.save_m2m()
    return item
