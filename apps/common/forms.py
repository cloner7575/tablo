"""Form fields shared across apps."""

from __future__ import annotations

from django import forms
from django.core.files.uploadedfile import UploadedFile


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleImageField(forms.ImageField):
    """An ``ImageField`` that accepts several files and cleans to a list."""

    def clean(
        self,
        data: UploadedFile | list[UploadedFile] | None,
        initial: object | None = None,
    ) -> list[UploadedFile]:
        single_clean = super().clean
        if isinstance(data, (list, tuple)):
            if not data:
                return []
            return [single_clean(item, initial) for item in data if item]
        if data in self.empty_values:
            return []
        return [single_clean(data, initial)]
