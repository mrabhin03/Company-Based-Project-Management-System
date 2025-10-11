from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from users.decorators import admin_required, manager_required, is_employee, is_admin_or_manager
from .models import Task,TaskAttachment
from .forms import TaskForm,TaskFormEdit,TaskStatus,TaskAttachmentForm
from users.models import EmployeeProfile
from company.models import Department
from django.db.models import Q

def get_all_subdepartments(department):
    subs = list(department.sub_departments.all()) 
    for sub in department.sub_departments.all():
        subs.extend(get_all_subdepartments(sub))
    return subs


# ------------------- Admin / Manager -------------------

@login_required
@admin_required
def task_list_admin(request):
    TaskFilter=TaskStatus()
    if request.method == 'GET' and request.GET.get('Status') and request.GET.get('Status')!="0":
        tasks = Task.objects.filter(status=request.GET.get('Status'))
        TaskFilter = TaskStatus(initial={'Status': request.GET.get('Status')})
    else:
        tasks = Task.objects.all()
    return render(request, 'tasks/task_list_admin.html', {'tasks': tasks,"status":TaskFilter})

@login_required
@manager_required
def task_list_manager(request):
    TaskFilter=TaskStatus()
    if request.method == 'GET' and request.GET.get('Status') and request.GET.get('Status')!="0":
        managed_departments = Department.objects.filter(manager=request.user)
        tasks = Task.objects.filter(assigned_department__in=managed_departments,status=request.GET.get('Status'))
        TaskFilter = TaskStatus(initial={'Status': request.GET.get('Status')})
    else:
        managed_departments = Department.objects.filter(manager=request.user)
        tasks = Task.objects.filter(assigned_department__in=managed_departments)
    return render(request, 'tasks/task_list_manager.html', {'tasks': tasks,"status":TaskFilter,"Title":"Department Tasks"})

@login_required
@manager_required
def emp_task_list_manager(request):
    TaskFilter=TaskStatus()
    managed_departments = Department.objects.filter(manager=request.user)
    all_departments = []

    for dept in managed_departments:
        all_departments.append(dept)
        all_departments.extend(get_all_subdepartments(dept))
    all_departments = list(set(all_departments))

    if request.method == 'GET' and request.GET.get('Status') and request.GET.get('Status')!="0":
        managed_departments = Department.objects.filter(manager=request.user)
        tasks = Task.objects.filter(Q(assigned_to__department__in=all_departments),status=request.GET.get('Status'))
        TaskFilter = TaskStatus(initial={'Status': request.GET.get('Status')})
    else:
        tasks = Task.objects.filter(Q(assigned_to__department__in=all_departments)
        )

    return render(request, 'tasks/task_list_manager.html', {'tasks': tasks,"status":TaskFilter,"Title":"Members Tasks"})


