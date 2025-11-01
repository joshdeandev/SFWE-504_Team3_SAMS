from django.shortcuts import render
from django.http import HttpResponse
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import os
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
import csv
import tempfile


@dataclass
class ApplicantData:
    """Data class representing detailed applicant information."""
    name: str
    student_id: str
    netid: str
    major: str
    minor: Optional[str] = None
    academic_achievements: List[Dict[str, Any]] = field(default_factory=list)  # List of achievements with details
    financial_info: Dict[str, Any] = field(default_factory=dict)  # Financial information
    essays: List[Dict[str, str]] = field(default_factory=list)  # List of essay submissions with prompts
    gpa: float = 0.0
    academic_level: str = ""  # Freshman, Sophomore, Junior, Senior, Graduate
    expected_graduation: Optional[datetime] = None
    academic_history: List[Dict[str, Any]] = field(default_factory=list)  # Previous academic records
    interview_notes: Optional[str] = None  # Notes from scholarship interview
    committee_feedback: List[Dict[str, Any]] = field(default_factory=list)  # Feedback from selection committee

@dataclass
class ScholarshipAward:
    """Data class representing a scholarship award to a specific applicant."""
    scholarship_name: str
    applicant: ApplicantData  # Changed from applicant_name to full ApplicantData
    award_date: datetime
    award_amount: float
    disbursement_dates: List[datetime]
    requirements_met: List[str]
    requirements_pending: List[str]
    status: str  # 'active', 'completed', 'revoked'
    performance_metrics: Dict[str, Any]  # GPA, participation, etc.
    essays_evaluation: Optional[List[Dict[str, Any]]] = None  # Evaluation of submitted essays
    interview_notes: Optional[str] = None  # Notes from scholarship interview
    committee_feedback: Optional[List[Dict[str, str]]] = None  # Feedback from selection committee
    notes: Optional[str] = None

@dataclass
class Scholarship:
    """Data class representing a scholarship with all relevant details."""
    name: str
    description: str
    eligibility_criteria: List[str]
    donor_info: dict
    disbursement_requirements: List[str]
    frequency: str
    amount: float
    deadline: Optional[datetime] = None
    review_dates: List[datetime] = None  # Dates for periodic review
    reporting_schedule: Dict[str, datetime] = None  # Schedule for required reports
    awards: List[ScholarshipAward] = None  # List of awards made under this scholarship


