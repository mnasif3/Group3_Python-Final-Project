from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from .models import Client, Job, Scheduler
#from .forms import ClientForm, JobForm, SchedulerForm


def home(request):
    return render(request, 'scheduler/home.html')