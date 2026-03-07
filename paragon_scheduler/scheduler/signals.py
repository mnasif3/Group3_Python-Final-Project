from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Job, Scheduler


@receiver(post_save, sender=Job)
def sync_scheduler_for_job(sender, instance, **kwargs):
    """Keep Scheduler rows in sync with Job.scheduled_date.

    The calendar renders Scheduler.scheduled_time, while the Jobs page edits
    Job.scheduled_date. This signal ensures updates on the Jobs page are
    reflected on the calendar, and also de-duplicates multiple Scheduler rows
    for the same Job (keeping the newest).
    """
    schedulers = Scheduler.objects.filter(job=instance).order_by('-pk')
    scheduler = schedulers.first()

    if scheduler is None:
        Scheduler.objects.create(
            job=instance,
            scheduled_time=instance.scheduled_date,
            status='pending',
        )
        return

    # Keep only the newest scheduler row for this job.
    Scheduler.objects.filter(job=instance).exclude(pk=scheduler.pk).delete()

    desired_time = instance.scheduled_date
    if scheduler.scheduled_time != desired_time:
        scheduler.scheduled_time = desired_time
        scheduler.save(update_fields=['scheduled_time'])
