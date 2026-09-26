from django.contrib import admin

from apps.portfolio.models import PortfolioItem


@admin.register(PortfolioItem)
class PortfolioItemAdmin(admin.ModelAdmin):
    list_display = ("title", "vendor", "service", "city", "is_published", "created_at")
    list_filter = ("is_published", "service", "city")
    search_fields = ("title", "vendor__business_name")
    prepopulated_fields = {"slug": ("title",)}
    list_select_related = ("vendor", "service", "city")
