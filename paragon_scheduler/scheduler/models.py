from django.db import models

# Create your models here.
class Client(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.name

class Jobs(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    job_title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    scheduled_date = models.DateTimeField()

    def __str__(self):
        return f"{self.job_title} for {self.client.name}"

class Scheduler(models.Model):
    job = models.ForeignKey(Jobs, on_delete=models.CASCADE)
    scheduled_time = models.DateTimeField()

    def __str__(self):
        return f"Scheduler for {self.job.job_title} at {self.scheduled_time}"