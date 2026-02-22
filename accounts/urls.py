from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('', views.landing_view, name='landing'),
    path('signup/', views.signup_view, name='signup'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('dashboard/assessment/', views.assessment_view, name='assessment'),
    path('profile/', views.profile_view, name='profile'),
    path('pulse/', views.weekly_pulse_view, name='pulse'),
    path('pulse/history/', views.pulse_history_view, name='pulse_history'),
    path('analytics/', views.analytics_view, name='analytics'),
    path('chat/', views.chat_view, name='chat'),
    path('chat/send/', views.chat_send_view, name='chat_send'),
    path('chat/new/', views.chat_new_session_view, name='chat_new_session'),
    path('content/', views.documents_view, name='documents'),
    path('content/generate/', views.document_generate_view, name='document_generate'),
    path('content/<int:pk>/favorite/', views.document_favorite_view, name='document_favorite'),
]
