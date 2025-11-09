# Financial Aid Integration Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          REPORT ENGINE                                       │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                    ReportEngine Class (views.py)                        │ │
│  │                                                                          │ │
│  │  • generate_disbursement_report()                                       │ │
│  │  • export_financial_aid_data()  ←─ Convenience Methods                 │ │
│  │  • submit_disbursements_to_financial_aid_system()                       │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                    │                                         │
│                                    ↓                                         │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │              Database Models (models.py)                                │ │
│  │                                                                          │ │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────────┐   │ │
│  │  │ Disbursement     │  │ Payment          │  │ FinancialAid      │   │ │
│  │  │ Transaction      │  │ Schedule         │  │ SystemLog         │   │ │
│  │  │                  │  │                  │  │                   │   │ │
│  │  │ • transaction_id │  │ • payment_number │  │ • system_name     │   │ │
│  │  │ • external_id    │  │ • scheduled_amt  │  │ • operation       │   │ │
│  │  │ • amount         │  │ • conditions     │  │ • request/response│   │ │
│  │  │ • status         │  │ • status         │  │ • status          │   │ │
│  │  │ • system_name    │  │                  │  │ • timestamps      │   │ │
│  │  └──────────────────┘  └──────────────────┘  └───────────────────┘   │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│              Financial Integration Layer (financial_integration.py)          │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │           FinancialAidIntegrationManager                                │ │
│  │                                                                          │ │
│  │  • get_adapter(system_name)                                             │ │
│  │  • submit_batch_disbursements()                                         │ │
│  │  • validate_batch_eligibility()                                         │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                    │                                         │
│                    ┌───────────────┴───────────────┐                        │
│                    ↓                               ↓                        │
│  ┌──────────────────────────────┐   ┌──────────────────────────────┐      │
│  │  FinancialAidSystemAdapter   │   │  FinancialAidSystemAdapter   │      │
│  │  (Abstract Base Class)       │   │  (Abstract Base Class)       │      │
│  │                              │   │                              │      │
│  │  • submit_disbursement()     │   │  • submit_disbursement()     │      │
│  │  • check_status()            │   │  • check_status()            │      │
│  │  • get_account_info()        │   │  • get_account_info()        │      │
│  │  • validate_eligibility()    │   │  • validate_eligibility()    │      │
│  └──────────────────────────────┘   └──────────────────────────────┘      │
│              ▲                                   ▲                          │
│              │                                   │                          │
│  ┌───────────┴────────────┐        ┌───────────┴────────────┐            │
│  │  BannerSystemAdapter   │        │  WorkdaySystemAdapter  │            │
│  │                        │        │                        │            │
│  │  • API Key Auth        │        │  • Basic Auth          │            │
│  │  • Banner-specific     │        │  • Workday-specific    │            │
│  │    endpoints           │        │    endpoints           │            │
│  │  • Full implementation │        │  • Template/Placeholder│            │
│  └────────────────────────┘        └────────────────────────┘            │
└─────────────────────────────────────────────────────────────────────────────┘
                    │                               │
                    ↓                               ↓
