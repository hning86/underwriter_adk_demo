# scripts/add_mock_client.py
import os
import sys
import time
from dotenv import load_dotenv
from google.cloud import bigquery
from google.cloud import discoveryengine_v1 as discoveryengine
from google.api_core.exceptions import Conflict, AlreadyExists

# ReportLab imports for PDF generation
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

load_dotenv()

# --- 1. MOCK CLIENT METADATA ---
NEW_CLIENT = {
    "client_id": "oceana",
    "name": "Oceana Maritime Logistics",
    "industry": "Shipping & Maritime",
    "company_size": 450,
    "annual_revenue": 125000000,
    "headquarters": "Seattle, WA",
    "years_in_business": 28,
    "primary_operations": "Ocean Freight & Port Logistics",
    "number_of_facilities": 5,
    "safety_rating_class": "Average"
}

LOSS_RUNS_DATA = {
    "narrative": "Oceana Maritime Logistics operates a fleet of 15 cargo vessels alongside port logistics operations in Seattle and Oakland. Overall claims experience has been average for the specialized maritime logistics sector. There are notable frequency patterns surrounding terminal equipment damage (cranes/forklifts) and sporadic high-severity bodily injury claims involving longshoremen over the past 3 policy periods. Weather-related hull claims remain below the industry baseline, indicating proactive storm avoidance and mature vessel maintenance protocols.",
    "claims_history": [
        {
            "policy_period": "2023-2024",
            "date_of_loss": "2023-11-12",
            "type": "Bodily Injury (Workers Comp)",
            "description": "Longshoreman suffered severe crush fracture to left leg during container offloading operations when a spreader bar swung unexpectedly due to high winds at Port of Seattle.",
            "paid": "$45,000",
            "reserves": "$150,000",
            "status": "Open"
        },
        {
            "policy_period": "2023-2024",
            "date_of_loss": "2024-02-05",
            "type": "Property Damage (Equipment)",
            "description": "Forklift collided with stationary reefer container during night operations; minor damage to container cooling unit, minimal cargo spoilage.",
            "paid": "$12,400",
            "reserves": "$0",
            "status": "Closed"
        },
        {
            "policy_period": "2022-2023",
            "date_of_loss": "2022-09-18",
            "type": "Hull & Machinery",
            "description": "Vessel 'Oceana Star' grazed concrete pier during heavy fog docking in Oakland. Superficial scraping requiring repainting. No structural steel damage.",
            "paid": "$28,500",
            "reserves": "$0",
            "status": "Closed"
        },
        {
            "policy_period": "2021-2022",
            "date_of_loss": "2021-12-03",
            "type": "Bodily Injury",
            "description": "Slip and fall on rain-slicked decking by 3rd party marine surveyor. Sustained broken collarbone.",
            "paid": "$65,000",
            "reserves": "$0",
            "status": "Closed"
        }
    ]
}

def inject_bigquery():
    print(f"\n--- 1. Injecting Structured Data to BigQuery ---")
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "ninghai-ccai")
    location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
    client = bigquery.Client(project=project_id, location=location)
    
    table_id = f"{project_id}.underwriter_demo.client_profiles"
    
    # We will attempt to insert the new row securely
    # Note: BQ insert_rows_json does not throw on duplicates natively unless strictly modeled.
    errors = client.insert_rows_json(table_id, [NEW_CLIENT])
    if not errors:
        print(f"✅ Successfully added '{NEW_CLIENT['name']}' to BigQuery dataset: {table_id}")
    else:
        print(f"⚠️ Encountered errors inserting into BQ: {errors}")


