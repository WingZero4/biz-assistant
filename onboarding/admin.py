from django.contrib import admin

from .models import BusinessProfile, Conversation


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
    list_display = ['user', 'role', 'content_preview', 'created_at']
    list_filter = ['role']
    search_fields = ['user__username', 'content']

    def content_preview(self, obj):
        return obj.content[:80]
    content_preview.short_description = 'Content'
