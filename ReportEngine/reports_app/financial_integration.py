"""
Financial Aid System Integration Module

This module provides the foundation for integrating with external financial aid systems
to automate or assist in payment processing.

Implements requirement: The report engine shall support future integration with 
financial aid systems to automate or assist in payment processing.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date
from decimal import Decimal
import json
import requests
from abc import ABC, abstractmethod
from django.conf import settings
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class FinancialAidSystemAdapter(ABC):
    """
    Abstract base class for financial aid system integrations.
    
    Each financial aid system (Banner, PeopleSoft, Workday, etc.) should implement
    this interface to provide standardized communication.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the adapter with configuration.
        
        Args:
            config: Dictionary containing API endpoints, credentials, and settings
                   Expected keys: 'base_url', 'api_key', 'timeout', etc.
        """
        self.config = config
        self.base_url = config.get('base_url', '')
        self.api_key = config.get('api_key', '')
        self.timeout = config.get('timeout', 30)
        self.session = requests.Session()
        self._setup_authentication()
    
    @abstractmethod
    def _setup_authentication(self):
        """Configure authentication for API requests."""
        pass
    
    @abstractmethod
    def submit_disbursement(self, disbursement_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submit a disbursement request to the financial aid system.
        
        Args:
            disbursement_data: Dictionary containing:
                - student_id: Student identifier
                - amount: Decimal amount to disburse
                - scholarship_name: Name of scholarship
                - disbursement_date: Date for disbursement
                - account_code: Accounting code for the transaction
                - reference_number: Internal reference number
        
        Returns:
            Dictionary with result:
                - success: bool
                - transaction_id: External system transaction ID
                - status: Current status
                - message: Any messages from the system
        """
        pass
    
    @abstractmethod
    def check_disbursement_status(self, transaction_id: str) -> Dict[str, Any]:
        """
        Check the status of a previously submitted disbursement.
        
        Args:
            transaction_id: The transaction ID from the financial aid system
        
        Returns:
            Dictionary with status information:
                - transaction_id: The transaction ID
                - status: Current status (pending, processed, failed, etc.)
                - processed_date: Date when processed (if applicable)
                - error_message: Any error message (if failed)
        """
        pass
    
    @abstractmethod
    def get_student_account_info(self, student_id: str) -> Dict[str, Any]:
        """
        Retrieve student account information from the financial aid system.
        
        Args:
            student_id: Student identifier
        
        Returns:
            Dictionary with account information:
                - student_id: Student identifier
                - account_balance: Current account balance
                - holds: Any holds on the account
                - eligible_for_disbursement: Boolean indicating eligibility
        """
        pass
    
    @abstractmethod
    def validate_student_eligibility(self, student_id: str) -> Tuple[bool, str]:
        """
        Validate if a student is eligible for disbursement.
        
        Args:
            student_id: Student identifier
        
        Returns:
            Tuple of (eligible: bool, reason: str)
        """
        pass
    
    def get_disbursement_history(self, student_id: str, 
                                 start_date: Optional[date] = None,
                                 end_date: Optional[date] = None) -> List[Dict[str, Any]]:
        """
        Retrieve disbursement history for a student.
        
        Args:
            student_id: Student identifier
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
        
        Returns:
            List of disbursement records
        """
        # Default implementation - override if system provides this
        return []


