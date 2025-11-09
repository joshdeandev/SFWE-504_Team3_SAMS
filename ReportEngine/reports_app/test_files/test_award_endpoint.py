"""Test the award_scholarship HTTP endpoint."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'report_engine.settings')
django.setup()

from django.test import Client
from reports_app.models import Applicant, AwardDecision, ScholarshipAward

# Create a test client
client = Client()

# Ensure test applicant exists
test_applicant, _ = Applicant.objects.get_or_create(
    student_id='TEST001',
    defaults={
        'name': 'Test Student',
        'netid': 'test001',
        'major': 'Computer Science',
        'gpa': 3.5,
        'academic_level': 'Junior'
    }
)

print("--- Test 1: POST award decision (pending) ---")
response = client.post('/award-decision/', {
    'applicant_id': 'TEST001',
    'scholarship_name': 'HTTP Test Scholarship',
    'decision': 'pending',
    'comments': 'Submitted via HTTP endpoint'
})
print(f"Status: {response.status_code}")
print(f"Response: {response.content.decode()}")

# Verify it was created
decision = AwardDecision.objects.filter(
    applicant__student_id='TEST001',
    scholarship_name='HTTP Test Scholarship'
).first()
print(f"Decision in DB: {decision}")
print(f"  Decision: {decision.decision if decision else 'N/A'}")
print(f"  Comments: {decision.comments if decision else 'N/A'}")

print("\n--- Test 2: POST award decision (awarded) with ScholarshipAward creation ---")
# Clear any existing awards for clean test
ScholarshipAward.objects.filter(
    applicant=test_applicant,
    scholarship_name='HTTP Test Scholarship'
).delete()

response = client.post('/award-decision/', {
    'applicant_id': 'TEST001',
    'scholarship_name': 'HTTP Test Scholarship',
    'decision': 'awarded',
    'comments': 'Approved - creating award record',
    'create_award': 'yes',
    'award_amount': '2500.00'
})
print(f"Status: {response.status_code}")
print(f"Response: {response.content.decode()}")

# Verify award was created
award = ScholarshipAward.objects.filter(
    applicant=test_applicant,
    scholarship_name='HTTP Test Scholarship'
).first()
print(f"ScholarshipAward created: {award is not None}")
if award:
    print(f"  Amount: ${award.award_amount}")
    print(f"  Status: {award.status}")
    print(f"  Notes: {award.notes}")

print("\n--- Test 3: POST with missing fields (should fail) ---")
response = client.post('/award-decision/', {
    'scholarship_name': 'Missing Applicant Test'
})
print(f"Status: {response.status_code} (expected 400)")
print(f"Response: {response.content.decode()}")

print("\n--- Test 4: POST with non-existent applicant (should fail) ---")
response = client.post('/award-decision/', {
    'applicant_id': 'NONEXISTENT999',
    'scholarship_name': 'Test',
    'decision': 'pending'
})
print(f"Status: {response.status_code} (expected 404)")
print(f"Response: {response.content.decode()}")

print("\n✓ HTTP endpoint tests completed!")
