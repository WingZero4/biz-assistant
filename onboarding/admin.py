from django.contrib import admin

from .models import BusinessProfile, Conversation


@admin.register(BusinessProfile)
class BusinessProfileAdmin(admin.ModelAdmin):
    list_display = ['business_name', 'user', 'business_type', 'stage', 'budget_range']
    list_filter = ['stage', 'business_type', 'budget_range']
    search_fields = ['business_name', 'user__username']
    readonly_fields = ['ai_assessment', 'ai_model_used', 'assessment_generated_at']


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'content_preview', 'created_at']
    list_filter = ['role']
    search_fields = ['user__username', 'content']

    def content_preview(self, obj):
        return obj.content[:80]
    content_preview.short_description = 'Content'