class BannerSystemAdapter(FinancialAidSystemAdapter):
    """
    Adapter for Ellucian Banner financial aid system integration.
    
    Banner is commonly used in higher education institutions.
    """
    
    def _setup_authentication(self):
        """Configure authentication using API key or OAuth."""
        if self.api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            })
    
    def submit_disbursement(self, disbursement_data: Dict[str, Any]) -> Dict[str, Any]:
        """Submit disbursement to Banner system."""
        try:
            endpoint = f"{self.base_url}/api/financial-aid/disbursements"
            
            payload = {
                'studentId': disbursement_data['student_id'],
                'amount': str(disbursement_data['amount']),
                'fundCode': disbursement_data.get('account_code', ''),
                'aidYear': disbursement_data.get('aid_year', str(datetime.now().year)),
                'disbursementDate': disbursement_data['disbursement_date'].isoformat(),
                'referenceNumber': disbursement_data.get('reference_number', ''),
                'description': disbursement_data.get('scholarship_name', '')
            }
            
            response = self.session.post(endpoint, json=payload, timeout=self.timeout)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Banner disbursement submitted successfully: {result.get('transactionId')}")
            
            return {
                'success': True,
                'transaction_id': result.get('transactionId'),
                'status': result.get('status', 'pending'),
                'message': result.get('message', 'Disbursement submitted successfully')
            }
            
        except requests.RequestException as e:
            logger.error(f"Banner disbursement submission failed: {str(e)}")
            return {
                'success': False,
                'transaction_id': None,
                'status': 'failed',
                'message': f'Error: {str(e)}'
            }
    
    def check_disbursement_status(self, transaction_id: str) -> Dict[str, Any]:
        """Check Banner disbursement status."""
        try:
            endpoint = f"{self.base_url}/api/financial-aid/disbursements/{transaction_id}"
            response = self.session.get(endpoint, timeout=self.timeout)
            response.raise_for_status()
            
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Banner status check failed: {str(e)}")
            return {
                'transaction_id': transaction_id,
                'status': 'unknown',
                'error_message': str(e)
            }
    
    def get_student_account_info(self, student_id: str) -> Dict[str, Any]:
        """Get student account info from Banner."""
        try:
            endpoint = f"{self.base_url}/api/students/{student_id}/account"
            response = self.session.get(endpoint, timeout=self.timeout)
            response.raise_for_status()
            
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Banner account info retrieval failed: {str(e)}")
            return {
                'student_id': student_id,
                'error': str(e)
            }
    
    def validate_student_eligibility(self, student_id: str) -> Tuple[bool, str]:
        """Validate student eligibility in Banner."""
        account_info = self.get_student_account_info(student_id)
        
        if 'error' in account_info:
            return False, f"Unable to retrieve account info: {account_info['error']}"
        
        # Check for holds
        holds = account_info.get('holds', [])
        if holds:
            return False, f"Account has holds: {', '.join(holds)}"
        
        # Check enrollment status
        if not account_info.get('enrolled', False):
            return False, "Student is not currently enrolled"
        
        return True, "Student is eligible for disbursement"


class WorkdaySystemAdapter(FinancialAidSystemAdapter):
    """
    Adapter for Workday Student financial aid system integration.
    """
    
    def _setup_authentication(self):
        """Configure Workday authentication (typically uses basic auth or OAuth)."""
        username = self.config.get('username', '')
        password = self.config.get('password', '')
        if username and password:
            self.session.auth = (username, password)
        self.session.headers.update({'Content-Type': 'application/json'})
    
    def submit_disbursement(self, disbursement_data: Dict[str, Any]) -> Dict[str, Any]:
        """Submit disbursement to Workday."""
        # Placeholder implementation - would need actual Workday API specs
        logger.info("Workday disbursement submission - implementation pending actual API specs")
        return {
            'success': False,
            'transaction_id': None,
            'status': 'not_implemented',
            'message': 'Workday integration requires specific API configuration'
        }
    
    def check_disbursement_status(self, transaction_id: str) -> Dict[str, Any]:
        """Check Workday disbursement status."""
        return {
            'transaction_id': transaction_id,
            'status': 'not_implemented',
            'error_message': 'Workday integration requires specific API configuration'
        }
    
    def get_student_account_info(self, student_id: str) -> Dict[str, Any]:
        """Get student account info from Workday."""
        return {
            'student_id': student_id,
            'error': 'Workday integration requires specific API configuration'
        }
    
    def validate_student_eligibility(self, student_id: str) -> Tuple[bool, str]:
        """Validate student eligibility in Workday."""
        return False, "Workday integration requires specific API configuration"


