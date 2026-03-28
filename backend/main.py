import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from google.genai import types

# ADK Imports
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from backend.underwriter_agent.agent import app as agent_app, MOCK_CLIENTS, list_client_profiles, get_client_telemetry

app = FastAPI()



# MOCK_CLIENTS is imported from backend.underwriter_agent.agent

class GenerateRequest(BaseModel):
    clientId: str

@app.get("/api/clients")
def get_clients():
    return list_client_profiles()

@app.get("/api/clients/{client_id}")
def get_client(client_id: str):
    data = get_client_telemetry(client_id)
    if "error" in data:
        raise HTTPException(status_code=404, detail=data["error"])
    return data

@app.post("/api/generate-summary")
async def generate_summary(request: GenerateRequest):
    client_id = request.clientId
    if client_id not in MOCK_CLIENTS:
        raise HTTPException(status_code=404, detail="Client not found")

    client = MOCK_CLIENTS[client_id]
    
    try:
        runner = Runner(
            app=agent_app,
            session_service=InMemorySessionService(),
            auto_create_session=True
        )
        
        prompt = f"Provide a risk assessment summary for client profile: {client_id}"
        
        response_text = ""
        async for event in runner.run_async(
            user_id="ui_user",
            session_id=f"session_{client_id}",
            new_message=types.Content(role="user", parts=[types.Part(text=prompt)])
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        response_text += part.text
                        
        if not response_text:
            raise Exception("Empty response from ADK agent")
            
        return {"summary": response_text}
        
    except Exception as e:
        print(f"ADK Agent call failed, using fallback simulation: {e}")
        return {"summary": get_fallback_summary(client)}

def get_fallback_summary(client):
    if client['id'] == 'acme':
        return """
### Executive Summary
**Acme Logistics** presents a *High-Risk* profile due to elevated loss ratios (82%) and recurring weather-related claims. The synthesis of BQ frequency data and narrative reports points to systemic gaps in route safety management during adverse conditions.

### High-Risk Factors Identified
- **Clustered Claims Trigger**: Correlating the $75k cargo claim with "Winter peaks" suggests lack of proactive routing procedures or anti-skid chain deployment.
- **Narrative Overlaps**: Multiple incidents match reports of "Incomplete maintenance logs" coupled with "Overtime spikes", increasing statistical likelihood of fatigue-driven accidents.

### Mitigation Recommendations
- Implement telematics tracking for speed and routing compliance.
- Mandate pre-shift vehicle checks using digital logging apps to standardize maintenance tracking.

### Underwriting Verdict
**Refer to Committee** (Due to loss ratio > 75% threshold).
"""
    elif client['id'] == 'zenith':
        return """
### Executive Summary
**Zenith Manufacturing** presents a *Low-to-Medium Risk* profile. An excellent loss ratio (45%) indicates robust safety cultures, though ergonomic and conveyors narratives indicate slight operational friction.

### High-Risk Factors Identified
- **Micro-hazard Frequency**: While large settlements are rare, "Ergonomic complaints" and "Moving conveyor" incidents signal potential for Cumulative Trauma Disorder (CTD) claims if left unmanaged.

### Mitigation Recommendations
- Conduct workplace ergonomic assessments for packing stations.
- Verify conveyor guards meet OSHA standards and perform lockout-tagout drills.

### Underwriting Verdict
**Auto-Bind** with standard pricing adjustments.
"""
    else:
        return """
### Executive Summary
**Stellar Retail** exhibits a *Medium-Risk* profile. High claims frequency (22/yr) is typical for rapid e-commerce expansion, but "Stress reports" and theft risks indicate potential operational strain causing delivery inefficiencies.

### High-Risk Factors Identified
- **Fatigue Indicators**: Narrative links "Distraction warnings" to peak delivery hours, suggesting driver routing optimization needs oversight.
- **Shrinkage & Tripping Variables**: Inventory theft overlapping with warehouse clutter (tripping hazards) shows workflow congestion.

### Mitigation Recommendations
- Standardize driver fatigue training and fatigue-management rest schedules.
- Optimize warehouse layout using 5S lean principles to reduce trip hazards.

### Underwriting Verdict
**Refer to Committee** for audit verification on expansion metrics.
"""

# Mount Static Files for UI (placed at bottom to avoid shadowing API routes)
app.mount("/reports", StaticFiles(directory="reports"), name="reports")
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
