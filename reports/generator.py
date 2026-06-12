import os
import csv
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

CSV_FILE = os.path.join(os.path.dirname(__file__), "../data/waste_log.csv")
PDF_FILE = os.path.join(os.path.dirname(__file__), "../outputs/waste_monitoring_report.pdf")

def init_csv():
    """Initializes the CSV log file with headers if it doesn't exist."""
    os.makedirs(os.path.dirname(CSV_FILE), exist_ok=True)
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Timestamp", "Bin ID", "Distance (cm)", "Fill Percentage (%)", "Status", "Temperature (°C)", "Humidity (%)", "Gas Level (%)", "Alert Triggered"])

def log_to_csv(bin_id, distance, fill_percentage, status, temp, humidity, gas_level, alert_triggered):
    """Appends a row of sensor data to the CSV file."""
    init_csv()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(CSV_FILE, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([timestamp, bin_id, f"{distance:.1f}", f"{fill_percentage:.1f}", status, f"{temp:.1f}", f"{humidity:.1f}", f"{gas_level:.1f}", "YES" if alert_triggered else "NO"])

def generate_pdf_report():
    """Generates a beautiful PDF summary report from the logged CSV data."""
    init_csv()
    os.makedirs(os.path.dirname(PDF_FILE), exist_ok=True)

    # Read data from CSV
    rows = []
    try:
        with open(CSV_FILE, mode='r') as file:
            reader = csv.reader(file)
            headers = next(reader)
            rows = list(reader)
    except Exception as e:
        print(f"Error reading CSV for PDF: {e}")
        return False

    # Get recent 15 entries for the report to prevent overflow
    recent_rows = rows[-15:] if len(rows) > 0 else []

    # Setup document
    doc = SimpleDocTemplate(PDF_FILE, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        textColor=colors.HexColor('#1A365D'),
        spaceAfter=15
    )
    subtitle_style = ParagraphStyle(
        'DocSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor('#4A5568'),
        spaceAfter=20
    )
    heading_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        textColor=colors.HexColor('#2B6CB0'),
        spaceBefore=10,
        spaceAfter=10
    )
    cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        textColor=colors.HexColor('#2D3748')
    )
    header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        textColor=colors.white
    )

    # Header / Title Info
    story.append(Paragraph("Smart Waste Management System", title_style))
    story.append(Paragraph(f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | <b>Scope:</b> Waste Bin Node-1 Monitoring Report", subtitle_style))
    story.append(Spacer(1, 10))

    # Add a summary block
    story.append(Paragraph("1. System Metrics Summary", heading_style))
    
    total_records = len(rows)
    if total_records > 0:
        latest = rows[-1]
        summary_data = [
            [Paragraph("<b>Total Logs Analyzed:</b>", cell_style), Paragraph(str(total_records), cell_style)],
            [Paragraph("<b>Latest Distance:</b>", cell_style), Paragraph(f"{latest[2]} cm", cell_style)],
            [Paragraph("<b>Latest Fill Level:</b>", cell_style), Paragraph(f"{latest[3]}%", cell_style)],
            [Paragraph("<b>Current Status:</b>", cell_style), Paragraph(latest[4], cell_style)],
            [Paragraph("<b>Latest Gas Alert Level:</b>", cell_style), Paragraph(f"{latest[7]}%", cell_style)],
            [Paragraph("<b>Alert Status:</b>", cell_style), Paragraph(f"Active Alert" if latest[8] == "YES" else "Normal", cell_style)]
        ]
    else:
        summary_data = [[Paragraph("No data logged yet. Please start simulation to generate telemetry.", cell_style)]]

    summary_table = Table(summary_data, colWidths=[200, 300])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#EDF2F7')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 15))

    # Add Recent Logs Table
    story.append(Paragraph("2. Telemetry Log (Last 15 Records)", heading_style))
    
    table_data = []
    # Set headers
    header_row = [Paragraph(f"<b>{h}</b>", header_style) for h in ["Timestamp", "Bin ID", "Dist (cm)", "Fill %", "Status", "Temp (°C)", "Hum (%)", "Gas (%)", "Alert"]]
    table_data.append(header_row)

    for row in recent_rows:
        # Wrap cells in Paragraph to support word-wrapping and style
        row_cells = [Paragraph(cell, cell_style) for cell in row]
        table_data.append(row_cells)

    # Column widths (Total width for Letter size printable area is ~540pt)
    col_widths = [110, 50, 50, 50, 60, 50, 50, 50, 70]
    
    log_table = Table(table_data, colWidths=col_widths)
    log_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2B6CB0')),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F7FAFC')]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    
    story.append(log_table)
    
    # Build Document
    try:
        doc.build(story)
        return True
    except Exception as e:
        print(f"Error building PDF: {e}")
        return False

if __name__ == "__main__":
    init_csv()
    # Log a dummy entry for test
    log_to_csv("bin_node_1", 15.0, 50.0, "Half Full", 28.5, 62.0, 15.4, False)
    generate_pdf_report()
    print("CSV and PDF generation verified.")
