# Financial Aid System Integration Guide

## Overview

The Report Engine now supports integration with external financial aid systems to automate or assist in payment processing. This feature meets the requirement:

> **The report engine shall support future integration with financial aid systems to automate or assist in payment processing.**

## Architecture

The integration system consists of the following components:

### 1. **Database Models** (models.py)

- **`DisbursementTransaction`**: Tracks individual disbursement transactions with external system integration details
- **`FinancialAidSystemLog`**: Audit log of all interactions with external systems
- **`PaymentSchedule`**: Manages payment schedules and conditions for awards

### 2. **Integration Adapters** (financial_integration.py)

- **`FinancialAidSystemAdapter`**: Abstract base class defining the integration interface
- **`BannerSystemAdapter`**: Implementation for Ellucian Banner system
- **`WorkdaySystemAdapter`**: Implementation for Workday Student (template/placeholder)
- **`FinancialAidIntegrationManager`**: Manager for handling multiple system integrations

### 3. **Management Commands**

- **`process_disbursements`**: Django management command to process scheduled disbursements

## Configuration

### Settings Configuration

Add the following to your Django settings (`settings.py`):

```python
# Financial Aid System Integration Configuration
FINANCIAL_AID_SYSTEMS = {
    'banner': {
        'type': 'banner',
        'enabled': True,  # Set to True when ready
        'base_url': 'https://banner.university.edu',
        'api_key': os.environ.get('BANNER_API_KEY', ''),  # Use environment variable
        'timeout': 30,
        'retry_attempts': 3,
        'retry_delay_seconds': 5,
    },
    'workday': {
        'type': 'workday',
        'enabled': False,
        'base_url': 'https://workday.university.edu',
        'username': os.environ.get('WORKDAY_USERNAME', ''),
        'password': os.environ.get('WORKDAY_PASSWORD', ''),
        'tenant': os.environ.get('WORKDAY_TENANT', ''),
        'timeout': 30,
    },
}

FINANCIAL_AID_INTEGRATION = {
    'default_system': 'banner',
    'auto_submit_enabled': False,  # Set to True for automatic processing
    'require_manual_approval': True,
    'batch_processing_enabled': True,
    'batch_size': 50,
    'export_directory': BASE_DIR / 'financial_aid_exports',
    'archive_exports': True,
    'notification_emails': ['finaid@university.edu'],
}
```

### Environment Variables (Production)

**Never store credentials in settings.py!** Use environment variables:

```bash
# Windows PowerShell
$env:BANNER_API_KEY = "your-api-key-here"
$env:WORKDAY_USERNAME = "your-username"
$env:WORKDAY_PASSWORD = "your-password"

# Linux/Mac
export BANNER_API_KEY="your-api-key-here"
export WORKDAY_USERNAME="your-username"
export WORKDAY_PASSWORD="your-password"
```

## Database Migration

After adding the new models, run migrations:

```bash
python manage.py makemigrations
python manage.py migrate
```

## Usage Examples

### 1. **Create Payment Schedules**

```python
from reports_app.models import ScholarshipAward, PaymentSchedule
from datetime import date, timedelta

# Get a scholarship award
award = ScholarshipAward.objects.get(id=1)

# Create payment schedules
total_payments = 2  # Two semester payments
amount_per_payment = award.award_amount / total_payments

for i in range(total_payments):
    schedule = PaymentSchedule.objects.create(
        scholarship_award=award,
        payment_number=i + 1,
        scheduled_amount=amount_per_payment,
        scheduled_date=date.today() + timedelta(days=90 * i),
        required_conditions=['enrollment_verified', 'gpa_check'],
        status='pending'
    )
```

### 2. **Verify Conditions and Create Disbursement**

```python
# Verify conditions for a payment
schedule = PaymentSchedule.objects.get(id=1)
schedule.verify_conditions(verified_by='Financial Aid Officer')

# Create disbursement transaction
transaction = schedule.create_disbursement_transaction()
```

### 3. **Submit Disbursement to Financial Aid System**

```python
from reports_app.financial_integration import FinancialAidIntegrationManager

# Initialize manager
manager = FinancialAidIntegrationManager()
adapter = manager.get_adapter('banner')

# Prepare disbursement data
disbursement_data = {
    'student_id': '12345678',
    'amount': 2500.00,
    'scholarship_name': 'Academic Excellence Scholarship',
    'disbursement_date': date.today(),
    'reference_number': 'DISB-001',
    'account_code': 'SCHLRSHP',
}

# Submit
result = adapter.submit_disbursement(disbursement_data)

if result['success']:
    print(f"Submitted successfully: {result['transaction_id']}")
else:
    print(f"Failed: {result['message']}")
```

### 4. **Batch Processing**

