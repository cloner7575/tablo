from django.contrib import admin

from apps.portfolio.models import PortfolioItem, PortfolioMedia


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
    search_fields = ("title", "vendor__business_name")
    prepopulated_fields = {"slug": ("title",)}
    list_select_related = ("vendor", "service", "city")
    inlines = [PortfolioMediaInline]
