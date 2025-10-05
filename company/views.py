from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Department, Position, Benefit
from .forms import DepartmentForm, PositionForm, BenefitForm

def is_admin(user):
    return user.is_authenticated and user.role == 'ADMIN'

@user_passes_test(is_admin, login_url='/users/login/')
def department_list(request):
    return render(request, 'company/department_list.html', {'departments': Department.objects.all()})

@user_passes_test(is_admin, login_url='/users/login/')
def department_create(request):
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('department_list')
    else:
        form = DepartmentForm()
    return render(request, 'company/department_form.html', {'form': form})

@user_passes_test(is_admin)
def department_edit(request, pk):
    department = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=department)
        if form.is_valid():
            form.save()
            return redirect('department_list')
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
            return redirect('position_list')
    else:
        form = PositionForm()
    return render(request, 'company/position_form.html', {'form': form})

@user_passes_test(is_admin)
def position_edit(request, pk):
    position = get_object_or_404(Position, pk=pk)
    if request.method == 'POST':
        form = PositionForm(request.POST, instance=position)
        if form.is_valid():
            form.save()
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



