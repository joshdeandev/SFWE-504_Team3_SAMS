from django.contrib import admin
from .models import Applicant


@admin.register(Applicant)
class ApplicantAdmin(admin.ModelAdmin):
	list_display = ('name', 'student_id', 'netid', 'major', 'gpa', 'academic_level')
	search_fields = ('name', 'student_id', 'netid', 'major')
	list_filter = ('academic_level', 'major')
