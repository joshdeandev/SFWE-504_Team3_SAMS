"""Direct test of award_scholarship view function."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'report_engine.settings')
django.setup()

from django.http import HttpRequest
from reports_app.views import award_scholarship
from reports_app.models import Applicant, AwardDecision, ScholarshipAward

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

print("--- Test 1: Record pending decision ---")
# Create a mock POST request
request = HttpRequest()
request.method = 'POST'
request.POST = {
    'applicant_id': 'TEST001',
    'scholarship_name': 'Direct Test Scholarship',
    'decision': 'pending',
    'comments': 'Testing direct view invocation'
}

response = award_scholarship(request)
print(f"Response status: {response.status_code}")
print(f"Response content: {response.content.decode()}")

# Verify decision was created
decision = AwardDecision.objects.filter(
    applicant__student_id='TEST001',
    scholarship_name='Direct Test Scholarship'
).first()
print(f"Decision created: {decision is not None}")
if decision:
    print(f"  Decision: {decision.decision}")
    print(f"  Comments: {decision.comments}")

print("\n--- Test 2: Update to awarded with ScholarshipAward ---")
# Clear existing awards
ScholarshipAward.objects.filter(
    applicant=test_applicant,
    scholarship_name='Direct Test Scholarship'
).delete()

request2 = HttpRequest()
request2.method = 'POST'
request2.POST = {
    'applicant_id': 'TEST001',
    'scholarship_name': 'Direct Test Scholarship',
    'decision': 'awarded',
    'comments': 'Approved with honors',
    'create_award': 'yes',
    'award_amount': '3500.00'
}

response2 = award_scholarship(request2)
print(f"Response status: {response2.status_code}")
print(f"Response content: {response2.content.decode()}")

# Verify decision was updated
decision = AwardDecision.objects.get(
    applicant__student_id='TEST001',
    scholarship_name='Direct Test Scholarship'
)
print(f"Decision updated: {decision.decision}")

# Verify award was created
award = ScholarshipAward.objects.filter(
    applicant=test_applicant,
    scholarship_name='Direct Test Scholarship'
).first()
print(f"ScholarshipAward created: {award is not None}")
if award:
    print(f"  Amount: ${award.award_amount}")
    print(f"  Status: {award.status}")
    print(f"  Notes: {award.notes}")

print("\n--- Test 3: Error handling - missing fields ---")
request3 = HttpRequest()
request3.method = 'POST'
request3.POST = {'scholarship_name': 'Missing Applicant'}

response3 = award_scholarship(request3)
print(f"Response status: {response3.status_code} (expected 400)")
print(f"Response content: {response3.content.decode()}")

print("\n--- Test 4: Error handling - non-existent applicant ---")
request4 = HttpRequest()
request4.method = 'POST'
request4.POST = {
    'applicant_id': 'NONEXISTENT999',
    'scholarship_name': 'Test',
    'decision': 'pending'
}

response4 = award_scholarship(request4)
print(f"Response status: {response4.status_code} (expected 404)")
print(f"Response content: {response4.content.decode()}")

print("\n--- Test 5: GET request (should fail) ---")
request5 = HttpRequest()
request5.method = 'GET'

response5 = award_scholarship(request5)
print(f"Response status: {response5.status_code} (expected 405)")
print(f"Response content: {response5.content.decode()}")

print("\n✓ All direct view tests completed successfully!")
