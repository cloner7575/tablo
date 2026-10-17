from __future__ import annotations

import math

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import QuerySet
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from apps.common.models import TimeStampedModel
from apps.common.validators import validate_uploaded_image


class PublicationStatus(models.TextChoices):
    DRAFT = 'draft', _('پیش‌نویس')
    PUBLISHED = 'published', _('منتشرشده')


class CategoryKind(models.TextChoices):
    BUSINESS = 'business', _('نوع کسب‌وکار')
    GUIDE = 'guide', _('موضوع مقاله')


class IdeaSource(models.TextChoices):
    AI = 'ai', _('ایده با هوش مصنوعی')
    CONCEPT = 'concept', _('طرح مفهومی')
    EXECUTED = 'executed', _('نمونهٔ اجراشده')


class IdeaStyle(models.TextChoices):
    MODERN = 'modern', _('مدرن')
    MINIMAL = 'minimal', _('مینیمال')
    CLASSIC = 'classic', _('کلاسیک')
    LUXURY = 'luxury', _('لوکس')
    INDUSTRIAL = 'industrial', _('صنعتی')


class PublishedQuerySet(models.QuerySet):
    def published(self) -> PublishedQuerySet:
        return self.filter(
            status=PublicationStatus.PUBLISHED,
            published_at__lte=timezone.now(),
            category__is_active=True,
        )


def available_slug(queryset: QuerySet, title: str) -> str:
    base = slugify(title, allow_unicode=True)[:200] or 'content'
    candidate = base
    number = 1
    while queryset.filter(slug=candidate).exists():
        number += 1
        candidate = f'{base}-{number}'
    return candidate


class Category(TimeStampedModel):
    name = models.CharField(_('نام'), max_length=100)
    slug = models.SlugField(_('نشانی'), max_length=120, unique=True, allow_unicode=True)
    description = models.TextField(_('توضیح'), blank=True)
    kind = models.CharField(_('نوع دسته'), max_length=20, choices=CategoryKind.choices)
    is_active = models.BooleanField(_('فعال'), default=True)
    sort_order = models.PositiveSmallIntegerField(_('ترتیب'), default=0)

    class Meta:
        ordering = ['sort_order', 'name']
        verbose_name = _('دستهٔ محتوا')
        verbose_name_plural = _('دسته‌های محتوا')

    def __str__(self) -> str:
        return self.name


class Idea(TimeStampedModel):
    title = models.CharField(_('عنوان ایده'), max_length=200)
    slug = models.SlugField(
        _('نشانی صفحه'), max_length=220, unique=True, allow_unicode=True, blank=True
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='ideas',
        verbose_name=_('مناسب برای کسب‌وکار'),
    )
    service = models.ForeignKey(
        'catalog.Service',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inspiration_ideas',
        verbose_name=_('نوع تابلو'),
    )
    image = models.ImageField(
        _('تصویر اصلی'),
        upload_to='inspiration/originals/',
        validators=[validate_uploaded_image],
    )
    thumbnail = models.ImageField(
        _('تصویر بهینه'), upload_to='inspiration/previews/', blank=True, editable=False
    )
    image_alt = models.CharField(_('توصیف تصویر'), max_length=250, blank=True)
    description = models.TextField(_('توضیح ایده'), blank=True)
    design_notes = models.TextField(
        _('نکته‌های طراحی'), blank=True, help_text=_('هر نکته را در یک خط بنویسید.')
    )
    source = models.CharField(
        _('نوع تصویر'), max_length=20, choices=IdeaSource.choices, default=IdeaSource.AI
    )
    style = models.CharField(
        _('سبک طراحی'),
        max_length=20,
        choices=IdeaStyle.choices,
        default=IdeaStyle.MODERN,
    )
    seo_title = models.CharField(_('عنوان سئو'), max_length=200, blank=True)
    meta_description = models.CharField(_('توضیحات سئو'), max_length=320, blank=True)
    status = models.CharField(
        _('وضعیت انتشار'),
        max_length=20,
        choices=PublicationStatus.choices,
        default=PublicationStatus.DRAFT,
    )
    published_at = models.DateTimeField(_('تاریخ انتشار'), null=True, blank=True)
    is_featured = models.BooleanField(_('منتخب گالری'), default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='editorial_ideas',
        verbose_name=_('ثبت‌کننده'),
    )

    objects = PublishedQuerySet.as_manager()

    class Meta:
        ordering = ['-is_featured', '-published_at', '-pk']
        verbose_name = _('ایدهٔ تابلو')
        verbose_name_plural = _('ایده‌های تابلو')
        indexes = [
            models.Index(fields=['status', '-published_at']),
            models.Index(fields=['category', 'style', 'status']),
        ]

    def __str__(self) -> str:
        return self.title

    def get_absolute_url(self) -> str:
        return reverse('editorial:idea', kwargs={'slug': self.slug})

    @property
    def display_image_url(self) -> str:
        return self.thumbnail.url if self.thumbnail else self.image.url

    @property
    def is_concept(self) -> bool:
        return self.source != IdeaSource.EXECUTED

    def clean(self) -> None:
        super().clean()
        errors = {}
        if self.category_id and self.category.kind != CategoryKind.BUSINESS:
            errors['category'] = _('یک دسته از نوع کسب‌وکار انتخاب کنید.')
        if self.status == PublicationStatus.PUBLISHED:
            for field in ('image', 'image_alt', 'description', 'meta_description'):
                if not getattr(self, field):
                    errors[field] = _('برای انتشار، این بخش را تکمیل کنید.')
        if errors:
            raise ValidationError(errors)

    def save(self, *args: object, **kwargs: object) -> None:
        if not self.slug:
            self.slug = available_slug(Idea.objects.exclude(pk=self.pk), self.title)
        if self.status == PublicationStatus.PUBLISHED and self.published_at is None:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)


