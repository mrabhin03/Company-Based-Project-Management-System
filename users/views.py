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


def home(request):
    return render(request, 'users/indexOfAll.html')


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

        total_tickets = Ticket.objects.exclude(status='Canceled').count()
        in_progress_tickets = Ticket.objects.filter(status='In Progress').count()
        completed_tickets = Ticket.objects.filter(status__in=['Resolved','Closed']).exclude(status='Canceled').count()
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
        payrolls = employee_profile.payrolls.order_by("-month").all()

        total_tasks = Task.objects.filter(assigned_to=employee_profile).count()
        completed_tasks = Task.objects.filter(status='Completed',assigned_to=employee_profile).count()
        pending_tasks = total_tasks-completed_tasks
        task_progress = {
            'pending': pending_tasks,
            'completed': completed_tasks,
            'total': total_tasks,
            'completed_percent': int((completed_tasks/total_tasks)*100) if total_tasks else 0,
        }
        context.update({
            'employee_profile': employee_profile,
            'payrolls': payrolls,
            'task_progress': task_progress,
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

EmpSort={
    'Name':"user__name",
    'Role':"user__role",
    'Position':'position',
    'Department':'department'
}
@user_passes_test(lambda u: u.is_authenticated and u.role in [User.ROLE_ADMIN, User.ROLE_MANAGER])
def employee_list(request):
    sortOP="Name"
    if request.GET.get('SortBy'):
        sortOP=request.GET.get('SortBy')
        if sortOP not in EmpSort:
            sortOP="Name"
    theSort=EmpSort[sortOP]
    DepFilter=0
    depSelector=DepFilterForm()

    if request.method == 'GET' and request.GET.get('department') and int(request.GET.get('department'))!=0:
        DepFilter = request.GET.get('department')
        department_queryset = Department.objects.filter(pk=DepFilter)
        first_department = department_queryset.first()
        if request.user.role == 'MANAGER':
            childDept=getAllChildren(request.user.employeeprofile.department)
            depSelector=DepFilterForm(departments=childDept,initial={'department': DepFilter})
            profiles = EmployeeProfile.objects.filter(department__in=childDept,department=first_department).exclude(user=request.user).order_by(theSort)
        else:
            profiles = EmployeeProfile.objects.filter(department=first_department).all().order_by(theSort)
            depSelector = DepFilterForm(initial={'department': DepFilter})
    else:
        if request.user.role == 'MANAGER':
            childDept=getAllChildren(request.user.employeeprofile.department)
            depSelector=DepFilterForm(departments=childDept,initial={'department': DepFilter})
            profiles = EmployeeProfile.objects.filter(department__in=childDept).exclude(user=request.user).order_by(theSort)
        else:
            profiles = EmployeeProfile.objects.select_related('user').all().order_by(theSort)
    return render(request, 'users/employee_list.html', {'profiles': profiles,'Dep':depSelector,'DepFilter':DepFilter,'sortOP':sortOP})


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







