from django.contrib import admin

from .models import ResourceTemplate, Task, TaskPlan, TaskResource


@admin.register(TaskPlan)
class TaskPlanAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'status', 'phase', 'starts_on', 'ends_on', 'completion_pct']
    list_filter = ['status']
    search_fields = ['user__username', 'title']


class TaskResourceInline(admin.TabularInline):
    model = TaskResource
    extra = 0
    fields = ['title', 'resource_type', 'template', 'is_completed', 'sort_order']
    readonly_fields = ['template']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'plan', 'category', 'difficulty', 'day_number', 'due_date', 'status']
    list_filter = ['status', 'category', 'difficulty']
    search_fields = ['title', 'description']
    date_hierarchy = 'due_date'
    inlines = [TaskResourceInline]


@admin.action(description='Approve selected templates (mark as Reviewed)')
def approve_templates(modeladmin, request, queryset):
    queryset.filter(status='DRAFT').update(status='REVIEWED')


@admin.action(description='Archive selected templates')
def archive_templates(modeladmin, request, queryset):
    queryset.exclude(status='ARCHIVED').update(status='ARCHIVED')


@admin.register(ResourceTemplate)
class ResourceTemplateAdmin(admin.ModelAdmin):
    list_display = ['title', 'resource_type', 'status', 'times_used', 'created_at']
    list_filter = ['status', 'resource_type']
    search_fields = ['title', 'content', 'tags']
    readonly_fields = ['times_used', 'ai_model_used', 'created_at', 'updated_at']
    actions = [approve_templates, archive_templates]
    fieldsets = (
        (None, {
            'fields': ('title', 'resource_type', 'status', 'content', 'external_url'),
        }),
        ('Categorization', {
            'fields': ('business_types', 'categories', 'tags'),
        }),
        ('Metadata', {
            'fields': ('times_used', 'ai_model_used', 'created_at', 'updated_at'),
        }),
    )
