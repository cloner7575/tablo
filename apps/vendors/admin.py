from django.contrib import admin, messages

from apps.vendors.models import Vendor, VerificationStatus


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = (
        "business_name",
        "city",
        "verification_status",
        "rating",
        "review_count",
        "completed_projects",
        "is_active",
        "is_featured",
    )
    list_filter = ("verification_status", "is_active", "is_featured", "city")
    search_fields = ("business_name", "phone", "user__phone")
    prepopulated_fields = {"slug": ("business_name",)}
    filter_horizontal = ("services",)
    list_select_related = ("city", "user")
    actions = ("approve_vendors", "suspend_vendors")

    @admin.action(description="تأیید تابلو‌سازهای انتخاب‌شده")
    def approve_vendors(self, request, queryset):
        updated = queryset.update(verification_status=VerificationStatus.APPROVED)
        self.message_user(request, f"{updated} تابلو‌ساز تأیید شد.", messages.SUCCESS)

    @admin.action(description="تعلیق تابلو‌سازهای انتخاب‌شده")
    def suspend_vendors(self, request, queryset):
        updated = queryset.update(verification_status=VerificationStatus.SUSPENDED)
        self.message_user(request, f"{updated} تابلو‌ساز معلق شد.", messages.WARNING)
