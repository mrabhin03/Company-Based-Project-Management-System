# customer/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from .forms import CustomerRegistrationForm, CustomerLoginForm, TicketForm
from .models import Ticket, Customer,TicketFeedback,TicketResponse,TicketAttachment,BugReport
from users.decorators import is_admin, is_manager,admin_required,is_admin_or_manager
from .forms import TicketStatusForm,TicketAttachmentForm,CustomerForm,BugReportForm,BugReportStatusForm,TicketStatusFilterForm
from tasks.models import Task
from users.models import EmployeeProfile
from company.models import Department
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
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
    for tic in tickets:
        taskDetails=getTicketDetails(tic)
        total=taskDetails[0]
        pending=taskDetails[1]
        if total==0:
            per=0
        elif pending==0 and (tic.status!="Resolved" and tic.status!="Closed"):
            per=95
        else:
            per=int(((total-pending)/total)*100)
        tic.per=per
        responses = tic.responses.filter(
            is_customer_reply=False,
            status=False
        ).count()
        tic.Notification=responses
    return render(request, 'customer/dashboard.html', {'tickets': tickets})



@login_required(login_url='/customers/login/',redirect_field_name='')
def ticket_create(request):
    if request.method == 'POST':
        form = TicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.customer = request.user.customer
            ticket.save()
            # Save each uploaded file
            for f in request.FILES.getlist('file'):
                TicketAttachment.objects.create(
                    ticket=ticket,
                    file=f,
                    uploaded_by=request.user
                )
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
            for f in request.FILES.getlist('file'):
                TicketAttachment.objects.create(
                    ticket=ticket,
                    file=f,
                    uploaded_by=request.user
                )
            return redirect('Client_ticket_detail',ticket_id)
    else:
        form = TicketForm(instance=ticket)
    attachments = ticket.attachments.filter(Output=False)
    return render(request, 'customer/ticket_form.html', {'form': form, 'ticket': ticket,'attachment':attachments})

@login_required
def delete_ticket_attachment(request, attachment_id):
    attachment = get_object_or_404(TicketAttachment, id=attachment_id)
    ticket = attachment.ticket
    # Only the ticket owner (customer) or admins/managers can delete
    if request.user == ticket.customer.user or request.user.role in ['ADMIN', 'MANAGER']:
        attachment.file.delete(save=False)  # Delete file from storage
        attachment.delete()  # Delete DB record
    return redirect('ticket_edit', ticket_id=ticket.id)


