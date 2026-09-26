from django.contrib import admin

from apps.requests.models import ProjectRequest


@admin.register(ProjectRequest)
class ProjectRequestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "customer",
        "service",
        "city",
        "status",
        "budget_max",
        "created_at",
    )
    list_filter = ("status", "city", "service", "lighting_type")
    search_fields = ("title", "description", "customer__phone")
    list_select_related = ("customer", "service", "city")
    readonly_fields = ("created_at", "updated_at")
