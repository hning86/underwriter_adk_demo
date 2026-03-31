import vertexai
from vertexai.preview import reasoning_engines
agent_id = "projects/840328373082/locations/us-central1/reasoningEngines/4546472334516551680"
vertexai.init(project="ninghai-ccai", location="us-central1")
agent = reasoning_engines.ReasoningEngine(agent_id)
print(dir(agent))
