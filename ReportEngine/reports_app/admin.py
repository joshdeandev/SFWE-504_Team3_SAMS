from django.contrib import admin
from .models import Applicant, ReviewerInformationRequest


@admin.register(Applicant)
class ApplicantAdmin(admin.ModelAdmin):
	list_display = ('name', 'student_id', 'netid', 'major', 'gpa', 'academic_level')
	search_fields = ('name', 'student_id', 'netid', 'major')
	list_filter = ('academic_level', 'major')


@admin.register(ReviewerInformationRequest)
class ReviewerInformationRequestAdmin(admin.ModelAdmin):
	list_display = ('applicant', 'reviewer_name', 'scholarship_name', 'request_type', 
	                'priority', 'status', 'requested_at', 'fulfilled_at')
	search_fields = ('applicant__name', 'applicant__student_id', 'reviewer_name', 
	                 'scholarship_name', 'request_type', 'request_details')
	list_filter = ('status', 'priority', 'request_type', 'requested_at')
	readonly_fields = ('requested_at', 'fulfilled_at')
	ordering = ('-requested_at',)
	
	fieldsets = (
		('Request Information', {
			'fields': ('applicant', 'reviewer_name', 'reviewer_email', 'scholarship_name')
		}),
		('Request Details', {
			'fields': ('request_type', 'request_details', 'priority', 'status')
		}),
		('Fulfillment', {
			'fields': ('requested_at', 'fulfilled_at', 'fulfillment_notes')
		}),
	)
