from django.db import models

class Department(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='sub_departments',
        default='null'
    )
    manager = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        limit_choices_to={'role': 'MANAGER'},
        related_name='managed_departments'
    )
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        # Optional: show hierarchy name
        if self.parent:
            return f"{self.parent.name} → {self.name}"
        return self.name

class Position(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='positions',null=True)
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.department.name})"

class Benefit(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

