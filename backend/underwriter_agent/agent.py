import os
from dotenv import load_dotenv

# Load environment variables (pulls GOOGLE_API_KEY from .env)
load_dotenv()

from google.cloud import bigquery
bq_client = bigquery.Client(
    project=os.environ.get('GOOGLE_CLOUD_PROJECT', 'ninghai-ccai'),
    location=os.environ.get('GOOGLE_CLOUD_LOCATION', 'us-central1')
)

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models.google_llm import Gemini
from google.genai import types, Client

# Custom Gemini subclass to enable Vertex AI
class VertexGemini(Gemini):
    _cached_client: Client | None = None

    @property
    def api_client(self) -> Client:
        if self._cached_client is None:
            self._cached_client = Client(
                vertexai=True,
                project=os.environ.get('GOOGLE_CLOUD_PROJECT', 'ninghai-ccai'),
                location=os.environ.get('GOOGLE_CLOUD_LOCATION', 'us-central1'),
                http_options=types.HttpOptions(
                    headers=self._tracking_headers(),
                    retry_options=self.retry_options,
                    base_url=self.base_url,
                )
            )
        return self._cached_client

# Mock Database
MOCK_CLIENTS = {
    "acme": {
        "id": "acme",
        "loss_runs": {
            "narrative": "Acme Logistics operates a fleet of 50 delivery vehicles. Recent safety checks suggest maintenance logs are incomplete. Drivers reported overtime peaks during holiday seasons.",
            "claims_history": [
                {"policy_period": "2023-2024", "date_of_loss": "2023-11-15", "type": "Auto", "description": "Rear-end collision in warehouse yard.", "paid": "$12,000", "reserves": "$0", "status": "Closed"},
                {"policy_period": "2023-2024", "date_of_loss": "2024-01-05", "type": "Workers Comp", "description": "Slip and fall on ice in depot.", "paid": "$4,500", "reserves": "$0", "status": "Closed"},
                {"policy_period": "2022-2023", "date_of_loss": "2023-01-20", "type": "Cargo", "description": "Cargo damage claim (Winter storm ice event).", "paid": "$75,000", "reserves": "$0", "status": "Closed"},
                {"policy_period": "2021-2022", "date_of_loss": "2021-08-14", "type": "Auto", "description": "Rollover accident.", "paid": "$50,000", "reserves": "$15,000", "status": "Open"}
            ]
        }
    },
    "zenith": {
        "id": "zenith",
        "loss_runs": {
            "narrative": "Zenith has automated production lines. Safety metrics are above average, but shop floor ergonomics are a recurring complaint in worker surveys.",
            "claims_history": [
                {"policy_period": "2023-2024", "date_of_loss": "2023-10-09", "type": "Workers Comp", "description": "Minor hand injury on conveyor belt.", "paid": "$2,500", "reserves": "$0", "status": "Closed"},
                {"policy_period": "2022-2023", "date_of_loss": "2022-04-12", "type": "Workers Comp", "description": "Back strain from manual lifting.", "paid": "$8,000", "reserves": "$0", "status": "Closed"},
                {"policy_period": "2020-2021", "date_of_loss": "2021-03-24", "type": "Workers Comp", "description": "Machine malfunction injury (Settled).", "paid": "$120,000", "reserves": "$0", "status": "Closed"}
            ]
        }
    },
    "stella": {
        "id": "stella",
        "loss_runs": {
            "narrative": "Stellar Retail has rapid expansion. High turnover of warehouse staff. Stress reports during peak delivery windows.",
            "claims_history": [
                {"policy_period": "2023-2024", "date_of_loss": "2023-12-05", "type": "Auto", "description": "Distracted driver warning/Near miss.", "paid": "$0", "reserves": "$0", "status": "Closed"},
                {"policy_period": "2023-2024", "date_of_loss": "2023-11-20", "type": "Workers Comp", "description": "Tripping hazard in packing aisle.", "paid": "$3,200", "reserves": "$1,000", "status": "Open"},
                {"policy_period": "2022-2023", "date_of_loss": "2022-08-30", "type": "Property", "description": "Warehouse inventory theft.", "paid": "$45,000", "reserves": "$0", "status": "Closed"},
                {"policy_period": "2022-2023", "date_of_loss": "2023-01-14", "type": "Auto", "description": "Delivery van bumper damage.", "paid": "$3,500", "reserves": "$0", "status": "Closed"}
            ]
        }
    }
}

# ------------------------------------------------------------------------------
# Tools
# ------------------------------------------------------------------------------

def get_client_telemetry(client_id: str) -> dict:
    """Retrieves combined structured (BigQuery) and unstructured metrics for a client.
    
    Args:
        client_id: Unique identifier for the client (e.g. 'acme', 'zenith', 'stella').
    """
    if client_id not in MOCK_CLIENTS:
        return {"error": f"Client ID '{client_id}' not found."}
    
    project_id = os.environ.get('GOOGLE_CLOUD_PROJECT', 'ninghai-ccai')
    query = f"""
        SELECT *
        FROM `{project_id}.underwriter_demo.client_profiles`
        WHERE client_id = @client_id
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("client_id", "STRING", client_id)
        ]
    )
    
    try:
        results = bq_client.query(query, job_config=job_config).result()
        for row in results:
            return {
                "id": client_id,
                "name": row.name,
                "industry": row.industry,
                "bq_data": {
                    "company_size": row.company_size,
                    "annual_revenue": row.annual_revenue,
                    "headquarters": row.headquarters,
                    "years_in_business": row.years_in_business,
                    "primary_operations": row.primary_operations,
                    "number_of_facilities": row.number_of_facilities,
                    "safety_rating_class": row.safety_rating_class
                },
                "loss_runs": MOCK_CLIENTS[client_id]["loss_runs"]
            }
        return {"error": "Client profile found in memory but missing in BigQuery."}
    except Exception as e:
        return {"error": f"Failed to retrieve data from BigQuery: {str(e)}"}

def list_client_profiles() -> list[dict]:
    """Lists available client profiles (ID and Name)."""
    project_id = os.environ.get('GOOGLE_CLOUD_PROJECT', 'ninghai-ccai')
    query = f"""
        SELECT client_id as id, name 
        FROM `{project_id}.underwriter_demo.client_profiles`
    """
    try:
        results = bq_client.query(query).result()
        return [{"id": row.id, "name": row.name} for row in results]
    except Exception as e:
        return [{"error": f"Failed to list profiles: {str(e)}"}]

# ------------------------------------------------------------------------------
# Agent & App Definition
# ------------------------------------------------------------------------------

# Using Vertex Gemini model instance
model = VertexGemini(model='gemini-2.5-flash')

root_agent = Agent(
    name="underwriter_agent",
    model=model,
    instruction="""You are an expert AI Underwriter assisting a human risk engineer.
    Your goal is to synthesize structured BigQuery data and unstructured Loss Runs data to provide a risk summary and recommendations.
    
    Use the `get_client_telemetry` tool to retrieve data for a selected client profile.
    Do NOT guess parameters. If you don't know the client ID, use `list_client_profiles` first!
    
    Structure your output using Markdown headers:
    1. ### Executive Summary
    2. ### High-Risk Factors Identified
    3. ### Mitigation Recommendations
    4. ### Underwriting Verdict
    """,
    tools=[get_client_telemetry, list_client_profiles]
)

app = App(
    name="underwriter_agent",
    root_agent=root_agent
)
