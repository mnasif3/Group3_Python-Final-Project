from django.shortcuts import render, redirect, get_object_or_404
from .models import Client, Job, Scheduler
from .forms import ClientForm, JobForm


def home(request):
    return render(request, 'scheduler/home.html')


def clients_list(request):
    clients = Client.objects.all()
    return render(request, 'scheduler/clients.html', {'clients': clients})


def jobs_list(request):
    jobs = Job.objects.all()
    return render(request, 'scheduler/jobs.html', {'jobs': jobs})

def add_client(request):
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('clients')
    else:
        form = ClientForm()
    return render(request, 'scheduler/add_client.html', {'form': form})

def edit_client(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            return redirect('clients')
    else:
        form = ClientForm(instance=client)
    return render(request, 'scheduler/edit_client.html', {'form': form, 'client': client})

def add_job(request):
    if request.method == 'POST':
        form = JobForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('jobs')
    else:
        form = JobForm()
    return render(request, 'scheduler/add_job.html', {'form': form})

def edit_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    if request.method == 'POST':
        form = JobForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            return redirect('jobs')
    else:
        form = JobForm(instance=job)
    return render(request, 'scheduler/edit_job.html', {'form': form, 'job': job})

def schedule(request):
    schedules = Scheduler.objects.all()
    return render(request, 'scheduler/schedule.html', {'schedules': schedules})