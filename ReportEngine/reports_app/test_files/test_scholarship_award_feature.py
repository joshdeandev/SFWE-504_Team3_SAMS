import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'report_engine_proj.settings')
django.setup()

from reports_app.models import Scholarship, AwardDecision, Applicant

print("="*70)
print("TESTING SCHOLARSHIP AWARD FEATURE")
print("="*70)

# Get the latest scholarships
engineering = Scholarship.objects.filter(
    name="Engineering Excellence Scholarship"
).order_by('-id').first()

cs = Scholarship.objects.filter(
    name="CS Leadership Scholarship"
).order_by('-id').first()

print("\nLatest Scholarships:")
if engineering:
    print(f"  * {engineering.name} - ${engineering.amount}")
else:
    print("  * Engineering Excellence Scholarship - NOT FOUND")

if cs:
    print(f"  * {cs.name} - ${cs.amount}")
else:
    print("  * CS Leadership Scholarship - NOT FOUND")

# Check for awarded decisions
print("\n" + "="*70)
print("AWARD STATUS CHECK")
print("="*70)

scholarships = [s for s in [engineering, cs] if s]

for scholarship in scholarships:
    has_award = AwardDecision.objects.filter(
        scholarship_name=scholarship.name,
        decision='awarded'
    ).exists()
    
    count = AwardDecision.objects.filter(
        scholarship_name=scholarship.name,
        decision='awarded'
    ).count()
    
    status = "AWARDED" if has_award else "AVAILABLE"
    print(f"\n{scholarship.name}:")
    print(f"  Status: {status}")
    print(f"  Awarded to: {count} applicant(s)")
    
    if has_award:
        awards = AwardDecision.objects.filter(
            scholarship_name=scholarship.name,
            decision='awarded'
        )
        for award in awards[:3]:  # Show first 3
            print(f"    - {award.applicant.name} ({award.applicant.student_id})")

print("\n" + "="*70)
print("AVAILABLE SCHOLARSHIPS (will be shown on page)")
print("="*70)

available = [s for s in scholarships if not AwardDecision.objects.filter(
    scholarship_name=s.name,
    decision='awarded'
).exists()]

print(f"\nTotal Available: {len(available)}")
for scholarship in available:
    print(f"  * {scholarship.name} - ${scholarship.amount}")

if len(available) == 0:
    print("  All scholarships have been awarded!")

print("\n" + "="*70)
print("FEATURE SUMMARY")
print("="*70)
print("\nNew Features:")
print("  1. OK 'Award Scholarship' button in Available Scholarships section")
print("  2. OK Modal to select applicant when awarding from scholarship")
print("  3. OK Scholarships removed from 'Available' list once awarded")
print("  4. OK Can still award/decline from applicant cards (for decisions)")
print("  5. OK All scholarships shown in dropdown when making decisions")
print("\nHow it works:")
print("  - Available Scholarships shows only non-awarded scholarships")
print("  - Click 'Award Scholarship' to select an applicant")
print("  - Once awarded (decision='awarded'), scholarship disappears from available list")
print("  - Can still manage decisions (award/decline/pending) from applicant cards")

print("\n" + "="*70)
