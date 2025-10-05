# recruitment/models.py
from django.db import models

class Candidate(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15, blank=True)
    resume = models.FileField(upload_to='resumes/')
    applied_position = models.CharField(max_length=100)
    applied_department = models.CharField(max_length=100)
    status = models.CharField(max_length=50, default='APPLIED')  # APPLIED, INTERVIEW, HIRED, REJECTED
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.status}"

class OnboardingChecklist(models.Model):
    # Change this line only:
    employee = models.ForeignKey('users.EmployeeProfile', on_delete=models.CASCADE)
    task = models.CharField(max_length=200)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.task} - {'Done' if self.completed else 'Pending'}"
