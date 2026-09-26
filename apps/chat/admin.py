from django.contrib import admin

from apps.chat.models import Conversation, Message


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ("sender", "body", "image", "read_at", "created_at")
    can_delete = False

    def has_add_permission(self, request, obj=None) -> bool:
        return False


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("id", "quote", "status", "last_message_at", "created_at")
    list_filter = ("status",)
    search_fields = ("quote__id", "quote__vendor__business_name")
    readonly_fields = ("quote", "last_message_at", "created_at", "updated_at")
    inlines = [MessageInline]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "conversation", "sender", "created_at", "read_at")
    list_filter = ("read_at",)
    search_fields = ("body", "sender__phone")
    readonly_fields = (
        "conversation",
        "sender",
        "body",
        "image",
        "read_at",
        "created_at",
        "updated_at",
    )
