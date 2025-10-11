from django.contrib import admin
from .models import ReportLog

class ReportLogAdmin(admin.ModelAdmin):
    list_display = ('report_name', 'user', 'generated_at')
    search_fields = ('report_name', 'user__username')

admin.site.register(ReportLog, ReportLogAdmin)
