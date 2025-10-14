# users/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from company.models import Department, Position, Benefit


class CustomUser(AbstractUser):
    ROLE_ADMIN = 'ADMIN'
    ROLE_MANAGER = 'MANAGER'
    ROLE_EMPLOYEE = 'EMPLOYEE'
    ROLE_CUSTOMER = 'CUSTOMER'
    ROLE_CHOICES = (
        (ROLE_ADMIN, 'Admin/HR'),
        (ROLE_MANAGER, 'Manager'),
        (ROLE_EMPLOYEE, 'Employee'),
        (ROLE_CUSTOMER,'Customer')
    )
    name=models.CharField(max_length=500,null=False)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_EMPLOYEE)
    phone = models.CharField(max_length=15, blank=True, null=True)

    # Avoid reverse accessor clashes with default auth models (important)
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='customuser_set',  # different from auth.User.user_set
        blank=True,
        help_text='The groups this user belongs to.'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='customuser_set',  # different from auth.Permission.user_set
        blank=True,
        help_text='Specific permissions for this user.'
    )
    
    def PendingTasks(self):
        return self.employeeprofile.tasks.exclude(status="Completed").count()
    def PendingTickets(self):
        from customers.models import Ticket
        return Ticket.objects.exclude(status__in=['Resolved','Canceled','Closed']).count()
    
    def DepartmentTask(self):
        managed_departments = Department.objects.filter(manager=self)
        from tasks.models import Task
        return Task.objects.filter(assigned_department__in=managed_departments).exclude(status="Completed").count()

    def __str__(self):
        return f"{self.name} ({self.role})"


class EmployeeProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    position = models.ForeignKey(Position, on_delete=models.SET_NULL, null=True)
    benefits = models.ManyToManyField(Benefit, blank=True)
    date_of_joining = models.DateField()
    salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    skills = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.name} - {self.position.title if self.position else 'No Position'}"
    
class Payroll(models.Model):
    employee = models.ForeignKey('EmployeeProfile', on_delete=models.CASCADE, related_name='payrolls')
    month = models.DateField()  
    base_salary = models.DecimalField(max_digits=10, decimal_places=2)
    bonuses = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_salary = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Calculate net_salary automatically
        self.net_salary = self.base_salary + self.bonuses - self.deductions
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee.user.username} - {self.month.strftime('%B %Y')} - {'Paid' if self.is_paid else 'Pending'}"