@login_required
@is_admin_or_manager
def task_create(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            task.save()
            # Save each uploaded file
            for f in request.FILES.getlist('file'):
                TaskAttachment.objects.create(
                    task=task,
                    file=f,
                    uploaded_by=request.user
                )
            return redirect('task_list_admin')
    else:
        form = TaskForm()
    return render(request, 'tasks/task_form.html', {'form': form})

@login_required
def task_edit(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    
    # Handle attachment deletion
    if request.method == 'POST' and 'delete_attachment_id' in request.POST:
        attachment_id = request.POST.get('delete_attachment_id')
        attachment = get_object_or_404(TaskAttachment, id=attachment_id, task=task)
        attachment.file.delete(save=False)
        attachment.delete() 
        if request.POST.get("toLocation"):
            return redirect(request.POST.get("toLocation"), task_id=task.id)
        return redirect('task_edit', task_id=task.id)
    
    if request.method == 'POST':
        form = TaskFormEdit(request.POST, instance=task)
        for f in request.FILES.getlist('file'):
            TaskAttachment.objects.create(
                task=task,
                file=f,
                uploaded_by=request.user
            )
        if form.is_valid():
            form.save()
            return redirect('task_list_admin')
    else:
        form = TaskFormEdit(instance=task)
    tasksAtt = TaskAttachment.objects.filter(task=task)
    return render(request, 'tasks/task_edit.html', {'form': form, 'tasksAtt': tasksAtt, 'task': task})

# ------------------- Employee -------------------

@login_required
def task_list_employee(request):
    tasks = Task.objects.filter(assigned_to=request.user.employeeprofile)
    return render(request, 'tasks/task_list_employee.html', {'tasks': tasks})

@login_required
def task_update_status(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    if request.method == 'POST':
        form = TaskStatusForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            # Save files uploaded as deliverables
            for f in request.FILES.getlist('file'):
                TaskAttachment.objects.create(
                    task=task,
                    file=f,
                    uploaded_by=request.user,
                    Output=True
                )
            if request.user.role=="EMPLOYEE":
                return redirect('task_list_employee')
            elif request.user.role=="MANAGER" and task.assigned_department:
                return redirect('task_list_manager')
            elif request.user.role=="MANAGER":
                return redirect('emp_task_list_manager')
            elif request.user.role=="ADMIN":
                return redirect('task_list_admin')
    else:
        form = TaskStatusForm(instance=task)
    return render(request, 'tasks/task_update_status.html', {'form': form, 'task': task})

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
    return redirect(request.GET.get("NextPath"), ticket_id=ticket_id)

@login_required
@is_admin_or_manager
def task_assign_from_task(request, task_id):
    parent_task = get_object_or_404(Task, id=task_id)
    sub_departments = Department.objects.filter(parent=parent_task.assigned_department)

    
    sub_departments = Department.objects.filter(parent=parent_task.assigned_department)

    if sub_departments.exists():
        employees = EmployeeProfile.objects.filter(department__in=sub_departments)
    else:
        employees = EmployeeProfile.objects.filter(department=parent_task.assigned_department)

    return render(request, "tasks/Task_Assign.html", {
        "parent_task": parent_task,
        "departments": sub_departments,
        "employees": employees,
    })


def Create_Task_Fom_TASK(request, task_id):
    parent_task = get_object_or_404(Task, id=task_id)
    if request.method == 'POST':
        assign_type = request.POST.get('assign_type')
        if assign_type == 'department':
            description = request.POST.get('description_department')
            dept_id = request.POST.get('department_id')
            department = Department.objects.get(id=dept_id)
            if department:
                Task.objects.create(
                    ticket=parent_task.ticket,
                    assigned_department=department,
                    parent_task=parent_task,
                    description=description,
                    created_by=request.user,
                    title = parent_task.ticket.subject if request.POST.get('DescTask_Title') == "" else request.POST.get('DescTask_Title'),
                    deadline=request.POST.get('deadline_department')
                )
        elif assign_type == 'employees':
            emp_ids = request.POST.getlist('employee_ids')
            for eid in emp_ids:
                emp = EmployeeProfile.objects.get(id=eid)
                desc=(request.POST.get('description_employee'+eid))
                Task.objects.create(
                    ticket=parent_task.ticket,
                    assigned_to=emp,
                    parent_task=parent_task,
                    description=desc,
                    created_by=request.user,
                    title = parent_task.ticket.subject if request.POST.get('Task_Title'+eid) == "" else request.POST.get('Task_Title'+eid),
                    deadline=request.POST.get('deadline'+eid)
                )
    return redirect("task_assign_from_task",task_id)


from .models import Task, TaskComment, TaskAttachment
from .forms import TaskCommentForm, TaskStatusForm
from django.contrib import messages

@login_required
@is_admin_or_manager
def task_review(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    attachments = task.attachments.all()
    comments = task.comments.order_by('-created_at')
    if request.method == 'POST':
        status_form = TaskStatusForm(request.POST, instance=task)
        comment_form = TaskCommentForm(request.POST, request.FILES)
        status_updated = False
        comment_posted = False
        if status_form.is_valid():
            status_form.save()
            status_updated = True
        if comment_form.is_valid() and comment_form.cleaned_data['text']:
            comment = comment_form.save(commit=False)
            comment.task = task
            comment.author = request.user
            comment.save()
            comment_posted = True
        # Optionally show success messages, or reload page
        if status_updated or comment_posted:
            return redirect('task_review', task_id=task.id)
    else:
        status_form = TaskStatusForm(instance=task)
        comment_form = TaskCommentForm()
    return render(request, 'tasks/task_review.html', {
        'task': task,
        'attachments': attachments,
        'comments': comments,
        'status_form': status_form,
        'comment_form': comment_form,
    })

@login_required
def task_employee_detail(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    Outputs = TaskAttachment.objects.filter(Output=True,task=task)
    Attachs = TaskAttachment.objects.filter(Output=False,task=task)
    return render(request, 'tasks/task_employee_detail.html', {'task': task,'Outputs':Outputs,'Attachs':Attachs})


def task_detail(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    Outputs = TaskAttachment.objects.filter(Output=True,task=task)
    Attachs = TaskAttachment.objects.filter(Output=False,task=task)
    return render(request, 'tasks/task_detail.html', {'task': task,'Outputs':Outputs,'Attachs':Attachs})