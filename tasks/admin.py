from django.contrib import admin
from .models import Task, TaskAttachment, TaskComment  # import all related models


# --- INLINE: Attachments inside Task Admin ---
class TaskAttachmentInline(admin.TabularInline):
    model = TaskAttachment
    extra = 1
    readonly_fields = ('uploaded_at', 'file_preview')

    def file_preview(self, obj):
        """Show small preview for image files."""
        if obj.file and obj.file.name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            return f'<img src="{obj.file.url}" style="max-width:100px; height:auto;" />'
        return "No preview"
    file_preview.allow_tags = True
    file_preview.short_description = "Preview"


# --- INLINE: Comments inside Task Admin ---
class TaskCommentInline(admin.TabularInline):
    model = TaskComment
    extra = 1
    readonly_fields = ('created_at',)
    fields = ('author', 'text', 'attachment', 'created_at')


# --- MAIN: Task Admin ---
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
        'ticket__subject'
    )
    date_hierarchy = 'deadline'
    readonly_fields = ('created_at', 'updated_at')
    inlines = [TaskAttachmentInline, TaskCommentInline]  # ✅ add both inlines

    fieldsets = (
        (None, {
            'fields': ('ticket', 'title', 'description', 'parent_task', 'status', 'deadline')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


# --- SEPARATE ADMIN PAGE: For managing attachments directly ---
@admin.register(TaskAttachment)
class TaskAttachmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'task', 'uploaded_by', 'uploaded_at', 'Output', 'file_link')
    list_filter = ('uploaded_at', 'Output')
    search_fields = ('task__title', 'uploaded_by__username', 'file')
    readonly_fields = ('uploaded_at', 'file_preview')

    def file_link(self, obj):
        if obj.file:
            return f"<a href='{obj.file.url}' target='_blank'>View File</a>"
        return "No file"
    file_link.allow_tags = True
    file_link.short_description = "File Link"

    def file_preview(self, obj):
        if obj.file and obj.file.name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            return f'<img src="{obj.file.url}" style="max-width:150px; height:auto;" />'
        return "No preview"
    file_preview.allow_tags = True
    file_preview.short_description = "Preview"


# --- Optional: Admin for Task Comments ---
@admin.register(TaskComment)
class TaskCommentAdmin(admin.ModelAdmin):
    list_display = ('task', 'author', 'created_at', 'short_text')
    search_fields = ('task__title', 'author__username', 'text')
    readonly_fields = ('created_at',)

    def short_text(self, obj):
        return obj.text[:50] + "..." if len(obj.text) > 50 else obj.text
    short_text.short_description = "Comment Preview"
