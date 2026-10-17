from __future__ import annotations

from django import forms
from django.core.files.uploadedfile import UploadedFile
from django.db.models import Q
from django.db.models.fields.files import FieldFile
from django.utils.translation import gettext_lazy as _

from apps.common.validators import validate_uploaded_image
from apps.editorial.models import Article, Category, CategoryKind, Idea
from apps.editorial.services import image_preview


class IdeaForm(forms.ModelForm):
    class Meta:
        model = Idea
        fields = (
            'title',
            'slug',
            'category',
            'service',
            'image',
            'image_alt',
            'description',
            'design_notes',
            'source',
            'style',
            'seo_title',
            'meta_description',
            'is_featured',
            'status',
        )
        widgets = {
            'image': forms.ClearableFileInput(
                attrs={
                    'accept': 'image/jpeg,image/png,image/webp',
                    'data-multi-preview': 'true',
                }
            ),
            'description': forms.Textarea(attrs={'rows': 4}),
            'design_notes': forms.Textarea(attrs={'rows': 4}),
            'meta_description': forms.Textarea(attrs={'rows': 3}),
        }
        help_texts = {
            'slug': _('اختیاری؛ از عنوان ساخته می‌شود. پس از اولین انتشار ثابت می‌ماند.'),
            'image_alt': _('آنچه در تصویر دیده می‌شود را دقیق و کوتاه توصیف کنید.'),
            'meta_description': _('خلاصه‌ای اختصاصی دربارهٔ این ایده برای نتیجهٔ جست‌وجو.'),
        }

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self.fields['category'].empty_label = _('نوع کسب‌وکار را انتخاب کنید')
        self.fields['service'].empty_label = _('بدون نوع تابلو مشخص')
        self.fields['category'].queryset = Category.objects.filter(
            kind=CategoryKind.BUSINESS
        ).filter(Q(is_active=True) | Q(pk=self.instance.category_id))
        self.fields['service'].queryset = self.fields['service'].queryset.filter(
            is_active=True
        )
        if self.instance.published_at:
            self.fields['slug'].disabled = True

    def clean_image(self) -> UploadedFile | FieldFile | bool | None:
        image = self.cleaned_data.get('image')
        if image:
            validate_uploaded_image(image)
        return image

    def save(self, commit: bool = True) -> Idea:
        instance = super().save(commit=False)
        upload = self.cleaned_data.get('image')
        if 'image' in self.changed_data and upload:
            instance.thumbnail = image_preview(upload)
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = (
            'title',
            'slug',
            'category',
            'excerpt',
            'body',
            'image',
            'image_alt',
            'image_caption',
            'author_name',
            'author_bio',
            'service',
            'related_ideas',
            'seo_title',
            'meta_description',
            'is_featured',
            'status',
        )
        widgets = {
            'image': forms.ClearableFileInput(
                attrs={
                    'accept': 'image/jpeg,image/png,image/webp',
                    'data-multi-preview': 'true',
                }
            ),
            'excerpt': forms.Textarea(attrs={'rows': 3}),
            'body': forms.Textarea(attrs={'rows': 18}),
            'meta_description': forms.Textarea(attrs={'rows': 3}),
            'related_ideas': forms.CheckboxSelectMultiple,
        }
        help_texts = {
            'slug': _('اختیاری؛ پس از اولین انتشار ثابت می‌ماند.'),
            'meta_description': _('خلاصهٔ اختصاصی و دقیق مقاله برای نتیجهٔ جست‌وجو.'),
        }

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self.fields['category'].empty_label = _('موضوع مقاله را انتخاب کنید')
        self.fields['service'].empty_label = _('بدون خدمت مرتبط')
        self.fields['category'].queryset = Category.objects.filter(
            kind=CategoryKind.GUIDE
        ).filter(Q(is_active=True) | Q(pk=self.instance.category_id))
        self.fields['service'].queryset = self.fields['service'].queryset.filter(
            is_active=True
        )
        self.fields['related_ideas'].queryset = Idea.objects.published().select_related(
            'category'
        )
        if self.instance.published_at:
            self.fields['slug'].disabled = True

    def clean_image(self) -> UploadedFile | FieldFile | bool | None:
        image = self.cleaned_data.get('image')
        if image:
            validate_uploaded_image(image)
        return image

    def save(self, commit: bool = True) -> Article:
        instance = super().save(commit=False)
        upload = self.cleaned_data.get('image')
        if 'image' in self.changed_data:
            instance.thumbnail = image_preview(upload) if upload else ''
        if commit:
            instance.save()
            self.save_m2m()
        return instance