def generate_pdf() -> str:
    print(f"\n--- 2. Generating Professional Loss Run Report (PDF) ---")
    out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'reports'))
    os.makedirs(out_dir, exist_ok=True)
    
    client_id = NEW_CLIENT["client_id"]
    client_name = NEW_CLIENT["name"]
    industry = NEW_CLIENT["industry"]
    file_path = os.path.join(out_dir, f"{client_id}_loss_runs.pdf")
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        name='TitleStyle', parent=styles['Heading1'], fontSize=18,
        spaceAfter=10, textColor=colors.HexColor("#1A202C")
    )
    subtitle_style = ParagraphStyle(
        name='SubtitleStyle', parent=styles['Normal'], fontSize=11,
        spaceAfter=20, textColor=colors.HexColor("#4A5568")
    )
    table_cell_style = ParagraphStyle(
        name='TableCell', parent=styles['Normal'], fontSize=9, leading=12
    )

    doc = SimpleDocTemplate(file_path, pagesize=landscape(letter), rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []

    elements.append(Paragraph(f"Official Loss Run Report: {client_name}", title_style))
    elements.append(Paragraph(f"<b>Client ID:</b> {client_id.upper()} | <b>Industry:</b> {industry}", subtitle_style))
    
    elements.append(Paragraph("<b>Background Narrative:</b>", styles['Heading3']))
    elements.append(Paragraph(LOSS_RUNS_DATA["narrative"], styles['Normal']))
    elements.append(Spacer(1, 20))

    table_data = [["Policy Period", "Date of Loss", "Type", "Description / Incident", "Paid", "Reserves", "Status"]]
    
    for claim in LOSS_RUNS_DATA["claims_history"]:
        desc_p = Paragraph(claim["description"], table_cell_style)
        table_data.append([
            claim["policy_period"], claim["date_of_loss"], claim["type"],
            desc_p, claim["paid"], claim["reserves"], claim["status"]
        ])

    col_widths = [80, 75, 90, 270, 70, 70, 60]
    t = Table(table_data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2D3748")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#F7FAFC")),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor("#E2E8F0")),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 10),
    ]))

    elements.append(Paragraph("<b>Claims History:</b>", styles['Heading3']))
    elements.append(t)
    
    doc.build(elements)
    print(f"✅ Generated Tabular PDF: {file_path}")
    return file_path

def upload_to_vertex_search(pdf_path: str):
    print(f"\n--- 3. Uploading unstructured PDF to Vertex AI Search ---")
    project_id = os.environ.get('GOOGLE_CLOUD_PROJECT', 'ninghai-ccai')
    location = "global"
    ds_id = "underwriter-loss-runs"
    client_id = NEW_CLIENT["client_id"]
    
    doc_client = discoveryengine.DocumentServiceClient()
    parent_ds = f"projects/{project_id}/locations/{location}/collections/default_collection/dataStores/{ds_id}"
    
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    doc = discoveryengine.Document(
        id=client_id,
        struct_data={
            "title": f"{NEW_CLIENT['name']} Loss Runs Report",
            "client_id": client_id,
            "document_type": "loss_runs"
        },
        content=discoveryengine.Document.Content(
            mime_type="application/pdf",
            raw_bytes=pdf_bytes
        )
    )
    
    request = discoveryengine.CreateDocumentRequest(
        parent=f"{parent_ds}/branches/0",
        document=doc,
        document_id=client_id
    )
    
    try:
        doc_client.delete_document(name=f"{parent_ds}/branches/0/documents/{client_id}")
        print(f"ℹ️ Purged old document for {client_id} to reseed.")
    except Exception:
        pass
        
    try:
        doc_client.create_document(request=request)
        print(f"✅ Successfully ingested '{client_id}_loss_runs.pdf' into Vertex AI Datastore.")
    except AlreadyExists:
        print(f"⚠️ Document {client_id} already exists. Skipping upload.")
    except Exception as e:
        print(f"❌ Failed to upload {client_id}: {e}")

def display_next_steps():
    print("\n=========================================================")
    print("🚀 Mock Client Data Provisioning Complete!")
    print("=========================================================")
    print("1. BigQuery has been seeded with structured profile details.")
    print("2. The Unstructured PDF was generated in your local `./reports` directory.")
    print("3. Vertex AI Search is now indexing the document.")
    print("\n⚠️ IMPORTANT NEXT STEP:")
    print("Because the PDF is locally built, you must redeploy your FastAPI container")
    print("so the Cloud Run UI can statically serve the file over HTTPS.")
    print("\nPlease run the following command in your terminal:")
    print("export CLOUDSDK_PYTHON=\"$(pwd)/.venv/bin/python\" && ./deploy_webapp.sh")
    print("=========================================================\n")

if __name__ == "__main__":
    print(f"Provisioning Mock Client: {NEW_CLIENT['name']}...\n")
    inject_bigquery()
    generated_pdf_path = generate_pdf()
    upload_to_vertex_search(generated_pdf_path)
    display_next_steps()
