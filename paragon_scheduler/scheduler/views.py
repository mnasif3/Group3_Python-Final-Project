from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from .models import Client, Job, Scheduler
from .forms import ClientForm, JobForm


def home(request):
    clients = Client.objects.all()
    jobs = Job.objects.all()
    schedules = Scheduler.objects.all()
    context = {
        'clients': clients,
        'jobs': jobs,
        'schedules': schedules,
    }
    return render(request, 'scheduler/home.html', context)

def add_client(request):
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = ClientForm()
    return render(request, 'scheduler/add_client.html', {'form': form})

def add_job(request):
    if request.method == 'POST':
        form = JobForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = JobForm()
    return render(request, 'scheduler/add_job.html', {'form': form})