from __future__ import annotations

from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from apps.common.models import TimeStampedModel


class Province(TimeStampedModel):
    name = models.CharField(_("نام"), max_length=100)
    slug = models.SlugField(_("اسلاگ"), max_length=120, unique=True, allow_unicode=True)
    is_active = models.BooleanField(_("فعال"), default=True)

    class Meta:
        db_table = "provinces"
        ordering = ["name"]
        verbose_name = _("استان")
        verbose_name_plural = _("استان‌ها")

    def __str__(self) -> str:
        return self.name

    def save(self, *args: object, **kwargs: object) -> None:
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)


class City(TimeStampedModel):
    name = models.CharField(_("نام"), max_length=100)
    slug = models.SlugField(_("اسلاگ"), max_length=120, unique=True, allow_unicode=True)
    province = models.ForeignKey(
        Province,
        on_delete=models.PROTECT,
        related_name="cities",
        verbose_name=_("استان"),
    )
    is_active = models.BooleanField(_("فعال"), default=True)

    class Meta:
        db_table = "cities"
        ordering = ["name"]
        verbose_name = _("شهر")
        verbose_name_plural = _("شهرها")
        indexes = [
            models.Index(fields=["is_active", "slug"]),
        ]

    def __str__(self) -> str:
        return self.name

    def save(self, *args: object, **kwargs: object) -> None:
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)
