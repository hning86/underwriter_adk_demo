#!/bin/bash
# High-speed automated deployment script for Vertex AI Agent Engine using Google ADK
set -e

# Default GCP project
PROJECT_ID="ninghai-ccai"

REGION="us-central1"
DISPLAY_NAME="Underwriter Agent"

echo "🚀 Deploying [$DISPLAY_NAME] to Vertex AI Agent Engine in project [$PROJECT_ID]..."

# Deploy the agent using Google ADK
# Using explicit virtual environment path for the ADK CLI
.venv/bin/adk deploy agent_engine \
  --project "$PROJECT_ID" \
  --region "$REGION" \
  --display_name "$DISPLAY_NAME" \
  --otel_to_cloud \
  --agent_engine_id "4546472334516551680" \
  underwriter_agent

echo "====================================================================================="
echo "✅ Agent Engine deployment successfully completed!"
echo "NOTE: Once the deployment completes, ADK will output a Reasoning Engine resource name."
echo "You must copy the returned resource name and configure it in your environment."
echo ""
echo "Example:"
echo "export AGENT_ID=\"projects/$PROJECT_ID/locations/$REGION/reasoningEngines/1234567890\""
echo "====================================================================================="
