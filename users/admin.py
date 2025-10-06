# users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, EmployeeProfile

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username','name', 'email', 'role',  'is_staff', 'is_active') 
    
    list_filter = ('role', 'is_staff', 'is_active')
    # list_editable = ('name', 'email') 

admin.site.register(CustomUser, CustomUserAdmin)


class EmployeeProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'department', 'position', 'date_of_joining', 'salary')
    search_fields = ('user__username', 'user__email', 'department', 'position')

admin.site.register(EmployeeProfile, EmployeeProfileAdmin)


from .models import Payroll

@admin.register(Payroll)
class PayrollAdmin(admin.ModelAdmin):
    list_display = ('employee', 'month', 'net_salary', 'is_paid')
    list_filter = ('month', 'is_paid')
    search_fields = ('employee__user__username',)