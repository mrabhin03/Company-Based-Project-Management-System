from django.db import models
from django.utils import timezone
from users.models import EmployeeProfile

class PerformanceReport(models.Model):
    employee = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE, related_name='performance_reports')
    total_tasks = models.PositiveIntegerField(default=0)
    completed_tasks = models.PositiveIntegerField(default=0)
    pending_tasks = models.PositiveIntegerField(default=0)
    overdue_tasks = models.PositiveIntegerField(default=0)
    performance_score = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def calculate_score(self):
        """Simple logic: Completed tasks / Total tasks * 100"""
        if self.total_tasks > 0:
            self.performance_score = (self.completed_tasks / self.total_tasks) * 100
        else:
            self.performance_score = 0
        self.save()

    def __str__(self):
        return f"Performance Report - {self.employee.user.username} ({self.performance_score:.2f}%)"
