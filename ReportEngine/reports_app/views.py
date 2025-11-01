from django.shortcuts import render
from django.http import HttpResponse
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
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
class ScholarshipAward:
    """Data class representing a scholarship award to a specific applicant."""
    scholarship_name: str
    applicant_name: str
    award_date: datetime
    award_amount: float
    disbursement_dates: List[datetime]
    requirements_met: List[str]
    requirements_pending: List[str]
    status: str  # 'active', 'completed', 'revoked'
    performance_metrics: Dict[str, Any]  # GPA, participation, etc.
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


# View to handle report generation and exporting
def home(request):
    # Create sample scholarship data (inline)
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
                    applicant_name="John Doe",
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
                    }
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
                
                # Read the file and create the response
                with open(output_path, 'rb') as f:
                    response = HttpResponse(f.read(), content_type=content_type)
                    filename = 'donor_report.pdf' if report_type == 'donor' else f'scholarship_report.{export_format}'
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
            temp_file = None
            try:
                # Create temporary file with appropriate extension
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f'.{export_format}')
                temp_file.close()  # Close the file handle immediately

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

                # Read the file and create the response
                with open(output_path, 'rb') as f:
                    response = HttpResponse(f.read(), content_type=content_type)
                    response['Content-Disposition'] = f'attachment; filename="scholarship_report.{export_format}"'
                
                return response

            except Exception as e:
                # Log the error (you might want to use proper logging here)
                print(f"Error during export: {str(e)}")
                return HttpResponse(f"Error generating {export_format.upper()} report: {str(e)}", status=500)

            finally:
                # Clean up temporary file in finally block to ensure it happens
                try:
                    if temp_file:
                        os.unlink(temp_file.name)
                except Exception as e:
                    print(f"Error cleaning up temporary file: {str(e)}")
    
    # Generate report for web display
    report = engine.generate_scholarship_report()
    return render(request, 'reports_app/index.html', {'report': report})