def ticket_detail(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    attachments = ticket.attachments.filter(Output=False)
    Outputs = ticket.attachments.filter(Output=True)
    responses_count = ticket.responses.filter(
        is_customer_reply=True,
        status=False
    ).count()
    ticket.notification=responses_count
    tasksdetails=Task.objects.filter(ticket=ticket,parent_task=None)
    bugs=BugReport.objects.filter(related_ticket=ticket).order_by('-created_at')
    bugsSt=BugReport.objects.filter(related_ticket=ticket).exclude(status="Closed").count()
    return render(request, 'customer/ticket_detail.html', {'ticket': ticket, 'attachments': attachments,"tasksdetails":tasksdetails,"Outputs":Outputs,"bugs":bugs,"bugsSt":bugsSt})

def Client_ticket_detail(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    attachments = ticket.attachments.filter(Output=False)
    Outputs = ticket.attachments.filter(Output=True)
    responses_count = ticket.responses.filter(
        is_customer_reply=False,
        status=False
    ).count()
    ticket.notification=responses_count
    bugs=BugReport.objects.filter(related_ticket=ticket).order_by('-created_at')
    return render(request, 'customer/Clients_ticketView.html', {'ticket': ticket, 'attachments': attachments,"Outputs":Outputs,"bugs":bugs})
def getTicketDetails(ticket):
    total=0
    pending=0
    tasks=Task.objects.filter(ticket=ticket)
    for tic in tasks:
        total+=1
        if tic.status!="Completed":
            pending+=1
    return [total,pending]

def ticket_list_admin(request):
    status="All"
    if request.GET.get("status") and request.GET.get("status")!="all":
        status=request.GET.get("status")
        tickets = Ticket.objects.filter(status=request.GET.get("status"))
    else:
        tickets = Ticket.objects.all()
    for tic in tickets:
        taskDetails=getTicketDetails(tic)
        tic.total=taskDetails[0] 
        tic.Complete=taskDetails[0]-taskDetails[1] 
        responses = tic.responses.filter(
            is_customer_reply=True,
            status=False
        ).count()
        tic.Notification=responses
    form=TicketStatusFilterForm(initial={'status': status})
    return render(request, 'customer/ticket_list_admin.html', {'tickets': tickets,"form":form})

# @admin_required
def ticket_update_status(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    if request.method=='GET' and request.GET.get("ticket_id"):
        ticket.status="Canceled"
        ticket.save()
        return redirect('Client_ticket_detail',ticket_id)
    if request.method == 'POST':
        form = TicketStatusForm(request.POST, instance=ticket)
        if form.is_valid():
            form.save()
            for f in request.FILES.getlist('file'):
                TicketAttachment.objects.create(
                    ticket=ticket,
                    file=f,
                    uploaded_by=request.user,
                    Output=True
                )
            return redirect('ticket_detail',ticket_id)
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
            if department:
                Task.objects.create(
                    ticket=ticket,
                    assigned_department=department,
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
    
@login_required
def ticket_response(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    responses = ticket.responses.all().order_by('created_at')

    if request.method == "POST":
        message = request.POST.get("message")
        TicketResponse.objects.create(
            ticket=ticket,
            responder=request.user,
            message=message,
            is_customer_reply=False
        )
        messages.success(request, "Response sent successfully.")
        return redirect('ticket_response', ticket_id=ticket_id)
    for tic in responses:
        if tic.is_customer_reply==True:
            tic.status=True
            tic.save()
    return render(request, 'customer/ticket_response.html', {'ticket': ticket, 'responses': responses})


@login_required
def customer_reply(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    responses = ticket.responses.all().order_by('created_at')

    if request.method == "POST":
        message = request.POST.get("message")
        TicketResponse.objects.create(
            ticket=ticket,
            responder=request.user,
            message=message,
            is_customer_reply=True
        )
        messages.success(request, "Your reply was sent successfully.")
        return redirect('customer_reply', ticket_id=ticket_id)
    for tic in responses:
        if tic.is_customer_reply==False:
            tic.status=True
            tic.save()

    return render(request, 'customer/customer_reply.html', {'ticket': ticket, 'responses': responses})
    
@login_required
def ticket_feedback(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)

    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        TicketFeedback.objects.create(
            ticket=ticket,
            rating=rating,
            comment=comment
        )
        messages.success(request, 'Thank you for your feedback!')
        return redirect('customer_dashboard')

    return render(request, 'customer/feedback.html', {'ticket': ticket})

@login_required
def feedback_list(request):
    if request.user.role == 'ADMIN':
        feedbacks = TicketFeedback.objects.select_related('ticket').all().order_by('-created_at')
    elif request.user.role == 'MANAGER':
        # Manager sees only feedback for tickets under their department
        feedbacks = TicketFeedback.objects.filter(
            ticket__department=request.user.employeeprofile.department
        ).select_related('ticket').order_by('-created_at')
    elif request.user.role == 'CUSTOMER':
        # Customer sees only their own feedbacks
        feedbacks = TicketFeedback.objects.filter(
            ticket__customer=request.user.customer
        ).select_related('ticket').order_by('-created_at')
    else:
        feedbacks = TicketFeedback.objects.none()

    return render(request, 'customer/feedback_list.html', {'feedbacks': feedbacks})

@login_required
def customer_edit(request):
    customer = request.user
    if request.method == "POST":
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            return redirect('customer_profile')
    else:
        form = CustomerForm(instance=customer)
    return render(request, 'customer/customer_edit.html', {'form': form})

from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash

@login_required
def customer_change_password(request):
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            return redirect('customer_profile')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'customer/customer_change_password.html', {'form': form})


@login_required
def customer_profile(request):
    customer = request.user.customer
    return render(request, 'customer/customer_profile.html', {'customer': customer})




@login_required
def bug_report_list(request):
    bug_reports = BugReport.objects.filter(reporter=request.user).order_by('-created_at')
    return render(request, 'customer/bug_report_list.html', {'bug_reports': bug_reports})

@login_required
def bug_report_create(request, ticket_id=None):
    ticket = None
    if ticket_id:
        ticket = get_object_or_404(Ticket, id=ticket_id)
    if request.method == 'POST':
        form = BugReportForm(request.POST)
        if form.is_valid():
            bug_report = form.save(commit=False)
            bug_report.reporter = request.user
            if ticket:
                ticket.status="Pending"
                ticket.save()
                bug_report.related_ticket = ticket
            bug_report.save()
            return redirect('Client_ticket_detail',ticket_id)
    else:
        form = BugReportForm()
    return render(request, 'customer/bug_report_form.html', {'form': form, 'ticket': ticket})

@login_required
def delete_bug(request, bug_id):
    bug = get_object_or_404(BugReport, id=bug_id)
    ticket_id=bug.related_ticket.id
    if request.method == "GET":
        bug.delete()
        pass
    return redirect('Client_ticket_detail',ticket_id)

@login_required
def update_bug_status(request, bug_id):
    bug = get_object_or_404(BugReport, id=bug_id)
    if request.method == 'POST':
        form = BugReportStatusForm(request.POST, instance=bug)
        if form.is_valid():
            form.save()
            return redirect('ticket_detail',request.POST.get("TicketID"))
    else:
        form = BugReportStatusForm(instance=bug)
    return render(request, 'customer/bug_report_status_form.html', {'form': form, 'bug': bug})