class FinancialAidIntegrationManager:
    """
    Manager class for handling financial aid system integrations.
    
    Provides a unified interface for working with different financial aid systems
    and manages the integration lifecycle.
    """
    
    def __init__(self):
        """Initialize the integration manager with configured adapters."""
        self.adapters: Dict[str, FinancialAidSystemAdapter] = {}
        self._load_configurations()
    
    def _load_configurations(self):
        """Load adapter configurations from Django settings."""
        configs = getattr(settings, 'FINANCIAL_AID_SYSTEMS', {})
        
        for system_name, config in configs.items():
            adapter_class = self._get_adapter_class(config.get('type', ''))
            if adapter_class:
                self.adapters[system_name] = adapter_class(config)
                logger.info(f"Loaded financial aid adapter: {system_name}")
    
    def _get_adapter_class(self, system_type: str):
        """Get the appropriate adapter class for the system type."""
        adapter_map = {
            'banner': BannerSystemAdapter,
            'workday': WorkdaySystemAdapter,
            # Add more system types as needed
        }
        return adapter_map.get(system_type.lower())
    
    def get_adapter(self, system_name: str = None) -> Optional[FinancialAidSystemAdapter]:
        """
        Get an adapter instance by system name.
        
        Args:
            system_name: Name of the system (if None, returns default/first adapter)
        
        Returns:
            Adapter instance or None if not found
        """
        if system_name:
            return self.adapters.get(system_name)
        
        # Return first available adapter as default
        if self.adapters:
            return next(iter(self.adapters.values()))
        
        return None
    
    def submit_batch_disbursements(self, disbursements: List[Dict[str, Any]], 
                                  system_name: str = None) -> List[Dict[str, Any]]:
        """
        Submit multiple disbursements in batch.
        
        Args:
            disbursements: List of disbursement data dictionaries
            system_name: Name of the financial aid system to use
        
        Returns:
            List of results for each disbursement
        """
        adapter = self.get_adapter(system_name)
        if not adapter:
            logger.error("No financial aid system adapter available")
            return [{
                'success': False,
                'error': 'No financial aid system configured'
            } for _ in disbursements]
        
        results = []
        for disbursement in disbursements:
            result = adapter.submit_disbursement(disbursement)
            results.append(result)
        
        return results
    
    def validate_batch_eligibility(self, student_ids: List[str], 
                                  system_name: str = None) -> Dict[str, Tuple[bool, str]]:
        """
        Validate eligibility for multiple students.
        
        Args:
            student_ids: List of student identifiers
            system_name: Name of the financial aid system to use
        
        Returns:
            Dictionary mapping student_id to (eligible, reason) tuples
        """
        adapter = self.get_adapter(system_name)
        if not adapter:
            logger.error("No financial aid system adapter available")
            return {sid: (False, 'No financial aid system configured') for sid in student_ids}
        
        results = {}
        for student_id in student_ids:
            eligible, reason = adapter.validate_student_eligibility(student_id)
            results[student_id] = (eligible, reason)
        
        return results


