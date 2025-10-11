from django.urls import path
from . import views

urlpatterns = [
    path('', views.performance_overview, name='performance_overview'),
]
