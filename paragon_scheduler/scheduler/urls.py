from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    #path('add-client/', views.add_client, name='add_client'),
    #path('add-job/', views.add_job, name='add_job'),
    #path('schedule/', views.schedule_job, name='schedule_job'),
]