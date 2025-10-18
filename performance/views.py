from django.shortcuts import render,get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from users.models import EmployeeProfile
from performance.models import PerformanceReport
from customers.models import TicketFeedback
from django.db.models import Q, Avg
from collections import OrderedDict
from company.models import Department
from datetime import date
from django.utils import timezone
from datetime import timedelta,datetime
from tasks.models import Task

def is_admin_or_manager(user):
    return user.is_authenticated and user.role in ['ADMIN', 'MANAGER']

@user_passes_test(is_admin_or_manager)
def performance_overview(request):
    if request.user.role == 'MANAGER':
        employees = EmployeeProfile.objects.filter(department=request.user.employeeprofile.department)
    else:
        employees = EmployeeProfile.objects.all()
    
    reports_qs = PerformanceReport.objects.filter(employee__in=employees)
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

def get_time_buckets(range_param):
    today = timezone.now().date()
    buckets = []

    if range_param == '1m':
        # daily buckets for current month
        start_date = today.replace(day=1)
        for i in range((today - start_date).days + 1):
            day = start_date + timedelta(days=i)
            buckets.append((day, day + timedelta(days=1), day.strftime('%d %b')))
    elif range_param == '6m':
        # monthly buckets for last 6 months
        for i in reversed(range(6)):
            month_start = (today.replace(day=1) - timedelta(days=i*30)).replace(day=1)
            month_end = (month_start + timedelta(days=32)).replace(day=1)
            buckets.append((month_start, month_end, month_start.strftime('%b %Y')))
    elif range_param == '1y':
        # monthly buckets for last 12 months
        for i in reversed(range(12)):
            month_start = (today.replace(day=1) - timedelta(days=i*30)).replace(day=1)
            month_end = (month_start + timedelta(days=32)).replace(day=1)
            buckets.append((month_start, month_end, month_start.strftime('%b %Y')))
    else:
        # default 6 months
        for i in reversed(range(6)):
            month_start = (today.replace(day=1) - timedelta(days=i*30)).replace(day=1)
            month_end = (month_start + timedelta(days=32)).replace(day=1)
            buckets.append((month_start, month_end, month_start.strftime('%b %Y')))

    return buckets

def collect_department_ids(root_dep):
    ids = [root_dep.id]
    children = Department.objects.filter(parent=root_dep)
    for c in children:
        ids.extend(collect_department_ids(c))
    return ids

def department_performance(request, department_id=None):
    user = request.user

    # range param -> months
    range_param = request.GET.get('range', '6m')
    if range_param == '1m':
        months = 1
    elif range_param == '1y':
        months = 12
    else:
        months = 6

    # choose departments to display
    if department_id:
        departments = [get_object_or_404(Department, id=department_id)]
    else:
        if getattr(user, 'role', None) == 'MANAGER':
            # manager sees his own dept root (the dept they are assigned to)
            if hasattr(user, 'employeeprofile') and user.employeeprofile.department:
                departments = [user.employeeprofile.department]
            else:
                departments = []
        else:
            # admin: show only root parents
            departments = Department.objects.filter(parent__isnull=True).order_by('name')

    # build month buckets
    buckets = get_time_buckets(range_param)

    data = []
    # For each department, include aggregated arrays for Chart.js
    for dep in departments:
        dep_ids = collect_department_ids(dep)  # includes children recursively

        # base tasks queryset for this dept hierarchy
        tasks_qs = Task.objects.filter(
            Q(assigned_department__id__in=dep_ids) |
            Q(assigned_to__department__id__in=dep_ids)
        )

        # get ticket ids associated with these tasks for feedback lookups
        ticket_ids = tasks_qs.values_list('ticket_id', flat=True).distinct()

        # prepare arrays per month
        labels = []
        total_by_status = OrderedDict()  # status -> [counts per month]
        status_order = ['Assigned', 'In Progress', 'Completed']  # update if your app uses different statuses
        for s in status_order:
            total_by_status[s] = []

        rating_series = []

        for start, end, label in buckets:
            labels.append(label)
            month_tasks = tasks_qs.filter(created_at__gte=start, created_at__lt=end)

            # counts by status
            for s in status_order:
                count = month_tasks.filter(status=s).count()
                total_by_status[s].append(count)

            # rating: average feedback for tickets connected to tasks created in this month
            feedbacks = TicketFeedback.objects.filter(
                ticket_id__in=month_tasks.values_list('ticket_id', flat=True).distinct(),
                created_at__gte=start, created_at__lt=end
            )
            avg_rating = feedbacks.aggregate(avg=Avg('rating'))['avg'] or 0
            rating_series.append(round(avg_rating, 2))

        # build dataset ready for Chart.js
        datasets = []
        colors = {
            'PENDING': 'rgba(255, 159, 64, 0.7)',
            'Assigned': 'rgba(54, 162, 235, 0.7)',
            'In Progress': 'rgba(153, 102, 255, 0.7)',
            'Completed': 'rgba(75, 192, 192, 0.7)',
        }
        for s in status_order:
            datasets.append({
                'label': s.replace('_', ' ').title(),
                'data': total_by_status[s],
                'backgroundColor': colors.get(s, 'rgba(100,100,100,0.6)'),
                'stack': 'tasks'
            })

        # rating dataset (line)
        rating_dataset = {
            'label': 'Avg Rating',
            'data': rating_series,
            'type': 'line',
            'yAxisID': 'rating',
            'borderColor': 'rgba(255,99,132,0.9)',
            'backgroundColor': 'rgba(255,99,132,0.2)',
            'tension': 0.3
        }

        data.append({
            'department': dep,
            'labels': labels,
            'datasets': datasets,
            'rating_dataset': rating_dataset,
            'subdepartments': Department.objects.filter(parent=dep).order_by('name')
        })

    return render(request, 'users/department_performance.html', {
        'data': data,
        'range_param': range_param
    })
