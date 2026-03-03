from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('clients/', views.clients_list, name='clients'),
    path('jobs/', views.jobs_list, name='jobs'),
    path('add-client/', views.add_client, name='add_client'),
    path('edit-client/<int:client_id>/', views.edit_client, name='edit_client'),
    path('add-job/', views.add_job, name='add_job'),
    path('edit-job/<int:job_id>/', views.edit_job, name='edit_job'),
    path('schedule/', views.schedule, name='schedule'),
    # API endpoints for calendar
    path('api/schedules/', views.schedules_json, name='schedules_json'),
    path('api/schedules/<int:schedule_id>/move/', views.move_schedule, name='move_schedule'),
    path('api/schedules/<int:schedule_id>/toggle/', views.toggle_schedule_status, name='toggle_schedule_status'),
    path('api/schedules/create/', views.create_schedule_from_job, name='create_schedule_from_job'),
    path('api/jobs/', views.jobs_json, name='jobs_json'),
    path('api/jobs/create/', views.create_job_and_schedule, name='create_job_and_schedule'),
    path('api/clients/', views.clients_json, name='clients_json'),
]