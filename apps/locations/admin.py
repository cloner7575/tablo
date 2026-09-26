from django.contrib import admin

from apps.locations.models import City, Province


@admin.register(Province)
class ProvinceAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "province", "is_active")
    list_filter = ("province", "is_active")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)
    list_select_related = ("province",)
