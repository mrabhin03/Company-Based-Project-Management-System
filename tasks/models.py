from django.db import models
from users.models import EmployeeProfile
from performance.models import PerformanceReport
from django.utils import timezone
from customers.models import Customer, Ticket
from users.models import EmployeeProfile, Department
from django.contrib.auth import get_user_model
CustomUser = get_user_model()

STATUS_CHOICES = [
    ('PENDING', 'Pending'),
    ('IN_PROGRESS', 'In Progress'),
    ('COMPLETED', 'Completed'),
]

class Task(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(
    CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_tasks'
    )
    assigned_to = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE, related_name='tasks')

    assigned_department = models.ForeignKey(
        Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='department_tasks'
    )
    assigned_employees = models.ManyToManyField(
        EmployeeProfile, blank=True, related_name='employee_tasks'
    )
    deadline = models.DateField(null=True, blank=True) 

    parent_task = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True, related_name='subtasks'
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.status})"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.update_performance()
        self.update_parent_ticket_status()

    def update_performance(self):
        employee = self.assigned_to
        tasks = Task.objects.filter(assigned_to=employee)
        total = tasks.count()
        completed = tasks.filter(status='COMPLETED').count()
        pending = tasks.filter(status='PENDING').count()
        overdue = tasks.filter(deadline__lt=timezone.now().date()).exclude(status='COMPLETED').count()

        report, _ = PerformanceReport.objects.get_or_create(employee=employee)
        report.total_tasks = total
        report.completed_tasks = completed
        report.pending_tasks = pending
        report.overdue_tasks = overdue
        report.calculate_score()
    def update_parent_ticket_status(self):
        all_tasks = self.ticket.tasks.all() 
        incomplete_tasks_exist = all_tasks.exclude(status='COMPLETED').exists()
        current_ticket_status = self.ticket.status
        ticket_updated = False
        if not incomplete_tasks_exist:
            if current_ticket_status not in ['RESOLVED', 'CLOSED']:
                self.ticket.status = 'RESOLVED'
                ticket_updated = True
        else:
            if current_ticket_status in ['RESOLVED', 'CLOSED']:
                self.ticket.status = 'IN_PROGRESS'
                ticket_updated = True

        if ticket_updated:
            self.ticket.save(update_fields=['status'])
