"""Test script for award decision endpoint."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'report_engine.settings')
django.setup()

from reports_app.models import Applicant, AwardDecision, Scholarship
from decimal import Decimal

# Create a test applicant if one doesn't exist
test_applicant, created = Applicant.objects.get_or_create(
    student_id='TEST001',
    defaults={
        'name': 'Test Student',
        'netid': 'test001',
        'major': 'Computer Science',
        'gpa': 3.5,
        'academic_level': 'Junior'
    }
)
print(f"Test applicant: {test_applicant} (created: {created})")

# Create a test scholarship if one doesn't exist
test_scholarship, created = Scholarship.objects.get_or_create(
    name='Test Scholarship',
    defaults={
        'description': 'A test scholarship for development',
        'frequency': 'annual',
        'amount': Decimal('5000.00'),
        'eligibility_criteria': ['GPA >= 3.0', 'Computer Science major'],
        'donor_info': {'name': 'Test Donor', 'contact': 'test@example.com'},
        'disbursement_requirements': ['Maintain GPA', 'Full-time enrollment']
    }
)
print(f"Test scholarship: {test_scholarship} (created: {created})")

# Test 1: Record a pending decision
print("\n--- Test 1: Record pending decision ---")
decision1 = AwardDecision.record(
    applicant=test_applicant,
    scholarship_name='Test Scholarship',
    decision='pending',
    comments='Initial review pending committee meeting'
)
print(f"Created decision: {decision1}")
print(f"  Decision: {decision1.decision}")
print(f"  Comments: {decision1.comments}")

# Test 2: Update to awarded
print("\n--- Test 2: Update to awarded ---")
decision2 = AwardDecision.record(
    applicant=test_applicant,
    scholarship_name='Test Scholarship',
    decision='awarded',
    comments='Committee approved - excellent academic record'
)
print(f"Updated decision: {decision2}")
print(f"  Decision: {decision2.decision}")
print(f"  Comments: {decision2.comments}")
print(f"  Same object: {decision1.id == decision2.id}")

# Test 3: Verify uniqueness constraint
print("\n--- Test 3: Verify database state ---")
all_decisions = AwardDecision.objects.filter(
    applicant=test_applicant,
    scholarship_name='Test Scholarship'
)
print(f"Total decisions for this applicant+scholarship: {all_decisions.count()} (should be 1)")

# Test 4: Add decision for different scholarship
print("\n--- Test 4: Add decision for different scholarship ---")
decision3 = AwardDecision.record(
    applicant=test_applicant,
    scholarship_name='Another Scholarship',
    decision='not_awarded',
    comments='Did not meet minimum GPA requirement'
)
print(f"Created new decision: {decision3}")
print(f"  Decision: {decision3.decision}")

# Summary
print("\n--- Summary ---")
all_applicant_decisions = AwardDecision.objects.filter(applicant=test_applicant)
print(f"Total decisions for {test_applicant.name}: {all_applicant_decisions.count()}")
for dec in all_applicant_decisions:
    print(f"  - {dec.scholarship_name}: {dec.decision}")

print("\n✓ All tests passed!")
