"""
Django management command to process scheduled disbursements.

This command can be run manually or scheduled via cron/task scheduler to automatically
process approved disbursements through the configured financial aid system.

Usage:
    python manage.py process_disbursements [options]

Implements requirement: The report engine shall support future integration with 
financial aid systems to automate or assist in payment processing.
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.utils import timezone
from datetime import date, timedelta
from reports_app.models import DisbursementTransaction, PaymentSchedule
from reports_app.financial_integration import FinancialAidIntegrationManager
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Process scheduled disbursements through the financial aid system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be processed without actually submitting',
        )
        parser.add_argument(
            '--system',
            type=str,
            help='Specific financial aid system to use (default: configured default)',
        )
        parser.add_argument(
            '--days-ahead',
            type=int,
            default=7,
            help='Process disbursements scheduled within this many days (default: 7)',
        )
        parser.add_argument(
            '--status',
            type=str,
            default='approved',
            help='Status of transactions to process (default: approved)',
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Maximum number of disbursements to process',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        system_name = options['system']
        days_ahead = options['days_ahead']
        status_filter = options['status']
        limit = options['limit']

        # Calculate date range
        today = date.today()
        future_date = today + timedelta(days=days_ahead)

        self.stdout.write(self.style.SUCCESS(
            f'Processing disbursements scheduled between {today} and {future_date}'
        ))

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No actual submissions will be made'))

        # Query disbursements to process
        transactions = DisbursementTransaction.objects.filter(
            status=status_filter,
            scheduled_date__gte=today,
            scheduled_date__lte=future_date
        ).order_by('scheduled_date')

        if limit:
            transactions = transactions[:limit]

        count = transactions.count()
        
        if count == 0:
            self.stdout.write(self.style.WARNING('No disbursements found to process'))
            return

        self.stdout.write(f'Found {count} disbursement(s) to process')

        if dry_run:
            self._display_dry_run_info(transactions)
            return

        # Initialize integration manager
        integration_manager = FinancialAidIntegrationManager()
        adapter = integration_manager.get_adapter(system_name)

        if not adapter:
            raise CommandError('No financial aid system adapter available. Check FINANCIAL_AID_SYSTEMS settings.')

        # Check if auto-submit is enabled
        auto_submit = getattr(settings, 'FINANCIAL_AID_INTEGRATION', {}).get('auto_submit_enabled', False)
        
        if not auto_submit:
            self.stdout.write(self.style.WARNING(
                'Auto-submit is disabled in settings. Enable FINANCIAL_AID_INTEGRATION[auto_submit_enabled] to process.'
            ))
            return

        # Process each transaction
        success_count = 0
        failure_count = 0

        for transaction in transactions:
            try:
                self.stdout.write(f'Processing: {transaction.transaction_id}')
                
                # Prepare disbursement data
                disbursement_data = {
                    'student_id': transaction.scholarship_award.applicant.student_id,
                    'amount': transaction.amount,
                    'scholarship_name': transaction.scholarship_award.scholarship_name,
                    'disbursement_date': transaction.scheduled_date,
                    'reference_number': transaction.transaction_id,
                    'account_code': transaction.account_code or 'SCHLRSHP',
                }

                # Submit to financial aid system
                result = adapter.submit_disbursement(disbursement_data)

                if result['success']:
                    transaction.mark_submitted(
                        external_id=result['transaction_id'],
                        system_name=adapter.config.get('type', 'unknown')
                    )
                    transaction.submission_payload = disbursement_data
                    transaction.response_data = result
                    transaction.save()
                    
                    success_count += 1
                    self.stdout.write(self.style.SUCCESS(
                        f'  ✓ Successfully submitted: {result["transaction_id"]}'
                    ))
                else:
                    transaction.mark_failed(result.get('message', 'Unknown error'))
                    transaction.submission_payload = disbursement_data
                    transaction.response_data = result
                    transaction.save()
                    
                    failure_count += 1
                    self.stdout.write(self.style.ERROR(
                        f'  ✗ Failed: {result.get("message")}'
                    ))

            except Exception as e:
                failure_count += 1
                logger.error(f'Error processing {transaction.transaction_id}: {str(e)}')
                self.stdout.write(self.style.ERROR(f'  ✗ Error: {str(e)}'))
                
                try:
                    transaction.mark_failed(str(e))
                except:
                    pass

        # Summary
        self.stdout.write(self.style.SUCCESS(
            f'\nProcessing complete: {success_count} successful, {failure_count} failed'
        ))

    def _display_dry_run_info(self, transactions):
        """Display information about transactions that would be processed."""
        self.stdout.write('\nTransactions that would be processed:')
        self.stdout.write('-' * 80)
        
        for transaction in transactions:
            self.stdout.write(
                f'ID: {transaction.transaction_id}\n'
                f'  Student: {transaction.scholarship_award.applicant.name} '
                f'({transaction.scholarship_award.applicant.student_id})\n'
                f'  Scholarship: {transaction.scholarship_award.scholarship_name}\n'
                f'  Amount: ${transaction.amount}\n'
                f'  Scheduled: {transaction.scheduled_date}\n'
                f'  Status: {transaction.status}\n'
            )
        
        self.stdout.write('-' * 80)
        self.stdout.write(f'Total: {transactions.count()} transaction(s)')
