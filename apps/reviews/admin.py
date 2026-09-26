from django.contrib import admin

from apps.reviews.models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("vendor", "customer", "rating", "is_published", "created_at")
    list_filter = ("rating", "is_published")
    search_fields = ("comment", "vendor__business_name", "customer__phone")
    list_select_related = ("vendor", "customer", "request")
