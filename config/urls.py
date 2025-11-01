"""URL Configuration for SAMS project."""

from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.urls import reverse_lazy

urlpatterns = [
    path('', RedirectView.as_view(url='/reports/', permanent=False)),
    path('admin/', admin.site.urls),
    path('reports/', include('ReportEngine.reports_app.urls')),
]