from django.contrib import admin

from apps.catalog.models import CityServicePage, Service


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "is_active", "sort_order")
    list_editable = ("is_active", "sort_order")
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ("title",)


@admin.register(CityServicePage)
class CityServicePageAdmin(admin.ModelAdmin):
    list_display = ("title", "city", "service", "is_published")
    list_filter = ("is_published", "city", "service")
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ("title", "body")
    list_select_related = ("city", "service")
