from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('users.urls')),
    path('company/', include('company.urls')),
    path('tasks/', include('tasks.urls')),
    path('performance/', include('performance.urls')),
    path('customers/', include('customers.urls')),
    path('', include('customers.urls')),

]
