from django.core.management.base import BaseCommand
from datetime import datetime
from reports_app.models import Applicant


class Command(BaseCommand):
    help = 'Seed the database with sample applicant data for testing'

    def handle(self, *args, **kwargs):
        # Sample applicant data (mirrors the examples from views.py)
        applicants_data = [
            {
                'name': "John Doe",
                'student_id': "12345678",
                'netid': "jdoe",
                'major': "Systems Engineering",
                'minor': "Computer Science",
                'academic_achievements': [
                    {
                        'type': 'Dean\'s List',
                        'date': datetime(2024, 12, 15),
                        'description': 'Fall 2024 Semester'
                    },
                    {
                        'type': 'Research Publication',
                        'date': datetime(2025, 3, 1),
                        'title': 'Innovation in Systems Design',
                        'journal': 'Engineering Research Quarterly'
                    }
                ],
                'financial_info': {
                    'fafsa_submitted': True,
                    'efc': 5000,
                    'household_income': '50000-75000',
                    'current_aid': [
                        {'type': 'Federal Grant', 'amount': 2500},
                        {'type': 'State Grant', 'amount': 1500}
                    ]
                },
                'essays': [
                    {
                        'prompt': 'Describe your career goals in engineering.',
                        'content': 'My passion for systems engineering stems from...',
                        'submission_date': datetime(2025, 2, 1),
                        'evaluation': {
                            'score': 9.2,
                            'feedback': 'Excellent vision and clear career trajectory.',
                            'reviewer': 'Dr. Sarah Chen',
                            'date': datetime(2025, 2, 15)
                        }
                    },
                    {
                        'prompt': 'How will this scholarship impact your education?',
                        'content': 'This scholarship will enable me to...',
                        'submission_date': datetime(2025, 2, 1),
                        'evaluation': {
                            'score': 8.8,
                            'feedback': 'Strong understanding of opportunity and impact.',
                            'reviewer': 'Prof. Michael Roberts',
                            'date': datetime(2025, 2, 16)
                        }
                    }
                ],
                'gpa': 3.8,
                'academic_level': "Junior",
                'expected_graduation': datetime(2027, 5, 15),
                'academic_history': [
                    {
                        'term': 'Fall 2024',
                        'courses': [
                            {'code': 'SYE301', 'name': 'Systems Engineering Fundamentals', 'grade': 'A'},
                            {'code': 'CS210', 'name': 'Software Systems', 'grade': 'A-'}
                        ],
                        'gpa': 3.85
                    }
                ],
                'interview_notes': "Conducted on 2025-03-01. Demonstrated strong leadership potential and excellent communication skills. Shows clear understanding of systems engineering principles.",
                'committee_feedback': [
                    {
                        'member': 'Dr. James Wilson',
                        'role': 'Department Chair',
                        'comments': 'Outstanding candidate with proven academic excellence.',
                        'recommendation': 'Highly Recommend',
                        'date': datetime(2025, 3, 5)
                    },
                    {
                        'member': 'Prof. Lisa Martinez',
                        'role': 'Scholarship Committee Head',
                        'comments': 'Strong technical background and leadership potential.',
                        'recommendation': 'Strongly Recommend',
                        'date': datetime(2025, 3, 6)
                    }
                ]
            },
            {
                'name': "Alice Smith",
                'student_id': "12346789",
                'netid': "asmith",
                'major': "Engineering",
                'minor': "Mathematics",
                'gpa': 3.8,
                'academic_level': "Junior",
                'expected_graduation': datetime(2027, 5, 15),
                'academic_history': [{
                    'term': 'Fall 2024',
                    'courses': [
                        {'code': 'ENG301', 'name': 'Advanced Engineering', 'grade': 'A'},
                        {'code': 'MATH400', 'name': 'Applied Mathematics', 'grade': 'A-'}
                    ],
                    'gpa': 3.8
                }],
                'essays': [{
                    'prompt': 'Describe your research interests.',
                    'content': 'My research focuses on sustainable engineering...',
                    'submission_date': datetime(2025, 2, 1),
                    'evaluation': {
                        'score': 9.5,
                        'feedback': 'Exceptional research vision and clarity.',
                        'reviewer': 'Dr. Thompson',
                        'date': datetime(2025, 2, 10)
                    }
                }],
                'financial_info': {
                    'fafsa_submitted': True,
                    'efc': 4000,
                    'household_income': '40000-60000'
                },
                'interview_notes': "Outstanding interview performance. Shows great potential.",
                'committee_feedback': [{
                    'member': 'Dr. Rodriguez',
                    'comments': 'Top candidate with excellent credentials.',
                    'recommendation': 'Highly Recommend',
                    'date': datetime(2025, 3, 1)
                }]
            },
            {
                'name': "Bob Johnson",
                'student_id': "12347890",
                'netid': "bjohnson",
                'major': "Computer Science",
                'gpa': 3.2,
                'academic_level': "Sophomore",
                'expected_graduation': datetime(2027, 12, 15),
                'essays': [{
                    'prompt': 'Describe your programming experience.',
                    'content': 'I have developed several applications...',
                    'submission_date': datetime(2025, 2, 2),
                    'evaluation': {
                        'score': 7.8,
                        'feedback': 'Good technical background, needs more detail.',
                        'reviewer': 'Prof. Chen',
                        'date': datetime(2025, 2, 12)
                    }
                }],
                'financial_info': {
                    'fafsa_submitted': True,
                    'efc': 8000,
                    'household_income': '75000-100000'
                }
            }
        ]

        # Create/update applicants using our model's from_dict helper
        created = 0
        updated = 0
        for data in applicants_data:
            student_id = data['student_id']
            # Use get_or_create to avoid duplicates
            applicant, is_new = Applicant.objects.get_or_create(
                student_id=student_id,
                defaults=data
            )
            if not is_new:
                # Update existing record with new data
                for key, value in data.items():
                    setattr(applicant, key, value)
                applicant.save()
                updated += 1
            else:
                created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully seeded sample applicants (created={created}, updated={updated})'
            )
        )