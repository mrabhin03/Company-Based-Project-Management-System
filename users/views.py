# users/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model, login as auth_login, logout as auth_logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse
from .forms import CustomUserForm, EmployeeProfileForm, CustomLoginForm
from .models import EmployeeProfile, Payroll
from .forms import PayrollForm,PayrollFilterForm
from django.db.models import Max
from datetime import date

User = get_user_model()

def is_admin(user):
    return user.is_authenticated and user.role == User.ROLE_ADMIN

def is_manager(user):
    return user.is_authenticated and user.role == User.ROLE_MANAGER

def is_employee(user):
    return user.is_authenticated and user.role == User.ROLE_EMPLOYEE

# Login view (custom for handling ?next)
def user_login(request):
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

# Dashboard - role-aware
@login_required
def dashboard(request):
    user = request.user
    context = {'user': user}

    # Admin/HR dashboard
    if user.role in ['ADMIN', 'HR']:
        # Add employee list link and payroll link
        context.update({
            'employees': EmployeeProfile.objects.all(),
        })
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
        return render(request, 'users/dashboard_manager.html', context)


@user_passes_test(lambda u: u.is_authenticated and u.role in [User.ROLE_ADMIN, User.ROLE_MANAGER])
def employee_list(request):
    if request.user.role == 'MANAGER':
        profiles = EmployeeProfile.objects.filter(department=request.user.employeeprofile.department) 
    else:
        profiles = EmployeeProfile.objects.select_related('user').all()
    return render(request, 'users/employee_list.html', {'profiles': profiles})


# Register employee (admin + manager)
@user_passes_test(lambda u: u.is_authenticated and u.role in [User.ROLE_ADMIN, User.ROLE_MANAGER], login_url='login')
def employee_register(request):
    if request.method == 'POST':
        user_form = CustomUserForm(request.POST)
        profile_form = EmployeeProfileForm(request.POST)
        payroll_form = PayrollForm(request.POST)
        if user_form.is_valid() and profile_form.is_valid() and payroll_form.is_valid():
            # Create User and Employee Profile
            user = user_form.save()
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()
            profile_form.save_m2m()

            # Create Payroll linked to Employee
            payroll = payroll_form.save(commit=False)
            payroll.employee = profile
            payroll.save()

            return redirect('employee_list')
    else:
        user_form = CustomUserForm()
        profile_form = EmployeeProfileForm()
        payroll_form = PayrollForm()

    return render(request, 'users/employee_register.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'payroll_form': payroll_form
    })
@user_passes_test(lambda u: u.is_authenticated and u.role in [User.ROLE_ADMIN, User.ROLE_MANAGER], login_url='login')
def edit_employee(request, profile_id):
    profile = get_object_or_404(EmployeeProfile, id=profile_id)
    if request.method == 'POST':
        user_form = CustomUserForm(request.POST, instance=profile.user)
        profile_form = EmployeeProfileForm(request.POST, instance=profile)
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save(commit=False)
            user.save()
            profile_form.save()
            return redirect('employee_list')
    else:
        user_form = CustomUserForm(instance=profile.user)
        profile_form = EmployeeProfileForm(instance=profile)
    return render(request, 'users/edit_employee.html', {'user_form': user_form, 'profile_form': profile_form, 'profile': profile})

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
        form = PayrollForm()
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

