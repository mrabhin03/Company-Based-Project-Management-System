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
    
    reports_qs = PerformanceReport.objects.filter(employee__in=employees)

    # Convert to list of dicts for JSON
    reports = []
    for r in reports_qs:
        reports.append({
            'employee': {
                'id': r.employee.id,
                'username': r.employee.user.username,
                'name': getattr(r.employee.user, 'name', r.employee.user.username),
            },
            'total_tasks': r.total_tasks,
            'completed_tasks': r.completed_tasks,
            'pending_tasks': r.pending_tasks,
            'overdue_tasks': r.overdue_tasks,
            'performance_score': float(r.performance_score or 0),
        })

    return render(request, 'performance/performance_overview.html', {'reports': reports})
