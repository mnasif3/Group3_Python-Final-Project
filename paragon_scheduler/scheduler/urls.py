from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('add-client/', views.add_client, name='add_client'),
    path('edit-client/<int:client_id>/', views.edit_client, name='edit_client'),
    path('add-job/', views.add_job, name='add_job'),
    path('edit-job/<int:job_id>/', views.edit_job, name='edit_job'),
    path('schedule/', views.schedule, name='schedule'),
]