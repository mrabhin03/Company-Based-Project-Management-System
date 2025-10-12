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
    
class TicketResponse(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='responses')
    responder = models.ForeignKey("users.CustomUser", on_delete=models.SET_NULL, null=True, blank=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_customer_reply = models.BooleanField(default=False)
    status=models.BooleanField(default=False)
    
class TicketFeedback(models.Model):
    ticket = models.OneToOneField(Ticket, on_delete=models.CASCADE, related_name='feedback')
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class TicketAttachment(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to="ticket_attachments/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    Output=models.BooleanField(default=False)

    def __str__(self):
        return self.file.name