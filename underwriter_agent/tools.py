import os
import re
from google.cloud import bigquery
from google.cloud import discoveryengine_v1 as discoveryengine

# Global client initialization to reuse connection pool
bq_client = bigquery.Client(
    project=os.environ.get('GOOGLE_CLOUD_PROJECT', 'ninghai-ccai'),
    location=os.environ.get('GOOGLE_CLOUD_LOCATION', 'us-central1')
)

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
                    extractive_content_spec=discoveryengine.SearchRequest.ContentSearchSpec.ExtractiveContentSpec(
                        max_extractive_segment_count=1
                    )
                )
            )
            response = search_client.search(request)
            for result in response.results:
                if result.document.id != client_id:
                    continue
                if result.document.derived_struct_data:
                    for seg in result.document.derived_struct_data.get("extractive_segments", []):
                        raw_seg = seg.get("content", "")
                        clean_seg = re.sub(r'</?b>', '', raw_seg)
                        clean_seg = clean_seg.replace('...', '').strip()
                        if clean_seg:
                            all_snippets.append(clean_seg)

        if not all_snippets:
            print(f"\\n⚠️ [RAG DEBUG] No snippets retrieved for client '{client_id}'. Index may be compiling.")
            return {"error": f"No relevant claims history found for client '{client_id}'.", "query": "Ensemble queries executed"}
            
        unique_snippets = list(set(all_snippets))
        combined_snippets = "\\n\\n".join(unique_snippets)
        print(f"\\n🔍 [RAG DEBUG] Sending the following Ensemble snippets to Gemini for {client_id}:\\n{combined_snippets}\\n=========================================\\n")
        return {"loss_runs": {"queries": ensemble_queries, "extracted_claims_context": combined_snippets}}
        
    except Exception as e:
        return {"error": f"Vertex AI Search execution failed: {str(e)}"}
