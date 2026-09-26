from django.contrib import admin

from apps.notifications.models import NotificationLog


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ("event", "channel", "recipient", "success", "created_at")
    list_filter = ("event", "channel", "success")
    search_fields = ("recipient",)
