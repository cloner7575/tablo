from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from apps.accounts.models import PhoneOTP, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = (
        "username",
        "phone",
        "role",
        "is_verified",
        "is_staff",
        "is_active",
        "date_joined",
    )
    list_filter = ("role", "is_verified", "is_staff", "is_active")
    search_fields = ("username", "phone", "email", "first_name", "last_name")
    ordering = ("-date_joined",)
    fieldsets = DjangoUserAdmin.fieldsets + (
        (
            "تابلو",
            {"fields": ("phone", "role", "is_verified")},
        ),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        (None, {"fields": ("phone", "role")}),
    )


@admin.register(PhoneOTP)
class PhoneOTPAdmin(admin.ModelAdmin):
    list_display = (
        "phone",
        "purpose",
        "is_used",
        "attempts",
        "expires_at",
        "created_at",
    )
    list_filter = ("purpose", "is_used")
    search_fields = ("phone",)
    readonly_fields = ("code",)
