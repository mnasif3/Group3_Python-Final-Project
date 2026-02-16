from django.contrib import admin
from .models import Client, Job, Scheduler

admin.site.register(Client)
admin.site.register(Job)
admin.site.register(Scheduler)