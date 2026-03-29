import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from google.genai import types

from google.cloud import bigquery

# ADK Imports
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from backend.underwriter_agent.agent import app as agent_app
from backend.underwriter_agent.tools import get_client_profile_by_id

app = FastAPI()



# MOCK_CLIENTS is imported from backend.underwriter_agent.agent

class GenerateRequest(BaseModel):
    clientId: str

@app.get("/api/clients")
def get_clients():
    project_id = os.environ.get('GOOGLE_CLOUD_PROJECT', 'ninghai-ccai')
    bq_client = bigquery.Client(project=project_id)
    query = f"SELECT client_id as id, name FROM `{project_id}.underwriter_demo.client_profiles`"
    try:
        results = bq_client.query(query).result()
        return [{"id": row.id, "name": row.name} for row in results]
    except Exception as e:
        return [{"error": f"Failed to list profiles: {str(e)}"}]

@app.get("/api/clients/{client_id}")
def get_client(client_id: str):
    data = get_client_profile_by_id(client_id)
    if "error" in data:
        raise HTTPException(status_code=404, detail=data["error"])
    return data

@app.post("/api/generate-summary")
async def generate_summary(request: GenerateRequest):
    client_id = request.clientId
    profile = get_client_profile_by_id(client_id)
    if "error" in profile:
        raise HTTPException(status_code=404, detail="Client not found")
    
    try:
        runner = Runner(
            app=agent_app,
            session_service=InMemorySessionService(),
            auto_create_session=True
        )
        
        prompt = f"Provide a risk assessment summary for client profile: {client_id}"
        
        response_text = ""
        rag_payload = None
        
        async for event in runner.run_async(
            user_id="ui_user",
            session_id=f"session_{client_id}",
            new_message=types.Content(role="user", parts=[types.Part(text=prompt)])
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        response_text += part.text
                    # Intercept Tool Returns
                    if getattr(part, "function_response", None) and part.function_response.name == "get_loss_run_report":
                        rag_payload = part.function_response.response
                        
        if not response_text:
            raise Exception("Empty response from ADK agent")
            
        return {"summary": response_text, "rag_payload": rag_payload}
        
    except Exception as e:
        print(f"ADK Agent call failed: {e}")
        raise HTTPException(status_code=500, detail=f"ADK Agent execution failed: {str(e)}")


# Mount Static Files for UI (placed at bottom to avoid shadowing API routes)
app.mount("/reports", StaticFiles(directory="reports"), name="reports")
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
