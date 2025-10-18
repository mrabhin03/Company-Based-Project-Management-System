from django.urls import path
from . import views

urlpatterns = [
    path('Employee', views.performance_overview, name='performance_overview'),
    path('Department/', views.department_performance, name='department_performance'),
    path('Department/<int:department_id>/', views.department_performance, name='department_performance_detail'),
]
