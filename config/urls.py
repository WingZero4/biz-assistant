from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    # Auth
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('password/change/', auth_views.PasswordChangeView.as_view(
        template_name='registration/password_change.html',
        success_url='/profile/',
    ), name='password_change'),
    path('password/reset/', auth_views.PasswordResetView.as_view(
        template_name='registration/password_reset.html',
        email_template_name='registration/password_reset_email.html',
        success_url='/password/reset/done/',
    ), name='password_reset'),
    path('password/reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='registration/password_reset_done.html',
    ), name='password_reset_done'),
    path('password/reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html',
        success_url='/login/',
    ), name='password_reset_confirm'),
    # Apps
    path('', include('accounts.urls')),
    path('onboarding/', include('onboarding.urls')),
    path('tasks/', include('tasks.urls')),
    path('webhooks/', include('notifications.urls')),
]
