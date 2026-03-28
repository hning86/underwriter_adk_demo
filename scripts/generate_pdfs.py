import sys
import os
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# Import the mock data dynamically
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.underwriter_agent.agent import MOCK_CLIENTS

def generate():
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "./reports"
    os.makedirs(out_dir, exist_ok=True)
    styles = getSampleStyleSheet()

    # Create custom styles
    title_style = ParagraphStyle(
        name='TitleStyle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=10,
        textColor=colors.HexColor("#1A202C")
    )
    
    subtitle_style = ParagraphStyle(
        name='SubtitleStyle',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=20,
        textColor=colors.HexColor("#4A5568")
    )
    
    table_cell_style = ParagraphStyle(
        name='TableCell',
        parent=styles['Normal'],
        fontSize=9,
        leading=12
    )

    for client_id, client_data in MOCK_CLIENTS.items():
        file_path = os.path.join(out_dir, f"{client_id}_loss_runs.pdf")
        
        # We use landscape to fit wide tables
        doc = SimpleDocTemplate(file_path, pagesize=landscape(letter), rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
        elements = []

        # Header Section
        elements.append(Paragraph(f"Official Loss Run Report: {client_data['name']}", title_style))
        elements.append(Paragraph(f"<b>Client ID:</b> {client_id.upper()} | <b>Industry:</b> {client_data['industry']}", subtitle_style))
        
        # Background Section
        elements.append(Paragraph("<b>Background Narrative:</b>", styles['Heading3']))
        elements.append(Paragraph(client_data["loss_runs"]["narrative"], styles['Normal']))
        elements.append(Spacer(1, 20))

        # Table Header Data
        table_data = [["Policy Period", "Date of Loss", "Type", "Description / Incident", "Paid", "Reserves", "Status"]]
        
        # Populate Table Rows
        for claim in client_data["loss_runs"]["claims_history"]:
            # Wrap description in a paragraph so it word-wraps cleanly within the cell
            desc_p = Paragraph(claim["description"], table_cell_style)
            
            table_data.append([
                claim["policy_period"],
                claim["date_of_loss"],
                claim["type"],
                desc_p,
                claim["paid"],
                claim["reserves"],
                claim["status"]
            ])

        # Define column widths for Landscape layout (Total ~732 points)
        col_widths = [80, 75, 90, 270, 70, 70, 60]
        t = Table(table_data, colWidths=col_widths)
        
        # Apply strict professional styling
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2D3748")),       # Header Background
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),                 # Header Text
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),                               # Left Align All
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),                   # Font Header
            ('FONTSIZE', (0, 0), (-1, 0), 10),                                 # Font Size Header
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),                             # Header Padding
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#F7FAFC")),      # Alternating row color base
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor("#E2E8F0")),         # Light border
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),                               # Top Align text
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 10),
            ('TOPPADDING', (0, 1), (-1, -1), 10),
        ]))

        elements.append(Paragraph("<b>Claims History:</b>", styles['Heading3']))
        elements.append(t)
        
        # Render the PDF to disk
        doc.build(elements)
        print(f"Generated Tabular PDF: {file_path}")

if __name__ == "__main__":
    generate()
