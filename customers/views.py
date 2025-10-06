# customer/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from .forms import CustomerRegistrationForm, CustomerLoginForm, TicketForm
from .models import Ticket, Customer
from users.decorators import is_admin, is_manager,admin_required,is_admin_or_manager
from .forms import TicketStatusForm
from tasks.models import Task
from users.models import EmployeeProfile
from company.models import Department
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
CustomUser = get_user_model()

def is_customer(user):
    return user.is_authenticated and user.role == CustomUser.ROLE_CUSTOMER
def customer_register(request):
    if request.method == 'POST':
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            Customer.objects.create(user=user)
            login(request, user)
            return redirect('customer_dashboard')
    else:
        form = CustomerRegistrationForm()
    return render(request, 'customer/register.html', {'form': form})

def customer_login(request):
    if request.method == 'POST':
        form = CustomerLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('customer_dashboard')
    else:
        form = CustomerLoginForm()
    return render(request, 'customer/login.html', {'form': form})

@login_required(login_url='/customers/login/',redirect_field_name='')
def customer_logout(request):
    logout(request)
    return redirect('customer_login')


@login_required(login_url='/customers/login/',redirect_field_name='')
@user_passes_test(is_customer,login_url='/customers/login/',redirect_field_name='')
def customer_dashboard(request):
    tickets = request.user.customer.tickets.all()
    return render(request, 'customer/dashboard.html', {'tickets': tickets})



@login_required(login_url='/customers/login/',redirect_field_name='')
def ticket_create(request):
    if request.method == 'POST':
        form = TicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.customer = request.user.customer
            ticket.save()
            return redirect('customer_dashboard')
    else:
        form = TicketForm()
    return render(request, 'customer/ticket_form.html', {'form': form})

@login_required(login_url='/customers/login/',redirect_field_name='')
def ticket_edit(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id, customer=request.user.customer)
    if request.method == 'POST':
        form = TicketForm(request.POST, instance=ticket)
        if form.is_valid():
            form.save()
            return redirect('customer_dashboard')
    else:
        form = TicketForm(instance=ticket)
    return render(request, 'customer/ticket_form.html', {'form': form})

def ticket_detail(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    return render(request, 'customer/ticket_detail.html', {'ticket': ticket})


def ticket_list_admin(request):
    tickets = Ticket.objects.all()
    return render(request, 'customer/ticket_list_admin.html', {'tickets': tickets})

@admin_required
def ticket_update_status(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    if request.method == 'POST':
        form = TicketStatusForm(request.POST, instance=ticket)
        if form.is_valid():
            form.save()
            return redirect('ticket_list_admin')
    else:
        form = TicketStatusForm(instance=ticket)
    return render(request, 'customer/ticket_update_status.html', {'form': form, 'ticket': ticket})


@login_required(redirect_field_name='')
@is_admin_or_manager
def ticket_assign(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    departments = Department.objects.all()
    employees = EmployeeProfile.objects.all()
    return render(request, 'customer/ticket_assign.html', {
        'ticket': ticket,
        'departments': departments,
        'employees': employees
    })


@login_required(redirect_field_name='')
@is_admin_or_manager
def ticket_assign_save(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    if request.method == 'POST':
        assign_type = request.POST.get('assign_type')
        if assign_type == 'department':
            description = request.POST.get('description_department')
            dept_id = request.POST.get('department_id')
            department = Department.objects.get(id=dept_id)
            # Create a task for manager of department (first step)
            manager = CustomUser.objects.filter(role='MANAGER', employeeprofile__department=department).first()
            if manager:
                Task.objects.create(
                    ticket=ticket,
                    assigned_to=manager.employeeprofile,
                    description=description,
                    created_by=request.user,
                    title = ticket.subject if request.POST.get('DescTask_Title') == "" else request.POST.get('DescTask_Title'),
                    deadline=request.POST.get('deadline_department')
                )
        elif assign_type == 'employees':
            emp_ids = request.POST.getlist('employee_ids')
            for eid in emp_ids:
                emp = EmployeeProfile.objects.get(id=eid)
                desc=(request.POST.get('description_employee'+eid))
                Task.objects.create(
                    ticket=ticket,
                    assigned_to=emp,
                    description=desc,
                    created_by=request.user,
                    title = ticket.subject if request.POST.get('Task_Title'+eid) == "" else request.POST.get('Task_Title'+eid),
                    deadline=request.POST.get('deadline'+eid)
                )
        return redirect('ticket_assign', ticket_id=ticket.id)
    