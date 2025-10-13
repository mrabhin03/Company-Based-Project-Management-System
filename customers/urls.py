# customer/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.customer_dashboard, name='customer_dashboard'),
    path('register/', views.customer_register, name='customer_register'),
    path('login/', views.customer_login, name='customer_login'),
    path('logout/', views.customer_logout, name='customer_logout'),
    path('dashboard/', views.customer_dashboard, name='customer_dashboard'),



    path('ticket/create/', views.ticket_create, name='ticket_create'),
    path('ticket/view/', views.ticket_list_admin, name='ticket_list_admin'),
    path('ticket/StatusUpdate/<int:ticket_id>', views.ticket_update_status, name='ticket_update_status'),
    path('ticket/<int:ticket_id>/edit/', views.ticket_edit, name='ticket_edit'),
    path('tickets/<int:ticket_id>/', views.ticket_detail, name='ticket_detail'),
    path('Mytickets/<int:ticket_id>/', views.Client_ticket_detail, name='Client_ticket_detail'),
    path('tickets/<int:ticket_id>/assign/', views.ticket_assign, name='ticket_assign'),
    path('tickets/<int:ticket_id>/assign/save/', views.ticket_assign_save, name='ticket_assign_save'),
    path('ticket/<int:ticket_id>/responses/', views.ticket_response, name='ticket_response'),
    path('ticket/<int:ticket_id>/customer_reply/', views.customer_reply, name='customer_reply'),
    path('ticket/<int:ticket_id>/feedback/', views.ticket_feedback, name='ticket_feedback'),

    path('attachment/delete/<int:attachment_id>/', views.delete_ticket_attachment, name='delete_ticket_attachment'),
    path('feedbacks/', views.feedback_list, name='feedback_list'),

    path('profile/', views.customer_profile, name='customer_profile'),
    path('profile/edit/', views.customer_edit, name='customer_edit'),
    path('profile/change-password/', views.customer_change_password, name='customer_change_password'),
    

    path('bug-reports/delete/<int:bug_id>/', views.delete_bug, name='delete_bug'),
    path('bug-reports/new/', views.bug_report_create, name='bug_report_create'),
    path('bug-reports/new/<int:ticket_id>/', views.bug_report_create, name='bug_report_create_with_ticket'),
    path('bug-reports/update-status/<int:bug_id>/', views.update_bug_status, name='update_bug_status'),
]
