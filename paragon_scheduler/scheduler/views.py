from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.utils.dateparse import parse_datetime, parse_date
from datetime import datetime, time
from collections import defaultdict
import time as time_module

from .models import Client, Job, Scheduler
from .forms import ClientForm, JobForm
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Exists, OuterRef

# Simple deduplication cache: token -> timestamp
# Clean up entries older than 5 seconds
submission_cache = {}
submission_lock = __import__('threading').Lock()
SUBMISSION_CACHE_TTL = 5.0

def check_and_mark_submission(token):
    """Return True if this is a new submission, False if duplicate.
    Uses a lock to make check-and-set atomic."""
    global submission_cache
    now = time_module.time()
    
    with submission_lock:
        # Clean old entries
        expired = [k for k, v in submission_cache.items() if now - v > SUBMISSION_CACHE_TTL]
        for k in expired:
            del submission_cache[k]
        
        if token in submission_cache:
            return False  # Duplicate
        submission_cache[token] = now
        return True  # New submission


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


def schedules_json(request):
    schedules = Scheduler.objects.select_related('job').all()
    events = []
    for s in schedules:
        events.append({
            'id': s.id,
            'title': s.job.job_title,
            'start': s.scheduled_time.isoformat(),
            'status': s.status,
            'client': s.job.client.name if s.job and s.job.client else '',
            'color': '#28a745' if s.status == 'completed' else '#007bff',
        })
    return JsonResponse(events, safe=False)


@require_POST
def move_schedule(request, schedule_id):
    s = get_object_or_404(Scheduler, id=schedule_id)
    new_start = request.POST.get('start') or request.body.decode()
    if not new_start:
        return HttpResponseBadRequest('Missing start')
    # attempt to parse ISO datetime
    dt = parse_datetime(new_start)
    if dt is None:
        return HttpResponseBadRequest('Invalid datetime')
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.get_current_timezone())

    s.scheduled_time = dt
    s.save()

    # also update the Job's scheduled_date if present
    job = s.job
    job.scheduled_date = dt
    job.save()

    return JsonResponse({'success': True, 'start': s.scheduled_time.isoformat()})


@require_POST
def toggle_schedule_status(request, schedule_id):
    s = get_object_or_404(Scheduler, id=schedule_id)
    # toggle
    if s.status == 'pending':
        s.status = 'completed'
        s.completed_at = timezone.now()
    else:
        s.status = 'pending'
        s.completed_at = None
    s.save()
    return JsonResponse({'success': True, 'status': s.status})


def jobs_json(request):
    # return jobs that are not scheduled yet
    scheduled_job_ids = Scheduler.objects.values_list('job_id', flat=True)
    jobs = Job.objects.exclude(id__in=scheduled_job_ids)
    data = []
    for j in jobs:
        data.append({'id': j.id, 'title': j.job_title, 'client': j.client.name})
    return JsonResponse(data, safe=False)


def clients_json(request):
    clients = Client.objects.all()
    data = [{'id': c.id, 'name': c.name} for c in clients]
    return JsonResponse(data, safe=False)


@require_POST
def create_schedule_from_job(request):
    job_id = request.POST.get('job_id')
    start = request.POST.get('start') or request.body.decode()
    token = request.POST.get('token', '')
    
    # Check for duplicate submission
    if token and not check_and_mark_submission(token):
        return JsonResponse({'success': True, 'id': -1, 'duplicate': True})
    
    if not job_id or not start:
        return HttpResponseBadRequest('Missing job_id or start')
    dt = parse_datetime(start)
    if dt is None:
        d = parse_date(start)
        if d is None:
            return HttpResponseBadRequest('Invalid datetime')
        # default time at 09:00
        dt = datetime.combine(d, time(9, 0))
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.get_current_timezone())
    try:
        job = Job.objects.get(id=job_id)
    except ObjectDoesNotExist:
        return HttpResponseBadRequest('Invalid job')

    with transaction.atomic():
        s = Scheduler.objects.create(job=job, scheduled_time=dt, status='pending')
        job.scheduled_date = dt
        job.save()

    return JsonResponse({'success': True, 'id': s.id, 'title': job.job_title, 'start': s.scheduled_time.isoformat()})


@require_POST
def create_job_and_schedule(request):
    title = request.POST.get('title')
    client_id = request.POST.get('client_id')
    desc = request.POST.get('description', '')
    start = request.POST.get('start') or request.body.decode()
    token = request.POST.get('token', '')
    
    # Check for duplicate submission
    if token and not check_and_mark_submission(token):
        return JsonResponse({'success': True, 'id': -1, 'duplicate': True})
    
    if not title or not client_id or not start:
        return HttpResponseBadRequest('Missing fields')
    dt = parse_datetime(start)
    if dt is None:
        d = parse_date(start)
        if d is None:
            return HttpResponseBadRequest('Invalid datetime')
        dt = datetime.combine(d, time(9, 0))
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.get_current_timezone())
    try:
        client = Client.objects.get(id=client_id)
    except ObjectDoesNotExist:
        return HttpResponseBadRequest('Invalid client')

    with transaction.atomic():
        job = Job.objects.create(client=client, job_title=title, description=desc, scheduled_date=dt, type='general')
        # Scheduler is created automatically by signal

    # Fetch the scheduler that was created by the signal
    s = Scheduler.objects.get(job=job)

    return JsonResponse({'success': True, 'id': s.id, 'title': job.job_title, 'start': s.scheduled_time.isoformat()})