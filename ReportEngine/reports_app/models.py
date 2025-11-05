from django.db import models
from django.utils import timezone
from typing import Dict, List, Optional, Any
from datetime import datetime


class Applicant(models.Model):
    """Persistent Applicant model representing the data previously held in ApplicantData dataclass.

    Nested and variable fields are stored in JSONField for flexibility (essays, achievements, history, etc.).
    """
    name = models.CharField(max_length=255)
    student_id = models.CharField(max_length=64, unique=True)
    netid = models.CharField(max_length=64, unique=True, null=True, blank=True)
    major = models.CharField(max_length=255, blank=True)
    minor = models.CharField(max_length=255, null=True, blank=True)
    gpa = models.FloatField(default=0.0)
    academic_level = models.CharField(max_length=64, blank=True)
    expected_graduation = models.DateField(null=True, blank=True)

    # Use JSON fields for complex / nested data structures
    academic_achievements = models.JSONField(default=list, blank=True)
    financial_info = models.JSONField(default=dict, blank=True)
    essays = models.JSONField(default=list, blank=True)
    academic_history = models.JSONField(default=list, blank=True)
    interview_notes = models.TextField(null=True, blank=True)
    committee_feedback = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Applicant'
        verbose_name_plural = 'Applicants'

    def __str__(self):
        return f"{self.name} ({self.student_id})"
    
    @staticmethod
    def _make_json_serializable(obj):
        """Recursively convert datetime/date objects to ISO strings for JSON storage."""
        from datetime import datetime, date
        if obj is None:
            return obj
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, dict):
            return {k: Applicant._make_json_serializable(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [Applicant._make_json_serializable(v) for v in obj]
        if isinstance(obj, tuple):
            return tuple(Applicant._make_json_serializable(v) for v in obj)
        return obj

    @classmethod
    def from_dict(cls, data: dict):
        """Create or update an Applicant from a dictionary similar to the previous ApplicantData shape.

        Sanitizes nested structures (dates -> ISO strings) so they are safe to store in JSONFields.
        Performs update_or_create when student_id is provided.
        """
        sanitized = {
            'academic_achievements': cls._make_json_serializable(data.get('academic_achievements', [])),
            'financial_info': cls._make_json_serializable(data.get('financial_info', {})),
            'essays': cls._make_json_serializable(data.get('essays', [])),
            'academic_history': cls._make_json_serializable(data.get('academic_history', [])),
            'committee_feedback': cls._make_json_serializable(data.get('committee_feedback', [])),
        }

        expected_graduation = data.get('expected_graduation')
        if hasattr(expected_graduation, 'date'):
            expected_graduation = expected_graduation.date()

        student_id = data.get('student_id')
        if student_id:
            obj, created = cls.objects.update_or_create(
                student_id=student_id,
                defaults={
                    'name': data.get('name', ''),
                    'netid': data.get('netid'),
                    'major': data.get('major', ''),
                    'minor': data.get('minor'),
                    'gpa': data.get('gpa', 0.0) or 0.0,
                    'academic_level': data.get('academic_level', ''),
                    'expected_graduation': expected_graduation,
                    'academic_achievements': sanitized['academic_achievements'],
                    'financial_info': sanitized['financial_info'],
                    'essays': sanitized['essays'],
                    'academic_history': sanitized['academic_history'],
                    'interview_notes': data.get('interview_notes'),
                    'committee_feedback': sanitized['committee_feedback']
                }
            )
            return obj

        # If no student_id provided, create a new record (non-unique temporary id)
        return cls.objects.create(
            name=data.get('name', ''),
            student_id=data.get('student_id') or f"tmp-{int(timezone.now().timestamp())}",
            netid=data.get('netid'),
            major=data.get('major', ''),
            minor=data.get('minor'),
            gpa=data.get('gpa', 0.0) or 0.0,
            academic_level=data.get('academic_level', ''),
            expected_graduation=expected_graduation,
            academic_achievements=sanitized['academic_achievements'],
            financial_info=sanitized['financial_info'],
            essays=sanitized['essays'],
            academic_history=sanitized['academic_history'],
            interview_notes=data.get('interview_notes'),
            committee_feedback=sanitized['committee_feedback']
        )


class ScholarshipAward(models.Model):
    """Model representing a scholarship award to a specific applicant."""
    scholarship_name = models.CharField(max_length=255)
    applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE, related_name='awards')
    award_date = models.DateTimeField()
    award_amount = models.DecimalField(max_digits=10, decimal_places=2)
    disbursement_dates = models.JSONField(default=list)  # List[datetime] as ISO strings
    requirements_met = models.JSONField(default=list)  # List[str]
    requirements_pending = models.JSONField(default=list)  # List[str]
    status = models.CharField(max_length=20, choices=[
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('revoked', 'Revoked')
    ])
    performance_metrics = models.JSONField(default=dict)  # Dict[str, Any]
    essays_evaluation = models.JSONField(null=True, blank=True)  # Optional[List[Dict[str, Any]]]
    interview_notes = models.TextField(null=True, blank=True)
    committee_feedback = models.JSONField(null=True, blank=True)  # Optional[List[Dict[str, str]]]
    notes = models.TextField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-award_date']
        verbose_name = 'Scholarship Award'
        verbose_name_plural = 'Scholarship Awards'

    def __str__(self):
        return f"{self.scholarship_name} awarded to {self.applicant.name}"

    @classmethod
    def from_dataclass(cls, data):
        """Create or update a ScholarshipAward from the previous dataclass-style dict.
        
        This helper converts from the old dataclass format to the new model,
        handling date serialization for JSONFields.
        """
        # Helper to convert datetime to ISO format in nested structures
        def serialize_dates(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            if isinstance(obj, dict):
                return {k: serialize_dates(v) for k, v in obj.items()}
            if isinstance(obj, (list, tuple)):
                return [serialize_dates(v) for v in obj]
            return obj

        # Convert datetime lists to ISO strings for JSONField
        disbursement_dates = [d.isoformat() for d in data.get('disbursement_dates', [])]
        essays_eval = serialize_dates(data.get('essays_evaluation'))
        committee_feedback = serialize_dates(data.get('committee_feedback'))
        performance_metrics = serialize_dates(data.get('performance_metrics', {}))

        return cls(
            scholarship_name=data['scholarship_name'],
            applicant=data['applicant'],
            award_date=data['award_date'],
            award_amount=data['award_amount'],
            disbursement_dates=disbursement_dates,
            requirements_met=data.get('requirements_met', []),
            requirements_pending=data.get('requirements_pending', []),
            status=data.get('status', 'active'),
            performance_metrics=performance_metrics,
            essays_evaluation=essays_eval,
            interview_notes=data.get('interview_notes'),
            committee_feedback=committee_feedback,
            notes=data.get('notes')
        )
