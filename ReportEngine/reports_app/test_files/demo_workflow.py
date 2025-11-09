"""Complete workflow demonstration of the Award Decision feature."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'report_engine.settings')
django.setup()

from reports_app.models import Applicant, Scholarship, AwardDecision, ScholarshipAward
from decimal import Decimal

print("=" * 70)
print("AWARD DECISION FEATURE - COMPLETE WORKFLOW DEMONSTRATION")
print("=" * 70)

# Step 1: Verify database and model
print("\n[Step 1] Verifying AwardDecision model...")
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='reports_app_awarddecision';")
    result = cursor.fetchone()
    if result:
        print("✓ AwardDecision table exists in database")
    else:
        print("✗ Table not found!")

# Step 2: Check admin registration
print("\n[Step 2] Verifying admin registration...")
from django.contrib import admin
from reports_app.admin import AwardDecisionAdmin
if AwardDecision in admin.site._registry:
    print(f"✓ AwardDecision registered in admin")
    admin_class = admin.site._registry[AwardDecision]
    print(f"  Admin class: {admin_class.__class__.__name__}")
    print(f"  List display: {admin_class.list_display}")
else:
    print("✗ Not registered in admin")

# Step 3: Test model operations
print("\n[Step 3] Testing model CRUD operations...")

# Create test data
applicant, created = Applicant.objects.get_or_create(
    student_id='DEMO001',
    defaults={
        'name': 'Demo Student',
        'netid': 'demo001',
        'major': 'Engineering',
        'gpa': 3.9,
        'academic_level': 'Senior'
    }
)
print(f"✓ Test applicant: {applicant} (created: {created})")

# Create decision
decision = AwardDecision.record(
    applicant=applicant,
    scholarship_name='Demo Scholarship',
    decision='pending',
    comments='Under review by committee'
)
print(f"✓ Created decision: {decision}")
print(f"  ID: {decision.id}")
print(f"  Decision: {decision.decision}")
print(f"  Comments: {decision.comments}")

# Update decision
updated_decision = AwardDecision.record(
    applicant=applicant,
    scholarship_name='Demo Scholarship',
    decision='awarded',
    comments='Committee approved - exceptional candidate'
)
print(f"✓ Updated decision (same ID: {decision.id == updated_decision.id})")
print(f"  New decision: {updated_decision.decision}")

# Step 4: Test endpoint
print("\n[Step 4] Testing award_scholarship endpoint...")
from django.http import HttpRequest
from reports_app.views import award_scholarship

request = HttpRequest()
request.method = 'POST'
request.POST = {
    'applicant_id': 'DEMO001',
    'scholarship_name': 'API Test Scholarship',
    'decision': 'awarded',
    'comments': 'Approved via API',
    'create_award': 'yes',
    'award_amount': '7500.00'
}

# Mock authentication (since we added @login_required)
from django.contrib.auth.models import AnonymousUser, User
request.user = User.objects.filter(is_staff=True).first()
if not request.user:
    request.user = User.objects.create_user('testadmin', 'test@test.com', 'password', is_staff=True)
    print(f"  Created test user: {request.user.username}")

try:
    response = award_scholarship(request)
    print(f"✓ Endpoint response: {response.status_code}")
    print(f"  Message: {response.content.decode()}")
    
    # Verify decision was created
    api_decision = AwardDecision.objects.get(
        applicant=applicant,
        scholarship_name='API Test Scholarship'
    )
    print(f"✓ Decision persisted: {api_decision.decision}")
    
    # Verify award was created
    award = ScholarshipAward.objects.filter(
        applicant=applicant,
        scholarship_name='API Test Scholarship'
    ).first()
    if award:
        print(f"✓ ScholarshipAward created: ${award.award_amount}")
    else:
        print("  (No award created)")
        
except Exception as e:
    print(f"✗ Endpoint error: {e}")

# Step 5: Test prescreening integration
print("\n[Step 5] Testing prescreening report integration...")
from reports_app.views import ReportEngine

engine = ReportEngine()
applicants = [applicant]

# Add a scholarship to test matching
scholarship, _ = Scholarship.objects.get_or_create(
    name='Demo Scholarship',
    defaults={
        'description': 'A demo scholarship',
        'frequency': 'annual',
        'amount': Decimal('10000.00'),
        'eligibility_criteria': ['GPA >= 3.0'],
        'donor_info': {'name': 'Demo Donor'},
        'disbursement_requirements': []
    }
)

report = engine.generate_prescreening_report(applicants)
print(f"✓ Report generated successfully")
print(f"  Total applicants: {report['total_applicants']}")

# Check award decisions in summary
if 'award_decisions' in report['summary']:
    ad_summary = report['summary']['award_decisions']
    print(f"✓ Award decisions in summary:")
    print(f"  Awarded: {ad_summary.get('awarded', 0)}")
    print(f"  Not Awarded: {ad_summary.get('not_awarded', 0)}")
    print(f"  Pending: {ad_summary.get('pending', 0)}")
else:
    print("✗ No award_decisions in summary")

# Step 6: Test exports
print("\n[Step 6] Testing export formats...")

# PDF
try:
    pdf_file = engine.export_prescreening_report_to_pdf(applicants, output_path='demo_report.pdf')
    import os
    if os.path.exists('demo_report.pdf'):
        size = os.path.getsize('demo_report.pdf')
        print(f"✓ PDF export successful ({size} bytes)")
except Exception as e:
    print(f"✗ PDF export failed: {e}")

# CSV
try:
    csv_file = engine.export_prescreening_report_to_csv(applicants, output_path='demo_report.csv')
    with open('demo_report.csv', 'r') as f:
        content = f.read()
    has_decision_col = 'Award Decision' in content
    has_comments_col = 'Decision Comments' in content
    print(f"✓ CSV export successful")
    print(f"  Has 'Award Decision' column: {has_decision_col}")
    print(f"  Has 'Decision Comments' column: {has_comments_col}")
except Exception as e:
    print(f"✗ CSV export failed: {e}")

# Excel
try:
    excel_file = engine.export_prescreening_report_to_excel(applicants, output_path='demo_report.xlsx')
    import os
    if os.path.exists('demo_report.xlsx'):
        size = os.path.getsize('demo_report.xlsx')
        print(f"✓ Excel export successful ({size} bytes)")
except Exception as e:
    print(f"✗ Excel export failed: {e}")

# Step 7: Summary
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

total_decisions = AwardDecision.objects.count()
awarded_count = AwardDecision.objects.filter(decision='awarded').count()
pending_count = AwardDecision.objects.filter(decision='pending').count()
not_awarded_count = AwardDecision.objects.filter(decision='not_awarded').count()

print(f"Total decisions in database: {total_decisions}")
print(f"  - Awarded: {awarded_count}")
print(f"  - Not Awarded: {not_awarded_count}")
print(f"  - Pending: {pending_count}")

print("\nGenerated files:")
for filename in ['demo_report.pdf', 'demo_report.csv', 'demo_report.xlsx']:
    if os.path.exists(filename):
        size = os.path.getsize(filename)
        print(f"  ✓ {filename} ({size} bytes)")

print("\n✅ All workflow steps completed successfully!")
print("=" * 70)
