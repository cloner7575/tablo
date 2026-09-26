from __future__ import annotations

from django import forms

from apps.common.validators import validate_uploaded_image
from apps.portfolio.models import PortfolioItem


class PortfolioForm(forms.ModelForm):
    class Meta:
        model = PortfolioItem
        fields = ["title", "description", "service", "city", "image"]

    def clean_image(self):
        image = self.cleaned_data.get("image")
        if image:
            validate_uploaded_image(image)
        return image
