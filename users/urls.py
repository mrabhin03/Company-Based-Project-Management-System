# users/urls.py
from django.urls import path
from . import views
from company import urls
urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('performance/', views.department_performance, name='department_performance'),
    path('performance/<int:department_id>/', views.department_performance, name='department_performance_detail'),

    # employee management
    path('employees/', views.employee_list, name='employee_list'),
    path('employees/register/', views.employee_register, name='employee_register'),
    path('employees/edit/<int:profile_id>/', views.edit_employee, name='edit_employee'),
    path('employees/ChangePassword/<int:profile_id>/', views.Change_Password, name='change_password'),
    path('employees/profile/<int:profile_id>/', views.view_profile, name='view_profile'),

    path('payroll/<int:employee_id>/', views.payroll_list, name='payroll_list'),
    path('payroll/add/<int:employee_id>/', views.payroll_add, name='payroll_add'),
    path('payroll/edit/<int:payroll_id>/', views.payroll_edit, name='payroll_edit'),
    path('payroll/filter/', views.payroll_list_all, name='payroll_list_all'),
]
