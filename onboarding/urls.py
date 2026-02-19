from django.urls import path

from . import views

app_name = 'onboarding'

urlpatterns = [
    path('step/1/', views.wizard_step_1, name='step_1'),
    path('step/2/', views.wizard_step_2, name='step_2'),
    path('step/3/', views.wizard_step_3, name='step_3'),
    path('step/4/', views.wizard_step_4, name='step_4'),
    path('complete/', views.onboarding_complete, name='complete'),
]
