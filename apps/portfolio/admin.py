from django import forms
from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from apps.portfolio.models import PortfolioItem, PortfolioMedia
from apps.portfolio.services import delete_item, update_item


class PortfolioMediaInline(admin.TabularInline):
    model = PortfolioMedia
    extra = 0
    fields = (
        "sort_order",
        "kind",
        "image",
        "video",
        "poster",
        "aparat_hash",
        "caption",
    )
    ordering = ("sort_order", "id")


@admin.register(PortfolioItem)
class PortfolioItemAdmin(admin.ModelAdmin):
    list_display = ("title", "vendor", "service", "city", "is_published", "created_at")
    list_filter = ("is_published", "service", "city")
    search_fields = ("title", "vendor__business_name", "source_name")
    prepopulated_fields = {"slug": ("title",)}
    list_select_related = ("vendor", "service", "city")
    inlines = [PortfolioMediaInline]

    def save_model(
        self,
        request: HttpRequest,
        obj: PortfolioItem,
        form: forms.ModelForm,
        change: bool,
    ) -> None:
        if change:
            update_item(item=obj)
        else:
            super().save_model(request, obj, form, change)

    def delete_model(self, request: HttpRequest, obj: PortfolioItem) -> None:
        delete_item(item=obj)

    def delete_queryset(
        self, request: HttpRequest, queryset: QuerySet[PortfolioItem]
    ) -> None:
        for item in queryset.prefetch_related("media"):
            delete_item(item=item)
