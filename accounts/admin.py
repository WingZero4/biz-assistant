from django.contrib import admin

from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'timezone', 'preferred_channel', 'is_onboarded']
    list_filter = ['is_onboarded', 'preferred_channel']
    search_fields = ['user__username', 'user__email', 'phone']
