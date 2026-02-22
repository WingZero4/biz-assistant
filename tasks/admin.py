from django.contrib import admin

from .models import Achievement, ResourceTemplate, StreakRecord, Task, TaskPlan, TaskResource


class TaskInline(admin.TabularInline):
    model = Task
    extra = 0
    fields = ['day_number', 'title', 'category', 'status', 'due_date']
    readonly_fields = ['day_number', 'title', 'category', 'status', 'due_date']
    show_change_link = True
    can_delete = False


@admin.register(TaskPlan)
class TaskPlanAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'user', 'status', 'phase',
        'starts_on', 'ends_on', 'task_count', 'completion_pct',
    ]
    list_filter = ['status']
    search_fields = ['user__username', 'title']
    inlines = [TaskInline]

    def task_count(self, obj):
        return obj.tasks.count()
    task_count.short_description = 'Tasks'


class TaskResourceInline(admin.TabularInline):
    model = TaskResource
    extra = 0
    fields = ['title', 'resource_type', 'template', 'is_completed', 'sort_order']
    readonly_fields = ['template']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'plan_user', 'category', 'difficulty',
        'day_number', 'due_date', 'status', 'resource_count',
    ]
    list_filter = ['status', 'category', 'difficulty']
    search_fields = ['title', 'description', 'plan__user__username']
    date_hierarchy = 'due_date'
    inlines = [TaskResourceInline]

    def plan_user(self, obj):
        return obj.plan.user.username
    plan_user.short_description = 'User'

    def resource_count(self, obj):
        return obj.resources.count()
    resource_count.short_description = 'Resources'


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'badge', 'earned_at']
    list_filter = ['badge']
    search_fields = ['user__username', 'title']
    readonly_fields = ['earned_at']


@admin.register(StreakRecord)
class StreakRecordAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'tasks_completed']
    list_filter = ['date']
    search_fields = ['user__username']


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
