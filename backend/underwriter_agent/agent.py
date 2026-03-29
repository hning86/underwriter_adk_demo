import os
from dotenv import load_dotenv

# Load environment variables (pulls GOOGLE_API_KEY from .env)
load_dotenv()

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models.google_llm import Gemini
from google.genai import types, Client

from backend.underwriter_agent.tools import get_client_profile_by_id, get_loss_run_report

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