def generate_financial_aid_export(scholarship_awards: List, 
                                  format: str = 'csv',
                                  system_type: str = 'banner') -> str:
    """
    Generate a standardized export file for financial aid systems.
    
    Args:
        scholarship_awards: List of ScholarshipAward model instances
        format: Export format ('csv', 'json', 'xml')
        system_type: Target system type ('banner', 'workday', etc.)
    
    Returns:
        File path to the generated export file
    
    This function creates export files in formats compatible with common
    financial aid systems for bulk import of disbursement data.
    """
    import csv
    import tempfile
    from xml.etree.ElementTree import Element, SubElement, tostring
    from xml.dom.minidom import parseString
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    if format == 'csv':
        # Generate CSV format
        temp_file = tempfile.NamedTemporaryFile(
            mode='w', 
            delete=False, 
            suffix='.csv',
            newline=''
        )
        
        writer = csv.writer(temp_file)
        
        # Headers vary by system type
        if system_type == 'banner':
            headers = [
                'Student_ID', 'Fund_Code', 'Aid_Year', 'Disbursement_Date',
                'Amount', 'Reference_Number', 'Description'
            ]
        else:
            headers = [
                'Student_ID', 'Scholarship_Name', 'Award_Date', 
                'Award_Amount', 'Disbursement_Date', 'Status'
            ]
        
        writer.writerow(headers)
        
        # Write award data
        for award in scholarship_awards:
            # Parse disbursement dates
            disbursement_dates = award.disbursement_dates
            if isinstance(disbursement_dates, str):
                disbursement_dates = json.loads(disbursement_dates)
            
            # Create a row for each disbursement date
            for i, disb_date in enumerate(disbursement_dates):
                if isinstance(disb_date, str):
                    disb_date = datetime.fromisoformat(disb_date)
                
                amount_per_disbursement = award.award_amount / len(disbursement_dates)
                
                if system_type == 'banner':
                    row = [
                        award.applicant.student_id,
                        'SCHLRSHP',  # Default fund code
                        award.award_date.year,
                        disb_date.strftime('%Y-%m-%d'),
                        f'{amount_per_disbursement:.2f}',
                        f'{award.id}-{i+1}',
                        award.scholarship_name
                    ]
                else:
                    row = [
                        award.applicant.student_id,
                        award.scholarship_name,
                        award.award_date.strftime('%Y-%m-%d'),
                        str(award.award_amount),
                        disb_date.strftime('%Y-%m-%d'),
                        award.status
                    ]
                
                writer.writerow(row)
        
        temp_file.close()
        logger.info(f"Generated CSV export: {temp_file.name}")
        return temp_file.name
    
    elif format == 'json':
        # Generate JSON format
        temp_file = tempfile.NamedTemporaryFile(
            mode='w',
            delete=False,
            suffix='.json'
        )
        
        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'system_type': system_type,
            'disbursements': []
        }
        
        for award in scholarship_awards:
            disbursement_dates = award.disbursement_dates
            if isinstance(disbursement_dates, str):
                disbursement_dates = json.loads(disbursement_dates)
            
            for i, disb_date in enumerate(disbursement_dates):
                if isinstance(disb_date, str):
                    disb_date = datetime.fromisoformat(disb_date)
                
                amount_per_disbursement = award.award_amount / len(disbursement_dates)
                
                disbursement = {
                    'student_id': award.applicant.student_id,
                    'student_name': award.applicant.name,
                    'scholarship_name': award.scholarship_name,
                    'award_date': award.award_date.isoformat(),
                    'disbursement_date': disb_date.isoformat(),
                    'amount': str(amount_per_disbursement),
                    'total_award_amount': str(award.award_amount),
                    'disbursement_number': i + 1,
                    'total_disbursements': len(disbursement_dates),
                    'reference_number': f'{award.id}-{i+1}',
                    'status': award.status
                }
                
                export_data['disbursements'].append(disbursement)
        
        json.dump(export_data, temp_file, indent=2)
        temp_file.close()
        logger.info(f"Generated JSON export: {temp_file.name}")
        return temp_file.name
    
    elif format == 'xml':
        # Generate XML format
        root = Element('FinancialAidExport')
        root.set('timestamp', datetime.now().isoformat())
        root.set('systemType', system_type)
        
        disbursements_element = SubElement(root, 'Disbursements')
        
        for award in scholarship_awards:
            disbursement_dates = award.disbursement_dates
            if isinstance(disbursement_dates, str):
                disbursement_dates = json.loads(disbursement_dates)
            
            for i, disb_date in enumerate(disbursement_dates):
                if isinstance(disb_date, str):
                    disb_date = datetime.fromisoformat(disb_date)
                
                amount_per_disbursement = award.award_amount / len(disbursement_dates)
                
                disb_element = SubElement(disbursements_element, 'Disbursement')
                
                SubElement(disb_element, 'StudentID').text = award.applicant.student_id
                SubElement(disb_element, 'StudentName').text = award.applicant.name
                SubElement(disb_element, 'ScholarshipName').text = award.scholarship_name
                SubElement(disb_element, 'AwardDate').text = award.award_date.strftime('%Y-%m-%d')
                SubElement(disb_element, 'DisbursementDate').text = disb_date.strftime('%Y-%m-%d')
                SubElement(disb_element, 'Amount').text = f'{amount_per_disbursement:.2f}'
                SubElement(disb_element, 'ReferenceNumber').text = f'{award.id}-{i+1}'
                SubElement(disb_element, 'Status').text = award.status
        
        # Pretty print XML
        xml_string = tostring(root, encoding='unicode')
        pretty_xml = parseString(xml_string).toprettyxml(indent='  ')
        
        temp_file = tempfile.NamedTemporaryFile(
            mode='w',
            delete=False,
            suffix='.xml'
        )
        temp_file.write(pretty_xml)
        temp_file.close()
        logger.info(f"Generated XML export: {temp_file.name}")
        return temp_file.name
    
    else:
        raise ValueError(f"Unsupported export format: {format}")
