#!/bin/bash
# High-speed automated deployment script for Google Cloud Run
set -e

# Detect active GCP project
PROJECT_ID=$(gcloud config get-value project)
if [ -z "$PROJECT_ID" ]; then
    echo "❌ Error: Could not determine active Google Cloud Project."
    echo "Please set one using: gcloud config set project [YOUR-PROJECT-ID]"
    exit 1
fi

SERVICE_NAME="underwriter-workbench"
REGION="us-central1"

echo "🚀 Deploying [$SERVICE_NAME] to Cloud Run in project [$PROJECT_ID]..."

# =========================================================================
# IAM PERMISSION REQUIREMENTS:
# The Service Account attached to this Cloud Run revision MUST possess 
# the following Google Cloud IAM Roles to function properly:
# 
# 1. roles/aiplatform.user      (To execute Gemini LLM context synthesis via ADK)
# 2. roles/discoveryengine.viewer (To query the 'underwriter-loss-runs' RAG Datastore)
# 3. roles/bigquery.dataViewer  (To read the 'client_profiles' dataset)
# 4. roles/bigquery.user        (To execute the structured BigQuery SQL jobs)
# =========================================================================

# Deploy the service utilizing Cloud Build to remotely craft the container
gcloud run deploy $SERVICE_NAME \
  --source . \
  --region $REGION \
  --memory 1Gi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 1

echo "✅ Environment deployment successfully initiated!"
