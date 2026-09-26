from django.contrib import admin

from apps.orders.models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "vendor",
        "customer",
        "agreed_price",
        "status",
        "completed_at",
        "created_at",
    )
    list_filter = ("status",)
    list_select_related = ("vendor", "customer", "request", "quote")
