from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    # Auth
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    # Apps
    path('', include('accounts.urls')),
    path('onboarding/', include('onboarding.urls')),
    path('tasks/', include('tasks.urls')),
    path('webhooks/', include('notifications.urls')),
]