┌───────────────────────────────┐   ┌────────────────────────────────────────┐
│   External Financial Systems  │   │      Export File Generators            │
│                               │   │                                        │
│  ┌─────────────────────────┐ │   │  • generate_financial_aid_export()     │
│  │  Ellucian Banner        │ │   │                                        │
│  │  • REST API             │ │   │  ┌──────────┐  ┌──────────┐  ┌──────┐ │
│  │  • /api/disbursements   │ │   │  │   CSV    │  │   JSON   │  │  XML │ │
│  │  • /api/students        │ │   │  │          │  │          │  │      │ │
│  └─────────────────────────┘ │   │  │ Banner   │  │ Generic  │  │ Ent. │ │
│                               │   │  │ Format   │  │ Format   │  │ Sys. │ │
│  ┌─────────────────────────┐ │   │  └──────────┘  └──────────┘  └──────┘ │
│  │  Workday Student        │ │   │                                        │
│  │  • REST/SOAP API        │ │   │  Used for manual import when           │
│  │  • OAuth/Basic Auth     │ │   │  API integration not available         │
│  └─────────────────────────┘ │   └────────────────────────────────────────┘
│                               │
│  ┌─────────────────────────┐ │
│  │  Other Systems          │ │
│  │  • PeopleSoft           │ │
│  │  • Jenzabar             │ │
│  │  • Custom Systems       │ │
│  └─────────────────────────┘ │
└───────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                    Management & Automation                                   │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  Django Management Command: process_disbursements                       │ │
│  │                                                                          │ │
│  │  • Scheduled via cron/task scheduler                                    │ │
│  │  • Queries approved DisbursementTransactions                            │ │
│  │  • Submits to configured financial aid system                           │ │
│  │  • Updates transaction status                                           │ │
│  │  • Logs all activities                                                  │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                    Configuration & Settings                                  │
│                                                                              │
│  settings.py:                                                                │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  FINANCIAL_AID_SYSTEMS = {                                              │ │
│  │      'banner': { 'type': 'banner', 'base_url': '...', 'api_key': ... } │ │
│  │      'workday': { 'type': 'workday', 'base_url': '...', ...  }         │ │
│  │  }                                                                       │ │
│  │                                                                          │ │
│  │  FINANCIAL_AID_INTEGRATION = {                                          │ │
│  │      'default_system': 'banner',                                        │ │
│  │      'auto_submit_enabled': False,                                      │ │
│  │      'batch_processing_enabled': True,                                  │ │
│  │      ...                                                                 │ │
│  │  }                                                                       │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                    Monitoring & Admin Interface                              │
│                                                                              │
│  Django Admin (/admin/):                                                     │
│  • DisbursementTransactionAdmin  ─  View/manage all transactions            │
│  • FinancialAidSystemLogAdmin    ─  Monitor API interactions                │
│  • PaymentScheduleAdmin          ─  Manage payment schedules                │
│                                                                              │
│  Features:                                                                   │
│  • Search by student ID, transaction ID, scholarship                         │
│  • Filter by status, system, dates                                           │
│  • View detailed payloads and responses                                      │
│  • Track errors and retries                                                  │
└─────────────────────────────────────────────────────────────────────────────┘


DATA FLOW EXAMPLES:
═══════════════════

1. AUTOMATED API SUBMISSION:
   
   ScholarshipAward → PaymentSchedule → verify_conditions() →
   create_disbursement_transaction() → DisbursementTransaction (approved) →
   process_disbursements command → FinancialAidIntegrationManager →
   BannerSystemAdapter.submit_disbursement() → External API →
   Response → Update DisbursementTransaction (submitted/completed) →
   Create FinancialAidSystemLog

2. MANUAL EXPORT WORKFLOW:
   
   ScholarshipAward → generate_disbursement_report() →
   export_financial_aid_data(format='csv') → CSV File →
   Manual Import to Financial Aid System → 
   Manual status update in Django Admin

3. STATUS CHECKING:
   
   DisbursementTransaction (submitted) → 
   BannerSystemAdapter.check_disbursement_status(external_id) →
   External API → Response → 
   Update DisbursementTransaction.status →
   Create FinancialAidSystemLog


EXTENSIBILITY:
═══════════════

To add a new financial aid system:

1. Create new adapter class inheriting from FinancialAidSystemAdapter
2. Implement required methods (submit, check_status, etc.)
3. Add to adapter_map in FinancialAidIntegrationManager
4. Add configuration to settings.FINANCIAL_AID_SYSTEMS
5. (Optional) Add system-specific export format logic

Example:
  class MySystemAdapter(FinancialAidSystemAdapter):
      def _setup_authentication(self): ...
      def submit_disbursement(self, data): ...
      def check_disbursement_status(self, tx_id): ...
      # etc.
```
