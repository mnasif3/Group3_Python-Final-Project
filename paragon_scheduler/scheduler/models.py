from django.db import models

# Create your models here.
class Client(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.name

class Job(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    job_title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    scheduled_date = models.DateTimeField()
    note = models.TextField(blank=True)
    type = models.CharField()

    def __str__(self):
        return f"{self.job_title} for {self.client.name}"

class Scheduler(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
    ]
    
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    scheduled_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.job.job_title} - {self.status} at {self.scheduled_time}"