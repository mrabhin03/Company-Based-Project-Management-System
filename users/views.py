# users/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model, login as auth_login, logout as auth_logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse
from .forms import CustomUserForm, EmployeeProfileForm, CustomLoginForm,UserFormEdit
from .models import EmployeeProfile, Payroll,CustomUser
from .forms import PayrollForm,PayrollFilterForm,DepFilterForm,ChangePassword,EmpSelfEdit1,EmpSelfEdit2
from company.models import Department
from django.db.models import Max
from datetime import date
from django.utils import timezone
from datetime import timedelta,datetime
from tasks.models import Task
from customers.models import TicketFeedback,Ticket
from django.db.models import Q, Avg
from collections import OrderedDict

User = get_user_model()

def is_admin(user):
    return user.is_authenticated and user.role == User.ROLE_ADMIN

def is_manager(user):
    return user.is_authenticated and user.role == User.ROLE_MANAGER

def is_employee(user):
    return user.is_authenticated and user.role == User.ROLE_EMPLOYEE

# Login view (custom for handling ?next)
def user_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            # redirect to next if present
            next_url = request.GET.get('next') or request.POST.get('next') or reverse('dashboard')
            return redirect(next_url)
    else:
        form = CustomLoginForm()
    return render(request, 'users/login.html', {'form': form})

def user_logout(request):
    auth_logout(request)
    return redirect('login')
def getAllChildren(dept):
    children = [dept]

    def _get_children(t):
        for child in t.sub_departments.all():
            children.append(child)
            _get_children(child) 

    _get_children(dept)
    return children

@login_required
def dashboard(request):
    user = request.user
    context = {'user': user}

    # Admin/HR dashboard
    if user.role in ['ADMIN', 'HR']:
        total_employees = EmployeeProfile.objects.count()
        total_departments = Department.objects.count()

        total_tickets = Ticket.objects.count()
        in_progress_tickets = Ticket.objects.filter(status='In Progress').count()
        completed_tickets = Ticket.objects.filter(status='Resolved').count()
        pending_tickets = total_tickets-completed_tickets
        ticket_progress = {
            'pending': pending_tickets,
            'in_progress': in_progress_tickets,
            'completed': completed_tickets,
            'total': total_tickets,
            'completed_percent': int((completed_tickets/total_tickets)*100) if total_tickets else 0,
            'in_progress_percent': int((in_progress_tickets/total_tickets)*100) if total_tickets else 0
        }
        total_tasks = Task.objects.count()
        completed_tasks = Task.objects.filter(status='Completed').count()
        pending_tasks = total_tasks-completed_tasks
        task_progress = {
            'pending': pending_tasks,
            'completed': completed_tasks,
            'total': total_tasks,
            'completed_percent': int((completed_tasks/total_tasks)*100) if total_tasks else 0,
        }

        context = {
            'total_employees': total_employees,
            'total_departments': total_departments,
            'ticket_progress': ticket_progress,
            'task_progress': task_progress,
        }
        return render(request, 'users/dashboard_admin.html', context)

    elif user.role == 'EMPLOYEE':
        employee_profile = EmployeeProfile.objects.get(user=user)
        payrolls = employee_profile.payrolls.all()
        context.update({
            'employee_profile': employee_profile,
            'payrolls': payrolls,
        })
        return render(request, 'users/dashboard_employee.html', context)

    elif user.role == 'MANAGER':
        dept=getAllChildren(user.employeeprofile.department)
        total_employees = EmployeeProfile.objects.filter(department__in=dept).count()
        total_departments =len(dept)
        
        total_tasks = Task.objects.filter(
            Q(assigned_department__in=dept) | Q(assigned_to__department__in=dept)
        ).count()
        completed_tasks = Task.objects.filter(
            Q(assigned_department__in=dept) | Q(assigned_to__department__in=dept),status='Completed'
        ).count()
        pending_tasks = total_tasks-completed_tasks
        task_progress = {
            'pending': pending_tasks,
            'completed': completed_tasks,
            'total': total_tasks,
            'completed_percent': int((completed_tasks/total_tasks)*100) if total_tasks else 0,
        }
        context = {
            'total_employees': total_employees,
            'total_departments': total_departments,
            'task_progress': task_progress,
        }
        return render(request, 'users/dashboard_manager.html', context)
    else:
        return redirect("customer_dashboard")