class ReportEngine:
    """OOP Report Engine for generating scholarship reports and summaries."""

    def __init__(self):
        self.scholarships = []

    # Function to generate donor report. Meets requirement SFWE504_3-LLR-2    
    def generate_donor_report(self, donor_name: str, start_date: Optional[datetime] = None, 
                            end_date: Optional[datetime] = None) -> dict:
        """Generate a comprehensive report for a specific donor including key dates and award summaries.

        Args:
            donor_name (str): Name of the donor to generate report for
            start_date (datetime, optional): Start date for report period
            end_date (datetime, optional): End date for report period

        Returns:
            dict: Detailed donor report including scholarships, awards, and key dates
        """
        # Default to last year if no dates provided
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - pd.DateOffset(years=1)

        # Filter scholarships for this donor
        donor_scholarships = [
            s for s in self.scholarships
            if s.donor_info.get('name') == donor_name
        ]

        active_awards = []
        completed_awards = []
        upcoming_deadlines = []
        upcoming_reviews = []
        reporting_requirements = []

        total_awarded = 0
        total_disbursed = 0

        for scholarship in donor_scholarships:
            # Track deadlines
            if scholarship.deadline and start_date <= scholarship.deadline <= end_date:
                upcoming_deadlines.append({
                    'scholarship': scholarship.name,
                    'deadline': scholarship.deadline,
                    'type': 'Application Deadline'
                })

            # Track review dates
            if scholarship.review_dates:
                for review_date in scholarship.review_dates:
                    if start_date <= review_date <= end_date:
                        upcoming_reviews.append({
                            'scholarship': scholarship.name,
                            'date': review_date,
                            'type': 'Performance Review'
                        })

            # Track reporting requirements
            if scholarship.reporting_schedule:
                for report_type, report_date in scholarship.reporting_schedule.items():
                    if start_date <= report_date <= end_date:
                        reporting_requirements.append({
                            'scholarship': scholarship.name,
                            'date': report_date,
                            'type': report_type
                        })

            # Process awards
            if scholarship.awards:
                for award in scholarship.awards:
                    # Only include awards within the date range
                    if start_date <= award.award_date <= end_date:
                        total_awarded += award.award_amount
                        
                        # Calculate disbursed amount
                        disbursed = sum(
                            award.award_amount / len(award.disbursement_dates)
                            for date in award.disbursement_dates
                            if date <= end_date
                        )
                        total_disbursed += disbursed

                        award_summary = {
                            'scholarship': scholarship.name,
                            'recipient': award.applicant_name,
                            'amount': award.award_amount,
                            'disbursed': disbursed,
                            'award_date': award.award_date,
                            'status': award.status,
                            'requirements_met': award.requirements_met,
                            'requirements_pending': award.requirements_pending,
                            'performance_metrics': award.performance_metrics,
                            'next_disbursement': next(
                                (d for d in award.disbursement_dates if d > end_date),
                                None
                            )
                        }

                        if award.status == 'completed':
                            completed_awards.append(award_summary)
                        elif award.status == 'active':
                            active_awards.append(award_summary)

        # Sort all dates
        upcoming_deadlines.sort(key=lambda x: x['deadline'])
        upcoming_reviews.sort(key=lambda x: x['date'])
        reporting_requirements.sort(key=lambda x: x['date'])
        active_awards.sort(key=lambda x: x['next_disbursement'] or end_date)
        completed_awards.sort(key=lambda x: x['award_date'], reverse=True)

        return {
            'donor_name': donor_name,
            'report_period': {
                'start': start_date,
                'end': end_date
            },
            'summary': {
                'total_scholarships': len(donor_scholarships),
                'total_awarded': total_awarded,
                'total_disbursed': total_disbursed,
                'active_awards': len(active_awards),
                'completed_awards': len(completed_awards)
            },
            'key_dates': {
                'upcoming_deadlines': upcoming_deadlines,
                'upcoming_reviews': upcoming_reviews,
                'reporting_requirements': reporting_requirements
            },
            'awards': {
                'active': active_awards,
                'completed': completed_awards
            },
            'scholarships': [{
                'name': s.name,
                'amount': s.amount,
                'frequency': s.frequency,
                'deadline': s.deadline,
                'description': s.description
            } for s in donor_scholarships]
        }

    def export_donor_report_to_excel(self, donor_name: str, output_path: str,
                                   start_date: Optional[datetime] = None,
                                   end_date: Optional[datetime] = None) -> str:
        """Export donor report to Excel format.

        Args:
            donor_name (str): Name of the donor
            output_path (str): Path where to save the Excel file
            start_date (datetime, optional): Start date for report period
            end_date (datetime, optional): End date for report period

        Returns:
            str: Path to the generated Excel file
        """
        report_data = self.generate_donor_report(donor_name, start_date, end_date)
        
        wb = Workbook()
        
        # Summary Sheet
        ws_summary = wb.active
        ws_summary.title = "Summary"
        ws_summary['A1'] = f"Donor Report: {donor_name}"
        ws_summary['A2'] = "Report Period:"
        ws_summary['B2'] = f"{report_data['report_period']['start'].strftime('%Y-%m-%d')} to {report_data['report_period']['end'].strftime('%Y-%m-%d')}"
        
        # Summary Statistics
        summary_headers = ['Metric', 'Value']
        summary_data = [
            ['Total Scholarships', report_data['summary']['total_scholarships']],
            ['Total Awarded', f"${report_data['summary']['total_awarded']:,.2f}"],
            ['Total Disbursed', f"${report_data['summary']['total_disbursed']:,.2f}"],
            ['Active Awards', report_data['summary']['active_awards']],
            ['Completed Awards', report_data['summary']['completed_awards']]
        ]
        
        for row_idx, row in enumerate([summary_headers] + summary_data, 4):
            for col_idx, value in enumerate(row, 1):
                cell = ws_summary.cell(row=row_idx, column=col_idx, value=value)
                if row_idx == 4:  # Headers
                    cell.font = Font(bold=True)
                    
        # Key Dates Sheet
        ws_dates = wb.create_sheet("Key Dates")
        date_headers = ['Type', 'Scholarship', 'Date']
        
        # Combine all dates
        all_dates = (
            [['Deadline'] + [d['scholarship'], d['deadline'].strftime('%Y-%m-%d')] 
             for d in report_data['key_dates']['upcoming_deadlines']] +
            [['Review'] + [d['scholarship'], d['date'].strftime('%Y-%m-%d')] 
             for d in report_data['key_dates']['upcoming_reviews']] +
            [['Report'] + [d['scholarship'], d['date'].strftime('%Y-%m-%d')] 
             for d in report_data['key_dates']['reporting_requirements']]
        )
        
        for row_idx, row in enumerate([date_headers] + sorted(all_dates, key=lambda x: x[2]), 1):
            for col_idx, value in enumerate(row, 1):
                cell = ws_dates.cell(row=row_idx, column=col_idx, value=value)
                if row_idx == 1:  # Headers
                    cell.font = Font(bold=True)
        
        # Active Awards Sheet
        ws_active = wb.create_sheet("Active Awards")
        award_headers = ['Scholarship', 'Recipient', 'Amount', 'Disbursed', 'Status', 
                        'Requirements Met', 'Requirements Pending', 'Next Disbursement']
        
        award_data = [[
            award['scholarship'],
            award['recipient'],
            f"${award['amount']:,.2f}",
            f"${award['disbursed']:,.2f}",
            award['status'],
            '; '.join(award['requirements_met']),
            '; '.join(award['requirements_pending']),
            award['next_disbursement'].strftime('%Y-%m-%d') if award['next_disbursement'] else 'N/A'
        ] for award in report_data['awards']['active']]
        
        for row_idx, row in enumerate([award_headers] + award_data, 1):
            for col_idx, value in enumerate(row, 1):
                cell = ws_active.cell(row=row_idx, column=col_idx, value=value)
                if row_idx == 1:  # Headers
                    cell.font = Font(bold=True)
        
        # Adjust column widths
        for ws in [ws_summary, ws_dates, ws_active]:
            for col in ws.columns:
                max_length = 0
                for cell in col:
                    try:
                        max_length = max(max_length, len(str(cell.value)))
                    except:
                        pass
                ws.column_dimensions[chr(64 + col[0].column)].width = min(max_length + 2, 50)
        
        wb.save(output_path)
        return output_path

    def export_donor_report_to_csv(self, donor_name: str, output_path: str,
                                 start_date: Optional[datetime] = None,
                                 end_date: Optional[datetime] = None) -> str:
        """Export donor report to CSV format.

        Args:
            donor_name (str): Name of the donor
            output_path (str): Path where to save the CSV file
            start_date (datetime, optional): Start date for report period
            end_date (datetime, optional): End date for report period

        Returns:
            str: Path to the generated CSV file
        """
        report_data = self.generate_donor_report(donor_name, start_date, end_date)
        
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Header
            writer.writerow([f"Donor Report: {donor_name}"])
            writer.writerow(['Report Period:', 
                           f"{report_data['report_period']['start'].strftime('%Y-%m-%d')} to "
                           f"{report_data['report_period']['end'].strftime('%Y-%m-%d')}"])
            writer.writerow([])
            
            # Summary Section
            writer.writerow(['Summary Statistics'])
            writer.writerow(['Metric', 'Value'])
            writer.writerow(['Total Scholarships', report_data['summary']['total_scholarships']])
            writer.writerow(['Total Awarded', f"${report_data['summary']['total_awarded']:,.2f}"])
            writer.writerow(['Total Disbursed', f"${report_data['summary']['total_disbursed']:,.2f}"])
            writer.writerow(['Active Awards', report_data['summary']['active_awards']])
            writer.writerow(['Completed Awards', report_data['summary']['completed_awards']])
            writer.writerow([])
            
            # Key Dates Section
            writer.writerow(['Key Dates'])
            writer.writerow(['Type', 'Scholarship', 'Date'])
            
            for deadline in report_data['key_dates']['upcoming_deadlines']:
                writer.writerow(['Deadline', deadline['scholarship'], 
                               deadline['deadline'].strftime('%Y-%m-%d')])
            
            for review in report_data['key_dates']['upcoming_reviews']:
                writer.writerow(['Review', review['scholarship'], 
                               review['date'].strftime('%Y-%m-%d')])
            
            for report in report_data['key_dates']['reporting_requirements']:
                writer.writerow(['Report', report['scholarship'], 
                               report['date'].strftime('%Y-%m-%d')])
            writer.writerow([])
            
            # Active Awards Section
            writer.writerow(['Active Awards'])
            writer.writerow(['Scholarship', 'Recipient', 'Amount', 'Disbursed', 'Status',
                           'Requirements Met', 'Requirements Pending', 'Next Disbursement'])
            
            for award in report_data['awards']['active']:
                writer.writerow([
                    award['scholarship'],
                    award['recipient'],
                    f"${award['amount']:,.2f}",
                    f"${award['disbursed']:,.2f}",
                    award['status'],
                    '; '.join(award['requirements_met']),
                    '; '.join(award['requirements_pending']),
                    award['next_disbursement'].strftime('%Y-%m-%d') if award['next_disbursement'] else 'N/A'
                ])
        
        return output_path

    def export_donor_report_to_pdf(self, donor_name: str, output_path: str,
                                 start_date: Optional[datetime] = None,
                                 end_date: Optional[datetime] = None) -> str:
        """Export donor report to PDF format.

        Args:
            donor_name (str): Name of the donor
            output_path (str): Path where to save the PDF file
            start_date (datetime, optional): Start date for report period
            end_date (datetime, optional): End date for report period

        Returns:
            str: Path to the generated PDF file
        """
        report_data = self.generate_donor_report(donor_name, start_date, end_date)
        
        doc = SimpleDocTemplate(output_path, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()

        # Title
        story.append(Paragraph(f"Donor Report: {donor_name}", styles['Heading1']))
        story.append(Paragraph(
            f"Report Period: {report_data['report_period']['start'].strftime('%Y-%m-%d')} to "
            f"{report_data['report_period']['end'].strftime('%Y-%m-%d')}", 
            styles['Normal']
        ))

        # Summary Section
        story.append(Paragraph("Summary", styles['Heading2']))
        summary_data = [
            ['Total Scholarships', str(report_data['summary']['total_scholarships'])],
            ['Total Awarded', f"${report_data['summary']['total_awarded']:,.2f}"],
            ['Total Disbursed', f"${report_data['summary']['total_disbursed']:,.2f}"],
            ['Active Awards', str(report_data['summary']['active_awards'])],
            ['Completed Awards', str(report_data['summary']['completed_awards'])]
        ]
        summary_table = Table(summary_data)
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(summary_table)
        story.append(Paragraph("<br/>", styles['Normal']))

        # Key Dates Section
        story.append(Paragraph("Key Dates and Deadlines", styles['Heading2']))
        if report_data['key_dates']['upcoming_deadlines']:
            story.append(Paragraph("Upcoming Deadlines:", styles['Heading3']))
            for deadline in report_data['key_dates']['upcoming_deadlines']:
                story.append(Paragraph(
                    f"• {deadline['scholarship']}: {deadline['deadline'].strftime('%Y-%m-%d')}",
                    styles['Normal']
                ))

        if report_data['key_dates']['upcoming_reviews']:
            story.append(Paragraph("Upcoming Reviews:", styles['Heading3']))
            for review in report_data['key_dates']['upcoming_reviews']:
                story.append(Paragraph(
                    f"• {review['scholarship']}: {review['date'].strftime('%Y-%m-%d')}",
                    styles['Normal']
                ))

        # Active Awards Section
        story.append(Paragraph("Active Awards", styles['Heading2']))
        for award in report_data['awards']['active']:
            story.append(Paragraph(f"Scholarship: {award['scholarship']}", styles['Heading3']))
            story.append(Paragraph(f"Recipient: {award['recipient']}", styles['Normal']))
            story.append(Paragraph(f"Amount: ${award['amount']:,.2f}", styles['Normal']))
            story.append(Paragraph(f"Disbursed: ${award['disbursed']:,.2f}", styles['Normal']))
            if award['next_disbursement']:
                story.append(Paragraph(
                    f"Next Disbursement: {award['next_disbursement'].strftime('%Y-%m-%d')}",
                    styles['Normal']
                ))
            story.append(Paragraph("Requirements Status:", styles['Normal']))
            for req in award['requirements_met']:
                story.append(Paragraph(f"✓ {req}", styles['Normal']))
            for req in award['requirements_pending']:
                story.append(Paragraph(f"□ {req}", styles['Normal']))
            story.append(Paragraph("<br/>", styles['Normal']))

        doc.build(story)
        return output_path

    def add_scholarship(self, scholarship: Scholarship):
        """Add a new scholarship to the system."""
        self.scholarships.append(scholarship)

    # Function to generate pre-screening report. Meets requirement for pre-screening applicants, SFWE504_3-LLR-7, SFWE504_3-LLR-25, SFWE504_3-LLR-26.
    def generate_prescreening_report(self, applicants: List[ApplicantData], scholarship_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate a pre-screening report identifying applicants who meet scholarship eligibility criteria.
        
        Args:
            applicants (List[ApplicantData]): List of applicants to evaluate
            scholarship_id (str, optional): Specific scholarship to evaluate for. If None, evaluate all scholarships.
            
        Returns:
            dict: Pre-screening report containing:
                - Qualified applicants list per scholarship
                - Detailed eligibility analysis for each applicant
                - Review scores and committee comments
                - Application progress tracking
                - Match statistics and summary
                - Scholarship-specific requirements status
                - Comprehensive applicant qualifications
        """
        report = {
            'generated_date': datetime.now(),
            'scholarships_evaluated': 0,
            'total_applicants': len(applicants),
            'matches': [],
            'qualified_applicants': {},  # Dictionary to store qualified applicants per scholarship
            'applicant_analysis': {},    # Detailed analysis of each applicant
            'review_tracking': {},       # Track review scores and comments
            'application_progress': {},   # Track application completion status
            'summary': {
                'total_matches': 0,
                'match_rate': 0.0,
                'scholarships_with_matches': 0,
                'qualification_distribution': {},  # Distribution of qualification rates
                'review_statistics': {    # Statistics about review scores
                    'average_scores': {},
                    'review_completion_rate': 0.0
                },
                'application_completion': {  # Track overall application completion
                    'complete': 0,
                    'in_progress': 0,
                    'incomplete': 0
                }
            }
        }
        
        # Filter scholarships if scholarship_id is provided
        scholarships_to_evaluate = [s for s in self.scholarships if scholarship_id is None or s.name == scholarship_id]
        report['scholarships_evaluated'] = len(scholarships_to_evaluate)
        
        for scholarship in scholarships_to_evaluate:
            scholarship_matches = []
            qualified_applicants = []
            qualification_scores = []  # Track qualification scores for distribution analysis
            
            for applicant in applicants:
                eligibility_results = []
                meets_all_criteria = True
                criteria_met_count = 0
                total_criteria = len(scholarship.eligibility_criteria)
                
                # Evaluate each eligibility criterion
                for criterion in scholarship.eligibility_criteria:
                    is_met = False
                    reason = ""
                    details = {}
                    
                    # Evaluate GPA requirements
                    if "GPA" in criterion:
                        required_gpa = float(criterion.split("+")[0].split()[-1])
                        is_met = applicant.gpa >= required_gpa
                        reason = f"GPA: {applicant.gpa:.2f} vs required {required_gpa}+"
                        details = {
                            'type': 'gpa',
                            'required': required_gpa,
                            'actual': applicant.gpa,
                            'difference': applicant.gpa - required_gpa
                        }
                    
                    # Evaluate major requirements
                    elif "major" in criterion.lower():
                        required_major = criterion.split("major")[0].strip()
                        is_met = required_major.lower() in applicant.major.lower()
                        reason = f"Major: {applicant.major} vs required {required_major}"
                        details = {
                            'type': 'major',
                            'required': required_major,
                            'actual': applicant.major,
                            'exact_match': required_major.lower() == applicant.major.lower()
                        }
                    
                    # Evaluate enrollment status
                    elif "enrollment" in criterion.lower():
                        # This would need to be enhanced with actual enrollment status data
                        is_met = True  # Assuming full-time enrollment for demo
                        reason = "Enrollment status verified"
                        details = {
                            'type': 'enrollment',
                            'status': 'full-time',
                            'verified': True
                        }
                    
                    # Track met criteria
                    if is_met:
                        criteria_met_count += 1
                    
                    # Add detailed evaluation results
                    eligibility_results.append({
                        'criterion': criterion,
                        'is_met': is_met,
                        'reason': reason,
                        'details': details
                    })
                    
                    if not is_met:
                        meets_all_criteria = False
                
                # Calculate qualification score
                qualification_score = (criteria_met_count / total_criteria) * 100
                qualification_scores.append(qualification_score)
                
                # Calculate application completion status
                required_components = {
                    'personal_info': bool(applicant.name and applicant.student_id),
                    'academic_info': bool(applicant.major and applicant.academic_level),
                    'essays': bool(applicant.essays),
                    'financial_info': bool(applicant.financial_info),
                    'academic_records': bool(applicant.academic_history)
                }
                completion_percentage = (sum(1 for v in required_components.values() if v) / len(required_components)) * 100
                
                # Determine application status
                if completion_percentage == 100:
                    application_status = 'complete'
                elif completion_percentage > 50:
                    application_status = 'in_progress'
                else:
                    application_status = 'incomplete'

                # Get review scores and comments if available
                review_data = {
                    'academic_review': {
                        'score': None,
                        'comments': [],
                        'reviewer': None,
                        'date': None
                    },
                    'essay_review': {
                        'scores': [],
                        'comments': [],
                        'reviewers': [],
                        'dates': []
                    },
                    'interview_notes': None,
                    'committee_feedback': []
                }
                
                # Process essay evaluations if available
                if hasattr(applicant, 'essays') and applicant.essays:
                    for essay in applicant.essays:
                        if hasattr(essay, 'evaluation'):
                            review_data['essay_review']['scores'].append(essay.evaluation.get('score'))
                            review_data['essay_review']['comments'].append(essay.evaluation.get('feedback'))
                            review_data['essay_review']['reviewers'].append(essay.evaluation.get('reviewer'))
                            review_data['essay_review']['dates'].append(essay.evaluation.get('date'))
                
                # Process interview notes if available
                if hasattr(applicant, 'interview_notes'):
                    review_data['interview_notes'] = applicant.interview_notes
                
                # Process committee feedback if available
                if hasattr(applicant, 'committee_feedback'):
                    review_data['committee_feedback'] = applicant.committee_feedback

                # Prepare detailed applicant assessment
                applicant_assessment = {
                    'applicant': {
                        'name': applicant.name,
                        'student_id': applicant.student_id,
                        'major': applicant.major,
                        'gpa': applicant.gpa,
                        'academic_level': applicant.academic_level
                    },
                    'qualification_score': qualification_score,
                    'eligibility_details': eligibility_results,
                    'criteria_met_count': criteria_met_count,
                    'total_criteria': total_criteria,
                    'fully_qualified': meets_all_criteria,
                    'application_status': {
                        'status': application_status,
                        'completion_percentage': completion_percentage,
                        'missing_components': [
                            component for component, completed in required_components.items() 
                            if not completed
                        ]
                    },
                    'review_data': review_data
                }
                
                if meets_all_criteria:
                    scholarship_matches.append(applicant_assessment)
                    qualified_applicants.append({
                        'applicant': applicant_assessment['applicant'],
                        'qualification_score': qualification_score
                    })
                
                # Store detailed analysis for each applicant
                if applicant.student_id not in report['applicant_analysis']:
                    report['applicant_analysis'][applicant.student_id] = []
                report['applicant_analysis'][applicant.student_id].append({
                    'scholarship_name': scholarship.name,
                    'assessment': applicant_assessment
                })
            
            if scholarship_matches:
                # Sort qualified applicants by qualification score
                qualified_applicants.sort(key=lambda x: x['qualification_score'], reverse=True)
                
                report['matches'].append({
                    'scholarship_name': scholarship.name,
                    'description': scholarship.description,
                    'amount': scholarship.amount,
                    'deadline': scholarship.deadline,
                    'matches': scholarship_matches,
                    'qualification_distribution': {
                        'min_score': min(qualification_scores) if qualification_scores else 0,
                        'max_score': max(qualification_scores) if qualification_scores else 0,
                        'average_score': sum(qualification_scores) / len(qualification_scores) if qualification_scores else 0
                    }
                })
                
                # Store qualified applicants for this scholarship
                report['qualified_applicants'][scholarship.name] = qualified_applicants
        
        # Calculate comprehensive summary statistics
        total_matches = sum(len(s['matches']) for s in report['matches'])
        scholarships_with_matches = len(report['matches'])
        
        # Calculate qualification distribution across all scholarships
        all_qualification_scores = []
        for scholarship in report['matches']:
            all_qualification_scores.extend([match['qualification_score'] for match in scholarship['matches']])
        
        # Collect review statistics
        review_scores = []
        essay_scores = []
        total_reviews = 0
        completed_reviews = 0
        
        # Count application completion status
        application_completion = {
            'complete': 0,
            'in_progress': 0,
            'incomplete': 0
        }
        
        for scholarship in report['matches']:
            for match in scholarship['matches']:
                # Track application status
                status = match['application_status']['status']
                application_completion[status] += 1
                
                # Track review completion
                review_data = match['review_data']
                if review_data['academic_review']['score'] is not None:
                    review_scores.append(review_data['academic_review']['score'])
                    completed_reviews += 1
                
                for essay_score in review_data['essay_review']['scores']:
                    if essay_score is not None:
                        essay_scores.append(essay_score)
                        completed_reviews += 1
                
                total_reviews += 1  # Count expected reviews
                if review_data['interview_notes']:
                    completed_reviews += 1
                total_reviews += 1  # Count interview as expected
        
        # Calculate average review scores
        avg_review_score = sum(review_scores) / len(review_scores) if review_scores else 0
        avg_essay_score = sum(essay_scores) / len(essay_scores) if essay_scores else 0
        review_completion_rate = (completed_reviews / total_reviews) if total_reviews > 0 else 0
        
        report['summary'] = {
            'total_matches': total_matches,
            'match_rate': (total_matches / len(applicants)) if applicants else 0.0,
            'scholarships_with_matches': scholarships_with_matches,
            'match_distribution': {
                'scholarship_match_rate': (scholarships_with_matches / len(scholarships_to_evaluate)) if scholarships_to_evaluate else 0.0,
                'average_matches_per_scholarship': (total_matches / len(scholarships_to_evaluate)) if scholarships_to_evaluate else 0.0
            },
            'qualification_distribution': {
                'min_score': min(all_qualification_scores) if all_qualification_scores else 0,
                'max_score': max(all_qualification_scores) if all_qualification_scores else 0,
                'average_score': sum(all_qualification_scores) / len(all_qualification_scores) if all_qualification_scores else 0,
                'score_ranges': {
                    '90-100': len([s for s in all_qualification_scores if 90 <= s <= 100]),
                    '80-89': len([s for s in all_qualification_scores if 80 <= s < 90]),
                    '70-79': len([s for s in all_qualification_scores if 70 <= s < 80]),
                    '60-69': len([s for s in all_qualification_scores if 60 <= s < 70]),
                    'Below 60': len([s for s in all_qualification_scores if s < 60])
                }
            },
            'review_statistics': {
                'average_scores': {
                    'academic_review': avg_review_score,
                    'essay_review': avg_essay_score
                },
                'review_completion_rate': review_completion_rate,
                'reviews_completed': completed_reviews,
                'total_reviews_expected': total_reviews
            },
            'application_completion': application_completion
        }
        
        return report

    def export_prescreening_report_to_pdf(self, applicants: List[ApplicantData], 
                                        scholarship_id: Optional[str] = None,
                                        output_path: str = None) -> str:
        """Export pre-screening report to PDF format."""
        report_data = self.generate_prescreening_report(applicants, scholarship_id)
        
        doc = SimpleDocTemplate(output_path, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()

        # Title
        story.append(Paragraph("Pre-screening Report", styles['Heading1']))
        story.append(Paragraph(
            f"Generated on: {report_data['generated_date'].strftime('%Y-%m-%d %H:%M:%S')}",
            styles['Normal']
        ))
        
        # Summary Section
        story.append(Paragraph("Summary", styles['Heading2']))
        summary_data = [
            ['Total Applicants', str(report_data['total_applicants'])],
            ['Total Matches', str(report_data['summary']['total_matches'])],
            ['Match Rate', f"{report_data['summary']['match_rate']*100:.1f}%"],
            ['Scholarships with Matches', str(report_data['summary']['scholarships_with_matches'])],
            ['Review Completion Rate', f"{report_data['summary']['review_statistics']['review_completion_rate']*100:.1f}%"],
            ['Applications Complete', str(report_data['summary']['application_completion']['complete'])],
            ['Applications In Progress', str(report_data['summary']['application_completion']['in_progress'])],
            ['Applications Incomplete', str(report_data['summary']['application_completion']['incomplete'])]
        ]
        
        summary_table = Table(summary_data)
        summary_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (0, -1), colors.grey),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke)
        ]))
        story.append(summary_table)
        story.append(Paragraph("<br/>", styles['Normal']))

        # Review Statistics
        story.append(Paragraph("Review Statistics", styles['Heading2']))
        review_stats = report_data['summary']['review_statistics']
        story.append(Paragraph(f"Average Academic Review Score: {review_stats['average_scores']['academic_review']:.1f}/10", styles['Normal']))
        story.append(Paragraph(f"Average Essay Review Score: {review_stats['average_scores']['essay_review']:.1f}/10", styles['Normal']))
        story.append(Paragraph(f"Reviews Completed: {review_stats['reviews_completed']} of {review_stats['total_reviews_expected']}", styles['Normal']))
        story.append(Paragraph("<br/>", styles['Normal']))

        # Matches by Scholarship
        for scholarship_match in report_data['matches']:
            story.append(Paragraph(scholarship_match['scholarship_name'], styles['Heading2']))
            story.append(Paragraph(scholarship_match['description'], styles['Normal']))
            story.append(Paragraph(
                f"Amount: ${scholarship_match['amount']:,.2f}", 
                styles['Normal']
            ))
            if scholarship_match['deadline']:
                story.append(Paragraph(
                    f"Deadline: {scholarship_match['deadline'].strftime('%Y-%m-%d')}",
                    styles['Normal']
                ))
            
            # Table of matching applicants with review scores
            story.append(Paragraph("Qualified Applicants:", styles['Heading3']))
            applicant_data = [['Name', 'Student ID', 'Major', 'GPA', 'Academic Level', 'Application Status', 'Review Score']]
            
            for match in scholarship_match['matches']:
                applicant = match['applicant']
                review_data = match.get('review_data', {})
                application_status = match.get('application_status', {})
                
                # Calculate average review score
                review_scores = []
                if review_data.get('academic_review', {}).get('score'):
                    review_scores.append(review_data['academic_review']['score'])
                if review_data.get('essay_review', {}).get('scores'):
                    review_scores.extend(review_data['essay_review']['scores'])
                avg_review_score = sum(review_scores) / len(review_scores) if review_scores else 'N/A'
                
                applicant_data.append([
                    applicant['name'],
                    applicant['student_id'],
                    applicant['major'],
                    f"{applicant['gpa']:.2f}",
                    applicant['academic_level'],
                    application_status.get('status', 'Unknown').title(),
                    f"{avg_review_score:.1f}" if isinstance(avg_review_score, float) else avg_review_score
                ])
            
            if len(applicant_data) > 1:
                applicant_table = Table(applicant_data)
                applicant_table.setStyle(TableStyle([
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold')
                ]))
                story.append(applicant_table)
            
            # Detailed Review Information
            for match in scholarship_match['matches']:
                applicant = match['applicant']
                review_data = match.get('review_data', {})
                story.append(Paragraph(f"\nDetailed Review for {applicant['name']}:", styles['Heading4']))
                
                # Essay Reviews
                if review_data.get('essay_review', {}).get('comments'):
                    story.append(Paragraph("Essay Reviews:", styles['Heading4']))
                    for i, (comment, score) in enumerate(zip(
                            review_data['essay_review']['comments'],
                            review_data['essay_review']['scores']), 1):
                        story.append(Paragraph(f"Essay {i} - Score: {score}/10", styles['Normal']))
                        story.append(Paragraph(f"Feedback: {comment}", styles['Normal']))
                
                # Interview Notes
                if review_data.get('interview_notes'):
                    story.append(Paragraph("Interview Notes:", styles['Heading4']))
                    story.append(Paragraph(review_data['interview_notes'], styles['Normal']))
                
                # Committee Feedback
                if review_data.get('committee_feedback'):
                    story.append(Paragraph("Committee Feedback:", styles['Heading4']))
                    for feedback in review_data['committee_feedback']:
                        story.append(Paragraph(
                            f"• {feedback['member']}: {feedback['comments']}", 
                            styles['Normal']
                        ))
            
            story.append(Paragraph("<br/>", styles['Normal']))

        doc.build(story)
        return output_path

    def export_prescreening_report_to_csv(self, applicants: List[ApplicantData],
                                         scholarship_id: Optional[str] = None,
                                         output_path: str = None) -> str:
        """Export pre-screening report to CSV format.

        Args:
            applicants (List[ApplicantData]): List of applicants to evaluate
            scholarship_id (str, optional): Specific scholarship to evaluate for
            output_path (str): Path where to save the CSV file

        Returns:
            str: Path to the generated CSV file
        """
        report_data = self.generate_prescreening_report(applicants, scholarship_id)
        
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header and summary information
            writer.writerow(['Pre-screening Report'])
            writer.writerow(['Generated Date:', report_data['generated_date'].strftime('%Y-%m-%d %H:%M:%S')])
            writer.writerow(['Total Applicants:', report_data['total_applicants']])
            writer.writerow(['Total Matches:', report_data['summary']['total_matches']])
            writer.writerow(['Match Rate:', f"{report_data['summary']['match_rate']*100:.1f}%"])
            writer.writerow(['Scholarships with Matches:', report_data['summary']['scholarships_with_matches']])
            writer.writerow([])
            
            # Write review statistics
            writer.writerow(['Review Statistics'])
            review_stats = report_data['summary']['review_statistics']
            writer.writerow(['Average Academic Review Score:', f"{review_stats['average_scores']['academic_review']:.1f}/10"])
            writer.writerow(['Average Essay Review Score:', f"{review_stats['average_scores']['essay_review']:.1f}/10"])
            writer.writerow(['Reviews Completed:', review_stats['reviews_completed']])
            writer.writerow(['Total Reviews Expected:', review_stats['total_reviews_expected']])
            writer.writerow(['Review Completion Rate:', f"{review_stats['review_completion_rate']*100:.1f}%"])
            writer.writerow([])
            
            # Write application completion statistics
            writer.writerow(['Application Completion'])
            completion_stats = report_data['summary']['application_completion']
            writer.writerow(['Complete:', completion_stats['complete']])
            writer.writerow(['In Progress:', completion_stats['in_progress']])
            writer.writerow(['Incomplete:', completion_stats['incomplete']])
            writer.writerow([])
            
            # Write detailed matches for each scholarship
            writer.writerow(['Scholarship Matches'])
            writer.writerow(['Scholarship Name', 'Applicant Name', 'Student ID', 'Major', 'GPA', 
                           'Academic Level', 'Application Status', 'Qualification Score', 
                           'Requirements Met', 'Requirements Pending', 'Review Score', 'Has Interview', 
                           'Has Committee Feedback'])
            
            for match in report_data['matches']:
                scholarship_name = match['scholarship_name']
                for applicant_match in match['matches']:
                    applicant = applicant_match['applicant']
                    review_data = applicant_match['review_data']
                    
                    # Calculate average review score
                    review_scores = []
                    if review_data.get('academic_review', {}).get('score'):
                        review_scores.append(review_data['academic_review']['score'])
                    if review_data.get('essay_review', {}).get('scores'):
                        review_scores.extend(review_data['essay_review']['scores'])
                    avg_review_score = f"{sum(review_scores) / len(review_scores):.1f}" if review_scores else 'N/A'
                    
                    writer.writerow([
                        scholarship_name,
                        applicant['name'],
                        applicant['student_id'],
                        applicant['major'],
                        f"{applicant['gpa']:.2f}",
                        applicant['academic_level'],
                        applicant_match['application_status']['status'].title(),
                        f"{applicant_match['qualification_score']:.1f}%",
                        '; '.join(applicant_match.get('criteria_met', [])),
                        '; '.join(applicant_match.get('requirements_pending', [])),
                        avg_review_score,
                        'Yes' if review_data.get('interview_notes') else 'No',
                        'Yes' if review_data.get('committee_feedback') else 'No'
                    ])
            writer.writerow([])
            
            # Write detailed review information
            writer.writerow(['Detailed Reviews'])
            writer.writerow(['Applicant Name', 'Student ID', 'Review Type', 'Score', 'Comments', 'Reviewer', 'Date'])
            
            for match in report_data['matches']:
                for applicant_match in match['matches']:
                    applicant = applicant_match['applicant']
                    review_data = applicant_match['review_data']
                    
                    # Academic Review
                    if review_data.get('academic_review', {}).get('score'):
                        writer.writerow([
                            applicant['name'],
                            applicant['student_id'],
                            'Academic Review',
                            review_data['academic_review']['score'],
                            review_data['academic_review'].get('comments', 'N/A'),
                            review_data['academic_review'].get('reviewer', 'N/A'),
                            review_data['academic_review'].get('date', 'N/A')
                        ])
                    
                    # Essay Reviews
                    for i, (score, comment, reviewer, date) in enumerate(zip(
                            review_data['essay_review']['scores'],
                            review_data['essay_review']['comments'],
                            review_data['essay_review']['reviewers'],
                            review_data['essay_review']['dates']
                    ), 1):
                        writer.writerow([
                            applicant['name'],
                            applicant['student_id'],
                            f'Essay Review {i}',
                            score,
                            comment,
                            reviewer,
                            date.strftime('%Y-%m-%d') if date else 'N/A'
                        ])
                    
                    # Committee Feedback
                    for feedback in review_data.get('committee_feedback', []):
                        writer.writerow([
                            applicant['name'],
                            applicant['student_id'],
                            'Committee Feedback',
                            feedback.get('recommendation', 'N/A'),
                            feedback['comments'],
                            feedback['member'],
                            feedback.get('date', 'N/A')
                        ])
        
        return output_path

    def export_prescreening_report_to_excel(self, applicants: List[ApplicantData],
                                          scholarship_id: Optional[str] = None,
                                          output_path: str = None) -> str:
        """Export pre-screening report to Excel format."""
        report_data = self.generate_prescreening_report(applicants, scholarship_id)
        
        wb = Workbook()
        
        # Summary Sheet
        ws_summary = wb.active
        ws_summary.title = "Summary"
        ws_summary['A1'] = "Pre-screening Report Summary"
        ws_summary['A2'] = "Generated on:"
        ws_summary['B2'] = report_data['generated_date'].strftime('%Y-%m-%d %H:%M:%S')
        
        summary_data = [
            ['Total Applicants', report_data['total_applicants']],
            ['Total Matches', report_data['summary']['total_matches']],
            ['Match Rate', f"{report_data['summary']['match_rate']*100:.1f}%"],
            ['Scholarships with Matches', report_data['summary']['scholarships_with_matches']],
            ['Review Completion Rate', f"{report_data['summary']['review_statistics']['review_completion_rate']*100:.1f}%"],
            ['Applications Complete', report_data['summary']['application_completion']['complete']],
            ['Applications In Progress', report_data['summary']['application_completion']['in_progress']],
            ['Applications Incomplete', report_data['summary']['application_completion']['incomplete']]
        ]
        
        for row_idx, (label, value) in enumerate(summary_data, 4):
            ws_summary[f'A{row_idx}'] = label
            ws_summary[f'B{row_idx}'] = value
            
        # Review Statistics
        ws_summary['A12'] = "Review Statistics"
        ws_summary['A12'].font = Font(bold=True)
        review_stats = [
            ['Average Academic Review Score', f"{report_data['summary']['review_statistics']['average_scores']['academic_review']:.1f}/10"],
            ['Average Essay Review Score', f"{report_data['summary']['review_statistics']['average_scores']['essay_review']:.1f}/10"],
            ['Reviews Completed', report_data['summary']['review_statistics']['reviews_completed']],
            ['Total Reviews Expected', report_data['summary']['review_statistics']['total_reviews_expected']]
        ]
        for row_idx, (label, value) in enumerate(review_stats, 13):
            ws_summary[f'A{row_idx}'] = label
            ws_summary[f'B{row_idx}'] = value
        
        # Matches Sheet with Review Information
        for scholarship_match in report_data['matches']:
            ws_matches = wb.create_sheet(scholarship_match['scholarship_name'][:31])
            
            # Scholarship details
            ws_matches['A1'] = "Scholarship Details"
            ws_matches['A2'] = "Description:"
            ws_matches['B2'] = scholarship_match['description']
            ws_matches['A3'] = "Amount:"
            ws_matches['B3'] = f"${scholarship_match['amount']:,.2f}"
            ws_matches['A4'] = "Deadline:"
            ws_matches['B4'] = (scholarship_match['deadline'].strftime('%Y-%m-%d') 
                              if scholarship_match['deadline'] else "No deadline set")
            
            # Matching applicants with review scores
            ws_matches['A6'] = "Qualified Applicants"
            headers = ['Name', 'Student ID', 'Major', 'GPA', 'Academic Level', 'Application Status', 
                      'Review Score', 'Essay Scores', 'Interview Complete', 'Committee Review']
            for col, header in enumerate(headers, 1):
                cell = ws_matches.cell(row=7, column=col, value=header)
                cell.font = Font(bold=True)
                cell.fill = PatternFill(start_color="CCCCCC", end_color="CCCCCC", fill_type="solid")
            
            row = 8
            for match in scholarship_match['matches']:
                applicant = match['applicant']
                review_data = match.get('review_data', {})
                application_status = match.get('application_status', {})
                
                # Calculate average review score
                review_scores = []
                if review_data.get('academic_review', {}).get('score'):
                    review_scores.append(review_data['academic_review']['score'])
                if review_data.get('essay_review', {}).get('scores'):
                    review_scores.extend(review_data['essay_review']['scores'])
                avg_review_score = sum(review_scores) / len(review_scores) if review_scores else 'N/A'
                
                ws_matches.cell(row=row, column=1, value=applicant['name'])
                ws_matches.cell(row=row, column=2, value=applicant['student_id'])
                ws_matches.cell(row=row, column=3, value=applicant['major'])
                ws_matches.cell(row=row, column=4, value=f"{applicant['gpa']:.2f}")
                ws_matches.cell(row=row, column=5, value=applicant['academic_level'])
                ws_matches.cell(row=row, column=6, value=application_status.get('status', 'Unknown').title())
                ws_matches.cell(row=row, column=7, value=f"{avg_review_score:.1f}" if isinstance(avg_review_score, float) else avg_review_score)
                ws_matches.cell(row=row, column=8, value=', '.join(f"{score:.1f}" for score in review_data.get('essay_review', {}).get('scores', [])) or 'N/A')
                ws_matches.cell(row=row, column=9, value='Yes' if review_data.get('interview_notes') else 'No')
                ws_matches.cell(row=row, column=10, value='Yes' if review_data.get('committee_feedback') else 'No')
                row += 1
                
                # Add detailed review information
                if review_data.get('interview_notes'):
                    row += 1
                    ws_matches.cell(row=row, column=1, value="Interview Notes:")
                    ws_matches.cell(row=row, column=2, value=review_data['interview_notes'], colspan=8)
                    row += 1
                
                if review_data.get('committee_feedback'):
                    row += 1
                    ws_matches.cell(row=row, column=1, value="Committee Feedback:")
                    for feedback in review_data['committee_feedback']:
                        row += 1
                        ws_matches.cell(row=row, column=2, value=f"{feedback['member']}: {feedback['comments']}", colspan=8)
                    row += 1
        
            # Create Review Details Sheet for each scholarship
            ws_reviews = wb.create_sheet(f"{scholarship_match['scholarship_name'][:20]}_Reviews")
            ws_reviews['A1'] = f"Detailed Review Information for {scholarship_match['scholarship_name']}"
            ws_reviews['A1'].font = Font(bold=True)
            
            row = 3
            for match in scholarship_match['matches']:
                applicant = match['applicant']
                review_data = match.get('review_data', {})
                
                ws_reviews.cell(row=row, column=1, value=f"Review Details for {applicant['name']}")
                ws_reviews.cell(row=row, column=1).font = Font(bold=True)
                row += 2
                
                # Essay Reviews
                if review_data.get('essay_review', {}).get('comments'):
                    ws_reviews.cell(row=row, column=1, value="Essay Reviews")
                    ws_reviews.cell(row=row, column=1).font = Font(bold=True)
                    row += 1
                    
                    for i, (comment, score, reviewer, date) in enumerate(zip(
                            review_data['essay_review']['comments'],
                            review_data['essay_review']['scores'],
                            review_data['essay_review']['reviewers'],
                            review_data['essay_review']['dates']), 1):
                        ws_reviews.cell(row=row, column=1, value=f"Essay {i}")
                        ws_reviews.cell(row=row, column=2, value=f"Score: {score}/10")
                        ws_reviews.cell(row=row+1, column=1, value="Reviewer:")
                        ws_reviews.cell(row=row+1, column=2, value=reviewer)
                        ws_reviews.cell(row=row+2, column=1, value="Date:")
                        ws_reviews.cell(row=row+2, column=2, value=date.strftime('%Y-%m-%d') if date else 'N/A')
                        ws_reviews.cell(row=row+3, column=1, value="Feedback:")
                        ws_reviews.cell(row=row+3, column=2, value=comment)
                        row += 5
                
                # Committee Feedback
                if review_data.get('committee_feedback'):
                    ws_reviews.cell(row=row, column=1, value="Committee Feedback")
                    ws_reviews.cell(row=row, column=1).font = Font(bold=True)
                    row += 1
                    
                    for feedback in review_data['committee_feedback']:
                        ws_reviews.cell(row=row, column=1, value="Member:")
                        ws_reviews.cell(row=row, column=2, value=feedback['member'])
                        ws_reviews.cell(row=row+1, column=1, value="Comments:")
                        ws_reviews.cell(row=row+1, column=2, value=feedback['comments'])
                        if 'date' in feedback:
                            ws_reviews.cell(row=row+2, column=1, value="Date:")
                            ws_reviews.cell(row=row+2, column=2, value=feedback['date'].strftime('%Y-%m-%d'))
                        row += 4
                
                row += 2  # Add space between applicants

        # Adjust column widths
        for ws in wb.worksheets:
            for col in ws.columns:
                max_length = 0
                for cell in col:
                    try:
                        max_length = max(max_length, len(str(cell.value)))
                    except:
                        pass
                ws.column_dimensions[chr(64 + col[0].column)].width = min(max_length + 2, 50)
        
        wb.save(output_path)
        return output_path

    # Function to generate applicant report. Meets requirement SFWE504_3-LLR-6.
    def generate_applicant_report(self, student_id: str = None, netid: str = None) -> Dict[str, Any]:
        """Generate a comprehensive report of an applicant's data and scholarship status.
        
        Args:
            student_id (str, optional): Student ID to search for
            netid (str, optional): NetID to search for (alternative to student_id)
            
        Returns:
            dict: Comprehensive applicant report including:
                - Personal and academic information
                - Current and past scholarships
                - Academic achievements
                - Financial information
                - Essay submissions and evaluations
        """
        # Find all awards for the applicant
        applicant_awards = []
        applicant_data = None
        
        for scholarship in self.scholarships:
            if scholarship.awards:
                for award in scholarship.awards:
                    if ((student_id and award.applicant.student_id == student_id) or 
                        (netid and award.applicant.netid == netid)):
                        applicant_awards.append({
                            'scholarship_name': award.scholarship_name,
                            'award_amount': award.award_amount,
                            'award_date': award.award_date,
                            'status': award.status,
                            'disbursements': [
                                {'date': date, 'amount': award.award_amount / len(award.disbursement_dates)}
                                for date in award.disbursement_dates
                            ],
                            'requirements_met': award.requirements_met,
                            'requirements_pending': award.requirements_pending,
                            'performance_metrics': award.performance_metrics,
                            'essays_evaluation': award.essays_evaluation,
                            'interview_notes': award.interview_notes,
                            'committee_feedback': award.committee_feedback
                        })
                        if not applicant_data:
                            applicant_data = award.applicant

        if not applicant_data:
            return None

        # Compile comprehensive applicant report
        report = {
            'personal_info': {
                'name': applicant_data.name,
                'student_id': applicant_data.student_id,
                'netid': applicant_data.netid,
            },
            'academic_info': {
                'major': applicant_data.major,
                'minor': applicant_data.minor,
                'gpa': applicant_data.gpa,
                'academic_level': applicant_data.academic_level,
                'expected_graduation': applicant_data.expected_graduation,
                'academic_history': applicant_data.academic_history,
            },
            'achievements': applicant_data.academic_achievements,
            'financial_info': applicant_data.financial_info,
            'essays': [{
                'prompt': essay['prompt'],
                'submission_date': essay['submission_date'],
                'content': essay['content']
            } for essay in applicant_data.essays],
            'scholarships': {
                'total_awards': len(applicant_awards),
                'total_amount': sum(award['award_amount'] for award in applicant_awards),
                'active_awards': [award for award in applicant_awards if award['status'] == 'active'],
                'completed_awards': [award for award in applicant_awards if award['status'] == 'completed'],
                'detailed_awards': applicant_awards
            }
        }

        return report

    # Function to generate scholarship report. Meets requirements SFWE504_3-LLR-3.
    def generate_scholarship_report(self, filters=None, export_format=None, output_path=None):
        """Generate a comprehensive report of scholarships and optionally export it.

        Args:
            filters (dict, optional): Filters to apply (e.g., {'frequency': 'annual'})
            export_format (str, optional): Format to export the report ('pdf', 'xlsx', 'csv')
            output_path (str, optional): Path where the exported file should be saved
                                       If not provided but export_format is, uses a temporary file

        Returns:
            Union[dict, str]: Report data as dictionary if no export_format specified,
                            otherwise path to the exported file
        """
        scholarships_data = self.scholarships

        # Apply filters if provided
        if filters:
            for key, value in filters.items():
                scholarships_data = [
                    s for s in scholarships_data
                    if getattr(s, key, None) == value
                ]

        # Generate report summary
        total_amount = sum(s.amount for s in scholarships_data)
        frequencies = {}
        for s in scholarships_data:
            frequencies[s.frequency] = frequencies.get(s.frequency, 0) + 1

        # Format scholarship details
        scholarship_details = []
        for s in scholarships_data:
            scholarship_details.append({
                'name': s.name,
                'description': s.description,
                'eligibility': s.eligibility_criteria,
                'donor': s.donor_info,
                'requirements': s.disbursement_requirements,
                'frequency': s.frequency,
                'amount': s.amount,
                'deadline': s.deadline.strftime('%Y-%m-%d') if s.deadline else 'No deadline set'
            })

        report_data = {
            'total_scholarships': len(scholarships_data),
            'total_amount': total_amount,
            'frequency_distribution': frequencies,
            'scholarships': scholarship_details
        }

        # Handle export if requested
        if export_format:
            if not output_path:
                # Create temporary file if no output path provided
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f'.{export_format}')
                output_path = temp_file.name
                temp_file.close()

            try:
                if export_format.lower() == 'pdf':
                    return self.export_to_pdf(output_path, filters)
                elif export_format.lower() == 'xlsx':
                    return self.export_to_excel(output_path, filters)
                elif export_format.lower() == 'csv':
                    return self.export_to_csv(output_path, filters)
                else:
                    raise ValueError(f"Unsupported export format: {export_format}")
            except Exception as e:
                if not output_path:
                    # Clean up temporary file on error
                    try:
                        os.unlink(output_path)
                    except:
                        pass
                raise e

        return report_data
        
    # Export Methods for PDF, Excel, CSV meeting the requirement SFWE504_3-LLR-3, SFWE504_3-LLR-11, and SFWE504_3-LLR-33
    def export_to_pdf(self, output_path: str, filters=None) -> str:
        """Export scholarships data to PDF format."""
        report_data = self.generate_scholarship_report(filters)
        
        doc = SimpleDocTemplate(output_path, pagesize=letter)
        story = []

        # Title and Summary
        styles = getSampleStyleSheet()
        story.append(Paragraph("Scholarship Report", styles['Heading1']))
        story.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
        story.append(Paragraph(f"Total Scholarships: {report_data['total_scholarships']}", styles['Normal']))
        story.append(Paragraph(f"Total Amount: ${report_data['total_amount']:,.2f}", styles['Normal']))

        # Frequency Distribution
        story.append(Paragraph("Frequency Distribution:", styles['Heading2']))
        freq_data = [[freq, count] for freq, count in report_data['frequency_distribution'].items()]
        if freq_data:
            freq_table = Table([['Frequency', 'Count']] + freq_data)
            freq_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(freq_table)
        story.append(Paragraph("<br/><br/>", styles['Normal']))

        # Scholarships Details
        story.append(Paragraph("Scholarship Details:", styles['Heading2']))
        for scholarship in report_data['scholarships']:
            # Scholarship Header
            story.append(Paragraph(f"<br/>{scholarship['name']}", styles['Heading3']))
            story.append(Paragraph(f"Amount: ${scholarship['amount']:,.2f}", styles['Normal']))
            story.append(Paragraph(f"Deadline: {scholarship['deadline']}", styles['Normal']))
            story.append(Paragraph(f"Frequency: {scholarship['frequency']}", styles['Normal']))
            
            # Description
            story.append(Paragraph("Description:", styles['Heading4']))
            story.append(Paragraph(scholarship['description'], styles['Normal']))
            
            # Eligibility Criteria
            story.append(Paragraph("Eligibility Criteria:", styles['Heading4']))
            for criterion in scholarship['eligibility']:
                story.append(Paragraph(f"• {criterion}", styles['Normal']))
                
            # Requirements
            story.append(Paragraph("Disbursement Requirements:", styles['Heading4']))
            for req in scholarship['requirements']:
                story.append(Paragraph(f"• {req}", styles['Normal']))
            
            story.append(Paragraph("<br/>", styles['Normal']))

        doc.build(story)
        return output_path

    def export_to_excel(self, output_path: str, filters=None) -> str:
        """Export scholarships data to Excel format."""
        report_data = self.generate_scholarship_report(filters)
        
        wb = Workbook()
        
        # Summary Sheet
        ws_summary = wb.active
        ws_summary.title = "Summary"
        ws_summary['A1'] = "Scholarship Report Summary"
        ws_summary['A2'] = "Generated on:"
        ws_summary['B2'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ws_summary['A3'] = "Total Scholarships:"
        ws_summary['B3'] = report_data['total_scholarships']
        ws_summary['A4'] = "Total Amount:"
        ws_summary['B4'] = f"${report_data['total_amount']:,.2f}"
        
        # Frequency Distribution
        ws_summary['A6'] = "Frequency Distribution"
        ws_summary['A7'] = "Frequency"
        ws_summary['B7'] = "Count"
        row = 8
        for freq, count in report_data['frequency_distribution'].items():
            ws_summary[f'A{row}'] = freq
            ws_summary[f'B{row}'] = count
            row += 1
            
        # Scholarships Sheet
        ws_details = wb.create_sheet("Scholarship Details")
        headers = ['Name', 'Amount', 'Deadline', 'Frequency', 'Description']
        for col, header in enumerate(headers, 1):
            cell = ws_details.cell(row=1, column=col)
            cell.value = header
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="CCCCCC", end_color="CCCCCC", fill_type="solid")
            
        for row, scholarship in enumerate(report_data['scholarships'], 2):
            ws_details.cell(row=row, column=1, value=scholarship['name'])
            ws_details.cell(row=row, column=2, value=f"${scholarship['amount']:,.2f}")
            ws_details.cell(row=row, column=3, value=scholarship['deadline'])
            ws_details.cell(row=row, column=4, value=scholarship['frequency'])
            ws_details.cell(row=row, column=5, value=scholarship['description'])

        # Adjust column widths
        for ws in [ws_summary, ws_details]:
            for col in ws.columns:
                max_length = 0
                for cell in col:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                ws.column_dimensions[chr(64 + col[0].column)].width = min(max_length + 2, 50)

        wb.save(output_path)
        return output_path

    def export_to_csv(self, output_path: str, filters=None) -> str:
        """Export scholarships data to CSV format."""
        report_data = self.generate_scholarship_report(filters)
        
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write summary
            writer.writerow(['Scholarship Report Summary'])
            writer.writerow(['Generated on:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
            writer.writerow(['Total Scholarships:', report_data['total_scholarships']])
            writer.writerow(['Total Amount:', f"${report_data['total_amount']:,.2f}"])
            writer.writerow([])
            
            # Write frequency distribution
            writer.writerow(['Frequency Distribution'])
            writer.writerow(['Frequency', 'Count'])
            for freq, count in report_data['frequency_distribution'].items():
                writer.writerow([freq, count])
            writer.writerow([])
            
            # Write scholarship details
            writer.writerow(['Scholarship Details'])
            writer.writerow(['Name', 'Amount', 'Deadline', 'Frequency', 'Description', 
                           'Eligibility Criteria', 'Requirements'])
            
            for scholarship in report_data['scholarships']:
                writer.writerow([
                    scholarship['name'],
                    f"${scholarship['amount']:,.2f}",
                    scholarship['deadline'],
                    scholarship['frequency'],
                    scholarship['description'],
                    '; '.join(scholarship['eligibility']),
                    '; '.join(scholarship['requirements'])
                ])
        
        return output_path

    def export_applicant_report_to_pdf(self, student_id: str = None, netid: str = None, output_path: str = None) -> str:
        """Export applicant report to PDF format."""
        report_data = self.generate_applicant_report(student_id, netid)
        if not report_data:
            raise ValueError("Applicant not found")

        doc = SimpleDocTemplate(output_path, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()

        # Title
        story.append(Paragraph(f"Applicant Report: {report_data['personal_info']['name']}", styles['Heading1']))
        story.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
        story.append(Paragraph("<br/>", styles['Normal']))

        # Personal and Academic Information
        story.append(Paragraph("Personal Information", styles['Heading2']))
        personal_info = [
            ['Student ID:', report_data['personal_info']['student_id']],
            ['NetID:', report_data['personal_info']['netid']],
            ['Major:', report_data['academic_info']['major']],
            ['Minor:', report_data['academic_info']['minor'] or 'N/A'],
            ['GPA:', f"{report_data['academic_info']['gpa']:.2f}"],
            ['Academic Level:', report_data['academic_info']['academic_level']],
            ['Expected Graduation:', report_data['academic_info']['expected_graduation'].strftime('%Y-%m-%d')]
        ]
        info_table = Table(personal_info)
        info_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (0, -1), colors.grey),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke)
        ]))
        story.append(info_table)
        story.append(Paragraph("<br/>", styles['Normal']))

        # Academic Achievements
        story.append(Paragraph("Academic Achievements", styles['Heading2']))
        for achievement in report_data['achievements']:
            story.append(Paragraph(
                f"• {achievement['type']} - {achievement['date'].strftime('%Y-%m-%d')}",
                styles['Normal']
            ))
            if 'description' in achievement:
                story.append(Paragraph(f"  {achievement['description']}", styles['Normal']))
        story.append(Paragraph("<br/>", styles['Normal']))

        # Financial Information
        story.append(Paragraph("Financial Information", styles['Heading2']))
        financial_info = report_data['financial_info']
        story.append(Paragraph(f"FAFSA Submitted: {financial_info['fafsa_submitted']}", styles['Normal']))
        story.append(Paragraph(f"Expected Family Contribution: ${financial_info['efc']:,}", styles['Normal']))
        story.append(Paragraph(f"Household Income Range: {financial_info['household_income']}", styles['Normal']))
        story.append(Paragraph("<br/>", styles['Normal']))

        # Current Aid
        if financial_info['current_aid']:
            story.append(Paragraph("Current Financial Aid:", styles['Heading3']))
            for aid in financial_info['current_aid']:
                story.append(Paragraph(f"• {aid['type']}: ${aid['amount']:,}", styles['Normal']))
        story.append(Paragraph("<br/>", styles['Normal']))

        # Scholarship Awards
        story.append(Paragraph("Scholarship Awards", styles['Heading2']))
        story.append(Paragraph(
            f"Total Awards: {report_data['scholarships']['total_awards']} "
            f"(${report_data['scholarships']['total_amount']:,})",
            styles['Normal']
        ))

        for award in report_data['scholarships']['detailed_awards']:
            story.append(Paragraph(f"Award: {award['scholarship_name']}", styles['Heading3']))
            story.append(Paragraph(f"Amount: ${award['award_amount']:,}", styles['Normal']))
            story.append(Paragraph(f"Status: {award['status']}", styles['Normal']))
            story.append(Paragraph(f"Award Date: {award['award_date'].strftime('%Y-%m-%d')}", styles['Normal']))
            
            if award['essays_evaluation']:
                story.append(Paragraph("Essay Evaluations:", styles['Heading4']))
                for eval in award['essays_evaluation']:
                    story.append(Paragraph(
                        f"• {eval['prompt']}: Score {eval['score']}/10 - {eval['feedback']}",
                        styles['Normal']
                    ))

            if award['committee_feedback']:
                story.append(Paragraph("Committee Feedback:", styles['Heading4']))
                for feedback in award['committee_feedback']:
                    story.append(Paragraph(
                        f"• {feedback['member']}: {feedback['comments']}",
                        styles['Normal']
                    ))
            story.append(Paragraph("<br/>", styles['Normal']))

        doc.build(story)
        return output_path

    def export_applicant_report_to_excel(self, student_id: str = None, netid: str = None, output_path: str = None) -> str:
        """Export applicant report to Excel format."""
        report_data = self.generate_applicant_report(student_id, netid)
        if not report_data:
            raise ValueError("Applicant not found")

        wb = Workbook()
        
        # Personal Information Sheet
        ws_personal = wb.active
        ws_personal.title = "Personal Information"
        
        personal_info = [
            ['Student Name', report_data['personal_info']['name']],
            ['Student ID', report_data['personal_info']['student_id']],
            ['NetID', report_data['personal_info']['netid']],
            ['Major', report_data['academic_info']['major']],
            ['Minor', report_data['academic_info']['minor'] or 'N/A'],
            ['GPA', f"{report_data['academic_info']['gpa']:.2f}"],
            ['Academic Level', report_data['academic_info']['academic_level']],
            ['Expected Graduation', report_data['academic_info']['expected_graduation'].strftime('%Y-%m-%d')]
        ]
        
        for row_idx, row in enumerate(personal_info, 1):
            for col_idx, value in enumerate(row, 1):
                cell = ws_personal.cell(row=row_idx, column=col_idx, value=value)
                if col_idx == 1:
                    cell.font = Font(bold=True)
        
        # Academic History Sheet
        ws_academic = wb.create_sheet("Academic History")
        headers = ['Term', 'Course Code', 'Course Name', 'Grade']
        for col, header in enumerate(headers, 1):
            cell = ws_academic.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="CCCCCC", end_color="CCCCCC", fill_type="solid")
        
        row = 2
        for term in report_data['academic_info']['academic_history']:
            for course in term['courses']:
                ws_academic.cell(row=row, column=1, value=term['term'])
                ws_academic.cell(row=row, column=2, value=course['code'])
                ws_academic.cell(row=row, column=3, value=course['name'])
                ws_academic.cell(row=row, column=4, value=course['grade'])
                row += 1
        
        # Scholarships Sheet
        ws_scholarships = wb.create_sheet("Scholarships")
        scholarship_headers = ['Scholarship Name', 'Amount', 'Status', 'Award Date']
        for col, header in enumerate(scholarship_headers, 1):
            cell = ws_scholarships.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="CCCCCC", end_color="CCCCCC", fill_type="solid")
        
        for row, award in enumerate(report_data['scholarships']['detailed_awards'], 2):
            ws_scholarships.cell(row=row, column=1, value=award['scholarship_name'])
            ws_scholarships.cell(row=row, column=2, value=f"${award['award_amount']:,}")
            ws_scholarships.cell(row=row, column=3, value=award['status'])
            ws_scholarships.cell(row=row, column=4, value=award['award_date'].strftime('%Y-%m-%d'))

        # Adjust column widths
        for ws in [ws_personal, ws_academic, ws_scholarships]:
            for col in ws.columns:
                max_length = 0
                for cell in col:
                    try:
                        max_length = max(max_length, len(str(cell.value)))
                    except:
                        pass
                ws.column_dimensions[chr(64 + col[0].column)].width = min(max_length + 2, 50)

        wb.save(output_path)
        return output_path


# View to handle report generation and exporting
def home(request):
    # Create sample scholarship data (inline)
    # Create sample applicant data with comprehensive review information
    john_doe = ApplicantData(
        name="John Doe",
        student_id="12345678",
        netid="jdoe",
        major="Systems Engineering",
        minor="Computer Science",
        academic_achievements=[
            {
                'type': 'Dean\'s List',
                'date': datetime(2024, 12, 15),
                'description': 'Fall 2024 Semester'
            },
            {
                'type': 'Research Publication',
                'date': datetime(2025, 3, 1),
                'title': 'Innovation in Systems Design',
                'journal': 'Engineering Research Quarterly'
            }
        ],
        financial_info={
            'fafsa_submitted': True,
            'efc': 5000,
            'household_income': '50000-75000',
            'current_aid': [
                {'type': 'Federal Grant', 'amount': 2500},
                {'type': 'State Grant', 'amount': 1500}
            ]
        },
        essays=[
            {
                'prompt': 'Describe your career goals in engineering.',
                'content': 'My passion for systems engineering stems from...',
                'submission_date': datetime(2025, 2, 1),
                'evaluation': {
                    'score': 9.2,
                    'feedback': 'Excellent vision and clear career trajectory.',
                    'reviewer': 'Dr. Sarah Chen',
                    'date': datetime(2025, 2, 15)
                }
            },
            {
                'prompt': 'How will this scholarship impact your education?',
                'content': 'This scholarship will enable me to...',
                'submission_date': datetime(2025, 2, 1),
                'evaluation': {
                    'score': 8.8,
                    'feedback': 'Strong understanding of opportunity and impact.',
                    'reviewer': 'Prof. Michael Roberts',
                    'date': datetime(2025, 2, 16)
                }
            }
        ],
        gpa=3.8,
        academic_level="Junior",
        expected_graduation=datetime(2027, 5, 15),
        academic_history=[
            {
                'term': 'Fall 2024',
                'courses': [
                    {'code': 'SYE301', 'name': 'Systems Engineering Fundamentals', 'grade': 'A'},
                    {'code': 'CS210', 'name': 'Software Systems', 'grade': 'A-'}
                ],
                'gpa': 3.85
            }
        ],
        interview_notes="Conducted on 2025-03-01. Demonstrated strong leadership potential and excellent communication skills. Shows clear understanding of systems engineering principles.",
        committee_feedback=[
            {
                'member': 'Dr. James Wilson',
                'role': 'Department Chair',
                'comments': 'Outstanding candidate with proven academic excellence.',
                'recommendation': 'Highly Recommend',
                'date': datetime(2025, 3, 5)
            },
            {
                'member': 'Prof. Lisa Martinez',
                'role': 'Scholarship Committee Head',
                'comments': 'Strong technical background and leadership potential.',
                'recommendation': 'Strongly Recommend',
                'date': datetime(2025, 3, 6)
            }
        ]
    )

    sample_scholarships = [
        Scholarship(
            name="Engineering Excellence Scholarship",
            description="Merit-based scholarship for outstanding engineering students",
            eligibility_criteria=[
                "3.5+ GPA",
                "Engineering major",
                "Full-time enrollment"
            ],
            donor_info={
                'name': 'Engineering Industry Association',
                'contact': 'donor@example.com'
            },
            disbursement_requirements=[
                "Maintain 3.5 GPA",
                "Submit semester progress report"
            ],
            frequency="annual",
            amount=5000.00,
            deadline=datetime(2026, 3, 15),
            review_dates=[
                datetime(2026, 1, 15),  # Mid-year review
                datetime(2026, 6, 15)   # End-year review
            ],
            reporting_schedule={
                'Progress Report': datetime(2026, 4, 15),
                'Financial Report': datetime(2026, 7, 15)
            },
            awards=[
                ScholarshipAward(
                    scholarship_name="Engineering Excellence Scholarship",
                    applicant=john_doe,  # Using the detailed ApplicantData
                    award_date=datetime(2025, 8, 15),
                    award_amount=5000.00,
                    disbursement_dates=[
                        datetime(2025, 9, 1),
                        datetime(2026, 1, 1)
                    ],
                    requirements_met=[
                        "Enrollment verification",
                        "First semester GPA requirement"
                    ],
                    requirements_pending=[
                        "Second semester progress report",
                        "Community service hours"
                    ],
                    status="active",
                    performance_metrics={
                        'current_gpa': 3.8,
                        'credits_completed': 15,
                        'service_hours': 20
                    },
                    essays_evaluation=[
                        {
                            'prompt': 'Career Goals',
                            'score': 9,
                            'feedback': 'Excellent clarity and vision'
                        },
                        {
                            'prompt': 'Impact',
                            'score': 8,
                            'feedback': 'Strong understanding of opportunity'
                        }
                    ],
                    interview_notes="Strong candidate with clear goals and excellent communication skills",
                    committee_feedback=[
                        {'member': 'Dr. Smith', 'comments': 'Highly recommended'},
                        {'member': 'Prof. Johnson', 'comments': 'Outstanding potential'}
                    ]
                )
            ]
        ),
        Scholarship(
            name="CS Leadership Scholarship",
            description="For computer science students demonstrating leadership",
            eligibility_criteria=[
                "3.0+ GPA",
                "Computer Science major",
                "Leadership role in student organization"
            ],
            donor_info={
                'name': 'Tech Leaders Foundation',
                'contact': 'foundation@techleaders.org'
            },
            disbursement_requirements=[
                "Maintain leadership position",
                "Submit leadership impact report"
            ],
            frequency="semester",
            amount=3000.00,
            deadline=datetime(2026, 2, 1)
        )
    ]

    # Initialize engine and add sample data
    engine = ReportEngine()
    for scholarship in sample_scholarships:
        engine.add_scholarship(scholarship)
    
    if request.method == 'POST':
        export_format = request.POST.get('export_format')
        report_type = request.POST.get('report_type', 'general')  # 'general' or 'donor'
        donor_name = request.POST.get('donor_name')

        if export_format:
            temp_file = None
            try:
                # Create temporary file with appropriate extension
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f'.{export_format}')
                temp_file.close()  # Close the file handle immediately

                if report_type == 'donor' and donor_name:
                    # Generate donor-specific report
                    if export_format == 'pdf':
                        output_path = engine.export_donor_report_to_pdf(
                            donor_name=donor_name,
                            output_path=temp_file.name
                        )
                        content_type = 'application/pdf'
                    elif export_format == 'xlsx':
                        output_path = engine.export_donor_report_to_excel(
                            donor_name=donor_name,
                            output_path=temp_file.name
                        )
                        content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                    elif export_format == 'csv':
                        output_path = engine.export_donor_report_to_csv(
                            donor_name=donor_name,
                            output_path=temp_file.name
                        )
                        content_type = 'text/csv'
                    else:
                        raise ValueError(f"Unsupported export format for donor report: {export_format}")
                    filename = f'donor_report.{export_format}'
                elif report_type == 'applicant':
                    # Use sample student_id for demo purposes (in real app, this would come from form input)
                    student_id = "12345678"
                    if export_format == 'pdf':
                        output_path = engine.export_applicant_report_to_pdf(
                            student_id=student_id,
                            output_path=temp_file.name
                        )
                        content_type = 'application/pdf'
                    elif export_format == 'xlsx':
                        output_path = engine.export_applicant_report_to_excel(
                            student_id=student_id,
                            output_path=temp_file.name
                        )
                        content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                    elif export_format == 'csv':
                        output_path = engine.export_to_csv(temp_file.name)  # Using general CSV export for now
                        content_type = 'text/csv'
                    else:
                        raise ValueError(f"Unsupported export format for applicant report: {export_format}")
                    filename = f'applicant_report.{export_format}'
                elif report_type == 'prescreening':
                    # For demo purposes, we'll create a list of sample applicants with varying completion levels
                    sample_applicants = [
                        ApplicantData(
                            name="Alice Smith",
                            student_id="12346789",
                            netid="asmith",
                            major="Engineering",
                            minor="Mathematics",
                            gpa=3.8,
                            academic_level="Junior",
                            expected_graduation=datetime(2027, 5, 15),
                            academic_history=[{
                                'term': 'Fall 2024',
                                'courses': [
                                    {'code': 'ENG301', 'name': 'Advanced Engineering', 'grade': 'A'},
                                    {'code': 'MATH400', 'name': 'Applied Mathematics', 'grade': 'A-'}
                                ],
                                'gpa': 3.8
                            }],
                            essays=[{
                                'prompt': 'Describe your research interests.',
                                'content': 'My research focuses on sustainable engineering...',
                                'submission_date': datetime(2025, 2, 1),
                                'evaluation': {
                                    'score': 9.5,
                                    'feedback': 'Exceptional research vision and clarity.',
                                    'reviewer': 'Dr. Thompson',
                                    'date': datetime(2025, 2, 10)
                                }
                            }],
                            financial_info={
                                'fafsa_submitted': True,
                                'efc': 4000,
                                'household_income': '40000-60000'
                            },
                            interview_notes="Outstanding interview performance. Shows great potential.",
                            committee_feedback=[{
                                'member': 'Dr. Rodriguez',
                                'comments': 'Top candidate with excellent credentials.',
                                'recommendation': 'Highly Recommend',
                                'date': datetime(2025, 3, 1)
                            }]
                        ),
                        ApplicantData(
                            name="Bob Johnson",
                            student_id="12347890",
                            netid="bjohnson",
                            major="Computer Science",
                            gpa=3.2,
                            academic_level="Sophomore",
                            essays=[{
                                'prompt': 'Describe your programming experience.',
                                'content': 'I have developed several applications...',
                                'submission_date': datetime(2025, 2, 2),
                                'evaluation': {
                                    'score': 7.8,
                                    'feedback': 'Good technical background, needs more detail.',
                                    'reviewer': 'Prof. Chen',
                                    'date': datetime(2025, 2, 12)
                                }
                            }],
                            financial_info={
                                'fafsa_submitted': True,
                                'efc': 6000,
                                'household_income': '60000-80000'
                            }
                            # Intentionally incomplete application
                        ),
                        ApplicantData(
                            name="Carol Williams",
                            student_id="12348901",
                            netid="cwilliams",
                            major="Engineering",
                            gpa=3.6,
                            academic_level="Senior",
                            expected_graduation=datetime(2026, 5, 15),
                            academic_history=[{
                                'term': 'Fall 2024',
                                'courses': [
                                    {'code': 'ENG401', 'name': 'Engineering Design', 'grade': 'A'},
                                    {'code': 'ENG402', 'name': 'Project Management', 'grade': 'B+'}
                                ],
                                'gpa': 3.6
                            }],
                            essays=[{
                                'prompt': 'Describe your leadership experience.',
                                'content': 'As president of the Engineering Club...',
                                'submission_date': datetime(2025, 2, 3),
                                'evaluation': {
                                    'score': 8.9,
                                    'feedback': 'Strong leadership qualities demonstrated.',
                                    'reviewer': 'Dr. Martinez',
                                    'date': datetime(2025, 2, 14)
                                }
                            }],
                            financial_info={
                                'fafsa_submitted': True,
                                'efc': 3000,
                                'household_income': '30000-50000'
                            },
                            interview_notes="Great communication skills and project experience.",
                            committee_feedback=[{
                                'member': 'Prof. Anderson',
                                'comments': 'Strong candidate with practical experience.',
                                'recommendation': 'Recommend',
                                'date': datetime(2025, 3, 2)
                            }]
                        )
                    ]
                    
                    if export_format == 'pdf':
                        output_path = engine.export_prescreening_report_to_pdf(
                            applicants=sample_applicants,
                            output_path=temp_file.name
                        )
                        content_type = 'application/pdf'
                    elif export_format == 'xlsx':
                        output_path = engine.export_prescreening_report_to_excel(
                            applicants=sample_applicants,
                            output_path=temp_file.name
                        )
                        content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                    elif export_format == 'csv':
                        output_path = engine.export_prescreening_report_to_csv(
                            applicants=sample_applicants,
                            output_path=temp_file.name
                        )
                        content_type = 'text/csv'
                    else:
                        raise ValueError(f"Unsupported export format for pre-screening report: {export_format}")
                    filename = f'prescreening_report.{export_format}'
                else:
                    # Generate general scholarship report
                    if export_format == 'pdf':
                        output_path = engine.export_to_pdf(temp_file.name)
                        content_type = 'application/pdf'
                    elif export_format == 'xlsx':
                        output_path = engine.export_to_excel(temp_file.name)
                        content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                    elif export_format == 'csv':
                        output_path = engine.export_to_csv(temp_file.name)
                        content_type = 'text/csv'
                    else:
                        raise ValueError(f"Unsupported export format: {export_format}")
                    filename = f'scholarship_report.{export_format}'

                # Read the file and create the response
                with open(output_path, 'rb') as f:
                    response = HttpResponse(f.read(), content_type=content_type)
                    response['Content-Disposition'] = f'attachment; filename="{filename}"'
                return response

            except Exception as e:
                # Log the error (you might want to use proper logging here)
                print(f"Error during export: {str(e)}")
                return HttpResponse(f"Error generating report: {str(e)}", status=500)

            finally:
                # Clean up temporary file in finally block to ensure it happens
                try:
                    if temp_file:
                        os.unlink(temp_file.name)
                except Exception as e:
                    print(f"Error cleaning up temporary file: {str(e)}")
    
    # Generate report for web display
    report_data = engine.generate_scholarship_report()
    
    # Convert scholarships data for template display
    for scholarship in report_data['scholarships']:
        # Ensure donor info is in the expected format
        if isinstance(scholarship.get('donor'), dict):
            scholarship['donor'] = scholarship['donor']
        else:
            scholarship['donor'] = {'name': 'Unknown', 'contact': 'Not provided'}
    
    return render(request, 'reports_app/index.html', {'report': report_data})
