from django.contrib import admin
from .models import (
	Applicant,
	ReviewerInformationRequest,
	Scholarship,
	ScholarshipAward,
	AwardDecision,
)


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


@admin.register(Scholarship)
class ScholarshipAdmin(admin.ModelAdmin):
	list_display = ('name', 'amount', 'frequency', 'deadline')
	search_fields = ('name',)
	list_filter = ('frequency',)
	ordering = ('name',)


@admin.register(ScholarshipAward)
class ScholarshipAwardAdmin(admin.ModelAdmin):
	list_display = ('scholarship_name', 'applicant', 'award_date', 'award_amount', 'status')
	search_fields = ('scholarship_name', 'applicant__name', 'applicant__student_id')
	list_filter = ('status',)
	ordering = ('-award_date',)


@admin.register(AwardDecision)
class AwardDecisionAdmin(admin.ModelAdmin):
	list_display = ('applicant', 'scholarship_name', 'decision', 'decided_at')
	search_fields = ('applicant__name', 'applicant__student_id', 'scholarship_name')
	list_filter = ('decision', 'decided_at')
	ordering = ('-decided_at',)


    
