import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from google.genai import types

from google.cloud import bigquery

# ADK / GenAI Imports
from google.genai import Client
from underwriter_agent.tools import get_client_profile_by_id

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
        
    async def event_generator():
        try:
            # Use configured AGENT_ID from environment explicitly
            agent_id = os.environ.get("AGENT_ID", "projects/840328373082/locations/us-central1/reasoningEngines/4546472334516551680")
            
            prompt = f"Provide a risk assessment summary for client profile: {client_id}"
            
            import google.auth
            from google.auth.transport.requests import Request
            import httpx
            import json
            
            credentials, _ = google.auth.default()
            credentials.refresh(Request())
            
            url = f"https://us-central1-aiplatform.googleapis.com/v1beta1/{agent_id}:streamQuery"
            headers = {
                "Authorization": f"Bearer {credentials.token}",
                "Content-Type": "application/json"
            }
            payload = {
                "input": {
                    "user_id": f"session_{client_id}",
                    "message": prompt
                }
            }
            
            async with httpx.AsyncClient(timeout=300.0) as http_client:
                async with http_client.stream("POST", url, headers=headers, json=payload) as response:
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        try:
                            chunk_data = json.loads(line)
                            parts = chunk_data.get("content", {}).get("parts", [])
                            
                            for part in parts:
                                match part:
                                    # 1. Intercept Tool Executions (Start of RAG process)
                                    case {"function_call": {"name": name, "args": args}} if name in ["get_loss_run_report", "get_client_profile_by_id", "profile_fetcher"]:
                                        client_id_arg = args.get("client_id", client_id)
                                        queries = [
                                            f"Function Called: {name}",
                                            f"Target profile arguments: {json.dumps(args)}",
                                            f"Awaiting Vertex AI remote big data infrastructure..."
                                        ]
                                        yield f"data: {json.dumps({'state': 'rag_search_started', 'queries': queries})}\n\n"
                                        
                                    # 2. Intercept Tool Results (The literal RAG Engine big data query result)
                                    case {"function_response": {"name": "get_loss_run_report", "response": response}}:
                                        yield f"data: {json.dumps({'state': 'rag_search_complete', 'rag_payload': response})}\n\n"
                                        
                                    # 3. Intercept Gemini Generation Output
                                    case {"text": text} if text:
                                        yield f"data: {json.dumps({'state': 'generating', 'chunk': text})}\n\n"
                                    
                        except json.JSONDecodeError:
                            continue
                            
            yield f"data: {json.dumps({'state': 'done'})}\n\n"
            
        except Exception as e:
            print(f"ADK Agent stream failed: {e}")
            yield f"data: {json.dumps({'state': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# Mount Static Files for UI (placed at bottom to avoid shadowing API routes)
app.mount("/reports", StaticFiles(directory="reports"), name="reports")
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
