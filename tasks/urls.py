from django.urls import path

from . import views

app_name = 'tasks'

urlpatterns = [
    path('', views.task_list_view, name='list'),
    path('<int:pk>/', views.task_detail_view, name='detail'),
    path('<int:pk>/done/', views.mark_done_view, name='mark_done'),
    path('<int:pk>/skip/', views.mark_skip_view, name='mark_skip'),
]
