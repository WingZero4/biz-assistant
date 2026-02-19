from django.contrib import admin

from .models import Task, TaskPlan


@admin.register(TaskPlan)
class TaskPlanAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'status', 'phase', 'starts_on', 'ends_on', 'completion_pct']
    list_filter = ['status']
    search_fields = ['user__username', 'title']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'plan', 'category', 'difficulty', 'day_number', 'due_date', 'status']
    list_filter = ['status', 'category', 'difficulty']
    search_fields = ['title', 'description']
    date_hierarchy = 'due_date'
