# customer/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.contrib.auth import get_user_model
from users.models import Department, EmployeeProfile
User = get_user_model()


class Customer(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15, blank=True)

    def __str__(self):
        return self.user.username
STATUS_CHOICES = [
    ('PENDING', 'Pending'),
    ('OPEN', 'Open'),
    ('IN_PROGRESS', 'In Progress'),
    ('RESOLVED', 'Resolved'),
    ('CLOSED', 'Closed'),
]

class Ticket(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='tickets')
    subject = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.subject} ({self.status})"