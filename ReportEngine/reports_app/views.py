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


class ReportEngine:
    """OOP Report Engine for generating scholarship reports and summaries."""

    def __init__(self):
        self.scholarships = []

    def add_scholarship(self, scholarship: Scholarship):
        """Add a new scholarship to the system."""
        self.scholarships.append(scholarship)

    def generate_scholarship_report(self, filters=None):
        """Generate a comprehensive report of scholarships.

        Args:
            filters (dict, optional): Filters to apply (e.g., {'frequency': 'annual'})

        Returns:
            dict: Report containing scholarship summaries and statistics
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

        return {
            'total_scholarships': len(scholarships_data),
            'total_amount': total_amount,
            'frequency_distribution': frequencies,
            'scholarships': scholarship_details
        }
        
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
            deadline=datetime(2026, 3, 15)
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
        if export_format:
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
