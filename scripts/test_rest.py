import google.auth
from google.auth.transport.requests import Request
import requests
import json

agent_id = "840328373082/locations/us-central1/reasoningEngines/4546472334516551680"
url = f"https://us-central1-aiplatform.googleapis.com/v1beta1/projects/{agent_id}:streamQuery"

credentials, _ = google.auth.default()
credentials.refresh(Request())

headers = {
    "Authorization": f"Bearer {credentials.token}",
    "Content-Type": "application/json"
}
payload = {
    "input": {
        "user_id": "session_acme",
        "message": "Provide a risk assessment summary for client profile: acme"
    }
}

response = requests.post(url, headers=headers, json=payload, stream=True)
for line in response.iter_lines():
    if line:
        try:
            d = json.loads(line.decode('utf-8'))
            print(json.dumps(d, indent=2))
        except:
            print(line.decode('utf-8'))
