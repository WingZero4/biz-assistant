from django.contrib import admin

from .models import BusinessProfile, Conversation, GeneratedDocument, WeeklyPulse


@admin.register(BusinessProfile)
class BusinessProfileAdmin(admin.ModelAdmin):
    list_display = [
        'business_name', 'user', 'business_type', 'stage',
        'budget_range', 'viability_score', 'created_at',
    ]
    list_filter = ['stage', 'business_type', 'budget_range', 'business_model']
    search_fields = ['business_name', 'user__username', 'niche']
    readonly_fields = ['ai_assessment', 'ai_model_used', 'assessment_generated_at']

    def viability_score(self, obj):
        assessment = obj.ai_assessment or {}
        score = assessment.get('viability_score')
        return f'{score}/10' if score else '—'
    viability_score.short_description = 'Viability'


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'conversation_type', 'session_id', 'content_preview', 'created_at']
    list_filter = ['role', 'conversation_type']
    search_fields = ['user__username', 'content', 'session_id']

    def content_preview(self, obj):
        return obj.content[:80]
    content_preview.short_description = 'Content'


@admin.register(WeeklyPulse)
class WeeklyPulseAdmin(admin.ModelAdmin):
    list_display = ['user', 'week_of', 'revenue_this_week', 'new_customers', 'energy_level', 'created_at']
    list_filter = ['energy_level', 'week_of']
    search_fields = ['user__username']


@admin.register(GeneratedDocument)
class GeneratedDocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'doc_type', 'platform', 'is_favorite', 'created_at']
    list_filter = ['doc_type', 'is_favorite']
    search_fields = ['user__username', 'title', 'content']
    readonly_fields = ['ai_model_used', 'created_at']
