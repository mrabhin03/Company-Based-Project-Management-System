from django.contrib import admin
from .models import Candidate, OnboardingChecklist

class CandidateAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'applied_position', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('first_name', 'last_name', 'email', 'applied_position')

admin.site.register(Candidate, CandidateAdmin)

class OnboardingChecklistAdmin(admin.ModelAdmin):
    list_display = ('employee', 'task', 'completed', 'created_at')
    list_filter = ('completed',)
    search_fields = ('task', 'employee__user__username')

admin.site.register(OnboardingChecklist, OnboardingChecklistAdmin)
