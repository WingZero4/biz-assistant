from django.urls import path

from . import views

app_name = 'tasks'

urlpatterns = [
    path('', views.task_list_view, name='list'),
    path('<int:pk>/', views.task_detail_view, name='detail'),
    path('<int:pk>/done/', views.mark_done_view, name='mark_done'),
    path('<int:pk>/skip/', views.mark_skip_view, name='mark_skip'),
    path('<int:pk>/reschedule/', views.reschedule_view, name='reschedule'),
    path('regenerate/', views.regenerate_plan_view, name='regenerate'),
    path('resource/<int:pk>/toggle/', views.toggle_resource_view, name='toggle_resource'),
    path('continue/', views.continue_plan_view, name='continue_plan'),
]
