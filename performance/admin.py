# # performance/admin.py

# from django.contrib import admin
# from .models import PerformanceReport

# @admin.register(PerformanceReport)
# class PerformanceAdmin(admin.ModelAdmin):
#     list_display = ('employee', 'rating', 'review_date', 'reviewer')
#     search_fields = ('employee__user__username', 'reviewer__username')
#     list_filter = ('rating', 'review_date')
