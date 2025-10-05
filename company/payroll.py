from django.db import models
from users.models import EmployeeProfile

class Payroll(models.Model):
    employee = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE, related_name='payrolls')
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2)
    bonuses = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    month = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def net_salary(self):
        return self.basic_salary + self.bonuses - self.deductions

    def __str__(self):
        return f"{self.employee.user.username} - {self.month.strftime('%B %Y')}"
