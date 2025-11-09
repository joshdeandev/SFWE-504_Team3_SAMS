"""Test prescreening report exports with award decisions."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'report_engine.settings')
django.setup()

from reports_app.views import ReportEngine
from reports_app.models import Applicant, Scholarship, AwardDecision
from decimal import Decimal
from datetime import datetime

# Ensure we have test data
test_applicant, _ = Applicant.objects.get_or_create(
    student_id='TEST001',
    defaults={
        'name': 'Test Student',
        'netid': 'test001',
        'major': 'Computer Science',
        'gpa': 3.8,
        'academic_level': 'Junior',
        'financial_info': {'efc': 5000, 'unmet_need': 15000}
    }
)

test_scholarship, _ = Scholarship.objects.get_or_create(
    name='Test Scholarship',
    defaults={
        'description': 'A test scholarship',
        'frequency': 'annual',
        'amount': Decimal('5000.00'),
        'eligibility_criteria': ['GPA >= 3.0', 'Computer Science major'],
        'donor_info': {'name': 'Test Donor'},
        'disbursement_requirements': ['Maintain GPA']
    }
)

# Create award decision
decision = AwardDecision.record(
    applicant=test_applicant,
    scholarship_name='Test Scholarship',
    decision='awarded',
    comments='Excellent academic record and financial need'
)

print(f"Test applicant: {test_applicant}")
print(f"Test scholarship: {test_scholarship}")
print(f"Award decision: {decision.decision} - {decision.comments[:50]}...")

# Generate prescreening report
print("\n--- Generating prescreening report ---")
engine = ReportEngine()
applicants = list(Applicant.objects.all())
report = engine.generate_prescreening_report(applicants)

print(f"Report keys: {list(report.keys())}")
print(f"Summary keys: {list(report.get('summary', {}).keys())}")

if 'total_applicants' in report['summary']:
    print(f"Total applicants: {report['summary']['total_applicants']}")
if 'scholarships_reviewed' in report['summary']:
    print(f"Scholarships reviewed: {report['summary']['scholarships_reviewed']}")
if 'total_matches' in report['summary']:
    print(f"Total matches: {report['summary']['total_matches']}")

# Check if award decisions are included in summary
if 'award_decisions' in report['summary']:
    print("\n--- Award Decisions Summary ---")
    ad_summary = report['summary']['award_decisions']
    print(f"  Awarded: {ad_summary.get('awarded', 0)}")
    print(f"  Not Awarded: {ad_summary.get('not_awarded', 0)}")
    print(f"  Pending: {ad_summary.get('pending', 0)}")
else:
    print("\n⚠ Warning: No award_decisions in summary")

# Check if decisions appear in applicant data
print("\n--- Checking applicant award decisions ---")
if 'qualified_applicants' in report:
    for applicant_data in report['qualified_applicants']:
        if applicant_data.get('student_id') == 'TEST001':
            print(f"Found test applicant: {applicant_data.get('name', 'Unknown')}")
            if 'scholarship_matches' in applicant_data:
                for match in applicant_data['scholarship_matches']:
                    if 'award_decision' in match:
                        ad = match['award_decision']
                        print(f"  Scholarship: {match.get('scholarship_name', 'Unknown')}")
                        print(f"  Decision: {ad.get('decision', 'N/A')}")
                        print(f"  Comments: {ad.get('comments', 'N/A')[:50]}...")
                        print(f"  Decided at: {ad.get('decided_at', 'N/A')}")
                    else:
                        print(f"  ⚠ No award_decision in match for {match.get('scholarship_name', 'Unknown')}")
            break
else:
    print("⚠ No qualified_applicants in report")
    if 'matches' in report:
        print(f"Found {len(report['matches'])} matches in report")
        for match in report['matches'][:3]:  # Show first 3
            print(f"  Match keys: {list(match.keys())}")

# Test PDF export
print("\n--- Testing PDF export ---")
try:
    pdf_path = 'test_prescreening_report.pdf'
    pdf_file = engine.export_prescreening_report_to_pdf(applicants, output_path=pdf_path)
    print(f"✓ PDF saved as {pdf_file}")
    
    # Check file size
    import os
    if os.path.exists(pdf_path):
        size = os.path.getsize(pdf_path)
        print(f"  PDF size: {size} bytes")
except Exception as e:
    print(f"✗ PDF export error: {e}")
    import traceback
    traceback.print_exc()

# Test CSV export
print("\n--- Testing CSV export ---")
try:
    csv_path = 'test_prescreening_report.csv'
    csv_file = engine.export_prescreening_report_to_csv(applicants, output_path=csv_path)
    print(f"✓ CSV saved as {csv_file}")
    
    # Check if CSV contains decision data
    with open(csv_path, 'r', encoding='utf-8') as f:
        csv_content = f.read()
    
    if 'Award Decision' in csv_content:
        print("  ✓ CSV contains 'Award Decision' column")
    if 'Decision Comments' in csv_content:
        print("  ✓ CSV contains 'Decision Comments' column")
    if decision.comments and decision.comments in csv_content:
        print("  ✓ CSV contains actual decision comments")
except Exception as e:
    print(f"✗ CSV export error: {e}")
    import traceback
    traceback.print_exc()

# Test Excel export
print("\n--- Testing Excel export ---")
try:
    excel_path = 'test_prescreening_report.xlsx'
    excel_file = engine.export_prescreening_report_to_excel(applicants, output_path=excel_path)
    print(f"✓ Excel saved as {excel_file}")
    
    # Check file size
    import os
    if os.path.exists(excel_path):
        size = os.path.getsize(excel_path)
        print(f"  Excel size: {size} bytes")
except Exception as e:
    print(f"✗ Excel export error: {e}")
    import traceback
    traceback.print_exc()

print("\n✓ Prescreening export tests completed!")
print("\nGenerated files:")
print("  - test_prescreening_report.pdf")
print("  - test_prescreening_report.csv")
print("  - test_prescreening_report.xlsx")
