from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('', views.landing_view, name='landing'),
    path('signup/', views.signup_view, name='signup'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('dashboard/assessment/', views.assessment_view, name='assessment'),
    path('profile/', views.profile_view, name='profile'),
]
