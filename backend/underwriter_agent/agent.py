import os
from dotenv import load_dotenv

# Load environment variables (pulls GOOGLE_API_KEY from .env)
load_dotenv()

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models.google_llm import Gemini
from google.genai import types

# Mock Database
MOCK_CLIENTS = {
    "acme": {
        "id": "acme",
        "name": "Acme Logistics",
        "industry": "Transportation",
        "bq_data": {
            "premium_3y": 450000,
            "loss_ratio": 0.82,
            "claims_frequency": 14,
            "large_claims": [
                "Cargo damage claim: $75,000 (Winter storm ice event)",
                "Rollover accident: $50,000"
            ]
        },
        "loss_runs": {
            "narrative": "Acme Logistics operates a fleet of 50 delivery vehicles. Recent safety checks suggest maintenance logs are incomplete. Drivers reported overtime peaks during holiday seasons.",
            "key_incidents": [
                "Rear-end collision in warehouse yard.",
                "Slip and fall on ice in depot."
            ]
        }
    },
    "zenith": {
        "id": "zenith",
        "name": "Zenith Manufacturing",
        "industry": "Heavy Machinery",
        "bq_data": {
            "premium_3y": 1200000,
            "loss_ratio": 0.45,
            "claims_frequency": 4,
            "large_claims": [
                "Machine malfunction injury: $120,000 (Settled)"
            ]
        },
        "loss_runs": {
            "narrative": "Zenith has automated production lines. Safety metrics are above average, but shop floor ergonomics are a recurring complaint in worker surveys.",
            "key_incidents": [
                "Minor hand injury on conveyor belt.",
                "Back strain from manual lifting."
            ]
        }
    },
    "retail": {
        "id": "retail",
        "name": "Stellar Retail",
        "industry": "E-Commerce",
        "bq_data": {
            "premium_3y": 800000,
            "loss_ratio": 0.68,
            "claims_frequency": 22,
            "large_claims": [
                "Warehouse inventory theft: $45,000",
                "Delivery van bumper damage: multiple small claims"
            ]
        },
        "loss_runs": {
            "narrative": "Stellar Retail has rapid expansion. High turnover of warehouse staff. Stress reports during peak delivery windows.",
            "key_incidents": [
                "Distracted driver warning.",
                "Tripping hazard in packing aisle."
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
        client_id: Unique identifier for the client (e.g. 'acme', 'zenith', 'retail').
    """
    if client_id not in MOCK_CLIENTS:
        return {"error": f"Client ID '{client_id}' not found."}
    return MOCK_CLIENTS[client_id]

def list_client_profiles() -> list[dict]:
    """Lists available client profiles (ID and Name)."""
    return [{"id": v["id"], "name": v["name"]} for v in MOCK_CLIENTS.values()]

# ------------------------------------------------------------------------------
# Agent & App Definition
# ------------------------------------------------------------------------------

# Using Gemini model instance
model = Gemini(model='gemini-2.5-flash')

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
