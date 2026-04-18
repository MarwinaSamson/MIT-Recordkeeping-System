from django.urls import path
from .views import admin_dashboard

app_name = 'admin_app'

urlpatterns = [
    path('dashboard/', admin_dashboard, name='dashboard'),
]
