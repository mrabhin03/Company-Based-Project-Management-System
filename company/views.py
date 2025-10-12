from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Department, Position, Benefit
from .forms import DepartmentForm, PositionForm, BenefitForm
from users.models import EmployeeProfile

def is_admin(user):
    return user.is_authenticated and user.role == 'ADMIN'

@user_passes_test(is_admin, login_url='/users/login/')
def department_list(request):
    value=0
    if request.method == 'GET' and request.GET.get("department") and request.GET.get("department")=="1":
        value=1
        depatList=Department.objects.all()
    else:
        depatList=Department.objects.filter(parent=None)
    return render(request, 'company/department_list.html', {'departments': depatList,'value':value})

@user_passes_test(is_admin, login_url='/users/login/')
def department_create(request):
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            form.save()
            if request.POST.get("parent"):
                return redirect('department_view',request.POST.get("parent"))
            return redirect('department_list')
    else:
        parent=None
        if request.method == 'GET' and request.GET.get("parent"):
            form = DepartmentForm(initial={'parent': request.GET.get("parent")})
            parent=request.GET.get("parent")
        else:
            form = DepartmentForm()
    return render(request, 'company/department_form.html', {'form': form,'parent':parent})

def get_all_sub_departments(department):
    sub_departments = Department.objects.filter(parent=department)
    all_subs = list(sub_departments)
    for sub in sub_departments:
        all_subs.extend(get_all_sub_departments(sub))
    return all_subs

@user_passes_test(is_admin, login_url='/users/login/')
def department_view(request, dept_id):
    department = get_object_or_404(Department, id=dept_id)
    sub_departments = Department.objects.filter(parent=department)
    all_departments = [department] + get_all_sub_departments(department)
    employees = EmployeeProfile.objects.filter(department__in=all_departments)
    positions=Position.objects.filter(department__in=all_departments)
    return render(request, 'company/Department_detail.html', {
        'department': department,
        'sub_departments': sub_departments,
        'employees':employees,
        'positions':positions
    })

@user_passes_test(is_admin)
def department_edit(request, pk):
    department = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=department)
        if form.is_valid():
            form.save()
            return redirect('department_view',department.id)
    else:
        form = DepartmentForm(instance=department)
    return render(request, 'company/department_form.html', {'form': form})

# --- Position ---
@user_passes_test(is_admin)
def position_list(request):
    return render(request, 'company/position_list.html', {'positions': Position.objects.all()})

@user_passes_test(is_admin)
def position_create(request):
    if request.method == 'POST':
        form = PositionForm(request.POST)
        if form.is_valid():
            form.save()
            if request.POST.get("parent"):
                return redirect('department_view',request.POST.get("parent"))
            return redirect('position_list')
    else:
        parent=None
        if request.method == 'GET' and request.GET.get("parent"):
            parent=request.GET.get("parent")
            form = PositionForm(initial={'department': request.GET.get("parent")})
        else:
            form = PositionForm()
    return render(request, 'company/position_form.html', {'form': form,'parent':parent})

@user_passes_test(is_admin)
def position_edit(request, pk):
    position = get_object_or_404(Position, pk=pk)
    if request.method == 'POST':
        form = PositionForm(request.POST, instance=position)
        if form.is_valid():
            form.save()
            if request.POST.get("parent"):
                return redirect('department_view',request.POST.get("parent"))
            return redirect('position_list')
    else:
        form = PositionForm(instance=position)
    return render(request, 'company/position_form.html', {'form': form})

# --- Benefit ---
@user_passes_test(is_admin)
def benefit_list(request):
    return render(request, 'company/benefit_list.html', {'benefits': Benefit.objects.all()})

@user_passes_test(is_admin)
def benefit_create(request):
    if request.method == 'POST':
        form = BenefitForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('benefit_list')
    else:
        form = BenefitForm()
    return render(request, 'company/benefit_form.html', {'form': form})

@user_passes_test(is_admin)
def benefit_edit(request, pk):
    benefit = get_object_or_404(Benefit, pk=pk)
    if request.method == 'POST':
        form = BenefitForm(request.POST, instance=benefit)
        if form.is_valid():
            form.save()
            return redirect('benefit_list')
    else:
        form = BenefitForm(instance=benefit)
    return render(request, 'company/benefit_form.html', {'form': form})



