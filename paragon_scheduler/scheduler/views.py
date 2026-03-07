from django.contrib.auth.decorators import login_required
from functools import wraps
from django.http import HttpResponseForbidden

# Decorator for role-based access
def role_required(roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return HttpResponseForbidden('You must be logged in.')
            # Always allow superusers (admins)
            if getattr(request.user, 'is_superuser', False):
                return view_func(request, *args, **kwargs)
            userprofile = getattr(request.user, 'userprofile', None)
            if not userprofile or userprofile.role not in roles:
                return HttpResponseForbidden('You do not have permission to access this page.')
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.utils.dateparse import parse_datetime, parse_date
from datetime import datetime, time
import time as time_module

from .models import Client, Job, Scheduler
from .forms import ClientForm, JobForm, UserCreationWithRoleForm
from django.contrib import messages
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist

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


@login_required
def home(request):
    clients = Client.objects.all().order_by('name')
    jobs = Job.objects.select_related('client').all().order_by('-id')
    schedules = (
        Scheduler.objects.select_related('job', 'job__client')
        .filter(scheduled_time__isnull=False)
        .order_by('-scheduled_time')
    )
    return render(
        request,
        'scheduler/home.html',
        {
            'clients': clients,
            'jobs': jobs,
            'schedules': schedules,
        },
    )


@login_required
def clients_list(request):
    clients = Client.objects.all()
    return render(request, 'scheduler/clients.html', {'clients': clients})


@login_required
def jobs_list(request):
    jobs = Job.objects.all()
    return render(request, 'scheduler/jobs.html', {'jobs': jobs})

# Restrict add_client to division_manager
@login_required
@role_required(['division_manager'])
def add_client(request):
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('clients')
    else:
        form = ClientForm()
    return render(request, 'scheduler/add_client.html', {'form': form})

# Restrict edit_client to division_manager
@login_required
@role_required(['division_manager'])
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

# Restrict add_job to division_manager
@login_required
@role_required(['division_manager'])
def add_job(request):
    if request.method == 'POST':
        form = JobForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('jobs')
    else:
        form = JobForm()
    return render(request, 'scheduler/add_job.html', {'form': form})

# Restrict edit_job to division_manager
@login_required
@role_required(['division_manager'])
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

# Restrict delete_client to division_manager
@login_required
@role_required(['division_manager'])
def delete_client(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    if request.method == 'POST':
        client.delete()
        return redirect('clients')
    return render(request, 'scheduler/delete_client.html', {'client': client})

# Restrict delete_job to division_manager
@login_required
@role_required(['division_manager'])
def delete_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    if request.method == 'POST':
        job.delete()
        return redirect('jobs')
    return render(request, 'scheduler/delete_job.html', {'job': job})


@login_required
def schedule(request):
    schedules = Scheduler.objects.all()
    user_role = None
    if hasattr(request.user, 'userprofile'):
        user_role = request.user.userprofile.role
    return render(request, 'scheduler/schedule.html', {'schedules': schedules, 'user_role': user_role})


@login_required
def schedules_json(request):
    # Only return scheduled entries for FullCalendar.
    schedules = Scheduler.objects.select_related('job', 'job__client').filter(scheduled_time__isnull=False)
    events = []
    for s in schedules:
        location = s.job.client.location if s.job and s.job.client else ''
        address = s.job.client.address if s.job and s.job.client else ''
        if s.scheduled_time is None:
            continue
        start = s.scheduled_time.isoformat()
        events.append({
            'id': getattr(s, 'id'),
            'title': s.job.job_title,
            'start': start,
            'status': s.status,
            'client': s.job.client.name if s.job and s.job.client else '',
            'location': location,
            'address': address,
            'color': '#28a745' if s.status == 'completed' else '#007bff',
        })
    return JsonResponse(events, safe=False)


@login_required
@role_required(['division_manager', 'manager'])
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

    return JsonResponse({'success': True, 'start': dt.isoformat()})


@login_required
@require_POST
def toggle_schedule_status(request, schedule_id):
    # Only division managers/admin can toggle completion
    if (getattr(request.user, 'userprofile', None) and request.user.userprofile.role in ['assistant_manager', 'manager']) and not request.user.is_superuser:
        return HttpResponseForbidden('You do not have permission to perform this action.')
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


@login_required
@require_POST
def delete_schedule(request, schedule_id):
    # Only division managers/admin can delete schedules/jobs
    if (getattr(request.user, 'userprofile', None) and request.user.userprofile.role in ['assistant_manager', 'manager']) and not request.user.is_superuser:
        return HttpResponseForbidden('You do not have permission to perform this action.')
    s = get_object_or_404(Scheduler, id=schedule_id)
    job = s.job
    s.delete()
    job.delete()
    return JsonResponse({'success': True})


@login_required
@require_POST
def unschedule_job(request, schedule_id):
    # Managers are allowed to unschedule; assistants are not
    if getattr(request.user, 'userprofile', None) and request.user.userprofile.role == 'assistant_manager' and not request.user.is_superuser:
        return HttpResponseForbidden('You do not have permission to perform this action.')
    s = get_object_or_404(Scheduler, id=schedule_id)
    job = s.job
    job.scheduled_date = None
    job.save()
    s.delete()
    return JsonResponse({'success': True})



@login_required
def jobs_json(request):
    # Return jobs that are not scheduled yet.
    # A job is considered "scheduled" only if it has a Scheduler row with a non-null scheduled_time.
    scheduled_job_ids = Scheduler.objects.filter(scheduled_time__isnull=False).values_list('job_id', flat=True)
    jobs = Job.objects.exclude(id__in=scheduled_job_ids)
    data = []
    for j in jobs:
        data.append({
            'id': getattr(j, 'id'),
            'title': j.job_title,
            'client': j.client.name,
            'location': j.client.location if j.client else '',
            'address': j.client.address if j.client else '',
        })
    return JsonResponse(data, safe=False)


@login_required
def clients_json(request):
    clients = Client.objects.all()
    data = [{'id': getattr(c, 'id'), 'name': c.name} for c in clients]
    return JsonResponse(data, safe=False)


@login_required
@require_POST
def create_schedule_from_job(request):
    # Managers are allowed to schedule existing jobs; assistants are not
    if getattr(request.user, 'userprofile', None) and request.user.userprofile.role == 'assistant_manager' and not request.user.is_superuser:
        return HttpResponseForbidden('You do not have permission to perform this action.')
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

    return JsonResponse({'success': True, 'id': getattr(s, 'id'), 'title': job.job_title, 'start': dt.isoformat()})


@login_required
@role_required(['division_manager'])
@require_POST
def delete_job_api(request, job_id):
    # Only division managers/admin can delete jobs
    if (getattr(request.user, 'userprofile', None) and request.user.userprofile.role in ['assistant_manager', 'manager']) and not request.user.is_superuser:
        return HttpResponseForbidden('You do not have permission to perform this action.')
    job = get_object_or_404(Job, id=job_id)
    # Clean up any scheduler entries (including ones with null scheduled_time)
    Scheduler.objects.filter(job=job).delete()
    job.delete()
    return JsonResponse({'success': True})


@login_required
@require_POST
def create_job_and_schedule(request):
    # Only division managers/admin can create new jobs
    if (getattr(request.user, 'userprofile', None) and request.user.userprofile.role in ['assistant_manager', 'manager']) and not request.user.is_superuser:
        return HttpResponseForbidden('You do not have permission to perform this action.')
    title = request.POST.get('title')
    client_id = request.POST.get('client_id')
    desc = request.POST.get('description', '')
    start = request.POST.get('start') or request.body.decode()
    token = request.POST.get('token', '')
    location = request.POST.get('location', 'OH')

    # Check for duplicate submission
    if token and not check_and_mark_submission(token):
        return JsonResponse({'success': True, 'id': -1, 'duplicate': True})

    if not title or not client_id or not start or not location:
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
        job = Job.objects.create(client=client, job_title=title, description=desc, scheduled_date=dt)
        client.location = location
        client.save()
        # Scheduler is created automatically by signal

    # Fetch the scheduler that was created by the signal
    s = Scheduler.objects.get(job=job)

    return JsonResponse({'success': True, 'id': getattr(s, 'id'), 'title': job.job_title, 'start': dt.isoformat()})


@login_required
def create_user_account(request):
    # Allow superusers (admins) and division managers
    if not (request.user.is_superuser or (hasattr(request.user, 'userprofile') and request.user.userprofile.role == 'division_manager')):
        return HttpResponseForbidden('You do not have permission to access this page.')
    if request.method == 'POST':
        form = UserCreationWithRoleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'User account created successfully!')
            return redirect('create_user_account')
    else:
        form = UserCreationWithRoleForm()
    return render(request, 'scheduler/create_user_account.html', {'form': form})