from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import Customer, Ticket, TicketAttachment
from django.contrib.auth.admin import UserAdmin

CustomUser = get_user_model()

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'subject', 'customer', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at', 'updated_at')
    search_fields = ('subject', 'description', 'customer__user__username')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')


# ✅ TicketAttachment Admin
@admin.register(TicketAttachment)
class TicketAttachmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'ticket', 'uploaded_by', 'uploaded_at', 'Output', 'file_link')
    list_filter = ('uploaded_at', 'Output')
    search_fields = ('ticket__subject', 'uploaded_by__username', 'file')
    readonly_fields = ('uploaded_at', 'file_preview')

    def file_link(self, obj):
        """Display clickable link to the uploaded file."""
        if obj.file:
            return f"<a href='{obj.file.url}' target='_blank'>View File</a>"
        return "No file"
    file_link.allow_tags = True
    file_link.short_description = "File"

    def file_preview(self, obj):
        """Preview image files inline in admin (optional)."""
        if obj.file and obj.file.name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            return f'<img src="{obj.file.url}" style="max-width: 200px; height: auto;" />'
        return "No preview available"
    file_preview.allow_tags = True
    file_preview.short_description = "Preview"


# ✅ Custom User Admin
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'email', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active')
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password', 'role', 'phone')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'role', 'phone', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )
    search_fields = ('username', 'email')
    ordering = ('username',)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone')
    search_fields = ('user__username', 'user__email', 'phone')
