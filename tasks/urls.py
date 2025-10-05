# tasks/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('admin/', views.task_list_admin, name='task_list_admin'),
    path('create/', views.task_create, name='task_create'),
    path('tasks/add/', views.task_create, name='task_add'),
    path('tasks/<int:task_id>/edit/', views.task_edit, name='task_edit'),
    path('employee/', views.task_list_employee, name='task_list_employee'),
    path('employee/update/<int:task_id>/', views.task_update_status, name='task_update_status'),
    path('create/<int:ticket_id>/', views.task_create_from_ticket, name='task_create_from_ticket'),
    path('task/<int:task_id>/decline/', views.task_decline, name='task_decline'),
]
