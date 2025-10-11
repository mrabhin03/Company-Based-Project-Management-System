from django.urls import path
from . import views

urlpatterns = [
    # Department
    path('departments/', views.department_list, name='department_list'),
    path('departments/create/', views.department_create, name='department_create'),
    path('departments/edit/<int:pk>/', views.department_edit, name='department_edit'),
    path('department/<int:dept_id>/', views.department_view, name='department_view'),


    # Position
    path('positions/', views.position_list, name='position_list'),
    path('positions/create/', views.position_create, name='position_create'),
    path('positions/edit/<int:pk>/', views.position_edit, name='position_edit'),

    # Benefit
    path('benefits/', views.benefit_list, name='benefit_list'),
    path('benefits/create/', views.benefit_create, name='benefit_create'),
    path('benefits/edit/<int:pk>/', views.benefit_edit, name='benefit_edit'),
]