```python
# Submit multiple disbursements
disbursements = [
    {
        'student_id': '12345678',
        'amount': 2500.00,
        'scholarship_name': 'Scholarship A',
        'disbursement_date': date.today(),
        'reference_number': 'DISB-001',
    },
    {
        'student_id': '87654321',
        'amount': 3000.00,
        'scholarship_name': 'Scholarship B',
        'disbursement_date': date.today(),
        'reference_number': 'DISB-002',
    },
]

results = manager.submit_batch_disbursements(disbursements, system_name='banner')
```

### 5. **Export Data for Manual Import**

```python
from reports_app.financial_integration import generate_financial_aid_export
from reports_app.models import ScholarshipAward

# Get awards to export
awards = ScholarshipAward.objects.filter(status='active')

# Generate CSV export for Banner
csv_file = generate_financial_aid_export(
    scholarship_awards=awards,
    format='csv',
    system_type='banner'
)

print(f"Export file created: {csv_file}")

# Also supports 'json' and 'xml' formats
json_file = generate_financial_aid_export(awards, format='json')
xml_file = generate_financial_aid_export(awards, format='xml')
```

### 6. **Management Command**

Process disbursements via command line:

```bash
# Dry run to see what would be processed
python manage.py process_disbursements --dry-run

# Process disbursements scheduled in next 7 days
python manage.py process_disbursements

# Process specific timeframe
python manage.py process_disbursements --days-ahead 14

# Use specific system
python manage.py process_disbursements --system banner

# Limit number of transactions
python manage.py process_disbursements --limit 10
```

### 7. **Check Transaction Status**

```python
# Check status of a submitted disbursement
adapter = manager.get_adapter('banner')
status = adapter.check_disbursement_status('EXT-TRANS-12345')

print(f"Status: {status['status']}")
if status.get('processed_date'):
    print(f"Processed: {status['processed_date']}")
```

## Adding New Financial Aid Systems

To add support for a new financial aid system:

1. **Create a new adapter class** in `financial_integration.py`:

```python
class MySystemAdapter(FinancialAidSystemAdapter):
    def _setup_authentication(self):
        # Configure authentication
        pass
    
    def submit_disbursement(self, disbursement_data):
        # Implement submission logic
        pass
    
    def check_disbursement_status(self, transaction_id):
        # Implement status checking
        pass
    
    def get_student_account_info(self, student_id):
        # Implement account info retrieval
        pass
    
    def validate_student_eligibility(self, student_id):
        # Implement eligibility validation
        pass
```

2. **Register the adapter** in `FinancialAidIntegrationManager._get_adapter_class()`:

```python
adapter_map = {
    'banner': BannerSystemAdapter,
    'workday': WorkdaySystemAdapter,
    'mysystem': MySystemAdapter,  # Add your adapter
}
```

3. **Add configuration** to settings:

```python
FINANCIAL_AID_SYSTEMS = {
    'mysystem': {
        'type': 'mysystem',
        'enabled': True,
        'base_url': 'https://api.mysystem.edu',
        'api_key': os.environ.get('MYSYSTEM_API_KEY'),
        # Add system-specific settings
    },
}
```

## Monitoring and Auditing

All integration activities are logged in the `FinancialAidSystemLog` model:

```python
from reports_app.models import FinancialAidSystemLog

# View recent logs
recent_logs = FinancialAidSystemLog.objects.filter(
    system_name='banner'
).order_by('-request_timestamp')[:10]

for log in recent_logs:
    print(f"{log.operation}: {log.status} ({log.response_time_ms}ms)")
```

View logs in Django Admin at `/admin/reports_app/financialaidsystemlog/`

## Security Best Practices

1. **Never hardcode credentials** - Use environment variables
2. **Use HTTPS** - Ensure all API endpoints use secure connections
3. **Implement rate limiting** - Prevent overwhelming external systems
4. **Validate inputs** - Sanitize all data before sending to external systems
5. **Encrypt sensitive data** - Use Django's encryption for stored credentials
6. **Audit all actions** - All transactions are logged automatically
7. **Use separate credentials** per environment (dev, staging, production)

## Troubleshooting

### Issue: "No financial aid system adapter available"
**Solution**: Check that a system is configured and enabled in `FINANCIAL_AID_SYSTEMS`

### Issue: Authentication failures
**Solution**: Verify API keys/credentials are correct and not expired

### Issue: Transaction stuck in "submitted" status
**Solution**: Use `check_disbursement_status()` to query the external system

### Issue: Export files not generating
**Solution**: Ensure `export_directory` exists and is writable

## Future Enhancements

The integration framework is designed to be extensible. Consider these enhancements:

- **Webhook receivers** for status updates from external systems
- **Scheduled background jobs** using Celery for async processing
- **Email notifications** for transaction status changes
- **Dashboard** for monitoring integration health
- **Retry mechanisms** with exponential backoff
- **Data synchronization** between systems

## Support

For questions or issues with the financial aid integration:
- Review the logs in Django Admin
- Check `FinancialAidSystemLog` for API interaction details
- Enable DEBUG logging for detailed information
- Contact your financial aid system administrator for API documentation
