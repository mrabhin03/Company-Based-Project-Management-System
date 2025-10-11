# tasks/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('admin/', views.task_list_admin, name='task_list_admin'),
    path('DepartmentTasks/', views.task_list_manager, name='task_list_manager'),
    path('EmployeeTasks/', views.emp_task_list_manager, name='emp_task_list_manager'),
    path('create/', views.task_create, name='task_create'),
    path('tasks/add/', views.task_create, name='task_add'),
    path('tasks/<int:task_id>/edit/', views.task_edit, name='task_edit'),
    path('task/<int:task_id>/', views.task_detail, name='task_detail'),
    path('employee/', views.task_list_employee, name='task_list_employee'),
    path('create/<int:ticket_id>/', views.task_create_from_ticket, name='task_create_from_ticket'),

    path('AssignTask/<int:task_id>/', views.task_assign_from_task, name='task_assign_from_task'),
    path('CreateTaskFromTask/<int:task_id>/', views.Create_Task_Fom_TASK, name='Create_Task_Fom_TASK'),

    path('task/<int:task_id>/decline/', views.task_decline, name='task_decline'),
    path('review/<int:task_id>/', views.task_review, name='task_review'),   
    path('TaskStatus/update/<int:task_id>/', views.task_update_status, name='task_update_status'),
    path('employee/task/<int:task_id>/', views.task_employee_detail, name='task_employee_detail'),
]
