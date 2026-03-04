from django.contrib.auth.models import User
from django.db import models

# User roles for permissions
class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('division_manager', 'Division Manager'),
        ('manager', 'Manager'),
        ('assistant_manager', 'Assistant Manager'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='assistant_manager')

    def __str__(self):
        role_display = dict(self.ROLE_CHOICES).get(self.role, self.role)
        return f"{self.user.username} ({role_display})"


# Create your models here.
class Client(models.Model):
    LOCATION_CHOICES = [
        ('N', 'North'),
        ('NE', 'Northeast'),
        ('NW', 'Northwest'),
        ('S', 'South'),
        ('SW', 'Southwest'),
        ('SE', 'Southeast'),
        ('OH', 'Ohio'),
    ]
    
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    phone_number = models.CharField(max_length=10, blank=True)
    location = models.CharField(max_length=2, choices=LOCATION_CHOICES, default='OH', blank=True)

    def __str__(self):
        return self.name

class Job(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    job_title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    scheduled_date = models.DateTimeField(null=True, blank=True)
    note = models.TextField(blank=True)

    def __str__(self):
        return f"{self.job_title} for {self.client.name}"

class Scheduler(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
    ]
    
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    scheduled_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.job.job_title} - {self.status} at {self.scheduled_time}"