from django.contrib import admin
from .models import (
	Applicant,
	ReviewerInformationRequest,
	Scholarship,
	ScholarshipAward,
	AwardDecision,
	DisbursementTransaction,
	FinancialAidSystemLog,
	PaymentSchedule,
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


@admin.register(DisbursementTransaction)
class DisbursementTransactionAdmin(admin.ModelAdmin):
	list_display = ('transaction_id', 'scholarship_award', 'amount', 'scheduled_date', 
	                'status', 'financial_aid_system', 'external_transaction_id')
	search_fields = ('transaction_id', 'external_transaction_id', 
	                 'scholarship_award__scholarship_name', 
	                 'scholarship_award__applicant__name',
	                 'scholarship_award__applicant__student_id')
	list_filter = ('status', 'financial_aid_system', 'scheduled_date', 'processed_date')
	readonly_fields = ('created_at', 'updated_at', 'last_retry_at')
	ordering = ('-scheduled_date', '-created_at')
	
	fieldsets = (
		('Transaction Information', {
			'fields': ('transaction_id', 'external_transaction_id', 'scholarship_award')
		}),
		('Financial Details', {
			'fields': ('amount', 'scheduled_date', 'processed_date', 'account_code', 'fund_code')
		}),
		('Status', {
			'fields': ('status', 'financial_aid_system')
		}),
		('Integration Data', {
			'fields': ('submission_payload', 'response_data'),
			'classes': ('collapse',)
		}),
		('Error Information', {
			'fields': ('error_message', 'retry_count', 'last_retry_at'),
			'classes': ('collapse',)
		}),
		('Audit Trail', {
			'fields': ('created_at', 'updated_at', 'created_by', 'updated_by', 'notes'),
			'classes': ('collapse',)
		}),
	)


@admin.register(FinancialAidSystemLog)
class FinancialAidSystemLogAdmin(admin.ModelAdmin):
	list_display = ('system_name', 'operation', 'status', 'request_timestamp', 
	                'response_time_ms', 'http_status_code')
	search_fields = ('system_name', 'operation', 'error_message')
	list_filter = ('system_name', 'status', 'operation', 'request_timestamp')
	readonly_fields = ('request_timestamp', 'response_time_ms')
	ordering = ('-request_timestamp',)
	
	fieldsets = (
		('Request Information', {
			'fields': ('system_name', 'operation', 'request_timestamp', 'transaction')
		}),
		('Request/Response Data', {
			'fields': ('request_data', 'response_data'),
			'classes': ('collapse',)
		}),
		('Status', {
			'fields': ('status', 'http_status_code', 'response_time_ms')
		}),
		('Error Details', {
			'fields': ('error_message',),
			'classes': ('collapse',)
		}),
	)


@admin.register(PaymentSchedule)
class PaymentScheduleAdmin(admin.ModelAdmin):
	list_display = ('scholarship_award', 'payment_number', 'scheduled_amount', 
	                'scheduled_date', 'status', 'conditions_met')
	search_fields = ('scholarship_award__scholarship_name', 
	                 'scholarship_award__applicant__name',
	                 'scholarship_award__applicant__student_id')
	list_filter = ('status', 'conditions_met', 'scheduled_date')
	readonly_fields = ('created_at', 'updated_at', 'conditions_verified_at')
	ordering = ('scholarship_award', 'payment_number')
	
	fieldsets = (
		('Schedule Information', {
			'fields': ('scholarship_award', 'payment_number', 'scheduled_amount', 'scheduled_date')
		}),
		('Conditions', {
			'fields': ('conditions_met', 'required_conditions', 'conditions_verified_at', 'verified_by')
		}),
		('Transaction', {
			'fields': ('disbursement_transaction', 'status')
		}),
		('Additional Information', {
			'fields': ('notes', 'created_at', 'updated_at'),
			'classes': ('collapse',)
		}),
	)


    