@user_passes_test(lambda u: u.is_authenticated and u.role in [User.ROLE_ADMIN, User.ROLE_MANAGER])
def employee_list(request):
    depSelector=DepFilterForm()
    if request.user.role == 'MANAGER':
        profiles = EmployeeProfile.objects.filter(department=request.user.employeeprofile.department) 
    else:
        if request.method == 'GET' and request.GET.get('department') and int(request.GET.get('department'))!=0:
            DepFilter = request.GET.get('department')
            department_queryset = Department.objects.filter(pk=DepFilter)
            first_department = department_queryset.first()
            profiles = EmployeeProfile.objects.filter(department=first_department).all()
            depSelector = DepFilterForm(initial={'department': DepFilter})
        else:
            profiles = EmployeeProfile.objects.select_related('user').all()
    return render(request, 'users/employee_list.html', {'profiles': profiles,'Dep':depSelector})


# Register employee (admin + manager)
@user_passes_test(lambda u: u.is_authenticated and u.role in [User.ROLE_ADMIN, User.ROLE_MANAGER], login_url='login')
def employee_register(request):
    if request.method == 'POST':
        user_form = CustomUserForm(request.POST)
        profile_form = EmployeeProfileForm(request.POST)
        if user_form.is_valid() and profile_form.is_valid() :
            # Create User and Employee Profile
            user = user_form.save()
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()
            profile_form.save_m2m()

            return redirect('employee_list')
    else:
        user_form = CustomUserForm()
        profile_form = EmployeeProfileForm()

    return render(request, 'users/employee_register.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })
@login_required
def edit_employee(request, profile_id):
    profile = get_object_or_404(EmployeeProfile, id=profile_id)
    if request.method == 'POST':
        if request.user.role!="EMPLOYEE":
            user_form = UserFormEdit(request.POST, instance=profile.user)
            profile_form = EmployeeProfileForm(request.POST, instance=profile)
            if user_form.is_valid() and profile_form.is_valid():
                user = user_form.save(commit=False)
                user.save()
                profile_form.save()
            return redirect('employee_list')
        else:
            EmpSelfEditF1 = EmpSelfEdit1(request.POST, instance=profile.user)
            EmpSelfEditF2 = EmpSelfEdit2(request.POST, instance=profile)
            if EmpSelfEditF1.is_valid() and EmpSelfEditF2.is_valid():
                user = EmpSelfEditF1.save(commit=False)
                user.save()
                EmpSelfEditF2.save()
                
            return redirect('view_profile',profile_id=profile.id)
    else:
        if request.user.role!="EMPLOYEE":
            user_form = UserFormEdit(instance=profile.user)
            profile_form = EmployeeProfileForm(instance=profile)
            return render(request, 'users/edit_employee.html', {'user_form': user_form, 'profile_form': profile_form, 'profile': profile})
        else:
            EmpSelfEditF1 = EmpSelfEdit1(instance=profile.user)
            EmpSelfEditF2 = EmpSelfEdit2(instance=profile)
            return render(request, 'users/edit_employee.html', { 'profile': profile,'EmpSelfEditF1':EmpSelfEditF1,'EmpSelfEditF2':EmpSelfEditF2})

@login_required
def view_profile(request, profile_id):
    profile = get_object_or_404(EmployeeProfile, id=profile_id)
    if request.user.role == User.ROLE_EMPLOYEE and profile.user != request.user:
        return render(request, 'users/forbidden.html', status=403)
    return render(request, 'users/profile.html', {'profile': profile})



def is_admin(user):
    return user.is_authenticated and user.role in ['ADMIN', 'HR']

@login_required
def payroll_list(request, employee_id):
    employee = get_object_or_404(EmployeeProfile, id=employee_id)
    payrolls = employee.payrolls.all()
    return render(request, 'users/payroll_list.html', {'employee': employee, 'payrolls': payrolls})

@user_passes_test(is_admin)
def payroll_add(request, employee_id):
    employee = get_object_or_404(EmployeeProfile, id=employee_id)
    if request.method == 'POST':
        form = PayrollForm(request.POST)
        if form.is_valid():
            payroll = form.save(commit=False)
            payroll.employee = employee
            payroll.save()
            return redirect('payroll_list', employee_id=employee.id)
    else:
        form = PayrollForm(initial={'base_salary': employee.salary})
    return render(request, 'users/payroll_add.html', {'form': form, 'employee': employee})

@user_passes_test(is_admin)
def payroll_edit(request, payroll_id):
    payroll = get_object_or_404(Payroll, id=payroll_id)
    if request.method == 'POST':
        form = PayrollForm(request.POST, instance=payroll)
        if form.is_valid():
            form.save()
            return redirect('payroll_list', employee_id=payroll.employee.id)
    else:
        form = PayrollForm(instance=payroll)
    return render(request, 'users/payroll_edit.html', {'form': form, 'employee': payroll.employee})


def getBonus(emp, month, year):
    bonus = 0
    deduction = 0 

    start_date = timezone.make_aware(datetime(year, month, 1))
    if month == 12:
        end_date = timezone.make_aware(datetime(year + 1, 1, 1)) - timedelta(seconds=1)
    else:
        end_date = timezone.make_aware(datetime(year, month + 1, 1)) - timedelta(seconds=1)

    today = date.today()

    if emp.user.role == "EMPLOYEE":
        taskDetails = Task.objects.filter(
            assigned_to=emp,
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        
        for task in taskDetails:
            if task.status == "Completed":
                bonus += 500
            elif task.status in ["Assigned", "In Progress", "Submitted", "Needs Revision", "Approved"]:
                bonus += 50
            
            if task.status != "Completed" and task.deadline < today:
                deduction += 50  

    elif emp.user.role == "MANAGER":
        dept_emps = EmployeeProfile.objects.filter(department=emp.department)
        taskDetails = Task.objects.filter(
            assigned_to__in=dept_emps,
            created_at__gte=start_date,
            created_at__lte=end_date
        )

        for task in taskDetails:
            if task.status == "Completed":
                bonus += 1000
            elif task.status in ["Assigned", "In Progress", "Submitted", "Needs Revision", "Approved"]:
                bonus += 100
        
            if task.status != "Completed" and task.deadline < today:
                deduction += 100 
        taskDetails = Task.objects.filter(
            assigned_to=emp,
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        
        for task in taskDetails:
            if task.status == "Completed":
                bonus += 500
            elif task.status in ["Assigned", "In Progress", "Submitted", "Needs Revision", "Approved"]:
                bonus += 50
            
            if task.status != "Completed" and task.deadline < today:
                deduction += 50  
    return [bonus,deduction]

def generateSalary(month, year):
    join_date = date(year, month, 1)
    employee = EmployeeProfile.objects.filter(date_of_joining__lt=join_date)
    for emp in (employee):
        Pays=Payroll.objects.filter(employee=emp, month=join_date).first()
        Special = getBonus(emp, month, year)
        bonus=Special[0]
        deduction=Special[1]
        if Pays:
            Pays.base_salary=emp.salary
            Pays.bonuses=bonus
            Pays.deductions=deduction
            Pays.save()
        else:
            Payroll.objects.create(
                employee=emp,
                month=join_date,
                base_salary=emp.salary,
                bonuses=bonus,
                deductions=deduction
            )
            pass
def payroll_list_all(request):
    latest = Payroll.objects.aggregate(latest_month=Max('month'))['latest_month']
    if request.GET:
        form = PayrollFilterForm(request.GET)
        if form.is_valid():
            month = int(form.cleaned_data['month'])
            year = int(form.cleaned_data['year'])
        else:
            month = latest.month if latest else 1
            year = latest.year if latest else date.today().year
        if 'Genarate' in request.GET:
            generateSalary(month,year)
            return redirect(f"{reverse('payroll_list_all')}?month={month}&year={year}")
    else:
        form = PayrollFilterForm(initial={
            'month': latest.month if latest else date.today().month,
            'year': latest.year if latest else date.today().year
        })
        month = latest.month if latest else date.today().month
        year = latest.year if latest else date.today().year

    payrolls = Payroll.objects.filter(month__month=month, month__year=year)

    context = {
        'form': form,
        'payrolls': payrolls,
        'selected_month': month,
        'selected_year': year,
    }
    return render(request, 'users/payroll_list_all.html', context)

def Change_Password(request, profile_id):
    profile = get_object_or_404(EmployeeProfile, id=profile_id)
    if request.method == 'POST':
        user_form = ChangePassword(request.POST, instance=profile.user)
        if user_form.is_valid():
            user = user_form.save(commit=False)
            user.save()
            return redirect('view_profile',profile_id=profile.id)
    Change = ChangePassword(instance=profile.user)
    return render(request, 'users/ChangePassword.html', { 'profile': profile,'Change':Change})


def collect_department_ids(root_dep):
    ids = [root_dep.id]
    children = Department.objects.filter(parent=root_dep)
    for c in children:
        ids.extend(collect_department_ids(c))
    return ids

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

