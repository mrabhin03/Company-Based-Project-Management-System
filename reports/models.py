from django.db import models
from users.models import CustomUser

class ReportLog(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    report_name = models.CharField(max_length=200)
    parameters = models.TextField(blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.report_name} by {self.user.username}"
