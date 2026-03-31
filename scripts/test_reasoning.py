import os
from google.cloud import aiplatform
from vertexai.preview import reasoning_engines

agent_id = "projects/840328373082/locations/us-central1/reasoningEngines/4546472334516551680"
print(f"Loading {agent_id}")
aiplatform.init(project="ninghai-ccai", location="us-central1")
remote_app = reasoning_engines.ReasoningEngine(agent_id)
print("Available methods:", dir(remote_app))
