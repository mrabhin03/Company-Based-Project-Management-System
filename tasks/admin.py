from django.contrib import admin
from .models import Task # Import Task model

class AssignedEmployeeInline(admin.TabularInline):
    model = Task
    extra = 1

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        'title', 
        'ticket', 
        'assigned_department', 
        'status', 
        'deadline', 
        'created_at'
    )
    
    list_filter = (
        'status', 
        'deadline', 
        'assigned_department'
    )
    
    search_fields = (
        'title', 
        'description', 
        'ticket__title'
    )
    
    date_hierarchy = 'deadline'
    
    # Use inlines to manage the ManyToMany relationship in the same form
    inlines = [
        AssignedEmployeeInline,
    ]
    
    # Group fields for better layout on the form
    fieldsets = (
        (None, {
            'fields': ('ticket', 'title', 'description', 'parent_task', 'status', 'deadline')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = (
        'created_at', 
        'updated_at',
    )











