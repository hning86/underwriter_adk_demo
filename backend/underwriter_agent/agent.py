import os
from dotenv import load_dotenv

# Load environment variables (pulls GOOGLE_API_KEY from .env)
load_dotenv()

from google.cloud import bigquery
from google.cloud import discoveryengine_v1 as discoveryengine
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

# Mock Database migrated to Google BigQuery and Vertex AI Search (RAG)

# ------------------------------------------------------------------------------
# Tools
# ------------------------------------------------------------------------------

def get_client_profile_by_id(client_id: str) -> dict:
    """Retrieves combined structured (BigQuery) and unstructured metrics for a client.
    
    Args:
        client_id: Unique identifier for the client (e.g. 'acme', 'zenith', 'stella').
    """
    project_id = os.environ.get('GOOGLE_CLOUD_PROJECT', 'ninghai-ccai')
    query = f"""
        SELECT *
        FROM `{project_id}.underwriter_demo.client_profiles`
        WHERE client_id = @client_id
    """
    display_query = f"""
        SELECT *
        FROM `{project_id}.underwriter_demo.client_profiles`
        WHERE client_id = '{client_id}'
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
                    "company_name": row.name,
                    "industry": row.industry,
                    "company_size": row.company_size,
                    "annual_revenue": row.annual_revenue,
                    "headquarters": row.headquarters,
                    "years_in_business": row.years_in_business,
                    "primary_operations": row.primary_operations,
                    "number_of_facilities": row.number_of_facilities,
                    "safety_rating_class": row.safety_rating_class
                },
                "bq_query": display_query.strip()
            }
        return {"error": "Client profile found in memory but missing in BigQuery."}
    except Exception as e:
        return {"error": f"Failed to retrieve data from BigQuery: {str(e)}"}

def get_loss_run_report(client_id: str) -> dict:
    """Retrieves the unstructured loss runs data (claims history) for a given client via Vertex Search.
    
    Args:
        client_id: Unique identifier for the client (e.g. 'acme', 'zenith', 'stella').
    """
    project_id = os.environ.get('GOOGLE_CLOUD_PROJECT', 'ninghai-ccai')
    location = "global"
    ds_id = "underwriter-loss-runs"
    
    search_client = discoveryengine.SearchServiceClient()
    serving_config = f"projects/{project_id}/locations/{location}/collections/default_collection/dataStores/{ds_id}/servingConfigs/default_search"
    
    ensemble_queries = [
        f"Provide a detailed summary of all financial loss runs and structured claims history for {client_id}.",
        f"What are the specific safety violations, ergonomic incidents, or warehouse accidents for {client_id}?",
        f"List all exact dollar payout amounts, claim costs, reserves, and cargo damages for {client_id}."
    ]
    
    all_snippets = []
    
    try:
        for query in ensemble_queries:
            request = discoveryengine.SearchRequest(
                serving_config=serving_config,
                query=query,
                page_size=3,
                content_search_spec=discoveryengine.SearchRequest.ContentSearchSpec(
                    snippet_spec=discoveryengine.SearchRequest.ContentSearchSpec.SnippetSpec(
                        return_snippet=True,
                        max_snippet_count=3
                    )
                )
            )
            response = search_client.search(request)
            for result in response.results:
                if result.document.id != client_id:
                    continue
                if result.document.derived_struct_data:
                    for snip in result.document.derived_struct_data.get("snippets", []):
                        all_snippets.append(snip.get("snippet", ""))

        if not all_snippets:
            print(f"\\n⚠️ [RAG DEBUG] No snippets retrieved for client '{client_id}'. Index may be compiling.")
            return {"error": f"No relevant claims history found for client '{client_id}'.", "query": "Ensemble queries executed"}
            
        unique_snippets = list(set(all_snippets))
        combined_snippets = " \\n...\\n ".join(unique_snippets)
        print(f"\\n🔍 [RAG DEBUG] Sending the following Ensemble snippets to Gemini for {client_id}:\\n{combined_snippets}\\n=========================================\\n")
        return {"loss_runs": {"query": f"Ensemble Search (3 deep analytical filters applied for {client_id})", "extracted_claims_context": combined_snippets}}
        
    except Exception as e:
        return {"error": f"Vertex AI Search execution failed: {str(e)}"}



# ------------------------------------------------------------------------------
# Agent & App Definition
# ------------------------------------------------------------------------------

# Using Vertex Gemini model instance
model_name = os.environ.get('GEMINI_MODEL', 'gemini-2.5-flash')
model = VertexGemini(model=model_name)

root_agent = Agent(
    name="underwriter_agent",
    model=model,
    instruction="""You are an expert AI Underwriter assisting a human risk engineer.
    Your goal is to synthesize structured BigQuery data and unstructured Loss Runs data to provide a risk summary and recommendations.
    
    You MUST execute TWO tools to retrieve the necessary context for your analysis:
    1. Use the `get_client_profile_by_id` tool to retrieve the structured BigQuery data.
    2. Use the `get_loss_run_report` tool to retrieve the unstructured claims history and narrative.
    
    Structure your output using Markdown headers:
    1. ### Executive Summary
    2. ### High-Risk Factors Identified
    3. ### Mitigation Recommendations
    4. ### Underwriting Verdict
    
    CRITICAL INSTRUCTION: Do NOT include, quote, or parrot the raw Vertex Search Query strings or the exact extracted JSON snippet payload in your final response. The user already views the raw search tool logs in a separate RAG Engine UI tab. Your job is ONLY to synthesize the information into the 4 professional headers above.
    """,
    tools=[get_client_profile_by_id, get_loss_run_report]
)

app = App(
    name="underwriter_agent",
    root_agent=root_agent
)
