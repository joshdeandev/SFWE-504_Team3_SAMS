# Quick Start Guide: Financial Aid Integration

## Prerequisites
- Django Report Engine installed
- Python 3.8+
- Access to financial aid system API (Banner, Workday, etc.)

## Step 1: Install Requirements
```bash
pip install -r requirements.txt
```

## Step 2: Run Database Migrations
```bash
cd ReportEngine
python manage.py makemigrations
python manage.py migrate
```

This creates the new tables:
- `DisbursementTransaction`
- `FinancialAidSystemLog`  
- `PaymentSchedule`

## Step 3: Configure Financial Aid System

### Option A: Using Environment Variables (Recommended for Production)
```powershell
# Windows PowerShell
$env:BANNER_API_KEY = "your-api-key-here"
$env:BANNER_BASE_URL = "https://banner.university.edu"
```

### Option B: Update settings.py Directly (Development Only)
Edit `report_engine/settings.py`:
```python
FINANCIAL_AID_SYSTEMS = {
    'banner': {
        'type': 'banner',
        'enabled': True,  # Enable integration
        'base_url': 'https://banner.university.edu',
        'api_key': 'your-api-key',
        'timeout': 30,
    },
}

FINANCIAL_AID_INTEGRATION = {
    'default_system': 'banner',
    'auto_submit_enabled': False,  # Start with manual mode
    'require_manual_approval': True,
}
```

## Step 4: Test Configuration
```bash
# Test dry run
python manage.py process_disbursements --dry-run
```

## Step 5: Create Payment Schedules

### Via Django Shell
```bash
python manage.py shell
```

```python
from reports_app.models import ScholarshipAward, PaymentSchedule
from datetime import date, timedelta

# Get a scholarship award
award = ScholarshipAward.objects.first()

# Create two payment schedules
for i in range(2):
    PaymentSchedule.objects.create(
        scholarship_award=award,
        payment_number=i + 1,
        scheduled_amount=award.award_amount / 2,
        scheduled_date=date.today() + timedelta(days=90 * i),
        required_conditions=['enrollment_verified'],
        status='pending'
    )
```

## Step 6: Process Disbursements

### Manual Export (Safest for First Time)
```python
from reports_app.models import ScholarshipAward
from reports_app.views import ReportEngine

engine = ReportEngine()
awards = ScholarshipAward.objects.filter(status='active')

# Export to CSV for Banner
csv_file = engine.export_financial_aid_data(
    scholarship_awards=awards,
    format='csv',
    system_type='banner'
)

print(f"Export file: {csv_file}")
# Now manually import this file into your financial aid system
```

### API Submission (After Testing)
```bash
# Enable in settings.py first:
# FINANCIAL_AID_INTEGRATION['auto_submit_enabled'] = True

python manage.py process_disbursements --days-ahead 30
```

## Step 7: Monitor in Django Admin

1. Start Django server:
```bash
python manage.py runserver
```

2. Visit: http://localhost:8000/admin/

3. Navigate to:
   - **Disbursement Transactions** - View transaction status
   - **Financial Aid System Logs** - Monitor API calls
   - **Payment Schedules** - Manage payment timings

## Common Commands

### View Pending Disbursements
```bash
python manage.py process_disbursements --dry-run --status approved
```

### Process Specific System
```bash
python manage.py process_disbursements --system banner
```

### Limit Processing
```bash
python manage.py process_disbursements --limit 5
```

## Verification Checklist

- [ ] Database migrations completed
- [ ] Financial aid system configured in settings
- [ ] API credentials working (test connection)
- [ ] Payment schedules created
- [ ] Dry run successful
- [ ] Export files generated correctly
- [ ] Django admin accessible
- [ ] Logs showing proper activity

## Troubleshooting

### "No financial aid system adapter available"
→ Check `FINANCIAL_AID_SYSTEMS` in settings.py
→ Ensure `'enabled': True`

### Authentication errors
→ Verify API key/credentials
→ Check base_url is correct
→ Ensure API endpoint is accessible

### No disbursements found
→ Check date range with `--days-ahead`
→ Verify status filter (default: 'approved')
→ Ensure PaymentSchedules exist

## Next Steps

1. **Test with sample data** - Use a few test records first
2. **Review logs** - Check FinancialAidSystemLog for any issues
3. **Pilot program** - Start with one scholarship
4. **Schedule automation** - Set up cron job for regular processing
5. **Monitor** - Watch for failed transactions and retry as needed

## Getting Help

- Review `FINANCIAL_AID_INTEGRATION.md` for detailed documentation
- Check `ARCHITECTURE_DIAGRAM.md` for system overview
- View `IMPLEMENTATION_SUMMARY.md` for complete feature list
- Check Django logs for error details

## Security Notes

⚠️ **Never commit API keys to version control**
⚠️ **Use environment variables in production**
⚠️ **Enable HTTPS for all API communications**
⚠️ **Regularly rotate API credentials**
⚠️ **Monitor logs for suspicious activity**
