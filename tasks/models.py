from django.db import models
from users.models import EmployeeProfile
from performance.models import PerformanceReport
from django.utils import timezone
from customers.models import Customer, Ticket
from users.models import EmployeeProfile, Department
from django.contrib.auth import get_user_model
from datetime import date, timedelta
CustomUser = get_user_model()

def default_deadline():
    return date.today() + timedelta(days=7)

class Task(models.Model):
    STATUS_CHOICES = [
    ('Assigned', 'Assigned'),
    ('In Progress', 'In Progress'),
    ('Submitted', 'Submitted'),
    ('Needs Revision', 'Needs Revision'),
    ('Approved', 'Approved'),
    ('Completed', 'Completed'),
    ]

    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE,null=True, related_name='tasks')
    title = models.CharField(max_length=200,null=False,default="No Title")
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(
    CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_tasks'
    )
    assigned_to = models.ForeignKey(EmployeeProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks')
    parent_task = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subtasks'
    )

    assigned_department = models.ForeignKey(
        Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='department_tasks'
    )
    assigned_employees = models.ManyToManyField(
        EmployeeProfile, blank=True, related_name='employee_tasks'
    )
    deadline = models.DateField(null=True, blank=True,default=default_deadline) 

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Assigned')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.parent_task:
            return f"{self.parent_task.title} → {self.title} ({self.status})"
        return f"{self.title} ({self.status})"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.update_performance()
        self.update_parent_task_status()

    def update_performance(self):
        employee = self.assigned_to
        if employee:
            tasks = Task.objects.filter(assigned_to=employee)
            total = tasks.count()
            completed = tasks.filter(status='Completed').count()
            pending = tasks.filter(status='In Progress').count()
            overdue = tasks.filter(deadline__lt=timezone.now().date()).exclude(status='Completed').count()

            report, _ = PerformanceReport.objects.get_or_create(employee=employee)
            report.total_tasks = total
            report.completed_tasks = completed
            report.pending_tasks = pending
            report.overdue_tasks = overdue
            report.calculate_score()
    def update_parent_ticket_status(self):
        all_tasks = self.ticket.tasks.all() 
        incomplete_tasks_exist = all_tasks.exclude(status='Completed').exists()
        current_ticket_status = self.ticket.status
        ticket_updated = False
        if not incomplete_tasks_exist:
            if current_ticket_status not in ['RESOLVED', 'CLOSED']:
                self.ticket.status = 'RESOLVED'
                ticket_updated = True
        else:
            if current_ticket_status in ['RESOLVED', 'CLOSED','PENDING']:
                self.ticket.status = 'IN_PROGRESS'
                ticket_updated = True
        if ticket_updated:
            self.ticket.save(update_fields=['status'])
    def update_parent_task_status(self):
        parent = self.parent_task
        while parent:
            all_done = not parent.subtasks.exclude(status='Completed').exists()
            if all_done and parent.status != 'Completed':
                parent.status = 'Submitted'
                parent.save(update_fields=['status'])
            else:
                if parent.status != 'In Progress':
                    parent.status = 'In Progress'
                    parent.save(update_fields=['status'])
            parent = parent.parent_task
        self.update_parent_ticket_status()


from django.conf import settings
from django.db import models

class TaskAttachment(models.Model):
    task = models.ForeignKey('Task', on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to="task/attachments/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    Output=models.BooleanField(default=False)

    def __str__(self):
        return self.file.name
    

class TaskComment(models.Model):
    task = models.ForeignKey('Task', on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    attachment = models.FileField(upload_to="task/comment_attachments/", null=True, blank=True)

    def __str__(self):
        return f"Comment by {self.author} on {self.task}"
