from django.shortcuts import render
from django.contrib.auth.decorators import user_passes_test
from users.models import EmployeeProfile
from performance.models import PerformanceReport

def is_admin_or_manager(user):
    return user.is_authenticated and user.role in ['ADMIN', 'MANAGER']

@user_passes_test(is_admin_or_manager)
def performance_overview(request):
    if request.user.role == 'MANAGER':
        employees = EmployeeProfile.objects.filter(department=request.user.employeeprofile.department)
    else:
        employees = EmployeeProfile.objects.all()
    
    reports = PerformanceReport.objects.filter(employee__in=employees)
    return render(request, 'performance/performance_overview.html', {'reports': reports})
