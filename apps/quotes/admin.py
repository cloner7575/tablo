from django.contrib import admin

from apps.quotes.models import Quote


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "vendor",
        "request",
        "price",
        "estimated_delivery_days",
        "status",
        "created_at",
    )
    list_filter = ("status",)
    search_fields = ("vendor__business_name", "request__title")
    list_select_related = ("vendor", "request")
    readonly_fields = ("created_at", "updated_at")
