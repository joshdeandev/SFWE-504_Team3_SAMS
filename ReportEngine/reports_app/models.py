from django.db import models
from django.utils import timezone


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
        """Recursively convert datetime/date objects inside lists/dicts to ISO-formatted strings so
        they can be stored in JSONField or serialized to JSON.
        """
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
        # For other types (int, float, str, bool, etc.) return as-is
        return obj

    @classmethod
    def from_dict(cls, data: dict):
        """Create or update an Applicant from a dictionary similar to the previous ApplicantData shape.

        This helper is convenient for seeding sample data or migrating in-memory examples into the DB.
        It performs a get_or_create on student_id when available.
        """
        # Sanitize nested structures so JSONField assignments contain only JSON-serializable types
        sanitized = {
            'academic_achievements': cls._make_json_serializable(data.get('academic_achievements', [])),
            'financial_info': cls._make_json_serializable(data.get('financial_info', {})),
            'essays': cls._make_json_serializable(data.get('essays', [])),
            'academic_history': cls._make_json_serializable(data.get('academic_history', [])),
            'committee_feedback': cls._make_json_serializable(data.get('committee_feedback', [])),
        }

        # Convert expected_graduation to date if it's a datetime/string
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

        # If no student_id provided, create a new record (non-unique)
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
