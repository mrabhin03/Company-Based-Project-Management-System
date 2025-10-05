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
    
ASSIGN_TYPE_CHOICES = [
    ('DEPARTMENT', 'Department'),
    ('EMPLOYEE', 'Employee'),
]

class TicketAssignment(models.Model):
    ticket = models.ForeignKey('Ticket', on_delete=models.CASCADE, related_name='assignments')
    assign_type = models.CharField(max_length=20, choices=ASSIGN_TYPE_CHOICES)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    employee = models.ForeignKey(EmployeeProfile, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField(blank=True)
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, default='ASSIGNED')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        target = self.department.name if self.department else (self.employee.user.username if self.employee else 'Unassigned')
        return f"{self.ticket.subject} → {target}"
    def save(self, *args, **kwargs):
        if self.ticket.status == 'PENDING':
            self.ticket.status = 'IN_PROGRESS'
            self.ticket.save(update_fields=['status'])
        super().save(*args, **kwargs)
