from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='reports_home'),
    path('analytics/', views.combined_analytics, name='analytics_dashboard'),
    path('request-information/', views.request_information, name='request_information'),
    path('view-request-logs/', views.view_request_logs, name='view_request_logs'),
    path('clear-request-logs/', views.clear_request_logs, name='clear_request_logs'),
    path('award-decision/', views.award_scholarship, name='award_scholarship'),
    path('prescreening-report/', views.view_prescreening_report, name='view_prescreening_report'),
]
