from django.contrib import admin

from apps.payments.models import (
    FeaturedPlacement,
    LeadPurchase,
    PriceEstimateConfig,
    SubscriptionPlan,
    VendorSubscription,
)


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ("title", "code", "monthly_price", "lead_quota", "is_active")


@admin.register(VendorSubscription)
class VendorSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("vendor", "plan", "starts_at", "ends_at", "is_active")
    list_select_related = ("vendor", "plan")


@admin.register(LeadPurchase)
class LeadPurchaseAdmin(admin.ModelAdmin):
    list_display = ("vendor", "request", "amount", "is_paid", "created_at")
    list_select_related = ("vendor", "request")


@admin.register(FeaturedPlacement)
class FeaturedPlacementAdmin(admin.ModelAdmin):
    list_display = ("vendor", "starts_at", "ends_at", "is_active")


@admin.register(PriceEstimateConfig)
class PriceEstimateConfigAdmin(admin.ModelAdmin):
    list_display = ("service", "base_price_per_sqm", "is_active")
    list_select_related = ("service",)