class Article(TimeStampedModel):
    title = models.CharField(_('عنوان مقاله'), max_length=200)
    slug = models.SlugField(
        _('نشانی صفحه'), max_length=220, unique=True, allow_unicode=True, blank=True
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='articles',
        verbose_name=_('موضوع مقاله'),
    )
    excerpt = models.CharField(_('خلاصهٔ مقاله'), max_length=500, blank=True)
    body = models.TextField(
        _('متن مقاله'),
        blank=True,
        help_text=_(
            'برای عنوان هر بخش از ## استفاده کنید؛ '
            'بین پاراگراف‌ها یک خط خالی بگذارید. متن HTML اجرا نمی‌شود.'
        ),
    )
    image = models.ImageField(
        _('تصویر شاخص'),
        upload_to='articles/originals/',
        blank=True,
        validators=[validate_uploaded_image],
    )
    thumbnail = models.ImageField(
        _('تصویر بهینه'), upload_to='articles/previews/', blank=True, editable=False
    )
    image_alt = models.CharField(_('توصیف تصویر شاخص'), max_length=250, blank=True)
    image_caption = models.CharField(_('زیرنویس تصویر'), max_length=250, blank=True)
    author_name = models.CharField(
        _('نام نویسنده'),
        max_length=100,
        blank=True,
        help_text=_('خالی باشد، مقاله به نام تحریریهٔ سایت نمایش داده می‌شود.'),
    )
    author_bio = models.CharField(_('معرفی نویسنده'), max_length=500, blank=True)
    seo_title = models.CharField(_('عنوان سئو'), max_length=200, blank=True)
    meta_description = models.CharField(_('توضیحات سئو'), max_length=320, blank=True)
    service = models.ForeignKey(
        'catalog.Service',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='editorial_articles',
        verbose_name=_('خدمت مرتبط'),
    )
    related_ideas = models.ManyToManyField(
        Idea, blank=True, related_name='articles', verbose_name=_('ایده‌های مرتبط')
    )
    status = models.CharField(
        _('وضعیت انتشار'),
        max_length=20,
        choices=PublicationStatus.choices,
        default=PublicationStatus.DRAFT,
    )
    published_at = models.DateTimeField(_('تاریخ انتشار'), null=True, blank=True)
    is_featured = models.BooleanField(_('مقالهٔ منتخب'), default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='editorial_articles',
        verbose_name=_('ثبت‌کننده'),
    )

    objects = PublishedQuerySet.as_manager()

    class Meta:
        ordering = ['-is_featured', '-published_at', '-pk']
        verbose_name = _('مقاله')
        verbose_name_plural = _('مقاله‌ها')
        indexes = [models.Index(fields=['status', '-published_at'])]

    def __str__(self) -> str:
        return self.title

    def get_absolute_url(self) -> str:
        return reverse('editorial:article', kwargs={'slug': self.slug})

    @property
    def reading_minutes(self) -> int:
        return max(1, math.ceil(len(self.body.split()) / 200))

    @property
    def display_image_url(self) -> str:
        if not self.image:
            return ''
        return self.thumbnail.url if self.thumbnail else self.image.url

    def clean(self) -> None:
        super().clean()
        errors = {}
        if self.category_id and self.category.kind != CategoryKind.GUIDE:
            errors['category'] = _('یک دسته از نوع موضوع مقاله انتخاب کنید.')
        if self.status == PublicationStatus.PUBLISHED:
            for field in ('excerpt', 'body', 'image', 'image_alt', 'meta_description'):
                if not getattr(self, field):
                    errors[field] = _('برای انتشار، این بخش را تکمیل کنید.')
        if errors:
            raise ValidationError(errors)

    def save(self, *args: object, **kwargs: object) -> None:
        if not self.slug:
            self.slug = available_slug(Article.objects.exclude(pk=self.pk), self.title)
        if self.status == PublicationStatus.PUBLISHED and self.published_at is None:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)


class SavedReference(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="saved_signs"
    )
    idea = models.ForeignKey(Idea, on_delete=models.CASCADE, null=True, blank=True)
    portfolio_item = models.ForeignKey(
        "portfolio.PortfolioItem", on_delete=models.CASCADE, null=True, blank=True
    )

    class Meta:
        verbose_name = _("تصویر ذخیره‌شده")
        verbose_name_plural = _("تصاویر ذخیره‌شده")
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(idea__isnull=False, portfolio_item__isnull=True)
                    | models.Q(idea__isnull=True, portfolio_item__isnull=False)
                ),
                name="saved_reference_one_target",
            ),
            models.UniqueConstraint(
                fields=["user", "idea"], name="saved_reference_unique_idea"
            ),
            models.UniqueConstraint(
                fields=["user", "portfolio_item"],
                name="saved_reference_unique_portfolio",
            ),
        ]
