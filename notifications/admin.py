from django.contrib import admin

from .models import MessageLog


@admin.register(MessageLog)
class MessageLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'channel', 'direction', 'status', 'content_preview', 'created_at']
    list_filter = ['channel', 'direction', 'status']
    search_fields = ['user__username', 'content', 'twilio_sid']
    date_hierarchy = 'created_at'

    def content_preview(self, obj):
        return obj.content[:80]
    content_preview.short_description = 'Content'
