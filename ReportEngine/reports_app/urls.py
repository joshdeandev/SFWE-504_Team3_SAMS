from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='reports_home'),
    path('request-information/', views.request_information, name='request_information'),
    path('view-request-logs/', views.view_request_logs, name='view_request_logs'),
]
