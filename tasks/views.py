from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from users.decorators import is_admin, is_manager, is_employee, is_admin_or_manager
from .models import Task
from .forms import TaskForm,TaskFormEdit
from users.models import EmployeeProfile

# ------------------- Admin / Manager -------------------

@login_required
@is_admin_or_manager
def task_list_admin(request):
    """Admin sees all tasks, Manager sees only department tasks"""
    if request.user.role == 'ADMIN':
        tasks = Task.objects.all()
    else:  # Manager
        tasks = Task.objects.filter(assigned_to__department=request.user.employeeprofile.department)
    return render(request, 'tasks/task_list_admin.html', {'tasks': tasks})

@login_required
@is_admin_or_manager
def task_create(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            # Restrict assignment for manager
            if request.user.role == 'MANAGER' and task.assigned_to.department != request.user.employeeprofile.department:
                return HttpResponse("Managers can assign tasks only to their department employees.")
            task.save()
            return redirect('task_list_admin')
    else:
        form = TaskForm()
        if request.user.role == 'MANAGER':
            # Limit dropdown to manager's department
            form.fields['assigned_to'].queryset = EmployeeProfile.objects.filter(
                department=request.user.employeeprofile.department
            )
    return render(request, 'tasks/task_form.html', {'form': form})

@login_required
@is_admin_or_manager
def task_edit(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    # Manager can edit only tasks in their department
    if request.user.role == 'MANAGER' and task.assigned_to.department != request.user.employeeprofile.department:
        return HttpResponse("Managers cannot edit tasks outside their department.")
    
    if request.method == 'POST':
        form = TaskFormEdit(request.POST, instance=task)
        if form.is_valid():
            form.save()
            return redirect('task_list_admin')
    else:
        form = TaskFormEdit(instance=task)
        if request.user.role == 'MANAGER':
            form.fields['assigned_to'].queryset = EmployeeProfile.objects.filter(
                department=request.user.employeeprofile.department
            )
    return render(request, 'tasks/task_edit.html', {'form': form})

# ------------------- Employee -------------------

@login_required
@is_employee
def task_list_employee(request):
    tasks = Task.objects.filter(assigned_to=request.user.employeeprofile)
    return render(request, 'tasks/task_list_employee.html', {'tasks': tasks})

@login_required
@is_employee
def task_update_status(request, task_id):
    task = get_object_or_404(Task, id=task_id, assigned_to=request.user.employeeprofile)
    if request.method == 'POST':
        status = request.POST.get('status')
        if status in ['ASSIGNED', 'IN_PROGRESS', 'COMPLETED']:
            task.status = status
            task.save()
        return redirect('task_list_employee')
    statuses = Task.STATUS_CHOICES
    return render(request, 'tasks/task_update_status.html', {'task': task,'statuses': statuses})

@login_required
@is_admin_or_manager
def task_create_from_ticket(request, ticket_id):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            task.save()
            form.save_m2m()
            return redirect('task_list_admin')
    else:
        form = TaskForm(initial={'ticket': ticket_id})
    return render(request, 'tasks/task_form.html', {'form': form})

def task_decline(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    ticket_id = task.ticket.id
    task.delete()
    return redirect('ticket_assign', ticket_id=ticket_id)
