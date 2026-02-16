from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Job, Scheduler


@receiver(post_save, sender=Job)
def create_scheduler_for_job(sender, instance, created, **kwargs):
    """Automatically create a Scheduler entry when a new Job is created."""
    if created:
        Scheduler.objects.create(
            job=instance,
            scheduled_time=instance.scheduled_date,
            status='pending'
        )
